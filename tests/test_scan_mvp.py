"""Unit tests for Niyam scan MVP capabilities introduced in Phase 1C."""

from __future__ import annotations

import json
from pathlib import Path
from typer.testing import CliRunner

from niyam.cli import app
from niyam.core.scan import run_scanner_checks


def test_scan_clean_app(tmp_path: Path) -> None:
    """A clean app with readme, tests, lockfile and no secrets should pass cleanly."""
    # Create required files
    (tmp_path / "README.md").write_text(
        "# Clean App\nThis is a production-ready application."
    )
    (tmp_path / "uv.lock").write_text("# lockfile\n")
    (tmp_path / ".gitignore").write_text("node_modules/\n")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_main.py").write_text(
        "def test_dummy():\n    assert True\n"
    )

    results = run_scanner_checks(tmp_path, profile="startup")

    assert results["score"] >= 85
    assert results["decision"] == "GO"
    assert len(results["findings"]) == 0 or not any(
        f["severity"] in ("critical", "high") for f in results["findings"]
    )


def test_scan_risky_app_env_no_go(tmp_path: Path) -> None:
    """A committed .env file with possible secrets must force a NO_GO decision."""
    (tmp_path / "README.md").write_text("# App\n")
    # Committed env file with secrets
    (tmp_path / ".env").write_text(
        "OPENAI_API_KEY=sk-proj-1234567890abcdef1234567890abcdef\n"
    )

    results = run_scanner_checks(tmp_path, profile="startup")

    assert results["decision"] == "NO_GO"
    assert results["score"] <= 49
    assert "Hard blocker triggered" in results["decision_reason"]
    assert "environment" in results["decision_reason"].lower()


def test_scan_obvious_private_key_no_go(tmp_path: Path) -> None:
    """An obvious private key block in code must force a NO_GO decision."""
    (tmp_path / "README.md").write_text("# App\n")
    # File containing obvious private key
    (tmp_path / "key.pem").write_text(
        "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA...\n-----END RSA PRIVATE KEY-----"
    )

    results = run_scanner_checks(tmp_path, profile="startup")

    assert results["decision"] == "NO_GO"
    assert results["score"] <= 49
    assert "Hard blocker triggered" in results["decision_reason"]
    assert "private key" in results["decision_reason"].lower()


def test_scan_public_cloud_no_go(tmp_path: Path) -> None:
    """Committed public cloud exposure patterns must force a NO_GO decision."""
    (tmp_path / "README.md").write_text("# App\n")
    # Committed AWS key ID
    (tmp_path / "config.json").write_text('{"aws_key": "AKIAIOSFODNN7EXAMPLE"}')

    results = run_scanner_checks(tmp_path, profile="startup")

    assert results["decision"] == "NO_GO"
    assert results["score"] <= 49
    assert "Hard blocker triggered" in results["decision_reason"]
    assert "public cloud" in results["decision_reason"].lower()


def test_scan_missing_readme(tmp_path: Path) -> None:
    """Missing README should register a documentation finding."""
    # Write a test and lockfile to isolate README missing
    (tmp_path / "uv.lock").write_text("# lockfile\n")

    results = run_scanner_checks(tmp_path, profile="startup")

    findings = results["findings"]
    readme_findings = [
        f for f in findings if f["category"] == "docs" or f["id"] == "DOC001"
    ]
    assert len(readme_findings) > 0
    assert readme_findings[0]["schema_version"] == "1.0.0"
    assert readme_findings[0]["confidence"] == "high"


def test_scan_missing_tests(tmp_path: Path) -> None:
    """Missing test suite should register a tests finding."""
    (tmp_path / "README.md").write_text("# App\n")

    results = run_scanner_checks(tmp_path, profile="startup")

    findings = results["findings"]
    test_findings = [
        f for f in findings if f["category"] == "tests" or f["id"] == "TST001"
    ]
    assert len(test_findings) > 0


def test_scan_ai_risk_placeholder(tmp_path: Path) -> None:
    """AI stubs or commented assertions must be detected."""
    (tmp_path / "README.md").write_text("# App\n")
    # Commented out assertion
    (tmp_path / "app.py").write_text(
        "def run():\n    # assert False\n    pass # TODO\n"
    )

    results = run_scanner_checks(tmp_path, profile="startup")

    findings = results["findings"]
    ai_findings = [
        f
        for f in findings
        if f["category"] == "ai_risk" or f["id"] in ("AI001", "AI002")
    ]
    assert len(ai_findings) > 0
    # Check that line number detection works (line 2 for assert, line 3 for todo)
    assert any(f["line_number"] in (2, 3) for f in ai_findings)


def test_scan_cli_fail_on(tmp_path: Path) -> None:
    """CLI must fail (exit code 2) when severity threshold is exceeded."""
    runner = CliRunner()

    # Create missing README & lockfiles (medium/info findings)
    # Scan with fail-on medium should exit with code 2
    result = runner.invoke(app, ["scan", str(tmp_path), "--fail-on", "medium"])
    assert result.exit_code == 2
    assert "Scan failed" in result.output

    # Scan with fail-on critical should exit with code 0 (since there are no critical findings)
    result_crit = runner.invoke(app, ["scan", str(tmp_path), "--fail-on", "critical"])
    # Wait, in the empty directory scan, is there a NO_GO decision?
    # Empty dir scan score is 100 - (deductions for missing docs/tests/lockfile/gitignore/cicd)
    # Deductions: docs(0) + tests(3) + dependencies(8) + env_config(8) + cicd(0) + health(0) = 19.
    # Score: 81 (CONDITIONAL_GO).
    # Since decision is CONDITIONAL_GO, and no critical findings exist, exit code should be 0.
    assert result_crit.exit_code == 0


def test_scan_cli_redacted_outputs(tmp_path: Path) -> None:
    """CLI outputs (text/json/markdown) must redact secrets completely."""
    runner = CliRunner()

    # Create a workspace directory whose name contains a secret to ensure it gets printed
    # Named directly starting with the secret prefix to ensure word boundary matches
    secret_workspace = tmp_path / "sk-proj-1234567890abcdef1234567890abcdef"
    secret_workspace.mkdir()

    (secret_workspace / "README.md").write_text("# App\n")
    (secret_workspace / ".gitignore").write_text("node_modules/\n")
    # Committed env file containing sensitive key
    (secret_workspace / ".env").write_text(
        "OPENAI_KEY=sk-proj-1234567890abcdef1234567890abcdef\n"
    )

    # 1. Text output
    result_text = runner.invoke(app, ["scan", str(secret_workspace)])
    # The exit code should be 2 because .env with secrets forces NO_GO
    assert result_text.exit_code == 2
    assert "sk-proj-123456" not in result_text.output
    assert "[REDACTED_SECRET]" in result_text.output

    # 2. JSON output
    result_json = runner.invoke(
        app, ["scan", str(secret_workspace), "--output", "json"]
    )
    assert result_json.exit_code == 2
    assert "sk-proj-123456" not in result_json.output
    data = json.loads(result_json.stdout)
    assert data["redaction_status"]["redacted"] is True
    # The secret must be masked in findings and paths
    assert "[REDACTED_SECRET]" in data["project_path"]
    for f in data["findings"]:
        assert "sk-proj-" not in f["description"]
        assert "sk-proj-" not in f["recommendation"]
