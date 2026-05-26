from sqlalchemy.orm import Session
from app.repositories.mood_repo import MoodRepository

class EmotionService:
    def __init__(self):
        self.repo = MoodRepository()

    def get_mood_stats(self, db: Session) -> dict[str, int]:
        return self.repo.get_mood_stats(db)

    def get_person_mood_history(self, db: Session, person_id: int, limit: int = 50):
        return self.repo.get_person_mood_history(db, person_id, limit)
