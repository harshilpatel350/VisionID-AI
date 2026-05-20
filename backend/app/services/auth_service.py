from __future__ import annotations
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.auth import RegisterRequest, LoginRequest

class AuthService:
    def __init__(self):
        self.repo = UserRepository()

    def register(self, db: Session, payload: RegisterRequest) -> User:
        if self.repo.get_by_email(db, payload.email):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
        user = User(
            full_name=payload.full_name,
            email=payload.email.lower(),
            password_hash=hash_password(payload.password),
            role="viewer",
            is_active=True,
        )
        db.add(user)
        db.flush()
        return user

    def login(self, db: Session, payload: LoginRequest) -> tuple[str, User]:
        user = self.repo.get_by_email(db, payload.email.lower())
        if not user or not verify_password(payload.password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is inactive")
        token = create_access_token(subject=str(user.id), extras={"role": user.role, "email": user.email})
        return token, user
