"""Niyam utilities module."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path


def format_date_iso(dt: datetime) -> str:
    """Format a datetime object into ISO-8601 UTC representation."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def compute_sha256(file_path: Path) -> str:
    """Compute SHA256 hash of a file."""
    h = hashlib.sha256()
    try:
        if not file_path.is_file():
            return "DIRECTORY"
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                h.update(chunk)
        return h.hexdigest()
    except Exception as e:
        return f"ERROR: {e}"
