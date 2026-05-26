from __future__ import annotations
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text, LargeBinary, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

class UnknownFaceLog(Base):
    __tablename__ = "unknown_face_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)
    source_type: Mapped[str] = mapped_column(String(40), nullable=False) # webcam, group_photo
    source_ref: Mapped[str | None] = mapped_column(String(255), nullable=True) # session_id or filename
    
    snapshot_path: Mapped[str] = mapped_column(String(512), nullable=False)
    embedding_vector: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    embedding_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    mood: Mapped[str | None] = mapped_column(String(20), nullable=True)
    mood_scores_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    liveness_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    bbox_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    
    is_reviewed: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    registered_as_person_id: Mapped[int | None] = mapped_column(ForeignKey("persons.id", ondelete="SET NULL"), nullable=True)
    cluster_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True) # for grouping similar unknowns
    
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    registered_person = relationship("Person")
