"""Niyam mission executor — run tasks in an approved plan."""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import threading
from datetime import datetime, timezone
import yaml
import concurrent.futures
from rich.console import Console
from rich.panel import Panel

from niyam.core.config import get_niyam_dir, load_niyam_config, load_project_config
from niyam.mission.planner import resolve_mission_id
from niyam.mission.utils import print_lock
from niyam.mission.worktree import (
    is_git_repo,
    git_has_commits,
    merge_final_changes,
    delete_mission_branches,
)
from niyam.mission.task_runner import (
    load_plan,
    save_plan,
    log_execution_event,
    run_hooks,
    execute_single_task,
    check_overlap,
)


def run_mission_start(
    console: Console,
    parallel: int | None = None,
    worktree: bool | None = None,
    non_interactive: bool = False,
    mission_id: str | None = None,
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

    parallel_limit = parallel if parallel is not None else plan_parallel
    use_worktree = worktree if worktree is not None else plan_worktree

    # Check Git repository requirement
    is_git = is_git_repo(repo_root)
    if use_worktree:
        if not is_git:
            if worktree is True:
                console.print(
                    "[bold red]Error:[/] Git worktree isolation was requested, but this is not a Git repository."
                )
                raise SystemExit(1)
            else:
                if parallel_limit > 1:
                    console.print(
                        "[bold red]Error:[/] Parallel execution (concurrency > 1) requires a Git repository for worktree isolation."
                    )
                    raise SystemExit(1)
                else:
                    use_worktree = False
        elif not git_has_commits(repo_root):
            if worktree is True:
                console.print(
                    "[bold red]Error:[/] Git worktree isolation requires the repository to have at least one commit."
                )
                raise SystemExit(1)
            else:
                if parallel_limit > 1:
                    console.print(
                        "[bold red]Error:[/] Parallel execution (concurrency > 1) requires a Git repository with at least one commit for worktree isolation."
                    )
                    raise SystemExit(1)
                else:
                    use_worktree = False

    # Save resolved settings and update status to running
    plan_data["mission"]["parallel"] = parallel_limit
    plan_data["mission"]["worktree"] = use_worktree
    plan_data["mission"]["status"] = "running"
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
    log_execution_event(
        run_dir,
        "MISSION_STARTED",
        "",
        f"Mission execution started (parallel={parallel_limit}, worktree={use_worktree}).",
    )
    run_hooks("pre_mission", {"mission_id": mission_id}, niyam_dir, console)

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
                        plan_data,
                        run_dir,
                        console,
                    )
                run_hooks(
                    "post_mission",
                    {"mission_id": mission_id, "mission_status": "paused"},
                    niyam_dir,
                    console,
                )
                return

            # Find ready tasks
            ready_tasks = []
            task_by_id = {task["id"]: task for task in tasks}
            for t in tasks:
                t_id = t["id"]
                if t["status"] == "pending" and t_id not in running_tasks:
                    deps = t.get("depends_on", [])
                    finished_statuses = {"completed", "failed", "skipped"}
                    dep_tasks = [task_by_id[dep] for dep in deps if dep in task_by_id]

                    if all(dt["status"] in finished_statuses for dt in dep_tasks):
                        if any(dt["status"] == "failed" for dt in dep_tasks):
                            t["status"] = "skipped"
                            save_plan(run_dir, plan_data)
                            log_execution_event(
                                run_dir,
                                "TASK_SKIPPED",
                                t_id,
                                "Dependency failed, skipping task.",
                            )
                            continue
                        ready_tasks.append(t)

            # Submit ready tasks up to concurrency capacity
            for t in ready_tasks:
                if len(running_tasks) < parallel_limit:
                    t_files = t.get("files_allowed") or t.get("allowed_files") or ["*"]
                    has_overlap = False
                    for active_id in running_tasks:
                        active_task = task_by_id[active_id]
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

                    t_id = t["id"]
                    running_tasks.add(t_id)
                    t["status"] = "running"
                    
                    # Update status from disk to avoid overwriting external changes
                    disk_plan = load_plan(run_dir)
                    plan_data["mission"]["status"] = disk_plan["mission"]["status"]
                    
                    save_plan(run_dir, plan_data)
                    log_execution_event(
                        run_dir, "TASK_STARTED", t_id, f"Running task: {t['title']}"
                    )

                    with print_lock:
                        console.print(
                            Panel(
                                f"Running Task [cyan]{t_id}[/]: {t['title']}\nAgent: [bold]{t['agent']}[/]",
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
                plan_data,
                run_dir,
                console,
            )

    # Determine final mission status
    final_plan = load_plan(run_dir)
    tasks_list = final_plan.get("tasks", [])
    any_failed = any(t["status"] == "failed" for t in tasks_list)
    any_skipped_due_to_failure = any(t["status"] == "skipped" for t in tasks_list)
    
    # If we are here and not failed, it means we finished all tasks successfully
    # UNLESS we exited because of a pause check (but that returns early)
    
    if any_failed or any_skipped_due_to_failure:
        final_plan["mission"]["status"] = "failed"
        save_plan(run_dir, final_plan)
        log_execution_event(
            run_dir,
            "MISSION_FAILED",
            "",
            "Mission execution failed due to task failures.",
        )
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
            merge_final_changes(repo_root, mission_id, tasks_list, console)
            delete_mission_branches(repo_root, mission_id, tasks_list, console)
        except Exception as e:
            console.print(f"[bold red]Error integrating final changes:[/] {e}")
            final_plan["mission"]["status"] = "failed"
            save_plan(run_dir, final_plan)
            raise SystemExit(1)

    # Complete mission
    final_plan["mission"]["status"] = "completed"
    save_plan(run_dir, final_plan)
    log_execution_event(
        run_dir, "MISSION_COMPLETED", "", "All tasks completed successfully."
    )
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
    console: Console,
) -> None:
    """Helper to process results of finished tasks and update plan."""
    for future in done:
        t = futures_map.pop(future)
        t_id = t["id"]
        if t_id in running_tasks:
            running_tasks.remove(t_id)

        try:
            success = future.result()
            if success:
                t["status"] = "completed"
                completed_tasks.add(t_id)
                
                # Update mission status from disk to avoid overwriting pause
                disk_plan = load_plan(run_dir)
                plan_data["mission"]["status"] = disk_plan["mission"]["status"]
                
                save_plan(run_dir, plan_data)
                log_execution_event(
                    run_dir,
                    "TASK_COMPLETED",
                    t_id,
                    f"Completed task: {t['title']}",
                )
                with print_lock:
                    console.print(
                        f"[bold green]✓[/] Task {t_id} completed successfully.\n"
                    )
            else:
                t["status"] = "failed"
                failed_tasks.add(t_id)
                
                # Update mission status from disk to avoid overwriting pause
                disk_plan = load_plan(run_dir)
                plan_data["mission"]["status"] = disk_plan["mission"]["status"]
                
                save_plan(run_dir, plan_data)
                log_execution_event(
                    run_dir, "TASK_FAILED", t_id, "Task execution failed."
                )
                with print_lock:
                    console.print(f"[bold red]❌[/] Task {t_id} failed.\n")
        except Exception as e:
            t["status"] = "failed"
            failed_tasks.add(t_id)
            
            # Update mission status from disk to avoid overwriting pause
            disk_plan = load_plan(run_dir)
            plan_data["mission"]["status"] = disk_plan["mission"]["status"]
            
            save_plan(run_dir, plan_data)
            log_execution_event(
                run_dir,
                "TASK_FAILED",
                t_id,
                f"Exception during task execution: {e}",
            )
            with print_lock:
                console.print(
                    f"[bold red]❌[/] Task {t_id} failed with exception: {e}\n"
                )


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

    plan_data["mission"]["status"] = "paused"
    save_plan(run_dir, plan_data)
    log_execution_event(run_dir, "MISSION_PAUSED", "", "Mission paused by user.")
    console.print(f"[bold green]✓[/] Mission '[cyan]{mission_id}[/]' has been paused.")


def run_mission_resume(
    console: Console,
    parallel: int | None = None,
    worktree: bool | None = None,
    non_interactive: bool = False,
    mission_id: str | None = None,
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
    )


def run_mission_retry(
    console: Console,
    parallel: int | None = None,
    worktree: bool | None = None,
    non_interactive: bool = False,
    mission_id: str | None = None,
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
        for t in tasks:
            if task_id in t.get("depends_on", []) and t["status"] == "skipped":
                t["status"] = "pending"
                reset_downstream(t["id"])

    for t in tasks:
        if t["status"] in ("failed", "skipped"):
            t["status"] = "pending"
            failed_any = True
            reset_downstream(t["id"])

    if not failed_any:
        console.print("[yellow]No failed or skipped tasks found to retry.[/]")
        return

    plan_data["mission"]["status"] = "approved"
    save_plan(run_dir, plan_data)
    log_execution_event(
        run_dir, "MISSION_RETRIED", "", "Retrying failed/skipped tasks."
    )
    console.print(
        f"[bold green]✓[/] Re-queued tasks. Resuming mission [cyan]{mission_id}[/]..."
    )
    run_mission_start(
        console,
        parallel=parallel,
        worktree=worktree,
        non_interactive=non_interactive,
        mission_id=mission_id,
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

    target_task["status"] = "skipped"
    plan_data["mission"]["status"] = "approved"
    save_plan(run_dir, plan_data)
    log_execution_event(
        run_dir, "TASK_SKIPPED_BY_USER", task_id, "Task skipped by user intervention."
    )
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
        plan_data["mission"]["status"] = "failed"
        save_plan(run_dir, plan_data)
        console.print("[bold green]✓[/] Workspace rolled back successfully.")
    else:
        console.print(
            f"[bold red]Failed to rollback changes:[/] {res.stderr or res.stdout}"
        )
