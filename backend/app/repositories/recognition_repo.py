from __future__ import annotations
from datetime import datetime, timedelta
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session
from app.models.recognition import RecognitionLog, AuditLog
from app.models.face import Person

class RecognitionRepository:
    def add_log(self, db: Session, log: RecognitionLog) -> RecognitionLog:
        db.add(log); db.flush(); return log

    def recent_logs(self, db: Session, limit: int = 100):
        return list(db.scalars(select(RecognitionLog).order_by(RecognitionLog.occurred_at.desc()).limit(limit)).all())

    def today_total(self, db: Session) -> int:
        start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        return db.scalar(select(func.count(RecognitionLog.id)).where(RecognitionLog.occurred_at >= start)) or 0

    def count_unknowns(self, db: Session) -> int:
        return db.scalar(select(func.count(RecognitionLog.id)).where(RecognitionLog.is_unknown.is_(True))) or 0

    def top_persons(self, db: Session, limit: int = 5):
        stmt = (
            select(Person.full_name, func.count(RecognitionLog.id).label("hits"))
            .join(RecognitionLog, RecognitionLog.person_id == Person.id)
            .group_by(Person.id)
            .order_by(func.count(RecognitionLog.id).desc())
            .limit(limit)
        )
        return db.execute(stmt).all()

    def add_audit(self, db: Session, audit: AuditLog) -> AuditLog:
        db.add(audit); db.flush(); return audit

    def logs_by_day(self, db: Session, days: int = 14):
        start = datetime.utcnow() - timedelta(days=days)
        stmt = (
            select(func.date(RecognitionLog.occurred_at).label("day"), func.count(RecognitionLog.id))
            .where(RecognitionLog.occurred_at >= start)
            .group_by(func.date(RecognitionLog.occurred_at))
            .order_by(func.date(RecognitionLog.occurred_at))
        )
        return db.execute(stmt).all()
