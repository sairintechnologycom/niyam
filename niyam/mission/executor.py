"""Niyam mission executor — run tasks in an approved plan."""

from __future__ import annotations

import json
import os
import shlex
from pathlib import Path
import subprocess
import time
from datetime import datetime, timezone
import concurrent.futures
from rich.console import Console
from rich.panel import Panel

from niyam.core.config import get_niyam_dir, load_niyam_config, load_project_config
from niyam.mission.planner import DAGPlanner, resolve_mission_id, run_mission_replan

from niyam.mission.utils import print_lock, load_plan, save_plan
from niyam.core.swarm import (
    acquire_lock,
    append_ledger_message,
    deregister_agent,
    heartbeat,
    load_swarm_state,
    release_lock,
)
from niyam.mission.worktree import (
    is_git_repo,
    git_has_commits,
    merge_final_changes,
    delete_mission_branches,
    save_checkpoint,
)
from niyam.mission.task_runner import (
    log_execution_event,
    run_hooks,
    execute_single_task,
    check_overlap,
)
from niyam.mission.state_machine import transition_task, transition_mission


MAX_HEALING_RETRIES = 3
WORKSPACE_LOCK_RESOURCE = "__workspace__"


def _task_agent_id(mission_id: str, task_id: str) -> str:
    return f"{mission_id}:{task_id}"


def _task_lock_resources(task: dict) -> list[str]:
    """Return coarse-grained swarm lock resources for a task."""
    if not task.get("writes_files", True):
        return []
    resources = task.get("files_allowed") or task.get("allowed_files") or ["*"]
    cleaned = []
    for resource in resources:
        if resource == "*":
            cleaned.append(WORKSPACE_LOCK_RESOURCE)
        else:
            cleaned.append(str(resource))
    return sorted(set(cleaned))


def _holder_for_resource(repo_root: Path, resource: str) -> str | None:
    state = load_swarm_state(repo_root)
    lock = state.locks.get(resource)
    return lock.agent_id if lock else None


def _try_acquire_task_locks(
    task: dict,
    mission_id: str,
    repo_root: Path,
) -> bool:
    """Acquire swarm locks for the task, releasing partial acquisitions on failure."""
    task_id = task["id"]
    agent_id = _task_agent_id(mission_id, task_id)
    resources = _task_lock_resources(task)
    acquired: list[str] = []

    heartbeat(
        agent_id=agent_id,
        role=task.get("agent", "agent"),
        status="waiting",
        task_id=task_id,
        repo_root=repo_root,
    )
    for resource in resources:
        if acquire_lock(
            resource,
            agent_id,
            reason=f"Mission {mission_id} task {task_id}",
            repo_root=repo_root,
        ):
            acquired.append(resource)
            continue

        holder = _holder_for_resource(repo_root, resource) or "unknown"
        append_ledger_message(
            sender=agent_id,
            receiver=holder,
            action="request_lock",
            resource=resource,
            payload={"mission_id": mission_id, "task_id": task_id},
            repo_root=repo_root,
        )
        for acquired_resource in acquired:
            release_lock(acquired_resource, agent_id, repo_root=repo_root)
        return False

    heartbeat(
        agent_id=agent_id,
        role=task.get("agent", "agent"),
        status="busy",
        task_id=task_id,
        repo_root=repo_root,
    )
    return True


def _release_task_locks(task: dict, mission_id: str, repo_root: Path) -> None:
    task_id = task["id"]
    agent_id = _task_agent_id(mission_id, task_id)
    for resource in _task_lock_resources(task):
        release_lock(resource, agent_id, repo_root=repo_root)
    deregister_agent(agent_id, repo_root=repo_root)


def _build_task_healing_prompt(run_dir: Path, task_id: str) -> str:
    """Collect concise failure context for the next retry prompt."""
    task_dir = run_dir / "tasks" / task_id
    parts: list[str] = []

    validation_path = task_dir / "validation.json"
    if validation_path.exists():
        try:
            validation = json.loads(validation_path.read_text(encoding="utf-8"))
            failed = [item for item in validation if not item.get("success", False)]
            if failed:
                parts.append("Failed validation checks:")
                for item in failed[:5]:
                    parts.append(
                        f"- {item.get('name', 'validation')}: "
                        f"{item.get('command', 'unknown command')} "
                        f"{item.get('error', '')}".strip()
                    )
        except Exception:
            pass

    output_path = task_dir / "output.log"
    if output_path.exists():
        try:
            tail = output_path.read_text(encoding="utf-8", errors="ignore").splitlines()[-40:]
            if tail:
                parts.append("Recent task output:")
                parts.append("\n".join(tail))
        except Exception:
            pass

    return "\n".join(parts).strip() or "Previous attempt failed; inspect validation results and fix the smallest likely cause."


def execute_with_healing(
    task: dict,
    validation_command: str,
    agent_executor,
    repo_root: Path,
    console: Console,
    max_retries: int = MAX_HEALING_RETRIES,
) -> bool:
    """Execute a task, feed validation failures back to the agent, and checkpoint success."""
    correction_prompt = None
    for attempt in range(1, max_retries + 1):
        result = agent_executor(task, correction_prompt=correction_prompt)
        if result is False:
            correction_prompt = "The previous execution reported failure. Please provide a fix."
            continue

        validation = subprocess.run(
            shlex.split(validation_command),
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if validation.returncode == 0:
            save_checkpoint(task["id"], repo_root, console=console)
            return True

        error_text = (validation.stderr or validation.stdout or "").strip()
        correction_prompt = (
            "The previous code failed validation.\n\n"
            f"Command: {validation_command}\n"
            f"Exit code: {validation.returncode}\n"
            f"Error output:\n{error_text}\n\n"
            "Please provide a targeted fix and rerun validation."
        )
        console.print(
            f"[bold yellow]Validation failed for {task['id']}[/] "
            f"(attempt {attempt}/{max_retries}). Retrying with correction prompt."
        )

    return False


def run_mission_start(
    console: Console,
    parallel: int | None = None,
    worktree: bool | None = None,
    auto_heal: bool | None = None,
    non_interactive: bool = False,
    mission_id: str | None = None,
    auto_heal_execute: bool = False,
) -> None:
    """Start or resume the latest approved mission."""
    from niyam.core.config import find_niyam_root
    from niyam.core.errors import NiyamConfigError

    repo_root = find_niyam_root()
    if not repo_root:
        raise NiyamConfigError("Not a Niyam workspace. Run 'niyam init' first.")
    niyam_dir = get_niyam_dir(repo_root)

    mission_id = resolve_mission_id(niyam_dir, mission_id)
    if not mission_id:
        console.print("[bold red]Error:[/] No missions found.")
        raise SystemExit(1)

    run_dir = niyam_dir / "runs" / mission_id
    approval_path = run_dir / "approval.json"

    # Check approval
    approved = False
    if approval_path.exists():
        try:
            with open(approval_path, encoding="utf-8") as f:
                app_data = json.load(f)
            if app_data.get("approved", False):
                approved = True
        except Exception:
            pass

    if not approved:
        if non_interactive and os.environ.get("NIYAM_CI_AUTO_APPROVE") == "1":
            auto_approve_allowed = True
            try:
                config = load_niyam_config(repo_root)
                if hasattr(config.guard, "allow_ci_auto_approve"):
                    auto_approve_allowed = config.guard.allow_ci_auto_approve
            except Exception:
                pass

            if not auto_approve_allowed:
                console.print(
                    "[bold red]Error:[/] NIYAM_CI_AUTO_APPROVE=1 is set but "
                    "guard.allow_ci_auto_approve is disabled in niyam.yaml."
                )
                raise SystemExit(1)

            console.print(
                "[cyan]Non-interactive mode & NIYAM_CI_AUTO_APPROVE=1: Auto-approving mission...[/]"
            )
            approval_data = {
                "approved": True,
                "auto_approved": True,
                "timestamp": datetime.now(timezone.utc)
                .isoformat()
                .replace("+00:00", "Z"),
            }
            approval_path.write_text(
                json.dumps(approval_data, indent=2), encoding="utf-8"
            )
            log_execution_event(
                run_dir,
                "POLICY_WARNING",
                "",
                "Mission auto-approved via NIYAM_CI_AUTO_APPROVE=1 (approval gate bypassed).",
            )
        else:
            console.print("[bold red]Error:[/] Mission has not been approved.")
            raise SystemExit(1)

    # Load plan
    plan_data = load_plan(run_dir)
    mission_meta = plan_data.get("mission", {})
    status = mission_meta.get("status", "planned")

    if status in ("completed", "failed"):
        console.print(f"[yellow]Mission '{mission_id}' is already {status}.[/]")
        return

    # Determine execution options
    plan_parallel = mission_meta.get("parallel", 1)
    plan_worktree = mission_meta.get("worktree", True)
    plan_auto_heal = mission_meta.get("auto_heal", False)

    parallel_limit = parallel if parallel is not None else plan_parallel
    use_worktree = worktree if worktree is not None else plan_worktree
    auto_heal_enabled = auto_heal if auto_heal is not None else plan_auto_heal

    # Check Git repository requirement
    is_git = is_git_repo(repo_root)
    if use_worktree:
        if not is_git:
            console.print(
                "[yellow]Warning: Not a Git repository. Disabling worktree isolation.[/]"
            )
            use_worktree = False
        elif not git_has_commits(repo_root):
            console.print(
                "[yellow]Warning: Git repository has no commits. Disabling worktree isolation.[/]"
            )
            use_worktree = False
    # Save resolved settings and update status to running
    plan_data["mission"]["parallel"] = parallel_limit
    plan_data["mission"]["worktree"] = use_worktree
    plan_data["mission"]["auto_heal"] = auto_heal_enabled
    if (
        is_git
        and git_has_commits(repo_root)
        and not plan_data["mission"].get("base_sha")
    ):
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=repo_root, capture_output=True, text=True
        )
        if res.returncode == 0:
            plan_data["mission"]["base_sha"] = res.stdout.strip()
    
    save_plan(run_dir, plan_data)
    transition_mission(run_dir, "running", reason=f"Mission execution started (parallel={parallel_limit}, worktree={use_worktree}).")
    run_hooks("pre_mission", {"mission_id": mission_id}, niyam_dir, console)

    console.print(
        Panel(
            f"Mission ID: [bold cyan]{mission_id}[/]\n"
            f"Parallel Workers: [bold]{parallel_limit}[/]\n"
            f"Worktree Isolation: [bold]{'Enabled' if use_worktree else 'Disabled'}[/]\n"
            f"Auto-Heal: [bold]{'Enabled' if auto_heal_enabled else 'Disabled'}[/]",
            title="[bold cyan]Starting Niyam Mission[/]",
            border_style="cyan",
        )
    )

    # Read project.yaml validation commands
    project_config = None
    try:
        project_config = load_project_config(repo_root)
    except Exception:
        pass

    tasks = plan_data.get("tasks", [])
    completed_tasks = {t["id"] for t in tasks if t["status"] == "completed"}
    failed_tasks = {t["id"] for t in tasks if t["status"] == "failed"}
    running_tasks = set()
    futures_map = {}

    with concurrent.futures.ThreadPoolExecutor(max_workers=parallel_limit) as executor:
        while True:
            # Check if mission has been paused from outside
            current_plan = load_plan(run_dir)
            if current_plan["mission"]["status"] == "paused":
                with print_lock:
                    console.print(
                        "[yellow]Mission execution paused. Waiting for active tasks to finish...[/]"
                    )
                if futures_map:
                    done, _ = concurrent.futures.wait(futures_map.keys())
                    _process_finished_tasks(
                        done,
                        futures_map,
                        running_tasks,
                        completed_tasks,
                        failed_tasks,
                        current_plan,
                        run_dir,
                        repo_root,
                        mission_id,
                        auto_heal_enabled,
                        console,
                    )

                    # Check if any task failed after processing
                    if failed_tasks:
                        # Pause mission to allow intervention or auto-heal
                        transition_mission(run_dir, "paused", reason="Mission paused due to task failures.")

                        if auto_heal_enabled:
                            with print_lock:
                                console.print(Panel(
                                    "[bold yellow]⚡ Roadblock Detected.[/]\n"
                                    "Autonomous resilience triggered. Invoking AI re-planner...",
                                    title="[bold yellow]Auto-Heal Active[/]",
                                    border_style="yellow"
                                ))

                            try:
                                run_mission_replan(
                                    console=console,
                                    mission_id=mission_id,
                                    reason="Automatic self-correction after repeated task failure."
                                )
                                # Re-load plan and continue the loop
                                current_plan = load_plan(run_dir)
                                failed_tasks.clear() # Clear failed set to allow retry of new plan

                                # Re-approve if auto-heal is on
                                current_plan["mission"]["status"] = "approved"
                                save_plan(run_dir, current_plan)

                                transition_mission(run_dir, "running", reason="Resuming after auto-heal.")
                                continue
                            except Exception as e:
                                with print_lock:
                                    console.print(f"[bold red]Auto-heal failed:[/] {e}")

                        # If not auto-heal, or heal failed, exit the loop
                        break

                run_hooks(
                    "post_mission",
                    {"mission_id": mission_id, "mission_status": "paused"},
                    niyam_dir,
                    console,
                )
                return

            # Avoid busy-waiting and lock contention
            time.sleep(0.1)

            # Budget Check
            config = None
            try:
                config = load_niyam_config(repo_root)
            except Exception:
                pass
                
            if config and config.governance and config.governance.budget:
                budget = config.governance.budget
                try:
                    from niyam.core.analytics import PerformanceMetrics
                    metrics = PerformanceMetrics(repo_root).get_mission_metrics(mission_id)
                    if metrics:
                        # 1. Cost check
                        if budget.max_mission_cost_usd is not None:
                            current_cost = metrics.get("total_cost_usd", 0.0)
                            if current_cost > budget.max_mission_cost_usd:
                                transition_mission(run_dir, "failed", reason=f"Mission budget breached: ${current_cost:.4f} > ${budget.max_mission_cost_usd:.4f}")
                                with print_lock:
                                    console.print(Panel(
                                        f"[bold red]🛑 Mission Cost Budget Breached![/]\n"
                                        f"Cost: ${current_cost:.4f} / Limit: ${budget.max_mission_cost_usd:.4f}\n"
                                        f"Mission has been automatically failed.",
                                        title="[bold red]Budget Enforcer[/]",
                                        border_style="red"
                                    ))
                                break
                            elif current_cost >= 0.8 * budget.max_mission_cost_usd:
                                with print_lock:
                                    console.print(f"[bold yellow]⚠️ Budget Alert:[/] Mission cost has reached 80% of the limit (${current_cost:.4f} / ${budget.max_mission_cost_usd:.4f})")

                        # 2. Token check
                        if budget.max_mission_tokens is not None:
                            current_tokens = metrics.get("total_tokens", 0)
                            if current_tokens > budget.max_mission_tokens:
                                transition_mission(run_dir, "failed", reason=f"Mission token budget breached: {current_tokens} > {budget.max_mission_tokens}")
                                with print_lock:
                                    console.print(Panel(
                                        f"[bold red]🛑 Mission Token Budget Breached![/]\n"
                                        f"Tokens: {current_tokens} / Limit: {budget.max_mission_tokens}\n"
                                        f"Mission has been automatically failed.",
                                        title="[bold red]Budget Enforcer[/]",
                                        border_style="red"
                                    ))
                                break
                            elif current_tokens >= 0.8 * budget.max_mission_tokens:
                                with print_lock:
                                    console.print(f"[bold yellow]⚠️ Budget Alert:[/] Mission tokens have reached 80% of the limit ({current_tokens} / {budget.max_mission_tokens})")
                except Exception:
                    pass


            # Find ready tasks via DAGPlanner (single scheduling source of truth)
            tasks = current_plan.get("tasks", [])
            task_by_id = {task["id"]: task for task in tasks}
            ready_tasks, skip_tasks = DAGPlanner().ready_tasks(
                tasks, exclude_ids=set(running_tasks)
            )
            for t in skip_tasks:
                transition_task(
                    run_dir, t["id"], "skipped", reason="Dependency failed."
                )

            # Submit ready tasks up to concurrency capacity
            for t in ready_tasks:
                if len(running_tasks) < parallel_limit:
                    t_id = t["id"]
                    
                    # ── Phase 10: Manual Approval Gate ─────────────────────────
                    is_recovery = t.get("type") == "recovery"
                    if (is_recovery or t.get("approval_required", False)) and t["status"] not in ("approved", "retry_ready"):
                        # If the task requires approval but hasn't been approved yet
                        if non_interactive or (is_recovery and auto_heal_execute):
                            with print_lock:
                                console.print(f"[{t_id}] [yellow]Auto-approving task '{t_id}' (Type: {t.get('type')})[/]")
                            t["status"] = "approved"
                            save_plan(run_dir, current_plan)
                        else:
                            label = "recovery" if is_recovery else "approval_required"
                            transition_task(run_dir, t_id, "awaiting_approval", reason=f"Task of type '{label}' requires manual human approval.")
                            with print_lock:
                                console.print(Panel(
                                    f"Task [cyan]{t_id}[/] ({label}) requires manual approval before execution.\n"
                                    f"Run: [bold]niyam mission approve-task {t_id}[/] to proceed.",
                                    title="[bold yellow]Approval Required[/]",
                                    border_style="yellow"
                                ))
                            
                            # If no other tasks are running, we must exit and wait
                            if not running_tasks:
                                transition_mission(run_dir, "paused", reason=f"Mission paused waiting for approval of task {t_id}.")
                                return
                            
                            # Skip this task for now
                            continue

                    t_writes = t.get("writes_files", True)
                    t_files = t.get("files_allowed") or t.get("allowed_files") or ["*"]
                    has_overlap = False
                    for active_id in running_tasks:
                        active_task = task_by_id[active_id]
                        active_writes = active_task.get("writes_files", True)
                        
                        # Collision check: only needed if at least one task writes files
                        if t_writes or active_writes:
                            active_files = (
                                active_task.get("files_allowed")
                                or active_task.get("allowed_files")
                                or ["*"]
                            )
                            if check_overlap(t_files, active_files):
                                has_overlap = True
                                break
                    if has_overlap:
                        continue

                    if not _try_acquire_task_locks(t, mission_id, repo_root):
                        with print_lock:
                            console.print(
                                f"[{t_id}] [yellow]Waiting for swarm resource locks.[/]"
                            )
                        continue

                    t_id = t["id"]
                    running_tasks.add(t_id)
                    
                    # transition_task will handle status update and logging
                    transition_task(run_dir, t_id, "queued", reason=f"Task queued for execution: {t['title']}")

                    with print_lock:
                        console.print(
                            Panel(
                                f"Queued Task [cyan]{t_id}[/]: {t['title']}\nAgent: [bold]{t['agent']}[/]",
                                title=f"[bold]Task {t_id}[/]",
                                border_style="cyan",
                            )
                        )

                    future = executor.submit(
                        execute_single_task,
                        task=t,
                        run_dir=run_dir,
                        niyam_dir=niyam_dir,
                        repo_root=repo_root,
                        mission_id=mission_id,
                        use_worktree=use_worktree,
                        project_config=project_config,
                        console=console,
                        non_interactive=non_interactive,
                    )
                    futures_map[future] = t

            if not futures_map:
                break

            done, _ = concurrent.futures.wait(
                futures_map.keys(), return_when=concurrent.futures.FIRST_COMPLETED
            )

            _process_finished_tasks(
                done,
                futures_map,
                running_tasks,
                completed_tasks,
                failed_tasks,
                current_plan,
                run_dir,
                repo_root,
                mission_id,
                auto_heal_enabled,
                console,
            )

            # Check if any task failed after processing
            if failed_tasks:
                # Pause mission to allow intervention or auto-heal
                transition_mission(run_dir, "paused", reason="Mission paused due to task failures.")

                if auto_heal_enabled:
                    with print_lock:
                        console.print(Panel(
                            "[bold yellow]⚡ Roadblock Detected.[/]\n"
                            "Autonomous resilience triggered. Invoking AI re-planner...",
                            title="[bold yellow]Auto-Heal Active[/]",
                            border_style="yellow"
                        ))

                    try:
                        run_mission_replan(
                            console=console,
                            mission_id=mission_id,
                            reason="Automatic self-correction after repeated task failure."
                        )
                        # Re-load plan and continue the loop
                        current_plan = load_plan(run_dir)
                        failed_tasks.clear() # Clear failed set to allow retry of new plan

                        # Re-approve if auto-heal is on
                        current_plan["mission"]["status"] = "approved"
                        save_plan(run_dir, current_plan)

                        transition_mission(run_dir, "running", reason="Resuming after auto-heal.")
                        continue
                    except Exception as e:
                        with print_lock:
                            console.print(f"[bold red]Auto-heal failed:[/] {e}")

                # If not auto-heal, or heal failed, exit the loop
                break



    # Determine final mission status
    final_plan = load_plan(run_dir)
    mission_status = final_plan.get("mission", {}).get("status")
    tasks_list = final_plan.get("tasks", [])
    any_failed = any(t["status"] == "failed" for t in tasks_list)
    any_skipped_due_to_failure = any(t["status"] == "skipped" for t in tasks_list)
    
    # If we are here and not failed, it means we finished all tasks successfully
    # UNLESS we exited because of a pause check (but that returns early)
    
    if mission_status == "failed" or any_failed or any_skipped_due_to_failure:
        if mission_status != "failed":
            transition_mission(run_dir, "failed", reason="Mission execution failed due to task failures.")
        run_hooks(
            "post_mission",
            {"mission_id": mission_id, "mission_status": "failed"},
            niyam_dir,
            console,
        )
        console.print(
            Panel(
                "[bold red]❌ Mission execution failed.[/]",
                title="[bold red]Mission Failed[/]",
                border_style="red",
            )
        )
        raise SystemExit(1)

    # Success integration (merge back if worktree was used)
    if use_worktree and is_git:
        try:
            merge_result = merge_final_changes(
                repo_root, mission_id, tasks_list, console
            )
            if not merge_result.success and merge_result.recovery_tasks:
                # Append recovery tasks and pause for human approval
                plan_now = load_plan(run_dir)
                existing = {t["id"] for t in plan_now.get("tasks", [])}
                for rec in merge_result.recovery_tasks:
                    if rec["id"] not in existing:
                        plan_now.setdefault("tasks", []).append(rec)
                        existing.add(rec["id"])
                save_plan(run_dir, plan_now)
                rec_ids = ", ".join(r["id"] for r in merge_result.recovery_tasks)
                console.print(
                    Panel(
                        f"[bold yellow]Merge conflict(s) detected.[/]\n"
                        f"Created recovery task(s): [cyan]{rec_ids}[/]\n"
                        f"Approve with: [bold]niyam mission approve-task <id>[/]\n"
                        f"Then resume: [bold]niyam mission start[/]",
                        title="[bold yellow]Merge Recovery Required[/]",
                        border_style="yellow",
                    )
                )
                transition_mission(
                    run_dir,
                    "paused",
                    reason=(
                        f"Paused for merge-conflict recovery: {merge_result.message}"
                    ),
                )
                run_hooks(
                    "post_mission",
                    {
                        "mission_id": mission_id,
                        "mission_status": "paused",
                        "reason": "merge_conflict_recovery",
                    },
                    niyam_dir,
                    console,
                )
                return

            if merge_result.success:
                delete_mission_branches(
                    repo_root, mission_id, tasks_list, console
                )
        except Exception as e:
            console.print(f"[bold red]Error integrating final changes:[/] {e}")
            transition_mission(run_dir, "failed", reason=f"Merge error: {e}")
            raise SystemExit(1)

    # Complete mission
    transition_mission(run_dir, "completed", reason="All tasks completed successfully.")
    run_hooks(
        "post_mission",
        {"mission_id": mission_id, "mission_status": "completed"},
        niyam_dir,
        console,
    )
    console.print(
        Panel(
            "[bold green]✓ Mission execution completed successfully![/]\nRun `niyam mission report` to generate evidence.",
            title="[bold green]Mission Success[/]",
            border_style="green",
        )
    )


def _process_finished_tasks(
    done: set[concurrent.futures.Future],
    futures_map: dict,
    running_tasks: set,
    completed_tasks: set,
    failed_tasks: set,
    plan_data: dict,
    run_dir: Path,
    repo_root: Path,
    mission_id: str,
    auto_heal_enabled: bool,
    console: Console,
) -> None:
    """Helper to process results of finished tasks and update plan."""
    from niyam.mission.utils import save_plan, load_plan

    for future in done:
        t = futures_map.pop(future)
        t_id = t["id"]
        if t_id in running_tasks:
            running_tasks.remove(t_id)

        try:
            success = future.result()
            if success:
                completed_tasks.add(t_id)
                if auto_heal_enabled and is_git_repo(repo_root) and git_has_commits(repo_root):
                    try:
                        save_checkpoint(t_id, repo_root, console=console)
                    except Exception as e:
                        with print_lock:
                            console.print(
                                f"[{t_id}] [dim yellow]Checkpoint skipped: {e}[/]"
                            )
                transition_task(
                    run_dir, t_id, "completed", reason=f"Completed task: {t['title']}"
                )
                with print_lock:
                    console.print(
                        f"[bold green]✓[/] Task {t_id} completed successfully.\n"
                    )
            else:
                # Handle Retry Logic
                current_plan = load_plan(run_dir)
                target_task = next((task for task in current_plan["tasks"] if task["id"] == t_id), None)
                if target_task:
                    retry_count = target_task.get("retry_count", 0) + 1
                    max_retries = target_task.get("max_retries", 2)
                    target_task["retry_count"] = retry_count
                    
                    # Persist retry_count update before status transition
                    save_plan(run_dir, current_plan)
                    
                    if retry_count < max_retries:
                        target_task["healing_prompt"] = _build_task_healing_prompt(
                            run_dir, t_id
                        )
                        save_plan(run_dir, current_plan)
                        transition_task(
                            run_dir, t_id, "retry_ready", reason=f"Task failed (attempt {retry_count}/{max_retries}). Retrying..."
                        )
                        with print_lock:
                            console.print(
                                f"[bold yellow]⚠[/] Task {t_id} failed (attempt {retry_count}/{max_retries}). Re-queueing for retry.\n"
                            )
                    else:
                        failed_tasks.add(t_id)
                        transition_task(
                            run_dir, t_id, "failed", reason=f"Task failed after {max_retries} attempts."
                        )
                        with print_lock:
                            console.print(
                                f"[bold red]❌[/] Task {t_id} failed after maximum retries ({max_retries}).\n"
                            )
                else:
                    failed_tasks.add(t_id)
                    transition_task(run_dir, t_id, "failed", reason="Task execution failed.")
                    with print_lock:
                        console.print(f"[bold red]❌[/] Task {t_id} failed.\n")
        except Exception as e:
            failed_tasks.add(t_id)
            transition_task(
                run_dir, t_id, "failed", reason=f"Exception during task execution: {e}"
            )
            with print_lock:
                console.print(f"[bold red]❌[/] Task {t_id} failed with exception: {e}\n")
        finally:
            _release_task_locks(t, mission_id, repo_root)


def run_mission_pause(console: Console, mission_id: str | None = None) -> None:
    """Pause the currently running mission."""
    from niyam.core.config import find_niyam_root
    from niyam.core.errors import NiyamConfigError

    repo_root = find_niyam_root()
    if not repo_root:
        raise NiyamConfigError("Not a Niyam workspace. Run 'niyam init' first.")
    niyam_dir = get_niyam_dir(repo_root)

    mission_id = resolve_mission_id(niyam_dir, mission_id)
    if not mission_id:
        console.print("[bold red]Error:[/] No missions found.")
        raise SystemExit(1)

    run_dir = niyam_dir / "runs" / mission_id
    plan_data = load_plan(run_dir)
    status = plan_data["mission"]["status"]

    if status != "running":
        console.print(f"[yellow]Mission is not running (current status: {status}).[/]")
        return

    transition_mission(run_dir, "paused", reason="Mission paused by user.")
    console.print(f"[bold green]✓[/] Mission '[cyan]{mission_id}[/]' has been paused.")


def run_mission_resume(
    console: Console,
    parallel: int | None = None,
    worktree: bool | None = None,
    non_interactive: bool = False,
    mission_id: str | None = None,
    auto_heal_execute: bool = False,
) -> None:
    """Resume a paused mission."""
    from niyam.core.config import find_niyam_root
    from niyam.core.errors import NiyamConfigError

    repo_root = find_niyam_root()
    if not repo_root:
        raise NiyamConfigError("Not a Niyam workspace. Run 'niyam init' first.")
    niyam_dir = get_niyam_dir(repo_root)

    mission_id = resolve_mission_id(niyam_dir, mission_id)
    if not mission_id:
        console.print("[bold red]Error:[/] No missions found.")
        raise SystemExit(1)

    run_dir = niyam_dir / "runs" / mission_id
    plan_data = load_plan(run_dir)
    status = plan_data["mission"]["status"]

    if status != "paused":
        console.print(f"[yellow]Mission is not paused (current status: {status}).[/]")
        return

    # Start the execution
    run_mission_start(
        console,
        parallel=parallel,
        worktree=worktree,
        non_interactive=non_interactive,
        mission_id=mission_id,
        auto_heal_execute=auto_heal_execute,
    )


def run_mission_retry(
    console: Console,
    parallel: int | None = None,
    worktree: bool | None = None,
    non_interactive: bool = False,
    mission_id: str | None = None,
    auto_heal_execute: bool = False,
) -> None:
    """Retry failed tasks of the latest mission."""
    from niyam.core.config import find_niyam_root
    from niyam.core.errors import NiyamConfigError

    repo_root = find_niyam_root()
    if not repo_root:
        raise NiyamConfigError("Not a Niyam workspace. Run 'niyam init' first.")
    niyam_dir = get_niyam_dir(repo_root)

    mission_id = resolve_mission_id(niyam_dir, mission_id)
    if not mission_id:
        console.print("[bold red]Error:[/] No missions found.")
        raise SystemExit(1)

    run_dir = niyam_dir / "runs" / mission_id
    plan_data = load_plan(run_dir)

    tasks = plan_data.get("tasks", [])
    failed_any = False

    def reset_downstream(task_id: str):
        # We need to reload plan every time because transition_task saves to disk
        current_plan = load_plan(run_dir)
        for t in current_plan.get("tasks", []):
            if task_id in t.get("depends_on", []) and t["status"] == "skipped":
                transition_task(run_dir, t["id"], "planned", reason="Upstream task retried.")
                reset_downstream(t["id"])

    # First pass: find all failed/skipped tasks that should be retried directly
    to_retry = [t["id"] for t in tasks if t["status"] in ("failed", "skipped")]
    
    for t_id in to_retry:
        transition_task(run_dir, t_id, "retry_ready", reason="Marked for retry.")
        failed_any = True
        reset_downstream(t_id)

    if not failed_any:
        console.print("[yellow]No failed or skipped tasks found to retry.[/]")
        return

    transition_mission(run_dir, "approved", reason="Retrying failed/skipped tasks.")
    console.print(
        f"[bold green]✓[/] Re-queued tasks. Resuming mission [cyan]{mission_id}[/]..."
    )
    run_mission_start(
        console,
        parallel=parallel,
        worktree=worktree,
        non_interactive=non_interactive,
        mission_id=mission_id,
        auto_heal_execute=auto_heal_execute,
    )


def run_mission_skip(
    task_id: str,
    console: Console,
    parallel: int | None = None,
    worktree: bool | None = None,
    non_interactive: bool = False,
    mission_id: str | None = None,
) -> None:
    """Skip a specific task and resume execution."""
    from niyam.core.config import find_niyam_root
    from niyam.core.errors import NiyamConfigError

    repo_root = find_niyam_root()
    if not repo_root:
        raise NiyamConfigError("Not a Niyam workspace. Run 'niyam init' first.")
    niyam_dir = get_niyam_dir(repo_root)

    mission_id = resolve_mission_id(niyam_dir, mission_id)
    if not mission_id:
        console.print("[bold red]Error:[/] No missions found.")
        raise SystemExit(1)

    run_dir = niyam_dir / "runs" / mission_id
    plan_data = load_plan(run_dir)

    tasks = plan_data.get("tasks", [])
    target_task = None
    for t in tasks:
        if t["id"] == task_id:
            target_task = t
            break

    if not target_task:
        console.print(
            f"[bold red]Error:[/] Task '{task_id}' not found in mission plan."
        )
        raise SystemExit(1)

    transition_task(run_dir, task_id, "skipped", reason="Task skipped by user intervention.", actor="human")
    transition_mission(run_dir, "approved", reason="Resuming after task skip.")
    console.print(
        f"[bold green]✓[/] Marked task [cyan]{task_id}[/] as skipped. Resuming mission..."
    )
    run_mission_start(
        console,
        parallel=parallel,
        worktree=worktree,
        non_interactive=non_interactive,
        mission_id=mission_id,
    )


def run_mission_rollback(console: Console, mission_id: str | None = None) -> None:
    """Rollback all workspace changes back to the start of the latest mission."""
    from niyam.core.config import find_niyam_root
    from niyam.core.errors import NiyamConfigError

    repo_root = find_niyam_root()
    if not repo_root:
        raise NiyamConfigError("Not a Niyam workspace. Run 'niyam init' first.")
    niyam_dir = get_niyam_dir(repo_root)

    mission_id = resolve_mission_id(niyam_dir, mission_id)
    if not mission_id:
        console.print("[bold red]Error:[/] No missions found.")
        raise SystemExit(1)

    run_dir = niyam_dir / "runs" / mission_id
    plan_data = load_plan(run_dir)
    base_sha = plan_data["mission"].get("base_sha")

    if not base_sha:
        console.print(
            "[yellow]No base commit SHA recorded for this mission. Cannot rollback automatically.[/]"
        )
        return

    console.print(
        f"[cyan]Rolling back changes to base commit [bold]{base_sha}[/]...[/]"
    )
    res = subprocess.run(
        ["git", "checkout", base_sha, "--", "."],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    if res.returncode == 0:
        transition_mission(run_dir, "rolled_back", reason="Workspace rolled back to base commit by user.", actor="human")
        console.print("[bold green]✓[/] Workspace rolled back successfully.")
    else:
        console.print(
            f"[bold red]Failed to rollback changes:[/] {res.stderr or res.stdout}"
        )
