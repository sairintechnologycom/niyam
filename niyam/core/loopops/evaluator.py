"""Evaluator engine for Niyam LoopOps — runs AI critics and command checks."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, Literal, Any

from pydantic import BaseModel, Field

from niyam.core.loopops.schema import LoopSpec


class LoopEvaluationResult(BaseModel):
    """Result from running a single evaluator against a step outcome."""

    model_config = {"populate_by_name": True, "extra": "allow"}

    evaluator_name: str = Field(..., alias="evaluatorName")
    evaluator_type: Literal["ai_critic", "command"] = Field(..., alias="evaluatorType")
    result: Literal["pass", "fail", "warn", "error"]
    required: bool
    details: str
    score: Optional[float] = Field(None, description="0.0–1.0 confidence/quality score")
    risk_level: Optional[Literal["low", "medium", "high", "critical"]] = Field(None, alias="riskLevel", description="Assessed risk level")
    timestamp: str


def run_evaluators(
    spec: LoopSpec,
    step_result: dict[str, Any],
    iteration_index: int,
) -> list[LoopEvaluationResult]:
    """Run all evaluators declared in the spec against a step result.

    In this phase, evaluators are simulated/mocked:
    - ai_critic: produces a structured review based on step status
    - command: produces pass/fail based on step status

    Future phases will delegate to real AI calls or subprocess execution.
    """
    if not spec.evaluators:
        return []

    now = datetime.now(timezone.utc).isoformat()
    results: list[LoopEvaluationResult] = []
    step_status = step_result.get("status", "success")

    for ev in spec.evaluators:
        if ev.type == "ai_critic":
            result = _simulate_ai_critic(ev.name, ev.actor or "unknown", ev.criteria, step_status, ev.required, now)
        elif ev.type == "command":
            result = _simulate_command(ev.name, ev.command or "unknown", step_status, ev.required, now)
        else:
            result = LoopEvaluationResult(
                evaluatorName=ev.name,
                evaluatorType=ev.type,
                result="error",
                required=ev.required,
                details=f"Unknown evaluator type '{ev.type}'.",
                timestamp=now,
            )
        results.append(result)

    return results


def _simulate_ai_critic(
    name: str, actor: str, criteria: str | None, step_status: str, required: bool, timestamp: str
) -> LoopEvaluationResult:
    """Simulate an AI critic evaluator.

    For simulation: 
    - step_status 'failure' or 'failed' → evaluator fails.
    - step_status 'high_risk' → evaluator flags high risk.
    - Otherwise evaluator passes with a mock review.
    """
    if step_status == "high_risk":
        return LoopEvaluationResult(
            evaluatorName=name,
            evaluatorType="ai_critic",
            result="warn",
            required=required,
            details=f"AI critic '{name}' ({actor}) detected high-risk issues requiring approval. Criteria: {criteria or 'general review'}",
            score=0.4,
            riskLevel="high",
            timestamp=timestamp,
        )

    if step_status in ("failure", "failed"):
        return LoopEvaluationResult(
            evaluatorName=name,
            evaluatorType="ai_critic",
            result="fail",
            required=required,
            details=f"AI critic '{name}' ({actor}) detected issues: step execution failed. Criteria: {criteria or 'general review'}",
            score=0.3,
            timestamp=timestamp,
        )

    return LoopEvaluationResult(
        evaluatorName=name,
        evaluatorType="ai_critic",
        result="pass",
        required=required,
        details=f"AI critic '{name}' ({actor}) review passed. Criteria: {criteria or 'general review'}",
        score=0.92,
        timestamp=timestamp,
    )


def _simulate_command(
    name: str, command: str, step_status: str, required: bool, timestamp: str
) -> LoopEvaluationResult:
    """Simulate a command-based evaluator.

    For simulation: step_status 'failure' or 'failed' → command fails.
    Otherwise command passes.
    """
    if step_status in ("failure", "failed"):
        return LoopEvaluationResult(
            evaluatorName=name,
            evaluatorType="command",
            result="fail",
            required=required,
            details=f"Command '{command}' exited with non-zero status (simulated).",
            score=None,
            timestamp=timestamp,
        )

    return LoopEvaluationResult(
        evaluatorName=name,
        evaluatorType="command",
        result="pass",
        required=required,
        details=f"Command '{command}' completed successfully (simulated).",
        score=None,
        timestamp=timestamp,
    )
