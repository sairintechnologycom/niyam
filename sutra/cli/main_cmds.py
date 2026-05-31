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
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            "-v",
            help="Show detailed file updates during synchronization.",
        ),
    ] = False,
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            help="Preview sync changes without writing files.",
        ),
    ] = False,
) -> None:
    """Sync .sutra/ source of truth to all configured runtimes."""
    from sutra.core.sync import run_sync

    run_sync(
        runtime=runtime.value if runtime else None,
        console=console,
        verbose=verbose,
        dry_run=dry_run,
    )


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
    check: Annotated[
        bool,
        typer.Option(
            "--check",
            help="Run configured lint/format validation checks.",
        ),
    ] = False,
    smoke_test: Annotated[
        bool,
        typer.Option(
            "--smoke-test",
            help="Run headless smoke tests for planner and Claude.",
        ),
    ] = False,
) -> None:
    """Validate .sutra/ configuration and runtime projections."""
    from sutra.core.doctor import run_doctor

    run_doctor(
        runtime=runtime.value if runtime else None,
        console=console,
        check=check,
        smoke_test=smoke_test,
    )


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
def hello(
    name: Annotated[
        Optional[str],
        typer.Option("--name", "-n", help="Name to greet."),
    ] = None,
) -> None:
    """A friendly greeting from Sutra."""
    if name:
        console.print(f"Hello, {name}!")
    else:
        console.print("Hello, Sutra Developer!")


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


def interrogate_requirement(requirement: str, orchestrator: str, console) -> str:
    import shutil
    import subprocess

    console.print(
        f"[cyan]Deep analyzing requirement with {orchestrator} to identify missing context...[/]"
    )
    prompt = f"""
You are the Sutra project architect. I am about to give you a requirement. 
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
        "\n[bold cyan]Sutra needs a bit more context to be highly accurate:[/]"
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


@app.command()
def start(
    runtime: Annotated[
        Optional[Runtime],
        typer.Option("--runtime", "-r", help="Runtime override for planning."),
    ] = None,
) -> None:
    """Interactive wizard to start a new task."""
    import sys
    from datetime import datetime
    from pathlib import Path
    from sutra.core.config import find_sutra_root, load_sutra_config
    from sutra.mission.planner import run_mission_plan

    repo_root = find_sutra_root()
    if not repo_root:
        console.print(
            "[bold red]Error:[/] Not a Sutra workspace. Run 'sutra init' first."
        )
        raise typer.Exit(1)

    console.print("🚀 [bold cyan]Welcome to Sutra! Let's start your new task.[/]")

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
    import re

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
        config = load_sutra_config(repo_root)
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
    temp_dir = repo_root / ".sutra" / "temp"
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


@app.command()
def next(
    chain: Annotated[
        bool,
        typer.Option(
            "--chain",
            help="Automatically run through all steps without stopping.",
        ),
    ] = False,
) -> None:
    """Automatically execute the next step in the current run."""
    import yaml
    from sutra.core.config import find_sutra_root, get_sutra_dir
    from sutra.mission.planner import resolve_mission_id
    from sutra.mission.validator import validate_mission_plan, PlanValidationError
    from sutra.mission.planner import run_mission_approve
    from sutra.mission.executor import run_mission_start, run_mission_resume

    repo_root = find_sutra_root()
    if not repo_root:
        console.print(
            "[bold red]Error:[/] Not a Sutra workspace. Run 'sutra init' first."
        )
        raise typer.Exit(1)

    sutra_dir = get_sutra_dir(repo_root)
    mission_id = resolve_mission_id(sutra_dir)

    if not mission_id:
        console.print("No active run found. Starting a new task wizard...")
        start()
        if chain:
            next(chain=chain)
        return

    run_dir = sutra_dir / "runs" / mission_id
    plan_path = run_dir / "mission-plan.yaml"

    if not plan_path.exists():
        console.print(f"[bold red]Error:[/] Mission plan for '{mission_id}' not found.")
        raise typer.Exit(1)

    with open(plan_path, encoding="utf-8") as f:
        plan_data = yaml.safe_load(f) or {}

    mission_meta = plan_data.get("mission", {})
    status = mission_meta.get("status", "planned")

    approval_path = run_dir / "approval.json"
    approved = False
    if approval_path.exists():
        import json

        try:
            with open(approval_path, encoding="utf-8") as f:
                app_data = json.load(f)
            approved = app_data.get("approved", False)
        except Exception:
            pass

    console.print(f"Current Run: [cyan]{mission_id}[/] [Status: [yellow]{status}[/]]")

    if status == "planned":
        console.print("Next logical step: Validating the plan.")
        try:
            validate_mission_plan(plan_path, repo_root)
            console.print(
                f"[bold green]✓[/] Mission plan '{mission_id}' is valid and ready for approval."
            )
            plan_data["mission"]["status"] = "validated"
            with open(plan_path, "w", encoding="utf-8") as f:
                yaml.dump(plan_data, f, default_flow_style=False, sort_keys=False)
        except PlanValidationError as e:
            console.print("[bold red]❌ Mission plan validation failed:[/]")
            for err in e.errors:
                console.print(f"  • [red]{err}[/]")
            raise typer.Exit(1)
        except Exception as e:
            console.print(f"[bold red]Error during validation:[/] {e}")
            raise typer.Exit(1)

        if chain:
            next(chain=chain)

    elif status == "validated" or (status == "planned" and not approved):
        if not approved:
            console.print("Next logical step: Approving the plan.")
            try:
                run_mission_approve(
                    console=console, interactive=not chain, mission_id=mission_id
                )
            except Exception as e:
                console.print(f"[bold red]Error during approval:[/] {e}")
                raise typer.Exit(1)
            if chain:
                next(chain=chain)
        else:
            console.print("Next logical step: Running the tasks.")
            try:
                run_mission_start(
                    console=console,
                    parallel=None,
                    worktree=None,
                    non_interactive=chain,
                    mission_id=mission_id,
                )
            except Exception as e:
                console.print(f"[bold red]Error starting mission:[/] {e}")
                raise typer.Exit(1)

    elif status == "running" or status == "paused" or status == "blocked":
        console.print("Resuming current run.")
        try:
            run_mission_resume(
                console=console,
                parallel=None,
                worktree=None,
                non_interactive=chain,
                mission_id=mission_id,
            )
        except Exception as e:
            console.print(f"[bold red]Error resuming mission:[/] {e}")
            raise typer.Exit(1)

    elif status == "completed":
        console.print("Current run is completed. Launching dashboard.")
        try:
            from sutra.mission.dashboard import run_mission_dashboard

            run_mission_dashboard(watch=False, console=console, mission_id=mission_id)
        except Exception as e:
            console.print(f"[bold red]Error displaying dashboard:[/] {e}")
            raise typer.Exit(1)
    else:
        console.print(
            f"Unknown status '{status}'. Try running 'sutra mission status --mission {mission_id}' for details."
        )


@app.command()
def update() -> None:
    """Update Sutra CLI to the latest version."""
    import sys
    import os
    import subprocess
    from pathlib import Path

    console.print("Checking for updates...")

    # 1. Check if we are running from a git clone (editable install).
    repo_root = Path(__file__).parent.parent.parent
    if (repo_root / ".git").exists():
        console.print("Detected editable/git installation. Pulling latest changes...")
        try:
            subprocess.run(["git", "pull"], check=True, cwd=str(repo_root))
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-e", "."],
                check=True,
                cwd=str(repo_root),
            )
            console.print("[green]Successfully updated from git.[/]")
        except Exception as exc:
            console.print(f"[red]Update failed:[/] {exc}")
        return

    # 2. Check for pipx.
    is_pipx = "pipx" in sys.executable or "/.local/share/pipx/" in sys.executable
    if is_pipx:
        console.print("Detected pipx installation. Updating via pipx...")
        try:
            subprocess.run(["pipx", "upgrade", "sutra-cli"], check=True)
            console.print("[green]Successfully updated via pipx.[/]")
        except Exception as exc:
            console.print(f"[red]Pipx update failed:[/] {exc}")
        return

    # 3. Default to pip update.
    console.print("Updating via pip...")
    cmd = [sys.executable, "-m", "pip", "install", "--upgrade", "sutra-cli"]

    # Check for PEP 668 externally managed environment.
    if sys.platform == "darwin" or os.path.exists("/etc/os-release"):
        cmd.append("--break-system-packages")

    try:
        subprocess.run(cmd, check=True)
        console.print("[green]Successfully updated via pip.[/]")
    except Exception as exc:
        console.print(f"[red]Pip update failed:[/] {exc}")
        console.print(
            "\nTip: If you are on macOS, we recommend using 'pipx upgrade sutra-cli' or "
            "'brew install pipx' if you haven't yet."
        )
