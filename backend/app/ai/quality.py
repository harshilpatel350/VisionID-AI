from __future__ import annotations
from dataclasses import dataclass
import math
import cv2
import numpy as np

@dataclass
class QualityReport:
    blur: float
    brightness: float
    contrast: float
    size_score: float
    pose_score: float
    overall: float
    is_valid: bool

def blur_score(image_bgr: np.ndarray) -> float:
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    var = cv2.Laplacian(gray, cv2.CV_64F).var()
    return float(min(1.0, var / 500.0))

def low_light_score(image_bgr: np.ndarray) -> float:
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    mean = gray.mean() / 255.0
    return float(max(0.0, 1.0 - mean))

def face_quality(face_crop_bgr: np.ndarray) -> float:
    if face_crop_bgr.size == 0:
        return 0.0
    b = blur_score(face_crop_bgr)
    l = 1.0 - low_light_score(face_crop_bgr)
    contrast = float(min(1.0, cv2.cvtColor(face_crop_bgr, cv2.COLOR_BGR2GRAY).std() / 64.0))
    return float(max(0.0, min(1.0, 0.45 * b + 0.35 * l + 0.20 * contrast)))

def size_score(face_crop_bgr: np.ndarray, frame_shape: tuple[int, int, int]) -> float:
    """Score based on how much of the frame the face takes up. Tiny faces are bad."""
    if face_crop_bgr.size == 0:
        return 0.0
    h, w = face_crop_bgr.shape[:2]
    fh, fw = frame_shape[:2]
    ratio = (h * w) / float(fh * fw + 1e-6)
    # If face takes > 5% of frame, it's good size
    score = min(1.0, ratio / 0.05)
    return score

def pose_score(landmarks: np.ndarray | None) -> float:
    """
    Estimate frontalness using landmark symmetry and eye-line roll.
    Returns 0.0 to 1.0 (1.0 = frontal/level).
    """
    if landmarks is None:
        return 1.0

    pts = np.asarray(landmarks, dtype=np.float32)
    if pts.ndim != 2 or pts.shape[0] < 2:
        return 1.0

    left_eye = pts[0]
    right_eye = pts[1]
    if pts.shape[0] >= 3:
        nose = pts[2]
    else:
        nose = (left_eye + right_eye) * 0.5

    left_dist = float(np.linalg.norm(nose - left_eye))
    right_dist = float(np.linalg.norm(right_eye - nose))
    denom = max(left_dist + right_dist, 1e-6)
    yaw_ratio = min(left_dist, right_dist) / denom
    yaw_score = max(0.0, min(1.0, yaw_ratio * 2.0))

    angle = math.degrees(math.atan2(float(right_eye[1] - left_eye[1]), float(right_eye[0] - left_eye[0])))
    roll_score = max(0.0, 1.0 - abs(angle) / 30.0)

    return float(max(0.0, min(1.0, 0.6 * yaw_score + 0.4 * roll_score)))

def comprehensive_quality(
    face_crop_bgr: np.ndarray,
    frame_shape: tuple[int, int, int],
    min_score: float = 0.35,
    landmarks: np.ndarray | None = None
) -> QualityReport:
    if face_crop_bgr.size == 0:
        return QualityReport(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, False)
        
    b = blur_score(face_crop_bgr)
    brightness = 1.0 - low_light_score(face_crop_bgr)
    contrast = float(min(1.0, cv2.cvtColor(face_crop_bgr, cv2.COLOR_BGR2GRAY).std() / 64.0))
    sz = size_score(face_crop_bgr, frame_shape)
    pose = pose_score(landmarks)
    
    # Weight size and blur heavily
    overall = float(max(0.0, min(1.0, 0.32 * b + 0.2 * brightness + 0.1 * contrast + 0.23 * sz + 0.15 * pose)))
    is_valid = overall >= min_score
    
    return QualityReport(
        blur=b,
        brightness=brightness,
        contrast=contrast,
        size_score=sz,
        pose_score=pose,
        overall=overall,
        is_valid=is_valid
    )
