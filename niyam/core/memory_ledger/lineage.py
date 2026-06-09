"""Lineage events tracking for Memory Ledger."""

from __future__ import annotations

import fcntl
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Iterator

from niyam.core.memory_ledger.models import MemoryLineageEvent


class LocalMemoryLineageStore:
    """Manages local JSONL storage for memory lineage events."""

    def __init__(self, index_path: Path):
        """Initialize with the path to the recall-events.jsonl file."""
        self.index_path = index_path

    def init_store(self) -> None:
        """Initialize the store."""
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.index_path.exists():
            self.index_path.touch()

    def append(self, event: MemoryLineageEvent) -> None:
        """Append an event to the lineage."""
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.index_path, "a+", encoding="utf-8") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            try:
                f.write(event.model_dump_json(exclude_none=True) + "\n")
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)

    def iter_events(self) -> Iterator[MemoryLineageEvent]:
        """Iterate over all events."""
        if not self.index_path.exists():
            return

        with open(self.index_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    yield MemoryLineageEvent.model_validate(data)
                except Exception:
                    pass

    def get_events_for_record(self, record_id: str) -> list[MemoryLineageEvent]:
        """Get all events related to a specific record_id."""
        events = []
        for event in self.iter_events():
            if event.record_id == record_id:
                events.append(event)
        return events


def create_lineage_event(
    event_type: str,
    record_id: str | None = None,
    actor: str | None = None,
    task_id: str | None = None,
    source_ref: str | None = None,
    reason: str | None = None,
    metadata: dict | None = None
) -> MemoryLineageEvent:
    """Helper to create a MemoryLineageEvent with auto-generated id and timestamp."""
    event_id = datetime.now(timezone.utc).strftime("evt-%Y%m%d%H%M%S%f")
    return MemoryLineageEvent(
        id=event_id,
        timestamp=datetime.now(timezone.utc),
        event_type=event_type, # type: ignore
        record_id=record_id,
        actor=actor,
        task_id=task_id,
        source_ref=source_ref,
        reason=reason,
        metadata=metadata or {}
    )
