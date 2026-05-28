"""Tests for Sutra CI/CD and non-interactive execution."""

from __future__ import annotations

import os
import json
from pathlib import Path
import pytest
from rich.console import Console

from sutra.core.config import get_sutra_dir
from sutra.mission.planner import run_mission_plan
from sutra.mission.executor import run_mission_start, run_mission_resume, load_plan


def test_non_interactive_fails_unapproved(sutra_repo: Path) -> None:
    """Should fail with SystemExit if not approved and running headlessly/non-interactively."""
    os.chdir(sutra_repo)
    console = Console(quiet=True)

    req_file = sutra_repo / "requirements.md"
    req_file.write_text("# Test requirement\n", encoding="utf-8")
    mission_id = run_mission_plan(str(req_file), console=console)

    # approval.json should indicate unapproved
    run_dir = get_sutra_dir(sutra_repo) / "runs" / mission_id
    with pytest.raises(SystemExit) as excinfo:
        run_mission_start(console=console, non_interactive=True)
    assert excinfo.value.code == 1

    # Verify still unapproved
    with open(run_dir / "approval.json", encoding="utf-8") as f:
        app_data = json.load(f)
    assert not app_data.get("approved")


def test_non_interactive_auto_approve(sutra_repo: Path) -> None:
    """Should auto-approve if non-interactive and SUTRA_CI_AUTO_APPROVE=1 is set."""
    os.chdir(sutra_repo)
    console = Console(quiet=True)

    req_file = sutra_repo / "requirements.md"
    req_file.write_text("# Test requirement\n", encoding="utf-8")
    mission_id = run_mission_plan(str(req_file), console=console)

    os.environ["SUTRA_TEST"] = "1"
    os.environ["SUTRA_CI_AUTO_APPROVE"] = "1"
    try:
        run_mission_start(console=console, non_interactive=True)
    finally:
        del os.environ["SUTRA_TEST"]
        del os.environ["SUTRA_CI_AUTO_APPROVE"]

    # Verify it became approved and completed
    run_dir = get_sutra_dir(sutra_repo) / "runs" / mission_id
    with open(run_dir / "approval.json", encoding="utf-8") as f:
        app_data = json.load(f)
    assert app_data.get("approved")

    plan = load_plan(run_dir)
    assert plan["mission"]["status"] == "completed"
