from __future__ import annotations
import cv2
import numpy as np

class LowLightEnhancer:
    def __init__(self, threshold: int = 60, gamma: float = 1.2, clip_limit: float = 2.0):
        self.threshold = threshold
        self.gamma = gamma
        self.clip_limit = clip_limit

    def is_low_light(self, frame_bgr: np.ndarray) -> bool:
        """Auto-detects if the frame is too dark."""
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        return float(gray.mean()) < self.threshold

    def enhance(self, frame_bgr: np.ndarray) -> np.ndarray:
        """
        Enhances low-light image: Gamma Correction -> CLAHE -> Bilateral Denoise
        """
        # 1. Gamma Correction
        f_img = frame_bgr.astype(np.float32) / 255.0
        corrected = np.power(f_img, self.gamma)
        corrected = np.clip(corrected * 255.0, 0, 255).astype(np.uint8)

        # 2. CLAHE in LAB color space
        lab = cv2.cvtColor(corrected, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=self.clip_limit, tileGridSize=(8, 8))
        cl = clahe.apply(l)
        limg = cv2.merge((cl, a, b))
        enhanced = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)

        # 3. Bilateral Filter for Denoising (preserves edges)
        denoised = cv2.bilateralFilter(enhanced, d=5, sigmaColor=50, sigmaSpace=50)
        return denoised

    def enhance_aggressive(self, frame_bgr: np.ndarray) -> np.ndarray:
        """Aggressive enhancement with edge-preserving filtering."""
        enhanced = self.enhance(frame_bgr)
        return cv2.edgePreservingFilter(enhanced, flags=1, sigma_s=40, sigma_r=0.2)
