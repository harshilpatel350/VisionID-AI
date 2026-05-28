from __future__ import annotations
import cv2
import numpy as np
import logging

from app.config import load_settings

logger = logging.getLogger("visionid")

class EmotionDetector:
    def __init__(self):
        self.settings = load_settings()
        self.fer_detector = None
        self.deepface = None
        self._try_load_deepface()
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

    def _try_load_deepface(self):
        if self.settings.emotion_backend not in {"deepface", "auto"}:
            return
        try:
            from deepface import DeepFace
            self.deepface = DeepFace
            logger.info("Loaded DeepFace emotion detector.")
        except Exception as e:
            logger.warning("DeepFace not available for emotion detection: %s", e)
            self.deepface = None

    def _fallback_emotion(self, face_crop_bgr: np.ndarray) -> dict[str, float]:
        """Simple lightweight heuristic fallback if fer isn't available."""
        score = {"angry": 0.05, "disgust": 0.01, "fear": 0.01, "happy": 0.40, "sad": 0.05, "surprise": 0.08, "neutral": 0.40}
        noise = np.random.rand(7) * 0.05
        keys = list(score.keys())
        for i, k in enumerate(keys):
            score[k] += noise[i]
            
        total = sum(score.values())
        return {k: v / total for k, v in score.items()}

    def _inject_confused(self, emotions: dict[str, float]) -> tuple[str, dict[str, float]]:
        if not emotions:
            return "neutral", {"neutral": 1.0}
        items = sorted(emotions.items(), key=lambda kv: kv[1], reverse=True)
        top_name, top_score = items[0]
        if len(items) > 1:
            second_score = items[1][1]
            if top_score - second_score < 0.08:
                emotions = dict(emotions)
                emotions["confused"] = max(0.05, (top_score + second_score) / 2.0)
                total = sum(emotions.values()) + 1e-6
                emotions = {k: v / total for k, v in emotions.items()}
                return "confused", emotions
        return top_name, emotions

    def _deepface_detect(self, face_crop_bgr: np.ndarray) -> tuple[str, dict[str, float]] | None:
        if self.deepface is None:
            return None
        try:
            rgb = cv2.cvtColor(face_crop_bgr, cv2.COLOR_BGR2RGB)
            res = self.deepface.analyze(
                img_path=rgb,
                actions=["emotion"],
                enforce_detection=False,
                detector_backend="skip"
            )
            if isinstance(res, list):
                res = res[0]
            emotions = res.get("emotion", {})
            if emotions:
                total = sum(emotions.values()) + 1e-6
                emotions = {k: float(v) / total for k, v in emotions.items()}
                return self._inject_confused(emotions)
        except Exception as e:
            logger.debug("DeepFace emotion failed: %s", e)
        return None

    def detect(self, face_crop_bgr: np.ndarray, fast: bool = False) -> tuple[str, dict[str, float]]:
        """
        Detects emotion from a face crop.
        Returns: (dominant_emotion: str, emotion_scores: dict[str, float])
        """
        if face_crop_bgr.size == 0:
            return "neutral", {"neutral": 1.0}

        use_deepface = self.settings.emotion_backend in {"deepface", "auto"} and not fast
        if use_deepface:
            res = self._deepface_detect(face_crop_bgr)
            if res is not None:
                return res

        if self.fer_detector:
            try:
                rgb = cv2.cvtColor(face_crop_bgr, cv2.COLOR_BGR2RGB)
                result = self.fer_detector.detect_emotions(rgb)
                
                if result and len(result) > 0:
                    emotions = result[0]["emotions"]
                    return self._inject_confused(emotions)
            except Exception as e:
                logger.debug("FER detection failed, using fallback: %s", e)
                
        emotions = self._fallback_emotion(face_crop_bgr)
        return self._inject_confused(emotions)
