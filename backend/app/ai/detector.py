from __future__ import annotations
from dataclasses import dataclass
from typing import Any

import cv2
import numpy as np

@dataclass
class DetectedFace:
    bbox: tuple[int, int, int, int]
    score: float
    landmark: np.ndarray | None = None
    embedding: np.ndarray | None = None

class FaceDetector:
    def __init__(self):
        self.cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        self.insightface = None
        self._try_load_insightface()

    def _try_load_insightface(self) -> None:
        try:
            from insightface.app import FaceAnalysis
            app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
            app.prepare(ctx_id=-1, det_size=(640, 640))
            if 'detection' in app.models:
                app.models['detection'].det_thresh = 0.2
            self.insightface = app
        except Exception:
            self.insightface = None

    def detect(self, image_bgr: np.ndarray) -> list[DetectedFace]:
        if self.insightface is not None:
            faces = self.insightface.get(image_bgr)
            results: list[DetectedFace] = []
            for face in faces:
                x1, y1, x2, y2 = map(int, face.bbox.tolist())
                emb = getattr(face, "embedding", None)
                results.append(DetectedFace((x1, y1, x2, y2), float(getattr(face, "det_score", 0.99)), getattr(face, "landmark", None), emb))
            return results
        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
        rects = self.cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=3, minSize=(48, 48))
        return [DetectedFace((x, y, x + w, y + h), 0.75) for (x, y, w, h) in rects]

    def align(self, image_bgr: np.ndarray, face: DetectedFace, size: tuple[int, int] = (112, 112)) -> np.ndarray:
        x1, y1, x2, y2 = face.bbox
        h, w = image_bgr.shape[:2]
        x1, y1, x2, y2 = max(0, x1), max(0, y1), min(w, x2), min(h, y2)
        crop = image_bgr[y1:y2, x1:x2]
        if crop.size == 0:
            return np.zeros((size[1], size[0], 3), dtype=np.uint8)
        return cv2.resize(crop, size, interpolation=cv2.INTER_AREA)
