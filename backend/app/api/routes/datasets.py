from __future__ import annotations
from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.models.dataset import Dataset
from app.schemas.response_envelope import ResponseEnvelope
from app.services.dataset_service import DatasetService
from app.utils.validators import sanitize_filename, validate_image_upload # we could write a validate_zip upload

router = APIRouter(prefix="/datasets", tags=["datasets"])
svc = DatasetService()

@router.get("", response_model=ResponseEnvelope[list[dict]])
def list_datasets(db: Session = Depends(get_db), _user=Depends(require_roles("admin", "operator", "viewer"))):
    rows = db.query(Dataset).order_by(Dataset.created_at.desc()).all()
    data = [{
        "id": d.id, "name": d.name, "description": d.description, "source_path": d.source_path,
        "total_images": d.total_images, "processed_images": d.processed_images, "status": d.status,
        "created_by": d.created_by, "created_at": d.created_at.isoformat() if d.created_at else None
    } for d in rows]
    return ResponseEnvelope(data=data)

@router.post("", response_model=ResponseEnvelope[dict], status_code=status.HTTP_201_CREATED)
def create_dataset(name: str = Form(...), description: str | None = Form(None), db: Session = Depends(get_db), user=Depends(require_roles("admin", "operator"))):
    ds = svc.create_dataset(db, name=name, description=description, created_by=user.id)
    db.commit()
    db.refresh(ds)
    return ResponseEnvelope(data={"id": ds.id, "name": ds.name})

@router.post("/upload", response_model=ResponseEnvelope[dict], status_code=status.HTTP_201_CREATED)
def upload_dataset(file: UploadFile = File(...), name_hint: str = Form("dataset"), db: Session = Depends(get_db), user=Depends(require_roles("admin", "operator"))):
    # Sanitize the name hint
    safe_name = sanitize_filename(name_hint)
    
    # We would add validate_archive_upload here but standard limits apply in service
    path = svc.save_folder_upload(file, safe_name)
    ds = svc.create_dataset(db, name=file.filename or safe_name, description="Uploaded dataset archive", created_by=user.id)
    ds.source_path = str(path)
    ds.status = "uploaded"
    db.commit()
    return ResponseEnvelope(data={"dataset_id": ds.id, "path": str(path)})
