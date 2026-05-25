from __future__ import annotations
from typing import Generator

from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.context import get_request_context
from app.core.exceptions import AuthenticationError, AuthorizationError
from app.core.security import decode_token
from app.db.session import SessionLocal
from app.models.user import User
from app.repositories.user_repo import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)
user_repo = UserRepository()

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_optional_current_user(
    request: Request,
    db: Session = Depends(get_db),
    token: str | None = Depends(oauth2_scheme),
) -> User | None:
    """Returns the current user if token is valid, otherwise None (doesn't abort)."""
    if not token:
        # Check query param for WebSockets / specialized endpoints
        token = request.query_params.get("token")
        if not token:
            return None

    try:
        payload = decode_token(token, expected_type="access")
        user_id = int(payload.get("sub", 0))
    except Exception:
        return None

    user = user_repo.get_by_id(db, user_id)
    if not user or not user.is_active:
        return None

    # Attach to context for audit trails
    ctx = get_request_context()
    ctx.user_id = user.id
    ctx.user_role = user.role
    return user


def get_current_user(user: User | None = Depends(get_optional_current_user)) -> User:
    """Requires an active authenticated user."""
    if not user:
        raise AuthenticationError("Not authenticated")
    return user


def require_roles(*roles: str):
    """Requires the user to have one of the specified roles."""
    def _dep(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise AuthorizationError(f"Requires one of roles: {', '.join(roles)}")
        return user
    return _dep
