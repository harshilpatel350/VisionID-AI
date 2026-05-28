from __future__ import annotations
from datetime import datetime, timedelta
from sqlalchemy import and_, func, select, desc
from sqlalchemy.orm import Session
from app.models.recognition import RecognitionLog, AuditLog
from app.models.face import Person

class RecognitionRepository:
    def add_log(self, db: Session, log: RecognitionLog) -> RecognitionLog:
        db.add(log); db.flush(); return log

    def recent_logs(self, db: Session, limit: int = 100, offset: int = 0):
        return list(db.scalars(select(RecognitionLog).order_by(RecognitionLog.occurred_at.desc()).offset(offset).limit(limit)).all())

    def count_total_logs(self, db: Session) -> int:
        return db.scalar(select(func.count(RecognitionLog.id))) or 0

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

    def filtered_logs(
        self,
        db: Session,
        start: datetime | None = None,
        end: datetime | None = None,
        mood: str | None = None,
        is_unknown: bool | None = None,
        person_name: str | None = None,
        sort: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[RecognitionLog], int]:
        stmt = select(RecognitionLog)
        if start:
            stmt = stmt.where(RecognitionLog.occurred_at >= start)
        if end:
            stmt = stmt.where(RecognitionLog.occurred_at <= end)
        if mood:
            stmt = stmt.where(RecognitionLog.mood == mood)
        if is_unknown is not None:
            stmt = stmt.where(RecognitionLog.is_unknown.is_(is_unknown))
        if person_name:
            stmt = stmt.where(RecognitionLog.person_name.ilike(f"%{person_name}%"))

        total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        if sort == "asc":
            stmt = stmt.order_by(RecognitionLog.occurred_at.asc())
        else:
            stmt = stmt.order_by(RecognitionLog.occurred_at.desc())
        stmt = stmt.offset(offset).limit(limit)
        items = list(db.scalars(stmt).all())
        return items, total
