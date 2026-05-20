from __future__ import annotations
import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class Settings(BaseModel):
    app_name: str = "VisionID AI"
    environment: str = "local"
    api_prefix: str = "/api"
    host: str = "0.0.0.0"
    port: int = 8000
    secret_key: str = "visionid-ai-local-secret-key-change-me"
    access_token_expire_minutes: int = 1440
    database_url: str = "mysql+pymysql://root:root@127.0.0.1:3306/visionid_ai?charset=utf8mb4"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000", "http://127.0.0.1:3000"])
    auto_create_tables: bool = True
    use_redis_cache: bool = False
    redis_url: str = "redis://127.0.0.1:6379/0"
    upload_dir: str = "storage/uploads"
    face_dir: str = "storage/faces"
    report_dir: str = "storage/reports"
    log_dir: str = "storage/logs"
    recognition_cooldown_seconds: int = 30
    recognition_threshold: float = 0.45
    duplicate_similarity_threshold: float = 0.92
    quality_min_score: float = 0.35
    frame_skip: int = 3
    max_batch_frames: int = 25

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


@lru_cache(maxsize=1)
def load_settings() -> Settings:
    config_path = Path(__file__).resolve().parents[1] / "config" / "settings.json"
    data: dict[str, Any] = {}
    if config_path.exists():
        data = json.loads(config_path.read_text(encoding="utf-8"))
    settings = Settings(**data)
    for d in (settings.abs_upload_dir, settings.abs_face_dir, settings.abs_report_dir, settings.abs_log_dir):
        d.mkdir(parents=True, exist_ok=True)
    return settings
