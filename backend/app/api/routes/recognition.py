from __future__ import annotations
import logging
from datetime import datetime
import uuid
import traceback
from fastapi import APIRouter, Depends, File, UploadFile, WebSocket, WebSocketDisconnect, Query, HTTPException
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
    start: str | None = Query(None),
    end: str | None = Query(None),
    mood: str | None = Query(None),
    is_unknown: bool | None = Query(None),
    person_name: str | None = Query(None),
    sort: str | None = Query("desc"),
    db: Session = Depends(get_db), 
    user=Depends(require_roles("admin", "operator", "viewer"))
):
    offset, limit = validate_pagination(page, page_size, max_page_size=500)
    start_dt = None
    end_dt = None
    try:
        if start:
            start_dt = datetime.fromisoformat(start)
        if end:
            end_dt = datetime.fromisoformat(end)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use ISO 8601.")

    items, total = repo.filtered_logs(
        db,
        start=start_dt,
        end=end_dt,
        mood=mood,
        is_unknown=is_unknown,
        person_name=person_name,
        sort=sort,
        limit=limit,
        offset=offset
    )
    
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
        "mood": i.mood,
        "mood_scores_json": i.mood_scores_json,
        "liveness_score": i.liveness_score,
        "tracking_id": i.tracking_id,
        "is_enhanced": i.is_enhanced,
        "snapshot_path": i.snapshot_path,
        "quality_score": i.quality_score,
        "low_light_score": i.low_light_score,
        "pose_score": i.pose_score,
        "size_score": i.size_score,
        "occurred_at": i.occurred_at.isoformat() if i.occurred_at else None,
    } for i in items]
    
    meta = PaginatedMeta(
        total=total,
        page=page,
        page_size=limit,
        has_more=(offset + limit) < total
    )
    return PaginatedResponse(data=data, meta=meta)


def _process_frame_sync(payload: str, host: str, enable_enhancement: bool):
    db = SessionLocal()
    try:
        res = svc.process_webcam_frame(db, payload, session_id=host, enable_enhancement=enable_enhancement)
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
    enhance_flag = websocket.query_params.get("enhance", "false").lower() == "true"
    logger.info("Client connected to Live AI: %s", session_id)
    
    try:
        while True:
            try:
                payload = await websocket.receive_text()
                if not payload:
                    continue
                
                _annotated, matches, jpeg_b64, meta = await run_in_threadpool(_process_frame_sync, payload, session_id, enhance_flag)
                
                await websocket.send_json({
                    "type": "frame",
                    "image": jpeg_b64,
                    "logs": [m.__dict__ for m in matches],
                    "meta": meta,
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
        db = SessionLocal()
        try:
            svc.cleanup_session(session_id, db)
        finally:
            db.close()
