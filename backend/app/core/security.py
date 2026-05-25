from __future__ import annotations
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import jwt, JWTError, ExpiredSignatureError
from passlib.context import CryptContext

from app.config import load_settings
from app.core.exceptions import (
    InvalidTokenError,
    TokenExpiredError,
    WeakPasswordError,
)
from app.core.token_blacklist import blacklist

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ── Password hashing ───────────────────────────────────────────

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


# ── Password strength validation ───────────────────────────────

def validate_password_strength(password: str) -> None:
    """Raise WeakPasswordError if password does not meet policy."""
    errors: list[str] = []
    if len(password) < 8:
        errors.append("at least 8 characters")
    if not any(c.isupper() for c in password):
        errors.append("at least one uppercase letter")
    if not any(c.islower() for c in password):
        errors.append("at least one lowercase letter")
    if not any(c.isdigit() for c in password):
        errors.append("at least one digit")
    if not any(c in "!@#$%^&*()-_=+[]{}|;:',.<>?/`~" for c in password):
        errors.append("at least one special character")
    if errors:
        raise WeakPasswordError(f"Password must contain: {'; '.join(errors)}")


# ── JWT tokens ──────────────────────────────────────────────────

def _build_token(
    subject: str,
    token_type: str,
    expire_delta: timedelta,
    extras: dict[str, Any] | None = None,
) -> str:
    settings = load_settings()
    now = datetime.now(timezone.utc)
    jti = uuid.uuid4().hex
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "jti": jti,
        "iat": int(now.timestamp()),
        "exp": int((now + expire_delta).timestamp()),
    }
    if extras:
        payload.update(extras)
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def create_access_token(subject: str, extras: dict[str, Any] | None = None) -> str:
    settings = load_settings()
    return _build_token(
        subject,
        token_type="access",
        expire_delta=timedelta(minutes=settings.access_token_expire_minutes),
        extras=extras,
    )


def create_refresh_token(subject: str) -> str:
    settings = load_settings()
    return _build_token(
        subject,
        token_type="refresh",
        expire_delta=timedelta(days=settings.refresh_token_expire_days),
    )


def decode_token(token: str, *, expected_type: str = "access") -> dict[str, Any]:
    """
    Decode and validate a JWT.

    Raises:
        TokenExpiredError  – if the token has expired.
        InvalidTokenError  – if the token is malformed, wrong type, or revoked.
    """
    settings = load_settings()
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except ExpiredSignatureError:
        raise TokenExpiredError()
    except JWTError:
        raise InvalidTokenError()

    # Check token type matches expectation
    if payload.get("type") != expected_type:
        raise InvalidTokenError(f"Expected {expected_type} token")

    # Check blacklist
    jti = payload.get("jti")
    if jti and blacklist.is_revoked(jti):
        raise InvalidTokenError("Token has been revoked")

    return payload


def revoke_token(token: str) -> None:
    """Revoke an access or refresh token by adding its JTI to the blacklist."""
    settings = load_settings()
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm], options={"verify_exp": False})
    except JWTError:
        return  # Nothing to revoke if we can't parse it
    jti = payload.get("jti")
    exp = payload.get("exp", 0)
    if jti:
        blacklist.revoke(jti, float(exp))
