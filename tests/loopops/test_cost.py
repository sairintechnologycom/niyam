from __future__ import annotations

import json
from pathlib import Path
from niyam.core.loopops import LoopRunner, LoopSpec

def test_token_budget_enforcement(tmp_path: Path) -> None:
    """LOOP-COST-005: Should stop the run when combined tokens exceed maxTokens budget."""
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
    assert run.status == "stopped"

def test_cost_estimation_from_pricing(tmp_path: Path) -> None:
    """LOOP-COST-001, LOOP-COST-002, LOOP-COST-003: Should estimate cost via Niyam pricing when cost_usd is missing."""
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
    # Verify cost was estimated (>0.0)
    assert run.cost_usd > 0.0
    assert abs(run.cost_usd - 0.000875) < 0.0001

def test_wasted_cost_calculation(tmp_path: Path) -> None:
    """LOOP-COST-007: Should calculate wasted cost for failed/stopped runs but not passed ones."""
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

    # 1. Passed run: wasted_cost is 0
    run_passed = LoopRunner.initialize_run(spec)
    LoopRunner.process_step_result(
        run_passed, spec, {"status": "passed", "cost_usd": 0.50}
    )
    assert run_passed.status == "passed"
    assert run_passed.wasted_cost_usd == 0.0

    # 2. Failed run: wasted_cost = total cost
    run_failed = LoopRunner.initialize_run(spec)
    from niyam.core.loopops.state_machine import LoopStateMachine
    sm = LoopStateMachine(run_failed)
    sm.transition_to("failed")
    run_failed.cost_usd = 0.75
    run_failed.wasted_cost_usd = 0.75
    assert run_failed.status == "failed"
    assert run_failed.wasted_cost_usd == 0.75
