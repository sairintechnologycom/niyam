"""Tests for Niyam evidence report generation capability."""

from __future__ import annotations

import json
from pathlib import Path
import pytest
from typer.testing import CliRunner

from niyam.cli import app
from niyam.core.evidence import run_generate_evidence

@pytest.fixture
def sample_scan_json(tmp_path: Path) -> Path:
    """Create a mock niyam-scan.json file for testing."""
    scan_file = tmp_path / "niyam-scan.json"
    scan_file.write_text(json.dumps({
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
                "recommendation": "Remove it from repo."
            },
            {
                "id": "DOC001",
                "title": "Missing Readme",
                "category": "docs",
                "severity": "low",
                "file_path": "",
                "description": "Readme is missing.",
                "recommendation": "Create README.md."
            }
        ]
    }))
    return scan_file

def test_generate_evidence_from_scan_json(sample_scan_json: Path) -> None:
    """Should correctly generate evidence when loading scan results from JSON."""
    report = run_generate_evidence(from_scan_json=str(sample_scan_json), fmt="markdown")
    
    assert "75/100" in report
    assert "CONDITIONAL_GO" in report
    assert "SEC001" in report
    assert "DOC001" in report


def test_generate_markdown_and_html_reports(sample_scan_json: Path, tmp_path: Path) -> None:
    """Should support both markdown and HTML generation and write to output path."""
    md_output = tmp_path / "report.md"
    html_output = tmp_path / "report.html"
    
    # Generate Markdown
    run_generate_evidence(from_scan_json=str(sample_scan_json), fmt="markdown", output=str(md_output))
    assert md_output.exists()
    assert "# Niyam Governance" in md_output.read_text(encoding="utf-8")
    
    # Generate HTML
    run_generate_evidence(from_scan_json=str(sample_scan_json), fmt="html", output=str(html_output))
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
    
    result = runner.invoke(app, [
        "evidence", "generate", 
        "--from", str(sample_scan_json), 
        "--format", "markdown", 
        "--output", str(output_file)
    ])
    
    assert result.exit_code == 0
    assert output_file.exists()
    assert "CONDITIONAL_GO" in output_file.read_text(encoding="utf-8")
