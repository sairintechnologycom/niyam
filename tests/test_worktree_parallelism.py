"""Integration tests for Multi-Worktree Parallelism."""

import os
import time
import threading
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock
from rich.console import Console

import pytest
import yaml

from niyam.mission.executor import run_mission_start
from niyam.mission.utils import save_plan


@pytest.fixture
def git_repo(tmp_path):
    """Setup a real git repository for worktree tests."""
    repo = tmp_path / "repo"
    repo.mkdir()
    os.chdir(repo)
    
    subprocess.run(["git", "init"], check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@niyam.ai"], check=True)
    subprocess.run(["git", "config", "user.name", "Niyam Test"], check=True)
    
    (repo / "README.md").write_text("# Test Repo", encoding="utf-8")
    subprocess.run(["git", "add", "."], check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], check=True)
    
    return repo


def test_worktree_parallel_execution(niyam_repo):
    """Verify that parallel tasks with disjoint allowed_files run in separate worktrees."""
    os.chdir(niyam_repo)
    console = Console()
    niyam_dir = niyam_repo / ".niyam"
    
    mission_id = "test-worktree-parallel"
    run_dir = niyam_dir / "runs" / mission_id
    run_dir.mkdir(parents=True, exist_ok=True)

    plan = {
        "mission": {
            "id": mission_id,
            "status": "approved",
            "parallel": 2,
            "worktree": True,
            "requirement": "implement a and b",
            "created": "2026-06-06T12:00:00Z",
            "orchestrator": "claude",
        },
        "tasks": [
            {
                "id": "T1",
                "title": "Implement A",
                "type": "implementation",
                "status": "planned",
                "agent": "default-agent",
                "writes_files": True,
                "allowed_files": ["a.py"],
            },
            {
                "id": "T2",
                "title": "Implement B",
                "type": "implementation",
                "status": "planned",
                "agent": "default-agent",
                "writes_files": True,
                "allowed_files": ["b.py"],
            },
        ],
    }
    save_plan(run_dir, plan)
    (run_dir / "approval.json").write_text('{"approved": true}', encoding="utf-8")
    (run_dir / "requirement.md").write_text("dummy requirements", encoding="utf-8")

    with patch.dict(os.environ, {"NIYAM_TEST": "1"}):
        with patch("shutil.which", return_value="/usr/bin/claude"):
            run_mission_start(console, mission_id=mission_id)

    # In NIYAM_TEST mode, task_runner creates mock files in the worktree
    # Verify files were merged into main repo (execute_single_task mocks changes)
    assert (niyam_repo / "a.py").exists()
    assert "Changes by task T1" in (niyam_repo / "a.py").read_text()
    assert (niyam_repo / "b.py").exists()
    assert "Changes by task T2" in (niyam_repo / "b.py").read_text()
    
    # Verify no worktrees remain
    worktrees_dir = run_dir / "worktrees"
    if worktrees_dir.exists():
        assert len(list(worktrees_dir.iterdir())) == 0
