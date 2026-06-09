"""Tests for Phase C Memory Ledger Redaction."""

from datetime import datetime, timezone
import pytest
from niyam.core.memory_ledger.models import MemoryRecord
from niyam.core.memory_ledger.redaction import redact_memory_records

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
    assert "sk-ant" not in redacted[1].content
    assert "[REDACTED_SECRET]" in redacted[1].content
    assert "sk-ant" not in redacted[1].summary
    assert "[REDACTED_SECRET]" in redacted[1].summary
    assert "sk-ant" not in redacted[1].metadata["secret_val"]
    assert "[REDACTED_SECRET]" in redacted[1].metadata["secret_val"]
