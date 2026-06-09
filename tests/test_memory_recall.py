"""Tests for Phase C Memory Ledger Recall."""

from datetime import datetime, timezone
from niyam.core.memory_ledger.models import MemoryRecord
from niyam.core.memory_ledger.recall import recall_records


def test_recall_returns_keyword_matches():
    now = datetime.now(timezone.utc)
    records = [
        MemoryRecord(id="mem-1", type="note", content="apples are red", created_at=now),
        MemoryRecord(id="mem-2", type="note", content="bananas are yellow", created_at=now),
        MemoryRecord(id="mem-3", type="note", content="apples and bananas", created_at=now),
    ]

    results = recall_records(records, "apples")
    assert len(results) == 2
    
    results_limit = recall_records(records, "apples", limit=1)
    assert len(results_limit) == 1
    # mem-3 has 'apples', mem-1 has 'apples'. Both count=1. Either can be returned depending on sort stability.
    assert "apples" in results_limit[0].content
