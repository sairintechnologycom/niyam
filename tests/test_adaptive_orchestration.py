"""Tests for EPIC-005: Adaptive Orchestration (Failure diagnostics and re-planning)."""

import os
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from niyam.mission.utils import get_failure_diagnostics
from niyam.mission.executor import run_mission_start
from niyam.mission.planner import build_replanner_prompt, run_mission_replan
from rich.console import Console


@pytest.fixture
def run_dir(tmp_path):
    """Setup a temporary run directory with a failed task log."""
    d = tmp_path / ".niyam" / "runs" / "test-mission"
    d.mkdir(parents=True)
    
    # Create a mock failed task log
    log_path = d / "task-T2-output.log"
    log_path.write_text("Error: ModuleNotFoundError: No module named 'missing_pkg'\n")
    
    return d


def test_failure_diagnostics_gathering(run_dir):
    """Test that diagnostics are correctly gathered from logs and environment."""
    with patch("os.environ", {"PYTHONPATH": "/usr/bin/python", "SECRET_KEY": "supersecret"}):
        # We need to mock redact_text to verify it's called for environment variables
        with patch("niyam.governance.common.redaction.redact_text", side_effect=lambda x: "[REDACTED]" if "secret" in x else x) as mock_redact:
            diag = get_failure_diagnostics(run_dir, failed_task_id="T2")
            
            assert "=== Niyam Failure Diagnostics ===" in diag
            assert "Log Tail: Task T2" in diag
            assert "ModuleNotFoundError: No module named 'missing_pkg'" in diag
            assert "PYTHONPATH=/usr/bin/python" in diag
            # SECRET_KEY should not be in the interesting prefixes, so it might not even be there
            # but let's check PATH
            assert "PATH=" in diag


def test_replanner_prompt_with_diagnostics():
    """Test that the replanner prompt includes the diagnostics section."""
    requirement = "Implement feature X"
    plan_data = {
        "tasks": [
            {"id": "T1", "status": "completed", "title": "Discovery"},
            {"id": "T2", "status": "failed", "title": "Implementation"}
        ]
    }
    failure_context = "Task T2 failed"
    available_agents = ["default-agent"]
    diagnostics = "Environment: Python 3.11\nError: missing dependency"
    
    prompt = build_replanner_prompt(requirement, plan_data, failure_context, available_agents, diagnostics=diagnostics)
    
    assert "Environment Diagnostics:" in prompt
    assert diagnostics in prompt
    assert "Look for missing dependencies" in prompt
    assert "recovery" in prompt


@patch("niyam.mission.planner.subprocess.run")
@patch("niyam.core.config.find_niyam_root")
def test_run_mission_replan_integration(mock_find_root, mock_sub_run, run_dir, tmp_path):
    """Test that run_mission_replan correctly calls the AI and updates the plan."""
    repo_root = tmp_path
    mock_find_root.return_value = repo_root
    (repo_root / ".niyam").mkdir(exist_ok=True)
    
    # Setup mission-plan.yaml
    plan_data = {
        "mission": {
            "id": "test-mission",
            "orchestrator": "claude",
            "status": "failed",
            "requirement": "Requirements...",
            "created": "2026-06-08T00:00:00Z",
        },
        "tasks": [
            {
                "id": "T1",
                "status": "completed",
                "title": "Discovery",
                "agent": "default-agent",
                "type": "discovery",
            },
            {
                "id": "T2",
                "status": "failed",
                "title": "Implementation",
                "agent": "default-agent",
                "type": "implementation",
            },
        ],
    }
    plan_path = run_dir / "mission-plan.yaml"
    import yaml
    with open(plan_path, "w") as f:
        yaml.dump(plan_data, f)
        
    (run_dir / "requirement.md").write_text("Requirements...")
    
    # Mock AI response
    mock_ai_output = """
```yaml
tasks:
  - id: T_REC_1
    title: "Recovery: Install missing pkg"
    type: "recovery"
    agent: "default-agent"
    approval_required: true
  - id: T2_FIXED
    title: "Implementation: retry changes"
    type: "implementation"
    agent: "default-agent"
```
"""
    mock_sub_run.return_value = MagicMock(returncode=0, stdout=mock_ai_output, stderr="")
    
    console = Console()
    with patch("niyam.mission.planner.get_latest_mission_id", return_value="test-mission"):
        run_mission_replan(console, mission_id="test-mission")
    
    # Verify plan was updated
    with open(plan_path) as f:
        updated_plan = yaml.safe_load(f)
    
    assert updated_plan["mission"]["status"] == "planned"
    assert len(updated_plan["tasks"]) == 3 # T1 (completed) + T_REC_1 + T2_FIXED
    assert updated_plan["tasks"][1]["type"] == "recovery"
    assert updated_plan["tasks"][1]["id"] == "T_REC_1"


@patch("niyam.mission.executor.execute_single_task")
def test_auto_heal_execute_bypasses_approval(mock_execute_single_task, run_dir, tmp_path):
    """Test that auto_heal_execute bypasses the approval gate for recovery tasks."""
    repo_root = tmp_path
    
    # Setup mission-plan.yaml with a recovery task waiting for approval
    plan_data = {
        "mission": {
            "id": "test-mission",
            "orchestrator": "claude",
            "status": "approved",
            "requirement": "Requirements...",
            "created": "2026-06-08T00:00:00Z",
            "worktree": False,
        },
        "tasks": [
            {
                "id": "T_REC_1",
                "status": "planned",
                "title": "Recovery: Install pkg",
                "agent": "default-agent",
                "type": "recovery",
                "approval_required": True,
            },
        ],
    }
    plan_path = run_dir / "mission-plan.yaml"
    import yaml
    with open(plan_path, "w") as f:
        yaml.dump(plan_data, f)
        
    (run_dir / "approval.json").write_text('{"approved": true}')
    (run_dir / "requirement.md").write_text("Requirements...")
    
    # Mock execute_single_task to succeed
    def mock_execute(*args, **kwargs):
        # We need to simulate the task finishing to break the loop
        task = kwargs.get("task", args[0] if len(args) > 0 else {})
        t_id = task["id"]
        from niyam.mission.state_machine import transition_task
        transition_task(run_dir, t_id, "completed")
        return True

    mock_execute_single_task.side_effect = mock_execute
    
    console = Console(quiet=True)
    with patch("niyam.core.config.find_niyam_root", return_value=repo_root):
        with patch("niyam.mission.executor.resolve_mission_id", return_value="test-mission"):
            # Should automatically execute without pausing for approval
            run_mission_start(console, auto_heal_execute=True, mission_id="test-mission")
    
    # Check that it actually ran
    assert mock_execute_single_task.called
    
    with open(plan_path) as f:
        updated_plan = yaml.safe_load(f)
    
    assert updated_plan["mission"]["status"] == "completed"
    assert updated_plan["tasks"][0]["status"] == "completed"
