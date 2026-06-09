"""Tests for Phase B Memory Ledger Core."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import pytest
from typer.testing import CliRunner

from niyam.cli import app
from niyam.core.memory import get_memory_file
from niyam.core.memory_ledger.models import MemoryRecord
from niyam.core.memory_ledger.local_store import LocalMemoryLedgerStore
from niyam.core.memory_ledger.manifest import export_manifest, import_manifest
from niyam.core.memory_ledger.diff import diff_manifests

runner = CliRunner()


def test_memory_record_validates_new_record():
    data = {
        "id": "mem-123",
        "type": "note",
        "content": "Test note",
        "scope": "project",
        "source_kind": "manual",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "tags": ["test"],
        "metadata": {"memory_file": "test.md"}
    }
    record = MemoryRecord.model_validate(data)
    assert record.id == "mem-123"
    assert record.source_kind == "manual"
    assert record.metadata["memory_file"] == "test.md"


def test_existing_legacy_index_record_validates():
    data = {
        "id": "mem-20260609",
        "created_at": "2026-06-09T10:00:00Z",
        "type": "note",
        "scope": "project",
        "memory_file": "project-lessons.md",
        "source": "manual",
        "confidence": "user-provided",
        "content": "Legacy content"
    }
    record = MemoryRecord.model_validate(data)
    assert record.id == "mem-20260609"
    assert record.source_kind == "manual"
    assert record.metadata["memory_file"] == "project-lessons.md"
    assert record.metadata["original_confidence"] == "user-provided"
    assert record.confidence is None


def test_niyam_memory_init(tmp_path: Path):
    store_path = tmp_path / "memory" / "index.jsonl"
    store = LocalMemoryLedgerStore(store_path)
    store.init_store()
    assert store_path.exists()
    assert store_path.is_file()


def test_niyam_memory_validate_passes_on_valid(tmp_path: Path):
    store_path = tmp_path / "memory" / "index.jsonl"
    store = LocalMemoryLedgerStore(store_path)
    store.init_store()
    
    record = MemoryRecord(
        id="mem-1",
        type="note",
        content="Test content",
        created_at=datetime.now(timezone.utc)
    )
    store.append(record)
    
    assert store.validate_store() is True


def test_niyam_memory_validate_fails_on_invalid(tmp_path: Path):
    store_path = tmp_path / "memory" / "index.jsonl"
    store_path.parent.mkdir(parents=True, exist_ok=True)
    with open(store_path, "w", encoding="utf-8") as f:
        f.write('{"id": "mem-1", "type": "invalid_type", "created_at": "2026-06-09T10:00:00Z", "content": "x"}\n')
        
    store = LocalMemoryLedgerStore(store_path)
    with pytest.raises(ValueError, match="Line 1 is invalid"):
        store.validate_store()


def test_export_import_round_trip_json(tmp_path: Path):
    records = [
        MemoryRecord(
            id="mem-1",
            type="note",
            content="Test content 1",
            created_at=datetime.now(timezone.utc)
        ),
        MemoryRecord(
            id="mem-2",
            type="semantic",
            content="Test content 2",
            created_at=datetime.now(timezone.utc)
        )
    ]
    export_path = tmp_path / "export.json"
    export_manifest(records, export_path, fmt="json")
    
    imported = import_manifest(export_path)
    assert len(imported) == 2
    assert imported[0].id == "mem-1"
    assert imported[1].id == "mem-2"


def test_export_import_round_trip_yaml(tmp_path: Path):
    records = [
        MemoryRecord(
            id="mem-1",
            type="note",
            content="Test content 1",
            created_at=datetime.now(timezone.utc)
        )
    ]
    export_path = tmp_path / "export.yaml"
    export_manifest(records, export_path, fmt="yaml")
    
    imported = import_manifest(export_path)
    assert len(imported) == 1
    assert imported[0].id == "mem-1"


def test_diff_detects_changes():
    t = datetime.now(timezone.utc)
    r1 = MemoryRecord(id="mem-1", type="note", content="A", created_at=t)
    r2 = MemoryRecord(id="mem-2", type="note", content="B", created_at=t)
    r2_mod = MemoryRecord(id="mem-2", type="note", content="B mod", created_at=t)
    r3 = MemoryRecord(id="mem-3", type="note", content="C", created_at=t)
    
    before = [r1, r2]
    after = [r2_mod, r3]
    
    diff = diff_manifests(before, after)
    
    assert len(diff.added) == 1
    assert diff.added[0].id == "mem-3"
    
    assert len(diff.removed) == 1
    assert diff.removed[0].id == "mem-1"
    
    assert len(diff.changed) == 1
    assert diff.changed[0][0].id == "mem-2"
    assert diff.changed[0][1].content == "B mod"


def test_memory_ledger_cli_init_list_validate_export(niyam_repo: Path):
    os.chdir(niyam_repo)

    init_result = runner.invoke(app, ["memory", "init"])
    assert init_result.exit_code == 0

    add_result = runner.invoke(
        app, ["memory", "add", "project-lessons", "CLI ledger note"]
    )
    assert add_result.exit_code == 0

    list_result = runner.invoke(app, ["memory", "list"])
    assert list_result.exit_code == 0
    assert "CLI ledger note" not in list_result.output
    assert "note" in list_result.output

    validate_result = runner.invoke(app, ["memory", "validate"])
    assert validate_result.exit_code == 0

    export_path = niyam_repo / "memory-export.json"
    export_result = runner.invoke(
        app,
        ["memory", "export", "--output", str(export_path), "--format", "json"],
    )
    assert export_result.exit_code == 0
    assert export_path.exists()

    imported = import_manifest(export_path)
    assert any(record.content == "CLI ledger note" for record in imported)


def test_memory_ledger_cli_import_and_diff(niyam_repo: Path, tmp_path: Path):
    os.chdir(niyam_repo)
    before_path = tmp_path / "before.yaml"
    after_path = tmp_path / "after.yaml"
    import_path = tmp_path / "import.yaml"
    timestamp = datetime.now(timezone.utc)

    before = [
        MemoryRecord(id="mem-1", type="note", content="A", created_at=timestamp),
    ]
    after = [
        MemoryRecord(id="mem-1", type="note", content="A changed", created_at=timestamp),
        MemoryRecord(id="mem-2", type="note", content="B", created_at=timestamp),
    ]
    export_manifest(before, before_path, fmt="yaml")
    export_manifest(after, after_path, fmt="yaml")
    export_manifest(after, import_path, fmt="yaml")

    diff_result = runner.invoke(
        app, ["memory", "diff", str(before_path), str(after_path)]
    )
    assert diff_result.exit_code == 0
    assert "Added" in diff_result.output
    assert "Changed" in diff_result.output

    import_result = runner.invoke(app, ["memory", "import", str(import_path)])
    assert import_result.exit_code == 0

    list_result = runner.invoke(app, ["memory", "list"])
    assert list_result.exit_code == 0
    assert "mem-2" in list_result.output


def test_existing_memory_add_still_updates_markdown_and_legacy_index(niyam_repo: Path):
    os.chdir(niyam_repo)

    result = runner.invoke(
        app, ["memory", "add", "project-lessons", "Backcompat note"]
    )
    assert result.exit_code == 0

    filepath = get_memory_file(niyam_repo, "project-lessons")
    assert "- Backcompat note" in filepath.read_text(encoding="utf-8")

    records_path = filepath.parent / "index.jsonl"
    raw_records = [
        json.loads(line)
        for line in records_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert raw_records[-1]["memory_file"] == "project-lessons.md"
    assert raw_records[-1]["source"] == "manual"

    parsed = MemoryRecord.model_validate(raw_records[-1])
    assert parsed.metadata["memory_file"] == "project-lessons.md"
    assert parsed.source_kind == "manual"
