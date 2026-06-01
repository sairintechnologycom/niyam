"""Tests for the mission and task lifecycle hooks system."""

from __future__ import annotations

import os
from pathlib import Path
import yaml
from rich.console import Console

from niyam.core.config import get_niyam_dir
from niyam.mission.executor import run_hooks


def test_hooks_lifecycle_triggers(niyam_repo: Path) -> None:
    """Should load hooks.yaml and execute matched hooks, interpolating variables."""
    os.chdir(niyam_repo)
    console = Console(quiet=True)

    niyam_dir = get_niyam_dir(niyam_repo)
    hooks_file = niyam_dir / "hooks.yaml"

    # Define hooks config
    hooks_config = {
        "hooks": {
            "pre_mission": [
                "echo 'Pre-mission starting for {{mission_id}}' > pre_mission.txt"
            ],
            "pre_task": [
                {
                    "run": "echo 'Pre-task {{task.id}} with agent {{task.agent}}' > pre_task_{{task.id}}.txt",
                    "when": "task.type == 'implementation'",
                },
                {
                    "run": "echo 'This should not run' > should_not_run.txt",
                    "when": "task.type == 'nonexistent'",
                },
            ],
            "post_task": [
                "echo 'Post-task {{task.id}} status: {{task.status}}' > post_task_{{task.id}}.txt"
            ],
            "post_mission": [
                "echo 'Post-mission {{mission_id}} status: {{mission_status}}' > post_mission.txt"
            ],
        }
    }

    with open(hooks_file, "w", encoding="utf-8") as f:
        yaml.safe_dump(hooks_config, f)

    # 1. Run pre_mission hook
    run_hooks("pre_mission", {"mission_id": "m1"}, niyam_dir, console)
    pre_mission_file = niyam_repo / "pre_mission.txt"
    assert pre_mission_file.exists()
    assert "Pre-mission starting for m1" in pre_mission_file.read_text(encoding="utf-8")

    # 2. Run pre_task hook for implementation task
    impl_task = {
        "id": "T2",
        "type": "implementation",
        "agent": "coder-agent",
        "title": "Impl task",
    }
    run_hooks("pre_task", {"mission_id": "m1", "task": impl_task}, niyam_dir, console)
    impl_hook_file = niyam_repo / "pre_task_T2.txt"
    assert impl_hook_file.exists()
    assert "Pre-task T2 with agent coder-agent" in impl_hook_file.read_text(
        encoding="utf-8"
    )

    # 3. Run pre_task hook for discovery task (should NOT run because of when conditional)
    disc_task = {
        "id": "T1",
        "type": "discovery",
        "agent": "scanner-agent",
        "title": "Disc task",
    }
    run_hooks("pre_task", {"mission_id": "m1", "task": disc_task}, niyam_dir, console)
    should_not_run_file = niyam_repo / "should_not_run.txt"
    assert not should_not_run_file.exists()

    # 4. Run post_task hook
    impl_task["status"] = "completed"
    run_hooks("post_task", {"mission_id": "m1", "task": impl_task}, niyam_dir, console)
    post_task_file = niyam_repo / "post_task_T2.txt"
    assert post_task_file.exists()
    assert "Post-task T2 status: completed" in post_task_file.read_text(
        encoding="utf-8"
    )

    # 5. Run post_mission hook
    run_hooks(
        "post_mission",
        {"mission_id": "m1", "mission_status": "success"},
        niyam_dir,
        console,
    )
    post_mission_file = niyam_repo / "post_mission.txt"
    assert post_mission_file.exists()
    assert "Post-mission m1 status: success" in post_mission_file.read_text(
        encoding="utf-8"
    )
