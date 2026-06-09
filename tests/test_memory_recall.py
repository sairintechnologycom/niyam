"""Tests for Phase C Memory Ledger Recall."""

import os
from datetime import datetime, timezone
from pathlib import Path
from typer.testing import CliRunner

from niyam.cli import app
from niyam.core.memory import get_memory_dir
from niyam.core.memory_ledger.lineage import LocalMemoryLineageStore
from niyam.core.memory_ledger.local_store import LocalMemoryLedgerStore
from niyam.core.memory_ledger.models import MemoryRecord
from niyam.core.memory_ledger.recall import recall_records

runner = CliRunner()


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


def test_recall_cli_writes_lineage_event(niyam_repo: Path):
    os.chdir(niyam_repo)
    store = LocalMemoryLedgerStore(get_memory_dir(niyam_repo) / "index.jsonl")
    store.replace_all(
        [
            MemoryRecord(
                id="mem-recall",
                type="note",
                content="Terraform deployment preference",
                created_at=datetime.now(timezone.utc),
            )
        ]
    )

    result = runner.invoke(app, ["memory", "recall", "terraform"])
    assert result.exit_code == 0
    assert "mem-recall" in result.output

    lineage = LocalMemoryLineageStore(
        get_memory_dir(niyam_repo) / "lineage" / "recall-events.jsonl"
    )
    events = lineage.get_events_for_record("mem-recall")
    assert any(event.event_type == "recalled" for event in events)
