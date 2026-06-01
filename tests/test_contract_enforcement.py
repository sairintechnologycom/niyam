"""Tests for Niyam contract enforcement."""

from __future__ import annotations

import os
from pathlib import Path
import pytest
import yaml
from rich.console import Console
from unittest.mock import patch, MagicMock

from niyam.core.config import get_niyam_dir
from niyam.mission.planner import run_mission_plan, run_mission_approve
from niyam.mission.executor import run_mission_start, load_plan


def test_any_bypass_removed_and_contract_prompt_enrichment(niyam_repo: Path) -> None:
    """Should ensure allowed_files enforce boundaries strictly (Any is not bypass) and prompt has contract details."""
    os.chdir(niyam_repo)
    console = Console(quiet=True)

    # Commit initial state so checkout works
    os.system("git add . && git commit -m 'Setup'")

    # 1. Plan a mission with allowed_files = ["src/*.py"] and acceptance criteria
    req_file = niyam_repo / "requirements.md"
    req_file.write_text("# Implement Authentication\n", encoding="utf-8")

    # Let's run a custom template plan with allowed_files and acceptance_criteria
    niyam_dir = get_niyam_dir(niyam_repo)
    run_dir = niyam_dir / "runs"

    # We will invoke run_mission_plan, then modify the generated mission plan directly
    # to set allowed_files = ["src/*.py"] and acceptance_criteria
    mission_id = run_mission_plan(str(req_file), console=console)

    plan_path = niyam_dir / "runs" / mission_id / "mission-plan.yaml"
    with open(plan_path) as f:
        plan_data = yaml.safe_load(f)

    # Modify T1 to require writes_files: True, allowed_files: ["src/*.py"], and acceptance_criteria
    t1 = plan_data["tasks"][0]
    t1["writes_files"] = True
    t1["allowed_files"] = ["src/*.py"]
    t1["acceptance_criteria"] = ["API response should be 200", "test file exists"]
    t1["validation"] = {"commands": ["echo 'custom validation'"]}

    with open(plan_path, "w") as f:
        yaml.dump(plan_data, f)

    run_mission_approve(console=console)

    # 2. Run mission start with mocked execution that writes to 'tests/test_auth.py' (violation!)
    import subprocess as sp

    real_run = sp.run

    def mock_subprocess_run(args, **kwargs):
        if args and args[0] == "git":
            return real_run(args, **kwargs)

        cwd = kwargs.get("cwd", niyam_repo)

        # Write to tests/test_auth.py (not in src/*.py, so should trigger violation!)
        wrong_file = Path(cwd) / "tests" / "test_auth.py"
        wrong_file.parent.mkdir(parents=True, exist_ok=True)
        wrong_file.write_text("class TestAuth: pass", encoding="utf-8")

        real_run(["git", "add", "tests/test_auth.py"], cwd=cwd)

        res = MagicMock()
        res.returncode = 0
        return res

    with (
        patch("shutil.which", return_value="/usr/local/bin/claude"),
        patch("subprocess.run", side_effect=mock_subprocess_run),
    ):
        try:
            with pytest.raises(SystemExit) as excinfo:
                run_mission_start(console=console, worktree=False)
            assert excinfo.value.code == 1
        except Exception:
            pass

    # 3. Assert task failed due to boundary violation (Any did not bypass it)
    run_dir = niyam_dir / "runs" / mission_id
    plan = load_plan(run_dir)
    assert plan["tasks"][0]["status"] == "failed"

    # Verify that the enriched prompt was written and contains contract details
    prompt_path = run_dir / "task-T1-prompt.md"
    assert prompt_path.exists()
    prompt_text = prompt_path.read_text(encoding="utf-8")
    assert "TASK CONTRACT" in prompt_text
    assert "Allowed files: ['src/*.py']" in prompt_text
    assert "Acceptance criteria:" in prompt_text
    assert "API response should be 200" in prompt_text
    assert "echo 'custom validation'" in prompt_text
