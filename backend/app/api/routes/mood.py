from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.services.emotion_service import EmotionService

router = APIRouter(prefix="/mood", tags=["Mood & Analytics"])
service = EmotionService()

@router.get("/stats")
def get_mood_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stats = service.get_mood_stats(db)
    return {
        "mood_distribution": stats,
        "total_records": sum(stats.values())
    }

@router.get("/person/{person_id}")
def get_person_mood_history(
    person_id: int,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    records = service.get_person_mood_history(db, person_id, limit)
    return records
