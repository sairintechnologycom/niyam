"""Tests for Sutra Fleet Mode — parallel execution and worktree isolation."""

from __future__ import annotations

import os
import json
from pathlib import Path
import subprocess
import pytest
import yaml
from rich.console import Console

from sutra.core.config import get_sutra_dir
from sutra.mission.planner import run_mission_plan, run_mission_approve
from sutra.mission.executor import run_mission_start, load_plan, save_plan


@pytest.fixture
def git_repo_with_commit(tmp_repo: Path) -> Path:
    """Create a temporary repo with at least one commit and sutra initialized."""
    # Write a dummy file and commit it so HEAD exists
    dummy_file = tmp_repo / "dummy.txt"
    dummy_file.write_text("initial content", encoding="utf-8")
    
    subprocess.run(["git", "add", "dummy.txt"], cwd=tmp_repo, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=tmp_repo, check=True, capture_output=True)
    
    from sutra.core.init import run_init
    console = Console(quiet=True)
    
    original_dir = os.getcwd()
    os.chdir(tmp_repo)
    try:
        run_init(profile="fullstack", runtime=None, dry_run=False, force=False, console=console)
    finally:
        os.chdir(original_dir)
        
    return tmp_repo


def test_fleet_parallel_execution(git_repo_with_commit: Path) -> None:
    """Should execute independent tasks in parallel with worktree isolation."""
    os.chdir(git_repo_with_commit)
    console = Console(quiet=True)

    # 1. Create requirements
    req_file = git_repo_with_commit / "requirements.md"
    req_file.write_text("# Test Fleet Parallelism\n", encoding="utf-8")

    mission_id = run_mission_plan(str(req_file), console=console)
    run_mission_approve(console=console)

    run_dir = get_sutra_dir(git_repo_with_commit) / "runs" / mission_id
    plan_data = load_plan(run_dir)

    # 2. Re-structure tasks to test parallel fork and join:
    # T1 -> T2 (parallel)
    # T1 -> T3 (parallel)
    # T2 & T3 -> T4 (join/validation)
    plan_data["tasks"] = [
        {
            "id": "T1",
            "title": "Discovery task",
            "type": "discovery",
            "status": "pending",
            "agent": "backend-specialist",
            "writes_files": False,
        },
        {
            "id": "T2",
            "title": "Parallel task A",
            "type": "implementation",
            "status": "pending",
            "agent": "backend-specialist",
            "depends_on": ["T1"],
            "files_allowed": ["*"],
        },
        {
            "id": "T3",
            "title": "Parallel task B",
            "type": "implementation",
            "status": "pending",
            "agent": "backend-specialist",
            "depends_on": ["T1"],
            "files_allowed": ["*"],
        },
        {
            "id": "T4",
            "title": "Validation task",
            "type": "validation",
            "status": "pending",
            "agent": "qa-reviewer",
            "depends_on": ["T2", "T3"],
        }
    ]
    save_plan(run_dir, plan_data)

    # 3. Run mission with SUTRA_TEST enabled so CLI execution is mocked
    os.environ["SUTRA_TEST"] = "1"
    try:
        run_mission_start(console=console, parallel=2, worktree=True)
    finally:
        del os.environ["SUTRA_TEST"]

    # 4. Verify completion
    updated_plan = load_plan(run_dir)
    assert updated_plan["mission"]["status"] == "completed"
    
    # Check all tasks ran and completed
    for task in updated_plan["tasks"]:
        assert task["status"] == "completed"

    # Check that changes from both T2 and T3 were successfully merged back to workspace!
    # Because SUTRA_TEST mocks wrote dummy files: change-T2.txt and change-T3.txt
    assert (git_repo_with_commit / "change-T2.txt").exists()
    assert (git_repo_with_commit / "change-T3.txt").exists()

    # Check branches were cleaned up
    res = subprocess.run(["git", "branch"], cwd=git_repo_with_commit, capture_output=True, text=True)
    assert f"sutra-{mission_id}-T1" not in res.stdout
    assert f"sutra-{mission_id}-T4" not in res.stdout


def test_fleet_dependency_failure(git_repo_with_commit: Path) -> None:
    """Should skip tasks that depend on failed tasks."""
    os.chdir(git_repo_with_commit)
    console = Console(quiet=True)

    req_file = git_repo_with_commit / "requirements.md"
    req_file.write_text("# Test Dependency Failure\n", encoding="utf-8")

    mission_id = run_mission_plan(str(req_file), console=console)
    run_mission_approve(console=console)

    run_dir = get_sutra_dir(git_repo_with_commit) / "runs" / mission_id
    plan_data = load_plan(run_dir)

    # Re-structure: T1 (completes) -> T2 (failed) -> T3 (depends on T2, should be skipped)
    plan_data["tasks"] = [
        {
            "id": "T1",
            "title": "Discovery",
            "type": "discovery",
            "status": "pending",
            "agent": "backend-specialist",
        },
        {
            "id": "T2",
            "title": "Failing Task",
            "type": "implementation",
            "status": "failed", # Pre-failed to trigger scheduler logic
            "agent": "backend-specialist",
            "depends_on": ["T1"],
        },
        {
            "id": "T3",
            "title": "Dependent Task",
            "type": "implementation",
            "status": "pending",
            "agent": "backend-specialist",
            "depends_on": ["T2"],
        }
    ]
    save_plan(run_dir, plan_data)

    os.environ["SUTRA_TEST"] = "1"
    try:
        with pytest.raises(SystemExit):
            run_mission_start(console=console, parallel=2, worktree=True)
    finally:
        del os.environ["SUTRA_TEST"]

    # Verify task states
    updated_plan = load_plan(run_dir)
    assert updated_plan["mission"]["status"] == "failed"
    assert updated_plan["tasks"][0]["status"] == "completed"
    assert updated_plan["tasks"][1]["status"] == "failed"
    assert updated_plan["tasks"][2]["status"] == "skipped"


def test_fleet_worktree_fallback_when_no_git(tmp_path: Path) -> None:
    """Should execute sequentially without worktrees if directory is not a Git repo."""
    # Note: tmp_path is a plain directory (NOT a git repo)
    from sutra.core.init import run_init
    console = Console(quiet=True)

    original_dir = os.getcwd()
    os.chdir(tmp_path)
    try:
        run_init(profile="fullstack", runtime=None, dry_run=False, force=False, console=console)
        
        req_file = tmp_path / "requirements.md"
        req_file.write_text("# Test No Git\n", encoding="utf-8")
        
        mission_id = run_mission_plan(str(req_file), console=console)
        run_mission_approve(console=console)

        # Start execution. Since parallel is 1 and worktree defaults to True,
        # it should detect no Git and fallback to worktree=False, executing sequentially.
        os.environ["SUTRA_TEST"] = "1"
        try:
            run_mission_start(console=console, parallel=1, worktree=None)
        finally:
            del os.environ["SUTRA_TEST"]

        # Verify completed in place
        run_dir = get_sutra_dir(tmp_path) / "runs" / mission_id
        updated_plan = load_plan(run_dir)
        assert updated_plan["mission"]["status"] == "completed"
        assert updated_plan["mission"]["worktree"] is False  # verified fallback
    finally:
        os.chdir(original_dir)
