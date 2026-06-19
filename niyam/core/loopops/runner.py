"""LoopRunner orchestrating loop initialization and step outcomes execution."""

from __future__ import annotations

import json
import logging
import os
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

logger = logging.getLogger(__name__)

class LoopRunner:
    """Manages the lifecycle of a LoopSpec execution."""

    @staticmethod
    def initialize_run(spec: LoopSpec, repo_root: Optional[Path] = None) -> LoopRun:
        """Create a new LoopRun database record from a LoopSpec."""
        run_id = f"LR-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.now(timezone.utc).isoformat()

        # Resolve evidence directory
        from niyam.core.config import find_niyam_root
        root = repo_root or find_niyam_root() or Path.cwd()
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
        run: LoopRun, spec: LoopSpec, step_result: dict[str, Any], repo_root: Optional[Path] = None
    ) -> list[LoopPolicyDecision]:
        """Evaluate enterprise policies against a step's results."""
        from niyam.core.config import find_niyam_root, load_niyam_config
        from niyam.core.mcp import load_mcp_registry
        from niyam.core.policy import is_exception_active
        import fnmatch
        import re

        root = repo_root or find_niyam_root() or Path.cwd()
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
            logger.debug("Exception caught", exc_info=True)

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
                logger.debug("Exception caught", exc_info=True)

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
        run: LoopRun, spec: LoopSpec, step_result: dict[str, Any], repo_root: Optional[Path] = None
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
        from niyam.core.config import find_niyam_root
        root = repo_root or find_niyam_root() or Path.cwd()
        policy_decisions = LoopRunner.evaluate_loop_policies(run, spec, step_result, root)

        # Run evaluators
        from niyam.core.loopops.evaluator import run_evaluators
        evaluation_results = run_evaluators(spec, step_result, run.iteration_count, workspace_path=root)

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

        # 7. Write execution artifacts from real adapter output (not mock data)
        artifacts_dir = evidence_dir / "artifacts"
        exec_out = artifacts_dir / "execution-output.txt"
        commands_run = step_result.get("commands_run") or []
        files_changed = step_result.get("files_changed") or []
        with open(exec_out, "w", encoding="utf-8") as f:
            f.write(f"=== Iteration {run.iteration_count} ===\n")
            f.write(f"Status: {status}\n")
            if commands_run:
                f.write(f"Commands Run:\n")
                for cmd in commands_run:
                    f.write(f"  - {cmd}\n")
            if files_changed:
                f.write(f"Files Changed:\n")
                for fp in files_changed:
                    f.write(f"  - {fp}\n")
            if step_result.get("error"):
                f.write(f"Error: {step_result['error']}\n")

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
            LoopRunner.sign_run_data(run, root)
            with open(evidence_dir / "run.json", "w", encoding="utf-8") as f:
                json.dump(run.model_dump(by_alias=True), f, indent=2)

            # Generate report.md
            report_md = LoopRunner.generate_report_markdown(run, spec, termination_reason or "Completed.")
            with open(evidence_dir / "report.md", "w", encoding="utf-8") as f:
                f.write(report_md)

        return termination_reason

    @staticmethod
    def sign_run_data(run: LoopRun, root: Path) -> None:
        """Sign LoopRun data using the workspace private Ed25519 key."""
        from niyam.core.identity import ensure_identity, sign_data, get_public_key_bytes
        try:
            # Dump to model representation
            data = run.model_dump(by_alias=True)
            # Remove existing signature and public key PEM for deterministic hash
            data.pop("signature", None)
            data.pop("publicKeyPem", None)

            # Serialize
            serialized_str = json.dumps(data, sort_keys=True)

            # Get key and sign
            private_key = ensure_identity(root)
            sig = sign_data(serialized_str, private_key)

            # Update fields in run object
            run.signature = sig
            run.public_key_pem = get_public_key_bytes(root).decode("utf-8")
        except Exception:
            logger.debug("Exception caught", exc_info=True)

    @staticmethod
    def replay_loop(run_dir: Path) -> tuple[LoopRun, Optional[str]]:
        """Replay a loop run from signed evidence directory without running agents."""
        run_path = run_dir / "run.json"
        if not run_path.exists():
            raise ValueError("Evidence run.json is missing.")

        with open(run_path, encoding="utf-8") as f:
            run_data = json.load(f)

        # Cryptographically verify the signature
        signature = run_data.get("signature")
        public_key_pem = run_data.get("publicKeyPem")

        # Verify
        verify_data = dict(run_data)
        verify_data.pop("signature", None)
        verify_data.pop("publicKeyPem", None)
        verify_serialized = json.dumps(verify_data, sort_keys=True)

        from niyam.core.identity import verify_signature
        is_valid = False
        if signature and public_key_pem:
            is_valid = verify_signature(verify_serialized, signature, public_key_pem.encode("utf-8"))

        if not is_valid:
            raise ValueError("Cryptographic signature verification failed or missing.")

        run = LoopRun.model_validate(run_data)

        # Play back iterations: verify that we have iterations
        iterations_dir = run_dir / "iterations"
        if not iterations_dir.is_dir() or not list(iterations_dir.glob("*.json")):
            raise ValueError("Missing evidence: iteration logs are missing.")

        # Reconstruct completion reason or message
        reason = run_data.get("reason")
        if not reason:
            report_path = run_dir / "report.md"
            if report_path.exists():
                report_content = report_path.read_text(encoding="utf-8")
                for line in report_content.splitlines():
                    if "Reason" in line:
                        reason = line.split(":", 1)[1].strip().replace("`", "")
                        break
        return run, reason


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

    @staticmethod
    def _prepare_workspace(
        run: LoopRun, spec: LoopSpec, dry_run: bool, root: Path, evidence_dir: Path
    ) -> tuple[Path, bool, str]:
        from niyam.mission.worktree import is_git_repo, create_worktree
        
        worktree_path = root
        use_worktree = (
            spec.workspace and spec.workspace.isolation == "git_worktree"
            and is_git_repo(root)
            and not dry_run
        )

        branch_name = f"niyam-loop/{run.id.lower()}"
        if use_worktree:
            from rich.console import Console
            console_log = Console(stderr=True)
            mock_task = {"id": run.id, "depends_on": []}
            try:
                worktree_path = create_worktree(
                    repo_root=root,
                    run_dir=evidence_dir,
                    mission_id="loop",
                    task=mock_task,
                    console=console_log,
                    branch_name=branch_name,
                )
            except Exception:
                logger.warning("Failed to create worktree", exc_info=True)
                use_worktree = False
                worktree_path = root
                
        return worktree_path, use_worktree, branch_name

    @staticmethod
    def _load_agent_context(spec: LoopSpec, root: Path) -> dict[str, Any]:
        from niyam.core.evidence import redact_secrets_recursive

        memories = []
        memory_dir = root / ".niyam" / "memory"
        if memory_dir.is_dir():
            for filepath in sorted(memory_dir.glob("*.md")):
                try:
                    content = filepath.read_text(encoding="utf-8")
                    if content.strip():
                        # Redact secrets before injecting into prompts
                        safe_content = redact_secrets_recursive(content)
                        memories.append(f"### Memory: {filepath.stem}\\n{safe_content}")
                except Exception:
                    logger.debug("Failed to read memory file", exc_info=True)

        search_results = []
        try:
            from niyam.core.memory import CodebaseIndexer
            indexer = CodebaseIndexer(root)
            search_results = indexer.search(spec.goal.description, k=3)
        except Exception:
            logger.debug("Failed to search codebase", exc_info=True)

        return {
            "memories": memories,
            "codebase_context": search_results,
            "tools_used": [],
        }

    @staticmethod
    def _execute_iteration(
        req: Any, step: Any, adapter: Any
    ) -> Any:
        action_lower = step.action.lower()
        if "plan" in action_lower or "inspect" in action_lower:
            return adapter.plan(req)
        elif "implement" in action_lower or "modify" in action_lower:
            return adapter.implement(req)
        elif "review" in action_lower:
            return adapter.review(req)
        elif "repair" in action_lower or "fix" in action_lower:
            return adapter.repair(req)
        else:
            return adapter.plan(req)

    @staticmethod
    def _evaluate_iteration(
        result: Any, step: Any, actor_provider: str
    ) -> dict[str, Any]:
        status_val = result.status
        return {
            "status": status_val,
            "error": result.summary if status_val in ("failed", "failure") else None,
            "cost_usd": result.cost_usd or 0.0,
            "tokens_in": result.tokens_in or 0,
            "tokens_out": result.tokens_out or 0,
            "files_changed": result.files_changed or [],
            "commands_run": result.commands_run or [],
            "step_name": step.name,
            "actor": actor_provider,
            "evidence": result.evidence_artifacts or [],
            "tools_used": result.context.get("tools_used", []) if result.context else [],
        }

    @staticmethod
    def _finalize_run(
        run: LoopRun, root: Path, worktree_path: Path, use_worktree: bool, branch_name: str
    ) -> None:
        if use_worktree:
            from rich.console import Console
            from niyam.mission.worktree import commit_worktree_changes, cleanup_worktree
            console_log = Console(stderr=True)
            if run.status == "passed":
                try:
                    commit_worktree_changes(worktree_path, run.id, console_log)
                    from niyam.mission.worktree import merge_final_changes
                    mock_tasks = [{"id": run.id, "status": "completed"}]
                    merge_final_changes(root, "loop", mock_tasks, console_log)
                except Exception:
                    logger.warning("Failed to commit worktree changes", exc_info=True)

            try:
                cleanup_worktree(root, worktree_path, branch_name, console_log)
            except Exception:
                logger.warning("Failed to cleanup worktree", exc_info=True)

    @staticmethod
    def run_loop(
        spec: LoopSpec,
        scenario: Optional[str] = None,
        dry_run: bool = False,
        mode: str = "governed",
        require_approval_on: str = "high-risk",
        repo_root: Optional[Path] = None,
    ) -> tuple[LoopRun, Optional[str]]:
        """Run the actual execution loop using adapters and policy gates."""
        from niyam.core.loopops.adapters import get_adapter, AgentTaskRequest
        from niyam.core.config import find_niyam_root

        root = repo_root or find_niyam_root() or Path.cwd()
        run = LoopRunner.initialize_run(spec, repo_root=root)
        evidence_dir = root / Path(run.evidence_path)

        worktree_path, use_worktree, branch_name = LoopRunner._prepare_workspace(
            run, spec, dry_run, root, evidence_dir
        )

        reason = None
        iteration_idx = 1
        step_attempts: dict[str, int] = {}  # tracks per-step attempt counts for maxAttempts enforcement
        original_guard_config = None
        hook_config_dir = root / ".niyam" / "hook-cache"
        guard_config_path = hook_config_dir / "guard-config.json"

        if mode == "governed" and not dry_run:
            try:
                hook_config_dir.mkdir(parents=True, exist_ok=True)
                if guard_config_path.exists():
                    original_guard_config = guard_config_path.read_text(encoding="utf-8")

                g_config = {
                    "guard_enabled": True,
                    "deny_patterns": [],
                    "warn_patterns": [],
                    "deny_write_patterns": [],
                    "allow_write_patterns": [],
                    "frozen_paths": [],
                }
                if original_guard_config:
                    try:
                        existing = json.loads(original_guard_config)
                        g_config.update(existing)
                    except Exception:
                        logger.debug("Exception caught", exc_info=True)
                g_config["guard_enabled"] = True
                guard_config_path.write_text(json.dumps(g_config, indent=2), encoding="utf-8")

                if use_worktree:
                    wt_hook_cache = worktree_path / ".niyam" / "hook-cache"
                    wt_hook_cache.mkdir(parents=True, exist_ok=True)
                    (wt_hook_cache / "guard-config.json").write_text(json.dumps(g_config, indent=2), encoding="utf-8")
            except Exception:
                logger.warning("Exception caught", exc_info=True)

        try:
            try:
                from niyam.core.swarm import prune_stale_agents
                prune_stale_agents(root)
            except Exception:
                logger.debug("Exception caught", exc_info=True)

            while run.status in ("pending", "running"):
                if run.iteration_count >= spec.budgets.max_iterations:
                    from niyam.core.loopops.state_machine import LoopStateMachine
                    sm = LoopStateMachine(run)
                    reason = sm.evaluate_budgets(spec.budgets)
                    break

                step_idx = (run.iteration_count) % len(spec.steps) if spec.steps else 0
                step = spec.steps[step_idx] if spec.steps else None

                if not step:
                    run.status = "passed"
                    reason = "No steps defined in LoopSpec."
                    break

                # Enforce maxAttempts per step
                if step.max_attempts is not None:
                    step_attempts[step.name] = step_attempts.get(step.name, 0) + 1
                    if step_attempts[step.name] > step.max_attempts:
                        run.status = "failed"
                        reason = (
                            f"Step '{step.name}' exceeded maxAttempts "
                            f"({step.max_attempts}). Stopping loop."
                        )
                        break

                actor_role = step.actor or "planner"
                actor_provider = spec.actors.get(actor_role, "claude")
                adapter = get_adapter(actor_provider)
                actor_id = f"agent-{actor_provider}-{run.id}"

                try:
                    from niyam.core.swarm import heartbeat
                    heartbeat(
                        agent_id=actor_id,
                        role=actor_role,
                        status="busy",
                        task_id=run.id,
                        repo_root=root,
                    )
                except Exception:
                    logger.debug("Exception caught", exc_info=True)

                target_files = []
                for word in spec.goal.description.split():
                    word_clean = word.strip("'\"`,;()[]{}")
                    if "." in word_clean and ("/" in word_clean or "\\\\" in word_clean):
                        target_files.append(word_clean)

                lock_failed = False
                locked_files = []
                for f in target_files:
                    try:
                        from niyam.core.swarm import acquire_lock
                        if not acquire_lock(f, actor_id, reason=f"Loop {run.id} step {step.name}", repo_root=root):
                            lock_failed = True
                            break
                        locked_files.append(f)
                    except Exception:
                        logger.debug("Exception caught", exc_info=True)

                if lock_failed:
                    for lf in locked_files:
                        try:
                            from niyam.core.swarm import release_lock
                            release_lock(lf, actor_id, repo_root=root)
                        except Exception:
                            logger.debug("Exception caught", exc_info=True)
                    try:
                        from niyam.core.swarm import deregister_agent
                        deregister_agent(actor_id, repo_root=root)
                    except Exception:
                        logger.debug("Exception caught", exc_info=True)
                    run.status = "failed"
                    reason = f"Blocked by swarm lock: resource '{target_files[0]}' is locked by another agent."
                    break

                agent_context = LoopRunner._load_agent_context(spec, root)

                req = AgentTaskRequest(
                    goal=spec.goal.description,
                    workspace_path=worktree_path,
                    action=step.action,
                    step_name=step.name,
                    dry_run=dry_run,
                    scenario=scenario,
                    iteration=iteration_idx,
                    context=agent_context,
                )

                result = LoopRunner._execute_iteration(req, step, adapter)

                for lf in locked_files:
                    try:
                        from niyam.core.swarm import release_lock
                        release_lock(lf, actor_id, repo_root=root)
                    except Exception:
                        logger.debug("Exception caught", exc_info=True)

                try:
                    from niyam.core.swarm import deregister_agent
                    deregister_agent(actor_id, repo_root=root)
                except Exception:
                    logger.debug("Exception caught", exc_info=True)

                if result.status == "needs_input":
                    run.status = "requires_approval"
                    reason = result.summary
                    break
                elif result.status == "blocked":
                    run.status = "failed"
                    reason = f"Blocked by actor: {result.summary}"
                    break

                step_result = LoopRunner._evaluate_iteration(result, step, actor_provider)

                # Scenario overrides: force terminal state at iteration 2 for
                # scenario-driven simulation paths.
                if scenario == "success" and iteration_idx == 2:
                    step_result["status"] = "passed"
                if scenario == "approval" and iteration_idx == 2:
                    step_result["human_approval_required"] = True

                reason = LoopRunner.process_step_result(run, spec, step_result, repo_root=root)
                iteration_idx += 1

        finally:
            if mode == "governed" and not dry_run:
                try:
                    if original_guard_config is not None:
                        guard_config_path.write_text(original_guard_config, encoding="utf-8")
                    elif guard_config_path.exists():
                        guard_config_path.unlink()
                except Exception:
                    logger.warning("Exception caught", exc_info=True)

        LoopRunner._finalize_run(run, root, worktree_path, use_worktree, branch_name)

        return run, reason
