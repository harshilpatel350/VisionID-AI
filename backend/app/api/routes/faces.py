from __future__ import annotations
from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.models.face import Person
from app.models.recognition import AuditLog
from app.schemas.face import PersonUpdate
from app.services.face_service import FaceService
from app.repositories.face_repo import FaceRepository
from app.repositories.recognition_repo import RecognitionRepository

router = APIRouter(prefix="/faces", tags=["faces"])
svc = FaceService()
repo = FaceRepository()
audit_repo = RecognitionRepository()

@router.get("/persons")
def list_persons(db: Session = Depends(get_db), _user=Depends(require_roles("admin", "operator", "viewer"))):
    return svc.list_persons(db)

@router.post("/persons")
def create_person(
    full_name: str = Form(...),
    email: str | None = Form(None),
    phone: str | None = Form(None),
    department: str | None = Form(None),
    title: str | None = Form(None),
    notes: str | None = Form(None),
    images: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
    user=Depends(require_roles("admin", "operator")),
):
    person = svc.create_person(
        db,
        created_by=user.id,
        data={"full_name": full_name, "email": email, "phone": phone, "department": department, "title": title, "notes": notes},
        files=images,
    )
    audit_repo.add_audit(db, AuditLog(actor_user_id=user.id, action="create_person", entity_type="person", entity_id=str(person.id), metadata_json={"name": person.full_name}))
    db.commit()
    db.refresh(person)
    return {
        "id": person.id,
        "person_code": person.person_code,
        "full_name": person.full_name,
        "email": person.email,
        "phone": person.phone,
        "department": person.department,
        "title": person.title,
        "notes": person.notes,
        "primary_image_path": person.primary_image_path,
        "is_active": person.is_active,
        "embedding_model": person.embedding_model,
        "duplicate_of": person.duplicate_of,
        "sample_count": repo.sample_count(db, person.id),
        "created_at": person.created_at.isoformat() if person.created_at else None,
    }

@router.get("/persons/{person_id}")
def get_person(person_id: int, db: Session = Depends(get_db), _user=Depends(require_roles("admin", "operator", "viewer"))):
    person = repo.get_person(db, person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    return {
        "id": person.id,
        "person_code": person.person_code,
        "full_name": person.full_name,
        "email": person.email,
        "phone": person.phone,
        "department": person.department,
        "title": person.title,
        "notes": person.notes,
        "primary_image_path": person.primary_image_path,
        "is_active": person.is_active,
        "embedding_model": person.embedding_model,
        "duplicate_of": person.duplicate_of,
        "sample_count": repo.sample_count(db, person.id),
        "created_at": person.created_at.isoformat() if person.created_at else None,
    }

@router.put("/persons/{person_id}")
def update_person(person_id: int, payload: PersonUpdate, db: Session = Depends(get_db), user=Depends(require_roles("admin", "operator"))):
    person = repo.get_person(db, person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(person, k, v)
    audit_repo.add_audit(db, AuditLog(actor_user_id=user.id, action="update_person", entity_type="person", entity_id=str(person_id), metadata_json=payload.model_dump(exclude_unset=True)))
    db.commit()
    db.refresh(person)
    return {"status": "updated", "person_id": person.id}

@router.delete("/persons/{person_id}")
def delete_person(person_id: int, db: Session = Depends(get_db), user=Depends(require_roles("admin"))):
    person = repo.get_person(db, person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    repo.delete_person(db, person)
    audit_repo.add_audit(db, AuditLog(actor_user_id=user.id, action="delete_person", entity_type="person", entity_id=str(person_id)))
    db.commit()
    return {"status": "deleted"}

@router.post("/persons/{person_id}/samples")
def add_samples(person_id: int, images: list[UploadFile] = File(...), db: Session = Depends(get_db), user=Depends(require_roles("admin", "operator"))):
    person = repo.get_person(db, person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    count = 0
    for upload in images:
        sample = svc.add_sample_to_existing_person(db, person, upload)
        if sample is not None:
            count += 1
    db.commit()
    return {"status": "ok", "samples_added": count}

@router.post("/search")
def search_by_face(image: UploadFile = File(...), db: Session = Depends(get_db), user=Depends(require_roles("admin", "operator", "viewer"))):
    raw = image.file.read()
    _, results = svc.recognize_image(db, raw, "search", image.filename)
    db.commit()
    return {"results": [r.__dict__ for r in results]}

@router.get("/duplicates")
def duplicates(db: Session = Depends(get_db), _user=Depends(require_roles("admin", "operator", "viewer"))):
    persons = repo.list_persons(db)
    dup = [p for p in persons if p.duplicate_of is not None]
    return [{"person_id": p.id, "duplicate_of": p.duplicate_of, "name": p.full_name} for p in dup]

@router.get("/samples")
def samples(db: Session = Depends(get_db)):
    rows = repo.list_samples(db)
    return [{
        "id": s.id, "person_id": s.person_id, "image_path": s.image_path, "crop_path": s.crop_path,
        "quality_score": s.quality_score, "blur_score": s.blur_score, "low_light_score": s.low_light_score,
        "detection_score": s.detection_score, "embedding_hash": s.embedding_hash
    } for s in rows]
