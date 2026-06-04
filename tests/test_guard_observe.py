"""Tests for Niyam guard observe mode."""

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


def test_guard_run_harmless_command(tmp_path: Path) -> None:
    """Should run a harmless command, preserve exit code, and log execution details."""
    runner = CliRunner()

    # Run a harmless command (echo 'hello') with capture output
    result = runner.invoke(
        app, ["guard", "run", "--capture-output", "--", "echo", "hello-observe"]
    )
    assert result.exit_code == 0
    assert "hello-observe" in result.stdout

    # Confirm log is created in the expected location
    log_file = tmp_path / ".niyam" / "logs" / "guard-actions.jsonl"
    assert log_file.exists()

    # Read the log entry
    lines = log_file.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 1

    entry = json.loads(lines[0])
    assert entry["exit_code"] == 0
    assert entry["mode"] == "observe"
    assert "echo" in entry["command"]
    assert entry["actor_type"] == "agent"


def test_guard_run_failed_command(tmp_path: Path) -> None:
    """Should log failed commands and preserve their exit codes."""
    import sys

    runner = CliRunner()

    # Run a command that returns non-zero exit code using the exact python interpreter
    result = runner.invoke(
        app, ["guard", "run", "--", sys.executable, "-c", "import sys; sys.exit(42)"]
    )
    assert result.exit_code == 42

    log_file = tmp_path / ".niyam" / "logs" / "guard-actions.jsonl"
    assert log_file.exists()

    lines = log_file.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 1

    entry = json.loads(lines[0])
    assert entry["exit_code"] == 42
    assert entry["mode"] == "observe"


def test_guard_status_command(tmp_path: Path) -> None:
    """Should display status including count of observed logs."""
    runner = CliRunner()

    # Run one harmless command
    runner.invoke(app, ["guard", "run", "--", "echo", "test"])

    # Check guard status
    result = runner.invoke(app, ["guard", "status"])
    assert result.exit_code == 0
    assert "Total Actions Logged: 1" in result.stdout


def test_guard_logs_command(tmp_path: Path) -> None:
    """Should display recent observed logs in a table format."""
    runner = CliRunner()

    # Run harmless commands
    runner.invoke(app, ["guard", "run", "--", "echo", "cmd1"])
    runner.invoke(app, ["guard", "run", "--", "echo", "cmd2"])

    # Check guard logs
    result = runner.invoke(app, ["guard", "logs"])
    assert result.exit_code == 0
    assert "cmd1" in result.stdout
    assert "cmd2" in result.stdout
