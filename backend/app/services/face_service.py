from __future__ import annotations
from dataclasses import asdict
from pathlib import Path
from typing import Any
from uuid import uuid4

import cv2
import numpy as np
from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.pipeline import FacePipeline
from app.ai.embedder import FaceEmbedder
from app.ai.quality import face_quality, blur_score, low_light_score
from app.config import load_settings
from app.models.face import Person, FaceSample, FaceEmbedding
from app.models.recognition import RecognitionLog
from app.models.mood import MoodRecord
from app.repositories.face_repo import FaceRepository
from app.repositories.recognition_repo import RecognitionRepository
from app.services.unknown_service import UnknownService
from app.utils.files import sha256_bytes, unique_filename

class FaceService:
    def __init__(self):
        self.repo = FaceRepository()
        self.rec_repo = RecognitionRepository()
        self.unknown_service = UnknownService()
        self.settings = load_settings()
        self.embedder = FaceEmbedder()
        self.pipeline = FacePipeline()

    def _save_upload(self, upload: UploadFile, dest_dir: Path) -> tuple[Path, bytes]:
        dest_dir.mkdir(parents=True, exist_ok=True)
        raw = upload.file.read()
        name = unique_filename("face", Path(upload.filename or ".jpg").suffix or ".jpg")
        path = dest_dir / name
        path.write_bytes(raw)
        return path, raw

    def _load_image(self, raw: bytes) -> np.ndarray:
        arr = np.frombuffer(raw, dtype=np.uint8)
        frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if frame is None:
            raise HTTPException(status_code=400, detail="Invalid image file")
        return frame

    def _store_face_sample(self, db: Session, person: Person, file_path: Path, raw: bytes, frame: np.ndarray) -> FaceSample | None:
        matches, aux, _meta = self.pipeline.analyze_frame(
            frame,
            enable_enhancement=self.settings.auto_low_light_enhance,
            fast_emotion=True,
            compute_emotion=False,
            compute_liveness=False,
            force_enhanced=False
        )
        if not matches:
            return None
        detection = matches[0]
        if detection.quality_score < self.settings.quality_min_score:
            return None

        crop_path = None
        crop_dir = file_path.parent / "crops"
        crop_dir.mkdir(parents=True, exist_ok=True)
        crop_name = unique_filename("crop", ".jpg")
        crop_file = crop_dir / crop_name
        cv2.imwrite(str(crop_file), aux[0].face_crop)
        crop_path = str(crop_file.relative_to(self.settings.base_dir))

        sample = FaceSample(
            person_id=person.id,
            image_path=str(file_path.relative_to(self.settings.base_dir)),
            crop_path=crop_path,
            quality_score=detection.quality_score,
            blur_score=detection.blur_score,
            low_light_score=detection.low_light_score,
            detection_score=1.0 - detection.distance,
            embedding_hash=detection.embedding_hash or sha256_bytes(raw),
        )
        db.add(sample)
        db.flush()
        emb = aux[0].embedding or self.embedder.extract(frame)
        if emb is None:
            return sample
        embedding = FaceEmbedding(
            sample_id=sample.id,
            person_id=person.id,
            embedding_dim=int(emb.embedding.shape[0]),
            embedding_vector=emb.embedding.astype(np.float32).tobytes(),
            similarity_threshold=self.settings.recognition_threshold,
        )
        db.add(embedding)
        return sample

    def quality_check(self, image_bytes: bytes) -> dict:
        from app.ai.quality import comprehensive_quality
        frame = self._load_image(image_bytes)
        detected_faces = self.pipeline.detector.detect(frame)
        if not detected_faces:
            raise HTTPException(status_code=400, detail="No face detected in image")
        if len(detected_faces) > 1:
            raise HTTPException(status_code=400, detail="Multiple faces detected, please upload an image with only one face")
            
        face_crop = self.pipeline.detector.align(frame, detected_faces[0])
        report = comprehensive_quality(face_crop, frame.shape, landmarks=detected_faces[0].landmark)
        return {
            "blur": report.blur,
            "brightness": report.brightness,
            "contrast": report.contrast,
            "size_score": report.size_score,
            "pose_score": report.pose_score,
            "overall": report.overall,
            "is_valid": report.is_valid
        }

    def duplicate_check(self, db: Session, image_bytes: bytes) -> dict | None:
        frame = self._load_image(image_bytes)
        matches, aux, _meta = self.pipeline.analyze_frame(
            frame,
            enable_enhancement=self.settings.auto_low_light_enhance,
            fast_emotion=True,
            compute_emotion=False,
            compute_liveness=False,
            force_enhanced=False
        )
        if not matches:
            raise HTTPException(status_code=400, detail="No face detected in image")
        emb = aux[0].embedding or self.embedder.extract(frame)
        if emb is None:
            raise HTTPException(status_code=400, detail="Failed to extract face embedding")
        return self._find_duplicate_for_embedding(db, emb)

    def create_person(self, db: Session, created_by: int | None, data: dict[str, Any], files: list[UploadFile]) -> Person:
        if not files:
            raise HTTPException(status_code=400, detail="At least one face image is required")

        person_code = data.get("person_code") or f"PID-{uuid4().hex[:10].upper()}"
        if self.repo.find_by_code(db, person_code):
            raise HTTPException(status_code=409, detail="Person code already exists")

        # Duplicate prevention (based on the first valid sample)
        if self.settings.prevent_duplicate_registration:
            emb_candidate = None
            for upload in files:
                raw = upload.file.read()
                upload.file.seek(0)
                frame = self._load_image(raw)
                matches, aux, _meta = self.pipeline.analyze_frame(
                    frame,
                    enable_enhancement=self.settings.auto_low_light_enhance,
                    fast_emotion=True,
                    compute_emotion=False,
                    compute_liveness=False,
                    force_enhanced=False
                )
                if not matches:
                    continue
                if matches[0].quality_score < self.settings.quality_min_score:
                    continue
                emb_candidate = aux[0].embedding or self.embedder.extract(frame)
                if emb_candidate is not None:
                    break

            if emb_candidate is not None:
                dup = self._find_duplicate_for_embedding(db, emb_candidate)
                if dup:
                    raise HTTPException(
                        status_code=409,
                        detail=f"Possible duplicate: {dup['full_name']} ({dup['person_code']}) similarity {dup['similarity']:.2f}"
                    )

        person = Person(
            person_code=person_code,
            full_name=data["full_name"],
            email=data.get("email"),
            phone=data.get("phone"),
            department=data.get("department"),
            title=data.get("title"),
            age=data.get("age"),
            gender=data.get("gender"),
            tags=data.get("tags"),
            notes=data.get("notes"),
            created_by=created_by,
            embedding_model=self.embedder.model_name,
        )
        db.add(person)
        db.flush()

        valid_samples = 0
        for upload in files:
            file_path, raw = self._save_upload(upload, self.settings.abs_face_dir / person.person_code)
            frame = self._load_image(raw)
            sample = self._store_face_sample(db, person, file_path, raw, frame)
            if sample is not None:
                valid_samples += 1

        if valid_samples == 0:
            db.rollback()
            raise HTTPException(status_code=400, detail="All uploaded images failed quality checks")

        db.flush()
        self._update_primary_image(person, db)
        self._prevent_duplicates(db, person)
        return person

    def add_sample_to_existing_person(self, db: Session, person: Person, upload: UploadFile) -> FaceSample | None:
        file_path, raw = self._save_upload(upload, self.settings.abs_face_dir / person.person_code)
        frame = self._load_image(raw)
        sample = self._store_face_sample(db, person, file_path, raw, frame)
        self._update_primary_image(person, db)
        self._prevent_duplicates(db, person)
        return sample

    def _update_primary_image(self, person: Person, db: Session) -> None:
        sample = db.scalar(select(FaceSample).where(FaceSample.person_id == person.id).order_by(FaceSample.quality_score.desc()))
        if sample:
            person.primary_image_path = sample.image_path

    def _prevent_duplicates(self, db: Session, new_person: Person) -> None:
        new_emb = self._person_average_embedding(db, new_person.id)
        if new_emb is None:
            return
            
        all_people = db.scalars(select(Person).where(Person.id != new_person.id, Person.is_active.is_(True))).all()
        if not all_people:
            return
            
        duplicates = []
        for p in all_people:
            emb = self._person_average_embedding(db, p.id)
            if emb is None:
                continue
            if new_emb.shape[0] != emb.shape[0]:
                continue
            sim = float(np.dot(new_emb, emb))
            if sim >= self.settings.duplicate_similarity_threshold:
                duplicates.append((p, sim))
                
        if duplicates:
            person, _sim = sorted(duplicates, key=lambda t: t[1], reverse=True)[0]
            new_person.duplicate_of = person.id

    def _find_duplicate_for_embedding(self, db: Session, emb_res: Any) -> dict[str, Any] | None:
        if emb_res is None:
            return None
        if self.pipeline.index is None:
            if not self.pipeline.load_index():
                self.rebuild_index(db)
        if self.pipeline.index is None or not self.pipeline._meta:
            return None

        vec = emb_res.embedding.astype(np.float32).reshape(1, -1)
        vec = self.pipeline._normalize(vec)
        scores, idxs = self.pipeline.index.search(vec, k=1)
        if scores.size == 0:
            return None
        best_score = float(scores[0][0])
        if best_score < self.settings.duplicate_similarity_threshold:
            return None
        best_idx = int(idxs[0][0])
        if best_idx < 0 or best_idx >= len(self.pipeline._meta):
            return None
        item = self.pipeline._meta[best_idx]
        return {
            "person_id": int(item["person_id"]),
            "person_code": str(item["person_code"]),
            "full_name": str(item["full_name"]),
            "similarity": best_score,
        }

    def _person_average_embedding(self, db: Session, person_id: int) -> np.ndarray | None:
        embeddings = db.scalars(select(FaceEmbedding).where(FaceEmbedding.person_id == person_id)).all()
        if not embeddings:
            return None
        vectors = []
        for item in embeddings:
            vec = np.frombuffer(item.embedding_vector, dtype=np.float32)
            vec = vec / (np.linalg.norm(vec) + 1e-6)
            vectors.append(vec)
        stacked = np.vstack(vectors)
        avg = stacked.mean(axis=0)
        avg = avg / (np.linalg.norm(avg) + 1e-6)
        return avg.astype(np.float32)

    def rebuild_index(self, db: Session) -> None:
        embeddings = []
        current_model = self.embedder.model_name
        for emb in db.scalars(select(FaceEmbedding)).all():
            person = db.get(Person, emb.person_id)
            if not person or person.embedding_model != current_model:
                continue
            embeddings.append(
                {
                    "person_id": person.id,
                    "person_code": person.person_code,
                    "full_name": person.full_name,
                    "department": person.department,
                    "title": person.title,
                    "email": person.email,
                    "phone": person.phone,
                    "vector": np.frombuffer(emb.embedding_vector, dtype=np.float32),
                }
            )
        self.pipeline.set_registry(embeddings)
        self.pipeline.save_index()

    def list_persons(self, db: Session) -> list[dict[str, Any]]:
        rows = []
        persons = self.repo.list_persons(db)
        for p in persons:
            rows.append(self._serialize_person(db, p))
        return rows

    def list_persons_paginated(self, db: Session, offset: int, limit: int) -> tuple[int, list[dict[str, Any]]]:
        from sqlalchemy import select, func
        from app.models.face import Person
        total = db.scalar(select(func.count(Person.id))) or 0
        persons = db.scalars(select(Person).order_by(Person.created_at.desc()).offset(offset).limit(limit)).all()
        rows = [self._serialize_person(db, p) for p in persons]
        return total, rows

    def _serialize_person(self, db: Session, p: Person) -> dict[str, Any]:
        return {
            "id": p.id,
            "person_code": p.person_code,
            "full_name": p.full_name,
            "email": p.email,
            "phone": p.phone,
            "department": p.department,
            "title": p.title,
            "age": p.age,
            "gender": p.gender,
            "tags": p.tags,
            "notes": p.notes,
            "primary_image_path": p.primary_image_path,
            "is_active": p.is_active,
            "embedding_model": p.embedding_model,
            "duplicate_of": p.duplicate_of,
            "sample_count": self.repo.sample_count(db, p.id),
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }

    def recognize_image(self, db: Session, image_bytes: bytes, source_type: str, source_ref: str | None = None, frame_index: int = 0):
        frame = self._load_image(image_bytes)
        
        # O(N) bottleneck fix: try disk cache first, then rebuild from DB
        if self.pipeline.index is None:
            if not self.pipeline.load_index():
                self.rebuild_index(db)
            
        matches, aux, _meta = self.pipeline.analyze_frame(
            frame,
            enable_enhancement=self.settings.auto_low_light_enhance,
            fast_emotion=False,
            compute_emotion=True,
            compute_liveness=True,
            force_enhanced=False
        )
        results = []
        for i, m in enumerate(matches):
            log = RecognitionLog(
                person_id=m.person_id,
                person_name=m.full_name if not m.is_unknown else None,
                source_type=source_type,
                source_ref=source_ref,
                confidence=m.confidence,
                distance=m.distance,
                is_unknown=m.is_unknown,
                frame_index=frame_index,
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
                size_score=m.size_score,
            )
            db.add(log)
            if m.is_unknown:
                emb_res = aux[i].embedding
                if emb_res is not None:
                    unknown_log = self.unknown_service.log_unknown_face(
                        db, aux[i].face_crop, emb_res.embedding, m.embedding_hash,
                        m.bbox, m.confidence, m.mood, m.mood_scores,
                        m.liveness_score, source_type, source_ref
                    )
                    if m.mood:
                        db.add(MoodRecord(
                            person_id=None,
                            unknown_face_id=unknown_log.id,
                            mood=m.mood,
                            mood_scores_json=m.mood_scores,
                            source_type=source_type,
                            source_ref=source_ref
                        ))
            else:
                if m.mood:
                    db.add(MoodRecord(
                        person_id=m.person_id,
                        unknown_face_id=None,
                        mood=m.mood,
                        mood_scores_json=m.mood_scores,
                        source_type=source_type,
                        source_ref=source_ref
                    ))
            results.append(m)
        db.flush()
        return frame, results

    def process_video_file(self, db: Session, file_path: Path, source_ref: str | None = None):
        cap = cv2.VideoCapture(str(file_path))
        if not cap.isOpened():
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail="Could not open video")
            
        if self.pipeline.index is None:
            if not self.pipeline.load_index():
                self.rebuild_index(db)
            
        frame_index = 0
        collected = []
        skip = max(1, self.settings.frame_skip)
        max_frames = self.settings.max_batch_frames
        while cap.isOpened() and frame_index < max_frames:
            ok, frame = cap.read()
            if not ok:
                break
            if frame_index % skip == 0:
                matches, aux, _meta = self.pipeline.analyze_frame(
                    frame,
                    enable_enhancement=self.settings.auto_low_light_enhance,
                    fast_emotion=True,
                    compute_emotion=True,
                    compute_liveness=True,
                    force_enhanced=False
                )
                for i, m in enumerate(matches):
                    log = RecognitionLog(
                        person_id=m.person_id,
                        person_name=m.full_name if not m.is_unknown else None,
                        source_type="video",
                        source_ref=source_ref or str(file_path),
                        confidence=m.confidence,
                        distance=m.distance,
                        is_unknown=m.is_unknown,
                        frame_index=frame_index,
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
                        size_score=m.size_score,
                    )
                    db.add(log)
                    if m.is_unknown:
                        emb_res = aux[i].embedding
                        if emb_res is not None:
                            unknown_log = self.unknown_service.log_unknown_face(
                                db, aux[i].face_crop, emb_res.embedding, m.embedding_hash,
                                m.bbox, m.confidence, m.mood, m.mood_scores,
                                m.liveness_score, "video", source_ref or str(file_path)
                            )
                            if m.mood:
                                db.add(MoodRecord(
                                    person_id=None,
                                    unknown_face_id=unknown_log.id,
                                    mood=m.mood,
                                    mood_scores_json=m.mood_scores,
                                    source_type="video",
                                    source_ref=source_ref or str(file_path)
                                ))
                    else:
                        if m.mood:
                            db.add(MoodRecord(
                                person_id=m.person_id,
                                unknown_face_id=None,
                                mood=m.mood,
                                mood_scores_json=m.mood_scores,
                                source_type="video",
                                source_ref=source_ref or str(file_path)
                            ))
                    collected.append(m)
            frame_index += 1
        cap.release()
        db.flush()
        return collected
