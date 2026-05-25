from __future__ import annotations
from typing import Any

from fastapi import APIRouter, Depends, File, Form, UploadFile, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.core.context import get_request_context
from app.core.exceptions import NotFoundError, ValidationError
from app.models.recognition import AuditLog
from app.schemas.face import PersonUpdate, PersonOut, FaceSampleOut, DuplicateHit
from app.schemas.response_envelope import ResponseEnvelope, PaginatedResponse, PaginatedMeta
from app.services.face_service import FaceService
from app.repositories.face_repo import FaceRepository
from app.repositories.recognition_repo import RecognitionRepository
from app.utils.validators import validate_image_upload, validate_pagination

router = APIRouter(prefix="/faces", tags=["faces"])
svc = FaceService()
repo = FaceRepository()
audit_repo = RecognitionRepository()

@router.get("/persons", response_model=PaginatedResponse[PersonOut])
def list_persons(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db), 
    _user=Depends(require_roles("admin", "operator", "viewer"))
):
    offset, limit = validate_pagination(page, page_size)
    total, persons = svc.list_persons_paginated(db, offset, limit)
    
    meta = PaginatedMeta(
        total=total,
        page=page,
        page_size=limit,
        has_more=(offset + limit) < total
    )
    return PaginatedResponse(data=persons, meta=meta)

@router.post("/persons", response_model=ResponseEnvelope[PersonOut], status_code=status.HTTP_201_CREATED)
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
    if not images:
        raise ValidationError("At least one image is required")
        
    person = svc.create_person(
        db,
        created_by=user.id,
        data={"full_name": full_name, "email": email, "phone": phone, "department": department, "title": title, "notes": notes},
        files=images,
    )
    
    ctx = get_request_context()
    audit_repo.add_audit(db, AuditLog(
        actor_user_id=user.id, 
        action="create_person", 
        entity_type="person", 
        entity_id=str(person.id), 
        metadata_json={"name": person.full_name},
        ip_address=ctx.client_ip
    ))
    db.commit()
    db.refresh(person)
    return ResponseEnvelope(data=svc._serialize_person(db, person))

@router.get("/persons/{person_id}", response_model=ResponseEnvelope[PersonOut])
def get_person(person_id: int, db: Session = Depends(get_db), _user=Depends(require_roles("admin", "operator", "viewer"))):
    person = repo.get_person(db, person_id)
    if not person:
        raise NotFoundError("Person", person_id)
    return ResponseEnvelope(data=svc._serialize_person(db, person))

@router.put("/persons/{person_id}", response_model=ResponseEnvelope[dict[str, Any]])
def update_person(person_id: int, payload: PersonUpdate, db: Session = Depends(get_db), user=Depends(require_roles("admin", "operator"))):
    person = repo.get_person(db, person_id)
    if not person:
        raise NotFoundError("Person", person_id)
        
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(person, k, v)
        
    ctx = get_request_context()
    audit_repo.add_audit(db, AuditLog(
        actor_user_id=user.id, 
        action="update_person", 
        entity_type="person", 
        entity_id=str(person_id), 
        metadata_json=payload.model_dump(exclude_unset=True),
        ip_address=ctx.client_ip
    ))
    db.commit()
    return ResponseEnvelope(data={"status": "updated", "person_id": person.id})

@router.delete("/persons/{person_id}", response_model=ResponseEnvelope[dict[str, Any]])
def delete_person(person_id: int, db: Session = Depends(get_db), user=Depends(require_roles("admin"))):
    person = repo.get_person(db, person_id)
    if not person:
        raise NotFoundError("Person", person_id)
        
    repo.delete_person(db, person)
    
    ctx = get_request_context()
    audit_repo.add_audit(db, AuditLog(
        actor_user_id=user.id, 
        action="delete_person", 
        entity_type="person", 
        entity_id=str(person_id),
        ip_address=ctx.client_ip
    ))
    db.commit()
    return ResponseEnvelope(data={"status": "deleted"})

@router.post("/persons/{person_id}/samples", response_model=ResponseEnvelope[dict[str, Any]])
def add_samples(person_id: int, images: list[UploadFile] = File(...), db: Session = Depends(get_db), user=Depends(require_roles("admin", "operator"))):
    person = repo.get_person(db, person_id)
    if not person:
        raise NotFoundError("Person", person_id)
    
    if not images:
        raise ValidationError("At least one image is required")
        
    count = 0
    for upload in images:
        sample = svc.add_sample_to_existing_person(db, person, upload)
        if sample is not None:
            count += 1
            
    ctx = get_request_context()
    audit_repo.add_audit(db, AuditLog(
        actor_user_id=user.id, 
        action="add_samples", 
        entity_type="person", 
        entity_id=str(person_id),
        metadata_json={"added": count},
        ip_address=ctx.client_ip
    ))
    db.commit()
    return ResponseEnvelope(data={"status": "ok", "samples_added": count})

@router.post("/search", response_model=ResponseEnvelope[list[dict[str, Any]]])
def search_by_face(image: UploadFile = File(...), db: Session = Depends(get_db), user=Depends(require_roles("admin", "operator", "viewer"))):
    raw = validate_image_upload(image)
    _, results = svc.recognize_image(db, raw, "search", image.filename)
    db.commit()
    return ResponseEnvelope(data=[r.__dict__ for r in results])

@router.get("/duplicates", response_model=ResponseEnvelope[list[DuplicateHit]])
def duplicates(db: Session = Depends(get_db), _user=Depends(require_roles("admin", "operator", "viewer"))):
    persons = repo.list_persons(db)
    dup = [p for p in persons if p.duplicate_of is not None]
    
    # Needs to match DuplicateHit schema: source_person_id, source_name, duplicate_person_id, duplicate_name, similarity
    # Just returning basic for now based on what we have, we might need to adjust DuplicateHit schema or mapping
    res = []
    for p in dup:
        parent = repo.get_person(db, p.duplicate_of)
        res.append({
            "source_person_id": p.id,
            "source_name": p.full_name,
            "duplicate_person_id": p.duplicate_of,
            "duplicate_name": parent.full_name if parent else "Unknown",
            "similarity": 0.99 # Mock similarity as it's not stored
        })
    return ResponseEnvelope(data=res)

@router.get("/samples", response_model=ResponseEnvelope[list[FaceSampleOut]])
def samples(db: Session = Depends(get_db), _user=Depends(require_roles("admin", "operator", "viewer"))):
    rows = repo.list_samples(db)
    return ResponseEnvelope(data=[{
        "id": s.id, "person_id": s.person_id, "image_path": s.image_path, "crop_path": s.crop_path,
        "quality_score": s.quality_score, "blur_score": s.blur_score, "low_light_score": s.low_light_score,
        "detection_score": s.detection_score, "embedding_hash": s.embedding_hash
    } for s in rows])
