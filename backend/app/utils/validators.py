"""
Input validation utilities for uploads, filenames, and content type checking.
"""
from __future__ import annotations
import re
from pathlib import Path

from fastapi import UploadFile

from app.config import load_settings
from app.core.exceptions import FileTooLargeError, InvalidFileTypeError, ValidationError

# Magic bytes for common image formats
_MAGIC_BYTES: dict[str, list[bytes]] = {
    ".jpg":  [b"\xff\xd8\xff"],
    ".jpeg": [b"\xff\xd8\xff"],
    ".png":  [b"\x89PNG\r\n\x1a\n"],
    ".webp": [b"RIFF"],
    ".gif":  [b"GIF87a", b"GIF89a"],
}

_ALLOWED_MIME_IMAGES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
_ALLOWED_MIME_VIDEOS = {"video/mp4", "video/quicktime", "video/x-msvideo", "video/webm", "video/x-matroska"}

_DANGEROUS_FILENAME_RE = re.compile(r"[^\w\s\-.]", re.UNICODE)


def sanitize_filename(raw_name: str | None) -> str:
    """
    Remove dangerous characters and prevent path-traversal.
    Returns a safe, flat filename.
    """
    if not raw_name:
        return "upload"
    # Take only the basename (strip any directory components)
    name = Path(raw_name).name
    # Remove dangerous characters
    name = _DANGEROUS_FILENAME_RE.sub("_", name)
    # Collapse multiple underscores
    name = re.sub(r"_+", "_", name).strip("_")
    return name or "upload"


def validate_image_upload(upload: UploadFile) -> bytes:
    """
    Read and validate an image upload. Returns the raw bytes.

    Checks:
    1. File size ≤ max_upload_size_mb
    2. Extension is in the allowed list
    3. MIME type matches an image type
    4. Magic bytes match the claimed extension
    """
    settings = load_settings()
    raw = upload.file.read()
    upload.file.seek(0)

    # Size check
    if len(raw) > settings.max_upload_bytes:
        raise FileTooLargeError(settings.max_upload_size_mb)

    # Extension check
    ext = Path(upload.filename or "").suffix.lower()
    if ext not in settings.allowed_image_extensions:
        raise InvalidFileTypeError(settings.allowed_image_extensions)

    # MIME check (best-effort — browsers don't always set this correctly)
    if upload.content_type and upload.content_type not in _ALLOWED_MIME_IMAGES:
        raise InvalidFileTypeError(settings.allowed_image_extensions)

    # Magic bytes check
    _verify_magic_bytes(raw, ext)

    return raw


def validate_video_upload(upload: UploadFile) -> bytes:
    """Read and validate a video upload. Returns the raw bytes."""
    settings = load_settings()
    raw = upload.file.read()
    upload.file.seek(0)

    if len(raw) > settings.max_video_bytes:
        raise FileTooLargeError(settings.max_video_size_mb)

    ext = Path(upload.filename or "").suffix.lower()
    if ext not in settings.allowed_video_extensions:
        raise InvalidFileTypeError(settings.allowed_video_extensions)

    return raw


def _verify_magic_bytes(data: bytes, ext: str) -> None:
    """Verify that file header bytes match the claimed extension."""
    signatures = _MAGIC_BYTES.get(ext)
    if not signatures:
        return  # No known signature for this extension, skip check
    if not any(data[:len(sig)] == sig for sig in signatures):
        raise InvalidFileTypeError([ext])


def validate_pagination(page: int, page_size: int, max_page_size: int = 100) -> tuple[int, int]:
    """Validate and clamp pagination parameters. Returns (offset, limit)."""
    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 20
    if page_size > max_page_size:
        page_size = max_page_size
    offset = (page - 1) * page_size
    return offset, page_size
