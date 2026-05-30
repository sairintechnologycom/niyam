"""Tests for Sutra CI/CD and non-interactive execution."""

from __future__ import annotations

import os
import json
from pathlib import Path
import pytest
from rich.console import Console

from sutra.core.config import get_sutra_dir
from sutra.mission.planner import run_mission_plan
from sutra.mission.executor import run_mission_start, load_plan


def test_non_interactive_fails_unapproved(sutra_repo: Path) -> None:
    """Should fail with SystemExit if not approved and running headlessly/non-interactively."""
    os.chdir(sutra_repo)
    console = Console(quiet=True)

    req_file = sutra_repo / "requirements.md"
    req_file.write_text("# Test requirement\n", encoding="utf-8")
    mission_id = run_mission_plan(str(req_file), console=console)

    # approval.json should indicate unapproved
    run_dir = get_sutra_dir(sutra_repo) / "runs" / mission_id
    with pytest.raises(SystemExit) as excinfo:
        run_mission_start(console=console, non_interactive=True)
    assert excinfo.value.code == 1

    # Verify still unapproved
    with open(run_dir / "approval.json", encoding="utf-8") as f:
        app_data = json.load(f)
    assert not app_data.get("approved")


def test_non_interactive_auto_approve(sutra_repo: Path) -> None:
    """Should auto-approve if non-interactive and SUTRA_CI_AUTO_APPROVE=1 is set."""
    os.chdir(sutra_repo)
    console = Console(quiet=True)

    req_file = sutra_repo / "requirements.md"
    req_file.write_text("# Test requirement\n", encoding="utf-8")
    mission_id = run_mission_plan(str(req_file), console=console)

    os.environ["SUTRA_TEST"] = "1"
    os.environ["SUTRA_CI_AUTO_APPROVE"] = "1"
    try:
        run_mission_start(console=console, non_interactive=True)
    finally:
        del os.environ["SUTRA_TEST"]
        del os.environ["SUTRA_CI_AUTO_APPROVE"]

    # Verify it became approved and completed
    run_dir = get_sutra_dir(sutra_repo) / "runs" / mission_id
    with open(run_dir / "approval.json", encoding="utf-8") as f:
        app_data = json.load(f)
    assert app_data.get("approved")

    plan = load_plan(run_dir)
    assert plan["mission"]["status"] == "completed"


def test_remote_policy_fetching(sutra_repo: Path) -> None:
    """Should fetch policy from remote URL if configured."""
    os.chdir(sutra_repo)
    sutra_dir = get_sutra_dir(sutra_repo)

    # Enable remote policy in config
    sutra_yaml_path = sutra_dir / "sutra.yaml"
    sutra_yaml_path.write_text(
        "version: 0.1.0\n"
        "project_name: sutra\n"
        "guard:\n"
        "  enabled: true\n"
        "  remote_policy_url: 'https://mock-server.com/policies/'\n",
        encoding="utf-8",
    )

    mock_yaml_content = b"deny_write_patterns:\n  - 'src/restricted/*'\nallow_write_patterns:\n  - 'src/*'\n"

    from unittest.mock import patch, MagicMock

    mock_response = MagicMock()
    mock_response.__enter__.return_value = mock_response
    mock_response.read.return_value = mock_yaml_content

    with patch("urllib.request.urlopen", return_value=mock_response) as mock_urlopen:
        from sutra.policies.guard import load_security_policy

        policy = load_security_policy(sutra_repo)

        # Verify URL called
        mock_urlopen.assert_called_once()
        assert (
            "https://mock-server.com/policies/security.yaml"
            in mock_urlopen.call_args[0][0].full_url
        )

        # Verify content parsed correctly
        assert policy.get("deny_write_patterns") == ["src/restricted/*"]


def test_remote_policy_fallback(sutra_repo: Path) -> None:
    """Should fallback to local security.yaml file if remote request fails."""
    os.chdir(sutra_repo)
    sutra_dir = get_sutra_dir(sutra_repo)

    # Enable remote policy in config
    sutra_yaml_path = sutra_dir / "sutra.yaml"
    sutra_yaml_path.write_text(
        "version: 0.1.0\n"
        "project_name: sutra\n"
        "guard:\n"
        "  enabled: true\n"
        "  remote_policy_url: 'https://mock-server.com/policies/'\n",
        encoding="utf-8",
    )

    # Write local security.yaml file
    local_security_path = sutra_dir / "policies" / "security.yaml"
    local_security_path.write_text(
        "deny_write_patterns:\n  - 'local/restricted/*'\n", encoding="utf-8"
    )

    from unittest.mock import patch

    with patch("urllib.request.urlopen", side_effect=Exception("Connection refused")):
        from sutra.policies.guard import load_security_policy

        policy = load_security_policy(sutra_repo)

        # Verify fallback content loaded
        assert policy.get("deny_write_patterns") == ["local/restricted/*"]


def test_ci_verify_strict_missing_evidence(sutra_repo: Path) -> None:
    """Should fail CI verification in strict mode if evidence.md is missing."""
    os.chdir(sutra_repo)
    console = Console(quiet=True)

    from sutra.core.ci import run_ci_verify

    with pytest.raises(SystemExit) as excinfo:
        run_ci_verify(target_branch="main", strict=True, console=console)
    assert excinfo.value.code == 1


def test_ci_verify_non_strict_missing_evidence(sutra_repo: Path) -> None:
    """Should warn but pass CI verification in non-strict mode if evidence.md is missing."""
    os.chdir(sutra_repo)
    console = Console(quiet=True)

    from sutra.core.ci import run_ci_verify

    # Mocks to bypass other checks
    from unittest.mock import patch, MagicMock

    mock_run = MagicMock()
    mock_run.returncode = 0
    mock_run.stdout = ""

    with patch("subprocess.run", return_value=mock_run):
        # Should not raise SystemExit
        run_ci_verify(target_branch="main", strict=False, console=console)


def test_ci_verify_write_violation(sutra_repo: Path) -> None:
    """Should fail CI verification if git diff contains write restriction violations."""
    os.chdir(sutra_repo)
    sutra_dir = get_sutra_dir(sutra_repo)
    console = Console(quiet=True)

    # Create dummy evidence.md
    mission_id = "test-mission-123"
    run_dir = sutra_dir / "runs" / mission_id
    run_dir.mkdir(parents=True, exist_ok=True)

    # Save a plan
    plan_path = run_dir / "mission-plan.yaml"
    plan_path.write_text(
        "mission:\n  id: test-mission-123\n  status: completed\n  orchestrator: claude\ntasks: []\n",
        encoding="utf-8",
    )

    evidence_md = run_dir / "evidence.md"
    evidence_md.write_text(
        "# Sutra Mission Evidence Package - test-mission-123\n"
        "<!-- SUTRA_SIGNATURE_START\n"
        "{\n"
        '  "mission_id": "test-mission-123",\n'
        '  "timestamp": "2026-05-29T00:00:00Z",\n'
        '  "files": {}\n'
        "}\n"
        "SUTRA_SIGNATURE_END -->\n",
        encoding="utf-8",
    )

    # Write write restriction policy locally
    local_security_path = sutra_dir / "policies" / "security.yaml"
    local_security_path.write_text(
        "deny_write_patterns:\n  - 'protected/*'\n", encoding="utf-8"
    )

    from unittest.mock import patch, MagicMock

    # Mock git status to return the mission ID
    def mock_git(cmd, **kwargs):
        res = MagicMock()
        res.returncode = 0
        if "diff" in cmd:
            res.stdout = "protected/secrets.json\nsrc/app.py\n"
        elif "status" in cmd:
            res.stdout = ""
        else:
            res.stdout = ""
        return res

    from sutra.core.ci import run_ci_verify

    with (
        patch("subprocess.run", side_effect=mock_git),
        patch("sutra.mission.reporter.run_verify_report"),
    ):  # Bypass integrity check details
        with pytest.raises(SystemExit) as excinfo:
            run_ci_verify(target_branch="main", strict=True, console=console)
        assert excinfo.value.code == 1

        # Check that report is generated
        report_path = sutra_dir / "ci-report.json"
        assert report_path.exists()
        with open(report_path, encoding="utf-8") as f:
            report = json.load(f)
        assert report["policy_status"] == "failed"
        assert any(
            "protected/secrets.json" in failure for failure in report["failures"]
        )
