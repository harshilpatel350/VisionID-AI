import time
import cv2
import numpy as np
from pathlib import Path
from sqlalchemy.orm import Session
from app.repositories.unknown_repo import UnknownRepository
from app.config import load_settings

class UnknownService:
    def __init__(self):
        self.repo = UnknownRepository()
        self.settings = load_settings()
        
    def _save_snapshot(self, face_crop_bgr: np.ndarray) -> str:
        out_dir = self.settings.abs_unknown_face_dir
        out_dir.mkdir(parents=True, exist_ok=True)
        fname = f"unknown_{int(time.time() * 1000)}.jpg"
        path = out_dir / fname
        cv2.imwrite(str(path), face_crop_bgr)
        return str(path.relative_to(self.settings.base_dir))

    def log_unknown_face(
        self, 
        db: Session, 
        face_crop_bgr: np.ndarray, 
        embedding: np.ndarray,
        embedding_hash: str,
        bbox: dict,
        confidence: float,
        mood: str | None,
        mood_scores: dict | None,
        liveness_score: float | None,
        source_type: str,
        source_ref: str | None = None
    ):
        snapshot_path = self._save_snapshot(face_crop_bgr) if self.settings.save_unknown_snapshots else ""
        
        data = {
            "source_type": source_type,
            "source_ref": source_ref,
            "snapshot_path": snapshot_path,
            "embedding_vector": embedding.tobytes(),
            "embedding_hash": embedding_hash,
            "confidence": confidence,
            "mood": mood,
            "mood_scores_json": mood_scores,
            "liveness_score": liveness_score,
            "bbox_json": bbox
        }
        return self.repo.create(db, data)

    def find_similar(self, db: Session, log_id: int, top_k: int | None = None, min_similarity: float | None = None) -> list[dict]:
        target = self.repo.get_by_id(db, log_id)
        if not target:
            return []
        vec = np.frombuffer(target.embedding_vector, dtype=np.float32)
        vec = vec / (np.linalg.norm(vec) + 1e-6)

        top_k = top_k or self.settings.unknown_similarity_top_k
        min_similarity = min_similarity or self.settings.unknown_similarity_threshold

        items, _total = self.repo.list_paginated(db, page=1, size=self.settings.export_max_rows)
        hits = []
        for item in items:
            if item.id == log_id:
                continue
            other = np.frombuffer(item.embedding_vector, dtype=np.float32)
            other = other / (np.linalg.norm(other) + 1e-6)
            sim = float(np.dot(vec, other))
            if sim >= min_similarity:
                hits.append({
                    "id": item.id,
                    "snapshot_path": item.snapshot_path,
                    "timestamp": item.timestamp,
                    "mood": item.mood,
                    "similarity": sim,
                })

        hits.sort(key=lambda h: h["similarity"], reverse=True)
        return hits[:top_k]
        
    def list_paginated(self, db: Session, page: int, size: int, is_reviewed: bool | None = None):
        return self.repo.list_paginated(db, page, size, is_reviewed)
        
    def mark_reviewed(self, db: Session, log_id: int):
        log = self.repo.get_by_id(db, log_id)
        if log:
            log.is_reviewed = True
            self.repo.update(db, log)
        return log
