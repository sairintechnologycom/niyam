"""Tests for the mission template system."""

from __future__ import annotations

import os
from pathlib import Path
import yaml
from rich.console import Console

from niyam.core.config import get_niyam_dir
from niyam.mission.planner import run_mission_plan
from niyam.mission.executor import load_plan


def test_builtin_template_planning(niyam_repo: Path) -> None:
    """Should plan a mission using the built-in api-endpoint template."""
    os.chdir(niyam_repo)
    console = Console(quiet=True)

    # 1. Generate plan using api-endpoint template
    mission_id = run_mission_plan(
        requirements_path="api-endpoint-test",
        console=console,
        template="api-endpoint",
        runtime_override="claude",
    )
    assert mission_id is not None

    niyam_dir = get_niyam_dir(niyam_repo)
    run_dir = niyam_dir / "runs" / mission_id
    assert run_dir.is_dir()

    # Load generated plan
    plan = load_plan(run_dir)
    assert plan["mission"]["id"] == mission_id
    assert plan["mission"]["status"] == "planned"
    assert plan["mission"]["orchestrator"] == "claude"

    # Verify variable interpolation (using defaults in non-interactive NIYAM_TEST mode)
    # T2 should be: "TDD: Write endpoint contract test case for GET /api/v1/resource"
    tasks = plan["tasks"]
    assert len(tasks) == 5
    assert (
        tasks[1]["title"]
        == "TDD: Write endpoint contract test case for GET /api/v1/resource"
    )
    assert (
        tasks[2]["title"]
        == "Implementation: implement the GET /api/v1/resource controller and router"
    )


def test_custom_template_planning(niyam_repo: Path) -> None:
    """Should plan a mission using a custom template file in .niyam/templates/missions/."""
    os.chdir(niyam_repo)
    console = Console(quiet=True)

    niyam_dir = get_niyam_dir(niyam_repo)
    custom_tmpl_dir = niyam_dir / "templates" / "missions"
    custom_tmpl_dir.mkdir(parents=True, exist_ok=True)

    # Define custom template
    custom_template = {
        "name": "custom-tmpl",
        "description": "My custom development flow",
        "variables": [
            {
                "name": "feature_name",
                "prompt": "Name of the feature",
                "default": "AwesomeFeature",
            },
        ],
        "tasks": [
            {
                "id": "T1",
                "title": "Design {{feature_name}} architecture",
                "type": "discovery",
                "agent": "backend-specialist",
                "writes_files": False,
            },
            {
                "id": "T2",
                "title": "Write tests for {{feature_name}}",
                "type": "implementation",
                "agent": "qa-reviewer",
                "depends_on": ["T1"],
            },
        ],
    }

    custom_tmpl_file = custom_tmpl_dir / "my-custom.yaml"
    with open(custom_tmpl_file, "w", encoding="utf-8") as f:
        yaml.safe_dump(custom_template, f)

    # Generate plan using the custom template
    mission_id = run_mission_plan(
        requirements_path="custom-test",
        console=console,
        template="my-custom",
        runtime_override="codex",
    )

    run_dir = niyam_dir / "runs" / mission_id
    plan = load_plan(run_dir)

    assert plan["mission"]["orchestrator"] == "codex"
    assert len(plan["tasks"]) == 2
    assert plan["tasks"][0]["title"] == "Design AwesomeFeature architecture"
    assert plan["tasks"][1]["title"] == "Write tests for AwesomeFeature"
