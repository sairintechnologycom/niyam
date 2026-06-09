"""Tests for Phase C Memory Ledger Evidence."""

import os
from pathlib import Path
from datetime import datetime, timezone, timedelta

from niyam.core.evidence import run_generate_evidence
from niyam.core.memory import get_memory_dir
from niyam.core.memory_ledger.lineage import LocalMemoryLineageStore, create_lineage_event
from niyam.core.memory_ledger.local_store import LocalMemoryLedgerStore
from niyam.core.memory_ledger.models import MemoryRecord

def test_evidence_without_memory_is_unchanged(niyam_repo: Path):
    os.chdir(niyam_repo)
    out = run_generate_evidence(fmt="markdown", include="scan,guard")
    assert "Memory Ledger Posture" not in out
    
def test_evidence_with_memory_includes_summary(niyam_repo: Path):
    os.chdir(niyam_repo)
    store = LocalMemoryLedgerStore(get_memory_dir(niyam_repo) / "index.jsonl")
    store.replace_all(
        [
            MemoryRecord(
                id="mem-evidence",
                type="note",
                content="Evidence memory",
                scope="project",
                expires_at=datetime.now(timezone.utc) - timedelta(days=1),
                created_at=datetime.now(timezone.utc),
            )
        ]
    )
    lineage = LocalMemoryLineageStore(
        get_memory_dir(niyam_repo) / "lineage" / "recall-events.jsonl"
    )
    lineage.append(
        create_lineage_event(
            "recalled",
            record_id="mem-evidence",
            reason="evidence test",
        )
    )

    out = run_generate_evidence(fmt="markdown", include="scan,guard,memory")
    assert "Memory Ledger Posture" in out
    assert "Expired Records:** 1" in out
    assert "Note**: 1" in out
