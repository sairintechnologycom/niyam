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


def test_evidence_reports_exact_11_sections_and_11_schema_keys(
    sample_scan_json: Path,
) -> None:
    """Verify that the generated report has the 11 standard sections and JSON has the 11 schema keys."""
    # Generate markdown and verify the 11 sections
    report_md = run_generate_evidence(
        from_scan_json=str(sample_scan_json), fmt="markdown"
    )
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
        "10. Cost & Performance Analytics",
        "11. Appendix Summary",
    ]
    for section in expected_sections:
        assert section in report_md

    # Generate JSON and verify the 11 schema keys
    report_json = run_generate_evidence(
        from_scan_json=str(sample_scan_json), fmt="json"
    )
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
        "redaction_status",
    ]
    for key in expected_keys:
        assert key in data


def test_evidence_with_and_without_guard_logs(
    sample_scan_json: Path, tmp_path: Path
) -> None:
    # 1. Without guard logs (skip guard section gracefully)
    # The file .niyam/logs/guard-actions.jsonl doesn't exist yet, so we test without guard logs.
    report_no_logs = run_generate_evidence(
        from_scan_json=str(sample_scan_json), fmt="markdown", include="scan,guard"
    )
    # The report should compile without crashing, and should not contain Agent Governance Summary
    assert "Agent Governance Summary (Niyam Guard)" not in report_no_logs

    # 2. With guard logs
    log_dir = tmp_path / ".niyam" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "guard-actions.jsonl"

    # Write some logs
    log_file.write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "timestamp": "2026-06-04T10:00:00Z",
                "session_id": "session-123",
                "actor_type": "agent",
                "tool": "shell",
                "action": "command_execute",
                "command": "npm test",
                "cwd": str(tmp_path),
                "exit_code": 0,
                "duration_ms": 1200,
                "mode": "observe",
                "policy_decision": "allow",
                "decision": "allowed",
            }
        )
        + "\n"
        + json.dumps(
            {
                "schema_version": "1.0.0",
                "timestamp": "2026-06-04T10:01:00Z",
                "session_id": "session-123",
                "actor_type": "agent",
                "tool": "shell",
                "action": "command_execute",
                "command": "rm -rf /tmp",
                "cwd": str(tmp_path),
                "exit_code": 1,
                "duration_ms": 0,
                "mode": "block",
                "policy_decision": "block",
                "decision": "blocked",
            }
        )
        + "\n"
    )

    report_with_logs = run_generate_evidence(
        from_scan_json=str(sample_scan_json), fmt="markdown", include="scan,guard"
    )

    # 1. Summarize total commands
    assert "Total Actions:** 2" in report_with_logs
    # 2. Summarize blocked/warned/approved actions
    assert "Total Blocked:** 1" in report_with_logs
    assert "Total Warned:** 0" in report_with_logs
    # 3. Summarize failed commands (blocked does not count as run/failed)
    assert "Total Failed:** 0" in report_with_logs
    # 4. Include latest session details
    assert "Session ID:** `session-123`" in report_with_logs
    assert "Session Total Actions:** 2" in report_with_logs
    assert "Session Blocked:** 1" in report_with_logs
    # 5. Top command categories
    assert "npm (1)" in report_with_logs
    assert "rm (1)" in report_with_logs
    # 6. Blocked action appears as policy event
    assert "rm -rf /tmp" in report_with_logs


def test_evidence_secrets_and_redaction(
    sample_scan_json: Path, tmp_path: Path, monkeypatch
) -> None:
    # Set environment secret variables to verify they are NOT included in the report
    monkeypatch.setenv("SECRET_AWS_KEY", "aws-super-secret-key-12345")
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:password123@localhost/db")

    log_dir = tmp_path / ".niyam" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "guard-actions.jsonl"

    # Write a log entry with a secret command to verify redaction
    log_file.write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "timestamp": "2026-06-04T10:00:00Z",
                "session_id": "session-sec",
                "actor_type": "agent",
                "tool": "shell",
                "action": "command_execute",
                "command": "curl -u admin sk-proj-1234567890abcdef1234567890abcdef",
                "cwd": str(tmp_path),
                "exit_code": 0,
                "duration_ms": 500,
                "mode": "observe",
                "policy_decision": "allow",
                "decision": "allowed",
            }
        )
        + "\n"
    )

    report = run_generate_evidence(
        from_scan_json=str(sample_scan_json), fmt="markdown", include="guard"
    )

    # 1. Redacted commands remain redacted in output
    assert "sk-proj-1234567890abcdef" not in report
    # 2. No environment secrets included
    assert "aws-super-secret-key-12345" not in report
    assert "password123" not in report


def test_evidence_with_and_without_registry(
    sample_scan_json: Path, tmp_path: Path
) -> None:
    # 1. Evidence without registry
    # Ensure any existing registry file is gone
    mcp_file = tmp_path / ".niyam" / "mcp-registry.json"
    if mcp_file.exists():
        mcp_file.unlink()

    report_no_reg = run_generate_evidence(
        from_scan_json=str(sample_scan_json), fmt="markdown", include="scan,mcp"
    )
    assert "MCP Registry not found. Skipping MCP governance posture." in report_no_reg
    assert "Total Registered Tools:" not in report_no_reg

    # Check JSON output format as well
    report_json_no_reg = run_generate_evidence(
        from_scan_json=str(sample_scan_json), fmt="json", include="scan,mcp"
    )
    data_no_reg = json.loads(report_json_no_reg)
    assert data_no_reg["mcp"]["exists"] is False
    assert data_no_reg["mcp"]["total"] == 0

    # 2. Evidence with registry
    mcp_file.write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "tools": {
                    "tool-a": {
                        "name": "tool-a",
                        "type": "cli",
                        "command_or_url": "python run.py",
                        "owner": "dev",
                        "risk_level": "low",
                        "approved": True,
                        "capabilities": [],
                        "data_access": None,
                        "notes": None,
                    }
                },
            }
        )
    )

    report_with_reg = run_generate_evidence(
        from_scan_json=str(sample_scan_json), fmt="markdown", include="scan,mcp"
    )
    assert "MCP Registry not found" not in report_with_reg
    assert "Total Registered Tools:** 1" in report_with_reg
    assert "Approved Tools:** 1" in report_with_reg
    assert "Unapproved Tools:** 0" in report_with_reg
    assert "High-risk Tools:** 0" in report_with_reg
    assert "Critical-risk Tools:** 0" in report_with_reg


def test_evidence_mcp_unapproved_findings(
    sample_scan_json: Path, tmp_path: Path
) -> None:
    mcp_file = tmp_path / ".niyam" / "mcp-registry.json"
    mcp_file.write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "tools": {
                    "approved-tool": {
                        "name": "approved-tool",
                        "type": "cli",
                        "risk_level": "medium",
                        "approved": True,
                    },
                    "unapproved-high-tool": {
                        "name": "unapproved-high-tool",
                        "type": "cli",
                        "risk_level": "high",
                        "approved": False,
                    },
                    "unapproved_critical_tool": {
                        "name": "unapproved_critical_tool",
                        "type": "cli",
                        "risk_level": "critical",
                        "approved": False,
                    },
                },
            }
        )
    )

    report_md = run_generate_evidence(
        from_scan_json=str(sample_scan_json), fmt="markdown", include="scan,mcp"
    )

    # High/critical unapproved tools count
    assert "High/Critical Unapproved Tools:** 2" in report_md

    # Check that they appear in findings / Risk Register
    assert "MCP-unapproved-high-tool" in report_md
    assert "MCP-unapproved_critical_tool" in report_md
    assert "Unapproved High-Risk Tool" in report_md
    assert "Unapproved Critical-Risk Tool" in report_md

    # Check recommended actions
    assert "Approve tool 'unapproved-high-tool'" in report_md

    # Check JSON output structure has updated risk_summary
    report_json = run_generate_evidence(
        from_scan_json=str(sample_scan_json), fmt="json", include="scan,mcp"
    )
    data = json.loads(report_json)

    # Check updated risk summary counts
    assert data["risk_summary"]["high"] == 1  # 0 from sample_scan_json + 1 injected
    assert (
        data["risk_summary"]["critical"] == 2
    )  # 1 from sample_scan_json (SEC001) + 1 injected

    # Findings should contain the injected ones
    finding_ids = [f["id"] for f in data["findings_summary"]]
    assert "MCP-unapproved-high-tool" in finding_ids
    assert "MCP-unapproved_critical_tool" in finding_ids


def test_evidence_mcp_redaction_and_secrets(
    sample_scan_json: Path, tmp_path: Path
) -> None:
    # Verify that sensitive fields/secrets in tools are redacted in the generated output formats
    mcp_file = tmp_path / ".niyam" / "mcp-registry.json"
    mcp_file.write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "tools": {
                    "api-key-tool": {
                        "name": "api-key-tool",
                        "type": "api",
                        "command_or_url": "https://api.github.com?token=ghp_abc1234567890abcdef1234567890abcdef12",
                        "owner": "test",
                        "risk_level": "medium",
                        "approved": True,
                        "notes": "password = 'secretPassword123'",
                    }
                },
            }
        )
    )

    # 1. Markdown redaction
    report_md = run_generate_evidence(
        from_scan_json=str(sample_scan_json), fmt="markdown", include="scan,mcp"
    )
    assert "ghp_abc1234567890abcdef" not in report_md
    assert "secretPassword123" not in report_md

    # 2. HTML redaction
    report_html = run_generate_evidence(
        from_scan_json=str(sample_scan_json), fmt="html", include="scan,mcp"
    )
    assert "ghp_abc1234567890abcdef" not in report_html
    assert "secretPassword123" not in report_html

    # 3. JSON redaction
    report_json = run_generate_evidence(
        from_scan_json=str(sample_scan_json), fmt="json", include="scan,mcp"
    )
    assert "ghp_abc1234567890abcdef" not in report_json
    assert "secretPassword123" not in report_json
    assert "[REDACTED_SECRET]" in report_json
