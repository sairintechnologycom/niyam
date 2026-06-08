"""Niyam CLI mission commands."""

from __future__ import annotations

from typing import Annotated, Optional

import typer
import yaml
from rich.panel import Panel
from rich.table import Table

from niyam.cli import console, mission_app
from niyam.cli.main_cmds import Runtime
from niyam.mission.state_machine import transition_task, transition_mission


@mission_app.command("plan")
def mission_plan(
    requirements: Annotated[
        str, typer.Argument(help="Path to requirements markdown file.")
    ],
    strict: Annotated[
        bool,
        typer.Option(
            "--strict",
            help="Fail if AI-powered planning fails, instead of falling back.",
        ),
    ] = False,
    template: Annotated[
        Optional[str],
        typer.Option(
            "--template",
            "-t",
            help="Use a mission template for planning.",
        ),
    ] = None,
    runtime: Annotated[
        Optional[Runtime],
        typer.Option("--runtime", "-r", help="Runtime override for this mission."),
    ] = None,
) -> None:
    """Generate a mission plan from a requirements file."""
    from niyam.mission.planner import run_mission_plan

    try:
        run_mission_plan(
            requirements_path=requirements,
            strict=strict,
            console=console,
            template=template,
            runtime_override=runtime.value if runtime else None,
        )
    except Exception as e:
        console.print(f"[bold red]Error:[/] {e}")
        raise typer.Exit(1)


@mission_app.command("show")
def mission_show(
    mission_id: Annotated[
        Optional[str],
        typer.Option("--mission", help="Mission ID to display."),
    ] = None,
) -> None:
    """Display tasks and configuration of the latest planned or active mission."""
    from niyam.core.config import find_niyam_root, get_niyam_dir
    from niyam.core.errors import NiyamConfigError
    from niyam.mission.planner import resolve_mission_id

    repo_root = find_niyam_root()
    if not repo_root:
        raise NiyamConfigError("Not a Niyam workspace. Run 'niyam init' first.")
    niyam_dir = get_niyam_dir(repo_root)

    mission_id = resolve_mission_id(niyam_dir, mission_id)
    if not mission_id:
        console.print("[bold red]Error:[/] No missions found.")
        raise typer.Exit(1)

    run_dir = niyam_dir / "runs" / mission_id
    plan_path = run_dir / "mission-plan.yaml"

    if not plan_path.exists():
        console.print(f"[bold red]Error:[/] Mission plan for '{mission_id}' not found.")
        raise typer.Exit(1)

    with open(plan_path, encoding="utf-8") as f:
        plan_data = yaml.safe_load(f) or {}

    tasks = plan_data.get("tasks", [])
    mission_meta = plan_data.get("mission", {})

    table = Table(title=f"Mission: [cyan]{mission_id}[/]", expand=True)
    table.add_column("ID", style="bold magenta", justify="center", width=4)
    table.add_column("Title")
    table.add_column("Agent", style="yellow")
    table.add_column("Runtime", style="cyan")
    table.add_column("Depends On", style="dim white")
    table.add_column("Writes", style="green")
    table.add_column("Status", style="bold")

    status_colors = {
        "planned": "white",
        "running": "yellow",
        "completed": "green",
        "failed": "red",
        "skipped": "dim white",
    }

    for t in tasks:
        t_id = t.get("id")
        t_title = t.get("title")
        t_agent = t.get("agent")
        t_rt = t.get("runtime") or mission_meta.get("orchestrator", "claude")
        t_deps = ", ".join(t.get("depends_on", [])) or "-"
        t_writes = "Yes" if t.get("writes_files", True) else "No"
        t_status = t.get("status", "planned")
        col = status_colors.get(t_status.lower(), "white")
        table.add_row(
            t_id,
            t_title,
            t_agent,
            t_rt,
            t_deps,
            t_writes,
            f"[{col}]{t_status}[/]",
        )

    console.print(Panel(table, border_style="magenta"))


@mission_app.command("dashboard")
def mission_dashboard(
    watch: Annotated[
        bool,
        typer.Option(
            "--watch",
            "-w",
            help="Periodically refresh the dashboard (live mode).",
        ),
    ] = False,
    mission_id: Annotated[
        Optional[str],
        typer.Option("--mission", help="Mission ID to display."),
    ] = None,
) -> None:
    """Show real-time dashboard of the active or latest mission."""
    from niyam.mission.dashboard import run_mission_dashboard

    try:
        run_mission_dashboard(watch=watch, console=console, mission_id=mission_id)
    except Exception as e:
        console.print(f"[bold red]Error:[/] {e}")
        raise typer.Exit(1)


@mission_app.command("validate-plan")
def mission_validate_plan(
    mission_id: Annotated[
        Optional[str],
        typer.Option("--mission", help="Mission ID to validate."),
    ] = None,
) -> None:
    """Validate the latest planned mission plan."""
    from niyam.core.config import find_niyam_root, get_niyam_dir
    from niyam.core.errors import NiyamConfigError
    from niyam.mission.planner import resolve_mission_id
    from niyam.mission.validator import validate_mission_plan, PlanValidationError

    repo_root = find_niyam_root()
    if not repo_root:
        raise NiyamConfigError("Not a Niyam workspace. Run 'niyam init' first.")
    niyam_dir = get_niyam_dir(repo_root)
    mission_id = resolve_mission_id(niyam_dir, mission_id)
    if not mission_id:
        console.print("[bold red]Error:[/] No missions found.")
        raise typer.Exit(1)

    run_dir = niyam_dir / "runs" / mission_id
    plan_path = run_dir / "mission-plan.yaml"

    try:
        validate_mission_plan(plan_path, repo_root)
        console.print(
            f"[bold green]✓[/] Mission plan '{mission_id}' is valid and ready for approval."
        )
    except PlanValidationError as e:
        console.print(
            f"[bold red]❌ Mission plan validation failed with {len(e.errors)} error(s):[/]"
        )
        for err in e.errors:
            console.print(f"  • [red]{err}[/]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[bold red]Error during validation:[/] {e}")
        raise typer.Exit(1)


@mission_app.command("approve")
def mission_approve(
    interactive: Annotated[
        bool,
        typer.Option(
            "--interactive",
            "-i",
            help="Approve tasks interactively with option to edit the plan.",
        ),
    ] = False,
    mission_id: Annotated[
        Optional[str],
        typer.Option("--mission", help="Mission ID to approve."),
    ] = None,
) -> None:
    """Approve the latest planned mission."""
    from niyam.mission.planner import run_mission_approve

    try:
        run_mission_approve(
            console=console, interactive=interactive, mission_id=mission_id
        )
    except Exception as e:
        console.print(f"[bold red]Error:[/] {e}")
        raise typer.Exit(1)


@mission_app.command("start")
def mission_start(
    parallel: Annotated[
        Optional[int],
        typer.Option(
            "--parallel", "-p", help="Override the number of parallel workers."
        ),
    ] = None,
    worktree: Annotated[
        Optional[bool],
        typer.Option(
            "--worktree/--no-worktree",
            help="Enable or disable git worktree isolation.",
        ),
    ] = None,
    non_interactive: Annotated[
        bool,
        typer.Option(
            "--non-interactive",
            "--ci",
            help="Run in non-interactive (CI/CD) mode.",
        ),
    ] = False,
    mission_id: Annotated[
        Optional[str],
        typer.Option("--mission", help="Mission ID to start."),
    ] = None,
    auto_heal: Annotated[
        Optional[bool],
        typer.Option(
            "--auto-heal/--no-auto-heal",
            help="Enable or disable autonomous resilience mid-mission.",
        ),
    ] = None,
    auto_heal_execute: Annotated[
        bool,
        typer.Option(
            "--auto-heal-execute",
            help="Autonomously execute recovery tasks without human approval.",
        ),
    ] = False,
    ) -> None:
    """Start or resume the latest approved mission."""
    from niyam.mission.executor import run_mission_start

    try:
        run_mission_start(
            console=console,
            parallel=parallel,
            worktree=worktree,
            auto_heal=auto_heal,
            auto_heal_execute=auto_heal_execute,
            non_interactive=non_interactive,
            mission_id=mission_id,
        )

    except Exception as e:
        console.print(f"[bold red]Error:[/] {e}")
        raise typer.Exit(1)


@mission_app.command("status")
def mission_status(
    mission_id: Annotated[
        Optional[str],
        typer.Option("--mission", help="Mission ID to inspect."),
    ] = None,
) -> None:
    """Show progress of the latest mission."""
    from niyam.mission.status import run_mission_status

    try:
        run_mission_status(console=console, mission_id=mission_id)
    except Exception as e:
        console.print(f"[bold red]Error:[/] {e}")
        raise typer.Exit(1)


@mission_app.command("pause")
def mission_pause(
    mission_id: Annotated[
        Optional[str],
        typer.Option("--mission", help="Mission ID to pause."),
    ] = None,
) -> None:
    """Pause the currently running mission."""
    from niyam.mission.executor import run_mission_pause

    try:
        run_mission_pause(console=console, mission_id=mission_id)
    except Exception as e:
        console.print(f"[bold red]Error:[/] {e}")
        raise typer.Exit(1)


@mission_app.command("resume")
def mission_resume(
    parallel: Annotated[
        Optional[int],
        typer.Option(
            "--parallel", "-p", help="Override the number of parallel workers."
        ),
    ] = None,
    worktree: Annotated[
        Optional[bool],
        typer.Option(
            "--worktree/--no-worktree",
            help="Enable or disable git worktree isolation.",
        ),
    ] = None,
    non_interactive: Annotated[
        bool,
        typer.Option(
            "--non-interactive",
            "--ci",
            help="Run in non-interactive (CI/CD) mode.",
        ),
    ] = False,
    mission_id: Annotated[
        Optional[str],
        typer.Option("--mission", help="Mission ID to resume."),
    ] = None,
    auto_heal_execute: Annotated[
        bool,
        typer.Option(
            "--auto-heal-execute",
            help="Autonomously execute recovery tasks without human approval.",
        ),
    ] = False,
) -> None:
    """Resume a paused mission."""
    from niyam.mission.executor import run_mission_resume

    try:
        run_mission_resume(
            parallel=parallel,
            worktree=worktree,
            non_interactive=non_interactive,
            console=console,
            mission_id=mission_id,
            auto_heal_execute=auto_heal_execute,
        )
    except Exception as e:
        console.print(f"[bold red]Error:[/] {e}")
        raise typer.Exit(1)


@mission_app.command("retry")
def mission_retry(
    parallel: Annotated[
        Optional[int],
        typer.Option(
            "--parallel", "-p", help="Override the number of parallel workers."
        ),
    ] = None,
    worktree: Annotated[
        Optional[bool],
        typer.Option(
            "--worktree/--no-worktree",
            help="Enable or disable git worktree isolation.",
        ),
    ] = None,
    non_interactive: Annotated[
        bool,
        typer.Option(
            "--non-interactive",
            "--ci",
            help="Run in non-interactive (CI/CD) mode.",
        ),
    ] = False,
    mission_id: Annotated[
        Optional[str],
        typer.Option("--mission", help="Mission ID to retry."),
    ] = None,
    auto_heal_execute: Annotated[
        bool,
        typer.Option(
            "--auto-heal-execute",
            help="Autonomously execute recovery tasks without human approval.",
        ),
    ] = False,
) -> None:
    """Retry failed or skipped tasks of the latest mission."""
    from niyam.mission.executor import run_mission_retry

    try:
        run_mission_retry(
            parallel=parallel,
            worktree=worktree,
            non_interactive=non_interactive,
            mission_id=mission_id,
            console=console,
            auto_heal_execute=auto_heal_execute,
        )
    except Exception as e:
        console.print(f"[bold red]Error:[/] {e}")
        raise typer.Exit(1)


@mission_app.command("replan")
def mission_replan(
    mission_id: Annotated[
        Optional[str],
        typer.Option("--mission", help="Mission ID to re-plan."),
    ] = None,
    reason: Annotated[
        Optional[str],
        typer.Option("--reason", help="Context or reason for re-planning."),
    ] = None,
    runtime: Annotated[
        Optional[Runtime],
        typer.Option("--runtime", "-r", help="Runtime override for re-planning."),
    ] = None,
) -> None:
    """Invoke AI to revise the remaining tasks in a mission plan after roadblocks."""
    from niyam.mission.planner import run_mission_replan

    try:
        run_mission_replan(
            mission_id=mission_id,
            reason=reason,
            runtime_override=runtime.value if runtime else None,
            console=console,
        )
    except Exception as e:
        console.print(f"[bold red]Error:[/] {e}")
        raise typer.Exit(1)


@mission_app.command("skip")
def mission_skip(
    task_id: Annotated[str, typer.Argument(help="ID of the task to skip.")],
    parallel: Annotated[
        Optional[int],
        typer.Option(
            "--parallel", "-p", help="Override the number of parallel workers."
        ),
    ] = None,
    worktree: Annotated[
        Optional[bool],
        typer.Option(
            "--worktree/--no-worktree",
            help="Enable or disable git worktree isolation.",
        ),
    ] = None,
    non_interactive: Annotated[
        bool,
        typer.Option(
            "--non-interactive",
            "--ci",
            help="Run in non-interactive (CI/CD) mode.",
        ),
    ] = False,
    mission_id: Annotated[
        Optional[str],
        typer.Option("--mission", help="Mission ID containing the task."),
    ] = None,
) -> None:
    """Skip a specific task and resume the mission execution."""
    from niyam.mission.executor import run_mission_skip

    try:
        run_mission_skip(
            task_id=task_id,
            console=console,
            parallel=parallel,
            worktree=worktree,
            non_interactive=non_interactive,
            mission_id=mission_id,
        )
    except Exception as e:
        console.print(f"[bold red]Error:[/] {e}")
        raise typer.Exit(1)


@mission_app.command("rollback")
def mission_rollback(
    mission_id: Annotated[
        Optional[str],
        typer.Option("--mission", help="Mission ID to roll back."),
    ] = None,
) -> None:
    """Rollback all workspace changes back to the start of the latest mission."""
    from niyam.mission.executor import run_mission_rollback

    try:
        run_mission_rollback(console=console, mission_id=mission_id)
    except Exception as e:
        console.print(f"[bold red]Error:[/] {e}")
        raise typer.Exit(1)


@mission_app.command("report")
def mission_report(
    mission_id: Annotated[
        Optional[str],
        typer.Option("--mission", help="Mission ID to report."),
    ] = None,
    upload: Annotated[
        bool,
        typer.Option("--upload", "-u", help="Upload report to Niyam Dashboard."),
    ] = False,
) -> None:
    """Generate final evidence package for the latest mission."""
    from niyam.mission.reporter import run_mission_report

    try:
        run_mission_report(console=console, mission_id=mission_id, upload=upload)
    except Exception as e:
        console.print(f"[bold red]Error:[/] {e}")
        raise typer.Exit(1)


@mission_app.command("verify-report")
def mission_verify_report(
    evidence_file: Annotated[
        str,
        typer.Argument(help="Path to the evidence.md report to verify."),
    ],
) -> None:
    """Verify the cryptographic integrity of an evidence report."""
    from niyam.mission.reporter import run_verify_report

    try:
        run_verify_report(evidence_path=evidence_file, console=console)
    except Exception as e:
        console.print(f"[bold red]Error:[/] {e}")
        raise typer.Exit(1)


@mission_app.command("active")
def mission_active(
    path: Annotated[
        bool,
        typer.Option(
            "--path",
            "-p",
            help="Print only the absolute path to the active mission directory.",
        ),
    ] = False,
) -> None:
    """Print the path or details of the active/latest mission run."""
    from niyam.core.config import find_niyam_root, get_niyam_dir
    from niyam.core.errors import NiyamConfigError
    from niyam.mission.planner import resolve_mission_id

    repo_root = find_niyam_root()
    if not repo_root:
        raise NiyamConfigError("Not a Niyam workspace. Run 'niyam init' first.")
    niyam_dir = get_niyam_dir(repo_root)

    current_symlink = niyam_dir / "runs" / "current"
    mission_id = None
    if current_symlink.is_symlink():
        try:
            target_path = current_symlink.readlink()
            if not target_path.is_absolute():
                resolved_dir = (niyam_dir / "runs" / target_path).resolve()
            else:
                resolved_dir = target_path.resolve()

            if resolved_dir.is_dir():
                mission_id = resolved_dir.name
        except Exception:
            pass

    if not mission_id:
        mission_id = resolve_mission_id(niyam_dir)

    if not mission_id:
        console.print("[bold red]Error:[/] No active mission found.")
        raise typer.Exit(1)

    active_dir = (niyam_dir / "runs" / mission_id).resolve()
    if path:
        console.print(str(active_dir))
    else:
        # Load the status
        plan_path = active_dir / "mission-plan.yaml"
        status = "unknown"
        if plan_path.exists():
            try:
                with open(plan_path, encoding="utf-8") as f:
                    plan_data = yaml.safe_load(f) or {}
                status = plan_data.get("mission", {}).get("status", "unknown")
            except Exception:
                pass
        console.print(f"Active Mission: [cyan]{mission_id}[/]")
        console.print(f"Status: [yellow]{status}[/]")
        console.print(f"Path: {active_dir}")


@mission_app.command("next")
def mission_next(
    mission_id: Annotated[
        Optional[str],
        typer.Option("--mission", help="Mission ID to inspect."),
    ] = None,
) -> None:
    """Suggest the next logical action for the current mission."""
    from niyam.core.config import find_niyam_root, get_niyam_dir
    from niyam.mission.planner import resolve_mission_id
    from niyam.mission.executor import load_plan

    repo_root = find_niyam_root()
    if not repo_root:
        console.print("[bold red]Error:[/] Not in a Niyam workspace.")
        raise typer.Exit(1)
    niyam_dir = get_niyam_dir(repo_root)
    mission_id = resolve_mission_id(niyam_dir, mission_id)
    if not mission_id:
        console.print("[yellow]No missions found.[/]")
        return

    run_dir = niyam_dir / "runs" / mission_id
    plan_data = load_plan(run_dir)
    mission_meta = plan_data.get("mission", {})
    tasks = plan_data.get("tasks", [])
    status = mission_meta.get("status", "planned")

    console.print(f"Mission: [bold cyan]{mission_id}[/]")
    console.print(f"Status: [bold]{status.upper()}[/]\n")

    if status == "planned":
        console.print("Next Recommended Action:")
        console.print(f"  [bold]niyam mission approve --mission {mission_id}[/]")
        console.print("  [dim]The mission plan needs your approval before it can start.[/]")
        return

    if status == "paused":
        console.print("Next Recommended Action:")
        console.print(f"  [bold]niyam mission resume --mission {mission_id}[/]")
        console.print("  [dim]The mission is currently paused and ready to continue.[/]")
        return

    if status == "completed":
        console.print("Mission completed successfully.")
        console.print("Next Recommended Action:")
        console.print(f"  [bold]niyam mission report --mission {mission_id}[/]")
        return

    # Check for blocking tasks
    awaiting = [t for t in tasks if t["status"] == "awaiting_approval"]
    if awaiting:
        console.print("Action Required: [bold yellow]Human Approval Needed[/]")
        for t in awaiting:
            console.print(f"  - Task [cyan]{t['id']}[/]: {t['title']}")
            console.print(f"    [bold]niyam mission approve-task {t['id']} --mission {mission_id}[/]")
        return

    blocked = [t for t in tasks if t["status"] == "blocked"]
    if blocked:
        console.print("Action Required: [bold red]Blocked Tasks[/]")
        for t in blocked:
            console.print(f"  - Task [cyan]{t['id']}[/]: {t['title']}")
            console.print(f"    Check evidence at: [dim]{run_dir}/tasks/{t['id']}/[/]")
        return

    failed = [t for t in tasks if t["status"] == "failed"]
    if failed:
        console.print("Action Required: [bold red]Task Failures[/]")
        for t in failed:
            console.print(f"  - Task [cyan]{t['id']}[/]: {t['title']}")
            console.print(f"    [bold]niyam mission retry --mission {mission_id}[/]")
        return

    if status == "running":
        running = [t for t in tasks if t["status"] == "running"]
        if running:
            console.print("Mission is actively running.")
            for t in running:
                console.print(f"  - Task [cyan]{t['id']}[/] is running by [bold]{t['agent']}[/].")
            console.print(f"\nView live dashboard: [bold]niyam mission dashboard --mission {mission_id}[/]")
        else:
            console.print("Mission is running but no tasks are currently executing.")
            console.print("It might be waiting for dependencies or concurrency slots.")
        return

    console.print("No specific recommendation. Check status with [bold]niyam mission status[/].")


@mission_app.command("inspect")
def mission_inspect(
    task_id: Annotated[str, typer.Argument(help="ID of the task to inspect.")],
    mission_id: Annotated[
        Optional[str],
        typer.Option("--mission", help="Mission ID containing the task."),
    ] = None,
) -> None:
    """Show detailed artifacts and history for a specific task."""
    import json
    from niyam.core.config import find_niyam_root, get_niyam_dir
    from niyam.mission.planner import resolve_mission_id

    repo_root = find_niyam_root()
    if not repo_root:
        console.print("[bold red]Error:[/] Not in a Niyam workspace.")
        raise typer.Exit(1)
    niyam_dir = get_niyam_dir(repo_root)
    mission_id = resolve_mission_id(niyam_dir, mission_id)
    if not mission_id:
        console.print("[bold red]Error:[/] No missions found.")
        raise typer.Exit(1)

    task_dir = niyam_dir / "runs" / mission_id / "tasks" / task_id
    if not task_dir.is_dir():
        console.print(f"[bold red]Error:[/] Artifact directory for task '{task_id}' not found.")
        console.print(f"Path: {task_dir}")
        raise typer.Exit(1)

    console.print(Panel(f"Task Inspection: [bold cyan]{task_id}[/] in Mission [bold]{mission_id}[/]", border_style="cyan"))

    # Status
    status_file = task_dir / "status.json"
    if status_file.exists():
        status_data = json.loads(status_file.read_text(encoding="utf-8"))
        console.print(f"Current Status: [bold magenta]{status_data.get('status', 'unknown').upper()}[/]")
        console.print(f"Last Actor: [bold]{status_data.get('actor', '-')}[/]")
        console.print(f"Last Updated: [dim]{status_data.get('updated_at', '-')}[/]")
        if status_data.get("reason"):
            console.print(f"Reason: {status_data.get('reason')}")
    
    # Prompt
    if (task_dir / "prompt.md").exists():
        console.print("\n[bold]Task Prompt (excerpt):[/]")
        prompt_content = (task_dir / "prompt.md").read_text(encoding="utf-8")
        console.print(f"[dim]{prompt_content[:500]}...[/]")

    # Diffs
    if (task_dir / "diff.patch").exists():
        diff_content = (task_dir / "diff.patch").read_text(encoding="utf-8")
        if diff_content.strip():
            console.print(f"\n[bold green]Changes Detected ({len(diff_content.splitlines())} lines of diff)[/]")
        else:
            console.print("\n[yellow]No changes detected in files.[/]")

    # Validation
    val_file = task_dir / "validation.json"
    if val_file.exists():
        val_data = json.loads(val_file.read_text(encoding="utf-8"))
        table = Table(title="Validation Results", box=None)
        table.add_column("Check")
        table.add_column("Result")
        for v in val_data:
            res = "[green]PASS[/]" if v.get("success") else "[red]FAIL[/]"
            table.add_row(v.get("name", "unknown"), res)
        console.print("\n")
        console.print(table)

    console.print(f"\nFull artifacts available at: [bold]{task_dir}[/]")


@mission_app.command("timeline")
def mission_timeline(
    mission_id: Annotated[
        Optional[str],
        typer.Option("--mission", help="Mission ID to display."),
    ] = None,
) -> None:
    """Display a chronological timeline of mission events."""
    import json
    from niyam.core.config import find_niyam_root, get_niyam_dir
    from niyam.mission.planner import resolve_mission_id

    repo_root = find_niyam_root()
    if not repo_root:
        console.print("[bold red]Error:[/] Not in a Niyam workspace.")
        raise typer.Exit(1)
    niyam_dir = get_niyam_dir(repo_root)
    mission_id = resolve_mission_id(niyam_dir, mission_id)
    if not mission_id:
        console.print("[bold red]Error:[/] No missions found.")
        raise typer.Exit(1)

    events_path = niyam_dir / "runs" / mission_id / "events.jsonl"
    if not events_path.exists():
        console.print("[yellow]No event history found for this mission.[/]")
        return

    table = Table(title=f"Timeline: [bold cyan]{mission_id}[/]", box=None, expand=True)
    table.add_column("Timestamp", style="dim", width=20)
    table.add_column("Actor", style="bold yellow", width=15)
    table.add_column("Event", width=25)
    table.add_column("Details")

    with open(events_path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                ev = json.loads(line)
                ts = ev.get("timestamp", "").split(".")[0].replace("T", " ")
                actor = ev.get("actor") or ev.get("task_id") or "system"
                event_type = ev.get("event", "UNKNOWN")
                
                details = ev.get("details", "")
                if event_type == "TASK_STATE_TRANSITION":
                    details = f"Task [cyan]{ev.get('task_id')}[/] status: [dim]{ev.get('from_status')}[/] -> [bold magenta]{ev.get('to_status')}[/]"
                    if ev.get("reason"):
                        details += f" ({ev.get('reason')})"
                elif event_type == "MISSION_STATE_TRANSITION":
                    details = f"Mission status: [dim]{ev.get('from_status')}[/] -> [bold green]{ev.get('to_status')}[/]"
                    if ev.get("reason"):
                        details += f" ({ev.get('reason')})"

                table.add_row(ts, str(actor), event_type, details)
            except Exception:
                continue

    console.print(table)


@mission_app.command("metrics")
def mission_metrics(
    mission_id: Annotated[
        Optional[str],
        typer.Option("--mission", help="Mission ID to show metrics for."),
    ] = None,
) -> None:
    """Show performance and efficiency metrics for missions and agents."""
    from niyam.core.analytics import PerformanceMetrics
    from niyam.core.config import find_niyam_root
    from rich.table import Table
    from rich.panel import Panel

    root = find_niyam_root()
    if not root:
        console.print("[bold red]Error:[/] Not a Niyam workspace.")
        raise SystemExit(1)

    analytics = PerformanceMetrics(root)

    if mission_id:
        m = analytics.get_mission_metrics(mission_id)
        if not m:
            console.print(f"[bold red]Error:[/] Mission '{mission_id}' not found.")
            return

        table = Table(title=f"Mission Metrics: {mission_id}")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="bold")
        
        table.add_row("Total Tokens", str(m["total_tokens"]))
        table.add_row("Total Cost", f"${m['total_cost_usd']:.4f}")
        table.add_row("Efficiency Savings", f"{m['savings_percent']:.1f}%")
        table.add_row("Task Count", str(m["task_count"]))
        table.add_row("Success Rate", f"{m['success_rate']:.1f}%")
        
        console.print(table)
        
        # Agent breakdown
        if m["by_agent"]:
            at = Table(title="Agent Performance")
            at.add_column("Agent", style="yellow")
            at.add_column("Tasks", justify="right")
            at.add_column("Success Rate", justify="right", style="green")
            
            for agent, stats in m["by_agent"].items():
                sr = (stats["completed"] / stats["count"]) * 100 if stats["count"] > 0 else 0
                at.add_row(agent, str(stats["count"]), f"{sr:.1f}%")
            console.print(at)
    else:
        summary = analytics.get_fleet_summary()
        if summary["total_missions"] == 0:
            console.print("[yellow]No mission history found to analyze.[/]")
            return

        console.print(Panel(
            f"[bold cyan]Total Missions:[/] {summary['total_missions']}\n"
            f"[bold cyan]Total Fleet Cost:[/] ${summary['total_cost_usd']:.4f}\n"
            f"[bold cyan]Avg Success Rate:[/] [green]{summary['avg_success_rate']:.1f}%[/]\n"
            f"[bold cyan]Avg Token Efficiency:[/] [cyan]{summary['avg_savings_percent']:.1f}%[/]",
            title="[bold]Fleet Performance Summary[/]",
            border_style="cyan"
        ))

        if summary["agent_performance"]:
            at = Table(title="Global Agent Performance Ranking")
            at.add_column("Agent", style="yellow")
            at.add_column("Total Tasks", justify="right")
            at.add_column("Overall Success Rate", justify="right", style="bold green")
            
            # Sort by success rate
            sorted_agents = sorted(
                summary["agent_performance"].items(),
                key=lambda x: x[1]["success_rate"],
                reverse=True
            )
            
            for agent, stats in sorted_agents:
                at.add_row(agent, str(stats["tasks"]), f"{stats['success_rate']:.1f}%")
            console.print(at)


@mission_app.command("approve-task")
def mission_approve_task(
    task_id: Annotated[str, typer.Argument(help="ID of the task to approve.")],
    mission_id: Annotated[
        Optional[str],
        typer.Option("--mission", help="Mission ID containing the task."),
    ] = None,
) -> None:
    """Manually approve a task that is awaiting approval."""
    import json
    from niyam.core.config import find_niyam_root, get_niyam_dir
    from niyam.mission.planner import resolve_mission_id

    repo_root = find_niyam_root()
    niyam_dir = get_niyam_dir(repo_root)
    mission_id = resolve_mission_id(niyam_dir, mission_id)
    if not mission_id:
        console.print("[bold red]Error:[/] No missions found.")
        raise typer.Exit(1)

    task_dir = niyam_dir / "runs" / mission_id / "tasks" / task_id
    task_dir.mkdir(parents=True, exist_ok=True)
    
    approval_data = {
        "approved": True,
        "approver": "human-cli",
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    (task_dir / "approval.json").write_text(json.dumps(approval_data, indent=2), encoding="utf-8")
    console.print(f"[bold green]✓[/] Task [cyan]{task_id}[/] approved. If the mission is running, it will proceed shortly.")


@mission_app.command("reject-task")
def mission_reject_task(
    task_id: Annotated[str, typer.Argument(help="ID of the task to reject.")],
    reason: Annotated[str, typer.Option("--reason", help="Reason for rejection.")] = "Rejected via CLI.",
    mission_id: Annotated[
        Optional[str],
        typer.Option("--mission", help="Mission ID containing the task."),
    ] = None,
) -> None:
    """Manually reject a task that is awaiting approval."""
    import json
    from niyam.core.config import find_niyam_root, get_niyam_dir
    from niyam.mission.planner import resolve_mission_id

    repo_root = find_niyam_root()
    niyam_dir = get_niyam_dir(repo_root)
    mission_id = resolve_mission_id(niyam_dir, mission_id)
    if not mission_id:
        console.print("[bold red]Error:[/] No missions found.")
        raise typer.Exit(1)

    task_dir = niyam_dir / "runs" / mission_id / "tasks" / task_id
    task_dir.mkdir(parents=True, exist_ok=True)
    
    approval_data = {
        "approved": False,
        "reason": reason,
        "approver": "human-cli",
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    (task_dir / "approval.json").write_text(json.dumps(approval_data, indent=2), encoding="utf-8")
    console.print(f"[bold red]❌[/] Task [cyan]{task_id}[/] rejected.")
