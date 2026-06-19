"""Niyam CLI mission commands."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import shutil
import subprocess
from typing import Annotated, Optional

import typer
import yaml
from rich.panel import Panel
from rich.table import Table

from niyam.cli import console, mission_app
from niyam.cli.main_cmds import Runtime, ReportFormat


@mission_app.command("ingest")
def mission_ingest(
    prd_path: Annotated[
        str,
        typer.Argument(help="Path to a Product Requirements Document markdown file."),
    ],
    ai: Annotated[
        bool,
        typer.Option("--ai/--no-ai", help="Use configured AI runtime when available."),
    ] = True,
) -> None:
    """Ingest a PRD into structured requirement markdown."""
    from niyam.core.config import find_niyam_root
    from niyam.core.errors import NiyamConfigError

    repo_root = find_niyam_root()
    if not repo_root:
        raise NiyamConfigError("Not a Niyam workspace. Run 'niyam init' first.")

    source_path = Path(prd_path)
    if not source_path.exists():
        console.print(f"[bold red]Error:[/] PRD file not found: {prd_path}")
        raise typer.Exit(1)

    prd_text = source_path.read_text(encoding="utf-8")
    requirements_dir = repo_root / "requirements"
    requirements_dir.mkdir(parents=True, exist_ok=True)

    output_path = requirements_dir / f"{source_path.stem}-structured.md"
    structured = None
    if ai:
        structured = _structure_prd_with_runtime(repo_root, source_path.name, prd_text)
    if not structured:
        structured = _structure_prd_markdown(source_path.name, prd_text)
    output_path.write_text(structured, encoding="utf-8")

    console.print(
        f"[bold green]✓[/] Ingested PRD into [cyan]{output_path.relative_to(repo_root)}[/]."
    )


def _structure_prd_with_runtime(repo_root: Path, source_name: str, prd_text: str) -> str | None:
    """Use the configured runtime to structure a PRD, returning None on failure."""
    try:
        from niyam.core.config import load_niyam_config

        config = load_niyam_config(repo_root)
        runtime = config.runtimes[0] if config.runtimes else None
        if not runtime or not shutil.which(runtime):
            return None
    except Exception:
        return None

    prompt = f"""Convert this Product Requirements Document into structured Markdown.

Return only Markdown using this shape:
# Structured Requirements: <title>
Source: `{source_name}`

## Epics
- EPIC-001: <name>

## Stories
### STORY-001
- Epic: EPIC-001
- Requirement: <specific requirement>
- Acceptance Criteria:
  - <testable criterion>
- Risks:
  - <risk or dependency>

PRD:
{prd_text}
"""
    cmd = [runtime, "-p", prompt]
    if runtime == "gemini":
        cmd.append("--skip-trust")
    try:
        res = subprocess.run(
            cmd,
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=180,
            check=False,
        )
    except Exception:
        return None
    if res.returncode != 0:
        return None
    output = (res.stdout or "").strip()
    if not output or "## Stories" not in output:
        return None
    return output


def _structure_prd_markdown(source_name: str, prd_text: str) -> str:
    """Create a deterministic epic/story scaffold from a markdown PRD."""
    title = source_name.rsplit(".", 1)[0].replace("-", " ").replace("_", " ").title()
    lines = [line.strip() for line in prd_text.splitlines() if line.strip()]
    headings = [line.lstrip("# ").strip() for line in lines if line.startswith("#")]
    bullets = [
        line.lstrip("-* ").strip()
        for line in lines
        if line.startswith(("- ", "* ")) and len(line.strip()) > 2
    ]

    epics = headings[1:] if len(headings) > 1 else headings[:1] or [title]
    stories = bullets[:10] or [
        "Convert the PRD into implementation-ready tasks.",
        "Validate the implementation against acceptance criteria.",
    ]

    output = [
        f"# Structured Requirements: {title}",
        "",
        f"Source: `{source_name}`",
        "",
        "## Epics",
        "",
    ]
    for index, epic in enumerate(epics, 1):
        output.append(f"- EPIC-{index:03d}: {epic}")

    output.extend(["", "## Stories", ""])
    for index, story in enumerate(stories, 1):
        epic_id = min(index, len(epics))
        output.extend(
            [
                f"### STORY-{index:03d}",
                f"- Epic: EPIC-{epic_id:03d}",
                f"- Requirement: {story}",
                "- Acceptance Criteria:",
                "  - The requirement is implemented and verified.",
                "  - Relevant validation commands pass.",
                "",
            ]
        )

    return "\n".join(output)


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


@mission_app.command("explain")
def mission_explain(
    mission_id: Annotated[
        Optional[str],
        typer.Option("--mission", help="Mission ID to explain."),
    ] = None,
) -> None:
    """Explain execution order, scopes, approvals, and validation for a mission."""
    from niyam.core.config import find_niyam_root, get_niyam_dir
    from niyam.core.errors import NiyamConfigError
    from niyam.mission.planner import DAGPlanner, resolve_mission_id

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
    plan_data = yaml.safe_load(plan_path.read_text(encoding="utf-8")) or {}
    tasks = plan_data.get("tasks", [])
    mission_meta = plan_data.get("mission", {})

    table = Table(title=f"Execution Preview: {mission_id}", expand=True)
    table.add_column("Layer", justify="right", style="cyan")
    table.add_column("Task")
    table.add_column("Agent", style="magenta")
    table.add_column("Writes")
    table.add_column("Approval")
    table.add_column("Validation")

    try:
        layers = DAGPlanner().executable_layers(tasks)
    except Exception as e:
        console.print(f"[bold red]Invalid task DAG:[/] {e}")
        raise typer.Exit(1)

    for layer_index, layer in enumerate(layers, 1):
        for task in layer:
            validation = task.get("validation") or {}
            commands = validation.get("commands", []) if isinstance(validation, dict) else []
            files = task.get("files_allowed") or task.get("allowed_files") or ["*"]
            table.add_row(
                str(layer_index),
                f"[bold]{task['id']}[/] {task['title']}",
                task.get("agent", "-"),
                ", ".join(files) if task.get("writes_files", True) else "no",
                "yes" if task.get("approval_required") else "no",
                ", ".join(commands) if commands else "-",
            )

    summary = (
        f"Parallel workers: [bold]{mission_meta.get('parallel', 1)}[/]\n"
        f"Worktree isolation: [bold]{mission_meta.get('worktree', True)}[/]\n"
        f"Auto-heal: [bold]{mission_meta.get('auto_heal', False)}[/]\n"
        "Swarm locks: [bold]write tasks acquire resources before execution[/]"
    )
    console.print(Panel(summary, title="[bold cyan]Mission Policy[/]", border_style="cyan"))
    console.print(table)


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
    role: Annotated[
        str,
        typer.Option("--role", help="Specific role to approve as (e.g., 'security', 'tech_lead')."),
    ] = "default",
) -> None:
    """Approve the latest planned mission."""
    from niyam.mission.planner import run_mission_approve

    try:
        run_mission_approve(
            console=console, interactive=interactive, mission_id=mission_id, role=role
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
    branch: Annotated[
        bool,
        typer.Option("--branch", "-b", help="Generate evidence report for the current branch."),
    ] = False,
    format: Annotated[
        Optional[ReportFormat],
        typer.Option("--format", "-f", help="Output format for branch report (markdown/json)."),
    ] = None,
) -> None:
    """Generate evidence report for the latest mission or current branch."""
    if branch:
        from niyam.evidence.reporter import run_report
        from niyam.cli.main_cmds import ReportFormat
        fmt = format or ReportFormat.md
        run_report(format=fmt.value, console=console)
    else:
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
            at.add_column("Tokens", justify="right", style="cyan")
            at.add_column("Total Cost", justify="right")
            at.add_column("Wasted", justify="right", style="red")
            
            for agent, stats in m["by_agent"].items():
                sr = (stats.get("completed", 0) / stats.get("count", 1)) * 100 if stats.get("count", 0) > 0 else 0
                at.add_row(
                    agent, 
                    str(stats.get("count", 0)), 
                    f"{sr:.1f}%",
                    f"{stats.get('tokens', 0):,}",
                    f"${stats.get('cost', 0.0):.4f}",
                    f"${stats.get('wasted', 0.0):.4f}"
                )
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
            at.add_column("Success Rate", justify="right", style="bold green")
            at.add_column("Tokens", justify="right", style="cyan")
            at.add_column("Total Cost", justify="right")
            at.add_column("Wasted", justify="right", style="red")
            
            # Sort by success rate
            sorted_agents = sorted(
                summary["agent_performance"].items(),
                key=lambda x: x[1]["success_rate"],
                reverse=True
            )
            
            for agent, stats in sorted_agents:
                at.add_row(
                    agent, 
                    str(stats["tasks"]), 
                    f"{stats['success_rate']:.1f}%",
                    f"{stats.get('tokens', 0):,}",
                    f"${stats.get('cost', 0.0):.4f}",
                    f"${stats.get('wasted', 0.0):.4f}"
                )
            console.print(at)


@mission_app.command("audit")
def mission_audit(
    mission_id: Annotated[
        Optional[str],
        typer.Option("--mission", help="Mission ID to audit."),
    ] = None,
    output: Annotated[
        Optional[str],
        typer.Option("--output", "-o", help="File to write the audit log to (Markdown)."),
    ] = None,
) -> None:
    """Show or export a full traceability audit of exact prompts and system instructions used."""
    import yaml
    from rich.markdown import Markdown
    from niyam.core.config import find_niyam_root, get_niyam_dir
    from niyam.mission.planner import resolve_mission_id

    repo_root = find_niyam_root()
    if not repo_root:
        console.print("[bold red]Error:[/] Not a Niyam workspace.")
        raise typer.Exit(1)
    niyam_dir = get_niyam_dir(repo_root)

    mission_id = resolve_mission_id(niyam_dir, mission_id)
    if not mission_id:
        console.print("[bold red]Error:[/] No missions found.")
        raise typer.Exit(1)

    run_dir = niyam_dir / "runs" / mission_id
    if not run_dir.exists():
        console.print(f"[bold red]Error:[/] Run directory for {mission_id} not found.")
        raise typer.Exit(1)

    audit_md = f"# Prompt Traceability Audit: Mission {mission_id}\n\n"
    
    plan_path = run_dir / "mission-plan.yaml"
    if plan_path.exists():
        try:
            with open(plan_path, encoding="utf-8") as f:
                plan_data = yaml.safe_load(f) or {}
                tasks = plan_data.get("tasks", [])
        except Exception:
            tasks = []
    else:
        tasks = []

    if not tasks:
        console.print("[yellow]No tasks found in mission plan.[/]")
        raise typer.Exit(0)

    for task in tasks:
        t_id = task.get("id", "Unknown")
        t_title = task.get("title", "Unknown")
        audit_md += f"## Task {t_id}: {t_title}\n\n"
        
        task_dir = run_dir / "tasks" / t_id
        prompt_path = task_dir / "prompt.md"
        
        if prompt_path.exists():
            prompt_content = prompt_path.read_text(encoding="utf-8")
            audit_md += "### Executed Prompt\n\n```markdown\n"
            audit_md += prompt_content + "\n```\n\n"
        else:
            audit_md += "### Executed Prompt\n\n*No prompt file found for this task.*\n\n"
            
        log_path = task_dir / "output.log"
        if log_path.exists():
            log_content = log_path.read_text(encoding="utf-8")
            audit_md += "### Agent Output Log (Excerpt)\n\n```text\n"
            audit_md += "\n".join(log_content.splitlines()[:50])
            if len(log_content.splitlines()) > 50:
                audit_md += "\n... [truncated for brevity]\n"
            audit_md += "\n```\n\n"

    if output:
        try:
            from pathlib import Path
            out_path = Path(output).resolve()
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(audit_md, encoding="utf-8")
            console.print(f"[bold green]✓[/] Audit log exported to [cyan]{out_path}[/]")
        except Exception as e:
            console.print(f"[bold red]Error exporting audit log:[/] {e}")
            raise typer.Exit(1)
    else:
        console.print(Panel(Markdown(audit_md), title=f"[bold cyan]Mission Audit: {mission_id}[/]", border_style="cyan"))


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


@mission_app.command("contract-schema")
def mission_contract_schema(
    output: Annotated[
        Optional[str],
        typer.Option("--output", "-o", help="File to write the JSON schema to."),
    ] = None,
) -> None:
    """Export the canonical JSON Schema for Niyam Task Contracts."""
    import json
    from niyam.core.config import TaskContract

    schema = TaskContract.model_json_schema()
    json_str = json.dumps(schema, indent=2)

    if output:
        try:
            from pathlib import Path
            out_path = Path(output).resolve()
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(json_str, encoding="utf-8")
            console.print(f"[bold green]✓[/] Task Contract JSON schema exported to [cyan]{out_path}[/]")
        except Exception as e:
            console.print(f"[bold red]Error exporting schema:[/] {e}")
            raise typer.Exit(1)
    else:
        console.print_json(json_str)

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


def interrogate_requirement(requirement: str, orchestrator: str, console) -> str:
    import shutil
    import subprocess

    console.print(
        f"[cyan]Deep analyzing requirement with {orchestrator} to identify missing context...[/]"
    )
    prompt = f"""
You are the Niyam project architect. I am about to give you a requirement. 
Before we start planning, identify 3 critical clarifying questions that would help you generate a perfect, production-ready implementation plan.

Requirement:
{requirement}

Format your response as a numbered list of 3 questions.
""".strip()

    if not shutil.which(orchestrator):
        return requirement

    cmd = [orchestrator, "-p", prompt]
    if orchestrator == "gemini":
        cmd.append("--skip-trust")

    try:
        res = subprocess.run(
            cmd,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if res.returncode != 0:
            return requirement
        raw = res.stdout or res.stderr or ""
    except Exception:
        return requirement

    console.print(
        "\n[bold cyan]Niyam needs a bit more context to be highly accurate:[/]"
    )
    console.print(raw.strip())

    console.print(
        "\n[dim](Enter your answers below, or just press Enter to skip and proceed with current context)[/]"
    )
    answers = []
    for i in range(1, 4):
        try:
            ans = input(f"Answer {i}: ").strip()
            if ans:
                answers.append(f"Q{i} Context: {ans}")
        except (KeyboardInterrupt, EOFError):
            break

    if answers:
        return (
            requirement + "\n\n## Additional Developer Context\n" + "\n".join(answers)
        )
    return requirement


@mission_app.command("validate-task")
def mission_validate_task(
    task_id: Annotated[
        str,
        typer.Argument(help="Task ID to validate (e.g., T1, TASK-001)."),
    ],
    mission: Annotated[
        Optional[str], typer.Option("--mission", help="Mission ID containing the task.")
    ] = None,
) -> None:
    """Validate a task's execution (scope enforcement and tests)."""
    from niyam.core.validate import run_task_validation

    try:
        run_task_validation(task_id=task_id, mission_id=mission, console=console)
    except Exception as e:
        console.print(f"[bold red]Error:[/] {e}")
        raise typer.Exit(1)


@mission_app.command("start-wizard")
def mission_start_wizard(
    runtime: Annotated[
        Optional[Runtime],
        typer.Option("--runtime", "-r", help="Runtime override for planning."),
    ] = None,
) -> None:
    """Interactive wizard to start a new task."""
    import sys
    import re
    from datetime import datetime
    from niyam.core.config import find_niyam_root, load_niyam_config
    from niyam.mission.planner import run_mission_plan

    repo_root = find_niyam_root()
    if not repo_root:
        console.print(
            "[bold red]Error:[/] Not a Niyam workspace. Run 'niyam init' first."
        )
        raise typer.Exit(1)

    console.print("🚀 [bold cyan]Welcome to Niyam! Let's start your new task.[/]")

    # 1. Ask for Task Name
    try:
        run_id = input("\n1. What is the name of this task? (e.g. ADD-AUTH): ").strip()
    except (KeyboardInterrupt, EOFError):
        console.print("\n[red]Cancelled.[/]")
        raise typer.Exit(1)

    if not run_id:
        run_id = f"RUN-{datetime.now().strftime('%m%d-%H%M')}"
        console.print(f"   (No name provided, using generated ID: {run_id})")

    # Clean the run_id
    run_id = re.sub(r"[^a-zA-Z0-9_\-]+", "-", run_id).strip("-")

    # 2. Ask for Requirement Source
    console.print("\n2. How would you like to provide the requirement?")
    console.print("   [1] Paste text (from clipboard/design doc)")
    console.print("   [2] Provide path to a Markdown file")
    try:
        choice = input("Choice [1/2]: ").strip()
    except (KeyboardInterrupt, EOFError):
        console.print("\n[red]Cancelled.[/]")
        raise typer.Exit(1)

    input_source = "-"
    requirement = ""
    if choice == "2":
        try:
            input_source = input("   Path to file: ").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[red]Cancelled.[/]")
            raise typer.Exit(1)

        if not Path(input_source).exists():
            console.print(
                f"   [yellow]Warning:[/] File {input_source} not found. Falling back to paste mode."
            )
            input_source = "-"
        else:
            requirement = Path(input_source).read_text(encoding="utf-8")

    if input_source == "-":
        console.print("   Paste requirement text below (Press Ctrl+D when finished):")
        try:
            requirement = sys.stdin.read()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[red]Cancelled.[/]")
            raise typer.Exit(1)

    # 3. Determine planning engine
    config = None
    try:
        config = load_niyam_config(repo_root)
    except Exception:
        pass

    default_engine = "claude"
    if config and config.runtimes:
        default_engine = config.runtimes[0]

    engine = runtime.value if runtime else default_engine
    if not runtime:
        console.print(
            f"\n3. Which planning engine should I use? (default: {default_engine})"
        )
        try:
            custom_engine = (
                input(
                    f"   Press Enter for {default_engine}, or type [claude/gemini/codex]: "
                )
                .strip()
                .lower()
            )
            if custom_engine in {"claude", "gemini", "codex"}:
                engine = custom_engine
        except (KeyboardInterrupt, EOFError):
            console.print("\n[red]Cancelled.[/]")
            raise typer.Exit(1)

    # Interrogation phase
    requirement = interrogate_requirement(requirement, engine, console)

    # 4. Confirm and Run Plan
    console.print(
        f"\n[cyan]Ready! Running plan generation for mission '{run_id}' using engine '{engine}'...[/]"
    )

    # We need a temporary file for the requirement
    temp_dir = repo_root / ".niyam" / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_req = temp_dir / f"{run_id}.md"
    temp_req.write_text(requirement, encoding="utf-8")

    try:
        run_mission_plan(
            requirements_path=str(temp_req),
            strict=False,
            console=console,
            template=None,
            runtime_override=engine,
        )
    finally:
        if temp_req.exists():
            temp_req.unlink()

