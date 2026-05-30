"""Tests for multi-runtime task delegation."""

from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from rich.console import Console

from sutra.core.config import get_sutra_dir
from sutra.mission.planner import run_mission_plan, build_planner_prompt
from sutra.mission.executor import run_mission_start, load_plan, save_plan


def test_planner_prompt_contains_runtime() -> None:
    """Should contain runtime instructions and runtime in YAML schema example."""
    prompt = build_planner_prompt(
        requirement="Build a feature",
        repo_map="file.py",
        available_agents=["backend-specialist", "qa-reviewer"],
    )
    assert "runtime" in prompt
    assert "gemini" in prompt
    assert "codex" in prompt
    assert "claude" in prompt


def test_planner_parses_runtime_field(sutra_repo: Path) -> None:
    """Should correctly parse and store the runtime field when generating plans."""
    os.chdir(sutra_repo)
    console = Console(quiet=True)

    # Create requirements file
    req_file = sutra_repo / "requirements.md"
    req_file.write_text("# Test multi-runtime planning", encoding="utf-8")

    # Mock planner output to return tasks with different runtimes
    mock_planner_output = """
```yaml
tasks:
  - id: T1
    title: "Discovery task"
    type: "discovery"
    agent: "backend-specialist"
    runtime: "claude"
  - id: T2
    title: "Implementation task"
    type: "implementation"
    agent: "backend-specialist"
    runtime: "gemini"
  - id: T3
    title: "Validation task"
    type: "validation"
    agent: "qa-reviewer"
```
"""

    mock_completed_proc = MagicMock()
    mock_completed_proc.returncode = 0
    mock_completed_proc.stdout = mock_planner_output
    mock_completed_proc.stderr = ""

    # Enable AI planner for tests
    os.environ["SUTRA_TEST_PLANNER"] = "1"
    try:
        with patch("subprocess.run", return_value=mock_completed_proc):
            mission_id = run_mission_plan(str(req_file), console=console)
    finally:
        del os.environ["SUTRA_TEST_PLANNER"]

    assert mission_id is not None
    sutra_dir = get_sutra_dir(sutra_repo)
    run_dir = sutra_dir / "runs" / mission_id

    # Verify parsed plan tasks contain runtimes correctly
    plan = load_plan(run_dir)
    assert len(plan["tasks"]) == 3
    assert plan["tasks"][0]["runtime"] == "claude"
    assert plan["tasks"][1]["runtime"] == "gemini"
    assert plan["tasks"][2]["runtime"] is None or plan["tasks"][2]["runtime"] == ""


def test_executor_resolves_task_runtime(sutra_repo: Path) -> None:
    """Should execute the correct runtime per task and fallback to global orchestrator if omitted."""
    os.chdir(sutra_repo)
    console = Console(quiet=True)

    # 1. Create a planned and approved mission
    req_file = sutra_repo / "requirements.md"
    req_file.write_text("# Test runtimes", encoding="utf-8")
    mission_id = run_mission_plan(str(req_file), console=console)

    # Approve it
    approval_path = get_sutra_dir(sutra_repo) / "runs" / mission_id / "approval.json"
    approval_path.write_text(
        '{"approved": true, "timestamp": "2026-05-28T22:00:00Z"}', encoding="utf-8"
    )

    run_dir = get_sutra_dir(sutra_repo) / "runs" / mission_id
    plan_data = load_plan(run_dir)
    plan_data["mission"]["status"] = "approved"

    # Set custom runtimes in YAML
    plan_data["tasks"] = [
        {
            "id": "T1",
            "title": "Task 1 (Gemini)",
            "type": "discovery",
            "status": "pending",
            "agent": "backend-specialist",
            "runtime": "gemini",
        },
        {
            "id": "T2",
            "title": "Task 2 (Codex)",
            "type": "implementation",
            "status": "pending",
            "agent": "backend-specialist",
            "runtime": "codex",
            "depends_on": ["T1"],
        },
        {
            "id": "T3",
            "title": "Task 3 (Fallback Claude)",
            "type": "validation",
            "status": "pending",
            "agent": "qa-reviewer",
            "depends_on": ["T2"],
        },
    ]
    save_plan(run_dir, plan_data)

    # Mock shutil.which to find all runtimes
    def mock_which(cmd: str) -> str | None:
        if cmd in ["gemini", "codex", "claude"]:
            return f"/mock/bin/{cmd}"
        return None

    # Patch subprocess.run to track invocations
    with (
        patch("shutil.which", side_effect=mock_which),
        patch("subprocess.run") as mock_run,
    ):
        # SUTRA_TEST=0 allows running subprocess block.
        # SUTRA_CI_AUTO_APPROVE=1 satisfies the approval check.
        os.environ["SUTRA_CI_AUTO_APPROVE"] = "1"
        try:
            run_mission_start(console=console)
        finally:
            del os.environ["SUTRA_CI_AUTO_APPROVE"]

        # Let's inspect mock_run calls
        # There should be calls to git status / diff or executing runtimes
        runtime_calls = []
        for call in mock_run.call_args_list:
            cmd = call[0][0]
            if isinstance(cmd, list) and len(cmd) > 0:
                if cmd[0] in ["gemini", "codex", "claude"]:
                    runtime_calls.append(cmd[0])

        # Assert correct dispatching sequence: T1 -> gemini, T2 -> codex, T3 -> claude (fallback)
        assert runtime_calls == ["gemini", "codex", "claude"]

        # Check Token Ledger
        ledger_path = run_dir / "token-ledger.json"
        assert ledger_path.exists()
        with open(ledger_path, encoding="utf-8") as f:
            ledger = json.load(f)

        events = ledger.get("events", [])
        assert len(events) >= 3
        # Map task ID to runtime used from ledger
        task_runtimes = {
            entry["task_id"]: entry["runtime"] for entry in events if "task_id" in entry
        }
        assert task_runtimes["T1"] == "gemini"
        assert task_runtimes["T2"] == "codex"
        assert task_runtimes["T3"] == "claude"
