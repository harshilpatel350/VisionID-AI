from sqlalchemy.orm import Session
from sqlalchemy import select, func, desc
from app.models.mood import MoodRecord, SessionHistory

class MoodRepository:
    def create_record(self, db: Session, data: dict) -> MoodRecord:
        record = MoodRecord(**data)
        db.add(record)
        db.commit()
        db.refresh(record)
        return record
        
    def get_mood_stats(self, db: Session) -> dict[str, int]:
        stmt = select(MoodRecord.mood, func.count(MoodRecord.id)).group_by(MoodRecord.mood)
        results = db.execute(stmt).all()
        return {mood: count for mood, count in results}

    def get_person_mood_history(self, db: Session, person_id: int, limit: int = 50) -> list[MoodRecord]:
        stmt = select(MoodRecord).where(MoodRecord.person_id == person_id).order_by(desc(MoodRecord.timestamp)).limit(limit)
        return list(db.scalars(stmt).all())

class SessionRepository:
    def create(self, db: Session, data: dict) -> SessionHistory:
        session = SessionHistory(**data)
        db.add(session)
        db.commit()
        db.refresh(session)
        return session
        
    def update(self, db: Session, session: SessionHistory) -> SessionHistory:
        db.commit()
        db.refresh(session)
        return session

    def get_by_session_id(self, db: Session, session_id: str) -> SessionHistory | None:
        return db.scalar(select(SessionHistory).where(SessionHistory.session_id == session_id))
