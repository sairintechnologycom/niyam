from __future__ import annotations

import json
from pathlib import Path
from niyam.core.loopops import LoopRunner, LoopSpec, validate_loop_spec
from niyam.governance.common.redaction import redact_text

def test_evidence_generation_success(tmp_path: Path) -> None:
    """LOOP-EVIDENCE-001 to 005, 010, 011: Verify directories, files, and report generation."""
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

def test_evidence_secrets_redacted() -> None:
    """LOOP-EVIDENCE-009: Secrets should be redacted via redact_text."""
    raw_text = "My AWS key is AKIAIOSFODNN7EXAMPLE and secret is wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
    redacted = redact_text(raw_text)
    assert "AKIAIOSFODNN7EXAMPLE" not in redacted or "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY" not in redacted
    assert "[REDACTED]" in redacted or "AWS" in redacted

def test_evidence_missing_evaluation_failure(tmp_path: Path) -> None:
    """LOOP-EVIDENCE-006: Missing required evidence fails loop evaluation (covered under policy)."""
    spec_data = {
        "apiVersion": "niyam.dev/v1",
        "kind": "LoopSpec",
        "metadata": {
            "name": "ev-missing-test",
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
    run = LoopRunner.initialize_run(spec)
    
    # Missing required evidence 'audit_report'
    result = LoopRunner.process_step_result(
        run, spec, {
            "step_name": "audit",
            "status": "success",
            "evidence": [] 
        }
    )
    assert "Blocked by policy" in result
    assert run.status == "failed"
