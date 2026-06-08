"""Niyam utilities module."""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def format_date_iso(dt: datetime) -> str:
    """Format a datetime object into ISO-8601 UTC representation."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def compute_sha256(file_path: Path) -> str:
    """Compute SHA256 hash of a file."""
    if not file_path.exists():
        return f"ERROR: File not found: {file_path}"
    if file_path.is_dir():
        return "DIRECTORY"
    
    h = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                h.update(chunk)
        return h.hexdigest()
    except Exception as e:
        return f"ERROR: {e}"


def configure_logging(json_logs: bool = False, level: int = logging.INFO) -> None:
    """Configure structured logging with a stdlib fallback."""
    try:
        import structlog

        renderer = (
            structlog.processors.JSONRenderer()
            if json_logs
            else structlog.dev.ConsoleRenderer()
        )
        logging.basicConfig(level=level)
        structlog.configure(
            processors=[
                structlog.processors.TimeStamper(fmt="iso", utc=True),
                structlog.processors.add_log_level,
                renderer,
            ],
            wrapper_class=structlog.make_filtering_bound_logger(level),
            logger_factory=structlog.PrintLoggerFactory(),
            cache_logger_on_first_use=True,
        )
    except Exception:
        logging.basicConfig(
            level=level,
            format="%(asctime)s %(name)s %(levelname)s %(message)s",
        )


def get_logger(name: str, **context: Any):
    """Return a structured logger when available, else a stdlib logger."""
    try:
        import structlog

        return structlog.get_logger(name).bind(**context)
    except Exception:
        return logging.getLogger(name)
