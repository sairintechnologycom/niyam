"""Tests for Niyam evidence report generation capability."""

from __future__ import annotations

import json
from pathlib import Path
import pytest
from typer.testing import CliRunner

from niyam.cli import app
from niyam.core.evidence import run_generate_evidence


@pytest.fixture(autouse=True)
def setup_workspace(tmp_path: Path, monkeypatch) -> None:
    """Fixture to ensure tests run in a workspace relative to tmp_path."""
    monkeypatch.chdir(tmp_path)
    # Create mock .niyam directory to mock find_niyam_root
    niyam_dir = tmp_path / ".niyam"
    niyam_dir.mkdir(exist_ok=True)
    # Write empty config
    with open(niyam_dir / "niyam.yaml", "w") as f:
        f.write("version: 0.1.0\n")


@pytest.fixture
def sample_scan_json(tmp_path: Path) -> Path:
    """Create a mock niyam-scan.json file for testing."""
    scan_file = tmp_path / "niyam-scan.json"
    scan_file.write_text(
        json.dumps(
            {
                "profile": "team",
                "score": 75,
                "decision": "CONDITIONAL_GO",
                "findings": [
                    {
                        "id": "SEC001",
                        "title": "Unprotected Env File",
                        "category": "secrets",
                        "severity": "critical",
                        "file_path": ".env",
                        "description": "Found active env file.",
                        "recommendation": "Remove it from repo.",
                    },
                    {
                        "id": "DOC001",
                        "title": "Missing Readme",
                        "category": "docs",
                        "severity": "low",
                        "file_path": "",
                        "description": "Readme is missing.",
                        "recommendation": "Create README.md.",
                    },
                ],
            }
        )
    )
    return scan_file


def test_generate_evidence_from_scan_json(sample_scan_json: Path) -> None:
    """Should correctly generate evidence when loading scan results from JSON."""
    report = run_generate_evidence(from_scan_json=str(sample_scan_json), fmt="markdown")

    assert "75/100" in report
    assert "CONDITIONAL GO" in report
    assert "SEC001" in report
    assert "DOC001" in report


def test_generate_markdown_and_html_reports(
    sample_scan_json: Path, tmp_path: Path
) -> None:
    """Should support both markdown and HTML generation and write to output path."""
    md_output = tmp_path / "report.md"
    html_output = tmp_path / "report.html"

    # Generate Markdown
    run_generate_evidence(
        from_scan_json=str(sample_scan_json), fmt="markdown", output=str(md_output)
    )
    assert md_output.exists()
    assert "# Niyam Governance" in md_output.read_text(encoding="utf-8")

    # Generate HTML
    run_generate_evidence(
        from_scan_json=str(sample_scan_json), fmt="html", output=str(html_output)
    )
    assert html_output.exists()
    assert "<!DOCTYPE html>" in html_output.read_text(encoding="utf-8")
    assert "75" in html_output.read_text(encoding="utf-8")


def test_generate_json_report(sample_scan_json: Path) -> None:
    """Should generate a JSON format representation containing metadata and findings."""
    report = run_generate_evidence(from_scan_json=str(sample_scan_json), fmt="json")
    data = json.loads(report)

    assert "metadata" in data
    assert "scan" in data
    assert data["scan"]["score"] == 75
    assert len(data["scan"]["findings"]) == 2


def test_missing_scan_file_graceful_failure() -> None:
    """Should fail cleanly with FileNotFoundError when loading non-existent JSON file."""
    with pytest.raises(FileNotFoundError):
        run_generate_evidence(from_scan_json="non-existent-scan.json")


def test_evidence_cli_generate_command(sample_scan_json: Path, tmp_path: Path) -> None:
    """The CLI evidence generate command should run successfully."""
    runner = CliRunner()
    output_file = tmp_path / "cli-evidence.md"

    result = runner.invoke(
        app,
        [
            "evidence",
            "generate",
            "--from",
            str(sample_scan_json),
            "--format",
            "markdown",
            "--output",
            str(output_file),
            "--include",
            "scan",
        ],
    )

    assert result.exit_code == 0
    assert output_file.exists()
    assert "CONDITIONAL GO" in output_file.read_text(encoding="utf-8")


def test_evidence_only_scan(sample_scan_json: Path) -> None:
    """Should generate report with only scan section included."""
    report = run_generate_evidence(
        from_scan_json=str(sample_scan_json), fmt="markdown", include="scan"
    )
    assert "3. Readiness Score" in report
    assert "4. Launch Decision" in report
    assert "9. AI-Assisted Development Governance Notes" in report
    # Under scan-only, no guard details should be rendered
    assert "Agent Governance / Guardrails" not in report


def test_evidence_scan_and_guard(sample_scan_json: Path, tmp_path: Path) -> None:
    """Should generate report with scan and guard sections included."""
    # Write mock guard log file
    log_dir = tmp_path / ".niyam" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "guard-actions.jsonl"
    log_file.write_text(
        json.dumps(
            {
                "timestamp": "2026-06-04T10:00:00Z",
                "session_id": "test-session",
                "actor_type": "agent",
                "tool": "shell",
                "action": "command_execute",
                "command": "npm test",
                "cwd": str(tmp_path),
                "exit_code": 0,
                "duration_ms": 1500,
                "mode": "observe",
            }
        )
        + "\n"
    )

    report = run_generate_evidence(
        from_scan_json=str(sample_scan_json), fmt="markdown", include="scan,guard"
    )
    assert "3. Readiness Score" in report
    assert "9. AI-Assisted Development Governance Notes" in report
    assert "npm test" in report


def test_evidence_all_sections(sample_scan_json: Path, tmp_path: Path) -> None:
    """Should generate report with all sections included."""
    # Mock guard log
    log_dir = tmp_path / ".niyam" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "guard-actions.jsonl"
    log_file.write_text(
        json.dumps(
            {
                "timestamp": "2026-06-04T10:00:00Z",
                "session_id": "test-session",
                "actor_type": "agent",
                "tool": "shell",
                "action": "command_execute",
                "command": "npm test",
                "cwd": str(tmp_path),
                "exit_code": 0,
                "duration_ms": 1500,
                "mode": "observe",
            }
        )
        + "\n"
    )

    # Mock MCP Registry
    mcp_file = tmp_path / ".niyam" / "mcp-registry.json"
    mcp_file.write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "tools": {
                    "mock-tool": {
                        "name": "mock-tool",
                        "type": "cli",
                        "command_or_url": "mock command",
                        "owner": "test-owner",
                        "risk_level": "medium",
                        "approved": True,
                        "capabilities": [],
                        "data_access": None,
                        "notes": None,
                    }
                },
            }
        )
    )

    # Mock Cost log
    cost_file = log_dir / "cost-events.jsonl"
    cost_file.write_text(
        json.dumps(
            {
                "timestamp": "2026-06-04T10:00:00Z",
                "session_id": "test-session",
                "task_id": "test-task",
                "tool_name": "claude",
                "model": "claude-sonnet",
                "input_tokens": 100,
                "output_tokens": 20,
                "estimated_cost": 0.0006,
                "repo": "test-repo",
                "branch": "main",
                "status": "success",
                "notes": None,
            }
        )
        + "\n"
    )

    report = run_generate_evidence(
        from_scan_json=str(sample_scan_json),
        fmt="markdown",
        include="scan,guard,mcp,cost",
    )
    assert "3. Readiness Score" in report
    assert "9. AI-Assisted Development Governance Notes" in report
    assert "mock-tool" in report
    assert "$0.0006" in report


def test_evidence_redacts_secrets(sample_scan_json: Path, tmp_path: Path) -> None:
    """Should redact secrets (like api keys or tokens) from the final evidence report."""
    # Write a mock guard log containing a secret key
    log_dir = tmp_path / ".niyam" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "guard-actions.jsonl"
    log_file.write_text(
        json.dumps(
            {
                "timestamp": "2026-06-04T10:00:00Z",
                "session_id": "test-session",
                "actor_type": "agent",
                "tool": "shell",
                "action": "command_execute",
                "command": "run_script.py --api_key=sb-1234567890abcdef",
                "cwd": str(tmp_path),
                "exit_code": 0,
                "duration_ms": 1500,
                "mode": "observe",
            }
        )
        + "\n"
    )

    report = run_generate_evidence(
        from_scan_json=str(sample_scan_json), fmt="markdown", include="guard"
    )
    assert "api_key=[REDACTED_SECRET]" in report
    assert "sb-1234567890abcdef" not in report


def test_evidence_reports_exact_10_sections_and_11_schema_keys(sample_scan_json: Path) -> None:
    """Verify that the generated report has the 10 standard sections and JSON has the 11 schema keys."""
    # Generate markdown and verify the 10 sections
    report_md = run_generate_evidence(from_scan_json=str(sample_scan_json), fmt="markdown")
    expected_sections = [
        "1. Executive Summary",
        "2. Project Metadata",
        "3. Readiness Score",
        "4. Launch Decision",
        "5. Decision Reason",
        "6. Critical and High Findings",
        "7. Risk Register",
        "8. Recommended Remediation Plan",
        "9. AI-Assisted Development Governance Notes",
        "10. Appendix Summary"
    ]
    for section in expected_sections:
        assert section in report_md

    # Generate JSON and verify the 11 schema keys
    report_json = run_generate_evidence(from_scan_json=str(sample_scan_json), fmt="json")
    data = json.loads(report_json)
    expected_keys = [
        "schema_version",
        "generated_at",
        "source",
        "project",
        "readiness_score",
        "decision",
        "decision_reason",
        "risk_summary",
        "findings_summary",
        "remediation_plan",
        "redaction_status"
    ]
    for key in expected_keys:
        assert key in data
