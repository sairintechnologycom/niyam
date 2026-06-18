from __future__ import annotations

import json
from pathlib import Path
import pytest
from typer.testing import CliRunner

from niyam.cli import app
from niyam.core.loopops import generate_starter_spec

def test_cli_loop_help() -> None:
    """LOOP-CLI-001: Should show help commands for niyam loop."""
    runner = CliRunner()
    result = runner.invoke(app, ["loop", "--help"])
    assert result.exit_code == 0
    assert "init" in result.stdout
    assert "validate" in result.stdout
    assert "run" in result.stdout
    assert "report" in result.stdout
    assert "evidence" in result.stdout

def test_cli_loop_init() -> None:
    """LOOP-CLI-002, LOOP-CLI-003, LOOP-CLI-004: Should print a starter spec YAML when calling 'niyam loop init'."""
    runner = CliRunner()
    # Starter code-change spec
    result = runner.invoke(app, ["loop", "init", "--name", "cli-test-loop", "--type", "code-change"])
    assert result.exit_code == 0
    assert "apiVersion: niyam.dev/v1" in result.stdout
    assert "name: cli-test-loop" in result.stdout
    assert "type: code-change" in result.stdout

def test_cli_loop_validate_success(tmp_path: Path) -> None:
    """LOOP-CLI-005: Should print PASS for a valid spec file."""
    runner = CliRunner()
    spec_file = tmp_path / "valid.yaml"
    starter_spec = generate_starter_spec("test-cli-valid", "code-change")
    spec_file.write_text(starter_spec, encoding="utf-8")

    result = runner.invoke(app, ["loop", "validate", str(spec_file)])
    assert result.exit_code == 0
    assert "PASS: LoopSpec 'test-cli-valid' is valid." in result.stdout
    assert "Summary:" in result.stdout
    assert "Name: test-cli-valid" in result.stdout

def test_cli_loop_validate_failure(tmp_path: Path) -> None:
    """LOOP-CLI-006: Should print FAIL and exit 1 for an invalid spec file."""
    runner = CliRunner()
    spec_file = tmp_path / "invalid.yaml"
    bad_yaml = """
apiVersion: niyam.dev/v1
kind: LoopSpec
metadata:
  owner: platform
goal:
  type: code
  description: desc
budgets:
  maxIterations: 0
"""
    spec_file.write_text(bad_yaml, encoding="utf-8")

    result = runner.invoke(app, ["loop", "validate", str(spec_file)])
    assert result.exit_code == 1
    assert "FAIL: LoopSpec validation failed." in result.stdout

def test_cli_loop_validate_missing() -> None:
    """LOOP-CLI-007: Should exit with non-zero when file is missing."""
    runner = CliRunner()
    result = runner.invoke(app, ["loop", "validate", "nonexistent_file.yaml"])
    # Typer should automatically fail with exit code 2 because exists=True on Argument
    assert result.exit_code != 0

def test_cli_loop_run_success(tmp_path: Path) -> None:
    """LOOP-CLI-008: Should run the simulator successfully."""
    runner = CliRunner()
    spec_file = tmp_path / "spec.yaml"
    starter_spec = generate_starter_spec("success-loop", "code-change")
    spec_file.write_text(starter_spec, encoding="utf-8")

    result = runner.invoke(app, ["loop", "run", str(spec_file), "--scenario", "success"])
    assert result.exit_code == 0
    assert "Niyam LoopOps" in result.stdout
    assert "Loop: success-loop" in result.stdout
    assert "Status: PASSED" in result.stdout
    assert "Iterations: 2/5" in result.stdout

def test_cli_loop_run_budget_iterations(tmp_path: Path) -> None:
    """Should simulate stopping when max iterations budget is exceeded."""
    runner = CliRunner()
    spec_file = tmp_path / "spec.yaml"
    starter_spec = generate_starter_spec("iter-loop", "code-change")
    spec_file.write_text(starter_spec, encoding="utf-8")

    result = runner.invoke(app, ["loop", "run", str(spec_file), "--scenario", "budget-iterations"])
    assert result.exit_code == 0
    assert "Status: STOPPED" in result.stdout
    assert "Iterations: 5/5" in result.stdout
    assert "Reason: Max iterations (5) exceeded." in result.stdout

def test_cli_loop_run_budget_cost(tmp_path: Path) -> None:
    """Should simulate stopping when cost budget is exceeded."""
    runner = CliRunner()
    spec_file = tmp_path / "spec.yaml"
    starter_spec = generate_starter_spec("cost-loop", "code-change")
    spec_file.write_text(starter_spec, encoding="utf-8")

    result = runner.invoke(app, ["loop", "run", str(spec_file), "--scenario", "budget-cost"])
    assert result.exit_code == 0
    assert "Status: STOPPED" in result.stdout
    assert "Reason: Max cost budget ($3.00) exceeded." in result.stdout

def test_cli_loop_run_stop_failures(tmp_path: Path) -> None:
    """Should simulate stopping due to repeated failures condition."""
    runner = CliRunner()
    spec_file = tmp_path / "spec.yaml"
    starter_spec = generate_starter_spec("fail-loop", "code-change")
    spec_file.write_text(starter_spec, encoding="utf-8")

    result = runner.invoke(app, ["loop", "run", str(spec_file), "--scenario", "stop-failures"])
    assert result.exit_code == 0
    assert "Status: STOPPED" in result.stdout
    assert "Reason: Stop condition triggered: 'repeatedFailureCount >= 3'." in result.stdout

def test_cli_loop_run_stop_errors(tmp_path: Path) -> None:
    """Should simulate stopping due to repeating error condition."""
    runner = CliRunner()
    spec_file = tmp_path / "spec.yaml"
    starter_spec = generate_starter_spec("err-loop", "code-change")
    spec_file.write_text(starter_spec, encoding="utf-8")

    result = runner.invoke(app, ["loop", "run", str(spec_file), "--scenario", "stop-errors"])
    assert result.exit_code == 0
    assert "Status: STOPPED" in result.stdout
    assert "Reason: Stop condition triggered: 'sameErrorRepeated >= 2'." in result.stdout

def test_cli_loop_run_approval(tmp_path: Path) -> None:
    """Should simulate transition to approval state."""
    runner = CliRunner()
    spec_file = tmp_path / "spec.yaml"
    starter_spec = generate_starter_spec("approve-loop", "code-change")
    spec_file.write_text(starter_spec, encoding="utf-8")

    result = runner.invoke(app, ["loop", "run", str(spec_file), "--scenario", "approval"])
    assert result.exit_code == 0
    assert "Status: STOPPED_FOR_APPROVAL" in result.stdout
    assert "Risk: Medium → High" in result.stdout

def test_cli_loop_report_and_evidence(tmp_path: Path) -> None:
    """Should successfully run report and bundle CLI commands."""
    runner = CliRunner()
    spec_file = tmp_path / "spec.yaml"
    starter_spec = generate_starter_spec("cli-ev-loop", "code-change")
    spec_file.write_text(starter_spec, encoding="utf-8")

    # Run the loop simulation to generate evidence
    run_res = runner.invoke(app, ["loop", "run", str(spec_file), "--scenario", "success"])
    assert run_res.exit_code == 0

    loops_dir = tmp_path / ".niyam" / "evidence" / "loops" / "cli-ev-loop"
    run_json_path = list(loops_dir.glob("**/run.json"))[0]
    with open(run_json_path, encoding="utf-8") as f:
        run_data = json.load(f)
    loop_id = run_data["id"]

    # Test niyam loop report
    report_res = runner.invoke(app, ["loop", "report", loop_id])
    assert report_res.exit_code == 0
    assert "Niyam LoopOps Run Report: cli-ev-loop" in report_res.stdout
    assert "- **Status**: `PASSED`" in report_res.stdout

    # Test HTML report format
    report_html_res = runner.invoke(app, ["loop", "report", loop_id, "--format", "html"])
    assert report_html_res.exit_code == 0
    assert "<!DOCTYPE html>" in report_html_res.stdout

    # Test report --output
    out_file = tmp_path / "custom_report.md"
    report_out_res = runner.invoke(app, ["loop", "report", loop_id, "--output", str(out_file)])
    assert report_out_res.exit_code == 0
    assert "PASS: Report written to" in report_out_res.stdout
    assert out_file.exists()

    # Test niyam loop evidence --bundle
    zip_bundle = tmp_path / "bundle.zip"
    bundle_res = runner.invoke(app, ["loop", "evidence", loop_id, "--bundle", str(zip_bundle)])
    assert bundle_res.exit_code == 0
    assert "PASS: Evidence bundle created at" in bundle_res.stdout
    assert zip_bundle.exists()


def test_cli_loop_review(tmp_path: Path) -> None:
    """Should run loop review successfully."""
    runner = CliRunner()
    diff_file = tmp_path / "test.patch"
    diff_file.write_text("diff --git a/test.py b/test.py\n+new line", encoding="utf-8")

    result = runner.invoke(app, ["loop", "review", "--diff", str(diff_file), "--reviewer", "gemini"])
    assert result.exit_code == 0
    assert "Niyam LoopOps: Reviewing diff via gemini" in result.stdout
    assert "Status: SUCCESS" in result.stdout


def test_cli_loop_run_with_overrides(tmp_path: Path) -> None:
    """Should run the loop run command with planner/implementer/reviewer overrides."""
    runner = CliRunner()
    spec_file = tmp_path / "spec.yaml"
    starter_spec = generate_starter_spec("override-loop", "code-change")
    spec_file.write_text(starter_spec, encoding="utf-8")

    result = runner.invoke(app, [
        "loop", "run", str(spec_file),
        "--scenario", "success",
        "--planner", "claude",
        "--implementer", "codex",
        "--reviewer", "gemini",
        "--dry-run"
    ])
    assert result.exit_code == 0
    assert "Status: PASSED" in result.stdout

