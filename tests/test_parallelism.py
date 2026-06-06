"""Tests for Niyam mission parallelism and collision management."""

from __future__ import annotations

import os
import time
import threading
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from rich.console import Console

import pytest
from niyam.mission.executor import run_mission_start
from niyam.mission.utils import save_plan


def test_discovery_parallelism(niyam_repo: Path) -> None:
    """Multiple discovery tasks should run in parallel despite having overlapping patterns."""
    os.chdir(niyam_repo)
    console = Console(quiet=True)
    niyam_dir = niyam_repo / ".niyam"
    mission_id = "test-parallel-discovery"
    run_dir = niyam_dir / "runs" / mission_id
    run_dir.mkdir(parents=True, exist_ok=True)

    plan = {
        "mission": {
            "id": mission_id,
            "status": "approved",
            "parallel": 2,
            "worktree": False,
            "requirement": "dummy",
            "created": "2026-06-06T12:00:00Z",
            "orchestrator": "claude",
        },
        "tasks": [
            {
                "id": "T1",
                "title": "Discovery 1",
                "type": "discovery",
                "status": "planned",
                "agent": "default-agent",
                "writes_files": False,
                "files_allowed": ["*"],
            },
            {
                "id": "T2",
                "title": "Discovery 2",
                "type": "discovery",
                "status": "planned",
                "agent": "default-agent",
                "writes_files": False,
                "files_allowed": ["*"],
            },
        ],
    }
    save_plan(run_dir, plan)
    (run_dir / "approval.json").write_text('{"approved": true}', encoding="utf-8")

    # Use events to track concurrency
    t1_started = threading.Event()
    t2_started = threading.Event()
    finish_all = threading.Event()

    def mock_execute_task(task, **kwargs):
        t_id = task["id"]
        if t_id == "T1":
            t1_started.set()
        elif t_id == "T2":
            t2_started.set()

        # Wait for both to start to prove parallelism
        # We use a timeout to avoid hanging the test if it fails
        finish_all.wait(timeout=5)
        return True

    with patch(
        "niyam.mission.executor.execute_single_task", side_effect=mock_execute_task
    ):
        # Run in a separate thread because it blocks until tasks complete
        exec_thread = threading.Thread(
            target=run_mission_start, args=(console,), kwargs={"mission_id": mission_id}
        )
        exec_thread.start()

        # Wait for both to be running simultaneously
        both_started = t1_started.wait(timeout=5) and t2_started.wait(timeout=5)
        finish_all.set()
        exec_thread.join()

        assert (
            both_started
        ), "Discovery tasks should have run in parallel despite both having '*'"


def test_implementation_serialization(niyam_repo: Path) -> None:
    """Overlapping implementation tasks should be serialized."""
    os.chdir(niyam_repo)
    console = Console(quiet=True)
    niyam_dir = niyam_repo / ".niyam"
    mission_id = "test-serialization"
    run_dir = niyam_dir / "runs" / mission_id
    run_dir.mkdir(parents=True, exist_ok=True)

    plan = {
        "mission": {
            "id": mission_id,
            "status": "approved",
            "parallel": 2,
            "worktree": False,
            "requirement": "dummy",
            "created": "2026-06-06T12:00:00Z",
            "orchestrator": "claude",
        },
        "tasks": [
            {
                "id": "T1",
                "title": "Writer 1",
                "type": "implementation",
                "status": "planned",
                "agent": "default-agent",
                "writes_files": True,
                "files_allowed": ["*"],
            },
            {
                "id": "T2",
                "title": "Writer 2",
                "type": "implementation",
                "status": "planned",
                "agent": "default-agent",
                "writes_files": True,
                "files_allowed": ["*"],
            },
        ],
    }
    save_plan(run_dir, plan)
    (run_dir / "approval.json").write_text('{"approved": true}', encoding="utf-8")

    running_count = 0
    max_concurrent = 0
    lock = threading.Lock()

    def mock_execute_task(task, **kwargs):
        nonlocal running_count, max_concurrent
        with lock:
            running_count += 1
            max_concurrent = max(max_concurrent, running_count)

        time.sleep(0.1)

        with lock:
            running_count -= 1
        return True

    with patch(
        "niyam.mission.executor.execute_single_task", side_effect=mock_execute_task
    ):
        run_mission_start(console, mission_id=mission_id)

        assert (
            max_concurrent == 1
        ), "Implementation tasks with overlapping '*' should have been serialized"


def test_dag_dependency_respected(niyam_repo: Path) -> None:
    """Task T2 should not start until T1 finishes, respecting DAG order."""
    os.chdir(niyam_repo)
    console = Console(quiet=True)
    niyam_dir = niyam_repo / ".niyam"
    mission_id = "test-dag"
    run_dir = niyam_dir / "runs" / mission_id
    run_dir.mkdir(parents=True, exist_ok=True)

    plan = {
        "mission": {
            "id": mission_id,
            "status": "approved",
            "parallel": 2,
            "worktree": False,
            "requirement": "dummy",
            "created": "2026-06-06T12:00:00Z",
            "orchestrator": "claude",
        },
        "tasks": [
            {
                "id": "T1",
                "title": "Parent",
                "type": "discovery",
                "status": "planned",
                "agent": "default-agent",
                "writes_files": False,
                "files_allowed": ["*"],
            },
            {
                "id": "T2",
                "title": "Child",
                "type": "discovery",
                "status": "planned",
                "agent": "default-agent",
                "depends_on": ["T1"],
                "writes_files": False,
                "files_allowed": ["*"],
            },
        ],
    }
    save_plan(run_dir, plan)
    (run_dir / "approval.json").write_text('{"approved": true}', encoding="utf-8")

    t1_finished = False
    t2_violated = False

    def mock_execute_task(task, **kwargs):
        nonlocal t1_finished, t2_violated
        t_id = task["id"]
        if t_id == "T1":
            time.sleep(0.2)
            t1_finished = True
        elif t_id == "T2":
            if not t1_finished:
                t2_violated = True
        return True

    with patch(
        "niyam.mission.executor.execute_single_task", side_effect=mock_execute_task
    ):
        run_mission_start(console, mission_id=mission_id)

        assert not t2_violated, "Task T2 started before T1 was finished"
