"""E2E tests for niyam scan commands."""

from __future__ import annotations

import json
from pathlib import Path


def test_clean_app_scan(clean_workspace: Path, run_cli) -> None:
    """Clean app scans with acceptable score (>= 85, decision GO or CONDITIONAL_GO)."""
    # 1. Initialize Niyam in the workspace
    init_res = run_cli(["niyam", "init", "--profile", "fullstack"], cwd=clean_workspace)
    assert init_res.returncode == 0

    # 2. Run the scan
    scan_res = run_cli(["niyam", "scan"], cwd=clean_workspace)
    assert scan_res.returncode == 0
    assert "Readiness Score:" in scan_res.stdout
    assert "Decision:" in scan_res.stdout

    # Run scan with json output to check values programmatically
    json_res = run_cli(["niyam", "scan", "--output", "json"], cwd=clean_workspace)
    assert json_res.returncode == 0

    results = json.loads(json_res.stdout)
    assert results["score"] >= 85
    assert results["decision"] in ("GO", "CONDITIONAL_GO")
    assert not any(f["severity"] == "critical" for f in results["findings"])


def test_risky_app_scan(risky_workspace: Path, run_cli) -> None:
    """Risky app scans with critical/high findings, producing NO_GO or HIGH_RISK."""
    # 1. Initialize Niyam
    init_res = run_cli(["niyam", "init", "--profile", "fullstack"], cwd=risky_workspace)
    assert init_res.returncode == 0

    # 2. Run scan with json output to inspect details
    json_res = run_cli(["niyam", "scan", "--output", "json"], cwd=risky_workspace)

    # Since risky_app has critical findings, it might exit with code 2 if NO_GO,
    # let's assert the decision is NO_GO or HIGH_RISK.
    results = json.loads(json_res.stdout)
    assert results["decision"] in ("NO_GO", "HIGH_RISK")

    findings = results["findings"]
    finding_ids = {f["id"] for f in findings}

    # SEC001 flags .env files, SEC002 flags hardcoded secrets
    assert "SEC001" in finding_ids
    assert "SEC002" in finding_ids

    # Ensure there's a critical finding
    criticals = [f for f in findings if f["severity"] == "critical"]
    assert len(criticals) > 0


def test_scan_report_generation(clean_workspace: Path, run_cli) -> None:
    """JSON and Markdown scan reports are successfully generated to files."""
    init_res = run_cli(["niyam", "init", "--profile", "fullstack"], cwd=clean_workspace)
    assert init_res.returncode == 0

    report_json = clean_workspace / "scan-report.json"
    report_md = clean_workspace / "scan-report.md"

    # 1. Generate JSON report
    json_res = run_cli(
        ["niyam", "scan", "--output", "json", "--report-file", str(report_json)],
        cwd=clean_workspace,
    )
    assert json_res.returncode == 0
    assert report_json.exists()

    # Load and parse json to verify it's valid
    with open(report_json, encoding="utf-8") as f:
        data = json.load(f)
    assert "score" in data
    assert "findings" in data

    # 2. Generate Markdown report
    md_res = run_cli(
        ["niyam", "scan", "--output", "markdown", "--report-file", str(report_md)],
        cwd=clean_workspace,
    )
    assert md_res.returncode == 0
    assert report_md.exists()

    # Verify markdown content
    md_content = report_md.read_text(encoding="utf-8")
    assert "# Niyam Production Readiness Report" in md_content
    assert "Scan Profile:" in md_content
    assert "Readiness Score:" in md_content
