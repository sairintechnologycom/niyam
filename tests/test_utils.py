"""Tests for core utilities."""

from __future__ import annotations

from datetime import datetime, timezone

from niyam.core.utils import format_date_iso


def test_format_date_iso_utc() -> None:
    """Should format timezone-aware datetime to ISO-8601 UTC string."""
    dt = datetime(2026, 5, 30, 11, 49, 17, tzinfo=timezone.utc)
    assert format_date_iso(dt) == "2026-05-30T11:49:17Z"


def test_format_date_iso_naive() -> None:
    """Should treat naive datetime as UTC and format to ISO-8601 string."""
    dt = datetime(2026, 5, 30, 11, 49, 17)
    assert format_date_iso(dt) == "2026-05-30T11:49:17Z"
