"""Tests for workspace browser and takeover functionality (Phase F)."""

import json
from pathlib import Path
from typer.testing import CliRunner
import pytest

from niyam.cli import app
from niyam.core.workspace import (
    WorkspaceStore,
    WorkspaceTimeline,
    WorkspaceApprovals,
)
from niyam.core.workspace.browser import BrowserStore, RecorderBrowserBackend

runner = CliRunner()


def _workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.chdir(tmp_path)
    niyam_dir = tmp_path / ".niyam"
    niyam_dir.mkdir()
    (niyam_dir / "niyam.yaml").write_text("version: 1.0.0-rc1\n", encoding="utf-8")
    return tmp_path


def test_browser_start(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    _workspace(tmp_path, monkeypatch)
    runner.invoke(app, ["workspace", "create", "Browser Test", "--session-id", "TASK-B1"])

    result = runner.invoke(app, ["workspace", "browser-start", "TASK-B1", "--url", "https://example.com"])
    assert result.exit_code == 0
    assert "Browser session started" in result.stdout

    b_store = BrowserStore(tmp_path / ".niyam" / "workspace")
    b_session = b_store.get_session("TASK-B1")
    assert b_session is not None
    assert b_session.status == "running"
    assert b_session.start_url == "https://example.com"


def test_browser_action_navigate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    _workspace(tmp_path, monkeypatch)
    runner.invoke(app, ["workspace", "create", "Nav Test", "--session-id", "TASK-N1"])
    runner.invoke(app, ["workspace", "browser-start", "TASK-N1", "--url", "https://example.com"])

    result = runner.invoke(app, ["workspace", "browser-action", "TASK-N1", "--type", "navigate", "--target", "https://example.com/about"])
    assert result.exit_code == 0

    b_store = BrowserStore(tmp_path / ".niyam" / "workspace")
    actions = b_store.get_actions("TASK-N1")
    assert len(actions) == 1
    assert actions[0].action_type == "navigate"
    assert actions[0].target == "https://example.com/about"
    assert actions[0].risk == "low"

    timeline = WorkspaceTimeline(tmp_path / ".niyam" / "workspace")
    t_actions = timeline.get_actions("TASK-N1")
    # 1 for status_change (start), 1 for command (navigate)
    assert len(t_actions) == 2
    assert t_actions[1].action_type == "command"


def test_browser_action_click(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    _workspace(tmp_path, monkeypatch)
    runner.invoke(app, ["workspace", "create", "Click Test", "--session-id", "TASK-C1"])
    runner.invoke(app, ["workspace", "browser-start", "TASK-C1"])

    runner.invoke(app, ["workspace", "browser-action", "TASK-C1", "--type", "click", "--target", "#btn"])

    b_store = BrowserStore(tmp_path / ".niyam" / "workspace")
    actions = b_store.get_actions("TASK-C1")
    assert len(actions) == 1
    assert actions[0].action_type == "click"
    assert actions[0].risk == "medium"


def test_browser_action_submit_requires_approval(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    _workspace(tmp_path, monkeypatch)
    runner.invoke(app, ["workspace", "create", "Submit Test", "--session-id", "TASK-S1"])
    runner.invoke(app, ["workspace", "browser-start", "TASK-S1"])

    result = runner.invoke(app, ["workspace", "browser-action", "TASK-S1", "--type", "submit", "--target", "#form"])
    assert result.exit_code == 0
    assert "Approval" in result.stdout
    assert "requested" in result.stdout

    b_store = BrowserStore(tmp_path / ".niyam" / "workspace")
    actions = b_store.get_actions("TASK-S1")
    assert len(actions) == 1
    assert actions[0].status == "approval_required"
    assert actions[0].requires_approval is True
    assert actions[0].approval_id is not None

    approvals = WorkspaceApprovals(tmp_path / ".niyam" / "workspace")
    apprs = approvals.get_approvals("TASK-S1")
    assert len(apprs) == 1
    assert apprs[0].id == actions[0].approval_id
    assert apprs[0].status == "pending"


def test_browser_pause_resume(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    _workspace(tmp_path, monkeypatch)
    runner.invoke(app, ["workspace", "create", "Pause Test", "--session-id", "TASK-P1"])
    runner.invoke(app, ["workspace", "browser-start", "TASK-P1"])

    runner.invoke(app, ["workspace", "browser-pause", "TASK-P1"])
    b_store = BrowserStore(tmp_path / ".niyam" / "workspace")
    assert b_store.get_session("TASK-P1").status == "paused"

    runner.invoke(app, ["workspace", "browser-resume", "TASK-P1"])
    assert b_store.get_session("TASK-P1").status == "running"

    timeline = WorkspaceTimeline(tmp_path / ".niyam" / "workspace")
    status_outputs = [
        action.output
        for action in timeline.get_actions("TASK-P1")
        if action.action_type == "status_change"
    ]
    assert "Browser session paused" in status_outputs
    assert "Browser session resumed" in status_outputs


def test_browser_type_sensitive_input_is_redacted_and_requires_approval(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    _workspace(tmp_path, monkeypatch)
    runner.invoke(app, ["workspace", "create", "Secret Test", "--session-id", "TASK-SEC1"])
    runner.invoke(app, ["workspace", "browser-start", "TASK-SEC1"])

    result = runner.invoke(
        app,
        [
            "workspace",
            "browser-action",
            "TASK-SEC1",
            "--type",
            "type",
            "--target",
            "#api-key",
            "--input",
            "sk-ant-1234567890123456789012345",
        ],
    )
    assert result.exit_code == 0

    b_store = BrowserStore(tmp_path / ".niyam" / "workspace")
    action = b_store.get_actions("TASK-SEC1")[0]
    assert action.risk == "high"
    assert action.status == "approval_required"
    assert action.redacted is True
    assert "sk-ant" not in action.input


def test_takeover_and_release(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    _workspace(tmp_path, monkeypatch)
    runner.invoke(app, ["workspace", "create", "Takeover Test", "--session-id", "TASK-T1"])
    runner.invoke(app, ["workspace", "browser-start", "TASK-T1"])

    runner.invoke(app, ["workspace", "takeover", "TASK-T1", "--by", "Alice"])

    store = WorkspaceStore(tmp_path / ".niyam" / "workspace")
    b_store = BrowserStore(tmp_path / ".niyam" / "workspace")

    assert store.get_session("TASK-T1").status == "paused"
    assert b_store.get_session("TASK-T1").status == "takeover"
    assert b_store.get_session("TASK-T1").takeover_by == "Alice"

    runner.invoke(app, ["workspace", "release", "TASK-T1", "--by", "Alice"])
    assert store.get_session("TASK-T1").status == "running"
    assert b_store.get_session("TASK-T1").status == "running"
    assert b_store.get_session("TASK-T1").takeover_by is None


def test_screenshot_action(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    _workspace(tmp_path, monkeypatch)
    runner.invoke(app, ["workspace", "create", "Screenshot Test", "--session-id", "TASK-SS1"])
    runner.invoke(app, ["workspace", "browser-start", "TASK-SS1"])

    runner.invoke(app, ["workspace", "browser-action", "TASK-SS1", "--type", "screenshot"])

    b_store = BrowserStore(tmp_path / ".niyam" / "workspace")
    actions = b_store.get_actions("TASK-SS1")
    assert len(actions) == 1
    assert actions[0].action_type == "screenshot"
    assert actions[0].output is not None
    assert "artifacts" in actions[0].output

    # Check that artifact mock file was created
    assert Path(actions[0].output).exists()


def test_workspace_evidence_includes_browser(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    _workspace(tmp_path, monkeypatch)
    runner.invoke(app, ["workspace", "create", "Evidence Test", "--session-id", "TASK-EV1"])
    runner.invoke(app, ["workspace", "browser-start", "TASK-EV1"])
    runner.invoke(app, ["workspace", "browser-action", "TASK-EV1", "--type", "navigate", "--target", "https://example.com"])
    runner.invoke(app, ["workspace", "browser-action", "TASK-EV1", "--type", "submit", "--target", "#login"]) # Pending approval

    result_json = runner.invoke(app, ["workspace", "evidence", "TASK-EV1", "--format", "json"])
    data = json.loads(result_json.stdout)
    assert "browser" in data
    assert data["browser"]["status"] == "running"
    assert data["browser"]["action_counts"]["navigate"] == 1
    assert data["browser"]["approval_required_actions"] == 1

    result_md = runner.invoke(app, ["workspace", "evidence", "TASK-EV1", "--format", "markdown"])
    assert "## Browser Session" in result_md.stdout
    assert "**navigate**: 1" in result_md.stdout
    assert "**Approval Required Actions**: 1" in result_md.stdout
