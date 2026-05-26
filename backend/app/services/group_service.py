import cv2
import numpy as np
from sqlalchemy.orm import Session
import time
from pathlib import Path

from app.ai.pipeline import FacePipeline
from app.config import load_settings
from app.services.unknown_service import UnknownService

class GroupService:
    def __init__(self, pipeline: FacePipeline):
        self.pipeline = pipeline
        self.settings = load_settings()
        self.unknown_service = UnknownService()

    def analyze_group_photo(self, db: Session, image_bytes: bytes) -> dict:
        np_arr = np.frombuffer(image_bytes, np.uint8)
        image_bgr = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if image_bgr is None:
            raise ValueError("Invalid image")
            
        matches = self.pipeline.analyze_face_enhanced(image_bgr)
        
        faces = []
        known_faces = 0
        unknown_faces = 0
        mood_dist = {}
        
        for m in matches:
            if m.mood:
                mood_dist[m.mood] = mood_dist.get(m.mood, 0) + 1
                
            if m.is_unknown:
                unknown_faces += 1
                # We could log this unknown face, but group photo might have many
                # Let's log it so it appears in the unknowns gallery
                # Need the face crop and embedding which aren't in RecognitionMatch directly...
                # For now, just count it. The pipeline does the work.
            else:
                known_faces += 1
                
            faces.append({
                "person_id": m.person_id,
                "full_name": m.full_name,
                "is_unknown": m.is_unknown,
                "confidence": m.confidence,
                "bbox": m.bbox,
                "mood": m.mood,
                "mood_scores": m.mood_scores
            })
            
        annotated = self.pipeline.draw(image_bgr, matches)
        out_dir = Path(self.settings.abs_report_dir) / "groups"
        out_dir.mkdir(parents=True, exist_ok=True)
        fname = f"group_{int(time.time() * 1000)}.jpg"
        path = out_dir / fname
        cv2.imwrite(str(path), annotated)
        
        return {
            "summary": {
                "total_faces": len(matches),
                "known_faces": known_faces,
                "unknown_faces": unknown_faces,
                "mood_distribution": mood_dist
            },
            "faces": faces,
            "annotated_image_url": f"storage/reports/groups/{fname}"
        }
