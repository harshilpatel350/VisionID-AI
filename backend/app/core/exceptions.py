"""
VisionID AI — Structured Exception Hierarchy.

Every exception carries:
  • http_status  – the HTTP status code to return
  • error_code   – a machine-readable error tag (e.g. "AUTH_001")
  • message      – a safe, user-facing description
"""
from __future__ import annotations


class AppException(Exception):
    """Base for all application-level errors."""

    http_status: int = 500
    error_code: str = "INTERNAL_ERROR"

    def __init__(self, message: str = "An unexpected error occurred", *, details: dict | None = None):
        self.message = message
        self.details = details or {}
        super().__init__(message)


# ── Authentication ──────────────────────────────────────────────

class AuthenticationError(AppException):
    http_status = 401
    error_code = "AUTH_001"

    def __init__(self, message: str = "Authentication required"):
        super().__init__(message)


class TokenExpiredError(AppException):
    http_status = 401
    error_code = "AUTH_002"

    def __init__(self, message: str = "Token has expired"):
        super().__init__(message)


class InvalidTokenError(AppException):
    http_status = 401
    error_code = "AUTH_003"

    def __init__(self, message: str = "Invalid or malformed token"):
        super().__init__(message)


class AccountLockedError(AppException):
    http_status = 403
    error_code = "AUTH_004"

    def __init__(self, message: str = "Account temporarily locked due to too many failed attempts"):
        super().__init__(message)


class InvalidCredentialsError(AppException):
    http_status = 401
    error_code = "AUTH_005"

    def __init__(self, message: str = "Invalid username or password"):
        super().__init__(message)


# ── Authorization ───────────────────────────────────────────────

class AuthorizationError(AppException):
    http_status = 403
    error_code = "AUTHZ_001"

    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message)


# ── Resource errors ─────────────────────────────────────────────

class NotFoundError(AppException):
    http_status = 404
    error_code = "NOT_FOUND"

    def __init__(self, resource: str = "Resource", identifier: str | int | None = None):
        detail = f"{resource} not found"
        if identifier is not None:
            detail = f"{resource} with id '{identifier}' not found"
        super().__init__(detail)


class ConflictError(AppException):
    http_status = 409
    error_code = "CONFLICT"

    def __init__(self, message: str = "Resource already exists"):
        super().__init__(message)


# ── Validation ──────────────────────────────────────────────────

class ValidationError(AppException):
    http_status = 422
    error_code = "VALIDATION_ERROR"

    def __init__(self, message: str = "Validation failed", *, details: dict | None = None):
        super().__init__(message, details=details)


class FileTooLargeError(ValidationError):
    error_code = "FILE_TOO_LARGE"

    def __init__(self, max_mb: int):
        super().__init__(f"File exceeds maximum allowed size of {max_mb} MB")


class InvalidFileTypeError(ValidationError):
    error_code = "INVALID_FILE_TYPE"

    def __init__(self, allowed: list[str] | None = None):
        msg = "Unsupported file type"
        if allowed:
            msg += f". Allowed: {', '.join(allowed)}"
        super().__init__(msg)


class WeakPasswordError(ValidationError):
    error_code = "WEAK_PASSWORD"

    def __init__(self, reason: str = "Password does not meet strength requirements"):
        super().__init__(reason)


# ── Rate limiting ───────────────────────────────────────────────

class RateLimitError(AppException):
    http_status = 429
    error_code = "RATE_LIMIT"

    def __init__(self, message: str = "Too many requests. Please try again later."):
        super().__init__(message)


# ── AI / Processing ────────────────────────────────────────────

class AIProcessingError(AppException):
    http_status = 500
    error_code = "AI_ERROR"

    def __init__(self, message: str = "Face processing failed"):
        super().__init__(message)


class NoFaceDetectedError(AppException):
    http_status = 422
    error_code = "NO_FACE"

    def __init__(self, message: str = "No face detected in the provided image"):
        super().__init__(message)
