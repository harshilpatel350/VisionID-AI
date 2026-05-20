from __future__ import annotations
from sqlalchemy import func, select, delete
from sqlalchemy.orm import Session
from app.models.face import Person, FaceSample, FaceEmbedding

class FaceRepository:
    def list_persons(self, db: Session) -> list[Person]:
        return list(db.scalars(select(Person).order_by(Person.created_at.desc())).all())

    def get_person(self, db: Session, person_id: int) -> Person | None:
        return db.get(Person, person_id)

    def find_by_code(self, db: Session, code: str) -> Person | None:
        return db.scalar(select(Person).where(Person.person_code == code))

    def find_by_name(self, db: Session, name: str) -> Person | None:
        return db.scalar(select(Person).where(Person.full_name == name))

    def create_person(self, db: Session, person: Person) -> Person:
        db.add(person); db.flush(); return person

    def add_sample(self, db: Session, sample: FaceSample) -> FaceSample:
        db.add(sample); db.flush(); return sample

    def add_embedding(self, db: Session, emb: FaceEmbedding) -> FaceEmbedding:
        db.add(emb); db.flush(); return emb

    def sample_count(self, db: Session, person_id: int) -> int:
        return db.scalar(select(func.count(FaceSample.id)).where(FaceSample.person_id == person_id)) or 0

    def delete_person(self, db: Session, person: Person) -> None:
        db.delete(person)

    def list_embeddings(self, db: Session):
        return list(db.scalars(select(FaceEmbedding).order_by(FaceEmbedding.created_at.desc())).all())

    def list_samples(self, db: Session, person_id: int | None = None):
        stmt = select(FaceSample).order_by(FaceSample.created_at.desc())
        if person_id is not None:
            stmt = stmt.where(FaceSample.person_id == person_id)
        return list(db.scalars(stmt).all())

    def set_duplicate(self, db: Session, person: Person, duplicate_of: int | None):
        person.duplicate_of = duplicate_of
        db.flush()
        return person
