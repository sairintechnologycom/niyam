"""Tests for Phase C Memory Ledger Policy."""

import pytest
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typer.testing import CliRunner

from niyam.core.memory_ledger.models import MemoryRecord, MemoryPolicy
from niyam.core.memory_ledger.policy import check_record, load_policy
from niyam.core.memory_ledger.local_store import LocalMemoryLedgerStore
from niyam.core.memory import get_memory_dir
from niyam.cli import app

runner = CliRunner()


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


def test_load_policy_rejects_invalid_yaml_shape(tmp_path: Path):
    policy_path = tmp_path / "memory-policy.yaml"
    policy_path.write_text("- not\n- a\n- mapping\n", encoding="utf-8")

    with pytest.raises(ValueError, match="YAML mapping"):
        load_policy(policy_path)


def test_memory_policy_check_cli_fail_on_and_json(niyam_repo: Path):
    os.chdir(niyam_repo)
    store = LocalMemoryLedgerStore(get_memory_dir(niyam_repo) / "index.jsonl")
    store.replace_all(
        [
            MemoryRecord(
                id="mem-policy-1",
                type="note",
                content="User scoped note",
                scope="user",
                created_at=datetime.now(timezone.utc),
            )
        ]
    )

    result = runner.invoke(
        app, ["memory", "policy-check", "--output", "json", "--fail-on", "medium"]
    )
    assert result.exit_code == 2
    assert "MEM001" in result.output


def test_memory_policy_check_cli_rejects_invalid_options(niyam_repo: Path):
    os.chdir(niyam_repo)

    invalid_output = runner.invoke(
        app, ["memory", "policy-check", "--output", "xml"]
    )
    assert invalid_output.exit_code == 1

    invalid_fail_on = runner.invoke(
        app, ["memory", "policy-check", "--fail-on", "severe"]
    )
    assert invalid_fail_on.exit_code == 1
