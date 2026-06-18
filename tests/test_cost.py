"""Tests for Niyam AI engineering cost tracking commands."""

from __future__ import annotations

import json
from pathlib import Path
import pytest
from typer.testing import CliRunner

from niyam.cli import app


@pytest.fixture(autouse=True)
def setup_workspace(tmp_path: Path, monkeypatch) -> None:
    """Fixture to ensure tests run in a workspace relative to tmp_path."""
    monkeypatch.chdir(tmp_path)
    # Create mock .niyam directory to mock find_niyam_root
    niyam_dir = tmp_path / ".niyam"
    niyam_dir.mkdir(exist_ok=True)
    # Write empty config
    with open(niyam_dir / "niyam.yaml", "w") as f:
        f.write("version: 0.1.0\n")


def test_cost_log_event(tmp_path: Path) -> None:
    """Should log a cost event with calculated estimated cost and save to JSONL."""
    runner = CliRunner()

    # Log an event
    result = runner.invoke(
        app,
        [
            "cost",
            "log",
            "--tool",
            "claude-code",
            "--model",
            "claude-sonnet",
            "--input-tokens",
            "10000",
            "--output-tokens",
            "2000",
            "--task",
            "refactor-scanner",
            "--status",
            "success",
            "--notes",
            "A test run.",
        ],
    )
    assert result.exit_code == 0
    assert "Logged AI session usage" in result.stdout
    assert "claude-sonnet" in result.stdout
    assert "$0.0600" in result.stdout

    # Verify JSONL log file is created
    log_file = tmp_path / ".niyam" / "logs" / "cost-events.jsonl"
    assert log_file.exists()

    with open(log_file) as f:
        lines = f.read().strip().split("\n")
    assert len(lines) == 1

    event = json.loads(lines[0])
    assert event["tool_name"] == "claude-code"
    assert event["model"] == "claude-sonnet"
    assert event["input_tokens"] == 10000
    assert event["output_tokens"] == 2000
    assert event["estimated_cost"] == 0.06
    assert event["task_id"] == "refactor-scanner"
    assert event["status"] == "success"
    assert event["notes"] == "A test run."
    assert "timestamp" in event
    assert "session_id" in event
    assert "repo" in event
    assert "branch" in event


def test_cost_log_gpt_5_codex_uses_default_pricing(tmp_path: Path) -> None:
    """Should estimate cost for gpt-5-codex instead of falling back to unknown."""
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "cost",
            "log",
            "--tool",
            "codex",
            "--model",
            "gpt-5-codex",
            "--input-tokens",
            "24000",
            "--output-tokens",
            "5200",
        ],
    )

    assert result.exit_code == 0
    assert "gpt-5-codex" in result.stdout
    assert "$0.1380" in result.stdout

    log_file = tmp_path / ".niyam" / "logs" / "cost-events.jsonl"
    event = json.loads(log_file.read_text(encoding="utf-8").strip())
    assert event["estimated_cost"] == 0.138


def test_cost_summary(tmp_path: Path) -> None:
    """Should display cost summary aggregates."""
    runner = CliRunner()

    # When no logs exist
    res_empty = runner.invoke(app, ["cost", "summary"])
    assert "No logged cost events found." in res_empty.stdout

    # Log some events
    runner.invoke(
        app,
        [
            "cost",
            "log",
            "--model",
            "claude-sonnet",
            "--input-tokens",
            "10000",
            "--output-tokens",
            "2000",
        ],
    )
    runner.invoke(
        app,
        [
            "cost",
            "log",
            "--model",
            "claude-opus",
            "--input-tokens",
            "5000",
            "--output-tokens",
            "1000",
        ],
    )

    result = runner.invoke(app, ["cost", "summary"])
    assert result.exit_code == 0
    assert "Total Logged Events: 2" in result.stdout
    assert "$0.2100" in result.stdout
    assert "15,000" in result.stdout
    assert "3,000" in result.stdout


def test_cost_repo_report(tmp_path: Path) -> None:
    """Should generate detailed repo, day, task, and status reports."""
    runner = CliRunner()

    # When no logs exist
    res_empty = runner.invoke(app, ["cost", "report"])
    assert "No logged cost events found to report." in res_empty.stdout

    # Log some events
    runner.invoke(
        app,
        [
            "cost",
            "log",
            "--model",
            "claude-sonnet",
            "--input-tokens",
            "10000",
            "--output-tokens",
            "2000",
            "--task",
            "task-A",
            "--status",
            "success",
        ],
    )
    runner.invoke(
        app,
        [
            "cost",
            "log",
            "--model",
            "claude-sonnet",
            "--input-tokens",
            "20000",
            "--output-tokens",
            "4000",
            "--task",
            "task-B",
            "--status",
            "failed",
        ],
    )

    result = runner.invoke(app, ["cost", "report"])
    assert result.exit_code == 0
    assert "Cost by Day" in result.stdout
    assert "Cost by Repository" in result.stdout
    assert "Cost by Task" in result.stdout
    assert "Top Expensive Sessions" in result.stdout
    assert "Failed/Repeated Task Cost Summary (Wasted Budget)" in result.stdout
    assert "task-A" in result.stdout
    assert "task-B" in result.stdout
    assert "Successful Tasks: 1" in result.stdout
    assert "Failed/Repeated Tasks: 1" in result.stdout


def test_cost_missing_fields_handling(tmp_path: Path) -> None:
    """Should handle missing or default values gracefully."""
    runner = CliRunner()

    # Log with minimal options, leaving tool, model, tokens blank
    result = runner.invoke(app, ["cost", "log"])
    assert result.exit_code == 0
    assert "Logged AI session usage: unknown" in result.stdout
    assert "$0.0000" in result.stdout

    # Verify defaults in the log
    log_file = tmp_path / ".niyam" / "logs" / "cost-events.jsonl"
    with open(log_file) as f:
        data = json.loads(f.read().strip())

    assert data["tool_name"] == "unknown"
    assert data["model"] == "unknown"
    assert data["input_tokens"] == 0
    assert data["output_tokens"] == 0
    assert data["estimated_cost"] == 0.0
    assert data["task_id"] == "default-task"
    assert data["status"] == "success"
    assert data["notes"] is None
