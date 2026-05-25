from fastapi import APIRouter
from app.schemas.response_envelope import ResponseEnvelope

router = APIRouter(tags=["health"])

@router.get("/health", response_model=ResponseEnvelope[dict])
def health():
    return ResponseEnvelope(data={"status": "ok", "service": "VisionID AI"})
