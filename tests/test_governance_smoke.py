"""Smoke tests for Niyam governance commands and structure."""

from __future__ import annotations

from typer.testing import CliRunner

from niyam.cli import app

runner = CliRunner()


def test_governance_imports() -> None:
    """Verify that all governance modules can be imported correctly."""
    from niyam.governance.scan.command import execute_scan
    from niyam.governance.evidence.command import execute_generate_evidence
    from niyam.governance.common.schemas import (
        GovernanceConfig,
        ScanConfig,
        GuardConfig,
    )
    from niyam.governance.common.redaction import redact_secrets

    assert execute_scan is not None
    assert execute_generate_evidence is not None
    assert GovernanceConfig is not None
    assert ScanConfig is not None
    assert GuardConfig is not None
    assert redact_secrets("password=supersecretkey") == "password=[REDACTED_SECRET]"


def test_scan_help() -> None:
    """Verify that niyam scan --help functions correctly."""
    result = runner.invoke(app, ["scan", "--help"])
    assert result.exit_code == 0
    assert "Scan the repository" in result.output
    assert "profile" in result.output


def test_evidence_help() -> None:
    """Verify that niyam evidence --help functions correctly."""
    result = runner.invoke(app, ["evidence", "--help"])
    assert result.exit_code == 0
    assert "evidence and readiness report" in result.output


def test_guard_help() -> None:
    """Verify that niyam guard --help functions correctly."""
    result = runner.invoke(app, ["guard", "--help"])
    assert result.exit_code == 0
    assert "Safety guardrails" in result.output


def test_mcp_help() -> None:
    """Verify that niyam mcp --help functions correctly."""
    result = runner.invoke(app, ["mcp", "--help"])
    assert result.exit_code == 0
    assert "Manage AI agent tools" in result.output


def test_cost_help() -> None:
    """Verify that niyam cost --help functions correctly."""
    result = runner.invoke(app, ["cost", "--help"])
    assert result.exit_code == 0
    assert "Track AI engineering token usage" in result.output


def test_regression_doctor_help() -> None:
    """Verify that existing command doctor --help still functions as expected."""
    result = runner.invoke(app, ["doctor", "--help"])
    assert result.exit_code == 0
    assert "Validate .niyam/ configuration" in result.output


def test_regression_init_help() -> None:
    """Verify that existing command init --help still functions as expected."""
    result = runner.invoke(app, ["init", "--help"])
    assert result.exit_code == 0
    assert "Initialize a governed" in result.output
