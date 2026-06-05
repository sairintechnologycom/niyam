"""Tests for Niyam scan baseline and risk acceptance support."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typer.testing import CliRunner

from niyam.cli import app
from niyam.core.scan import run_scanner_checks


def test_create_and_consume_baseline(tmp_path: Path) -> None:
    """Should create a baseline file from a risky app and consume it to suppress findings."""
    # 1. Create a risky app: write a .env file and a manifest but no lockfile
    env_file = tmp_path / ".env"
    env_file.write_text("API_KEY=sk-proj-1234567890123456\n")

    package_json = tmp_path / "package.json"
    package_json.write_text('{"dependencies": {"express": "*"}}')

    # Baseline output path
    baseline_file = tmp_path / "baseline.json"

    # 2. Run scan to create the baseline
    run_scanner_checks(tmp_path, profile="startup", create_baseline_path=baseline_file)

    # 3. Check baseline file exists and contains the schema keys
    assert baseline_file.exists()
    baseline_data = json.loads(baseline_file.read_text(encoding="utf-8"))
    assert baseline_data["schema_version"] == "1.0.0"
    assert "created_at" in baseline_data
    assert baseline_data["project"] == tmp_path.name
    assert len(baseline_data["accepted_findings"]) > 0

    # Ensure no secrets are present in the baseline file
    assert "sk-proj-123456789" not in baseline_file.read_text(encoding="utf-8")

    # 4. Re-scan consuming the baseline. Readiness score should be 100 because findings are accepted.
    results_with_baseline = run_scanner_checks(
        tmp_path, profile="startup", baseline_path=baseline_file
    )
    assert results_with_baseline["score"] == 100
    assert results_with_baseline["decision"] == "GO"
    for f in results_with_baseline["findings"]:
        assert f["status"] == "accepted_existing"


def test_new_finding_is_open(tmp_path: Path) -> None:
    """Should mark a new finding as open while baseline-suppressed findings are accepted_existing."""
    # Write a readme to create baseline first
    readme = tmp_path / "README.md"
    readme.write_text("# Old App")

    baseline_file = tmp_path / "baseline.json"
    run_scanner_checks(tmp_path, profile="startup", create_baseline_path=baseline_file)

    # Now add a new risky file (e.g. .env) that wasn't there before
    env_file = tmp_path / ".env"
    env_file.write_text("DB_PWD=secretpass\n")

    # Re-scan with baseline. The new env_file finding should be "open", while others are "accepted_existing"
    results = run_scanner_checks(
        tmp_path, profile="startup", baseline_path=baseline_file
    )

    env_findings = [f for f in results["findings"] if ".env" in f["file_path"]]
    assert len(env_findings) > 0
    assert any(f["status"] == "open" for f in env_findings)

    # The score should drop because of the new finding
    assert results["score"] < 100


def test_expired_baseline_item(tmp_path: Path) -> None:
    """Expired baseline item must revert to open status."""
    readme = tmp_path / "README.md"
    readme.write_text("# App")

    # Create baseline
    baseline_file = tmp_path / "baseline.json"
    run_scanner_checks(tmp_path, profile="startup", create_baseline_path=baseline_file)

    # Load baseline and manually set an expired date on the findings
    data = json.loads(baseline_file.read_text(encoding="utf-8"))
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    for entry in data["accepted_findings"]:
        entry["expires_at"] = yesterday

    baseline_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    # Re-scan. The findings should be "open" because the baseline items are expired
    results = run_scanner_checks(
        tmp_path, profile="startup", baseline_path=baseline_file
    )
    for f in results["findings"]:
        # Since they are expired, they must be marked as open
        assert f["status"] == "open"


def test_critical_new_finding_fails(tmp_path: Path) -> None:
    """A critical new finding must still cause scan to fail under fail-on options."""
    baseline_file = tmp_path / "baseline.json"
    # Create baseline empty
    run_scanner_checks(tmp_path, profile="startup", create_baseline_path=baseline_file)

    # Now create a new critical finding (.env with secrets)
    env_file = tmp_path / ".env"
    env_file.write_text("AWS_KEY=AWS_KEY=AKIA1234567890123456\n")

    runner = CliRunner()
    # Execute scan. Should exit with code 2 because of the new critical finding (fail-on critical)
    result = runner.invoke(
        app,
        [
            "scan",
            str(tmp_path),
            "--baseline",
            str(baseline_file),
            "--fail-on",
            "critical",
        ],
    )
    assert result.exit_code == 2
    assert "Scan failed" in result.stderr
