from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.services.group_service import GroupService
from app.services.face_service import FaceService

router = APIRouter(prefix="/group", tags=["Group Photo Analysis"])

@router.post("/analyze")
def analyze_group_photo(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        raw_bytes = file.file.read()
        # GroupService needs pipeline, let's borrow it from FaceService
        face_service = FaceService()
        if face_service.pipeline.index is None:
            if not face_service.pipeline.load_index():
                face_service.rebuild_index(db)
                
        service = GroupService(face_service.pipeline)
        result = service.analyze_group_photo(db, raw_bytes, source_ref=file.filename)
        db.commit()
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
