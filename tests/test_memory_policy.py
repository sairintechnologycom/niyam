"""Tests for Phase C Memory Ledger Policy."""

import pytest
from datetime import datetime, timezone, timedelta

from niyam.core.memory_ledger.models import MemoryRecord, MemoryPolicy
from niyam.core.memory_ledger.policy import check_record


def create_record(
    scope="project", 
    type="note", 
    source_ref=None, 
    confidence=None, 
    content="Test content",
    tags=None,
    expires_at=None,
    created_at=None
):
    now = datetime.now(timezone.utc)
    return MemoryRecord(
        id="mem-1",
        type=type,
        scope=scope,
        content=content,
        source_kind="manual",
        source_ref=source_ref,
        confidence=confidence,
        tags=tags or [],
        created_at=created_at or now,
        expires_at=expires_at,
        metadata={}
    )


def test_policy_passes_valid_record():
    record = create_record()
    policy = MemoryPolicy()
    findings = check_record(record, policy)
    assert len(findings) == 0


def test_policy_flags_disallowed_scope():
    record = create_record(scope="user")
    policy = MemoryPolicy(allowed_scopes=["project"])
    findings = check_record(record, policy)
    assert len(findings) == 1
    assert findings[0].code == "MEM001"
    assert "user" in findings[0].message


def test_policy_flags_expired_memory():
    past = datetime.now(timezone.utc) - timedelta(days=1)
    record = create_record(expires_at=past)
    policy = MemoryPolicy()
    findings = check_record(record, policy)
    assert any(f.code == "MEM002" for f in findings)


def test_policy_flags_retention_exceeded():
    past = datetime.now(timezone.utc) - timedelta(days=10)
    record = create_record(created_at=past)
    policy = MemoryPolicy(max_retention_days=5)
    findings = check_record(record, policy)
    assert any(f.code == "MEM003" for f in findings)


def test_policy_flags_missing_source_ref():
    record = create_record(source_ref=None)
    policy = MemoryPolicy(require_source_ref=True)
    findings = check_record(record, policy)
    assert any(f.code == "MEM004" for f in findings)


def test_policy_flags_low_confidence():
    record = create_record(confidence=0.5)
    policy = MemoryPolicy(min_confidence=0.8)
    findings = check_record(record, policy)
    assert any(f.code == "MEM005" for f in findings)


def test_policy_detects_secret_in_content():
    record = create_record(content="Here is a secret: sk-ant-1234567890123456789012345")
    policy = MemoryPolicy(redact_secrets=True)
    findings = check_record(record, policy)
    assert any(f.code == "MEM008" for f in findings)
