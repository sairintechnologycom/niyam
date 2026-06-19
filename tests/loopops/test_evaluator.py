from __future__ import annotations

import json
from pathlib import Path
from niyam.core.loopops import LoopRunner, LoopSpec, validate_loop_spec

def test_evaluator_schema_validation() -> None:
    """LOOP-EVAL-001: Validate evaluator schema fields and validation constraints."""
    base = {
        "apiVersion": "niyam.dev/v1",
        "kind": "LoopSpec",
        "metadata": {"name": "ev-val-test", "owner": "platform"},
        "goal": {"type": "testing", "description": "Evaluator validation"},
        "actors": {"reviewer": "gemini"},
        "steps": [{"name": "s1", "action": "act"}],
        "budgets": {"maxIterations": 3},
    }

    # Valid evaluators
    valid_spec = {
        **base,
        "evaluators": [
            {"name": "sec-review", "type": "ai_critic", "actor": "gemini", "required": True},
            {"name": "test-run", "type": "command", "command": "npm test", "required": True},
        ]
    }
    errors = validate_loop_spec(valid_spec)
    assert not errors

    # ai_critic without actor
    bad_spec_1 = {
        **base,
        "evaluators": [
            {"name": "bad-critic", "type": "ai_critic", "required": True},
        ]
    }
    errors = validate_loop_spec(bad_spec_1)
    assert any("must specify an 'actor'" in e for e in errors)

    # command without command
    bad_spec_2 = {
        **base,
        "evaluators": [
            {"name": "bad-cmd", "type": "command", "required": True},
        ]
    }
    errors = validate_loop_spec(bad_spec_2)
    assert any("must specify a 'command'" in e for e in errors)

def test_evaluator_required_fail_blocks_loop(tmp_path: Path) -> None:
    """LOOP-EVAL-002: Should block loop when a required evaluator fails."""
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

    result = LoopRunner.process_step_result(
        run, spec, {"status": "failure", "cost_usd": 0.10, "error": "CompilationError"}
    )
    assert result is not None
    assert "Blocked by evaluator" in result
    assert "security-review" in result
    assert run.status == "blocked"

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

    result = LoopRunner.process_step_result(
        run, spec, {"status": "failure", "cost_usd": 0.10, "error": "LintError"}
    )
    assert run.status == "retrying"
    assert result is None

    # Verify warning in trace
    evidence_dir = tmp_path / run.evidence_path
    with open(evidence_dir / "iterations" / "001.json", encoding="utf-8") as f:
        trace = json.load(f)
    obs_types = [o["type"] for o in trace["observations"]]
    assert "evaluator_warn" in obs_types

def test_evaluator_high_risk_requires_approval(tmp_path: Path) -> None:
    """Should require human approval when an evaluator flags high risk."""
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

    LoopRunner.process_step_result(
        run, spec, {"status": "success", "cost_usd": 0.20}
    )

    evidence_dir = tmp_path / run.evidence_path
    eval_file = evidence_dir / "evaluations" / "001.json"
    assert eval_file.exists()

    with open(eval_file, encoding="utf-8") as f:
        eval_data = json.load(f)
    assert eval_data["iteration"] == 1
    assert len(eval_data["results"]) == 2
    assert eval_data["results"][0]["evaluatorName"] == "sec-review"
    assert eval_data["results"][0]["result"] == "pass"

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
        ],
    }
    spec = LoopSpec.model_validate(spec_data)
    run = LoopRunner.initialize_run(spec)

    LoopRunner.process_step_result(run, spec, {"status": "passed", "cost_usd": 0.30})
    evidence_dir = tmp_path / run.evidence_path
    report = (evidence_dir / "report.md").read_text(encoding="utf-8")

    assert "## Evaluator Results" in report
    assert "**security-review** (ai_critic, Required)" in report
    assert "Criteria: Check for security issues" in report
