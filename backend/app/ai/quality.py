from __future__ import annotations
import cv2
import numpy as np

def blur_score(image_bgr: np.ndarray) -> float:
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    var = cv2.Laplacian(gray, cv2.CV_64F).var()
    return float(min(1.0, var / 500.0))

def low_light_score(image_bgr: np.ndarray) -> float:
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    mean = gray.mean() / 255.0
    return float(max(0.0, 1.0 - mean))

def face_quality(image_bgr: np.ndarray) -> float:
    b = blur_score(image_bgr)
    l = 1.0 - low_light_score(image_bgr)
    contrast = float(min(1.0, cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY).std() / 64.0))
    return float(max(0.0, min(1.0, 0.45 * b + 0.35 * l + 0.20 * contrast)))
