from __future__ import annotations
from io import BytesIO
from datetime import datetime

import pandas as pd
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.config import load_settings
from app.repositories.recognition_repo import RecognitionRepository
from app.models.face import Person, FaceSample
from app.models.unknown import UnknownFaceLog

class ExportService:
    def __init__(self):
        self.settings = load_settings()
        self.repo = RecognitionRepository()

    def recognition_dataframe(
        self,
        db: Session,
        start: datetime | None = None,
        end: datetime | None = None,
        mood: str | None = None,
        is_unknown: bool | None = None,
        person_name: str | None = None,
        sort: str | None = None,
    ) -> pd.DataFrame:
        logs, _total = self.repo.filtered_logs(
            db,
            start=start,
            end=end,
            mood=mood,
            is_unknown=is_unknown,
            person_name=person_name,
            sort=sort,
            limit=self.settings.export_max_rows,
            offset=0,
        )
        rows = []
        for log in logs:
            rows.append({
                "id": log.id,
                "person_id": log.person_id,
                "person_name": log.person_name,
                "source_type": log.source_type,
                "source_ref": log.source_ref,
                "confidence": log.confidence,
                "distance": log.distance,
                "is_unknown": log.is_unknown,
                "frame_index": log.frame_index,
                "mood": log.mood,
                "mood_scores_json": log.mood_scores_json,
                "liveness_score": log.liveness_score,
                "tracking_id": log.tracking_id,
                "is_enhanced": log.is_enhanced,
                "snapshot_path": log.snapshot_path,
                "quality_score": log.quality_score,
                "low_light_score": log.low_light_score,
                "pose_score": log.pose_score,
                "size_score": log.size_score,
                "occurred_at": log.occurred_at.isoformat() if log.occurred_at else None,
            })
        return pd.DataFrame(rows)

    def persons_dataframe(
        self,
        db: Session,
        name: str | None = None,
        department: str | None = None,
        is_active: bool | None = None,
    ) -> pd.DataFrame:
        stmt = (
            select(Person, func.count(FaceSample.id).label("sample_count"))
            .outerjoin(FaceSample, FaceSample.person_id == Person.id)
            .group_by(Person.id)
            .order_by(Person.created_at.desc())
            .limit(self.settings.export_max_rows)
        )
        if name:
            stmt = stmt.where(Person.full_name.ilike(f"%{name}%"))
        if department:
            stmt = stmt.where(Person.department.ilike(f"%{department}%"))
        if is_active is not None:
            stmt = stmt.where(Person.is_active.is_(is_active))

        rows = []
        for person, sample_count in db.execute(stmt).all():
            rows.append({
                "id": person.id,
                "person_code": person.person_code,
                "full_name": person.full_name,
                "email": person.email,
                "phone": person.phone,
                "department": person.department,
                "title": person.title,
                "age": person.age,
                "gender": person.gender,
                "tags": person.tags,
                "notes": person.notes,
                "is_active": person.is_active,
                "embedding_model": person.embedding_model,
                "duplicate_of": person.duplicate_of,
                "sample_count": int(sample_count or 0),
                "created_at": person.created_at.isoformat() if person.created_at else None,
            })
        return pd.DataFrame(rows)

    def unknowns_dataframe(
        self,
        db: Session,
        start: datetime | None = None,
        end: datetime | None = None,
        mood: str | None = None,
        is_reviewed: bool | None = None,
    ) -> pd.DataFrame:
        stmt = select(UnknownFaceLog).order_by(UnknownFaceLog.timestamp.desc()).limit(self.settings.export_max_rows)
        if start:
            stmt = stmt.where(UnknownFaceLog.timestamp >= start)
        if end:
            stmt = stmt.where(UnknownFaceLog.timestamp <= end)
        if mood:
            stmt = stmt.where(UnknownFaceLog.mood == mood)
        if is_reviewed is not None:
            stmt = stmt.where(UnknownFaceLog.is_reviewed.is_(is_reviewed))

        rows = []
        for log in db.scalars(stmt).all():
            rows.append({
                "id": log.id,
                "timestamp": log.timestamp.isoformat() if log.timestamp else None,
                "source_type": log.source_type,
                "source_ref": log.source_ref,
                "snapshot_path": log.snapshot_path,
                "confidence": log.confidence,
                "mood": log.mood,
                "mood_scores_json": log.mood_scores_json,
                "liveness_score": log.liveness_score,
                "is_reviewed": log.is_reviewed,
                "registered_as_person_id": log.registered_as_person_id,
                "cluster_id": log.cluster_id,
            })
        return pd.DataFrame(rows)

    def export_csv_bytes(
        self,
        db: Session,
        start: datetime | None = None,
        end: datetime | None = None,
        mood: str | None = None,
        is_unknown: bool | None = None,
        person_name: str | None = None,
        sort: str | None = None,
    ) -> bytes:
        return self.recognition_dataframe(
            db,
            start=start,
            end=end,
            mood=mood,
            is_unknown=is_unknown,
            person_name=person_name,
            sort=sort,
        ).to_csv(index=False).encode("utf-8")

    def export_xlsx_bytes(
        self,
        db: Session,
        start: datetime | None = None,
        end: datetime | None = None,
        mood: str | None = None,
        is_unknown: bool | None = None,
        person_name: str | None = None,
        sort: str | None = None,
    ) -> bytes:
        buffer = BytesIO()
        self.recognition_dataframe(
            db,
            start=start,
            end=end,
            mood=mood,
            is_unknown=is_unknown,
            person_name=person_name,
            sort=sort,
        ).to_excel(buffer, index=False)
        return buffer.getvalue()

    def export_persons_csv_bytes(
        self,
        db: Session,
        name: str | None = None,
        department: str | None = None,
        is_active: bool | None = None,
    ) -> bytes:
        return self.persons_dataframe(db, name=name, department=department, is_active=is_active).to_csv(index=False).encode("utf-8")

    def export_persons_xlsx_bytes(
        self,
        db: Session,
        name: str | None = None,
        department: str | None = None,
        is_active: bool | None = None,
    ) -> bytes:
        buffer = BytesIO()
        self.persons_dataframe(db, name=name, department=department, is_active=is_active).to_excel(buffer, index=False)
        return buffer.getvalue()

    def export_unknowns_csv_bytes(
        self,
        db: Session,
        start: datetime | None = None,
        end: datetime | None = None,
        mood: str | None = None,
        is_reviewed: bool | None = None,
    ) -> bytes:
        return self.unknowns_dataframe(db, start=start, end=end, mood=mood, is_reviewed=is_reviewed).to_csv(index=False).encode("utf-8")

    def export_unknowns_xlsx_bytes(
        self,
        db: Session,
        start: datetime | None = None,
        end: datetime | None = None,
        mood: str | None = None,
        is_reviewed: bool | None = None,
    ) -> bytes:
        buffer = BytesIO()
        self.unknowns_dataframe(db, start=start, end=end, mood=mood, is_reviewed=is_reviewed).to_excel(buffer, index=False)
        return buffer.getvalue()
