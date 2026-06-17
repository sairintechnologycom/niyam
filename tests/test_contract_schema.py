"""Tests for the Task-Contract canonical model schema."""

import json
from pathlib import Path
import pytest
from typer.testing import CliRunner

from niyam.cli import app
from niyam.core.config import TaskContract

runner = CliRunner()


def test_contract_schema_cli_output():
    """Test that the CLI can dump the Task Contract schema."""
    result = runner.invoke(app, ["mission", "contract-schema"])
    assert result.exit_code == 0
    schema = json.loads(result.stdout)
    assert schema["title"] == "TaskContract"
    assert "id" in schema["properties"]
    assert "retry_policy" in schema["properties"]
    assert "evidence_refs" in schema["properties"]


def test_task_contract_validation():
    """Test that TaskContract properly validates valid task data."""
    valid_data = {
        "id": "TASK-123",
        "title": "Fix the database schema",
        "type": "implementation",
        "status": "planned",
        "agent": "codex",
        "allowed_files": ["src/db/*"],
        "timeout_seconds": 300,
        "risk": "high",
        "approval_required": True,
        "evidence_refs": ["EVID-1", "EVID-2"],
        "retry_policy": "manual",
        "max_retries": 1,
    }
    
    contract = TaskContract(**valid_data)
    assert contract.id == "TASK-123"
    assert contract.risk == "high"
    assert contract.approval_required is True
    assert len(contract.evidence_refs) == 2
    assert contract.retry_policy == "manual"
    
    # Check alias working (files_allowed -> allowed_files)
    valid_data_alias = valid_data.copy()
    del valid_data_alias["allowed_files"]
    valid_data_alias["files_allowed"] = ["src/db/*"]
    
    contract_alias = TaskContract(**valid_data_alias)
    assert contract_alias.allowed_files == ["src/db/*"]


def test_task_contract_invalid_data():
    """Test that TaskContract rejects invalid data."""
    from pydantic import ValidationError
    
    # Missing required fields
    with pytest.raises(ValidationError):
        TaskContract(title="Missing ID")
        
    # Invalid enum
    with pytest.raises(ValidationError):
        TaskContract(
            id="TASK-1",
            title="Title",
            type="invalid_type",
            status="planned",
            agent="codex"
        )
