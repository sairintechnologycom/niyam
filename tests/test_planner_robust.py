"""Tests for planner robustness."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import yaml
from rich.console import Console

from sutra.core.config import get_sutra_dir
from sutra.mission.planner import (
    run_mission_plan,
    extract_yaml_or_json,
    choose_fallback_template,
    inject_validation_commands,
)


def test_extract_yaml_or_json_malformed() -> None:
    """Should correctly extract YAML or JSON block from malformed texts."""
    # Test valid yaml block
    text1 = "some introductory text\n```yaml\ntasks:\n  - id: T1\n    title: Task 1\n```\nsome trailing text"
    parsed1 = extract_yaml_or_json(text1)
    assert parsed1 is not None
    assert parsed1["tasks"][0]["id"] == "T1"

    # Test valid json block
    text2 = 'some introductory text\n```json\n{"tasks": [{"id": "T2", "title": "Task 2"}]}\n```\nsome trailing text'
    parsed2 = extract_yaml_or_json(text2)
    assert parsed2 is not None
    assert parsed2["tasks"][0]["id"] == "T2"

    # Test raw yaml
    text3 = "tasks:\n  - id: T3\n    title: Task 3"
    parsed3 = extract_yaml_or_json(text3)
    assert parsed3 is not None
    assert parsed3["tasks"][0]["id"] == "T3"

    # Test invalid content
    text4 = "this is not yaml or json at all"
    parsed4 = extract_yaml_or_json(text4)
    assert parsed4 is None

    # Test wrapped nested JSON in response field (ultra-robust extraction check)
    text5 = '{"response": "{\\\"tasks\\\": [{\\\"id\\\": \\\"T5\\\", \\\"title\\\": \\\"Task 5\\\"}]}"}'
    parsed5 = extract_yaml_or_json(text5)
    assert parsed5 is not None
    assert parsed5["tasks"][0]["id"] == "T5"


def test_fallback_matches_requirement_keywords() -> None:
    """Should choose closest fallback template based on requirement keywords."""
    assert (
        choose_fallback_template("implement /api/v1/users endpoint") == "api-endpoint"
    )
    assert choose_fallback_template("Fix auth bug where user cannot login") == "bugfix"
    assert choose_fallback_template("refactor executor.py code structure") == "refactor"
    assert choose_fallback_template("do some generic stuff") == "default"


def test_validation_commands_injected_from_project_yaml(sutra_repo: Path) -> None:
    """Should inject validation commands from project.yaml into task configuration."""
    os.chdir(sutra_repo)

    # Setup project config validation commands
    proj_config_path = get_sutra_dir(sutra_repo) / "project.yaml"
    proj_data = yaml.safe_load(proj_config_path.read_text()) or {}
    proj_data["validation"] = {
        "test": "pytest tests/",
        "lint": "ruff check",
        "typecheck": "mypy",
        "build": "hatch build",
    }
    with open(proj_config_path, "w") as f:
        yaml.dump(proj_data, f)

    tasks = [
        {"id": "T1", "type": "discovery"},
        {"id": "T2", "type": "implementation"},
        {"id": "T3", "type": "review"},
        {"id": "T4", "type": "validation"},
    ]

    inject_validation_commands(tasks, sutra_repo)

    assert tasks[0]["validation"]["commands"] == []
    assert "pytest tests/" in tasks[1]["validation"]["commands"]
    assert "ruff check" in tasks[1]["validation"]["commands"]
    assert tasks[2]["validation"]["commands"] == []
    assert "pytest tests/" in tasks[3]["validation"]["commands"]
    assert "ruff check" in tasks[3]["validation"]["commands"]
    assert "mypy" in tasks[3]["validation"]["commands"]
    assert "hatch build" in tasks[3]["validation"]["commands"]


@patch("subprocess.run")
def test_planner_retry_on_bad_output(mock_run: MagicMock, sutra_repo: Path) -> None:
    """Should retry AI planning if first attempt returns garbage, and succeed on second attempt."""
    os.chdir(sutra_repo)
    console = Console(quiet=True)

    # Configure mock_run to fail/return garbage on first run, succeed on second run
    first_res = MagicMock()
    first_res.returncode = 0
    first_res.stdout = "This is garbage output with no code fences or tasks"
    first_res.stderr = ""

    second_res = MagicMock()
    second_res.returncode = 0
    second_res.stdout = """
Here is the plan:
```yaml
tasks:
  - id: T1
    title: "Discovery: analysis"
    type: "discovery"
    agent: "backend-specialist"
    writes_files: false
  - id: T2
    title: "Implementation: code"
    type: "implementation"
    agent: "backend-specialist"
    depends_on: ["T1"]
    files_allowed: ["*"]
  - id: T3
    title: "Validation: test"
    type: "validation"
    agent: "qa-reviewer"
    depends_on: ["T2"]
```
"""
    second_res.stderr = ""

    mock_run.side_effect = [first_res, second_res]

    # Set up config to trigger AI planner
    sutra_config_path = get_sutra_dir(sutra_repo) / "sutra.yaml"
    sutra_data = yaml.safe_load(sutra_config_path.read_text()) or {}
    sutra_data["runtimes"] = ["claude"]
    with open(sutra_config_path, "w") as f:
        yaml.dump(sutra_data, f)

    req_file = sutra_repo / "requirements.md"
    req_file.write_text("# Test requirement", encoding="utf-8")

    # Mock shutil.which to say 'claude' is present
    with patch("shutil.which", return_value="/usr/local/bin/claude"):
        # Make sure we are not in basic unit test mode
        with patch.dict(os.environ, {"SUTRA_TEST": "0", "SUTRA_TEST_PLANNER": "1"}):
            mission_id = run_mission_plan(str(req_file), console=console)

    assert mission_id is not None
    assert mock_run.call_count == 2

    # Check that second output is written to runs
    run_dir = get_sutra_dir(sutra_repo) / "runs" / mission_id
    plan_path = run_dir / "mission-plan.yaml"
    assert plan_path.exists()

    with open(plan_path) as f:
        plan = yaml.safe_load(f)
    assert len(plan["tasks"]) == 3
    assert plan["tasks"][0]["id"] == "T1"
