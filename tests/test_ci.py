"""Tests for Niyam CI/CD and non-interactive execution."""

from __future__ import annotations

import os
import json
from pathlib import Path
import pytest
from rich.console import Console
from typer.testing import CliRunner

from niyam.core.config import get_niyam_dir
from niyam.mission.planner import run_mission_plan
from niyam.mission.executor import run_mission_start, load_plan
from niyam.cli import app

runner = CliRunner()


def test_non_interactive_fails_unapproved(niyam_repo: Path) -> None:
    """Should fail with SystemExit if not approved and running headlessly/non-interactively."""
    os.chdir(niyam_repo)
    console = Console(quiet=True)

    req_file = niyam_repo / "requirements.md"
    req_file.write_text("# Test requirement\n", encoding="utf-8")
    mission_id = run_mission_plan(str(req_file), console=console)

    # approval.json should indicate unapproved
    run_dir = get_niyam_dir(niyam_repo) / "runs" / mission_id
    with pytest.raises(SystemExit) as excinfo:
        run_mission_start(console=console, non_interactive=True)
    assert excinfo.value.code == 1

    # Verify still unapproved
    with open(run_dir / "approval.json", encoding="utf-8") as f:
        app_data = json.load(f)
    assert not app_data.get("approved")


def test_non_interactive_auto_approve(niyam_repo: Path) -> None:
    """Should auto-approve if non-interactive and NIYAM_CI_AUTO_APPROVE=1 is set."""
    os.chdir(niyam_repo)
    console = Console(quiet=True)

    req_file = niyam_repo / "requirements.md"
    req_file.write_text("# Test requirement\n", encoding="utf-8")
    mission_id = run_mission_plan(str(req_file), console=console)

    os.environ["NIYAM_TEST"] = "1"
    os.environ["NIYAM_CI_AUTO_APPROVE"] = "1"
    try:
        run_mission_start(console=console, non_interactive=True)
    finally:
        if "NIYAM_TEST" in os.environ:
            del os.environ["NIYAM_TEST"]
        if "NIYAM_CI_AUTO_APPROVE" in os.environ:
            del os.environ["NIYAM_CI_AUTO_APPROVE"]

    # Verify it became approved and completed
    run_dir = get_niyam_dir(niyam_repo) / "runs" / mission_id
    with open(run_dir / "approval.json", encoding="utf-8") as f:
        app_data = json.load(f)
    assert app_data.get("approved")

    plan = load_plan(run_dir)
    assert plan["mission"]["status"] == "completed"


def test_remote_policy_fetching(niyam_repo: Path) -> None:
    """Should fetch policy from remote URL if configured."""
    os.chdir(niyam_repo)
    niyam_dir = get_niyam_dir(niyam_repo)

    # Enable remote policy in config
    niyam_yaml_path = niyam_dir / "niyam.yaml"
    niyam_yaml_path.write_text(
        "version: 0.1.0\n"
        "project_name: niyam\n"
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
        from niyam.policies.guard import load_security_policy

        policy = load_security_policy(niyam_repo)

        # Verify URL called
        mock_urlopen.assert_called_once()
        assert (
            "https://mock-server.com/policies/security.yaml"
            in mock_urlopen.call_args[0][0].full_url
        )

        # Verify content parsed correctly
        assert policy.get("deny_write_patterns") == ["src/restricted/*"]


def test_remote_policy_fallback(niyam_repo: Path) -> None:
    """Should fallback to local security.yaml file if remote request fails."""
    os.chdir(niyam_repo)
    niyam_dir = get_niyam_dir(niyam_repo)

    # Enable remote policy in config
    niyam_yaml_path = niyam_dir / "niyam.yaml"
    niyam_yaml_path.write_text(
        "version: 0.1.0\n"
        "project_name: niyam\n"
        "guard:\n"
        "  enabled: true\n"
        "  remote_policy_url: 'https://mock-server.com/policies/'\n",
        encoding="utf-8",
    )

    # Write local security.yaml file
    local_security_path = niyam_dir / "policies" / "security.yaml"
    local_security_path.write_text(
        "deny_write_patterns:\n  - 'local/restricted/*'\n", encoding="utf-8"
    )

    from unittest.mock import patch

    with patch("urllib.request.urlopen", side_effect=Exception("Connection refused")):
        from niyam.policies.guard import load_security_policy

        policy = load_security_policy(niyam_repo)

        # Verify fallback content loaded
        assert policy.get("deny_write_patterns") == ["local/restricted/*"]


def test_ci_verify_strict_missing_evidence(niyam_repo: Path) -> None:
    """Should fail CI verification in strict mode if evidence.md is missing."""
    os.chdir(niyam_repo)
    console = Console(quiet=True)

    from niyam.core.ci import run_ci_verify

    with pytest.raises(SystemExit) as excinfo:
        run_ci_verify(target_branch="main", strict=True, console=console)
    assert excinfo.value.code == 1


def test_ci_verify_uses_workspace_scan_report(niyam_repo: Path) -> None:
    """CI verify should load .niyam/scan-report.json when no mission scan exists."""
    os.chdir(niyam_repo)
    niyam_dir = get_niyam_dir(niyam_repo)
    console = Console(quiet=True)

    # Passing readiness score at workspace level (no mission-scoped scan)
    scan_payload = {
        "score": 82,
        "readiness_score": 82,
        "decision": "GO",
        "findings": [],
    }
    (niyam_dir / "scan-report.json").write_text(
        json.dumps(scan_payload), encoding="utf-8"
    )

    # Minimal evidence so integrity does not hard-fail before governance
    mission_id = "ci-scan-link"
    run_dir = niyam_dir / "runs" / mission_id
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "mission-plan.yaml").write_text(
        "mission:\n  id: ci-scan-link\n  status: completed\n  orchestrator: claude\ntasks: []\n",
        encoding="utf-8",
    )
    (run_dir / "evidence.md").write_text(
        "# Niyam Mission Evidence Package - ci-scan-link\n"
        "<!-- NIYAM_SIGNATURE_START\n"
        "{\n"
        '  "mission_id": "ci-scan-link",\n'
        '  "timestamp": "2026-07-14T00:00:00Z",\n'
        '  "files": {}\n'
        "}\n"
        "NIYAM_SIGNATURE_END -->\n",
        encoding="utf-8",
    )
    (run_dir / "evidence.json").write_text(
        json.dumps({"readiness_score": None, "decision": None}), encoding="utf-8"
    )

    from unittest.mock import MagicMock, patch

    from niyam.core.ci import run_ci_verify

    mock_run = MagicMock()
    mock_run.returncode = 0
    mock_run.stdout = ""
    mock_cfg = MagicMock()
    mock_cfg.validation = None  # skip lint/test suite for this unit

    with (
        patch("subprocess.run", return_value=mock_run),
        patch("niyam.core.ci.run_verify_report"),
        patch("niyam.core.ci.load_project_config", return_value=mock_cfg),
    ):
        # Should not raise — governance score comes from workspace scan
        run_ci_verify(target_branch="main", strict=True, min_score=50, console=console)

    report_path = niyam_dir / "ci-report.json"
    assert report_path.exists()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["governance_status"] == "passed"


def test_ci_verify_strict_rejects_scan_without_score(niyam_repo: Path) -> None:
    """Strict CI must not pass when a scan artifact has no score."""
    os.chdir(niyam_repo)
    niyam_dir = get_niyam_dir(niyam_repo)
    (niyam_dir / "scan-report.json").write_text(
        json.dumps({"decision": "GO", "findings": []}), encoding="utf-8"
    )

    from unittest.mock import MagicMock, patch

    from niyam.core.ci import run_ci_verify

    mock_run = MagicMock(returncode=0, stdout="")
    mock_cfg = MagicMock(validation=None)
    with (
        patch("subprocess.run", return_value=mock_run),
        patch("niyam.core.ci.load_project_config", return_value=mock_cfg),
        pytest.raises(SystemExit) as excinfo,
    ):
        run_ci_verify(target_branch="main", strict=True, console=Console(quiet=True))

    assert excinfo.value.code == 1
    report = json.loads((niyam_dir / "ci-report.json").read_text(encoding="utf-8"))
    assert report["governance_status"] == "failed"
    assert any("no readiness score" in failure for failure in report["failures"])


def test_ci_verify_treats_zero_as_a_real_score(niyam_repo: Path) -> None:
    """A zero readiness score must fail the threshold, not parse as missing."""
    os.chdir(niyam_repo)
    niyam_dir = get_niyam_dir(niyam_repo)
    (niyam_dir / "scan-report.json").write_text(
        json.dumps({"score": 0, "decision": "NO_GO"}), encoding="utf-8"
    )

    from niyam.core.ci import run_ci_verify

    with pytest.raises(SystemExit):
        run_ci_verify(target_branch="main", strict=True, console=Console(quiet=True))

    report = json.loads((niyam_dir / "ci-report.json").read_text(encoding="utf-8"))
    assert any("Readiness score 0" in failure for failure in report["failures"])


def test_ci_verify_strict_missing_scan_suggests_remediation(niyam_repo: Path) -> None:
    """Missing scan in strict mode should fail with actionable remediation text."""
    os.chdir(niyam_repo)
    console = Console(quiet=True)
    from io import StringIO
    from rich.console import Console as RichConsole

    from niyam.core.ci import run_ci_verify

    buf = StringIO()
    noisy = RichConsole(file=buf, force_terminal=False, width=120)

    with pytest.raises(SystemExit) as excinfo:
        run_ci_verify(target_branch="main", strict=True, console=noisy)
    assert excinfo.value.code == 1
    output = buf.getvalue()
    assert "No scan report found" in output or "scan report" in output.lower()
    assert "niyam scan" in output


def test_ci_verify_non_strict_missing_evidence(niyam_repo: Path) -> None:
    """Should warn but pass CI verification in non-strict mode if evidence.md is missing."""
    os.chdir(niyam_repo)
    console = Console(quiet=True)

    from niyam.core.ci import run_ci_verify

    # Mocks to bypass other checks
    from unittest.mock import patch, MagicMock

    mock_run = MagicMock()
    mock_run.returncode = 0
    mock_run.stdout = ""

    with patch("subprocess.run", return_value=mock_run):
        # Should not raise SystemExit
        run_ci_verify(target_branch="main", strict=False, console=console)


def test_ci_verify_does_not_verify_unsigned_workspace_evidence(
    niyam_repo: Path,
) -> None:
    """Governance evidence is not a signed mission integrity artifact."""
    os.chdir(niyam_repo)
    niyam_dir = get_niyam_dir(niyam_repo)
    (niyam_dir / "evidence.md").write_text(
        "# Unsigned governance evidence\n", encoding="utf-8"
    )

    from unittest.mock import MagicMock, patch

    from niyam.core.ci import run_ci_verify

    mock_run = MagicMock(returncode=0, stdout="")
    with (
        patch("subprocess.run", return_value=mock_run),
        patch("niyam.core.ci.run_verify_report") as verify,
    ):
        run_ci_verify(target_branch="main", strict=False, console=Console(quiet=True))

    verify.assert_not_called()


def test_ci_verify_write_violation(niyam_repo: Path) -> None:
    """Should fail CI verification if git diff contains write restriction violations."""
    os.chdir(niyam_repo)
    niyam_dir = get_niyam_dir(niyam_repo)
    console = Console(quiet=True)

    # Create dummy evidence.md
    mission_id = "test-mission-123"
    run_dir = niyam_dir / "runs" / mission_id
    run_dir.mkdir(parents=True, exist_ok=True)

    # Save a plan
    plan_path = run_dir / "mission-plan.yaml"
    plan_path.write_text(
        "mission:\n  id: test-mission-123\n  status: completed\n  orchestrator: claude\ntasks: []\n",
        encoding="utf-8",
    )

    evidence_md = run_dir / "evidence.md"
    evidence_md.write_text(
        "# Niyam Mission Evidence Package - test-mission-123\n"
        "<!-- NIYAM_SIGNATURE_START\n"
        "{\n"
        '  "mission_id": "test-mission-123",\n'
        '  "timestamp": "2026-05-29T00:00:00Z",\n'
        '  "files": {}\n'
        "}\n"
        "NIYAM_SIGNATURE_END -->\n",
        encoding="utf-8",
    )

    # Write write restriction policy locally
    local_security_path = niyam_dir / "policies" / "security.yaml"
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

    from niyam.core.ci import run_ci_verify

    with (
        patch("subprocess.run", side_effect=mock_git),
        patch("niyam.mission.reporter.run_verify_report"),
    ):  # Bypass integrity check details
        with pytest.raises(SystemExit) as excinfo:
            run_ci_verify(target_branch="main", strict=True, console=console)
        assert excinfo.value.code == 1

        # Check that report is generated
        report_path = niyam_dir / "ci-report.json"
        assert report_path.exists()
        with open(report_path, encoding="utf-8") as f:
            report = json.load(f)
        assert report["policy_status"] == "failed"
        assert any(
            "protected/secrets.json" in failure for failure in report["failures"]
        )

def test_cli_ci_generate_github(niyam_repo: Path) -> None:
    """Should generate GitHub Actions template via CLI."""
    os.chdir(niyam_repo)
    result = runner.invoke(app, ["ci", "generate", "github"])
    
    assert result.exit_code == 0
    assert "Generated Hardened GitHub Actions workflow" in result.stdout
    assert (niyam_repo / ".github" / "workflows" / "niyam-verification.yml").exists()

def test_cli_ci_generate_azure(niyam_repo: Path) -> None:
    """Should generate Azure DevOps template via CLI."""
    os.chdir(niyam_repo)
    result = runner.invoke(app, ["ci", "generate", "azure"])
    
    assert result.exit_code == 0
    assert "Generated Hardened Azure DevOps pipeline" in result.stdout
    assert (niyam_repo / "azure-pipelines.yml").exists()

def test_cli_ci_generate_gitlab(niyam_repo: Path) -> None:
    """Should generate GitLab CI template via CLI."""
    os.chdir(niyam_repo)
    result = runner.invoke(app, ["ci", "generate", "gitlab"])
    
    assert result.exit_code == 0
    assert "Generated GitLab CI pipeline" in result.stdout
    assert (niyam_repo / ".gitlab-ci.yml").exists()
