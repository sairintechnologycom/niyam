"""Tests for task execution runtime fallback on token exhaustion."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from rich.console import Console

from niyam.core.config import get_niyam_dir, load_niyam_config, save_niyam_config
from niyam.mission.executor import execute_single_task, save_plan


def test_executor_fallback_success(niyam_repo: Path, monkeypatch):
    """Test that task executor automatically falls back to gemini when claude gets quota errors."""
    os.chdir(niyam_repo)
    console = Console(quiet=True)
    niyam_dir = get_niyam_dir(niyam_repo)

    # Enable claude and gemini runtimes in config
    config = load_niyam_config(niyam_repo)
    config.runtimes = ["claude", "gemini"]
    save_niyam_config(config, niyam_repo)

    # Mock shutil.which to find both CLIs
    monkeypatch.setattr(shutil, "which", lambda cmd: f"/usr/bin/{cmd}")

    # Set up task directories and plan
    run_dir = niyam_dir / "runs" / "test-mission"
    run_dir.mkdir(parents=True, exist_ok=True)

    plan_data = {
        "mission": {
            "id": "test-mission",
            "requirement": "Requirements doc",
            "created": "2026-06-03T12:00:00Z",
            "status": "running",
            "orchestrator": "claude",
            "parallel": 1,
            "worktree": False,
        },
        "tasks": [],
    }
    save_plan(run_dir, plan_data)

    task = {
        "id": "T1",
        "title": "Build user model",
        "type": "implementation",
        "status": "running",
        "agent": "backend-specialist",
        "runtime": "claude",
        "writes_files": False,
    }

    subprocess_runs = []
    original_run = subprocess.run

    def mock_run(cmd, *args, **kwargs):
        cmd_name = cmd[0] if isinstance(cmd, list) else cmd.split()[0]
        if "claude" in cmd_name or "gemini" in cmd_name:
            subprocess_runs.append(cmd)
            if "claude" in cmd_name:
                # Mock quota exceeded error in parallel mode redirect log
                log_path = run_dir / "task-T1-output.log"
                log_path.write_text(
                    "Fatal: quota exceeded on current plan.", encoding="utf-8"
                )
                raise subprocess.CalledProcessError(returncode=1, cmd=cmd)
            else:
                # Mock success for gemini
                log_path = run_dir / "task-T1-output.log"
                log_path.write_text(
                    "Code generation completed successfully.", encoding="utf-8"
                )
                return subprocess.CompletedProcess(
                    cmd, returncode=0, stdout="", stderr=""
                )
        return original_run(cmd, *args, **kwargs)

    monkeypatch.setattr(subprocess, "run", mock_run)

    # Execute task headlessly (non_interactive=True)
    res = execute_single_task(
        task=task,
        run_dir=run_dir,
        niyam_dir=niyam_dir,
        repo_root=niyam_repo,
        mission_id="test-mission",
        use_worktree=False,
        project_config=None,
        console=console,
        non_interactive=True,
    )

    assert res is True
    # Should have run subprocess twice: once for claude, then fallback to gemini
    assert len(subprocess_runs) == 2
    assert "claude" in subprocess_runs[0][0]
    assert "gemini" in subprocess_runs[1][0]
    # Task runtime should have been updated to gemini
    assert task["runtime"] == "gemini"


def test_executor_fallback_no_runtimes(niyam_repo: Path, monkeypatch):
    """Test that executor fails when the fallback runtime itself gets quota error."""
    os.chdir(niyam_repo)
    console = Console(quiet=True)
    niyam_dir = get_niyam_dir(niyam_repo)

    config = load_niyam_config(niyam_repo)
    config.runtimes = ["claude", "gemini"]
    save_niyam_config(config, niyam_repo)

    monkeypatch.setattr(shutil, "which", lambda cmd: f"/usr/bin/{cmd}")

    run_dir = niyam_dir / "runs" / "test-mission"
    run_dir.mkdir(parents=True, exist_ok=True)

    plan_data = {
        "mission": {
            "id": "test-mission",
            "requirement": "Requirements doc",
            "created": "2026-06-03T12:00:00Z",
            "status": "running",
            "orchestrator": "claude",
            "parallel": 1,
            "worktree": False,
        },
        "tasks": [],
    }
    save_plan(run_dir, plan_data)

    task = {
        "id": "T1",
        "title": "Build user model",
        "type": "implementation",
        "status": "running",
        "agent": "backend-specialist",
        "runtime": "claude",
        "writes_files": False,
    }

    subprocess_runs = []
    original_run = subprocess.run

    def mock_run(cmd, *args, **kwargs):
        cmd_name = cmd[0] if isinstance(cmd, list) else cmd.split()[0]
        if "claude" in cmd_name or "gemini" in cmd_name:
            subprocess_runs.append(cmd)
            log_path = run_dir / "task-T1-output.log"
            log_path.write_text("Error: rate limit exceeded.", encoding="utf-8")
            raise subprocess.CalledProcessError(returncode=1, cmd=cmd)
        return original_run(cmd, *args, **kwargs)

    monkeypatch.setattr(subprocess, "run", mock_run)

    res = execute_single_task(
        task=task,
        run_dir=run_dir,
        niyam_dir=niyam_dir,
        repo_root=niyam_repo,
        mission_id="test-mission",
        use_worktree=False,
        project_config=None,
        console=console,
        non_interactive=True,
    )

    # Task should fail after trying both runtimes
    assert res is False
    assert len(subprocess_runs) == 2
    assert "claude" in subprocess_runs[0][0]
    assert "gemini" in subprocess_runs[1][0]


def test_executor_no_fallback_on_code_failure(niyam_repo: Path, monkeypatch):
    """Test that executor does not fallback if the failure is a standard code error (no quota keywords)."""
    os.chdir(niyam_repo)
    console = Console(quiet=True)
    niyam_dir = get_niyam_dir(niyam_repo)

    config = load_niyam_config(niyam_repo)
    config.runtimes = ["claude", "gemini"]
    save_niyam_config(config, niyam_repo)

    monkeypatch.setattr(shutil, "which", lambda cmd: f"/usr/bin/{cmd}")

    run_dir = niyam_dir / "runs" / "test-mission"
    run_dir.mkdir(parents=True, exist_ok=True)

    plan_data = {
        "mission": {
            "id": "test-mission",
            "requirement": "Requirements doc",
            "created": "2026-06-03T12:00:00Z",
            "status": "running",
            "orchestrator": "claude",
            "parallel": 1,
            "worktree": False,
        },
        "tasks": [],
    }
    save_plan(run_dir, plan_data)

    task = {
        "id": "T1",
        "title": "Build user model",
        "type": "implementation",
        "status": "running",
        "agent": "backend-specialist",
        "runtime": "claude",
        "writes_files": False,
    }

    subprocess_runs = []
    original_run = subprocess.run

    def mock_run(cmd, *args, **kwargs):
        cmd_name = cmd[0] if isinstance(cmd, list) else cmd.split()[0]
        if "claude" in cmd_name or "gemini" in cmd_name:
            subprocess_runs.append(cmd)
            log_path = run_dir / "task-T1-output.log"
            # Standard code syntax error or linter failure, no quota keywords
            log_path.write_text(
                "SyntaxError: invalid syntax in models.py line 45", encoding="utf-8"
            )
            raise subprocess.CalledProcessError(returncode=1, cmd=cmd)
        return original_run(cmd, *args, **kwargs)

    monkeypatch.setattr(subprocess, "run", mock_run)

    res = execute_single_task(
        task=task,
        run_dir=run_dir,
        niyam_dir=niyam_dir,
        repo_root=niyam_repo,
        mission_id="test-mission",
        use_worktree=False,
        project_config=None,
        console=console,
        non_interactive=True,
    )

    # Task should fail immediately on first runtime, no fallbacks tried
    assert res is False
    assert len(subprocess_runs) == 1
    assert "claude" in subprocess_runs[0][0]
