from __future__ import annotations
from io import BytesIO
from pathlib import Path

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import load_settings
from app.models.recognition import RecognitionLog

class ExportService:
    def __init__(self):
        self.settings = load_settings()

    def recognition_dataframe(self, db: Session) -> pd.DataFrame:
        logs = db.scalars(select(RecognitionLog).order_by(RecognitionLog.occurred_at.desc()).limit(self.settings.export_max_rows)).all()
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
                "occurred_at": log.occurred_at.isoformat() if log.occurred_at else None,
            })
        return pd.DataFrame(rows)

    def export_csv_bytes(self, db: Session) -> bytes:
        return self.recognition_dataframe(db).to_csv(index=False).encode("utf-8")

    def export_xlsx_bytes(self, db: Session) -> bytes:
        buffer = BytesIO()
        self.recognition_dataframe(db).to_excel(buffer, index=False)
        return buffer.getvalue()
