from __future__ import annotations
import base64
from pathlib import Path
import time
from datetime import datetime

import cv2
from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.ai.pipeline import FacePipeline
from app.ai.tracker import FaceTracker
from app.config import load_settings
from app.models.recognition import RecognitionLog
from app.repositories.recognition_repo import RecognitionRepository
from app.services.face_service import FaceService
from app.services.unknown_service import UnknownService
from app.services.emotion_service import EmotionService
from app.utils.files import unique_filename

class RecognitionService:
    def __init__(self):
        self.face_service = FaceService()
        self.rec_repo = RecognitionRepository()
        self.unknown_service = UnknownService()
        self.emotion_service = EmotionService()
        self.settings = load_settings()
        self.cooldowns: dict[str, float] = {}
        self._index_built = False
        
        # Trackers per session
        self.trackers: dict[str, FaceTracker] = {}
        self.session_start_times: dict[str, datetime] = {}
        
        # Smoothing cache per tracking_id: {session_id: {track_id: list[person_id]}}
        self._smoothing_cache: dict[str, dict[int, list[int | None]]] = {}
        self._smoothing_window = 10

    def cleanup_session(self, db: Session, session_id: str) -> None:
        """Called when a websocket connection closes to prevent memory leaks and save session stats."""
        self.trackers.pop(session_id, None)
        self._smoothing_cache.pop(session_id, None)
        
        if session_id in self.session_start_times:
            # We could save session history here
            # (Implemented in analytics/mood phase later or directly in a background task)
            self.session_start_times.pop(session_id)

    def _get_or_create_tracker(self, session_id: str) -> FaceTracker:
        if session_id not in self.trackers:
            self.trackers[session_id] = FaceTracker()
            self.session_start_times[session_id] = datetime.now()
            self._smoothing_cache[session_id] = {}
        return self.trackers[session_id]

    def _get_smoothed_match(self, session_id: str, track_id: int, current_person_id: int | None) -> int | None:
        if session_id not in self._smoothing_cache:
            self._smoothing_cache[session_id] = {}
        if track_id not in self._smoothing_cache[session_id]:
            self._smoothing_cache[session_id][track_id] = []
            
        cache = self._smoothing_cache[session_id][track_id]
        cache.append(current_person_id)
        if len(cache) > self._smoothing_window:
            cache.pop(0)
            
        from collections import Counter
        counts = Counter(cache)
        top_id, count = counts.most_common(1)[0]
        threshold = max(1, int(len(cache) * 0.6))
        if count >= threshold:
            return top_id
        return None

    def _cooldown_key(self, session_id: str, person_id: int | None, track_id: int | None) -> str:
        return f"{session_id}:{track_id if track_id is not None else (person_id or 'unknown')}"

    def _allow_log(self, session_id: str, person_id: int | None, track_id: int | None) -> bool:
        key = self._cooldown_key(session_id, person_id, track_id)
        now = time.time()
        last = self.cooldowns.get(key, 0.0)
        if now - last < self.settings.recognition_cooldown_seconds:
            return False
        self.cooldowns[key] = now
        return True

    def _ensure_index(self, db: Session) -> None:
        from sqlalchemy import func
        from app.models.face import FaceEmbedding, Person
        
        current_model = self.face_service.embedder.model_name
        count = db.query(FaceEmbedding).join(Person).filter(Person.embedding_model == current_model).count()
        
        if not self._index_built or getattr(self, "_last_count", -1) != count:
            self.face_service.rebuild_index(db)
            self._index_built = True
            self._last_count = count

    def invalidate_index(self) -> None:
        self._index_built = False

    def process_image_upload(self, db: Session, upload: UploadFile, source_ref: str | None = None):
        raw = upload.file.read()
        self._index_built = False
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

    def process_webcam_frame(self, db: Session, frame_b64: str, session_id: str, enable_enhancement: bool = False):
        if "," in frame_b64:
            frame_b64 = frame_b64.split(",", 1)[1]
        raw = base64.b64decode(frame_b64)
        frame = self.face_service._load_image(raw)
        self._ensure_index(db)
        
        # 1. Analyze faces
        if enable_enhancement:
            matches = self.face_service.pipeline.analyze_face_enhanced(frame)
        else:
            matches = self.face_service.pipeline.analyze_face(frame)
            
        # 2. Track faces
        tracker = self._get_or_create_tracker(session_id)
        bboxes = [(m.bbox["x1"], m.bbox["y1"], m.bbox["x2"], m.bbox["y2"]) for m in matches]
        track_ids = tracker.update(bboxes)
        
        for i, match in enumerate(matches):
            match.tracking_id = track_ids[i]
            
            # 3. Smooth ID assignment using tracking
            smoothed_id = self._get_smoothed_match(session_id, match.tracking_id, match.person_id if not match.is_unknown else None)
            
            if smoothed_id is None and not match.is_unknown:
                match.is_unknown = True
                match.full_name = "Unknown"
                match.person_id = None
                match.person_code = None
            elif smoothed_id is not None and (match.is_unknown or match.person_id != smoothed_id):
                for item in self.face_service.pipeline._meta:
                    if item["person_id"] == smoothed_id:
                        match.person_id = item["person_id"]
                        match.person_code = item["person_code"]
                        match.full_name = item["full_name"]
                        match.is_unknown = False
                        match.confidence = max(match.confidence, 0.5)
                        break

            # 4. Log to DB
            if self._allow_log(session_id, match.person_id, match.tracking_id):
                # Log regular recognition
                log = RecognitionLog(
                    person_id=match.person_id,
                    person_name=match.full_name if not match.is_unknown else None,
                    source_type="webcam",
                    source_ref=session_id,
                    confidence=match.confidence,
                    distance=match.distance,
                    is_unknown=match.is_unknown,
                    frame_index=0,
                    bounding_box_json=match.bbox,
                    embedding_hash=match.embedding_hash,
                    mood=match.mood,
                    liveness_score=match.liveness_score,
                    tracking_id=match.tracking_id,
                    is_enhanced=match.is_enhanced
                )
                db.add(log)
                
                # Log unknown face details
                if match.is_unknown:
                    # We need the crop to save snapshot
                    face_crop = self.face_service.pipeline.detector.align(frame, self.face_service.pipeline.detector.detect(frame)[i])
                    # Re-embed to get numpy array
                    emb_res = self.face_service.pipeline.embedder.extract(frame, self.face_service.pipeline.detector.detect(frame)[i])
                    if emb_res:
                        self.unknown_service.log_unknown_face(
                            db, face_crop, emb_res.embedding, match.embedding_hash,
                            match.bbox, match.confidence, match.mood, match.mood_scores,
                            match.liveness_score, "webcam", session_id
                        )
                        
        db.flush()
        return None, matches, ""
