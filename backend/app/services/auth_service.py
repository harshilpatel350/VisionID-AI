from __future__ import annotations
import time
from sqlalchemy.orm import Session
from fastapi import Request

from app.config import load_settings
from app.core.context import get_request_context
from app.core.exceptions import (
    AccountLockedError,
    ConflictError,
    InvalidCredentialsError,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    validate_password_strength,
    verify_password,
    revoke_token,
)
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.auth import RegisterRequest, LoginRequest


class AuthService:
    def __init__(self):
        self.repo = UserRepository()
        self.settings = load_settings()
        # In-memory brute-force tracking: ip -> { email: { 'attempts': int, 'locked_until': float } }
        self._failed_attempts: dict[str, dict[str, dict[str, float]]] = {}

    def _check_bruteforce(self, ip: str, email: str) -> None:
        """Raise error if the account/IP combo is locked."""
        ip_tracker = self._failed_attempts.get(ip, {})
        entry = ip_tracker.get(email)
        if entry:
            if entry["attempts"] >= self.settings.max_login_attempts:
                if time.time() < entry["locked_until"]:
                    raise AccountLockedError()
                else:
                    # Lock expired, reset
                    entry["attempts"] = 0
                    entry["locked_until"] = 0

    def _record_failed_attempt(self, ip: str, email: str) -> None:
        if ip not in self._failed_attempts:
            self._failed_attempts[ip] = {}
        if email not in self._failed_attempts[ip]:
            self._failed_attempts[ip][email] = {"attempts": 0, "locked_until": 0.0}
        
        entry = self._failed_attempts[ip][email]
        entry["attempts"] += 1
        
        if entry["attempts"] >= self.settings.max_login_attempts:
            entry["locked_until"] = time.time() + (self.settings.login_lockout_minutes * 60)

    def _record_success(self, ip: str, email: str) -> None:
        if ip in self._failed_attempts and email in self._failed_attempts[ip]:
            self._failed_attempts[ip][email]["attempts"] = 0
            self._failed_attempts[ip][email]["locked_until"] = 0.0

    def register(self, db: Session, payload: RegisterRequest) -> User:
        if self.repo.get_by_email(db, payload.email.lower()):
            raise ConflictError("Email already registered")
            
        validate_password_strength(payload.password)
        
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

    def login(self, db: Session, payload: LoginRequest) -> tuple[str, str, User]:
        """Returns (access_token, refresh_token, user)."""
        ctx = get_request_context()
        email = payload.email.lower()
        
        self._check_bruteforce(ctx.client_ip, email)

        user = self.repo.get_by_email(db, email)
        if not user or not verify_password(payload.password, user.password_hash):
            self._record_failed_attempt(ctx.client_ip, email)
            raise InvalidCredentialsError()

        if not user.is_active:
            raise AccountLockedError("User account is inactive")

        self._record_success(ctx.client_ip, email)

        access_token = create_access_token(
            subject=str(user.id),
            extras={"role": user.role, "email": user.email}
        )
        refresh_token = create_refresh_token(subject=str(user.id))
        
        return access_token, refresh_token, user

    def logout(self, access_token: str | None, refresh_token: str | None) -> None:
        if access_token:
            revoke_token(access_token)
        if refresh_token:
            revoke_token(refresh_token)
