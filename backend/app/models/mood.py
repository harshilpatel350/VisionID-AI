from __future__ import annotations
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

class MoodRecord(Base):
    __tablename__ = "mood_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    person_id: Mapped[int | None] = mapped_column(ForeignKey("persons.id", ondelete="CASCADE"), nullable=True, index=True)
    unknown_face_id: Mapped[int | None] = mapped_column(ForeignKey("unknown_face_logs.id", ondelete="CASCADE"), nullable=True, index=True)
    
    mood: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    mood_scores_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    
    source_type: Mapped[str] = mapped_column(String(40), nullable=False)
    source_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)

    person = relationship("Person")
    unknown_face = relationship("UnknownFaceLog")

class SessionHistory(Base):
    __tablename__ = "session_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    
    total_faces_detected: Mapped[int] = mapped_column(Integer, default=0)
    unique_persons_seen: Mapped[int] = mapped_column(Integer, default=0)
    unknown_count: Mapped[int] = mapped_column(Integer, default=0)
    
    mood_distribution_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
