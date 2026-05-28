from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.services.unknown_service import UnknownService
from app.schemas.unknown import UnknownFaceListResponse, RegisterFromUnknownRequest, UnknownSimilarityResponse
from app.services.face_service import FaceService

router = APIRouter(prefix="/unknowns", tags=["Unknown Faces"])
service = UnknownService()

@router.get("", response_model=UnknownFaceListResponse)
def list_unknowns(
    page: int = 1,
    size: int = 20,
    is_reviewed: bool | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    items, total = service.list_paginated(db, page, size, is_reviewed)
    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size
    }

@router.put("/{log_id}/review")
def mark_reviewed(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    log = service.mark_reviewed(db, log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Unknown face log not found")
    return log

@router.post("/{log_id}/register")
def register_unknown_as_person(
    log_id: int,
    request: RegisterFromUnknownRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    log = service.repo.get_by_id(db, log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Unknown face log not found")
        
    if log.registered_as_person_id:
        raise HTTPException(status_code=400, detail="This face is already registered")
        
    face_service = FaceService()
    
    # We would need to read the snapshot image and pass it as an UploadFile equivalent
    # Since FaceService expects UploadFile, we need to mock it or update the service.
    # For now, let's create a minimal implementation that bypasses the UploadFile requirement
    
    from fastapi import UploadFile
    import io
    from pathlib import Path
    from app.config import load_settings
    
    settings = load_settings()
    snapshot_abs_path = settings.base_dir / log.snapshot_path
    if not snapshot_abs_path.exists():
        raise HTTPException(status_code=404, detail="Snapshot file missing")
        
    with open(snapshot_abs_path, "rb") as f:
        raw_bytes = f.read()
        
    class MockUploadFile:
        def __init__(self, filename, content):
            self.filename = filename
            self.file = io.BytesIO(content)
            
    mock_file = MockUploadFile(Path(log.snapshot_path).name, raw_bytes)
    
    data = request.model_dump()
    # Let FaceService handle creation
    person = face_service.create_person(db, current_user.id, data, [mock_file])
    
    # Update log
    log.is_reviewed = True
    log.registered_as_person_id = person.id
    service.repo.update(db, log)
    
    return person

@router.get("/{log_id}/similar", response_model=UnknownSimilarityResponse)
def similar_unknowns(
    log_id: int,
    top_k: int | None = Query(None, ge=1, le=50),
    min_similarity: float | None = Query(None, ge=0.0, le=1.0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    items = service.find_similar(db, log_id, top_k=top_k, min_similarity=min_similarity)
    return {"items": items}
