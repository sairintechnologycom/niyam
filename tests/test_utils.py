"""Tests for core utilities."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from niyam.core.utils import format_date_iso, compute_sha256


def test_format_date_iso_utc() -> None:
    """Should format timezone-aware datetime to ISO-8601 UTC string."""
    dt = datetime(2026, 5, 30, 11, 49, 17, tzinfo=timezone.utc)
    assert format_date_iso(dt) == "2026-05-30T11:49:17Z"


def test_format_date_iso_naive() -> None:
    """Should treat naive datetime as UTC and format to ISO-8601 string."""
    dt = datetime(2026, 5, 30, 11, 49, 17)
    assert format_date_iso(dt) == "2026-05-30T11:49:17Z"


def test_compute_sha256_file(tmp_path: Path) -> None:
    """Should compute correct SHA256 hash for a file."""
    f = tmp_path / "test.txt"
    f.write_text("niyam test", encoding="utf-8")
    
    import hashlib
    expected = hashlib.sha256("niyam test".encode("utf-8")).hexdigest()
    
    assert compute_sha256(f) == expected


def test_compute_sha256_directory(tmp_path: Path) -> None:
    """Should return DIRECTORY for a directory path."""
    assert compute_sha256(tmp_path) == "DIRECTORY"


def test_compute_sha256_missing_file(tmp_path: Path) -> None:
    """Should return ERROR for a missing file."""
    missing = tmp_path / "missing.txt"
    assert compute_sha256(missing).startswith("ERROR")
