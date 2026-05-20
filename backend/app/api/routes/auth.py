from __future__ import annotations
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, MeResponse, UserOut
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])
svc = AuthService()

@router.post("/register", response_model=UserOut)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    user = svc.register(db, payload)
    db.commit()
    db.refresh(user)
    return user

@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    token, _user = svc.login(db, payload)
    db.commit()
    return TokenResponse(access_token=token)

@router.get("/me", response_model=MeResponse)
def me(user=Depends(get_current_user)):
    return user
