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
from app.repositories.face_repo import FaceRepository
from app.repositories.recognition_repo import RecognitionRepository
from app.utils.files import sha256_bytes, unique_filename

class FaceService:
    def __init__(self):
        self.repo = FaceRepository()
        self.rec_repo = RecognitionRepository()
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
        analysis = self.pipeline.analyze_face(frame)
        if not analysis:
            return None
        detection = analysis[0]
        sample = FaceSample(
            person_id=person.id,
            image_path=str(file_path.relative_to(self.settings.base_dir)),
            crop_path=None,
            quality_score=detection.quality_score,
            blur_score=detection.blur_score,
            low_light_score=detection.low_light_score,
            detection_score=1.0 - detection.distance,
            embedding_hash=detection.embedding_hash or sha256_bytes(raw),
        )
        db.add(sample)
        db.flush()
        emb = self.embedder.extract(frame)
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

    def create_person(self, db: Session, created_by: int | None, data: dict[str, Any], files: list[UploadFile]) -> Person:
        person_code = f"PID-{uuid4().hex[:10].upper()}"
        person = Person(
            person_code=person_code,
            full_name=data["full_name"],
            email=data.get("email"),
            phone=data.get("phone"),
            department=data.get("department"),
            title=data.get("title"),
            notes=data.get("notes"),
            created_by=created_by,
            embedding_model=self.embedder.model_name,
        )
        db.add(person)
        db.flush()

        if not files:
            raise HTTPException(status_code=400, detail="At least one face image is required")
        for upload in files:
            file_path, raw = self._save_upload(upload, self.settings.abs_face_dir / person.person_code)
            frame = self._load_image(raw)
            self._store_face_sample(db, person, file_path, raw, frame)
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
        all_people = db.scalars(select(Person).where(Person.id != new_person.id, Person.is_active.is_(True))).all()
        if not all_people:
            return
        new_emb = self._person_average_embedding(db, new_person.id)
        if new_emb is None:
            return
        duplicates = []
        for p in all_people:
            emb = self._person_average_embedding(db, p.id)
            if emb is None:
                continue
            sim = float(np.dot(new_emb, emb))
            if sim >= self.settings.duplicate_similarity_threshold:
                duplicates.append((p, sim))
        if duplicates:
            person, _sim = sorted(duplicates, key=lambda t: t[1], reverse=True)[0]
            new_person.duplicate_of = person.id

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
        for emb in db.scalars(select(FaceEmbedding)).all():
            person = db.get(Person, emb.person_id)
            if not person:
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

    def list_persons(self, db: Session) -> list[dict[str, Any]]:
        rows = []
        persons = self.repo.list_persons(db)
        for p in persons:
            rows.append(
                {
                    "id": p.id,
                    "person_code": p.person_code,
                    "full_name": p.full_name,
                    "email": p.email,
                    "phone": p.phone,
                    "department": p.department,
                    "title": p.title,
                    "notes": p.notes,
                    "primary_image_path": p.primary_image_path,
                    "is_active": p.is_active,
                    "embedding_model": p.embedding_model,
                    "duplicate_of": p.duplicate_of,
                    "sample_count": self.repo.sample_count(db, p.id),
                    "created_at": p.created_at.isoformat() if p.created_at else None,
                }
            )
        return rows

    def recognize_image(self, db: Session, image_bytes: bytes, source_type: str, source_ref: str | None = None, frame_index: int = 0):
        frame = self._load_image(image_bytes)
        self.rebuild_index(db)
        matches = self.pipeline.analyze_face(frame)
        results = []
        for m in matches:
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
            )
            db.add(log)
            results.append(m)
        db.flush()
        return frame, results

    def process_video_file(self, db: Session, file_path: Path, source_ref: str | None = None):
        cap = cv2.VideoCapture(str(file_path))
        if not cap.isOpened():
            raise HTTPException(status_code=400, detail="Could not open video")
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
                matches = self.pipeline.analyze_face(frame)
                for m in matches:
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
                    )
                    db.add(log)
                    collected.append(m)
            frame_index += 1
        cap.release()
        db.flush()
        return collected
