"""Sutra CLI top-level commands."""

from __future__ import annotations

from enum import Enum
from typing import Annotated, Optional

import typer

from sutra import __version__
from sutra.cli import app, console


class Runtime(str, Enum):
    claude = "claude"
    codex = "codex"
    gemini = "gemini"


class ReportFormat(str, Enum):
    md = "md"
    json = "json"


@app.command()
def version() -> None:
    """Show the Sutra version."""
    console.print(f"[bold cyan]sutra[/] {__version__}")


@app.command()
def init(
    profile: Annotated[
        str,
        typer.Option(
            "--profile",
            "-p",
            help="Project profile to use (e.g., fullstack, backend, frontend, startup-saas, platform-engineering, governed-enterprise).",
        ),
    ] = "fullstack",
    runtime: Annotated[
        Optional[Runtime],
        typer.Option("--runtime", "-r", help="Initial runtime to configure."),
    ] = None,
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            help="Preview changes without writing files.",
        ),
    ] = False,
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            help="Overwrite existing .sutra/ directory.",
        ),
    ] = False,
) -> None:
    """Initialize a governed AI-development workspace."""
    from sutra.core.init import run_init

    run_init(
        profile=profile,
        runtime=runtime.value if runtime else None,
        dry_run=dry_run,
        force=force,
        console=console,
    )


@app.command()
def run(
    requirement: Annotated[
        str,
        typer.Argument(
            help="Requirement text or path to requirements markdown file.",
        ),
    ],
    runtime: Annotated[
        Optional[Runtime],
        typer.Option("--runtime", "-r", help="Runtime override for this mission."),
    ] = None,
    parallel: Annotated[
        Optional[int],
        typer.Option("--parallel", "-p", help="Number of parallel workers."),
    ] = None,
    auto_approve: Annotated[
        bool,
        typer.Option(
            "--auto-approve",
            help="Skip approval gate and execute immediately.",
        ),
    ] = False,
    strict: Annotated[
        bool,
        typer.Option(
            "--strict",
            help="Fail if AI-powered planning fails, instead of falling back.",
        ),
    ] = False,
    worktree: Annotated[
        Optional[bool],
        typer.Option(
            "--worktree/--no-worktree",
            help="Enable or disable git worktree isolation.",
        ),
    ] = None,
    template: Annotated[
        Optional[str],
        typer.Option(
            "--template",
            "-t",
            help="Use a mission template for planning.",
        ),
    ] = None,
) -> None:
    """Plan, approve, and execute a mission in one step."""
    from sutra.core.context import run_context_refresh
    from sutra.core.sync import run_sync
    from sutra.mission.planner import run_mission_plan, run_mission_approve
    from sutra.mission.executor import run_mission_start

    # 1. Refresh context
    console.print("[cyan]1. Refreshing project context...[/]")
    run_context_refresh(console=console)

    # 2. Sync configured runtimes
    console.print("\n[cyan]2. Syncing runtimes...[/]")
    run_sync(runtime=None, console=console)

    # 3. Plan the mission
    console.print("\n[cyan]3. Generating mission plan...[/]")
    mission_id = run_mission_plan(
        requirements_path=requirement,
        strict=strict,
        console=console,
        template=template,
        runtime_override=runtime.value if runtime else None,
    )

    # 4. Approve plan
    console.print("\n[cyan]4. Checking plan approval...[/]")
    run_mission_approve(console=console, interactive=not auto_approve)

    # 5. Start execution
    console.print(f"\n[cyan]5. Starting execution for mission '{mission_id}'...[/]")
    run_mission_start(
        parallel=parallel,
        worktree=worktree,
        non_interactive=auto_approve,
        console=console,
    )


@app.command()
def sync(
    runtime: Annotated[
        Optional[Runtime],
        typer.Option(
            "--runtime",
            "-r",
            help="Sync a specific runtime only.",
        ),
    ] = None,
) -> None:
    """Sync .sutra/ source of truth to all configured runtimes."""
    from sutra.core.sync import run_sync

    run_sync(runtime=runtime.value if runtime else None, console=console)


@app.command()
def setup() -> None:
    """Run the interactive onboarding wizard to configure your workspace."""
    from sutra.core.setup import run_setup

    run_setup(console=console)


@app.command()
def doctor(
    runtime: Annotated[
        Optional[Runtime],
        typer.Argument(help="Check a specific runtime adapter."),
    ] = None,
) -> None:
    """Validate .sutra/ configuration and runtime projections."""
    from sutra.core.doctor import run_doctor

    run_doctor(runtime=runtime.value if runtime else None, console=console)


@app.command()
def report(
    format: Annotated[
        ReportFormat,
        typer.Option("--format", "-f", help="Output format."),
    ] = ReportFormat.md,
) -> None:
    """Generate evidence report for the current branch."""
    from sutra.evidence.reporter import run_report

    run_report(format=format.value, console=console)


@app.command()
def dashboard(
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


@app.command()
def watch() -> None:
    """Watch the active or latest mission in real-time (live mode)."""
    from sutra.mission.dashboard import run_mission_dashboard

    try:
        run_mission_dashboard(watch=True, console=console)
    except Exception as e:
        console.print(f"[bold red]Error:[/] {e}")
        raise typer.Exit(1)


@app.command()
def plan(
    requirements: Annotated[
        str,
        typer.Argument(help="Path to requirements markdown file."),
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
    """Plan a mission from a requirements file (alias for 'mission plan')."""
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


@app.command()
def compare(
    task_id: Annotated[
        str,
        typer.Argument(help="Task ID to run comparison for (e.g., T1, TASK-001)."),
    ],
    executors: Annotated[
        str,
        typer.Option(
            "--executors",
            "-e",
            help="Comma-separated list of executors to compare (e.g., claude,gemini,codex).",
        ),
    ] = "claude,gemini,codex",
) -> None:
    """Compare performance, cost, and validation status of multiple runtimes on a task."""
    from sutra.core.compare import run_comparison

    try:
        run_comparison(task_id=task_id, executors_str=executors, console=console)
    except Exception as e:
        console.print(f"[bold red]Error:[/] {e}")
        raise typer.Exit(1)
