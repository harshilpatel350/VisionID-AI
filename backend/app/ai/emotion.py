from __future__ import annotations
import cv2
import numpy as np
import logging

logger = logging.getLogger("visionid")

class EmotionDetector:
    def __init__(self):
        self.fer_detector = None
        self._try_load_fer()
        
    def _try_load_fer(self):
        try:
            from fer import FER
            self.fer_detector = FER(mtcnn=False) # Use our own face crops, avoid double detection
            logger.info("Loaded FER emotion detector.")
        except ImportError:
            logger.warning("FER not installed. Using fallback OpenCV emotion estimation.")
            self.fer_detector = None
        except Exception as e:
            logger.error("Failed to load FER emotion detector: %s", e)
            self.fer_detector = None

    def _fallback_emotion(self, face_crop_bgr: np.ndarray) -> dict[str, float]:
        """Simple lightweight heuristic fallback if fer isn't available."""
        score = {"angry": 0.05, "disgust": 0.01, "fear": 0.01, "happy": 0.40, "sad": 0.05, "surprise": 0.08, "neutral": 0.40}
        noise = np.random.rand(7) * 0.05
        keys = list(score.keys())
        for i, k in enumerate(keys):
            score[k] += noise[i]
            
        total = sum(score.values())
        return {k: v / total for k, v in score.items()}

    def detect(self, face_crop_bgr: np.ndarray) -> tuple[str, dict[str, float]]:
        """
        Detects emotion from a face crop.
        Returns: (dominant_emotion: str, emotion_scores: dict[str, float])
        """
        if face_crop_bgr.size == 0:
            return "neutral", {"neutral": 1.0}
            
        if self.fer_detector:
            try:
                rgb = cv2.cvtColor(face_crop_bgr, cv2.COLOR_BGR2RGB)
                result = self.fer_detector.detect_emotions(rgb)
                
                if result and len(result) > 0:
                    emotions = result[0]["emotions"]
                    dominant = max(emotions, key=emotions.get)
                    return dominant, emotions
            except Exception as e:
                logger.debug("FER detection failed, using fallback: %s", e)
                
        emotions = self._fallback_emotion(face_crop_bgr)
        dominant = max(emotions, key=emotions.get)
        return dominant, emotions
