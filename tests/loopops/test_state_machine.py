from __future__ import annotations

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
