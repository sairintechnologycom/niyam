"""Tests for the niyam run composite CLI command."""

from __future__ import annotations

import os
from pathlib import Path
from typer.testing import CliRunner

from niyam.cli import app
from niyam.core.config import get_niyam_dir
from niyam.mission.executor import load_plan

runner = CliRunner()


def test_run_composite_command_file(niyam_repo: Path) -> None:
    """Should run context refresh, sync, plan, approve, and execute in one command using a requirements file."""
    os.chdir(niyam_repo)

    # Create requirements file
    req_file = niyam_repo / "reqs.md"
    req_file.write_text("# Test requirements\nSome instructions.", encoding="utf-8")

    # Run the composite command
    os.environ["NIYAM_TEST"] = "1"
    try:
        # Using --auto-approve to bypass interactive prompts
        result = runner.invoke(app, ["run", str(req_file), "--auto-approve"])
        assert result.exit_code == 0
        assert "Refreshing project context" in result.output
        assert "Syncing runtimes" in result.output
        assert "Generating mission plan" in result.output
        assert "Checking plan approval" in result.output
        assert "Starting execution" in result.output
    finally:
        del os.environ["NIYAM_TEST"]

    # Verify latest mission plan has completed status
    niyam_dir = get_niyam_dir(niyam_repo)
    runs_dir = niyam_dir / "runs"
    assert runs_dir.is_dir()
    runs = [d for d in runs_dir.iterdir() if d.name != "current"]
    assert len(runs) == 1

    plan = load_plan(runs[0])
    assert plan["mission"]["status"] == "completed"
    assert plan["mission"]["requirement"] == str(req_file)


def test_run_composite_command_inline_string(niyam_repo: Path) -> None:
    """Should support run command with inline string requirement and auto-approve."""
    os.chdir(niyam_repo)

    inline_req = "implement a simple helper function"

    os.environ["NIYAM_TEST"] = "1"
    try:
        result = runner.invoke(
            app, ["run", inline_req, "--auto-approve", "--runtime", "claude"]
        )
        assert result.exit_code == 0
    finally:
        del os.environ["NIYAM_TEST"]

    niyam_dir = get_niyam_dir(niyam_repo)
    runs_dir = niyam_dir / "runs"
    runs = [d for d in runs_dir.iterdir() if d.is_dir() and d.name != "current"]
    assert len(runs) > 0

    # Sort runs by name/creation to get the latest
    runs.sort(key=lambda d: d.name)
    latest_run = runs[-1]

    plan = load_plan(latest_run)
    assert plan["mission"]["status"] == "completed"
    assert plan["mission"]["requirement"] == inline_req
    assert plan["mission"]["orchestrator"] == "claude"

    # Requirement file should contain the inline requirements
    req_file_on_disk = latest_run / "requirement.md"
    assert req_file_on_disk.exists()
    assert req_file_on_disk.read_text(encoding="utf-8") == inline_req
