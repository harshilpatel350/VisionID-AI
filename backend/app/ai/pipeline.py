from __future__ import annotations
import json
import logging
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

import cv2
import faiss
import numpy as np

from app.ai.detector import FaceDetector
from app.ai.embedder import FaceEmbedder
from app.ai.quality import face_quality, blur_score, low_light_score
from app.ai.emotion import EmotionDetector
from app.ai.liveness import LivenessDetector
from app.ai.enhancement import LowLightEnhancer
from app.config import load_settings

logger = logging.getLogger("visionid")

@dataclass
class RecognitionMatch:
    person_id: int | None
    person_code: str | None
    full_name: str
    confidence: float
    distance: float
    is_unknown: bool
    bbox: dict[str, int]
    quality_score: float
    blur_score: float
    low_light_score: float
    embedding_hash: str | None = None
    department: str | None = None
    title: str | None = None
    email: str | None = None
    phone: str | None = None
    mood: str | None = None
    mood_scores: dict[str, float] | None = None
    liveness_score: float | None = None
    liveness_suspicious: bool = False
    tracking_id: int | None = None
    is_enhanced: bool = False

class FacePipeline:
    def __init__(self):
        self.settings = load_settings()
        self.detector = FaceDetector()
        self.embedder = FaceEmbedder()
        self.emotion_detector = EmotionDetector()
        self.liveness_detector = LivenessDetector(threshold=0.5)
        self.enhancer = LowLightEnhancer()
        self.index = None
        self._vectors: np.ndarray | None = None
        self._meta: list[dict[str, Any]] = []

    def set_registry(self, embeddings: list[dict[str, Any]]) -> None:
        if not embeddings:
            self._meta = []
            self.index = None
            self._vectors = None
            return
            
        first_dim = len(embeddings[0]["vector"])
        valid_embeddings = []
        for e in embeddings:
            if len(e["vector"]) == first_dim:
                valid_embeddings.append(e)
        
        self._meta = valid_embeddings
        if not valid_embeddings:
            self.index = None
            self._vectors = None
            return

        vectors = np.asarray([e["vector"] for e in valid_embeddings], dtype=np.float32)
        vectors = self._normalize(vectors)
        self._vectors = vectors
        dim = vectors.shape[1]
        index = faiss.IndexFlatIP(dim)
        index.add(vectors)
        self.index = index

    def _index_dir(self) -> Path:
        d = self.settings.base_dir / "storage" / "faiss"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def save_index(self) -> None:
        if self.index is None or not self._meta:
            return
        idx_dir = self._index_dir()
        try:
            faiss.write_index(self.index, str(idx_dir / "face.index"))
            serializable = []
            for m in self._meta:
                entry = {k: v for k, v in m.items() if k != "vector"}
                serializable.append(entry)
            (idx_dir / "meta.json").write_text(json.dumps(serializable, default=str), encoding="utf-8")
            logger.info("FAISS index saved to disk (%d vectors)", self.index.ntotal)
        except Exception as e:
            logger.error("Failed to save FAISS index: %s", e)

    def load_index(self) -> bool:
        idx_dir = self._index_dir()
        idx_path = idx_dir / "face.index"
        meta_path = idx_dir / "meta.json"
        if not idx_path.exists() or not meta_path.exists():
            return False
        try:
            self.index = faiss.read_index(str(idx_path))
            raw_meta = json.loads(meta_path.read_text(encoding="utf-8"))
            self._meta = raw_meta
            self._vectors = None
            logger.info("FAISS index loaded from disk (%d vectors)", self.index.ntotal)
            return True
        except Exception as e:
            logger.error("Failed to load FAISS index from disk: %s", e)
            self.index = None
            self._meta = []
            return False

    def invalidate_disk_index(self) -> None:
        idx_dir = self._index_dir()
        for f in ("face.index", "meta.json"):
            p = idx_dir / f
            if p.exists():
                p.unlink()
        logger.info("Disk FAISS index invalidated")

    def _normalize(self, vectors: np.ndarray) -> np.ndarray:
        norms = np.linalg.norm(vectors, axis=1, keepdims=True) + 1e-6
        return vectors / norms

    def analyze_face(self, image_bgr: np.ndarray, is_enhanced: bool = False) -> list[RecognitionMatch]:
        detected_faces = self.detector.detect(image_bgr)
        results: list[RecognitionMatch] = []
        for face in detected_faces:
            face_crop = self.detector.align(image_bgr, face)
            
            # Embed
            emb_res = self.embedder.extract(image_bgr, face)
            if emb_res is None:
                continue

            match_data = self._match_and_find(emb_res)

            # Mirror fallback
            if match_data["is_unknown"]:
                flipped = cv2.flip(face_crop, 1)
                emb_flipped = self.embedder.extract(flipped)
                if emb_flipped:
                    match_flipped = self._match_and_find(emb_flipped)
                    if not match_flipped["is_unknown"]:
                        match_data = match_flipped
                        
            # Analyze Emotion
            mood, mood_scores = self.emotion_detector.detect(face_crop)
            
            # Analyze Liveness
            liveness_result = self.liveness_detector.score(face_crop)

            results.append(
                RecognitionMatch(
                    person_id=match_data["person_id"],
                    person_code=match_data["person_code"],
                    full_name=match_data["full_name"],
                    confidence=match_data["confidence"],
                    distance=match_data["distance"],
                    is_unknown=match_data["is_unknown"],
                    bbox={"x1": int(face.bbox[0]), "y1": int(face.bbox[1]), "x2": int(face.bbox[2]), "y2": int(face.bbox[3])},
                    quality_score=float(face_quality(face_crop)),
                    blur_score=float(blur_score(image_bgr)),
                    low_light_score=float(low_light_score(image_bgr)),
                    embedding_hash=match_data["embedding_hash"],
                    department=match_data["department"] if not match_data["is_unknown"] else None,
                    title=match_data["title"] if not match_data["is_unknown"] else None,
                    email=match_data["email"] if not match_data["is_unknown"] else None,
                    phone=match_data["phone"] if not match_data["is_unknown"] else None,
                    mood=mood,
                    mood_scores=mood_scores,
                    liveness_score=liveness_result["liveness_score"],
                    liveness_suspicious=liveness_result["is_suspicious"],
                    is_enhanced=is_enhanced,
                )
            )
        return results

    def analyze_face_enhanced(self, image_bgr: np.ndarray) -> list[RecognitionMatch]:
        """Auto-enhances if low light is detected, then analyzes."""
        if self.enhancer.is_low_light(image_bgr):
            enhanced = self.enhancer.enhance(image_bgr)
            return self.analyze_face(enhanced, is_enhanced=True)
        return self.analyze_face(image_bgr, is_enhanced=False)

    def _match_and_find(self, emb_res: Any) -> dict[str, Any]:
        res = {
            "person_id": None, "person_code": None, "full_name": "Unknown",
            "confidence": 0.0, "distance": 1.0, "is_unknown": True,
            "department": None, "title": None, "email": None, "phone": None,
            "embedding_hash": emb_res.hash_hex
        }

        if self.index is not None and self._meta:
            vec = emb_res.embedding.astype(np.float32).reshape(1, -1)
            vec = self._normalize(vec)
            
            if self.index.ntotal > 0 and vec.shape[1] == self.index.d:
                try:
                    scores, idxs = self.index.search(vec, k=min(5, len(self._meta)))
                    best_score = float(scores[0][0]) if scores.size else 0.0
                    best_idx = int(idxs[0][0]) if idxs.size else -1
                    res["distance"] = float(1.0 - best_score)
                    
                    threshold = self.settings.recognition_threshold
                    if self.embedder.model_name == "opencv_histogram":
                        threshold = max(threshold, 0.82)
                        
                    res["confidence"] = max(0.0, min(1.0, best_score))
                    if best_idx >= 0 and best_score >= threshold:
                        item = self._meta[best_idx]
                        res["person_id"] = int(item["person_id"])
                        res["person_code"] = str(item["person_code"])
                        res["full_name"] = str(item["full_name"])
                        res["is_unknown"] = False
                        res["department"] = item.get("department")
                        res["title"] = item.get("title")
                        res["email"] = item.get("email")
                        res["phone"] = item.get("phone")
                except Exception as e:
                    print(f"Error searching index: {e}")
        return res

