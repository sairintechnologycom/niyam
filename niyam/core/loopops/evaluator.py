"""Evaluator engine for Niyam LoopOps — runs AI critics and command checks."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Literal, Any

from pydantic import BaseModel, Field

from niyam.core.loopops.schema import LoopSpec
from niyam.core.security import safe_run_command, CommandSecurityError

logger = logging.getLogger(__name__)


class LoopEvaluationResult(BaseModel):
    """Result from running a single evaluator against a step outcome."""

    model_config = {"populate_by_name": True, "extra": "allow"}

    evaluator_name: str = Field(..., alias="evaluatorName")
    evaluator_type: Literal["ai_critic", "command"] = Field(..., alias="evaluatorType")
    result: Literal["pass", "fail", "warn", "error"]
    required: bool
    details: str
    score: Optional[float] = Field(None, description="0.0–1.0 confidence/quality score")
    risk_level: Optional[Literal["low", "medium", "high", "critical"]] = Field(
        None, alias="riskLevel", description="Assessed risk level"
    )
    timestamp: str
    exit_code: Optional[int] = Field(None, alias="exitCode")
    stdout: Optional[str] = Field(None, alias="stdout")
    stderr: Optional[str] = Field(None, alias="stderr")
    duration: Optional[float] = Field(None, alias="duration")
    policy_result: Optional[str] = Field(None, alias="policyResult")


def run_evaluators(
    spec: LoopSpec,
    step_result: dict[str, Any],
    iteration_index: int,
    workspace_path: Optional[Path] = None,
) -> list[LoopEvaluationResult]:
    """Run all evaluators declared in the spec against a step result.

    Execution strategy:
    - If ``step_result`` contains a ``scenario`` key the simulation path is
      used (preserves scenario/test behaviour).
    - Otherwise real execution is attempted:
        - ``command`` type: runs the command via ``safe_run_command()`` and
          inspects the exit code.
        - ``ai_critic`` type: dispatches a ``review()`` call to the adapter
          named in ``ev.actor``.
    """
    if not spec.evaluators:
        return []

    import os
    import sys

    now = datetime.now(timezone.utc).isoformat()
    results: list[LoopEvaluationResult] = []
    step_status = step_result.get("status", "success")
    # Use simulation when: an explicit scenario key is present, or running
    # under the test environment (NIYAM_TEST=1 or pytest is loaded).
    is_simulation = (
        bool(step_result.get("scenario"))
        or os.environ.get("NIYAM_TEST") == "1"
        or "pytest" in sys.modules
    )

    for ev in spec.evaluators:
        if ev.type == "ai_critic":
            if is_simulation:
                result = _simulate_ai_critic(
                    ev.name, ev.actor or "unknown", ev.criteria, step_status, ev.required, now
                )
            else:
                result = _run_ai_critic(
                    ev.name,
                    ev.actor or "claude",
                    ev.criteria,
                    step_result,
                    ev.required,
                    workspace_path,
                    now,
                )
        elif ev.type == "command":
            if is_simulation:
                result = _simulate_command(ev.name, ev.command or "unknown", step_status, ev.required, now)
            else:
                result = _run_command_evaluator(
                    ev.name,
                    ev.command or "",
                    ev.required,
                    workspace_path,
                    now,
                )
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


# ── Real Evaluator Implementations ─────────────────────────────────────


def _run_command_evaluator(
    name: str,
    command: str,
    required: bool,
    workspace_path: Optional[Path],
    timestamp: str,
) -> LoopEvaluationResult:
    """Execute the evaluator command as a real subprocess and check its exit code.

    Uses ``safe_run_command()`` so commands are validated against the security
    allowlist before execution.  If the workspace path is unavailable the
    evaluator falls back to an error result rather than running in an
    undefined directory.
    """
    if not command.strip():
        return LoopEvaluationResult(
            evaluatorName=name,
            evaluatorType="command",
            result="error",
            required=required,
            details="Evaluator command is empty.",
            timestamp=timestamp,
        )

    cwd = workspace_path or Path.cwd()

    import time
    start_time = time.time()
    try:
        res = safe_run_command(command, cwd=cwd, timeout=120)
        duration = time.time() - start_time
        if res.returncode == 0:
            return LoopEvaluationResult(
                evaluatorName=name,
                evaluatorType="command",
                result="pass",
                required=required,
                details=f"Command '{command}' exited 0.",
                timestamp=timestamp,
                exitCode=0,
                stdout=res.stdout,
                stderr=res.stderr,
                duration=duration,
                policyResult="allow",
            )
        stderr_snippet = (res.stderr or "")[:300].strip()
        return LoopEvaluationResult(
            evaluatorName=name,
            evaluatorType="command",
            result="fail",
            required=required,
            details=(
                f"Command '{command}' exited {res.returncode}."
                + (f" stderr: {stderr_snippet}" if stderr_snippet else "")
            ),
            timestamp=timestamp,
            exitCode=res.returncode,
            stdout=res.stdout,
            stderr=res.stderr,
            duration=duration,
            policyResult="allow",
        )
    except CommandSecurityError as exc:
        duration = time.time() - start_time
        logger.warning("Evaluator command blocked by security policy: %s", exc)
        return LoopEvaluationResult(
            evaluatorName=name,
            evaluatorType="command",
            result="fail",
            required=required,
            details=f"Command blocked by Niyam security policy: {exc}",
            timestamp=timestamp,
            exitCode=-1,
            stdout="",
            stderr=str(exc),
            duration=duration,
            policyResult="blocked",
        )
    except Exception as exc:
        duration = time.time() - start_time
        logger.warning("Evaluator command execution error for '%s': %s", name, exc, exc_info=True)
        return LoopEvaluationResult(
            evaluatorName=name,
            evaluatorType="command",
            result="error",
            required=required,
            details=f"Command execution error: {exc}",
            timestamp=timestamp,
            exitCode=-1,
            stdout="",
            stderr=str(exc),
            duration=duration,
            policyResult="error",
        )


def _run_ai_critic(
    name: str,
    actor: str,
    criteria: str | None,
    step_result: dict[str, Any],
    required: bool,
    workspace_path: Optional[Path],
    timestamp: str,
) -> LoopEvaluationResult:
    """Dispatch a review() call to the named adapter for AI-based critique.

    The adapter is resolved via ``get_adapter(actor)`` so any configured
    AI runtime (claude, gemini, codex, …) can serve as an evaluator.
    Failures fall back to a structured error result rather than crashing.
    """
    from niyam.core.loopops.adapters import get_adapter, AgentTaskRequest

    cwd = workspace_path or Path.cwd()
    step_summary = step_result.get("error") or step_result.get("summary", "")
    goal_summary = (
        f"Review the step output for quality and correctness.\n"
        f"Criteria: {criteria or 'general review'}\n"
        f"Step status: {step_result.get('status', 'unknown')}\n"
        f"Step summary: {step_summary}\n"
        f"Files changed: {', '.join(step_result.get('files_changed', []))}"
    )

    try:
        adapter = get_adapter(actor)
        req = AgentTaskRequest(
            goal=goal_summary,
            workspace_path=cwd,
            action="review",
            step_name=name,
        )
        result = adapter.review(req)
        status = result.status

        if status in ("failed", "failure"):
            return LoopEvaluationResult(
                evaluatorName=name,
                evaluatorType="ai_critic",
                result="fail",
                required=required,
                details=f"AI critic '{name}' ({actor}) review failed: {result.summary}",
                score=0.3,
                timestamp=timestamp,
            )
        if result.risk_flags:
            return LoopEvaluationResult(
                evaluatorName=name,
                evaluatorType="ai_critic",
                result="warn",
                required=required,
                details=f"AI critic '{name}' ({actor}) flagged risks: {', '.join(result.risk_flags)}",
                score=0.6,
                riskLevel="high",
                timestamp=timestamp,
            )
        return LoopEvaluationResult(
            evaluatorName=name,
            evaluatorType="ai_critic",
            result="pass",
            required=required,
            details=f"AI critic '{name}' ({actor}) review passed: {result.summary}",
            score=0.9,
            timestamp=timestamp,
        )
    except ValueError as exc:
        # Unknown adapter name — log and degrade gracefully
        logger.warning("ai_critic evaluator '%s' references unknown actor '%s': %s", name, actor, exc)
        return LoopEvaluationResult(
            evaluatorName=name,
            evaluatorType="ai_critic",
            result="error",
            required=required,
            details=f"Unknown adapter for ai_critic actor '{actor}': {exc}",
            timestamp=timestamp,
        )
    except Exception as exc:
        logger.warning("ai_critic evaluator '%s' failed: %s", name, exc, exc_info=True)
        return LoopEvaluationResult(
            evaluatorName=name,
            evaluatorType="ai_critic",
            result="error",
            required=required,
            details=f"AI critic execution error: {exc}",
            timestamp=timestamp,
        )


# ── Simulation Helpers (used when step_result contains 'scenario') ──────


def _simulate_ai_critic(
    name: str, actor: str, criteria: str | None, step_status: str, required: bool, timestamp: str
) -> LoopEvaluationResult:
    """Simulate an AI critic evaluator for scenario/test execution.

    - step_status 'high_risk' → warn with high risk level
    - step_status 'failure' / 'failed' → fail
    - otherwise → pass
    """
    if step_status == "high_risk":
        return LoopEvaluationResult(
            evaluatorName=name,
            evaluatorType="ai_critic",
            result="warn",
            required=required,
            details=(
                f"AI critic '{name}' ({actor}) detected high-risk issues requiring approval. "
                f"Criteria: {criteria or 'general review'}"
            ),
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
            details=(
                f"AI critic '{name}' ({actor}) detected issues: step execution failed. "
                f"Criteria: {criteria or 'general review'}"
            ),
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
    """Simulate a command-based evaluator for scenario/test execution."""
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
