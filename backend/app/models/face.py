from __future__ import annotations
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, LargeBinary, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

class Person(Base):
    __tablename__ = "persons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    person_code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    department: Mapped[str | None] = mapped_column(String(120), nullable=True)
    title: Mapped[str | None] = mapped_column(String(120), nullable=True)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    gender: Mapped[str | None] = mapped_column(String(20), nullable=True)
    tags: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    primary_image_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    embedding_model: Mapped[str] = mapped_column(String(80), default="insightface_buffalo_l", nullable=False)
    duplicate_of: Mapped[int | None] = mapped_column(ForeignKey("persons.id", ondelete="SET NULL"), nullable=True)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    created_by_user = relationship("User", back_populates="created_persons", foreign_keys=[created_by])
    samples = relationship("FaceSample", back_populates="person", cascade="all, delete-orphan")
    embeddings = relationship("FaceEmbedding", back_populates="person", cascade="all, delete-orphan")
    duplicate_parent = relationship("Person", remote_side=[id])

class FaceSample(Base):
    __tablename__ = "face_samples"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    person_id: Mapped[int] = mapped_column(ForeignKey("persons.id", ondelete="CASCADE"), nullable=False, index=True)
    image_path: Mapped[str] = mapped_column(String(512), nullable=False)
    crop_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    quality_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    blur_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    low_light_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    detection_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    embedding_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    person = relationship("Person", back_populates="samples")
    embedding = relationship("FaceEmbedding", back_populates="sample", uselist=False, cascade="all, delete-orphan")

class FaceEmbedding(Base):
    __tablename__ = "face_embeddings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sample_id: Mapped[int] = mapped_column(ForeignKey("face_samples.id", ondelete="CASCADE"), nullable=False, index=True)
    person_id: Mapped[int] = mapped_column(ForeignKey("persons.id", ondelete="CASCADE"), nullable=False, index=True)
    embedding_dim: Mapped[int] = mapped_column(Integer, nullable=False)
    embedding_vector: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    similarity_threshold: Mapped[float] = mapped_column(Float, default=0.45, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    sample = relationship("FaceSample", back_populates="embedding")
    person = relationship("Person", back_populates="embeddings")
