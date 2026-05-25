from __future__ import annotations
import logging
import uuid
import traceback
from fastapi import APIRouter, Depends, File, UploadFile, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.orm import Session
from fastapi.concurrency import run_in_threadpool

from app.api.deps import get_db, require_roles
from app.db.session import SessionLocal
from app.repositories.recognition_repo import RecognitionRepository
from app.services.recognition_service import RecognitionService
from app.schemas.response_envelope import ResponseEnvelope, PaginatedResponse, PaginatedMeta
from app.schemas.recognition import RecognitionLogOut
from app.utils.validators import validate_image_upload, validate_video_upload, validate_pagination
from app.core.exceptions import AuthenticationError

router = APIRouter(prefix="/recognition", tags=["recognition"])
svc = RecognitionService()
repo = RecognitionRepository()
logger = logging.getLogger("visionid.ws")

@router.post("/image", response_model=ResponseEnvelope[list[dict]])
def recognize_image(image: UploadFile = File(...), db: Session = Depends(get_db), user=Depends(require_roles("admin", "operator", "viewer"))):
    validate_image_upload(image)
    _, results = svc.process_image_upload(db, image, source_ref=image.filename)
    db.commit()
    return ResponseEnvelope(data=[r.__dict__ for r in results])

@router.post("/batch", response_model=ResponseEnvelope[list[dict]])
def recognize_batch(images: list[UploadFile] = File(...), db: Session = Depends(get_db), user=Depends(require_roles("admin", "operator", "viewer"))):
    for image in images:
        validate_image_upload(image)
    data = svc.process_batch_images(db, images)
    db.commit()
    return ResponseEnvelope(data=data)

@router.post("/video", response_model=ResponseEnvelope[dict])
def recognize_video(video: UploadFile = File(...), db: Session = Depends(get_db), user=Depends(require_roles("admin", "operator"))):
    validate_video_upload(video)
    path, matches = svc.process_video_upload(db, video)
    db.commit()
    return ResponseEnvelope(data={"video_path": str(path), "results": [m.__dict__ for m in matches]})

@router.get("/logs", response_model=PaginatedResponse[RecognitionLogOut])
def logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db), 
    user=Depends(require_roles("admin", "operator", "viewer"))
):
    offset, limit = validate_pagination(page, page_size, max_page_size=500)
    # Note: repo.recent_logs needs pagination support, I'll update it later or just slice here for now.
    # To be precise, I should update the repo. Let's slice for now to match interface, we'll fix repo in Phase 5.
    items = repo.recent_logs(db, limit=limit, offset=offset)
    total = repo.count_total_logs(db)
    
    data = [{
        "id": i.id,
        "person_id": i.person_id,
        "person_name": i.person_name,
        "source_type": i.source_type,
        "source_ref": i.source_ref,
        "confidence": i.confidence,
        "distance": i.distance,
        "is_unknown": i.is_unknown,
        "frame_index": i.frame_index,
        "bounding_box_json": i.bounding_box_json,
        "embedding_hash": i.embedding_hash,
        "occurred_at": i.occurred_at.isoformat() if i.occurred_at else None,
    } for i in items]
    
    meta = PaginatedMeta(
        total=total,
        page=page,
        page_size=limit,
        has_more=(offset + limit) < total
    )
    return PaginatedResponse(data=data, meta=meta)


def _process_frame_sync(payload: str, host: str):
    db = SessionLocal()
    try:
        res = svc.process_webcam_frame(db, payload, session_id=host)
        db.commit()
        return res
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@router.websocket("/ws")
async def webcam_socket(websocket: WebSocket):
    # Authenticate via query param
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008, reason="Missing token")
        return
        
    try:
        from app.core.security import decode_token
        decode_token(token)
    except Exception:
        await websocket.close(code=1008, reason="Invalid token")
        return

    await websocket.accept()
    session_id = str(uuid.uuid4())
    logger.info("Client connected to Live AI: %s", session_id)
    
    try:
        while True:
            try:
                payload = await websocket.receive_text()
                if not payload:
                    continue
                
                _annotated, matches, jpeg_b64 = await run_in_threadpool(_process_frame_sync, payload, session_id)
                
                await websocket.send_json({
                    "type": "frame",
                    "image": jpeg_b64,
                    "logs": [m.__dict__ for m in matches],
                })
            except WebSocketDisconnect:
                raise
            except Exception as e:
                err_str = traceback.format_exc()
                logger.error("Error processing frame for %s: %s\n%s", session_id, e, err_str)
                try:
                    await websocket.send_json({"type": "error", "message": str(e)})
                except Exception as send_err:
                    logger.error("Failed to send error to client %s: %s", session_id, send_err)
                    break
    except WebSocketDisconnect:
        logger.info("Client disconnected: %s", session_id)
    except Exception as e:
        logger.error("WebSocket session error for %s: %s", session_id, e)
    finally:
        svc.cleanup_session(session_id)
