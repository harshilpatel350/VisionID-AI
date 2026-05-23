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
        self.embedding_dim = 4096 if self.insightface is None else 512

    def _get_lbp_feature(self, img: np.ndarray) -> np.ndarray:
        """Simple Local Binary Pattern implementation."""
        h, w = img.shape
        # Use faster bitwise operations if possible, but keeping it simple for now
        lbp = np.zeros((h-2, w-2), dtype=np.uint8)
        # Optimized LBP calculation using shifts
        img_f = img.astype(np.float32)
        lbp |= ((img_f[0:-2, 0:-2] >= img_f[1:-1, 1:-1]).astype(np.uint8) << 7)
        lbp |= ((img_f[0:-2, 1:-1] >= img_f[1:-1, 1:-1]).astype(np.uint8) << 6)
        lbp |= ((img_f[0:-2, 2:] >= img_f[1:-1, 1:-1]).astype(np.uint8) << 5)
        lbp |= ((img_f[1:-1, 2:] >= img_f[1:-1, 1:-1]).astype(np.uint8) << 4)
        lbp |= ((img_f[2:, 2:] >= img_f[1:-1, 1:-1]).astype(np.uint8) << 3)
        lbp |= ((img_f[2:, 1:-1] >= img_f[1:-1, 1:-1]).astype(np.uint8) << 2)
        lbp |= ((img_f[2:, 0:-2] >= img_f[1:-1, 1:-1]).astype(np.uint8) << 1)
        lbp |= ((img_f[1:-1, 0:-2] >= img_f[1:-1, 1:-1]).astype(np.uint8) << 0)
        
        hist, _ = np.histogram(lbp, bins=256, range=(0, 256))
        hist = hist.astype(np.float32)
        hist /= (hist.sum() + 1e-6)
        return hist

    def _fallback_embedding(self, face_bgr: np.ndarray) -> np.ndarray:
        # Spatial LBP: 4x4 grid for better discriminability
        gray = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)
        gray = cv2.resize(gray, (128, 128))
        
        grid_size = 4
        h, w = gray.shape
        gh, gw = h // grid_size, w // grid_size
        
        features = []
        for i in range(grid_size):
            for j in range(grid_size):
                cell = gray[i*gh : (i+1)*gh, j*gw : (j+1)*gw]
                features.append(self._get_lbp_feature(cell))
        
        vec = np.concatenate(features)
        # Unit length normalization
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
