from __future__ import annotations
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, oauth2_scheme
from app.models.recognition import AuditLog
from app.repositories.recognition_repo import RecognitionRepository
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, MeResponse, UserOut
from app.schemas.response_envelope import ResponseEnvelope
from app.services.auth_service import AuthService
from app.core.context import get_request_context

router = APIRouter(prefix="/auth", tags=["auth"])
svc = AuthService()
audit_repo = RecognitionRepository()

@router.post("/register", response_model=ResponseEnvelope[UserOut], status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    user = svc.register(db, payload)
    
    # Audit trail
    ctx = get_request_context()
    audit_repo.add_audit(db, AuditLog(
        actor_user_id=user.id,
        action="register",
        entity_type="user",
        entity_id=str(user.id),
        ip_address=ctx.client_ip
    ))
    
    db.commit()
    db.refresh(user)
    return ResponseEnvelope(data=user)


@router.post("/login", response_model=ResponseEnvelope[TokenResponse])
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    access_token, refresh_token, user = svc.login(db, payload)
    
    ctx = get_request_context()
    audit_repo.add_audit(db, AuditLog(
        actor_user_id=user.id,
        action="login",
        entity_type="user",
        ip_address=ctx.client_ip
    ))
    
    db.commit()
    return ResponseEnvelope(data=TokenResponse(access_token=access_token, refresh_token=refresh_token))


@router.post("/logout", response_model=ResponseEnvelope[None])
def logout(
    access_token: str = Depends(oauth2_scheme), 
    refresh_token: str | None = None,
    user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    svc.logout(access_token, refresh_token)
    
    ctx = get_request_context()
    audit_repo.add_audit(db, AuditLog(
        actor_user_id=user.id,
        action="logout",
        entity_type="user",
        ip_address=ctx.client_ip
    ))
    db.commit()
    return ResponseEnvelope(data=None)


@router.get("/me", response_model=ResponseEnvelope[MeResponse])
def me(user=Depends(get_current_user)):
    return ResponseEnvelope(data=user)
