from pydantic import BaseModel
from typing import Any

class RecognitionLogOut(BaseModel):
    id: int
    person_id: int | None
    person_name: str | None
    source_type: str
    source_ref: str | None
    confidence: float
    distance: float
    is_unknown: bool
    frame_index: int
    bounding_box_json: dict[str, Any] | None
    embedding_hash: str | None
    mood: str | None = None
    liveness_score: float | None = None
    tracking_id: int | None = None
    is_enhanced: bool = False
    occurred_at: str | None

class DashboardStats(BaseModel):
    total_persons: int
    total_samples: int
    total_recognitions: int
    unknown_detections: int
    active_users: int
    today_recognitions: int
    recent_unknowns: int
    recognition_rate: float
    avg_confidence: float
    top_persons: list[dict[str, Any]]
    daily_activity: list[dict[str, Any]]

class AnalyticsOverview(BaseModel):
    logs_by_day: list[dict[str, Any]]
    confidence_buckets: list[dict[str, Any]]
    source_breakdown: list[dict[str, Any]]
    unknown_trend: list[dict[str, Any]]
