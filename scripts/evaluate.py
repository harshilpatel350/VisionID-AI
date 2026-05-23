import os
import cv2
import numpy as np
from sqlalchemy.orm import Session
from app.db.session import engine
from app.models.user import User
from app.models.dataset import Dataset
from app.models.face import Person, FaceSample, FaceEmbedding
from app.models.recognition import RecognitionLog, AuditLog
from app.ai.pipeline import FacePipeline
from app.config import load_settings

def run_evaluation():
    settings = load_settings()
    with Session(engine) as db:
        # Load all registered persons for the registry
        from app.services.face_service import FaceService
        face_service = FaceService()
        face_service.rebuild_index(db)
        pipeline = face_service.pipeline
        
        # We'll use the FaceSample table as our "test set" for this internal evaluation
        # In a real scenario, this would be a separate labeled dataset.
        samples = db.query(FaceSample).all()
        if not samples:
            print("No samples found for evaluation.")
            return

        print(f"Starting evaluation on {len(samples)} samples...")
        
        correct = 0
        total = 0
        unknown_as_known = 0
        known_as_unknown = 0
        wrong_match = 0
        
        for s in samples:
            person = db.get(Person, s.person_id)
            if not person: continue
            
            abs_path = settings.base_dir / s.image_path
            if not abs_path.exists(): continue
            
            img = cv2.imread(str(abs_path))
            if img is None: continue
            
            total += 1
            matches = pipeline.analyze_face(img)
            
            # Find the match that corresponds to the face in the sample
            # (Assuming one face per sample image for evaluation)
            if not matches:
                known_as_unknown += 1
                continue
                
            best_match = matches[0] # Take the top match
            print(f"  Image {s.id}: Best confidence={best_match.confidence:.4f}, Unknown={best_match.is_unknown}")
            
            if best_match.is_unknown:
                known_as_unknown += 1
            elif best_match.person_id == s.person_id:
                correct += 1
            else:
                wrong_match += 1
                
        accuracy = (correct / total) * 100 if total > 0 else 0
        print("\n--- Evaluation Results ---")
        print(f"Total Images: {total}")
        print(f"Correct Matches: {correct}")
        print(f"Known marked as Unknown: {known_as_unknown}")
        print(f"Wrong Matches: {wrong_match}")
        print(f"Accuracy: {accuracy:.2f}%")
        
        if accuracy < 50:
            print("\nWARNING: Accuracy is below 50%. Check thresholds and model alignment.")

if __name__ == "__main__":
    run_evaluation()
