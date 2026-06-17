"""Tests for Niyam LoopOps validation and CLI commands."""

from __future__ import annotations

import os
from pathlib import Path
import json
import pytest
import yaml
from typer.testing import CliRunner

from niyam.cli import app
from niyam.core.loopops import (
    validate_loop_spec,
    generate_starter_spec,
    LoopSpec,
    LoopRun,
    LoopStateMachine,
    LoopRunner,
    LoopIteration,
    LoopObservation,
    LoopPolicyDecision,
)


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


def test_loopops_generate_starter_spec() -> None:
    """Should generate a valid starter spec string."""
    spec_str = generate_starter_spec("test-loop", "code-change")
    assert "apiVersion: niyam.dev/v1" in spec_str
    assert "kind: LoopSpec" in spec_str
    assert "name: test-loop" in spec_str
    assert "type: code-change" in spec_str

    # Validate that it loads as valid YAML
    data = yaml.safe_load(spec_str)
    assert data["apiVersion"] == "niyam.dev/v1"
    assert data["metadata"]["name"] == "test-loop"

    # Validate using core validator
    errors = validate_loop_spec(data)
    assert not errors, f"Starter spec has validation errors: {errors}"


def test_loopops_validation_success() -> None:
    """Should pass validation on a correct LoopSpec dictionary."""
    valid_data = {
        "apiVersion": "niyam.dev/v1",
        "kind": "LoopSpec",
        "metadata": {
            "name": "valid-loop",
            "owner": "platform",
            "riskTier": "low"
        },
        "goal": {
            "type": "code_change",
            "description": "Safe code changes"
        },
        "actors": {
            "planner": "claude",
            "implementer": "codex"
        },
        "steps": [
            {
                "name": "plan",
                "action": "generate_plan",
                "actor": "claude",
                "requiredEvidence": ["plan_doc"]
            },
            {
                "name": "implement",
                "action": "modify_files",
                "actor": "codex"
            }
        ],
        "budgets": {
            "maxIterations": 5,
            "maxTokens": 1000,
            "maxCostUsd": 1.5,
            "maxRuntimeMinutes": 10
        },
        "stopConditions": [
            "repeatedFailureCount >= 3",
            "policyViolation == critical"
        ]
    }
    errors = validate_loop_spec(valid_data)
    assert not errors


def test_loopops_validation_failures() -> None:
    """Should return errors for various semantic validation failure conditions."""
    # 1. Missing metadata.name
    bad_data = {
        "apiVersion": "niyam.dev/v1",
        "kind": "LoopSpec",
        "metadata": {
            "owner": "platform"
        },
        "goal": {
            "type": "code",
            "description": "desc"
        },
        "actors": {},
        "steps": [{"name": "s1", "action": "act"}],
        "budgets": {"maxIterations": 3}
    }
    errors = validate_loop_spec(bad_data)
    assert any("Schema error at metadata -> name" in err for err in errors)

    # 2. No steps defined
    bad_data_steps = {
        "apiVersion": "niyam.dev/v1",
        "kind": "LoopSpec",
        "metadata": {"name": "test", "owner": "platform"},
        "goal": {"type": "code", "description": "desc"},
        "actors": {},
        "steps": [],
        "budgets": {"maxIterations": 3}
    }
    errors = validate_loop_spec(bad_data_steps)
    assert "No steps are defined in the loop specification." in errors

    # 3. maxIterations < 1
    bad_data_budget = {
        "apiVersion": "niyam.dev/v1",
        "kind": "LoopSpec",
        "metadata": {"name": "test", "owner": "platform"},
        "goal": {"type": "code", "description": "desc"},
        "actors": {},
        "steps": [{"name": "s1", "action": "act"}],
        "budgets": {"maxIterations": 0}
    }
    errors = validate_loop_spec(bad_data_budget)
    assert "budgets.maxIterations must be greater than or equal to 1." in errors

    # 4. Step references unknown actor
    bad_data_actor = {
        "apiVersion": "niyam.dev/v1",
        "kind": "LoopSpec",
        "metadata": {"name": "test", "owner": "platform"},
        "goal": {"type": "code", "description": "desc"},
        "actors": {"planner": "claude"},
        "steps": [{"name": "s1", "action": "act", "actor": "unknown_actor"}],
        "budgets": {"maxIterations": 3}
    }
    errors = validate_loop_spec(bad_data_actor)
    assert "Step 's1' references an unknown actor 'unknown_actor'." in errors

    # 5. Invalid stop conditions comparison syntax
    bad_data_stop = {
        "apiVersion": "niyam.dev/v1",
        "kind": "LoopSpec",
        "metadata": {"name": "test", "owner": "platform"},
        "goal": {"type": "code", "description": "desc"},
        "actors": {},
        "steps": [{"name": "s1", "action": "act"}],
        "budgets": {"maxIterations": 3},
        "stopConditions": ["invalidCondition", "var = 5", "var >= "]
    }
    errors = validate_loop_spec(bad_data_stop)
    assert "Stop condition 'invalidCondition' has invalid comparison syntax." in errors[0]
    assert "Stop condition 'var = 5' has invalid comparison syntax." in errors[1]
    assert "Stop condition 'var >= ' has invalid comparison syntax." in errors[2]

    # 6. Malformed requiredEvidence
    bad_data_evidence = {
        "apiVersion": "niyam.dev/v1",
        "kind": "LoopSpec",
        "metadata": {"name": "test", "owner": "platform"},
        "goal": {"type": "code", "description": "desc"},
        "actors": {},
        "steps": [{"name": "s1", "action": "act", "requiredEvidence": ["", "valid_ev"]}],
        "budgets": {"maxIterations": 3}
    }
    errors = validate_loop_spec(bad_data_evidence)
    assert "Step 's1' requiredEvidence at index 0 must be a non-empty string." in errors


def test_cli_loop_init() -> None:
    """Should print a starter spec YAML when calling 'niyam loop init'."""
    runner = CliRunner()
    result = runner.invoke(app, ["loop", "init", "--name", "cli-test-loop", "--type", "custom-type"])
    assert result.exit_code == 0
    assert "apiVersion: niyam.dev/v1" in result.stdout
    assert "name: cli-test-loop" in result.stdout
    assert "type: custom-type" in result.stdout


def test_cli_loop_validate_success(tmp_path: Path) -> None:
    """Should print PASS for a valid spec file."""
    runner = CliRunner()

    spec_file = tmp_path / "valid.yaml"
    starter_spec = generate_starter_spec("test-cli-valid", "code-change")
    spec_file.write_text(starter_spec, encoding="utf-8")

    result = runner.invoke(app, ["loop", "validate", str(spec_file)])
    assert result.exit_code == 0
    assert "PASS: LoopSpec 'test-cli-valid' is valid." in result.stdout
    assert "Summary:" in result.stdout
    assert "Name: test-cli-valid" in result.stdout
    assert "Owner:" in result.stdout
    assert "Goal: code-change" in result.stdout


def test_cli_loop_validate_failure(tmp_path: Path) -> None:
    """Should print FAIL and exit 1 for an invalid spec file."""
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


def test_state_machine_transitions() -> None:
    """Should enforce valid state transitions and raise ValueError for invalid ones."""
    # Initialize a LoopRun
    run = LoopRun(
        id="LR-123456",
        specName="test-loop",
        goal="testing transitions",
        status="pending",
        startedAt="2026-06-17T12:00:00Z",
        maxIterations=5,
    )
    sm = LoopStateMachine(run)

    # Valid transitions from pending
    assert run.status == "pending"
    sm.transition_to("running")
    assert run.status == "running"

    # Valid transition to evaluating
    sm.transition_to("evaluating")
    assert run.status == "evaluating"

    # Valid transition to running
    sm.transition_to("running")
    assert run.status == "running"

    # Valid transition to stopped
    sm.transition_to("stopped")
    assert run.status == "stopped"

    # Stopped is terminal, cannot transition out
    with pytest.raises(ValueError, match="Invalid transition"):
        sm.transition_to("running")


def test_state_machine_budgets() -> None:
    """Should correctly stop when max iterations or max cost budgets are exceeded."""
    from niyam.core.loopops import LoopBudgets

    # 1. Max iterations exceeded
    run = LoopRun(
        id="LR-ITER",
        specName="test-loop",
        goal="test",
        status="running",
        startedAt="2026-06-17T12:00:00Z",
        maxIterations=5,
        iterationCount=5,  # Exceeded or met
        costUsd=1.0,
    )
    sm = LoopStateMachine(run)
    budgets = LoopBudgets(maxIterations=5, maxCostUsd=3.0)

    sm.transition_to("evaluating")
    reason = sm.evaluate_budgets(budgets)
    assert reason == "Max iterations (5) exceeded."
    assert run.status == "stopped"

    # 2. Max cost exceeded
    run_cost = LoopRun(
        id="LR-COST",
        specName="test-loop",
        goal="test",
        status="running",
        startedAt="2026-06-17T12:00:00Z",
        maxIterations=5,
        iterationCount=2,
        costUsd=3.50,  # Exceeds budget
    )
    sm_cost = LoopStateMachine(run_cost)
    sm_cost.transition_to("evaluating")
    reason_cost = sm_cost.evaluate_budgets(budgets)
    assert reason_cost == "Max cost budget ($3.00) exceeded."
    assert run_cost.status == "stopped"


def test_state_machine_stop_conditions() -> None:
    """Should correctly parse and evaluate comparison stop conditions."""
    run = LoopRun(
        id="LR-COND",
        specName="test-loop",
        goal="test",
        status="running",
        startedAt="2026-06-17T12:00:00Z",
        maxIterations=5,
    )
    sm = LoopStateMachine(run)

    # 1. repeatedFailureCount >= 3
    metrics = {"repeatedFailureCount": 3}
    assert sm.evaluate_stop_condition("repeatedFailureCount >= 3", metrics) is True
    metrics = {"repeatedFailureCount": 2}
    assert sm.evaluate_stop_condition("repeatedFailureCount >= 3", metrics) is False

    # 2. sameErrorRepeated >= 2
    metrics = {"sameErrorRepeated": 2}
    assert sm.evaluate_stop_condition("sameErrorRepeated >= 2", metrics) is True
    metrics = {"sameErrorRepeated": 1}
    assert sm.evaluate_stop_condition("sameErrorRepeated >= 2", metrics) is False

    # 3. policyViolation == critical
    metrics = {"policyViolation": "critical"}
    assert sm.evaluate_stop_condition("policyViolation == critical", metrics) is True
    metrics = {"policyViolation": "high"}
    assert sm.evaluate_stop_condition("policyViolation == critical", metrics) is False

    # 4. humanApprovalRequired == true
    metrics = {"humanApprovalRequired": True}
    assert sm.evaluate_stop_condition("humanApprovalRequired == true", metrics) is True
    metrics = {"humanApprovalRequired": False}
    assert sm.evaluate_stop_condition("humanApprovalRequired == true", metrics) is False


def test_cli_loop_run_success(tmp_path: Path) -> None:
    """Should simulate successful run to completion."""
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
    assert "Cost: $0.85 / $3.00" in result.stdout
    assert "Risk: Medium" in result.stdout
    assert "Reason: Loop completed successfully (goal met)." in result.stdout
    assert "Evidence Pack:" in result.stdout


def test_cli_loop_run_budget_iterations(tmp_path: Path) -> None:
    """Should simulate stopping when max iterations budget is exceeded."""
    runner = CliRunner()
    spec_file = tmp_path / "spec.yaml"
    starter_spec = generate_starter_spec("iter-loop", "code-change")
    spec_file.write_text(starter_spec, encoding="utf-8")

    result = runner.invoke(app, ["loop", "run", str(spec_file), "--scenario", "budget-iterations"])
    assert result.exit_code == 0
    assert "Niyam LoopOps" in result.stdout
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
    assert "Niyam LoopOps" in result.stdout
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
    assert "Niyam LoopOps" in result.stdout
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
    assert "Niyam LoopOps" in result.stdout
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
    assert "Niyam LoopOps" in result.stdout
    assert "Status: STOPPED_FOR_APPROVAL" in result.stdout
    assert "Risk: Medium → High" in result.stdout
    assert "Reason: Modified authentication middleware" in result.stdout


def test_evidence_generation_success(tmp_path: Path) -> None:
    """Should correctly generate iterations, artifacts, and report.md in the evidence directory."""
    from niyam.core.loopops import LoopRunner, validate_loop_spec
    import json

    spec_data = {
        "apiVersion": "niyam.dev/v1",
        "kind": "LoopSpec",
        "metadata": {
            "name": "ev-test-loop",
            "owner": "platform",
            "riskTier": "low"
        },
        "goal": {
            "type": "code_change",
            "description": "Evidence testing"
        },
        "actors": {
            "planner": "claude",
            "implementer": "codex"
        },
        "steps": [
            {
                "name": "plan",
                "action": "generate_plan",
                "actor": "claude"
            }
        ],
        "budgets": {
            "maxIterations": 3,
            "maxCostUsd": 2.0
        },
        "stopConditions": [
            "repeatedFailureCount >= 2"
        ]
    }

    errors = validate_loop_spec(spec_data)
    assert not errors

    spec = LoopSpec.model_validate(spec_data)
    run = LoopRunner.initialize_run(spec)

    # Check that evidence directory structure was initialized
    evidence_dir = tmp_path / run.evidence_path
    assert evidence_dir.exists()
    assert (evidence_dir / "iterations").exists()
    assert (evidence_dir / "artifacts").exists()
    assert (evidence_dir / "run.json").exists()
    assert (evidence_dir / "loop-spec.yaml").exists()

    # Process iteration 1
    reason1 = LoopRunner.process_step_result(run, spec, {"status": "success", "cost_usd": 0.50})
    assert reason1 is None
    assert (evidence_dir / "iterations" / "001.json").exists()
    assert (evidence_dir / "artifacts" / "test-output.txt").exists()
    assert (evidence_dir / "artifacts" / "diff.patch").exists()
    assert (evidence_dir / "artifacts" / "policy-results.json").exists()

    # Process iteration 2 (passed/completed)
    reason2 = LoopRunner.process_step_result(run, spec, {"status": "passed", "cost_usd": 0.30})
    assert reason2 == "Loop completed successfully (goal met)."
    assert (evidence_dir / "iterations" / "002.json").exists()
    assert (evidence_dir / "report.md").exists()
    assert run.status == "passed"

    # Verify report content
    report_content = (evidence_dir / "report.md").read_text(encoding="utf-8")
    assert "Niyam LoopOps Run Report: ev-test-loop" in report_content
    assert run.id in report_content
    assert "- **Status**: `PASSED`" in report_content
    assert "- **Total Iterations**: 2 / 3" in report_content
    assert "- **Total Cost (USD)**: $0.80" in report_content


def test_cli_loop_report_and_evidence(tmp_path: Path) -> None:
    """Should successfully run report and bundle CLI commands."""
    runner = CliRunner()
    spec_file = tmp_path / "spec.yaml"
    starter_spec = generate_starter_spec("cli-ev-loop", "code-change")
    spec_file.write_text(starter_spec, encoding="utf-8")

    # 1. Run the loop simulation to generate evidence
    run_res = runner.invoke(app, ["loop", "run", str(spec_file), "--scenario", "success"])
    assert run_res.exit_code == 0

    # Parse run ID from output or search for it in run.json
    loops_dir = tmp_path / ".niyam" / "evidence" / "loops" / "cli-ev-loop"
    run_json_path = list(loops_dir.glob("**/run.json"))[0]
    with open(run_json_path, encoding="utf-8") as f:
        run_data = json.load(f)
    loop_id = run_data["id"]

    # 2. Test niyam loop report
    report_res = runner.invoke(app, ["loop", "report", loop_id])
    assert report_res.exit_code == 0
    assert "Niyam LoopOps Run Report: cli-ev-loop" in report_res.stdout
    assert "- **Status**: `PASSED`" in report_res.stdout

    # Test HTML report format
    report_html_res = runner.invoke(app, ["loop", "report", loop_id, "--format", "html"])
    assert report_html_res.exit_code == 0
    assert "<!DOCTYPE html>" in report_html_res.stdout
    assert "Niyam LoopOps Report: cli-ev-loop" in report_html_res.stdout

    # Test report --output
    out_file = tmp_path / "custom_report.md"
    report_out_res = runner.invoke(app, ["loop", "report", loop_id, "--output", str(out_file)])
    assert report_out_res.exit_code == 0
    assert "PASS: Report written to" in report_out_res.stdout
    assert out_file.exists()
    assert "- **Status**: `PASSED`" in out_file.read_text(encoding="utf-8")

    # 3. Test niyam loop evidence --bundle
    zip_bundle = tmp_path / "bundle.zip"
    bundle_res = runner.invoke(app, ["loop", "evidence", loop_id, "--bundle", str(zip_bundle)])
    assert bundle_res.exit_code == 0
    assert "PASS: Evidence bundle created at" in bundle_res.stdout
    assert zip_bundle.exists()

    # Test bundle extension auto-appending
    zip_bundle_no_ext = tmp_path / "bundle_no_ext"
    bundle_res_no_ext = runner.invoke(app, ["loop", "evidence", loop_id, "--bundle", str(zip_bundle_no_ext)])
    assert bundle_res_no_ext.exit_code == 0
    assert (tmp_path / "bundle_no_ext.zip").exists()


def test_loopops_policy_integration_protected_files(tmp_path: Path) -> None:
    """Should correctly detect write attempts to protected files and enforce them."""
    # Setup protected files in niyam config
    config_data = {
        "version": "0.1.0",
        "governance": {
            "guard": {
                "protected_files": ["src/auth/**", "config/*.json"]
            }
        }
    }
    with open(tmp_path / ".niyam" / "niyam.yaml", "w") as f:
        yaml.dump(config_data, f)

    spec_data = {
        "apiVersion": "niyam.dev/v1",
        "kind": "LoopSpec",
        "metadata": {
            "name": "policy-test",
            "owner": "platform",
            "riskTier": "medium"
        },
        "goal": {
            "type": "testing",
            "description": "Policy integration testing"
        },
        "budgets": {
            "maxIterations": 3
        }
    }
    spec = LoopSpec.model_validate(spec_data)
    run = LoopRunner.initialize_run(spec)

    # 1. Test modifying a clean file (allowed)
    result = LoopRunner.process_step_result(
        run, spec, {
            "status": "success",
            "files_changed": ["src/clean.py"]
        }
    )
    assert result is None
    assert run.status == "running"

    # 2. Test modifying a protected file (should transition to requires_approval)
    result = LoopRunner.process_step_result(
        run, spec, {
            "status": "success",
            "files_changed": ["src/auth/login.py"]
        }
    )
    assert "Requires human approval" in result
    assert run.status == "requires_approval"

    # Verify policy-results.json trace exists and lists the decision
    evidence_dir = tmp_path / run.evidence_path
    with open(evidence_dir / "artifacts" / "policy-results.json", encoding="utf-8") as f:
        policy_res = json.load(f)
    assert policy_res["requires_approval"] is True
    assert len(policy_res["decisions"]) == 1
    assert policy_res["decisions"][0]["ruleId"] == "protected_file:src/auth/**"
    assert policy_res["decisions"][0]["result"] == "approval_required"


def test_loopops_policy_integration_unapproved_mcp_tools(tmp_path: Path) -> None:
    """Should check MCP tools against registry and block or require approval based on risk."""
    # Write mock MCP registry
    mcp_data = {
        "schema_version": "1.0.0",
        "tools": {
            "my_mcp/critical_tool": {
                "name": "my_mcp/critical_tool",
                "type": "mcp_server",
                "risk_level": "critical",
                "approved": False
            },
            "my_mcp/medium_tool": {
                "name": "my_mcp/medium_tool",
                "type": "mcp_server",
                "risk_level": "medium",
                "approved": False
            }
        }
    }
    with open(tmp_path / ".niyam" / "mcp-registry.json", "w") as f:
        json.dump(mcp_data, f)

    spec_data = {
        "apiVersion": "niyam.dev/v1",
        "kind": "LoopSpec",
        "metadata": {
            "name": "mcp-policy-test",
            "owner": "platform",
            "riskTier": "medium"
        },
        "goal": {
            "type": "testing",
            "description": "MCP Tool testing"
        },
        "budgets": {
            "maxIterations": 3
        }
    }
    spec = LoopSpec.model_validate(spec_data)

    # 1. Medium risk unapproved tool -> requires_approval
    run_medium = LoopRunner.initialize_run(spec)
    result = LoopRunner.process_step_result(
        run_medium, spec, {
            "status": "success",
            "tools_used": ["my_mcp/medium_tool"]
        }
    )
    assert "Requires human approval" in result
    assert run_medium.status == "requires_approval"

    # 2. Critical risk unapproved tool -> failed (blocked)
    run_critical = LoopRunner.initialize_run(spec)
    result = LoopRunner.process_step_result(
        run_critical, spec, {
            "status": "success",
            "tools_used": ["my_mcp/critical_tool"]
        }
    )
    assert "Blocked by policy" in result
    assert run_critical.status == "failed"


def test_loopops_policy_integration_evidence(tmp_path: Path) -> None:
    """Should block or warn when a step is missing required evidence."""
    spec_data = {
        "apiVersion": "niyam.dev/v1",
        "kind": "LoopSpec",
        "metadata": {
            "name": "ev-policy-test",
            "owner": "platform",
            "riskTier": "high"
        },
        "goal": {
            "type": "testing",
            "description": "Required evidence testing"
        },
        "steps": [
            {
                "name": "audit",
                "action": "run_audit",
                "requiredEvidence": ["audit_report"]
            }
        ],
        "budgets": {
            "maxIterations": 3
        }
    }
    spec = LoopSpec.model_validate(spec_data)

    # High risk loop -> missing evidence should block (failed)
    run_high = LoopRunner.initialize_run(spec)
    result = LoopRunner.process_step_result(
        run_high, spec, {
            "step_name": "audit",
            "status": "success",
            "evidence": [] # missing audit_report
        }
    )
    assert "Blocked by policy" in result
    assert run_high.status == "failed"

    # Medium risk loop -> missing evidence should only warn (loop runs successfully)
    spec_data["metadata"]["riskTier"] = "medium"
    spec_medium = LoopSpec.model_validate(spec_data)
    run_medium = LoopRunner.initialize_run(spec_medium)
    result = LoopRunner.process_step_result(
        run_medium, spec_medium, {
            "step_name": "audit",
            "status": "success",
            "evidence": [] # missing audit_report
        }
    )
    assert result is None
    assert run_medium.status == "running"
    
    # Assert decision trace has a warn outcome
    evidence_dir = tmp_path / run_medium.evidence_path
    with open(evidence_dir / "iterations" / "001.json", encoding="utf-8") as f:
        trace = json.load(f)
    assert trace["policyDecisions"][0]["result"] == "warn"


def test_loopops_policy_integration_exceptions(tmp_path: Path) -> None:
    """Should downgrade policy block/approvals to allow when active exceptions exist."""
    # Setup protected files and unapproved tool
    config_data = {
        "version": "0.1.0",
        "governance": {
            "guard": {
                "protected_files": ["src/auth/**"]
            }
        }
    }
    with open(tmp_path / ".niyam" / "niyam.yaml", "w") as f:
        yaml.dump(config_data, f)

    mcp_data = {
        "schema_version": "1.0.0",
        "tools": {
            "my_mcp/critical_tool": {
                "name": "my_mcp/critical_tool",
                "type": "mcp_server",
                "risk_level": "critical",
                "approved": False
            }
        }
    }
    with open(tmp_path / ".niyam" / "mcp-registry.json", "w") as f:
        json.dump(mcp_data, f)

    # Register exceptions
    exceptions_dir = tmp_path / ".niyam" / "governance"
    exceptions_dir.mkdir(parents=True, exist_ok=True)
    with open(exceptions_dir / "policy-exceptions.jsonl", "w") as f:
        # Exception for the protected file
        f.write(json.dumps({
            "id": "EX-FILE",
            "pattern": "src/auth/**",
            "accepted_by": "security-officer",
            "reason": "Temporary file access exception for test",
            "created_at": "2026-06-17T12:00:00Z"
        }) + "\n")
        # Exception for the tool
        f.write(json.dumps({
            "id": "EX-TOOL",
            "pattern": "my_mcp/critical_tool",
            "accepted_by": "security-officer",
            "reason": "Temporary tool exception for test",
            "created_at": "2026-06-17T12:00:00Z"
        }) + "\n")

    spec_data = {
        "apiVersion": "niyam.dev/v1",
        "kind": "LoopSpec",
        "metadata": {
            "name": "exception-test",
            "owner": "platform",
            "riskTier": "high"
        },
        "goal": {
            "type": "testing",
            "description": "Risk Exceptions testing"
        },
        "budgets": {
            "maxIterations": 3
        }
    }
    spec = LoopSpec.model_validate(spec_data)
    run = LoopRunner.initialize_run(spec)

    # Running a step with BOTH policy violations should be allowed since exceptions are active
    result = LoopRunner.process_step_result(
        run, spec, {
            "status": "success",
            "files_changed": ["src/auth/login.py"],
            "tools_used": ["my_mcp/critical_tool"]
        }
    )
    assert result is None
    assert run.status == "running"

    # Verify trace shows "allow" for both
    evidence_dir = tmp_path / run.evidence_path
    with open(evidence_dir / "iterations" / "001.json", encoding="utf-8") as f:
        trace = json.load(f)
    decisions = trace["policyDecisions"]
    assert len(decisions) == 2
    assert decisions[0]["result"] == "allow"
    assert "EX-FILE" in decisions[0]["reason"]
    assert decisions[1]["result"] == "allow"
    assert "EX-TOOL" in decisions[1]["reason"]


# ============================================================================
# Phase 5: Cost & Token Tracking Tests
# ============================================================================


def test_token_budget_enforcement(tmp_path: Path) -> None:
    """Should stop the run when combined tokens exceed maxTokens budget."""
    spec_data = {
        "apiVersion": "niyam.dev/v1",
        "kind": "LoopSpec",
        "metadata": {
            "name": "token-budget-test",
            "owner": "platform",
            "riskTier": "low"
        },
        "goal": {
            "type": "testing",
            "description": "Token budget enforcement"
        },
        "budgets": {
            "maxIterations": 10,
            "maxTokens": 5000,
            "maxCostUsd": 10.0
        },
        "stopConditions": []
    }
    spec = LoopSpec.model_validate(spec_data)
    run = LoopRunner.initialize_run(spec)

    # Iteration 1: 3000 tokens (within budget)
    result1 = LoopRunner.process_step_result(
        run, spec, {
            "status": "success",
            "cost_usd": 0.10,
            "tokens_in": 2000,
            "tokens_out": 1000,
        }
    )
    assert result1 is None
    assert run.status == "running"
    assert run.tokens_in == 2000
    assert run.tokens_out == 1000

    # Iteration 2: 3500 more tokens (total 6500 > 5000 budget)
    result2 = LoopRunner.process_step_result(
        run, spec, {
            "status": "success",
            "cost_usd": 0.12,
            "tokens_in": 2500,
            "tokens_out": 1000,
        }
    )
    assert result2 is not None
    assert "Max token budget" in result2
    assert "5,000" in result2
    assert "6,500" in result2
    assert run.status == "stopped"
    assert run.tokens_in == 4500
    assert run.tokens_out == 2000


def test_cost_estimation_from_pricing(tmp_path: Path) -> None:
    """Should estimate cost via Niyam pricing when cost_usd is not provided but model + tokens are."""
    spec_data = {
        "apiVersion": "niyam.dev/v1",
        "kind": "LoopSpec",
        "metadata": {
            "name": "cost-estimate-test",
            "owner": "platform",
            "riskTier": "low"
        },
        "goal": {
            "type": "testing",
            "description": "Cost estimation testing"
        },
        "budgets": {
            "maxIterations": 5,
            "maxCostUsd": 10.0
        },
        "stopConditions": []
    }
    spec = LoopSpec.model_validate(spec_data)
    run = LoopRunner.initialize_run(spec)

    # Pass model + tokens but NO explicit cost_usd
    # Using "claude-haiku" from DEFAULT_PRICING: input=$0.25/M, output=$1.25/M
    result = LoopRunner.process_step_result(
        run, spec, {
            "status": "success",
            "model": "claude-haiku",
            "tokens_in": 1000,
            "tokens_out": 500,
        }
    )
    assert result is None
    assert run.status == "running"

    # Expected cost: (1000 * 0.25 / 1_000_000) + (500 * 1.25 / 1_000_000)
    # = 0.00025 + 0.000625 = 0.000875
    assert run.cost_usd > 0.0
    assert abs(run.cost_usd - 0.000875) < 0.0001

    # Verify trace records the estimated cost
    evidence_dir = tmp_path / run.evidence_path
    with open(evidence_dir / "iterations" / "001.json", encoding="utf-8") as f:
        trace = json.load(f)
    assert trace["tokensIn"] == 1000
    assert trace["tokensOut"] == 500
    assert trace["costUsd"] > 0.0


def test_wasted_cost_calculation(tmp_path: Path) -> None:
    """Should set wasted_cost_usd for failed/stopped runs but not for passed runs."""
    spec_data = {
        "apiVersion": "niyam.dev/v1",
        "kind": "LoopSpec",
        "metadata": {
            "name": "wasted-cost-test",
            "owner": "platform",
            "riskTier": "low"
        },
        "goal": {
            "type": "testing",
            "description": "Wasted cost testing"
        },
        "budgets": {
            "maxIterations": 5,
            "maxCostUsd": 10.0
        },
        "stopConditions": []
    }
    spec = LoopSpec.model_validate(spec_data)

    # 1. Passed run: wasted_cost should remain 0
    run_passed = LoopRunner.initialize_run(spec)
    LoopRunner.process_step_result(
        run_passed, spec, {"status": "passed", "cost_usd": 0.50}
    )
    assert run_passed.status == "passed"
    assert run_passed.wasted_cost_usd == 0.0

    # 2. Failed run: wasted_cost should equal total cost
    run_failed = LoopRunner.initialize_run(spec)
    LoopRunner.process_step_result(
        run_failed, spec, {"status": "success", "cost_usd": 0.30}
    )
    LoopRunner.process_step_result(
        run_failed, spec, {"status": "failure", "cost_usd": 0.20, "error": "crash"}
    )
    # Loop is still running after one failure (no stop condition met)
    # Force it to fail explicitly
    run_failed2 = LoopRunner.initialize_run(spec)
    LoopRunner.process_step_result(
        run_failed2, spec, {"status": "failed", "cost_usd": 0.75}
    )
    assert run_failed2.status == "failed"
    assert run_failed2.wasted_cost_usd == 0.75

    # 3. Stopped run: wasted_cost should equal total cost
    spec_stopped = LoopSpec.model_validate({
        **spec_data,
        "budgets": {"maxIterations": 1, "maxCostUsd": 10.0},
    })
    run_stopped = LoopRunner.initialize_run(spec_stopped)
    LoopRunner.process_step_result(
        run_stopped, spec_stopped, {"status": "success", "cost_usd": 0.40}
    )
    assert run_stopped.status == "stopped"
    assert run_stopped.wasted_cost_usd == 0.40


def test_finops_report_section(tmp_path: Path) -> None:
    """Should include FinOps & Efficiency Analytics section in the generated report."""
    spec_data = {
        "apiVersion": "niyam.dev/v1",
        "kind": "LoopSpec",
        "metadata": {
            "name": "finops-report-test",
            "owner": "platform",
            "riskTier": "low"
        },
        "goal": {
            "type": "testing",
            "description": "FinOps report testing"
        },
        "budgets": {
            "maxIterations": 5,
            "maxTokens": 100000,
            "maxCostUsd": 10.0
        },
        "stopConditions": []
    }
    spec = LoopSpec.model_validate(spec_data)
    run = LoopRunner.initialize_run(spec)

    # Iteration 1
    LoopRunner.process_step_result(
        run, spec, {
            "status": "success",
            "cost_usd": 0.50,
            "tokens_in": 3000,
            "tokens_out": 1500,
        }
    )
    # Iteration 2 (passed)
    LoopRunner.process_step_result(
        run, spec, {
            "status": "passed",
            "cost_usd": 0.30,
            "tokens_in": 2000,
            "tokens_out": 1000,
        }
    )

    assert run.status == "passed"
    evidence_dir = tmp_path / run.evidence_path
    report = (evidence_dir / "report.md").read_text(encoding="utf-8")

    # Verify FinOps section exists
    assert "## FinOps & Efficiency Analytics" in report
    assert "**Total Tokens**: 7,500" in report
    assert "Input: 5,000" in report
    assert "Output: 2,500" in report
    assert "**Avg Cost/Iteration**: $0.4000" in report
    assert "**Wasted Cost (USD)**: $0.00" in report
    assert "**Efficiency Status**: Efficient" in report

    # Max Tokens budget should also appear in Budgets section
    assert "**Max Tokens**: 100,000" in report


# ============================================================================
# Phase 6: AI Reviewer / Critic Loop Tests
# ============================================================================


def test_evaluator_schema_validation() -> None:
    """Should validate evaluator constraints: ai_critic needs actor, command needs command."""
    from niyam.core.loopops import validate_loop_spec

    base = {
        "apiVersion": "niyam.dev/v1",
        "kind": "LoopSpec",
        "metadata": {"name": "ev-val-test", "owner": "platform"},
        "goal": {"type": "testing", "description": "Evaluator validation"},
        "actors": {"reviewer": "gemini"},
        "steps": [{"name": "s1", "action": "act"}],
        "budgets": {"maxIterations": 3},
    }

    # 1. Valid evaluators — no errors
    valid_spec = {
        **base,
        "evaluators": [
            {"name": "sec-review", "type": "ai_critic", "actor": "gemini", "required": True},
            {"name": "test-run", "type": "command", "command": "npm test", "required": True},
        ]
    }
    errors = validate_loop_spec(valid_spec)
    assert not errors

    # 2. ai_critic without actor
    bad_spec_1 = {
        **base,
        "evaluators": [
            {"name": "bad-critic", "type": "ai_critic", "required": True},
        ]
    }
    errors = validate_loop_spec(bad_spec_1)
    assert any("must specify an 'actor'" in e for e in errors)

    # 3. command without command
    bad_spec_2 = {
        **base,
        "evaluators": [
            {"name": "bad-cmd", "type": "command", "required": True},
        ]
    }
    errors = validate_loop_spec(bad_spec_2)
    assert any("must specify a 'command'" in e for e in errors)

    # 4. ai_critic with unknown actor
    bad_spec_3 = {
        **base,
        "evaluators": [
            {"name": "unknown-actor", "type": "ai_critic", "actor": "nonexistent", "required": True},
        ]
    }
    errors = validate_loop_spec(bad_spec_3)
    assert any("unknown actor 'nonexistent'" in e for e in errors)

    # 5. Duplicate evaluator names
    bad_spec_4 = {
        **base,
        "evaluators": [
            {"name": "dup-eval", "type": "command", "command": "cmd1"},
            {"name": "dup-eval", "type": "command", "command": "cmd2"},
        ]
    }
    errors = validate_loop_spec(bad_spec_4)
    assert any("duplicated" in e for e in errors)


def test_evaluator_required_fail_blocks_loop(tmp_path: Path) -> None:
    """Should block loop when a required evaluator fails (step_status = failure)."""
    spec_data = {
        "apiVersion": "niyam.dev/v1",
        "kind": "LoopSpec",
        "metadata": {"name": "eval-block-test", "owner": "platform", "riskTier": "low"},
        "goal": {"type": "testing", "description": "Required evaluator blocking"},
        "actors": {"reviewer": "gemini"},
        "steps": [{"name": "implement", "action": "modify"}],
        "budgets": {"maxIterations": 5},
        "evaluators": [
            {
                "name": "security-review",
                "type": "ai_critic",
                "actor": "gemini",
                "required": True,
                "criteria": "Check for vulnerabilities",
            }
        ],
    }
    spec = LoopSpec.model_validate(spec_data)
    run = LoopRunner.initialize_run(spec)

    # Step that fails -> evaluator will also fail -> required -> should block
    result = LoopRunner.process_step_result(
        run, spec, {"status": "failure", "cost_usd": 0.10, "error": "CompilationError"}
    )
    assert result is not None
    assert "Blocked by evaluator" in result
    assert "security-review" in result
    assert run.status == "failed"


def test_evaluator_optional_fail_warns(tmp_path: Path) -> None:
    """Should continue with warning when an optional evaluator fails."""
    spec_data = {
        "apiVersion": "niyam.dev/v1",
        "kind": "LoopSpec",
        "metadata": {"name": "eval-warn-test", "owner": "platform", "riskTier": "low"},
        "goal": {"type": "testing", "description": "Optional evaluator warning"},
        "actors": {"reviewer": "gemini"},
        "steps": [{"name": "implement", "action": "modify"}],
        "budgets": {"maxIterations": 5},
        "evaluators": [
            {
                "name": "style-check",
                "type": "command",
                "command": "npx eslint .",
                "required": False,
            }
        ],
    }
    spec = LoopSpec.model_validate(spec_data)
    run = LoopRunner.initialize_run(spec)

    # Step failure -> optional evaluator fails -> loop should NOT be blocked
    result = LoopRunner.process_step_result(
        run, spec, {"status": "failure", "cost_usd": 0.10, "error": "LintError"}
    )
    # Loop not blocked (evaluator is optional), but step itself is a failure
    # The run should still be running (one failure doesn't terminate without stop condition)
    assert run.status == "running"
    assert result is None

    # Verify observation includes evaluator warning
    evidence_dir = tmp_path / run.evidence_path
    with open(evidence_dir / "iterations" / "001.json", encoding="utf-8") as f:
        trace = json.load(f)
    obs_types = [o["type"] for o in trace["observations"]]
    assert "evaluator_warn" in obs_types


def test_evaluator_high_risk_requires_approval(tmp_path: Path) -> None:
    """Should require human approval when an evaluator flags a result as high risk."""
    spec_data = {
        "apiVersion": "niyam.dev/v1",
        "kind": "LoopSpec",
        "metadata": {"name": "eval-high-risk-test", "owner": "platform", "riskTier": "low"},
        "goal": {"type": "testing", "description": "High-risk evaluator requires approval"},
        "actors": {"reviewer": "gemini"},
        "steps": [{"name": "implement", "action": "modify"}],
        "budgets": {"maxIterations": 5},
        "evaluators": [
            {
                "name": "security-review",
                "type": "ai_critic",
                "actor": "gemini",
                "required": True,
                "criteria": "Check for security issues",
            }
        ],
    }
    spec = LoopSpec.model_validate(spec_data)
    run = LoopRunner.initialize_run(spec)

    # Step returns 'high_risk' -> evaluator returns high risk level -> should require approval
    result = LoopRunner.process_step_result(
        run, spec, {"status": "high_risk", "cost_usd": 0.10}
    )
    
    assert result is not None
    assert "Requires human approval" in result
    assert "security-review" in result
    assert "high-risk result" in result
    assert run.status == "requires_approval"

def test_evaluator_results_in_evidence(tmp_path: Path) -> None:
    """Should write evaluations/<index>.json to evidence directory."""
    spec_data = {
        "apiVersion": "niyam.dev/v1",
        "kind": "LoopSpec",
        "metadata": {"name": "eval-evidence-test", "owner": "platform", "riskTier": "low"},
        "goal": {"type": "testing", "description": "Evaluator evidence"},
        "actors": {"reviewer": "gemini"},
        "steps": [{"name": "implement", "action": "modify"}],
        "budgets": {"maxIterations": 5},
        "evaluators": [
            {"name": "sec-review", "type": "ai_critic", "actor": "gemini", "required": True},
            {"name": "tests", "type": "command", "command": "pytest", "required": True},
        ],
    }
    spec = LoopSpec.model_validate(spec_data)
    run = LoopRunner.initialize_run(spec)

    # Successful step -> evaluators pass
    LoopRunner.process_step_result(
        run, spec, {"status": "success", "cost_usd": 0.20}
    )

    evidence_dir = tmp_path / run.evidence_path

    # Check evaluations directory exists and has file
    eval_file = evidence_dir / "evaluations" / "001.json"
    assert eval_file.exists()

    with open(eval_file, encoding="utf-8") as f:
        eval_data = json.load(f)
    assert eval_data["iteration"] == 1
    assert len(eval_data["results"]) == 2
    assert eval_data["results"][0]["evaluatorName"] == "sec-review"
    assert eval_data["results"][0]["result"] == "pass"
    assert eval_data["results"][1]["evaluatorName"] == "tests"
    assert eval_data["results"][1]["result"] == "pass"


def test_evaluator_report_section(tmp_path: Path) -> None:
    """Should include Evaluator Results section in the generated report."""
    spec_data = {
        "apiVersion": "niyam.dev/v1",
        "kind": "LoopSpec",
        "metadata": {"name": "eval-report-test", "owner": "platform", "riskTier": "low"},
        "goal": {"type": "testing", "description": "Evaluator report"},
        "actors": {"reviewer": "gemini"},
        "steps": [{"name": "implement", "action": "modify"}],
        "budgets": {"maxIterations": 5},
        "evaluators": [
            {
                "name": "security-review",
                "type": "ai_critic",
                "actor": "gemini",
                "required": True,
                "criteria": "Check for security issues",
            },
            {
                "name": "lint-check",
                "type": "command",
                "command": "eslint .",
                "required": False,
            },
        ],
    }
    spec = LoopSpec.model_validate(spec_data)
    run = LoopRunner.initialize_run(spec)

    # Run to completion
    LoopRunner.process_step_result(run, spec, {"status": "passed", "cost_usd": 0.30})

    assert run.status == "passed"
    evidence_dir = tmp_path / run.evidence_path
    report = (evidence_dir / "report.md").read_text(encoding="utf-8")

    assert "## Evaluator Results" in report
    assert "**security-review** (ai_critic, Required)" in report
    assert "Criteria: Check for security issues" in report
    assert "**lint-check** (command, Optional)" in report
