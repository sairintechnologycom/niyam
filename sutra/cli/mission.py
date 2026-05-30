"""Sutra CLI mission commands."""

from __future__ import annotations

from typing import Annotated, Optional

import typer
import yaml
from rich.panel import Panel
from rich.table import Table

from sutra.cli import console, mission_app
from sutra.cli.main_cmds import Runtime


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
    from sutra.mission.planner import run_mission_plan

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
def mission_show() -> None:
    """Display tasks and configuration of the latest planned or active mission."""
    from sutra.core.config import find_sutra_root, get_sutra_dir
    from sutra.core.errors import SutraConfigError
    from sutra.mission.planner import get_latest_mission_id

    repo_root = find_sutra_root()
    if not repo_root:
        raise SutraConfigError("Not a Sutra workspace. Run 'sutra init' first.")
    sutra_dir = get_sutra_dir(repo_root)

    mission_id = get_latest_mission_id(sutra_dir)
    if not mission_id:
        console.print("[bold red]Error:[/] No missions found.")
        raise typer.Exit(1)

    run_dir = sutra_dir / "runs" / mission_id
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
        "pending": "white",
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
        t_status = t.get("status", "pending")
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
) -> None:
    """Show real-time dashboard of the active or latest mission."""
    from sutra.mission.dashboard import run_mission_dashboard

    try:
        run_mission_dashboard(watch=watch, console=console)
    except Exception as e:
        console.print(f"[bold red]Error:[/] {e}")
        raise typer.Exit(1)


@mission_app.command("validate-plan")
def mission_validate_plan() -> None:
    """Validate the latest planned mission plan."""
    from sutra.core.config import find_sutra_root, get_sutra_dir
    from sutra.core.errors import SutraConfigError
    from sutra.mission.planner import get_latest_mission_id
    from sutra.mission.validator import validate_mission_plan, PlanValidationError

    repo_root = find_sutra_root()
    if not repo_root:
        raise SutraConfigError("Not a Sutra workspace. Run 'sutra init' first.")
    sutra_dir = get_sutra_dir(repo_root)
    mission_id = get_latest_mission_id(sutra_dir)
    if not mission_id:
        console.print("[bold red]Error:[/] No missions found.")
        raise typer.Exit(1)

    run_dir = sutra_dir / "runs" / mission_id
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
) -> None:
    """Approve the latest planned mission."""
    from sutra.mission.planner import run_mission_approve

    try:
        run_mission_approve(console=console, interactive=interactive)
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
) -> None:
    """Start or resume the latest approved mission."""
    from sutra.mission.executor import run_mission_start

    try:
        run_mission_start(
            parallel=parallel,
            worktree=worktree,
            non_interactive=non_interactive,
            console=console,
        )
    except Exception as e:
        console.print(f"[bold red]Error:[/] {e}")
        raise typer.Exit(1)


@mission_app.command("status")
def mission_status() -> None:
    """Show progress of the latest mission."""
    from sutra.mission.status import run_mission_status

    try:
        run_mission_status(console=console)
    except Exception as e:
        console.print(f"[bold red]Error:[/] {e}")
        raise typer.Exit(1)


@mission_app.command("pause")
def mission_pause() -> None:
    """Pause the currently running mission."""
    from sutra.mission.executor import run_mission_pause

    try:
        run_mission_pause(console=console)
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
) -> None:
    """Resume a paused mission."""
    from sutra.mission.executor import run_mission_resume

    try:
        run_mission_resume(
            parallel=parallel,
            worktree=worktree,
            non_interactive=non_interactive,
            console=console,
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
) -> None:
    """Retry failed or skipped tasks of the latest mission."""
    from sutra.mission.executor import run_mission_retry

    try:
        run_mission_retry(
            console=console,
            parallel=parallel,
            worktree=worktree,
            non_interactive=non_interactive,
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
) -> None:
    """Skip a specific task and resume the mission execution."""
    from sutra.mission.executor import run_mission_skip

    try:
        run_mission_skip(
            task_id=task_id,
            console=console,
            parallel=parallel,
            worktree=worktree,
            non_interactive=non_interactive,
        )
    except Exception as e:
        console.print(f"[bold red]Error:[/] {e}")
        raise typer.Exit(1)


@mission_app.command("rollback")
def mission_rollback() -> None:
    """Rollback all workspace changes back to the start of the latest mission."""
    from sutra.mission.executor import run_mission_rollback

    try:
        run_mission_rollback(console=console)
    except Exception as e:
        console.print(f"[bold red]Error:[/] {e}")
        raise typer.Exit(1)


@mission_app.command("report")
def mission_report() -> None:
    """Generate final evidence package for the latest mission."""
    from sutra.mission.reporter import run_mission_report

    try:
        run_mission_report(console=console)
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
    from sutra.mission.reporter import run_verify_report

    try:
        run_verify_report(evidence_path=evidence_file, console=console)
    except Exception as e:
        console.print(f"[bold red]Error:[/] {e}")
        raise typer.Exit(1)
