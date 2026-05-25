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
        self._smoothing_cache: dict[str, list[int | None]] = {} # session_id -> list of person_ids
        self._smoothing_window = 10

    def cleanup_session(self, session_id: str) -> None:
        """Called when a websocket connection closes to prevent memory leaks."""
        self._smoothing_cache.pop(session_id, None)
        # We could also cleanup cooldowns here if we wanted to be rigorous,
        # but the cooldown keys append the person_id, so it's a bit harder to find all of them.
        # Periodic cleanup handles cooldowns anyway.

    def _get_smoothed_match(self, session_id: str, current_person_id: int | None) -> int | None:
        if session_id not in self._smoothing_cache:
            self._smoothing_cache[session_id] = []
        
        cache = self._smoothing_cache[session_id]
        cache.append(current_person_id)
        if len(cache) > self._smoothing_window:
            cache.pop(0)
            
        # Majority voting
        from collections import Counter
        counts = Counter(cache)
        # Require a clear majority (e.g., 60% of current buffer) to confirm identity
        top_id, count = counts.most_common(1)[0]
        threshold = max(1, int(len(cache) * 0.6))
        if count >= threshold:
            return top_id
        return None # Fallback to Unknown if no clear winner

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
        """Build FAISS index if not built or if count changed."""
        from sqlalchemy import func
        from app.models.face import FaceEmbedding, Person
        
        # We only care about embeddings matching the current model
        current_model = self.face_service.embedder.model_name
        count = db.query(FaceEmbedding).join(Person).filter(Person.embedding_model == current_model).count()
        
        if not self._index_built or getattr(self, "_last_count", -1) != count:
            self.face_service.rebuild_index(db)
            self._index_built = True
            self._last_count = count

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
        
        # Apply smoothing to the primary match (assuming single face for now for simplicity, 
        # or we could use a more complex tracker for multiple faces).
        # For simplicity, we smooth based on the session_id and the best match found.
        if matches:
            # We sort by confidence to get the best one
            matches.sort(key=lambda x: x.confidence, reverse=True)
            best_match = matches[0]
            
            smoothed_id = self._get_smoothed_match(session_id, best_match.person_id if not best_match.is_unknown else None)
            
            # If smoothing says this should be someone else or unknown
            if smoothed_id is None and not best_match.is_unknown:
                # Downgrade to unknown if not enough consensus
                best_match.is_unknown = True
                best_match.full_name = "Unknown"
                best_match.person_id = None
                best_match.person_code = None
            elif smoothed_id is not None and (best_match.is_unknown or best_match.person_id != smoothed_id):
                # Upgrade to known if consensus exists
                # We need to fetch the person info from registry
                for item in self.face_service.pipeline._meta:
                    if item["person_id"] == smoothed_id:
                        best_match.person_id = item["person_id"]
                        best_match.person_code = item["person_code"]
                        best_match.full_name = item["full_name"]
                        best_match.is_unknown = False
                        best_match.confidence = max(best_match.confidence, 0.5) # boost confidence slightly
                        break

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
