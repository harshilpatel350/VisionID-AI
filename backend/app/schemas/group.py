from pydantic import BaseModel

class GroupFaceResult(BaseModel):
    person_id: int | None = None
    full_name: str
    is_unknown: bool
    confidence: float
    bbox: dict[str, int]
    mood: str | None = None
    mood_scores: dict[str, float] | None = None

class GroupSummary(BaseModel):
    total_faces: int
    known_faces: int
    unknown_faces: int
    mood_distribution: dict[str, int]

class GroupAnalysisResult(BaseModel):
    summary: GroupSummary
    faces: list[GroupFaceResult]
    annotated_image_url: str | None = None
