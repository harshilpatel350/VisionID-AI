from __future__ import annotations
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app.config import load_settings


def configure_logging() -> None:
    settings = load_settings()
    log_dir = settings.abs_log_dir
    log_dir.mkdir(parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(log_dir / "visionid.log", maxBytes=5_000_000, backupCount=5, encoding="utf-8")
    stream_handler = logging.StreamHandler()
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)
    logging.basicConfig(level=logging.INFO, handlers=[file_handler, stream_handler], force=True)
