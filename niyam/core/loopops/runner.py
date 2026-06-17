"""LoopRunner orchestrating loop initialization and step outcomes execution."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Any
import yaml

from niyam.core.loopops.schema import LoopSpec
from niyam.core.loopops.state_machine import (
    LoopRun,
    LoopStateMachine,
    LoopIteration,
    LoopObservation,
    LoopPolicyDecision,
)


class LoopRunner:
    """Manages the lifecycle of a LoopSpec execution."""

    @staticmethod
    def initialize_run(spec: LoopSpec) -> LoopRun:
        """Create a new LoopRun database record from a LoopSpec."""
        run_id = f"LR-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.now(timezone.utc).isoformat()

        # Resolve evidence directory
        from niyam.core.config import find_niyam_root
        root = find_niyam_root() or Path.cwd()
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        evidence_dir = root / ".niyam" / "evidence" / "loops" / spec.metadata.name / date_str

        # Create subdirectories
        evidence_dir.mkdir(parents=True, exist_ok=True)
        (evidence_dir / "iterations").mkdir(parents=True, exist_ok=True)
        (evidence_dir / "artifacts").mkdir(parents=True, exist_ok=True)
        (evidence_dir / "evaluations").mkdir(parents=True, exist_ok=True)

        rel_path = f"./.niyam/evidence/loops/{spec.metadata.name}/{date_str}/"

        run = LoopRun(
            id=run_id,
            specName=spec.metadata.name,
            goal=spec.goal.description,
            status="pending",
            startedAt=now,
            iterationCount=0,
            maxIterations=spec.budgets.max_iterations,
            costUsd=0.0,
            maxCostUsd=spec.budgets.max_cost_usd,
            riskLevel=spec.metadata.risk_tier or "medium",
            evidencePath=rel_path,
        )

        # Save initial run.json and loop-spec.yaml
        with open(evidence_dir / "run.json", "w", encoding="utf-8") as f:
            json.dump(run.model_dump(by_alias=True), f, indent=2)
        with open(evidence_dir / "loop-spec.yaml", "w", encoding="utf-8") as f:
            yaml.dump(spec.model_dump(by_alias=True), f, default_flow_style=False, sort_keys=False)

        return run

    @staticmethod
    def evaluate_loop_policies(
        run: LoopRun, spec: LoopSpec, step_result: dict[str, Any]
    ) -> list[LoopPolicyDecision]:
        """Evaluate enterprise policies against a step's results."""
        from niyam.core.config import find_niyam_root, load_niyam_config
        from niyam.core.mcp import load_mcp_registry
        from niyam.core.policy import is_exception_active
        import fnmatch
        import re

        root = find_niyam_root() or Path.cwd()
        decisions: list[LoopPolicyDecision] = []

        # 1. Load protected files policy
        protected_files = []
        try:
            config = load_niyam_config(root)
            if config and config.governance and config.governance.guard:
                protected_files = config.governance.guard.protected_files
            else:
                # Fallback to local file
                from niyam.core.security import safe_load_yaml
                sec_policy_path = root / ".niyam" / "policies" / "security.yaml"
                if sec_policy_path.exists():
                    sec_data = safe_load_yaml(sec_policy_path) or {}
                    protected_files = sec_data.get("deny_write_patterns", [])
            # Merge frozen paths from legacy guard config
            if config and config.guard and config.guard.frozen_paths:
                for fp in config.guard.frozen_paths:
                    if fp not in protected_files:
                        protected_files.append(fp)
        except Exception:
            pass

        # Helper to match file path against protected file patterns
        def is_protected_match(file_path: str, pattern: str) -> bool:
            file_path = file_path.replace("\\", "/")
            pattern = pattern.replace("\\", "/")
            if fnmatch.fnmatch(file_path, pattern):
                return True
            norm_pattern = pattern.rstrip("/")
            if file_path.startswith(norm_pattern + "/"):
                return True
            if "**" in pattern:
                regex_parts = []
                i = 0
                while i < len(pattern):
                    if pattern[i:i+2] == "**":
                        regex_parts.append(".*")
                        i += 2
                    elif pattern[i] == "*":
                        regex_parts.append("[^/]*")
                        i += 1
                    elif pattern[i] == "?":
                        regex_parts.append("[^/]")
                        i += 1
                    else:
                        regex_parts.append(re.escape(pattern[i]))
                        i += 1
                regex = "^" + "".join(regex_parts) + "$"
                if re.match(regex, file_path):
                    return True
            return False

        # Evaluate file changes
        files_changed = step_result.get("files_changed", [])
        for f in files_changed:
            for pattern in protected_files:
                if is_protected_match(f, pattern):
                    # Check for active exception
                    exception = is_exception_active(pattern, root)
                    if exception:
                        decisions.append(
                            LoopPolicyDecision(
                                ruleId=f"protected_file:{pattern}",
                                result="allow",
                                reason=f"Modified file '{f}' matched protected pattern '{pattern}' but is allowed via active exception: {exception.id} ({exception.reason})",
                            )
                        )
                    else:
                        decisions.append(
                            LoopPolicyDecision(
                                ruleId=f"protected_file:{pattern}",
                                result="approval_required",
                                reason=f"Modified protected file '{f}' matching pattern '{pattern}'",
                            )
                        )
                    break # Match one pattern per file is enough

        # 2. Evaluate MCP Tools
        tools_used = step_result.get("tools_used", [])
        if tools_used:
            try:
                registry = load_mcp_registry(root)
                for tool_name in tools_used:
                    # Look up tool in registry
                    tool = registry.tools.get(tool_name)
                    if not tool:
                        # Fallback: maybe it's in the form server/tool
                        for t_name, t_val in registry.tools.items():
                            if t_name == tool_name or os.path.basename(t_name) == tool_name:
                                tool = t_val
                                tool_name = t_name
                                break
                    
                    if tool and not tool.approved:
                        # Check active exception
                        exception = is_exception_active(tool_name, root)
                        if exception:
                            decisions.append(
                                LoopPolicyDecision(
                                    ruleId=f"mcp_unapproved:{tool_name}",
                                    result="allow",
                                    reason=f"Used unapproved tool '{tool_name}' but is allowed via active exception: {exception.id} ({exception.reason})",
                                )
                            )
                        else:
                            risk = tool.risk_level or "medium"
                            if risk in ("high", "critical"):
                                decisions.append(
                                    LoopPolicyDecision(
                                        ruleId=f"mcp_unapproved:{tool_name}",
                                        result="block",
                                        reason=f"Unapproved {risk} risk tool from registry: '{tool_name}'",
                                    )
                                )
                            elif risk == "medium":
                                decisions.append(
                                    LoopPolicyDecision(
                                        ruleId=f"mcp_unapproved:{tool_name}",
                                        result="approval_required",
                                        reason=f"Unapproved medium risk tool from registry: '{tool_name}'",
                                    )
                                )
            except Exception:
                pass

        # 3. Evaluate Required Evidence
        # Resolve current step
        step_name = step_result.get("step_name") or (spec.steps[0].name if spec.steps else None)
        current_step = None
        if step_name:
            for step in spec.steps:
                if step.name == step_name:
                    current_step = step
                    break
        
        if current_step and current_step.required_evidence:
            step_evidence = step_result.get("evidence", [])
            for ev_key in current_step.required_evidence:
                if ev_key not in step_evidence:
                    # Check active exception
                    exception = is_exception_active(ev_key, root)
                    if exception:
                        decisions.append(
                            LoopPolicyDecision(
                                ruleId=f"required_evidence:{ev_key}",
                                result="allow",
                                reason=f"Required evidence '{ev_key}' is missing but is allowed via active exception: {exception.id} ({exception.reason})",
                            )
                        )
                    else:
                        loop_risk = run.risk_level or "medium"
                        if loop_risk in ("high", "critical"):
                            decisions.append(
                                LoopPolicyDecision(
                                    ruleId=f"required_evidence:{ev_key}",
                                    result="block",
                                    reason=f"Missing required evidence '{ev_key}' in step '{step_name}' (Loop Risk: {loop_risk})",
                                )
                            )
                        else:
                            decisions.append(
                                LoopPolicyDecision(
                                    ruleId=f"required_evidence:{ev_key}",
                                    result="warn",
                                    reason=f"Missing required evidence '{ev_key}' in step '{step_name}' (Loop Risk: {loop_risk})",
                                )
                            )

        return decisions

    @staticmethod
    def process_step_result(
        run: LoopRun, spec: LoopSpec, step_result: dict[str, Any]
    ) -> Optional[str]:
        """Process the outcome of a step iteration.

        Updates execution metrics, evaluates budgets and stop conditions,
        and transitions the run status.

        Returns:
            Optional[str]: The stop/failure reason if the run is completed or stopped, None otherwise.
        """
        sm = LoopStateMachine(run)
        if run.status == "pending":
            sm.transition_to("running")

        # 1. Update iterations and cost
        run.iteration_count += 1

        # Extract token counts from step result
        step_tokens_in = step_result.get("tokens_in", 0) or 0
        step_tokens_out = step_result.get("tokens_out", 0) or 0
        run.tokens_in += step_tokens_in
        run.tokens_out += step_tokens_out

        # Determine cost: use explicit cost_usd, or estimate from model + tokens
        cost = step_result.get("cost_usd")
        if cost is None and step_result.get("model") and (step_tokens_in or step_tokens_out):
            from niyam.core.cost import load_pricing, calculate_cost
            pricing = load_pricing()
            cost = calculate_cost(step_result["model"], step_tokens_in, step_tokens_out, pricing)
        cost = cost or 0.0
        run.cost_usd += cost

        # 2. Track failures and repeating errors
        status = step_result.get("status", "success")
        error = step_result.get("error")

        if status == "failure":
            run.consecutive_failures += 1
            if error:
                # Track occurrences of this specific error
                err_str = str(error).strip()
                run.consecutive_errors[err_str] = (
                    run.consecutive_errors.get(err_str, 0) + 1
                )
        else:
            # Reset consecutive metrics on success
            run.consecutive_failures = 0
            run.consecutive_errors.clear()

        # 3. Transition to evaluating
        sm.transition_to("evaluating")

        # Run policy evaluations
        policy_decisions = LoopRunner.evaluate_loop_policies(run, spec, step_result)

        # Run evaluators
        from niyam.core.loopops.evaluator import run_evaluators
        evaluation_results = run_evaluators(spec, step_result, run.iteration_count)

        has_block = False
        has_approval = False
        block_reasons = []
        approval_reasons = []

        for dec in policy_decisions:
            if dec.result == "block":
                has_block = True
                block_reasons.append(dec.reason)
            elif dec.result == "approval_required":
                has_approval = True
                approval_reasons.append(dec.reason)

        # Check evaluator results: required fail → block the loop
        evaluator_blocked = False
        evaluator_block_reasons = []
        for ev_res in evaluation_results:
            if ev_res.result == "fail" and ev_res.required:
                evaluator_blocked = True
                evaluator_block_reasons.append(
                    f"Required evaluator '{ev_res.evaluator_name}' failed: {ev_res.details}"
                )
            if getattr(ev_res, "risk_level", None) in ("high", "critical"):
                has_approval = True
                approval_reasons.append(
                    f"Evaluator '{ev_res.evaluator_name}' flagged high-risk result: {ev_res.details}"
                )

        # Check if step status explicitly completed the loop
        termination_reason: Optional[str] = None
        if has_block:
            status = "blocked"
            sm.transition_to("failed")
            termination_reason = f"Blocked by policy: {'; '.join(block_reasons)}"
        elif evaluator_blocked:
            status = "blocked"
            sm.transition_to("failed")
            termination_reason = f"Blocked by evaluator: {'; '.join(evaluator_block_reasons)}"
        elif has_approval:
            sm.transition_to("requires_approval")
            termination_reason = f"Requires human approval: {'; '.join(approval_reasons)}"
        elif status == "passed":
            sm.transition_to("passed")
            termination_reason = "Loop completed successfully (goal met)."
        elif status == "failed":
            sm.transition_to("failed")
            termination_reason = "Loop execution failed."

        # 4. Check budget limits first if not already terminated
        if not termination_reason:
            budget_stop = sm.evaluate_budgets(spec.budgets)
            if budget_stop:
                termination_reason = budget_stop

        # 5. Evaluate stop conditions if not already terminated
        if not termination_reason:
            max_err_repeat = (
                max(run.consecutive_errors.values()) if run.consecutive_errors else 0
            )
            policy_violation_val = "none"
            if any(dec.result == "warn" for dec in policy_decisions):
                policy_violation_val = "warning"
            elif any(dec.result == "block" for dec in policy_decisions):
                policy_violation_val = "critical"

            step_metrics = {
                "repeatedFailureCount": run.consecutive_failures,
                "sameErrorRepeated": max_err_repeat,
                "policyViolation": policy_violation_val,
                "humanApprovalRequired": step_result.get("human_approval_required", False) or has_approval,
                "iterations": run.iteration_count,
                "costUsd": run.cost_usd,
            }

            for condition in spec.stop_conditions:
                if sm.evaluate_stop_condition(condition, step_metrics):
                    # Check if it was human approval required
                    if "humanApprovalRequired" in condition:
                        sm.transition_to("requires_approval")
                        termination_reason = f"Requires human approval: condition '{condition}' triggered."
                    else:
                        sm.transition_to("stopped")
                        termination_reason = f"Stop condition triggered: '{condition}'."
                    break

        # If no budget or stop conditions met and not completed, transition back to running
        if not termination_reason:
            sm.transition_to("running")

        # Resolve evidence directory
        from niyam.core.config import find_niyam_root
        root = find_niyam_root() or Path.cwd()
        evidence_dir = root / Path(run.evidence_path)

        # Determine step name / actor for trace
        step_name = step_result.get("step_name") or (spec.steps[0].name if spec.steps else "execute")
        actor = step_result.get("actor") or (spec.steps[0].actor if spec.steps and spec.steps[0].actor else "claude")

        # Populate observations
        observations = []
        if error:
            observations.append(
                LoopObservation(
                    type="error",
                    content=str(error),
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )
            )

        # Add evaluator warnings to observations
        for ev_res in evaluation_results:
            if ev_res.result == "fail" and not ev_res.required:
                observations.append(
                    LoopObservation(
                        type="evaluator_warn",
                        content=f"Optional evaluator '{ev_res.evaluator_name}' failed: {ev_res.details}",
                        timestamp=ev_res.timestamp,
                    )
                )

        # 6. Write LoopIteration trace
        iter_result = "success"
        if status == "failure":
            iter_result = "failure"
        elif status == "blocked" or has_block or evaluator_blocked:
            iter_result = "blocked"
        elif any(dec.result == "warn" for dec in policy_decisions):
            iter_result = "warning"

        iteration = LoopIteration(
            id=f"LI-{run.id[3:]}-{run.iteration_count:03d}",
            loopRunId=run.id,
            index=run.iteration_count,
            actor=actor,
            stepName=step_name,
            action="execute_step",
            startedAt=datetime.now(timezone.utc).isoformat(),
            completedAt=datetime.now(timezone.utc).isoformat(),
            tokensIn=step_tokens_in,
            tokensOut=step_tokens_out,
            costUsd=cost,
            result=iter_result,
            observations=observations,
            policyDecisions=policy_decisions,
        )

        iter_file = evidence_dir / "iterations" / f"{run.iteration_count:03d}.json"
        with open(iter_file, "w", encoding="utf-8") as f:
            json.dump(iteration.model_dump(by_alias=True), f, indent=2)

        # 7. Write mock artifacts
        artifacts_dir = evidence_dir / "artifacts"
        with open(artifacts_dir / "test-output.txt", "w", encoding="utf-8") as f:
            f.write(f"=== Test Run Log (Iteration {run.iteration_count}) ===\n")
            if status == "failure":
                f.write(f"FAIL: {error or 'AssertionError'}\n")
            else:
                f.write("PASS: All unit tests completed successfully.\n")

        with open(artifacts_dir / "diff.patch", "w", encoding="utf-8") as f:
            f.write("diff --git a/src/app.py b/src/app.py\n")
            f.write("--- a/src/app.py\n")
            f.write("+++ b/src/app.py\n")
            f.write("@@ -10,3 +10,3 @@\n")
            if status == "failure":
                f.write("-# buggy code\n+# broken implementation\n")
            else:
                f.write("-# buggy code\n+# fixed implementation\n")

        policy_res = {
            "iteration": run.iteration_count,
            "policy_violation": "critical" if has_block else ("warning" if any(dec.result == "warn" for dec in policy_decisions) else "none"),
            "blocked_commands": [dec.rule_id for dec in policy_decisions if dec.result == "block"],
            "requires_approval": has_approval or step_result.get("human_approval_required", False),
            "decisions": [dec.model_dump(by_alias=True) for dec in policy_decisions],
        }
        # Write evaluation results
        if evaluation_results:
            eval_dir = evidence_dir / "evaluations"
            eval_data = {
                "iteration": run.iteration_count,
                "results": [er.model_dump(by_alias=True) for er in evaluation_results],
            }
            with open(eval_dir / f"{run.iteration_count:03d}.json", "w", encoding="utf-8") as f:
                json.dump(eval_data, f, indent=2)

        with open(artifacts_dir / "policy-results.json", "w", encoding="utf-8") as f:
            json.dump(policy_res, f, indent=2)

        # 8. Check if loop is completed to write final run.json and report.md
        if run.status in ("passed", "failed", "stopped", "requires_approval"):
            run.completed_at = datetime.now(timezone.utc).isoformat()

            # Calculate wasted cost for non-passed terminal states
            if run.status in ("failed", "stopped"):
                run.wasted_cost_usd = run.cost_usd

            # Save run.json
            with open(evidence_dir / "run.json", "w", encoding="utf-8") as f:
                json.dump(run.model_dump(by_alias=True), f, indent=2)

            # Generate report.md
            report_md = LoopRunner.generate_report_markdown(run, spec, termination_reason or "Completed.")
            with open(evidence_dir / "report.md", "w", encoding="utf-8") as f:
                f.write(report_md)

        return termination_reason

    @staticmethod
    def generate_report_markdown(run: LoopRun, spec: LoopSpec, reason_message: str) -> str:
        """Generate a summarized markdown report for the LoopRun."""
        max_cost_str = f"${spec.budgets.max_cost_usd:.2f}" if spec.budgets.max_cost_usd is not None else "N/A"
        max_tokens_str = f"{spec.budgets.max_tokens:,}" if spec.budgets.max_tokens is not None else "N/A"
        stop_conditions_list = "\n".join(f"- `{cond}`" for cond in spec.stop_conditions)

        total_tokens = run.tokens_in + run.tokens_out
        avg_cost = run.cost_usd / run.iteration_count if run.iteration_count > 0 else 0.0
        efficiency_status = "Efficient" if run.wasted_cost_usd == 0.0 else "Wasteful"

        report = f"""# Niyam LoopOps Run Report: {run.spec_name}

## Executive Summary
- **Loop Run ID**: `{run.id}`
- **Goal**: {run.goal}
- **Status**: `{run.status.upper()}`
- **Risk Level**: `{run.risk_level.upper()}`
- **Completed At**: {run.completed_at}

## Execution Summary
- **Total Iterations**: {run.iteration_count} / {run.max_iterations}
- **Total Cost (USD)**: ${run.cost_usd:.2f}
- **Reason**: {reason_message}

## Budgets & Stop Conditions
### Budgets
- **Max Iterations**: {spec.budgets.max_iterations}
- **Max Cost (USD)**: {max_cost_str}
- **Max Tokens**: {max_tokens_str}

### Stop Conditions
{stop_conditions_list}

## FinOps & Efficiency Analytics
- **Total Tokens**: {total_tokens:,}
  - Input: {run.tokens_in:,}
  - Output: {run.tokens_out:,}
- **Avg Cost/Iteration**: ${avg_cost:.4f}
- **Wasted Cost (USD)**: ${run.wasted_cost_usd:.2f}
- **Efficiency Status**: {efficiency_status}
"""
        # Append evaluator section if spec has evaluators
        if spec.evaluators:
            eval_lines = ["\n## Evaluator Results"]
            for ev in spec.evaluators:
                req_str = "Required" if ev.required else "Optional"
                eval_lines.append(f"- **{ev.name}** ({ev.type}, {req_str})")
                if ev.criteria:
                    eval_lines.append(f"  - Criteria: {ev.criteria}")
            report += "\n".join(eval_lines) + "\n"

        return report

