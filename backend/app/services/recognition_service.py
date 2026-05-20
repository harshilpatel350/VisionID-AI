from __future__ import annotations
import base64
from pathlib import Path
import time

import cv2
from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.ai.pipeline import FacePipeline
from app.config import load_settings
from app.models.recognition import RecognitionLog
from app.repositories.recognition_repo import RecognitionRepository
from app.services.face_service import FaceService
from app.utils.files import unique_filename

class RecognitionService:
    def __init__(self):
        self.face_service = FaceService()
        self.rec_repo = RecognitionRepository()
        self.settings = load_settings()
        self.cooldowns: dict[str, float] = {}
        self._index_built = False

    def _cooldown_key(self, session_id: str, person_id: int | None, is_unknown: bool) -> str:
        return f"{session_id}:{'unknown' if is_unknown else person_id}"

    def _allow_log(self, session_id: str, person_id: int | None, is_unknown: bool) -> bool:
        key = self._cooldown_key(session_id, person_id, is_unknown)
        now = time.time()
        last = self.cooldowns.get(key, 0.0)
        if now - last < self.settings.recognition_cooldown_seconds:
            return False
        self.cooldowns[key] = now
        return True

    def _ensure_index(self, db: Session) -> None:
        """Build FAISS index once, not every frame."""
        if not self._index_built:
            self.face_service.rebuild_index(db)
            self._index_built = True

    def invalidate_index(self) -> None:
        """Call when persons/embeddings change to force a rebuild."""
        self._index_built = False

    def process_image_upload(self, db: Session, upload: UploadFile, source_ref: str | None = None):
        raw = upload.file.read()
        self._index_built = False  # force fresh index for uploads
        return self.face_service.recognize_image(db, raw, "image", source_ref)

    def process_video_upload(self, db: Session, upload: UploadFile):
        dest_dir = self.settings.abs_upload_dir / "videos"
        dest_dir.mkdir(parents=True, exist_ok=True)
        raw = upload.file.read()
        path = dest_dir / unique_filename("video", Path(upload.filename or ".mp4").suffix or ".mp4")
        path.write_bytes(raw)
        self._index_built = False
        matches = self.face_service.process_video_file(db, path, source_ref=str(path.relative_to(self.settings.base_dir)))
        return path, matches

    def process_batch_images(self, db: Session, uploads: list[UploadFile]):
        payload = []
        for upload in uploads:
            _, results = self.process_image_upload(db, upload, source_ref=upload.filename)
            payload.append({"file": upload.filename, "results": [m.__dict__ for m in results]})
        return payload

    def process_webcam_frame(self, db: Session, frame_b64: str, session_id: str):
        if "," in frame_b64:
            frame_b64 = frame_b64.split(",", 1)[1]
        raw = base64.b64decode(frame_b64)
        frame = self.face_service._load_image(raw)
        self._ensure_index(db)
        matches = self.face_service.pipeline.analyze_face(frame)
        # Skip encoding annotated image — frontend draws boxes via overlay canvas
        for m in matches:
            if not self._allow_log(session_id, m.person_id, m.is_unknown):
                continue
            log = RecognitionLog(
                person_id=m.person_id,
                person_name=m.full_name if not m.is_unknown else None,
                source_type="webcam",
                source_ref=session_id,
                confidence=m.confidence,
                distance=m.distance,
                is_unknown=m.is_unknown,
                frame_index=0,
                bounding_box_json=m.bbox,
                embedding_hash=m.embedding_hash,
            )
            db.add(log)
        db.flush()
        return None, matches, ""
