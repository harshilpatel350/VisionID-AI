from __future__ import annotations
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.user import User

class UserRepository:
    def get_by_email(self, db: Session, email: str) -> User | None:
        return db.scalar(select(User).where(User.email == email))

    def get_by_id(self, db: Session, user_id: int) -> User | None:
        return db.get(User, user_id)

    def list_users(self, db: Session) -> list[User]:
        return list(db.scalars(select(User).order_by(User.created_at.desc())).all())

    def create(self, db: Session, user: User) -> User:
        db.add(user)
        db.flush()
        return user
