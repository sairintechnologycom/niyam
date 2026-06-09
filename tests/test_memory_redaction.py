"""Tests for Phase C Memory Ledger Redaction."""

from datetime import datetime, timezone
import os
from pathlib import Path
from typer.testing import CliRunner

from niyam.cli import app
from niyam.core.memory import get_memory_dir
from niyam.core.memory_ledger.lineage import LocalMemoryLineageStore
from niyam.core.memory_ledger.local_store import LocalMemoryLedgerStore
from niyam.core.memory_ledger.models import MemoryRecord
from niyam.core.memory_ledger.redaction import redact_memory_records

runner = CliRunner()


def test_redact_command_removes_secrets_from_memory_records():
    now = datetime.now(timezone.utc)
    records = [
        MemoryRecord(
            id="mem-1",
            type="note",
            content="Normal content",
            created_at=now
        ),
        MemoryRecord(
            id="mem-2",
            type="note",
            content="Secret content sk-ant-1234567890123456789012345",
            summary="Also sk-ant-1234567890123456789012345",
            metadata={"secret_val": "sk-ant-1234567890123456789012345"},
            created_at=now
        )
    ]
    
    redacted, count = redact_memory_records(records)

    assert count == 1
    assert "sk-ant" in records[1].content
    assert "sk-ant" not in redacted[1].content
    assert "[REDACTED_SECRET]" in redacted[1].content
    assert "sk-ant" not in redacted[1].summary
    assert "[REDACTED_SECRET]" in redacted[1].summary
    assert "sk-ant" not in redacted[1].metadata["secret_val"]
    assert "[REDACTED_SECRET]" in redacted[1].metadata["secret_val"]


def test_redact_cli_writes_lineage_only_for_modified_records(niyam_repo: Path):
    os.chdir(niyam_repo)
    now = datetime.now(timezone.utc)
    store = LocalMemoryLedgerStore(get_memory_dir(niyam_repo) / "index.jsonl")
    store.replace_all(
        [
            MemoryRecord(
                id="mem-clean",
                type="note",
                content="Normal content",
                created_at=now,
            ),
            MemoryRecord(
                id="mem-secret",
                type="note",
                content="Secret sk-ant-1234567890123456789012345",
                created_at=now,
            ),
        ]
    )

    result = runner.invoke(app, ["memory", "redact"])
    assert result.exit_code == 0

    records = store.list_records()
    secret_record = next(record for record in records if record.id == "mem-secret")
    assert "sk-ant" not in secret_record.content

    lineage = LocalMemoryLineageStore(
        get_memory_dir(niyam_repo) / "lineage" / "recall-events.jsonl"
    )
    events = list(lineage.iter_events())
    assert [event.record_id for event in events if event.event_type == "redacted"] == [
        "mem-secret"
    ]
