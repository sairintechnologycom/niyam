"""Tests for Niyam CI/CD scan gate behavior, exit codes, and artifacts."""

from __future__ import annotations

from pathlib import Path
from typer.testing import CliRunner

from niyam.cli import app


def test_fail_on_critical_with_critical_finding(tmp_path: Path) -> None:
    """Scan exits with code 2 when a critical finding is found and --fail-on critical is set."""
    # Write a tracked .env file to trigger critical secrets leak
    env_file = tmp_path / ".env"
    env_file.write_text("API_KEY=sk-proj-1234567890123456\n")

    # Add README to satisfy other checks
    readme = tmp_path / "README.md"
    readme.write_text("# Test App\n")

    runner = CliRunner()
    result = runner.invoke(
        app, ["scan", str(tmp_path), "--profile", "startup", "--fail-on", "critical"]
    )
    assert result.exit_code == 2
    assert "Scan failed" in result.stderr
    assert "CRITICAL:" in result.stderr


def test_fail_on_high_with_high_finding(tmp_path: Path) -> None:
    """Scan exits with code 2 when a high finding is found and --fail-on high is set."""
    # Write a package.json to trigger missing lockfile check (high in enterprise)
    package_json = tmp_path / "package.json"
    package_json.write_text('{"dependencies": {"express": "*"}}')

    readme = tmp_path / "README.md"
    readme.write_text("# Test App\n")

    runner = CliRunner()
    result = runner.invoke(
        app, ["scan", str(tmp_path), "--profile", "enterprise", "--fail-on", "high"]
    )
    assert result.exit_code == 2
    assert "Scan failed" in result.stderr
    assert "HIGH:" in result.stderr


def test_no_blocking_findings_exits_0(tmp_path: Path) -> None:
    """Scan exits with code 0 when there are no findings exceeding the threshold."""
    readme = tmp_path / "README.md"
    readme.write_text("# Clean App\n")

    runner = CliRunner()
    result = runner.invoke(
        app, ["scan", str(tmp_path), "--profile", "startup", "--fail-on", "critical"]
    )
    assert result.exit_code == 0
    assert "Scan Findings Summary by Severity" in result.stdout


def test_invalid_rule_exits_3(tmp_path: Path) -> None:
    """Scan exits with code 3 when configuration or rules are invalid."""
    bad_rule_file = tmp_path / "bad-rule.yaml"
    bad_rule_file.write_text("""
rules:
  - id: BAD001
    title: Bad Rule
    # Missing required keys like category, severity, match, etc.
""")
    runner = CliRunner()
    result = runner.invoke(app, ["scan", str(tmp_path), "--rules", str(bad_rule_file)])
    assert result.exit_code == 3
    assert "Configuration Error" in result.stdout


def test_scan_permission_error_exits_5(tmp_path: Path, monkeypatch) -> None:
    """Scan exits with code 5 when it encounters a file permission/access error."""
    import niyam.governance.scan.command

    def mock_execute_scan(*args, **kwargs):
        raise PermissionError("Access denied")

    monkeypatch.setattr(
        niyam.governance.scan.command, "execute_scan", mock_execute_scan
    )

    runner = CliRunner()
    result = runner.invoke(app, ["scan", str(tmp_path)])
    assert result.exit_code == 5
    assert "Permission/Access Error" in result.stdout


def test_artifacts_created(tmp_path: Path) -> None:
    """Scan successfully creates JSON, Markdown, and SARIF output reports."""
    readme = tmp_path / "README.md"
    readme.write_text("# Test App\n")

    json_report = tmp_path / "report.json"
    md_report = tmp_path / "report.md"
    sarif_report = tmp_path / "report.sarif"

    runner = CliRunner()

    # 1. JSON report
    result_json = runner.invoke(
        app,
        ["scan", str(tmp_path), "--output", "json", "--report-file", str(json_report)],
    )
    assert result_json.exit_code == 0
    assert json_report.exists()
    assert "findings" in json_report.read_text(encoding="utf-8")

    # 2. Markdown report
    result_md = runner.invoke(
        app,
        [
            "scan",
            str(tmp_path),
            "--output",
            "markdown",
            "--report-file",
            str(md_report),
        ],
    )
    assert result_md.exit_code == 0
    assert md_report.exists()
    assert "# Niyam Production Readiness Report" in md_report.read_text(
        encoding="utf-8"
    )

    # 3. SARIF report
    result_sarif = runner.invoke(
        app,
        [
            "scan",
            str(tmp_path),
            "--output",
            "sarif",
            "--report-file",
            str(sarif_report),
        ],
    )
    assert result_sarif.exit_code == 0
    assert sarif_report.exists()
    sarif_content = sarif_report.read_text(encoding="utf-8")
    assert "$schema" in sarif_content
    assert "sarif" in sarif_content.lower()
