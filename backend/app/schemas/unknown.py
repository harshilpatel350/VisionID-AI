from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class UnknownFaceBase(BaseModel):
    source_type: str
    source_ref: str | None = None
    confidence: float
    mood: str | None = None
    liveness_score: float | None = None
    cluster_id: str | None = None

class UnknownFaceOut(UnknownFaceBase):
    id: int
    timestamp: datetime
    snapshot_path: str
    is_reviewed: bool
    registered_as_person_id: int | None = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class UnknownFaceListResponse(BaseModel):
    items: list[UnknownFaceOut]
    total: int
    page: int
    size: int

class RegisterFromUnknownRequest(BaseModel):
    full_name: str
    person_code: str | None = None
    department: str | None = None
    title: str | None = None
    age: int | None = None
    gender: str | None = None
    tags: str | None = None
    notes: str | None = None

class UnknownSimilarityHit(BaseModel):
    id: int
    snapshot_path: str
    timestamp: datetime
    mood: str | None = None
    similarity: float

class UnknownSimilarityResponse(BaseModel):
    items: list[UnknownSimilarityHit]
