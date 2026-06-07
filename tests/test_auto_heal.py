"""Tests for Niyam autonomous resilience (auto-heal)."""

from __future__ import annotations

import os
import json
import threading
from pathlib import Path
from unittest.mock import patch, MagicMock
from rich.console import Console

import pytest
from niyam.mission.executor import run_mission_start
from niyam.mission.utils import save_plan, load_plan


def test_mission_auto_heal(niyam_repo: Path) -> None:
    """Should trigger re-planning automatically after repeated task failures."""
    os.chdir(niyam_repo)
    console = Console(quiet=True)
    niyam_dir = niyam_repo / ".niyam"
    mission_id = "test-auto-heal"
    run_dir = niyam_dir / "runs" / mission_id
    run_dir.mkdir(parents=True, exist_ok=True)

    # 1. Setup plan with auto_heal enabled and a task that will fail
    plan = {
        "mission": {
            "id": mission_id,
            "status": "approved",
            "parallel": 1,
            "worktree": False,
            "auto_heal": True,
            "requirement": "dummy-req",
            "created": "2026-06-06T12:00:00Z",
            "orchestrator": "claude",
        },
        "tasks": [
            {
                "id": "T1",
                "title": "Failing Task",
                "type": "implementation",
                "status": "planned",
                "agent": "default-agent",
                "retry_count": 0,
                "max_retries": 2, # Will fail twice and then trigger auto-heal
            }
        ],
    }
    save_plan(run_dir, plan)
    (run_dir / "approval.json").write_text('{"approved": true}', encoding="utf-8")
    (run_dir / "requirement.md").write_text("Objective", encoding="utf-8")

    # 2. Mock execution to fail, and mock replan to update plan
    execute_calls = 0
    replan_called = threading.Event()

    def mock_execute_task(**kwargs):
        nonlocal execute_calls
        execute_calls += 1
        return False # Always fail

    def mock_replan(**kwargs):
        nonlocal replan_called
        # Update plan to simulate a fix (e.g. mark task as completed or add new one)
        current = load_plan(run_dir)
        current["tasks"] = [{
            "id": "T1", 
            "status": "completed", 
            "title": "Fixed",
            "type": "implementation",
            "agent": "default-agent"
        }]
        current["mission"]["status"] = "completed" # Cheat to end the loop
        save_plan(run_dir, current)
        replan_called.set()

    with (
        patch("niyam.mission.executor.execute_single_task", side_effect=mock_execute_task),
        patch("niyam.mission.executor.run_mission_replan", side_effect=mock_replan),
    ):
        # Run mission
        run_mission_start(console, mission_id=mission_id)

        # 3. Verify
        assert execute_calls == 2, "Task should have been retried once (total 2 calls)"
        assert replan_called.is_set(), "Re-planner should have been invoked after max retries"
        
        final_plan = load_plan(run_dir)
        assert final_plan["mission"]["status"] == "completed"
