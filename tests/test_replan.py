"""Tests for Niyam adaptive re-planning."""

from __future__ import annotations

import os
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from rich.console import Console

import pytest
from niyam.mission.planner import run_mission_replan
from niyam.mission.utils import save_plan, load_plan


def test_mission_replan_logic(niyam_repo: Path) -> None:
    """Should keep completed tasks and replace others with AI-generated tasks."""
    os.chdir(niyam_repo)
    console = Console(quiet=True)
    niyam_dir = niyam_repo / ".niyam"
    mission_id = "test-replan"
    run_dir = niyam_dir / "runs" / mission_id
    run_dir.mkdir(parents=True, exist_ok=True)

    # 1. Setup original plan with one completed task and one failed task
    original_plan = {
        "mission": {
            "id": mission_id,
            "status": "failed",
            "orchestrator": "claude",
            "parallel": 1,
            "worktree": False,
            "requirement": "dummy-req",
            "created": "2026-06-06T12:00:00Z",
        },
        "tasks": [
            {
                "id": "T1",
                "title": "Completed Task",
                "type": "discovery",
                "status": "completed",
                "agent": "default-agent",
            },
            {
                "id": "T2",
                "title": "Failed Task",
                "type": "implementation",
                "status": "failed",
                "agent": "default-agent",
            },
        ],
    }
    save_plan(run_dir, original_plan)
    (run_dir / "requirement.md").write_text("Original Objective", encoding="utf-8")

    # 2. Mock AI response for re-plan
    mock_ai_output = """
```yaml
tasks:
  - id: T2_FIX
    title: "Correction: Fix the previous failure"
    type: "implementation"
    agent: "default-agent"
    depends_on: ["T1"]
  - id: T3
    title: "Final Validation"
    type: "validation"
    agent: "default-agent"
    depends_on: ["T2_FIX"]
```
"""
    
    with (
        patch("subprocess.run") as mock_run,
        patch("shutil.which", return_value="/bin/claude"),
    ):
        mock_res = MagicMock()
        mock_res.returncode = 0
        mock_res.stdout = mock_ai_output
        mock_res.stderr = ""
        mock_run.return_value = mock_res

        # Execute re-plan
        run_mission_replan(console, mission_id=mission_id, reason="Testing re-plan")

        # 3. Verify merged plan
        updated_plan = load_plan(run_dir)
        tasks = updated_plan["tasks"]
        
        # Should have 3 tasks: T1 (kept), T2_FIX (new), T3 (new)
        assert len(tasks) == 3
        assert tasks[0]["id"] == "T1"
        assert tasks[0]["status"] == "completed"
        
        assert tasks[1]["id"] == "T2_FIX"
        assert tasks[1]["status"] == "planned"
        
        assert tasks[2]["id"] == "T3"
        assert tasks[2]["status"] == "planned"
        
        # Mission status should be reset
        assert updated_plan["mission"]["status"] == "planned"
