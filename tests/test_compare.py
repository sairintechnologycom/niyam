"""Tests for multi-runtime comparison."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

from rich.console import Console
from typer.testing import CliRunner

from sutra.cli import app
from sutra.core.config import get_sutra_dir
from sutra.mission.planner import run_mission_plan
from sutra.mission.executor import load_plan, save_plan
from sutra.core.compare import run_comparison

runner = CliRunner()


def test_comparison_runs_multiple_executors(sutra_repo: Path) -> None:
    """Should execute the task under each specified executor in isolated worktrees/directories."""
    os.chdir(sutra_repo)
    console = Console(quiet=True)

    # 1. Create a planned and approved mission
    req_file = sutra_repo / "requirements.md"
    req_file.write_text("# Test comparison\n", encoding="utf-8")

    # Initialize / Mock a run config
    mission_id = run_mission_plan(str(req_file), console=console)

    # Approve the mission
    run_dir = get_sutra_dir(sutra_repo) / "runs" / mission_id
    approval_path = run_dir / "approval.json"
    approval_path.write_text(
        '{"approved": true, "timestamp": "2026-05-28T22:00:00Z"}', encoding="utf-8"
    )

    plan_data = load_plan(run_dir)
    plan_data["mission"]["status"] = "approved"
    plan_data["tasks"] = [
        {
            "id": "T1",
            "title": "Discovery task",
            "type": "discovery",
            "status": "pending",
            "agent": "backend-specialist",
            "runtime": "claude",
        }
    ]
    save_plan(run_dir, plan_data)

    # Mock shutil.which to find all runtimes
    def mock_which(cmd: str) -> str | None:
        if cmd in ["gemini", "codex", "claude"]:
            return f"/mock/bin/{cmd}"
        return None

    # Patch execution to avoid calling real CLI commands
    with (
        patch("shutil.which", side_effect=mock_which),
        patch("subprocess.run"),
    ):
        os.environ["SUTRA_TEST"] = "1"
        try:
            run_comparison(task_id="T1", executors_str="claude,gemini", console=console)
        finally:
            del os.environ["SUTRA_TEST"]

        # Verify the comparison folder was created with sub-runs for each executor
        comparison_dir = run_dir / "comparison" / "T1"
        assert comparison_dir.exists()

        claude_run_dir = comparison_dir / "claude"
        gemini_run_dir = comparison_dir / "gemini"

        assert claude_run_dir.exists()
        assert gemini_run_dir.exists()

        # Check that the comparison report was written
        report_file = comparison_dir / "comparison-report.md"
        assert report_file.exists()
        report_content = report_file.read_text(encoding="utf-8")
        assert "# Comparison Report — Task T1" in report_content
        assert "| claude |" in report_content
        assert "| gemini |" in report_content


def test_compare_cli_command(sutra_repo: Path) -> None:
    """Should verify the CLI command `sutra compare` parses arguments correctly and invokes the compare function."""
    os.chdir(sutra_repo)

    # We will mock run_comparison to verify it gets called
    with patch("sutra.core.compare.run_comparison") as mock_run_comparison:
        # Run command via Typer runner
        result = runner.invoke(app, ["compare", "T1", "--executors", "gemini,codex"])

        # Check it completed successfully and called run_comparison with correct arguments
        assert result.exit_code == 0
        mock_run_comparison.assert_called_once()
        _, kwargs = mock_run_comparison.call_args
        assert kwargs["task_id"] == "T1"
        assert kwargs["executors_str"] == "gemini,codex"
