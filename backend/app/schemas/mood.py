from datetime import datetime
from pydantic import BaseModel, ConfigDict

class MoodRecordBase(BaseModel):
    mood: str
    source_type: str
    source_ref: str | None = None

class MoodRecordOut(MoodRecordBase):
    id: int
    person_id: int | None = None
    unknown_face_id: int | None = None
    timestamp: datetime
    
    model_config = ConfigDict(from_attributes=True)

class MoodStatsResponse(BaseModel):
    mood_distribution: dict[str, int]
    total_records: int

class SessionHistoryOut(BaseModel):
    id: int
    session_id: str
    started_at: datetime
    ended_at: datetime | None = None
    total_faces_detected: int
    unique_persons_seen: int
    unknown_count: int
    mood_distribution_json: dict | None = None
    
    model_config = ConfigDict(from_attributes=True)
