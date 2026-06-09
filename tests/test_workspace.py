"""Tests for the workspace module and CLI."""

import json
from pathlib import Path
from click.testing import CliRunner
import pytest
from niyam.cli import app
from niyam.core.workspace import WorkspaceAction, WorkspaceSession, WorkspaceStore, WorkspaceTimeline, WorkspaceApprovals

runner = CliRunner()


def test_workspace_create_and_list(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("niyam.core.config.NIYAM_DIR", str(tmp_path / ".niyam"))
    
    result = runner.invoke(app, ["workspace", "create", "Research Pricing", "--agent-type", "manual", "--session-id", "TASK-TEST1"])
    assert result.exit_code == 0
    assert "Created workspace session: TASK-TEST1" in result.stdout

    store = WorkspaceStore(tmp_path / ".niyam" / "workspace")
    session = store.get_session("TASK-TEST1")
    assert session is not None
    assert session.title == "Research Pricing"
    assert session.status == "created"

    result_list = runner.invoke(app, ["workspace", "list"])
    assert result_list.exit_code == 0
    assert "TASK-TEST1" in result_list.stdout
    assert "Research Pricing" in result_list.stdout


def test_workspace_log_and_timeline(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("niyam.core.config.NIYAM_DIR", str(tmp_path / ".niyam"))
    
    runner.invoke(app, ["workspace", "create", "Test Logic", "--session-id", "TASK-LOG1"])
    
    result = runner.invoke(app, ["workspace", "log", "TASK-LOG1", "--type", "prompt", "--actor", "human", "--input", "Hello agent"])
    assert result.exit_code == 0
    
    timeline = WorkspaceTimeline(tmp_path / ".niyam" / "workspace")
    actions = timeline.get_actions("TASK-LOG1")
    assert len(actions) == 1
    assert actions[0].action_type == "prompt"
    assert actions[0].actor == "human"
    assert actions[0].input == "Hello agent"
    
    result_timeline = runner.invoke(app, ["workspace", "timeline", "TASK-LOG1"])
    assert result_timeline.exit_code == 0
    assert "prompt by human" in result_timeline.stdout
    assert "Hello agent" in result_timeline.stdout


def test_workspace_pause_resume(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("niyam.core.config.NIYAM_DIR", str(tmp_path / ".niyam"))
    
    runner.invoke(app, ["workspace", "create", "Test Pause", "--session-id", "TASK-PAUSE1"])
    
    runner.invoke(app, ["workspace", "pause", "TASK-PAUSE1"])
    store = WorkspaceStore(tmp_path / ".niyam" / "workspace")
    assert store.get_session("TASK-PAUSE1").status == "paused"
    
    runner.invoke(app, ["workspace", "resume", "TASK-PAUSE1"])
    assert store.get_session("TASK-PAUSE1").status == "running"


def test_workspace_approval_flow(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("niyam.core.config.NIYAM_DIR", str(tmp_path / ".niyam"))
    
    runner.invoke(app, ["workspace", "create", "Test Approval", "--session-id", "TASK-APP1"])
    
    result_req = runner.invoke(app, ["workspace", "request-approval", "TASK-APP1", "--action", "delete-db", "--by", "userA"])
    assert result_req.exit_code == 0
    
    store = WorkspaceStore(tmp_path / ".niyam" / "workspace")
    assert store.get_session("TASK-APP1").status == "approval_required"
    
    approvals_manager = WorkspaceApprovals(tmp_path / ".niyam" / "workspace")
    approvals = approvals_manager.get_approvals("TASK-APP1")
    assert len(approvals) == 1
    appr_id = approvals[0].id
    assert approvals[0].status == "pending"
    
    result_appr = runner.invoke(app, ["workspace", "approve", "TASK-APP1", "--approval", appr_id, "--by", "admin"])
    assert result_appr.exit_code == 0
    assert store.get_session("TASK-APP1").status == "running"
    
    approvals = approvals_manager.get_approvals("TASK-APP1")
    assert approvals[0].status == "approved"
    assert approvals[0].decided_by == "admin"


def test_workspace_evidence(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("niyam.core.config.NIYAM_DIR", str(tmp_path / ".niyam"))
    runner.invoke(app, ["workspace", "create", "Test Evidence", "--session-id", "TASK-EVIDENCE"])
    runner.invoke(app, ["workspace", "log", "TASK-EVIDENCE", "--type", "prompt", "--actor", "human", "--input", "Hello"])
    
    result_json = runner.invoke(app, ["workspace", "evidence", "TASK-EVIDENCE", "--format", "json"])
    assert result_json.exit_code == 0
    data = json.loads(result_json.stdout)
    assert data["session"]["id"] == "TASK-EVIDENCE"
    assert data["action_counts"]["prompt"] == 1
    
    result_md = runner.invoke(app, ["workspace", "evidence", "TASK-EVIDENCE", "--format", "markdown"])
    assert result_md.exit_code == 0
    assert "Workspace Session: TASK-EVIDENCE" in result_md.stdout
    assert "**prompt**: 1" in result_md.stdout
