"""LoopRun State Machine and Data Models for Niyam LoopOps."""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Optional, Literal, Any
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Valid state transitions
VALID_TRANSITIONS: dict[str, set[str]] = {
    "pending": {"running", "stopped", "failed"},
    "running": {"evaluating", "stopped", "failed", "requires_approval"},
    "evaluating": {"running", "passed", "failed", "stopped", "requires_approval"},
    "requires_approval": {"running", "stopped", "failed"},
    "passed": set(),
    "failed": set(),
    "stopped": set(),
}

STOP_CONDITION_REGEX = re.compile(
    r"^([a-zA-Z_][a-zA-Z0-9_]*)\s*(>=|<=|==|!=|>|<)\s*([a-zA-Z0-9_\.]+)$"
)


class LoopObservation(BaseModel):
    """An observation recorded during loop execution."""

    model_config = {"populate_by_name": True, "extra": "allow"}

    type: str
    content: str
    timestamp: str


class LoopPolicyDecision(BaseModel):
    """A policy enforcement decision made during a loop step."""

    model_config = {"populate_by_name": True, "extra": "allow"}

    rule_id: str = Field(..., alias="ruleId")
    result: Literal["allow", "warn", "block", "approval_required"]
    reason: str


class LoopIteration(BaseModel):
    """Execution trace for a single loop iteration."""

    model_config = {"populate_by_name": True, "extra": "allow"}

    id: str
    loop_run_id: str = Field(..., alias="loopRunId")
    index: int
    actor: str
    step_name: str = Field(..., alias="stepName")
    action: str
    started_at: str = Field(..., alias="startedAt")
    completed_at: Optional[str] = Field(None, alias="completedAt")
    input_hash: Optional[str] = Field(None, alias="inputHash")
    output_hash: Optional[str] = Field(None, alias="outputHash")
    tokens_in: Optional[int] = Field(None, alias="tokensIn")
    tokens_out: Optional[int] = Field(None, alias="tokensOut")
    cost_usd: Optional[float] = Field(None, alias="costUsd")
    result: Literal["success", "failure", "warning", "blocked"]
    observations: list[LoopObservation] = Field(default_factory=list)
    policy_decisions: list[LoopPolicyDecision] = Field(
        default_factory=list, alias="policyDecisions"
    )


class LoopRun(BaseModel):
    """Loop execution state database record."""

    model_config = {"populate_by_name": True, "extra": "allow"}

    id: str
    spec_name: str = Field(..., alias="specName")
    goal: str
    status: Literal[
        "pending",
        "running",
        "evaluating",
        "passed",
        "failed",
        "stopped",
        "requires_approval",
    ] = "pending"
    started_at: str = Field(..., alias="startedAt")
    completed_at: Optional[str] = Field(None, alias="completedAt")
    iteration_count: int = Field(0, alias="iterationCount")
    max_iterations: int = Field(..., alias="maxIterations")
    cost_usd: float = Field(0.0, alias="costUsd")
    max_cost_usd: Optional[float] = Field(None, alias="maxCostUsd")
    tokens_in: int = Field(0, alias="tokensIn")
    tokens_out: int = Field(0, alias="tokensOut")
    wasted_cost_usd: float = Field(0.0, alias="wastedCostUsd")
    risk_level: Literal["low", "medium", "high", "critical"] = Field(
        "medium", alias="riskLevel"
    )
    evidence_path: Optional[str] = Field(None, alias="evidencePath")
    consecutive_failures: int = Field(0, alias="consecutiveFailures")
    consecutive_errors: dict[str, int] = Field(
        default_factory=dict, alias="consecutiveErrors"
    )
    signature: Optional[str] = Field(None, alias="signature")
    public_key_pem: Optional[str] = Field(None, alias="publicKeyPem")


class LoopStateMachine:
    """State machine governing state transitions and safety limit checks for a LoopRun."""

    def __init__(self, run: LoopRun) -> None:
        self.run = run

    def transition_to(
        self,
        new_status: Literal[
            "pending",
            "running",
            "evaluating",
            "passed",
            "failed",
            "stopped",
            "requires_approval",
        ],
    ) -> None:
        """Transition the LoopRun status to a new state if valid."""
        current = self.run.status
        allowed = VALID_TRANSITIONS.get(current, set())
        if new_status not in allowed and new_status != current:
            raise ValueError(
                f"Invalid transition from state '{current}' to '{new_status}'."
            )
        self.run.status = new_status

    def evaluate_budgets(self, budgets: Any) -> Optional[str]:
        """Check if execution limits (iterations, cost, tokens) have been exceeded.

        Transitions status to stopped/failed if budget limit is hit.
        Returns the stop reason or None.
        """
        # 1. Check max iterations
        if self.run.iteration_count >= budgets.max_iterations:
            reason = f"Max iterations ({budgets.max_iterations}) exceeded."
            self.transition_to("stopped")
            return reason

        # 2. Check max cost limit
        if (
            budgets.max_cost_usd is not None
            and self.run.cost_usd > budgets.max_cost_usd
        ):
            reason = f"Max cost budget (${budgets.max_cost_usd:.2f}) exceeded."
            self.transition_to("stopped")
            return reason

        # 3. Check max tokens limit (input + output combined)
        if budgets.max_tokens is not None:
            total_tokens = self.run.tokens_in + self.run.tokens_out
            if total_tokens > budgets.max_tokens:
                reason = f"Max token budget ({budgets.max_tokens:,}) exceeded (used {total_tokens:,})."
                self.transition_to("stopped")
                return reason

        # 4. Check max runtime limit
        if budgets.max_runtime_minutes is not None:
            try:
                started = datetime.fromisoformat(self.run.started_at)
                if started.tzinfo is None:
                    started = started.replace(tzinfo=timezone.utc)
                elapsed_minutes = (datetime.now(timezone.utc) - started).total_seconds() / 60
                if elapsed_minutes > budgets.max_runtime_minutes:
                    reason = (
                        f"Max runtime ({budgets.max_runtime_minutes}m) exceeded "
                        f"(elapsed {elapsed_minutes:.1f}m)."
                    )
                    self.transition_to("stopped")
                    return reason
            except Exception:
                logger.debug("Could not evaluate maxRuntimeMinutes budget", exc_info=True)

        return None

    def evaluate_stop_condition(self, condition: str, step_metrics: dict[str, Any]) -> bool:
        """Parse and evaluate a single stop condition against the current run context/metrics."""
        match = STOP_CONDITION_REGEX.match(condition.strip())
        if not match:
            return False

        var_name, op, rhs_str = match.groups()

        # Get value from context/step_metrics
        if var_name not in step_metrics:
            return False

        lhs = step_metrics[var_name]

        # Convert RHS value to correct type based on LHS type
        rhs: Any = rhs_str
        if isinstance(lhs, bool):
            rhs = rhs_str.lower() in ("true", "1", "yes")
        elif isinstance(lhs, int):
            try:
                rhs = int(rhs_str)
            except ValueError:
                return False
        elif isinstance(lhs, float):
            try:
                rhs = float(rhs_str)
            except ValueError:
                return False

        # Compare
        if op == "==":
            return lhs == rhs
        elif op == "!=":
            return lhs != rhs
        elif op == ">":
            return lhs > rhs
        elif op == "<":
            return lhs < rhs
        elif op == ">=":
            return lhs >= rhs
        elif op == "<=":
            return lhs <= rhs

        return False
