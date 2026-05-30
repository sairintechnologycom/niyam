"""Sutra utilities module."""

from __future__ import annotations

from datetime import datetime, timezone


def format_date_iso(dt: datetime) -> str:
    """Format a datetime object into ISO-8601 UTC representation."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
