"""Tests for the niyam scan capability."""

from __future__ import annotations

import json
from pathlib import Path
from typer.testing import CliRunner

from niyam.cli import app
from niyam.core.scan import run_scanner_checks

def test_scan_empty_folder(tmp_path: Path) -> None:
    """Scanning an empty folder should succeed but return a lower readiness score."""
    # Run the checks on the empty folder under enterprise profile for higher strictness
    results = run_scanner_checks(tmp_path, profile="enterprise")
    
    assert results is not None
    assert "score" in results
    assert "findings" in results
    assert "decision" in results
    assert results["score"] < 100
    assert results["decision"] in ("HIGH_RISK", "NO_GO", "CONDITIONAL_GO")
    
    # We should have findings about missing docs, tests, lockfiles, etc.
    categories = {f["category"] for f in results["findings"]}
    assert "docs" in categories
    assert "tests" in categories

def test_scan_sample_app_with_env(tmp_path: Path) -> None:
    """Scanning an app with .env and secrets should yield critical/high findings."""
    # Write a tracked .env file
    env_file = tmp_path / ".env"
    env_file.write_text("DATABASE_URL=postgres://user:password@localhost/db\nAPI_KEY=sk-proj-123456789\n")
    
    # Also write a readme to avoid other checks failing
    readme = tmp_path / "README.md"
    readme.write_text("# Test App\n")
    
    results = run_scanner_checks(tmp_path, profile="startup")
    
    # We should detect secrets exposure
    secret_findings = [f for f in results["findings"] if f["category"] == "secrets"]
    assert len(secret_findings) > 0
    assert any(".env" in f["file_path"] or "secrets" in f["category"] for f in secret_findings)
    # The severity should be critical
    assert any(f["severity"] == "critical" for f in secret_findings)


def test_scan_sample_app_with_package_json(tmp_path: Path) -> None:
    """Scanning an app with package.json but missing lockfile should flag dependencies."""
    package_json = tmp_path / "package.json"
    package_json.write_text('{"dependencies": {"lodash": "^4.17.21"}}')
    
    readme = tmp_path / "README.md"
    readme.write_text("# Test App\n")
    
    # Run check under enterprise profile (stricter)
    results = run_scanner_checks(tmp_path, profile="enterprise")
    
    dep_findings = [f for f in results["findings"] if f["category"] == "dependencies"]
    assert len(dep_findings) > 0
    assert any("lockfile" in f["description"].lower() for f in dep_findings)
    assert any(f["severity"] == "high" for f in dep_findings)

def test_scan_cli_json_report(tmp_path: Path) -> None:
    """The scan command should generate valid JSON output."""
    runner = CliRunner()
    
    # Scan an empty folder and output as json
    result = runner.invoke(app, ["scan", str(tmp_path), "--output", "json"])
    assert result.exit_code == 0
    
    data = json.loads(result.stdout)
    assert "score" in data
    assert "decision" in data
    assert "findings" in data

def test_scan_cli_markdown_report(tmp_path: Path) -> None:
    """The scan command should generate a markdown report when requested."""
    runner = CliRunner()
    report_file = tmp_path / "niyam-readiness.md"
    
    result = runner.invoke(app, ["scan", str(tmp_path), "--output", "markdown", "--report-file", str(report_file)])
    assert result.exit_code == 0
    assert report_file.exists()
    
    content = report_file.read_text(encoding="utf-8")
    assert "# Niyam Production Readiness Report" in content
    assert "Readiness Score:" in content
    assert "Decision:" in content
