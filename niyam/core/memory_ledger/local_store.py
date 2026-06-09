"""Local Memory Ledger Store."""

from __future__ import annotations

import fcntl
import json
from pathlib import Path
from typing import Iterator

from niyam.core.memory_ledger.models import MemoryRecord


class LocalMemoryLedgerStore:
    """Manages local JSONL storage for the memory ledger."""

    def __init__(self, index_path: Path):
        """Initialize with the path to the index.jsonl file."""
        self.index_path = index_path

    def init_store(self) -> None:
        """Initialize the store, creating directories and the file if they do not exist."""
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.index_path.exists():
            self.index_path.touch()

    def append(self, record: MemoryRecord) -> None:
        """Append a record to the ledger."""
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.index_path, "a+", encoding="utf-8") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            try:
                # Use model_dump_json to serialize datetimes properly
                f.write(record.model_dump_json(exclude_none=True) + "\n")
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)

    def list_records(self) -> list[MemoryRecord]:
        """List all records in the ledger."""
        return list(self.iter_records())

    def iter_records(self) -> Iterator[MemoryRecord]:
        """Iterate over records in the ledger."""
        if not self.index_path.exists():
            return

        with open(self.index_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                data = json.loads(line)
                yield MemoryRecord.model_validate(data)

    def validate_store(self) -> bool:
        """Validate all records in the store. Raises ValueError if invalid."""
        if not self.index_path.exists():
            return True

        with open(self.index_path, "r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    MemoryRecord.model_validate(data)
                except Exception as e:
                    raise ValueError(f"Line {line_no} is invalid: {e}")
        return True
