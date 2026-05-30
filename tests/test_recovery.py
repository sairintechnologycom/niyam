"""Tests for mission error recovery commands (retry, skip, rollback)."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from rich.console import Console

from sutra.core.config import get_sutra_dir
from sutra.mission.planner import run_mission_plan, run_mission_approve
from sutra.mission.executor import (
    run_mission_retry,
    run_mission_skip,
    run_mission_rollback,
    load_plan,
    save_plan,
)


def test_mission_skip_unblocks_downstream(sutra_repo: Path) -> None:
    """Marking a task as skipped should unblock downstream tasks and run them."""
    os.chdir(sutra_repo)
    console = Console(quiet=True)

    # Initial commit so HEAD exists and we have commits
    os.system("git add . && git commit -m 'Initial commit'")

    # 1. Create plan
    req_file = sutra_repo / "requirements.md"
    req_file.write_text("# Test\n", encoding="utf-8")
    mission_id = run_mission_plan(str(req_file), console=console)
    run_mission_approve(console=console)

    run_dir = get_sutra_dir(sutra_repo) / "runs" / mission_id

    # Mark first task (T1) as failed, which would normally auto-skip T2
    plan = load_plan(run_dir)
    plan["tasks"][0]["status"] = "failed"
    save_plan(run_dir, plan)

    # 2. Skip T1 using run_mission_skip, with worktree=False to avoid worktree isolation merge issues
    os.environ["SUTRA_TEST"] = "1"
    try:
        try:
            run_mission_skip(task_id="T1", console=console, worktree=False)
        except SystemExit:
            pass  # Expected to exit since mission is marked failed at end due to a skipped task
    finally:
        del os.environ["SUTRA_TEST"]

    # 3. Verify T1 is marked as skipped, and downstream tasks execute
    plan = load_plan(run_dir)
    assert plan["tasks"][0]["status"] == "skipped"
    # Because T1 is skipped (not failed), T2, T3, T4, T5 should run and complete under mock
    assert plan["tasks"][1]["status"] == "completed"
    assert plan["tasks"][2]["status"] == "completed"
    assert plan["tasks"][3]["status"] == "completed"
    assert plan["tasks"][4]["status"] == "completed"
    assert (
        plan["mission"]["status"] == "failed"
    )  # Failed is expected because a task was skipped


def test_mission_retry_requeues_tasks(sutra_repo: Path) -> None:
    """Retrying a mission should set failed/skipped tasks to pending and re-run them."""
    os.chdir(sutra_repo)
    console = Console(quiet=True)

    # Initial commit so HEAD exists and we have commits
    os.system("git add . && git commit -m 'Initial commit'")

    req_file = sutra_repo / "requirements.md"
    req_file.write_text("# Test\n", encoding="utf-8")
    mission_id = run_mission_plan(str(req_file), console=console)
    run_mission_approve(console=console)

    run_dir = get_sutra_dir(sutra_repo) / "runs" / mission_id

    # Set some tasks to failed/skipped
    plan = load_plan(run_dir)
    plan["tasks"][0]["status"] = "failed"
    plan["tasks"][1]["status"] = "skipped"
    save_plan(run_dir, plan)

    # Run retry under mock, with worktree=False to avoid worktree isolation merge issues
    os.environ["SUTRA_TEST"] = "1"
    try:
        run_mission_retry(console=console, worktree=False)
    finally:
        del os.environ["SUTRA_TEST"]

    # All tasks should be completed now
    plan = load_plan(run_dir)
    for t in plan["tasks"]:
        assert t["status"] == "completed"
    assert plan["mission"]["status"] == "completed"


def test_mission_rollback_git_checkout(sutra_repo: Path) -> None:
    """Rollback should checkout the recorded base_sha in git."""
    os.chdir(sutra_repo)
    console = Console(quiet=True)

    # Initial commit so HEAD exists
    os.system("git add . && git commit -m 'Initial commit'")

    req_file = sutra_repo / "requirements.md"
    req_file.write_text("# Test\n", encoding="utf-8")
    mission_id = run_mission_plan(str(req_file), console=console)
    run_mission_approve(console=console)

    run_dir = get_sutra_dir(sutra_repo) / "runs" / mission_id
    plan = load_plan(run_dir)
    base_sha = "abc123commit"
    plan["mission"]["base_sha"] = base_sha
    save_plan(run_dir, plan)

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        run_mission_rollback(console=console)

        # Verify git checkout base_sha command is executed
        mock_run.assert_any_call(
            ["git", "checkout", base_sha, "--", "."],
            cwd=sutra_repo,
            capture_output=True,
            text=True,
        )

    plan = load_plan(run_dir)
    assert plan["mission"]["status"] == "failed"
