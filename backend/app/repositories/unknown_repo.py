from sqlalchemy.orm import Session
from sqlalchemy import select, func, desc
from app.models.unknown import UnknownFaceLog

class UnknownRepository:
    def get_by_id(self, db: Session, log_id: int) -> UnknownFaceLog | None:
        return db.scalar(select(UnknownFaceLog).where(UnknownFaceLog.id == log_id))

    def create(self, db: Session, data: dict) -> UnknownFaceLog:
        log = UnknownFaceLog(**data)
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    def list_paginated(
        self, 
        db: Session, 
        page: int = 1, 
        size: int = 20, 
        is_reviewed: bool | None = None
    ) -> tuple[list[UnknownFaceLog], int]:
        stmt = select(UnknownFaceLog)
        if is_reviewed is not None:
            stmt = stmt.where(UnknownFaceLog.is_reviewed == is_reviewed)
            
        total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        
        stmt = stmt.order_by(desc(UnknownFaceLog.timestamp))
        stmt = stmt.offset((page - 1) * size).limit(size)
        items = list(db.scalars(stmt).all())
        
        return items, total

    def update(self, db: Session, log: UnknownFaceLog) -> UnknownFaceLog:
        db.commit()
        db.refresh(log)
        return log
