from __future__ import annotations
import cv2
import numpy as np

class LivenessDetector:
    def __init__(self, threshold: float = 0.5):
        self.threshold = threshold

    def _get_lbp(self, img: np.ndarray) -> np.ndarray:
        h, w = img.shape
        img_f = img.astype(np.float32)
        lbp = np.zeros((h-2, w-2), dtype=np.uint8)
        
        lbp |= ((img_f[0:-2, 0:-2] >= img_f[1:-1, 1:-1]).astype(np.uint8) << 7)
        lbp |= ((img_f[0:-2, 1:-1] >= img_f[1:-1, 1:-1]).astype(np.uint8) << 6)
        lbp |= ((img_f[0:-2, 2:] >= img_f[1:-1, 1:-1]).astype(np.uint8) << 5)
        lbp |= ((img_f[1:-1, 2:] >= img_f[1:-1, 1:-1]).astype(np.uint8) << 4)
        lbp |= ((img_f[2:, 2:] >= img_f[1:-1, 1:-1]).astype(np.uint8) << 3)
        lbp |= ((img_f[2:, 1:-1] >= img_f[1:-1, 1:-1]).astype(np.uint8) << 2)
        lbp |= ((img_f[2:, 0:-2] >= img_f[1:-1, 1:-1]).astype(np.uint8) << 1)
        lbp |= ((img_f[1:-1, 0:-2] >= img_f[1:-1, 1:-1]).astype(np.uint8) << 0)
        
        return lbp

    def check_texture(self, face_crop_bgr: np.ndarray) -> float:
        """
        Uses LBP variance to detect texture anomalies.
        Printed photos or screens often have different LBP variance than real 3D faces.
        Returns a score 0.0 to 1.0 (1.0 = highly likely real).
        """
        if face_crop_bgr.size == 0:
            return 0.5
            
        gray = cv2.cvtColor(face_crop_bgr, cv2.COLOR_BGR2GRAY)
        lbp = self._get_lbp(gray)
        var = np.var(lbp)
        
        # Heuristic scaling: variance of real faces usually falls in a certain range.
        # Below ~500 can be too smooth (filter/screen blur), above ~3000 can be noisy (print/moire).
        if 500 < var < 3000:
            score = 1.0 - abs(1750 - var) / 1250.0  # Peak around 1750
        else:
            score = 0.1
            
        return max(0.0, min(1.0, score))

    def check_moire(self, face_crop_bgr: np.ndarray) -> float:
        """
        Detects Moiré patterns (common when capturing a screen) using FFT.
        Returns a score 0.0 to 1.0 (1.0 = no moire, real).
        """
        if face_crop_bgr.size == 0:
            return 0.5
            
        gray = cv2.cvtColor(face_crop_bgr, cv2.COLOR_BGR2GRAY)
        f = np.fft.fft2(gray)
        fshift = np.fft.fftshift(f)
        magnitude_spectrum = 20 * np.log(np.abs(fshift) + 1e-6)
        
        # High frequencies at specific angles indicate Moiré
        h, w = gray.shape
        cy, cx = h // 2, w // 2
        # Mask out low frequencies (center)
        mask = np.ones((h, w), np.uint8)
        r = 15
        cv2.circle(mask, (cx, cy), r, 0, -1)
        
        high_freq_mag = magnitude_spectrum * mask
        peak_ratio = np.max(high_freq_mag) / (np.mean(high_freq_mag) + 1e-6)
        
        # High peak ratio implies distinct pattern (like screen pixels)
        score = 1.0 - min(1.0, max(0.0, (peak_ratio - 5.0) / 15.0))
        return score

    def score(self, face_crop_bgr: np.ndarray) -> dict:
        texture_score = self.check_texture(face_crop_bgr)
        moire_score = self.check_moire(face_crop_bgr)
        
        # Combine
        final_score = 0.6 * texture_score + 0.4 * moire_score
        is_suspicious = final_score < self.threshold
        
        return {
            "liveness_score": final_score,
            "texture_score": texture_score,
            "moire_score": moire_score,
            "is_suspicious": is_suspicious
        }
