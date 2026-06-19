from __future__ import annotations

from pathlib import Path

import pytest
from niyam.core.loopops import LoopRun, LoopStateMachine, LoopBudgets


def test_state_machine_transitions() -> None:
    """LOOP-STATE-001 to 012: Enforce valid state transitions."""
    run = LoopRun(
        id="LR-123456",
        specName="test-loop",
        goal="testing transitions",
        status="pending",
        startedAt="2026-06-17T12:00:00Z",
        maxIterations=5,
    )
    sm = LoopStateMachine(run)

    # Starts as pending
    assert run.status == "pending"
    
    # Transition to running
    sm.transition_to("running")
    assert run.status == "running"

    # Transition to evaluating
    sm.transition_to("evaluating")
    assert run.status == "evaluating"

    # Transition back to running
    sm.transition_to("running")
    assert run.status == "running"

    # Transition to stopped
    sm.transition_to("stopped")
    assert run.status == "stopped"

    # Stopped is terminal
    with pytest.raises(ValueError, match="Invalid transition"):
        sm.transition_to("running")

def test_state_machine_budgets() -> None:
    """Should correctly stop when budgets are exceeded."""
    # Iteration limit
    run_iter = LoopRun(
        id="LR-ITER",
        specName="test-loop",
        goal="test",
        status="running",
        startedAt="2026-06-17T12:00:00Z",
        maxIterations=5,
        iterationCount=5,
        costUsd=1.0,
    )
    sm_iter = LoopStateMachine(run_iter)
    budgets = LoopBudgets(maxIterations=5, maxCostUsd=3.0)

    sm_iter.transition_to("evaluating")
    reason = sm_iter.evaluate_budgets(budgets)
    assert reason == "Max iterations (5) exceeded."
    assert run_iter.status == "stopped"

    # Cost limit
    run_cost = LoopRun(
        id="LR-COST",
        specName="test-loop",
        goal="test",
        status="running",
        startedAt="2026-06-17T12:00:00Z",
        maxIterations=5,
        iterationCount=2,
        costUsd=3.50,
    )
    sm_cost = LoopStateMachine(run_cost)
    sm_cost.transition_to("evaluating")
    reason_cost = sm_cost.evaluate_budgets(budgets)
    assert reason_cost == "Max cost budget ($3.00) exceeded."
    assert run_cost.status == "stopped"

def test_state_machine_stop_conditions() -> None:
    """Should evaluate stop conditions correctly."""
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

    # 3. policyViolation == critical
    metrics = {"policyViolation": "critical"}
    assert sm.evaluate_stop_condition("policyViolation == critical", metrics) is True

    # 4. humanApprovalRequired == true
    metrics = {"humanApprovalRequired": True}
    assert sm.evaluate_stop_condition("humanApprovalRequired == true", metrics) is True


def test_budget_max_runtime_minutes_exceeded() -> None:
    """LOOP-BUDGET-RT-001: evaluate_budgets() stops when maxRuntimeMinutes is exceeded."""
    from datetime import datetime, timezone, timedelta

    # Create a run that started 10 minutes ago
    past_start = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
    run = LoopRun(
        id="LR-RTLIM",
        specName="rt-test",
        goal="runtime limit test",
        status="evaluating",
        startedAt=past_start,
        maxIterations=100,
        iterationCount=1,
    )
    sm = LoopStateMachine(run)
    # maxRuntimeMinutes=5 → 10 minutes elapsed → should stop
    budgets = LoopBudgets(maxIterations=100, maxRuntimeMinutes=5)
    reason = sm.evaluate_budgets(budgets)

    assert reason is not None
    assert "Max runtime" in reason
    assert "5m" in reason
    assert run.status == "stopped"


def test_budget_max_runtime_minutes_within_limit() -> None:
    """LOOP-BUDGET-RT-002: evaluate_budgets() continues when within runtime limit."""
    from datetime import datetime, timezone

    run = LoopRun(
        id="LR-RTNOK",
        specName="rt-test",
        goal="runtime within limit",
        status="evaluating",
        startedAt=datetime.now(timezone.utc).isoformat(),
        maxIterations=100,
        iterationCount=1,
    )
    sm = LoopStateMachine(run)
    # maxRuntimeMinutes=60 → just started → should NOT stop
    budgets = LoopBudgets(maxIterations=100, maxRuntimeMinutes=60)
    reason = sm.evaluate_budgets(budgets)

    assert reason is None
    assert run.status == "evaluating"


def test_run_loop_max_attempts_per_step(tmp_path: Path) -> None:
    """LOOP-ATTEMPTS-001: run_loop() stops when a step exceeds its maxAttempts limit."""
    from niyam.core.loopops import LoopSpec, LoopRunner

    spec_data = {
        "apiVersion": "niyam.dev/v1",
        "kind": "LoopSpec",
        "metadata": {"name": "max-attempts-test", "owner": "platform", "riskTier": "low"},
        "goal": {"type": "testing", "description": "max attempts enforcement"},
        # Use claude which simulates success in dry_run/test mode — so the step
        # always succeeds and only maxAttempts terminates the loop.
        "actors": {"implementer": "claude"},
        "steps": [{"name": "build", "action": "implement", "actor": "implementer", "maxAttempts": 2}],
        "budgets": {"maxIterations": 10},
    }
    spec = LoopSpec.model_validate(spec_data)
    run, reason = LoopRunner.run_loop(spec, dry_run=True, repo_root=tmp_path)

    assert run.status == "failed"
    assert reason is not None
    assert "maxAttempts" in reason
    assert "build" in reason
