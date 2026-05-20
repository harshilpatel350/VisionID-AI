from __future__ import annotations
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Any

class ORMBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

class PersonCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=180)
    email: EmailStr | None = None
    phone: str | None = None
    department: str | None = None
    title: str | None = None
    notes: str | None = None

class PersonUpdate(PersonCreate):
    is_active: bool | None = None

class PersonOut(ORMBase):
    id: int
    person_code: str
    full_name: str
    email: str | None
    phone: str | None
    department: str | None
    title: str | None
    notes: str | None
    primary_image_path: str | None
    is_active: bool
    embedding_model: str
    duplicate_of: int | None
    sample_count: int = 0
    created_at: str | None = None

class FaceSampleOut(ORMBase):
    id: int
    person_id: int
    image_path: str
    crop_path: str | None
    quality_score: float
    blur_score: float
    low_light_score: float
    detection_score: float
    embedding_hash: str

class SearchRequest(BaseModel):
    similarity_threshold: float | None = None
    limit: int = 10

class SearchHit(BaseModel):
    person_id: int | None
    person_code: str | None
    full_name: str
    confidence: float
    distance: float
    is_unknown: bool
    bounding_box: dict[str, int] | None = None
    quality_score: float = 0

class DuplicateHit(BaseModel):
    source_person_id: int
    source_name: str
    duplicate_person_id: int
    duplicate_name: str
    similarity: float
