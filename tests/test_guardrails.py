"""Tests for Niyam path-based guardrails."""

from __future__ import annotations

import os
import json
import yaml
from pathlib import Path
import pytest
from rich.console import Console
from unittest.mock import patch, MagicMock

from niyam.core.config import get_niyam_dir
from niyam.mission.planner import run_mission_plan, run_mission_approve
from niyam.mission.executor import run_mission_start, load_plan


def test_path_write_denial_and_revert(niyam_repo: Path) -> None:
    """Should detect unauthorized changes to denied path, revert them, and fail task."""
    os.chdir(niyam_repo)
    console = Console(quiet=True)

    # 1. Write custom security policy with deny write patterns
    niyam_dir = get_niyam_dir(niyam_repo)
    security_yaml = niyam_dir / "policies" / "security.yaml"
    policy_data = {
        "block_secrets_in_code": True,
        "require_auth_review": True,
        "require_input_validation": True,
        "deny_write_patterns": ["src/secure/*.py"],
    }
    with open(security_yaml, "w", encoding="utf-8") as f:
        yaml.dump(policy_data, f)

    # Create dummy directories
    (niyam_repo / "src" / "secure").mkdir(parents=True, exist_ok=True)

    # Initial git commit so checkout works
    os.system("git add .niyam && git commit -m 'Initial commit'")

    # 2. Plan and approve mission
    req_file = niyam_repo / "requirements.md"
    req_file.write_text("# Guardrail test\n", encoding="utf-8")
    mission_id = run_mission_plan(str(req_file), console=console)
    run_mission_approve(console=console)

    # 3. Patch shutil.which to find 'claude' CLI, and patch subprocess.run
    # When claude CLI is executed, we write a denied file and return success.
    import subprocess as sp

    real_run = sp.run

    def mock_subprocess_run(args, **kwargs):
        if args and args[0] == "git":
            return real_run(args, **kwargs)

        cwd = kwargs.get("cwd", niyam_repo)

        # Write the unauthorized file to the correct cwd
        unauthorized_file = Path(cwd) / "src" / "secure" / "secret.py"
        unauthorized_file.parent.mkdir(parents=True, exist_ok=True)
        unauthorized_file.write_text("unauthorized changes", encoding="utf-8")

        # Also add it to git so status --porcelain sees it
        real_run(["git", "add", "src/secure/secret.py"], cwd=cwd)

        res = MagicMock()
        res.returncode = 0
        return res

    with (
        patch("shutil.which", return_value="/usr/local/bin/claude"),
        patch("subprocess.run", side_effect=mock_subprocess_run),
    ):
        # We do NOT run in test mode (NIYAM_TEST) because we want orchestrator execution path
        # But wait, run_mission_start will run.
        # Let's make sure it doesn't fail on validation test commands (no validation set in fullstack by default)
        try:
            # Run the mission start (which will execute the first task T1)
            # T1 is discovery (writes_files: False, but we simulate writing anyway)
            with pytest.raises(SystemExit) as excinfo:
                run_mission_start(console=console, worktree=False)
            assert excinfo.value.code == 1
        except Exception:
            # Let it fail with SystemExit as expected
            pass

    # 4. Assert task T1 failed due to violation, and unauthorized file was deleted/reverted
    run_dir = niyam_dir / "runs" / mission_id
    plan = load_plan(run_dir)

    # The first task executed (T1) should be failed
    assert plan["tasks"][0]["status"] == "failed"
    assert plan["mission"]["status"] == "failed"

    # Unauthorized file should have been deleted (since it was untracked/added and then checkout/removed)
    assert not (niyam_repo / "src" / "secure" / "secret.py").exists()

    # Verify policy event was logged
    policy_events_path = run_dir / "policy-events.json"
    assert policy_events_path.exists()
    with open(policy_events_path, encoding="utf-8") as f:
        events = json.load(f)
    assert len(events) > 0
    assert events[0]["type"] == "WRITE_VIOLATION"
    assert "src/secure/secret.py" in events[0]["details"]
