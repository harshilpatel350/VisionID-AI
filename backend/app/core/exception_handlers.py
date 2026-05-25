"""
Global exception handlers registered on the FastAPI app.

• AppException subtypes → structured JSON with the appropriate status code.
• Pydantic RequestValidationError → 422 with field-level details.
• Unhandled Exception → 500 with a generic message (internals logged, not leaked).
"""
from __future__ import annotations

import logging
import traceback

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette.responses import JSONResponse

from app.core.context import current_request_id
from app.core.exceptions import AppException

logger = logging.getLogger("visionid")


def _error_envelope(
    status: int,
    code: str,
    message: str,
    details: dict | list | None = None,
) -> JSONResponse:
    body: dict = {
        "success": False,
        "error": {
            "code": code,
            "message": message,
            "request_id": current_request_id(),
        },
    }
    if details:
        body["error"]["details"] = details
    return JSONResponse(status_code=status, content=body)


async def app_exception_handler(_request: Request, exc: AppException) -> JSONResponse:
    logger.warning(
        "AppException | code=%s status=%s msg=%s details=%s",
        exc.error_code,
        exc.http_status,
        exc.message,
        exc.details,
    )
    return _error_envelope(exc.http_status, exc.error_code, exc.message, exc.details or None)


async def validation_exception_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = []
    for err in exc.errors():
        errors.append({
            "field": " → ".join(str(loc) for loc in err.get("loc", [])),
            "message": err.get("msg", ""),
            "type": err.get("type", ""),
        })
    return _error_envelope(422, "VALIDATION_ERROR", "Request validation failed", errors)


async def unhandled_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    logger.error(
        "Unhandled exception | request_id=%s\n%s",
        current_request_id(),
        traceback.format_exc(),
    )
    return _error_envelope(500, "INTERNAL_ERROR", "An unexpected error occurred. Please try again.")


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppException, app_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unhandled_exception_handler)  # type: ignore[arg-type]
