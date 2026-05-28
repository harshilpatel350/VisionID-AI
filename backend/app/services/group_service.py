import cv2
import numpy as np
from sqlalchemy.orm import Session
import time
from pathlib import Path

from app.ai.pipeline import FacePipeline
from app.config import load_settings
from app.services.unknown_service import UnknownService
from app.models.recognition import RecognitionLog
from app.models.mood import MoodRecord

class GroupService:
    def __init__(self, pipeline: FacePipeline):
        self.pipeline = pipeline
        self.settings = load_settings()
        self.unknown_service = UnknownService()

    def analyze_group_photo(self, db: Session, image_bytes: bytes, source_ref: str | None = None) -> dict:
        np_arr = np.frombuffer(image_bytes, np.uint8)
        image_bgr = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if image_bgr is None:
            raise ValueError("Invalid image")
            
        matches, aux, _meta = self.pipeline.analyze_frame(
            image_bgr,
            enable_enhancement=True,
            fast_emotion=False,
            compute_emotion=True,
            compute_liveness=True,
            force_enhanced=False
        )
        
        faces = []
        known_faces = 0
        unknown_faces = 0
        mood_dist = {}
        
        for i, m in enumerate(matches):
            if m.mood:
                mood_dist[m.mood] = mood_dist.get(m.mood, 0) + 1
                
            if m.is_unknown:
                unknown_faces += 1
            else:
                known_faces += 1

            db.add(RecognitionLog(
                person_id=m.person_id,
                person_name=m.full_name if not m.is_unknown else None,
                source_type="group_photo",
                source_ref=source_ref,
                confidence=m.confidence,
                distance=m.distance,
                is_unknown=m.is_unknown,
                frame_index=0,
                bounding_box_json=m.bbox,
                embedding_hash=m.embedding_hash,
                mood=m.mood,
                mood_scores_json=m.mood_scores,
                liveness_score=m.liveness_score,
                tracking_id=m.tracking_id,
                is_enhanced=m.is_enhanced,
                quality_score=m.quality_score,
                low_light_score=m.low_light_score,
                pose_score=m.pose_score,
                size_score=m.size_score
            ))

            if m.is_unknown:
                emb_res = aux[i].embedding
                if emb_res is not None:
                    unknown_log = self.unknown_service.log_unknown_face(
                        db, aux[i].face_crop, emb_res.embedding, m.embedding_hash,
                        m.bbox, m.confidence, m.mood, m.mood_scores,
                        m.liveness_score, "group_photo", source_ref
                    )
                    if m.mood:
                        db.add(MoodRecord(
                            person_id=None,
                            unknown_face_id=unknown_log.id,
                            mood=m.mood,
                            mood_scores_json=m.mood_scores,
                            source_type="group_photo",
                            source_ref=source_ref
                        ))
            else:
                if m.mood:
                    db.add(MoodRecord(
                        person_id=m.person_id,
                        unknown_face_id=None,
                        mood=m.mood,
                        mood_scores_json=m.mood_scores,
                        source_type="group_photo",
                        source_ref=source_ref
                    ))
                
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

        db.flush()
        
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
