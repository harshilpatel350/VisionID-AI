import cv2
import numpy as np
from app.ai.enhancement import LowLightEnhancer

class EnhancementService:
    def __init__(self):
        self.enhancer = LowLightEnhancer()
        
    def get_enhancement_status(self, frame_bgr: np.ndarray) -> dict:
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        brightness = float(gray.mean())
        is_low_light = brightness < self.enhancer.threshold
        return {
            "brightness": brightness,
            "is_low_light": is_low_light,
            "threshold": self.enhancer.threshold
        }
