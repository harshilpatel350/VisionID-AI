from __future__ import annotations
import hashlib
from dataclasses import dataclass

import cv2
import numpy as np

from app.ai.detector import FaceDetector, DetectedFace

@dataclass
class EmbeddingResult:
    embedding: np.ndarray
    hash_hex: str
    model_name: str

class FaceEmbedder:
    def __init__(self):
        self.detector = FaceDetector()
        self.insightface = getattr(self.detector, "insightface", None)
        self.model_name = "insightface_buffalo_l" if self.insightface is not None else "opencv_histogram"

    def _fallback_embedding(self, face_bgr: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2GRAY)
        # Use 16x32 to get 512 dimensions, matching insightface_buffalo_l dimension
        # and existing seeded data in the database.
        resized = cv2.resize(gray, (16, 32), interpolation=cv2.INTER_AREA)
        vec = resized.astype(np.float32).reshape(-1)
        vec = (vec - vec.mean()) / (vec.std() + 1e-6)
        vec = vec / (np.linalg.norm(vec) + 1e-6)
        return vec.astype(np.float32)

    def _bbox_iou(self, box1: tuple[int, int, int, int], box2: tuple[int, int, int, int]) -> float:
        xA = max(box1[0], box2[0])
        yA = max(box1[1], box2[1])
        xB = min(box1[2], box2[2])
        yB = min(box1[3], box2[3])
        interArea = max(0, xB - xA + 1) * max(0, yB - yA + 1)
        box1Area = (box1[2] - box1[0] + 1) * (box1[3] - box1[1] + 1)
        box2Area = (box2[2] - box2[0] + 1) * (box2[3] - box2[1] + 1)
        iou = interArea / float(box1Area + box2Area - interArea)
        return iou

    def extract(self, image_bgr: np.ndarray, detected: DetectedFace | None = None) -> EmbeddingResult | None:
        face = detected
        if face is None:
            faces = self.detector.detect(image_bgr)
            if not faces:
                return None
            face = faces[0]
            
        emb = getattr(face, "embedding", None)
        if emb is None:
            aligned = self.detector.align(image_bgr, face)
            if self.insightface is not None:
                # use detector output if available
                try:
                    app = self.insightface
                    faces = app.get(image_bgr)
                    if faces:
                        best_face = faces[0]
                        best_iou = -1.0
                        for f in faces:
                            f_bbox = tuple(map(int, f.bbox.tolist()))
                            iou = self._bbox_iou(face.bbox, f_bbox)
                            if iou > best_iou:
                                best_iou = iou
                                best_face = f
                        emb = np.asarray(best_face.embedding, dtype=np.float32)
                    else:
                        emb = self._fallback_embedding(aligned)
                except Exception:
                    emb = self._fallback_embedding(aligned)
            else:
                emb = self._fallback_embedding(aligned)
        
        emb = emb.astype(np.float32)
        if emb.ndim != 1:
            emb = emb.reshape(-1)
        emb = emb / (np.linalg.norm(emb) + 1e-6)
        hash_hex = hashlib.sha256(emb.tobytes()).hexdigest()
        return EmbeddingResult(embedding=emb, hash_hex=hash_hex, model_name=self.model_name)
