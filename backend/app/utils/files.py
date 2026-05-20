from __future__ import annotations
import hashlib
from pathlib import Path
from uuid import uuid4

def safe_slug(text: str) -> str:
    return "".join(c.lower() if c.isalnum() else "-" for c in text).strip("-")

def unique_filename(prefix: str, suffix: str) -> str:
    return f"{prefix}_{uuid4().hex}{suffix}"

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
