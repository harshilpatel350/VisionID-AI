from __future__ import annotations
import logging
import json as _json
from logging.handlers import RotatingFileHandler
from pathlib import Path
from datetime import datetime, timezone

from app.config import load_settings


class _JSONFormatter(logging.Formatter):
    """Structured JSON log format for production observability."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        # Attach request_id if available in the context
        try:
            from app.core.context import current_request_id
            log_entry["request_id"] = current_request_id()
        except Exception:
            pass

        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)
        return _json.dumps(log_entry, default=str)


def configure_logging() -> None:
    settings = load_settings()
    log_dir = settings.abs_log_dir
    log_dir.mkdir(parents=True, exist_ok=True)

    # ── File handler (always JSON for machine parsing) ──────────
    file_handler = RotatingFileHandler(
        log_dir / "visionid.log",
        maxBytes=10_000_000,
        backupCount=10,
        encoding="utf-8",
    )
    file_handler.setFormatter(_JSONFormatter())

    # ── Console handler (human-readable in dev, JSON in prod) ──
    stream_handler = logging.StreamHandler()
    if settings.environment == "production":
        stream_handler.setFormatter(_JSONFormatter())
    else:
        human_formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        stream_handler.setFormatter(human_formatter)

    log_level = logging.DEBUG if settings.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        handlers=[file_handler, stream_handler],
        force=True,
    )

    # Silence noisy third-party loggers
    for noisy in ("urllib3", "httpcore", "httpx", "multipart", "PIL"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
