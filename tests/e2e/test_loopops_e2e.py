from __future__ import annotations

import json
from pathlib import Path
from typer.testing import CliRunner
from niyam.cli import app
from niyam.core.loopops import generate_starter_spec

def test_e2e_successful_code_change(tmp_path: Path) -> None:
    """E2E-001: Agent implements a safe code change, tests pass, evidence generated."""
    runner = CliRunner()
    spec_file = tmp_path / "spec.yaml"
    starter_spec = generate_starter_spec("success-loop", "code-change")
    spec_file.write_text(starter_spec, encoding="utf-8")

    result = runner.invoke(app, ["loop", "run", str(spec_file), "--scenario", "success"])
    assert result.exit_code == 0
    assert "Status: PASSED" in result.stdout
    assert "Iterations: 2/5" in result.stdout
    assert "Reason: Loop completed successfully (goal met)." in result.stdout

def test_e2e_requires_approval(tmp_path: Path) -> None:
    """E2E-002: Agent modifies authentication files or high-risk files -> requires approval."""
    runner = CliRunner()
    spec_file = tmp_path / "spec.yaml"
    starter_spec = generate_starter_spec("approve-loop", "code-change")
    spec_file.write_text(starter_spec, encoding="utf-8")

    result = runner.invoke(app, ["loop", "run", str(spec_file), "--scenario", "approval"])
    assert result.exit_code == 0
    assert "Status: STOPPED_FOR_APPROVAL" in result.stdout
    assert "Reason: Modified authentication middleware" in result.stdout

def test_e2e_repeated_failure(tmp_path: Path) -> None:
    """E2E-003: Agent tries to fix the same failing test repeatedly -> stops."""
    runner = CliRunner()
    spec_file = tmp_path / "spec.yaml"
    starter_spec = generate_starter_spec("fail-loop", "code-change")
    spec_file.write_text(starter_spec, encoding="utf-8")

    result = runner.invoke(app, ["loop", "run", str(spec_file), "--scenario", "stop-failures"])
    assert result.exit_code == 0
    assert "Status: STOPPED" in result.stdout
    assert "Reason: Stop condition triggered: 'repeatedFailureCount >= 3'." in result.stdout

def test_e2e_cost_overrun(tmp_path: Path) -> None:
    """E2E-004: Agent consumes too many tokens/exceeds budget -> stops."""
    runner = CliRunner()
    spec_file = tmp_path / "spec.yaml"
    starter_spec = generate_starter_spec("cost-loop", "code-change")
    spec_file.write_text(starter_spec, encoding="utf-8")

    result = runner.invoke(app, ["loop", "run", str(spec_file), "--scenario", "budget-cost"])
    assert result.exit_code == 0
    assert "Status: STOPPED" in result.stdout
    assert "Reason: Max cost budget ($3.00) exceeded." in result.stdout
