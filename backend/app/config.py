from __future__ import annotations
import json
import logging
import secrets
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


logger = logging.getLogger("visionid")

_IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".webp"]
_VIDEO_EXTENSIONS = [".mp4", ".avi", ".mov", ".mkv", ".webm"]


class Settings(BaseModel):
    # ── Application ─────────────────────────────────────────────
    app_name: str = "VisionID AI"
    environment: str = "local"  # local | staging | production
    debug: bool = False
    api_prefix: str = "/api"
    host: str = "0.0.0.0"
    port: int = 8000

    # ── Security ────────────────────────────────────────────────
    secret_key: str = ""  # auto-generated if blank or default
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # ── Brute-force protection ──────────────────────────────────
    max_login_attempts: int = 5
    login_lockout_minutes: int = 15

    # ── Database ────────────────────────────────────────────────
    database_url: str = "sqlite:///storage/visionid.db"
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_timeout: int = 30
    db_pool_recycle: int = 1800
    db_echo: bool = False

    # ── CORS ────────────────────────────────────────────────────
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000", "http://127.0.0.1:3000"])

    auto_create_tables: bool = True

    # ── Redis ───────────────────────────────────────────────────
    use_redis_cache: bool = False
    redis_url: str = "redis://127.0.0.1:6379/0"

    # ── Storage ─────────────────────────────────────────────────
    upload_dir: str = "storage/uploads"
    face_dir: str = "storage/faces"
    report_dir: str = "storage/reports"
    log_dir: str = "storage/logs"
    unknown_face_dir: str = "storage/unknowns"

    # ── Upload limits ───────────────────────────────────────────
    max_upload_size_mb: int = 10
    max_video_size_mb: int = 100
    allowed_image_extensions: list[str] = Field(default_factory=lambda: _IMAGE_EXTENSIONS)
    allowed_video_extensions: list[str] = Field(default_factory=lambda: _VIDEO_EXTENSIONS)

    # ── Recognition & AI tuning ─────────────────────────────────
    recognition_cooldown_seconds: int = 30
    recognition_threshold: float = 0.45
    duplicate_similarity_threshold: float = 0.92
    prevent_duplicate_registration: bool = True
    quality_min_score: float = 0.35
    frame_skip: int = 3
    max_batch_frames: int = 25
    low_light_threshold: int = 60
    enhancement_gamma: float = 1.2
    enhancement_clip_limit: float = 2.0
    auto_low_light_enhance: bool = True
    liveness_enabled: bool = True
    liveness_threshold: float = 0.5
    liveness_mode: str = "enhanced"  # light | enhanced
    liveness_motion_weight: float = 0.3
    emotion_enabled: bool = True
    emotion_backend: str = "auto"  # fer | deepface | auto
    emotion_fast_in_live: bool = True

    # ── Snapshot storage ────────────────────────────────────────
    save_recognition_snapshots: bool = False
    recognition_snapshot_dir: str = "storage/snapshots/recognitions"
    save_unknown_snapshots: bool = True

    # ── Unknown similarity ──────────────────────────────────────
    unknown_similarity_threshold: float = 0.85
    unknown_similarity_top_k: int = 8

    # ── Rate limiting ───────────────────────────────────────────
    rate_limit_per_minute: int = 240
    rate_limit_login_per_minute: int = 10
    ws_max_connections_per_ip: int = 3
    ws_max_fps: int = 15

    # ── Export limits ───────────────────────────────────────────
    export_max_rows: int = 50_000

    @property
    def base_dir(self) -> Path:
        return Path(__file__).resolve().parents[2]

    @property
    def abs_upload_dir(self) -> Path:
        return self.base_dir / self.upload_dir

    @property
    def abs_face_dir(self) -> Path:
        return self.base_dir / self.face_dir

    @property
    def abs_report_dir(self) -> Path:
        return self.base_dir / self.report_dir

    @property
    def abs_log_dir(self) -> Path:
        return self.base_dir / self.log_dir

    @property
    def abs_unknown_face_dir(self) -> Path:
        return self.base_dir / self.unknown_face_dir

    @property
    def abs_recognition_snapshot_dir(self) -> Path:
        return self.base_dir / self.recognition_snapshot_dir

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def max_video_bytes(self) -> int:
        return self.max_video_size_mb * 1024 * 1024


def _ensure_secure_key(settings: Settings) -> None:
    """Replace weak / placeholder secret keys with a cryptographically random one."""
    weak_defaults = {"", "visionid-ai-local-secret-key-change-me", "changeme", "secret"}
    if settings.secret_key.strip().lower() in weak_defaults:
        generated = secrets.token_urlsafe(64)
        settings.secret_key = generated
        logger.warning(
            "SECURITY: secret_key was blank or default. "
            "A random key has been generated for this session. "
            "Set a permanent key in config/settings.json for production."
        )


@lru_cache(maxsize=1)
def load_settings() -> Settings:
    config_path = Path(__file__).resolve().parents[1] / "config" / "settings.json"
    data: dict[str, Any] = {}
    if config_path.exists():
        data = json.loads(config_path.read_text(encoding="utf-8"))
    settings = Settings(**data)
    _ensure_secure_key(settings)
    for d in (
        settings.abs_upload_dir,
        settings.abs_face_dir,
        settings.abs_report_dir,
        settings.abs_log_dir,
        settings.abs_unknown_face_dir,
        settings.abs_recognition_snapshot_dir,
    ):
        d.mkdir(parents=True, exist_ok=True)
    return settings
