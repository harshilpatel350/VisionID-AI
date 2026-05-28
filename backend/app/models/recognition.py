from __future__ import annotations
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

class RecognitionLog(Base):
    __tablename__ = "recognition_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    person_id: Mapped[int | None] = mapped_column(ForeignKey("persons.id", ondelete="SET NULL"), nullable=True, index=True)
    person_name: Mapped[str | None] = mapped_column(String(180), nullable=True)
    source_type: Mapped[str] = mapped_column(String(40), nullable=False)
    source_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    distance: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    is_unknown: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    frame_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    bounding_box_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    embedding_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    mood: Mapped[str | None] = mapped_column(String(20), nullable=True)
    mood_scores_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    liveness_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    tracking_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_enhanced: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    snapshot_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    low_light_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    pose_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    size_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    person = relationship("Person")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    actor_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(80), nullable=False)
    entity_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)

    actor_user = relationship("User", back_populates="audit_logs")
