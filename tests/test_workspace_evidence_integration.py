"""Tests for Phase G workspace evidence integration."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from niyam.cli import app
from niyam.core.evidence import run_generate_evidence

runner = CliRunner()


def _workspace(tmp_path: Path, monkeypatch) -> Path:
    monkeypatch.chdir(tmp_path)
    niyam_dir = tmp_path / ".niyam"
    niyam_dir.mkdir()
    (niyam_dir / "niyam.yaml").write_text("version: 1.0.0-rc1\n", encoding="utf-8")
    return tmp_path


def _create_workspace_activity() -> None:
    create = runner.invoke(
        app,
        [
            "workspace",
            "create",
            "Evidence Workspace",
            "--session-id",
            "TASK-EVID-G",
            "--risk",
            "medium",
        ],
    )
    assert create.exit_code == 0

    start = runner.invoke(
        app,
        [
            "workspace",
            "browser-start",
            "TASK-EVID-G",
            "--url",
            "https://example.com",
        ],
    )
    assert start.exit_code == 0

    submit = runner.invoke(
        app,
        [
            "workspace",
            "browser-action",
            "TASK-EVID-G",
            "--type",
            "submit",
            "--target",
            "#publish",
        ],
    )
    assert submit.exit_code == 0


def test_evidence_without_workspace_is_unchanged(tmp_path: Path, monkeypatch) -> None:
    _workspace(tmp_path, monkeypatch)
    _create_workspace_activity()

    report = run_generate_evidence(fmt="markdown", include="scan,guard")

    assert "Control Room Posture" not in report
    assert "Workspace Sessions by Status" not in report


def test_evidence_workspace_markdown_summary(tmp_path: Path, monkeypatch) -> None:
    _workspace(tmp_path, monkeypatch)
    _create_workspace_activity()

    report = run_generate_evidence(fmt="markdown", include="scan,workspace")

    assert "Control Room Posture" in report
    assert "1 workspace sessions" in report
    assert "Pending Approvals:** 1" in report
    assert "Browser Sessions:** 1" in report
    assert "Approval Required**: 1" in report
    assert "submit" in report


def test_evidence_workspace_json_summary(tmp_path: Path, monkeypatch) -> None:
    _workspace(tmp_path, monkeypatch)
    _create_workspace_activity()

    report = run_generate_evidence(fmt="json", include="workspace")
    data = json.loads(report)

    assert data["workspace"]["exists"] is True
    assert data["workspace"]["total_sessions"] == 1
    assert data["workspace"]["pending_approvals"] == 1
    assert data["workspace"]["browser_action_counts"]["submit"] == 1
    assert data["workspace"]["recent_sessions"][0]["id"] == "TASK-EVID-G"


def test_evidence_workspace_html_summary(tmp_path: Path, monkeypatch) -> None:
    _workspace(tmp_path, monkeypatch)
    _create_workspace_activity()

    report = run_generate_evidence(fmt="html", include="workspace")

    assert "Control Room Governance" in report
    assert "TASK-EVID-G" in report
