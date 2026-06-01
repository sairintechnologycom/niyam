"""Tests for the interactive plan refiner CLI loop."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch
from rich.console import Console

from niyam.mission.planner import run_mission_plan, _run_refiner_loop
from niyam.core.config import get_niyam_dir
import yaml


def test_interactive_refiner_loop(niyam_repo: Path) -> None:
    os.chdir(niyam_repo)
    console = Console(quiet=True)

    # 1. Generate a plan
    req_file = niyam_repo / "reqs.md"
    req_file.write_text("# Test Requirements\n", encoding="utf-8")
    mission_id = run_mission_plan(str(req_file), console=console)

    niyam_dir = get_niyam_dir(niyam_repo)
    plan_path = niyam_dir / "runs" / mission_id / "mission-plan.yaml"

    # We will simulate user inputs to the refiner CLI:
    # 1. add T_New: test task (gets assigned T6 automatically since there are 5 fallback tasks)
    # 2. edit T6 type=review
    # 3. show table
    # 4. delete T6
    # 5. done
    inputs = [
        "add T_New: test task",
        "edit T6 type=review",
        "show",
        "delete T6",
        "done",
    ]

    with patch("builtins.input", side_effect=inputs):
        _run_refiner_loop(console, plan_path, niyam_repo, niyam_dir)

    # Load the plan and verify
    with open(plan_path, encoding="utf-8") as f:
        plan_data = yaml.safe_load(f)

    # Assert that T6 was deleted and plan is valid
    tasks = plan_data["tasks"]
    task_ids = [t["id"] for t in tasks]
    assert "T6" not in task_ids
