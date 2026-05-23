from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any

import cv2
import faiss
import numpy as np

from app.ai.detector import FaceDetector
from app.ai.embedder import FaceEmbedder
from app.ai.quality import face_quality, blur_score, low_light_score
from app.config import load_settings

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

class FacePipeline:
    def __init__(self):
        self.settings = load_settings()
        self.detector = FaceDetector()
        self.embedder = FaceEmbedder()
        self.index = None
        self._vectors: np.ndarray | None = None
        self._meta: list[dict[str, Any]] = []

    def set_registry(self, embeddings: list[dict[str, Any]]) -> None:
        if not embeddings:
            self._meta = []
            self.index = None
            self._vectors = None
            return
            
        # Ensure all vectors have the same dimension as the first one
        first_dim = len(embeddings[0]["vector"])
        valid_embeddings = []
        for e in embeddings:
            if len(e["vector"]) == first_dim:
                valid_embeddings.append(e)
            else:
                # Log or skip incompatible dimension
                pass
        
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

    def _normalize(self, vectors: np.ndarray) -> np.ndarray:
        norms = np.linalg.norm(vectors, axis=1, keepdims=True) + 1e-6
        return vectors / norms

    def analyze_face(self, image_bgr: np.ndarray) -> list[RecognitionMatch]:
        detected_faces = self.detector.detect(image_bgr)
        results: list[RecognitionMatch] = []
        for face in detected_faces:
            emb_res = self.embedder.extract(image_bgr, face)
            if emb_res is None:
                continue

            match_data = self._match_and_find(emb_res)

            # If unknown, try horizontal flip (mirroring robustness)
            if match_data["is_unknown"]:
                face_img = self.detector.align(image_bgr, face)
                flipped = cv2.flip(face_img, 1)
                emb_flipped = self.embedder.extract(flipped)
                if emb_flipped:
                    match_flipped = self._match_and_find(emb_flipped)
                    if not match_flipped["is_unknown"]:
                        match_data = match_flipped

            results.append(
                RecognitionMatch(
                    person_id=match_data["person_id"],
                    person_code=match_data["person_code"],
                    full_name=match_data["full_name"],
                    confidence=match_data["confidence"],
                    distance=match_data["distance"],
                    is_unknown=match_data["is_unknown"],
                    bbox={"x1": int(face.bbox[0]), "y1": int(face.bbox[1]), "x2": int(face.bbox[2]), "y2": int(face.bbox[3])},
                    quality_score=float(face_quality(self.detector.align(image_bgr, face))),
                    blur_score=float(blur_score(image_bgr)),
                    low_light_score=float(low_light_score(image_bgr)),
                    embedding_hash=match_data["embedding_hash"],
                    department=match_data["department"] if not match_data["is_unknown"] else None,
                    title=match_data["title"] if not match_data["is_unknown"] else None,
                    email=match_data["email"] if not match_data["is_unknown"] else None,
                    phone=match_data["phone"] if not match_data["is_unknown"] else None,
                )
            )
        return results

    def _match_and_find(self, emb_res: Any) -> dict[str, Any]:
        """Helper to match a single embedding against the registry."""
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
                        # Robust LBP+HOG (6x6) works well at 0.82
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

    def draw(self, image_bgr: np.ndarray, matches: list[RecognitionMatch]) -> np.ndarray:
        out = image_bgr.copy()
        for m in matches:
            box = m.bbox
            x1, y1, x2, y2 = box["x1"], box["y1"], box["x2"], box["y2"]
            color = (0, 255, 0) if not m.is_unknown else (0, 165, 255)
            cv2.rectangle(out, (x1, y1), (x2, y2), color, 2)
            
            label = f"{m.full_name}"
            if not m.is_unknown and m.person_code:
                label += f" ({m.person_code})"
            label += f" | {m.confidence * 100:.1f}%"
            
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 2)
            # Draw solid background for text
            cv2.rectangle(out, (x1, max(0, y1 - th - 10)), (x1 + tw + 10, max(0, y1)), color, -1)
            # Draw text in white over the solid background
            cv2.putText(out, label, (x1 + 5, max(0, y1 - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2, cv2.LINE_AA)
        return out
