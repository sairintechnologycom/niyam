from __future__ import annotations

from pathlib import Path
from niyam.core.loopops import LoopRunner, LoopSpec

def test_runner_initialize_run(tmp_path: Path) -> None:
    """LOOP-RUNNER-001: Should correctly initialize a LoopRun directory structure."""
    spec_data = {
        "apiVersion": "niyam.dev/v1",
        "kind": "LoopSpec",
        "metadata": {
            "name": "run-test-loop",
            "owner": "platform",
            "riskTier": "low"
        },
        "goal": {
            "type": "testing",
            "description": "Orchestration testing"
        },
        "budgets": {
            "maxIterations": 3
        }
    }
    spec = LoopSpec.model_validate(spec_data)
    run = LoopRunner.initialize_run(spec)

    assert run.id.startswith("LR-")
    assert run.spec_name == "run-test-loop"
    assert run.status == "pending"

    # Verify directory exists
    evidence_dir = tmp_path / run.evidence_path
    assert evidence_dir.exists()
    assert (evidence_dir / "iterations").exists()
    assert (evidence_dir / "artifacts").exists()
    assert (evidence_dir / "run.json").exists()
    assert (evidence_dir / "loop-spec.yaml").exists()

def test_runner_process_step_result_success(tmp_path: Path) -> None:
    """Should transition to evaluating or running after processing step results."""
    spec_data = {
        "apiVersion": "niyam.dev/v1",
        "kind": "LoopSpec",
        "metadata": {
            "name": "run-success-loop",
            "owner": "platform",
            "riskTier": "low"
        },
        "goal": {
            "type": "testing",
            "description": "Success simulation"
        },
        "budgets": {
            "maxIterations": 3
        }
    }
    spec = LoopSpec.model_validate(spec_data)
    run = LoopRunner.initialize_run(spec)

    # Process step 1 success
    reason = LoopRunner.process_step_result(run, spec, {"status": "success", "cost_usd": 0.2})
    assert reason is None
    assert run.status == "running"
    assert run.iteration_count == 1
    assert run.cost_usd == 0.2

    # Process step 2 passed/completion
    reason2 = LoopRunner.process_step_result(run, spec, {"status": "passed", "cost_usd": 0.1})
    assert reason2 == "Loop completed successfully (goal met)."
    assert run.status == "passed"
    assert run.iteration_count == 2
    import pytest
    assert run.cost_usd == pytest.approx(0.3)
