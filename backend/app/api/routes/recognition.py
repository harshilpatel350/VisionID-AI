from __future__ import annotations
from fastapi import APIRouter, Depends, File, UploadFile, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.db.session import SessionLocal
from app.repositories.recognition_repo import RecognitionRepository
from app.services.recognition_service import RecognitionService

router = APIRouter(prefix="/recognition", tags=["recognition"])
svc = RecognitionService()
repo = RecognitionRepository()

@router.post("/image")
def recognize_image(image: UploadFile = File(...), db: Session = Depends(get_db), user=Depends(require_roles("admin", "operator", "viewer"))):
    _, results = svc.process_image_upload(db, image, source_ref=image.filename)
    db.commit()
    return {"results": [r.__dict__ for r in results]}

@router.post("/batch")
def recognize_batch(images: list[UploadFile] = File(...), db: Session = Depends(get_db), user=Depends(require_roles("admin", "operator", "viewer"))):
    data = svc.process_batch_images(db, images)
    db.commit()
    return {"items": data}

@router.post("/video")
def recognize_video(video: UploadFile = File(...), db: Session = Depends(get_db), user=Depends(require_roles("admin", "operator"))):
    path, matches = svc.process_video_upload(db, video)
    db.commit()
    return {"video_path": str(path), "results": [m.__dict__ for m in matches]}

@router.get("/logs")
def logs(limit: int = Query(100, ge=1, le=500), db: Session = Depends(get_db), user=Depends(require_roles("admin", "operator", "viewer"))):
    items = repo.recent_logs(db, limit=limit)
    return [{
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

from fastapi.concurrency import run_in_threadpool

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
    await websocket.accept()
    host = websocket.client.host if websocket.client else "ws"
    print(f"Client connected to Live AI: {host}")
    try:
        while True:
            try:
                payload = await websocket.receive_text()
                if not payload:
                    continue
                
                _annotated, logs, jpeg_b64 = await run_in_threadpool(_process_frame_sync, payload, host)
                
                await websocket.send_json({
                    "type": "frame",
                    "image": jpeg_b64,
                    "logs": [m.__dict__ for m in logs],
                })
            except WebSocketDisconnect:
                raise
            except Exception as e:
                import traceback
                err_str = traceback.format_exc()
                print(f"Error processing frame for {host}: {e}\n{err_str}")
                try:
                    await websocket.send_json({"type": "error", "message": str(e)})
                except Exception as send_err:
                    print(f"Failed to send error to client: {send_err}")
                    break
    except WebSocketDisconnect:
        print(f"Client disconnected: {host}")
    except Exception as e:
        print(f"WebSocket session error for {host}: {e}")
