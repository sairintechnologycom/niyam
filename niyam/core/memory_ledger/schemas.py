"""Schemas for Memory Ledger APIs."""

from __future__ import annotations

from pydantic import BaseModel
from niyam.core.memory_ledger.models import MemoryRecord


class MemoryManifest(BaseModel):
    """Manifest representing exported memory records."""
    records: list[MemoryRecord]
