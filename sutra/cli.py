"""Sutra CLI — governed AI-development workspaces."""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console

from sutra import __version__

# ── App & Console ──────────────────────────────────────────────────────

app = typer.Typer(
    name="sutra",
    help="Governed AI-development workspaces for Claude Code, Codex CLI, and future coding runtimes.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)
console = Console()

# ── Subcommand groups ──────────────────────────────────────────────────

context_app = typer.Typer(
    name="context",
    help="Manage project context for AI agents.",
    no_args_is_help=True,
)
app.add_typer(context_app)

guard_app = typer.Typer(
    name="guard",
    help="Safety guardrails for AI-assisted development.",
    no_args_is_help=True,
)
app.add_typer(guard_app)

runtime_app = typer.Typer(
    name="runtime",
    help="Manage AI runtime adapters.",
    no_args_is_help=True,
)
app.add_typer(runtime_app)

policy_app = typer.Typer(
    name="policy",
    help="Policy management and validation.",
    no_args_is_help=True,
)
app.add_typer(policy_app)

pack_app = typer.Typer(
    name="pack",
    help="Manage modular pack bundles.",
    no_args_is_help=True,
)
app.add_typer(pack_app)

memory_app = typer.Typer(
    name="memory",
    help="Manage project memory and context.",
    no_args_is_help=True,
)
app.add_typer(memory_app)

mission_app = typer.Typer(
    name="mission",
    help="Manage the single-agent mission lifecycle.",
    no_args_is_help=True,
)
app.add_typer(mission_app)

review_app = typer.Typer(
    name="review",
    help="Run structured reviews on code or pull requests.",
    no_args_is_help=False,
)
app.add_typer(review_app)

pr_app = typer.Typer(
    name="pr",
    help="Manage pull requests with evidence reports.",
    no_args_is_help=True,
)
app.add_typer(pr_app)

ci_app = typer.Typer(
    name="ci",
    help="CI/CD environment verification checks.",
    no_args_is_help=True,
)
app.add_typer(ci_app)



# ── Enums ──────────────────────────────────────────────────────────────


class Runtime(str, Enum):
    claude = "claude"
    codex = "codex"
    gemini = "gemini"


class ReportFormat(str, Enum):
    md = "md"
    json = "json"


class ReviewLens(str, Enum):
    product = "product"
    engineering = "engineering"
    design = "design"
    security = "security"


class ReviewMode(str, Enum):
    collaborative = "collaborative"
    adversarial = "adversarial"


# ── Top-level commands ─────────────────────────────────────────────────


@app.command()
def version() -> None:
    """Show the Sutra version."""
    console.print(f"[bold cyan]sutra[/] {__version__}")


@app.command()
def init(
    profile: Annotated[
        str,
        typer.Option("--profile", "-p", help="Project profile to use (e.g., fullstack, backend, frontend, startup-saas, platform-engineering, governed-enterprise)."),
    ] = "fullstack",
    runtime: Annotated[
        Optional[Runtime],
        typer.Option("--runtime", "-r", help="Initial runtime to configure."),
    ] = None,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Preview changes without writing files."),
    ] = False,
    force: Annotated[
        bool,
        typer.Option("--force", help="Overwrite existing .sutra/ directory."),
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
        typer.Argument(help="Requirement text or path to requirements markdown file."),
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
        typer.Option("--auto-approve", help="Skip approval gate and execute immediately."),
    ] = False,
    strict: Annotated[
        bool,
        typer.Option("--strict", help="Fail if AI-powered planning fails, instead of falling back."),
    ] = False,
    worktree: Annotated[
        Optional[bool],
        typer.Option("--worktree/--no-worktree", help="Enable or disable git worktree isolation."),
    ] = None,
    template: Annotated[
        Optional[str],
        typer.Option("--template", "-t", help="Use a mission template for planning."),
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
    console.print(f"\n[cyan]3. Generating mission plan...[/]")
    mission_id = run_mission_plan(
        requirements_path=requirement,
        strict=strict,
        console=console,
        template=template,
        runtime_override=runtime.value if runtime else None
    )

    # 4. Approve plan
    console.print(f"\n[cyan]4. Checking plan approval...[/]")
    run_mission_approve(console=console, interactive=not auto_approve)

    # 5. Start execution
    console.print(f"\n[cyan]5. Starting execution for mission '{mission_id}'...[/]")
    run_mission_start(
        parallel=parallel,
        worktree=worktree,
        non_interactive=auto_approve,
        console=console
    )


@app.command()
def sync(
    runtime: Annotated[
        Optional[Runtime],
        typer.Option("--runtime", "-r", help="Sync a specific runtime only."),
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


@review_app.callback(invoke_without_command=True)
def review(
    ctx: typer.Context,
    lens: Annotated[
        ReviewLens,
        typer.Option("--lens", "-l", help="Review lens/perspective."),
    ] = ReviewLens.engineering,
    runtime: Annotated[
        Runtime,
        typer.Option("--runtime", "-r", help="Runtime to execute the review with."),
    ] = Runtime.claude,
    mode: Annotated[
        ReviewMode,
        typer.Option("--mode", "-m", help="Review mode."),
    ] = ReviewMode.collaborative,
) -> None:
    """Run a structured code review on current changes."""
    if ctx.invoked_subcommand is not None:
        return
    from sutra.core.review import run_review

    run_review(
        lens=lens.value,
        runtime=runtime.value,
        mode=mode.value,
        console=console,
    )


@review_app.command("pr")
def review_pr(
    pr: Annotated[str, typer.Argument(help="Pull Request ID.")],
    lens: Annotated[
        ReviewLens,
        typer.Option("--lens", "-l", help="Review lens/perspective."),
    ] = ReviewLens.engineering,
    runtime: Annotated[
        Runtime,
        typer.Option("--runtime", "-r", help="Runtime to execute the review with."),
    ] = Runtime.claude,
    mode: Annotated[
        ReviewMode,
        typer.Option("--mode", "-m", help="Review mode."),
    ] = ReviewMode.collaborative,
    token: Annotated[
        Optional[str],
        typer.Option("--token", help="GitHub token (overrides GITHUB_TOKEN environment variable)."),
    ] = None,
) -> None:
    """Run a structured code review on a GitHub pull request."""
    from sutra.core.pr import run_pr_review

    try:
        run_pr_review(
            pr_id=pr,
            lens=lens.value,
            runtime=runtime.value,
            mode=mode.value,
            token=token,
            console=console,
        )
    except Exception as e:
        console.print(f"[bold red]Error:[/] {e}")
        raise typer.Exit(1)


@pr_app.command("create")
def pr_create(
    title: Annotated[str, typer.Option("--title", "-t", help="Pull Request title.")],
    body: Annotated[Optional[str], typer.Option("--body", "-b", help="Pull Request body/description.")] = None,
    base: Annotated[str, typer.Option("--base", help="Target branch for the pull request.")] = "main",
    token: Annotated[
        Optional[str],
        typer.Option("--token", help="GitHub token (overrides GITHUB_TOKEN environment variable)."),
    ] = None,
) -> None:
    """Push the active branch and create a GitHub pull request with evidence report attached."""
    from sutra.core.pr import run_pr_create

    try:
        run_pr_create(
            title=title,
            body=body,
            base=base,
            token=token,
            console=console,
        )
    except Exception as e:
        console.print(f"[bold red]Error:[/] {e}")
        raise typer.Exit(1)


@app.command()
def dashboard(
    watch: Annotated[
        bool,
        typer.Option("--watch", "-w", help="Periodically refresh the dashboard (live mode)."),
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


# ── Context subcommands ────────────────────────────────────────────────


@context_app.command("refresh")
def context_refresh() -> None:
    """Scan the repo and update project context."""
    from sutra.core.context import run_context_refresh

    run_context_refresh(console=console)


@context_app.command("show")
def context_show() -> None:
    """Display current project context."""
    from sutra.core.context import run_context_show

    run_context_show(console=console)


@context_app.command("diff")
def context_diff() -> None:
    """Show changes since last context refresh."""
    from sutra.core.context import run_context_diff

    run_context_diff(console=console)


# ── Guard subcommands ──────────────────────────────────────────────────


@guard_app.command("enable")
def guard_enable() -> None:
    """Enable all configured guardrails."""
    from sutra.policies.guard import run_guard_enable

    run_guard_enable(console=console)


@guard_app.command("disable")
def guard_disable() -> None:
    """Disable all guardrails."""
    from sutra.policies.guard import run_guard_disable

    run_guard_disable(console=console)


@guard_app.command("careful")
def guard_careful() -> None:
    """Enable destructive-command warnings."""
    from sutra.policies.guard import run_guard_careful

    run_guard_careful(console=console)


@guard_app.command("freeze")
def guard_freeze(
    path: Annotated[
        str,
        typer.Argument(help="Path to restrict edits to."),
    ],
) -> None:
    """Restrict AI edits to a specific directory."""
    from sutra.policies.guard import run_guard_freeze

    run_guard_freeze(path=path, console=console)


# ── Runtime subcommands ────────────────────────────────────────────────


@runtime_app.command("add")
def runtime_add(
    runtime: Annotated[
        Runtime,
        typer.Argument(help="Runtime to add."),
    ],
) -> None:
    """Add and configure a new AI runtime."""
    from sutra.core.sync import run_runtime_add

    run_runtime_add(runtime=runtime.value, console=console)


# ── Policy subcommands ─────────────────────────────────────────────────


@policy_app.command("validate")
def policy_validate() -> None:
    """Validate all policy YAML files."""
    from sutra.policies.validator import run_policy_validate

    run_policy_validate(console=console)


# ── Pack subcommands ───────────────────────────────────────────────────


@pack_app.command("list")
def pack_list() -> None:
    """Show available and installed packs."""
    from sutra.core.packs import list_packs
    from rich.table import Table
    from sutra.core.config import find_sutra_root
    from sutra.core.errors import SutraConfigError

    root = find_sutra_root()
    if not root:
        raise SutraConfigError("Not a Sutra workspace. Run 'sutra init' first.")

    packs = list_packs(root)
    if not packs:
        console.print("[yellow]No packs found.[/]")
        return

    table = Table(title="Sutra Packs")
    table.add_column("Pack Name", style="cyan")
    table.add_column("Version", style="magenta")
    table.add_column("Description", style="green")
    table.add_column("Status", style="bold")

    for p in packs:
        status = "[green]Installed[/]" if p["installed"] else "[dim]Not Installed[/]"
        table.add_row(p["name"], p["version"], p["description"], status)

    console.print(table)


@pack_app.command("add")
def pack_add(
    name: Annotated[str, typer.Argument(help="Name of the pack to add.")],
    force: Annotated[bool, typer.Option("--force", help="Overwrite existing files.")] = False,
) -> None:
    """Install a pack into the workspace."""
    from sutra.core.packs import add_pack
    from sutra.core.sync import run_sync
    from sutra.core.config import find_sutra_root
    from sutra.core.errors import SutraConfigError

    try:
        root = find_sutra_root()
        if not root:
            raise SutraConfigError("Not a Sutra workspace. Run 'sutra init' first.")
        add_pack(root, name, force=force, console=console)
        console.print(f"[bold green]✓[/] Pack '[cyan]{name}[/]' successfully installed.")
        # Trigger run_sync to sync config/runtimes
        run_sync(runtime=None, console=console)
    except Exception as e:
        console.print(f"[bold red]Error:[/] {e}")
        raise typer.Exit(1)


@pack_app.command("remove")
def pack_remove(
    name: Annotated[str, typer.Argument(help="Name of the pack to remove.")],
) -> None:
    """Remove an installed pack from the workspace."""
    from sutra.core.packs import remove_pack
    from sutra.core.sync import run_sync
    from sutra.core.config import find_sutra_root
    from sutra.core.errors import SutraConfigError

    try:
        root = find_sutra_root()
        if not root:
            raise SutraConfigError("Not a Sutra workspace. Run 'sutra init' first.")
        remove_pack(root, name, console=console)
        console.print(f"[bold green]✓[/] Pack '[cyan]{name}[/]' successfully removed.")
        run_sync(runtime=None, console=console)
    except Exception as e:
        console.print(f"[bold red]Error:[/] {e}")
        raise typer.Exit(1)


@pack_app.command("sync")
def pack_sync() -> None:
    """Re-sync all installed packs."""
    from sutra.core.packs import sync_packs
    from sutra.core.sync import run_sync
    from sutra.core.config import find_sutra_root
    from sutra.core.errors import SutraConfigError

    try:
        root = find_sutra_root()
        if not root:
            raise SutraConfigError("Not a Sutra workspace. Run 'sutra init' first.")
        sync_packs(root, console=console)
        console.print("[bold green]✓[/] Packs successfully synced.")
        run_sync(runtime=None, console=console)
    except Exception as e:
        console.print(f"[bold red]Error:[/] {e}")
        raise typer.Exit(1)


# ── Memory subcommands ─────────────────────────────────────────────────


@memory_app.command("show")
def memory_show() -> None:
    """Display all memory files and their content."""
    from sutra.core.memory import run_memory_show

    run_memory_show(console=console)


@memory_app.command("add")
def memory_add(
    file: Annotated[str, typer.Argument(help="Memory file to append to (e.g. project-lessons).")],
    note: Annotated[str, typer.Argument(help="Note to append.")],
) -> None:
    """Append a note to a memory file."""
    from sutra.core.memory import run_memory_add
    from sutra.core.sync import run_sync

    run_memory_add(file=file, note=note, console=console)
    run_sync(runtime=None, console=console)


@memory_app.command("clear")
def memory_clear(
    file: Annotated[str, typer.Argument(help="Memory file to clear.")],
) -> None:
    """Clear a memory file, resetting it to its title/headers."""
    from sutra.core.memory import run_memory_clear
    from sutra.core.sync import run_sync

    run_memory_clear(file=file, console=console)
    run_sync(runtime=None, console=console)


# ── Mission subcommands ────────────────────────────────────────────────


@mission_app.command("plan")
def mission_plan(
    requirements: Annotated[str, typer.Argument(help="Path to requirements markdown file.")],
    strict: Annotated[
        bool,
        typer.Option("--strict", help="Fail if AI-powered planning fails, instead of falling back."),
    ] = False,
    template: Annotated[
        Optional[str],
        typer.Option("--template", "-t", help="Use a mission template for planning."),
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
            runtime_override=runtime.value if runtime else None
        )
    except Exception as e:
        console.print(f"[bold red]Error:[/] {e}")
        raise typer.Exit(1)


@mission_app.command("show")
def mission_show() -> None:
    """Display tasks and configuration of the latest planned or active mission."""
    from sutra.mission.planner import get_latest_mission_id
    from sutra.core.config import get_sutra_dir, find_sutra_root
    from sutra.core.errors import SutraConfigError
    from rich.table import Table
    from rich.panel import Panel
    import yaml

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
        table.add_row(t_id, t_title, t_agent, t_rt, t_deps, t_writes, f"[{col}]{t_status}[/]")

    console.print(Panel(table, border_style="magenta"))


@mission_app.command("dashboard")
def mission_dashboard(
    watch: Annotated[
        bool,
        typer.Option("--watch", "-w", help="Periodically refresh the dashboard (live mode)."),
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
    from sutra.mission.validator import validate_mission_plan, PlanValidationError
    from sutra.mission.planner import get_latest_mission_id
    from sutra.core.config import get_sutra_dir, find_sutra_root
    from sutra.core.errors import SutraConfigError

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
        console.print(f"[bold green]✓[/] Mission plan '{mission_id}' is valid and ready for approval.")
    except PlanValidationError as e:
        console.print(f"[bold red]❌ Mission plan validation failed with {len(e.errors)} error(s):[/]")
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
        typer.Option("--interactive", "-i", help="Approve tasks interactively with option to edit the plan."),
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
        typer.Option("--parallel", "-p", help="Override the number of parallel workers."),
    ] = None,
    worktree: Annotated[
        Optional[bool],
        typer.Option("--worktree/--no-worktree", help="Enable or disable git worktree isolation."),
    ] = None,
    non_interactive: Annotated[
        bool,
        typer.Option("--non-interactive", "--ci", help="Run in non-interactive (CI/CD) mode."),
    ] = False,
) -> None:
    """Start or resume the latest approved mission."""
    from sutra.mission.executor import run_mission_start

    try:
        run_mission_start(parallel=parallel, worktree=worktree, non_interactive=non_interactive, console=console)
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
        typer.Option("--parallel", "-p", help="Override the number of parallel workers."),
    ] = None,
    worktree: Annotated[
        Optional[bool],
        typer.Option("--worktree/--no-worktree", help="Enable or disable git worktree isolation."),
    ] = None,
    non_interactive: Annotated[
        bool,
        typer.Option("--non-interactive", "--ci", help="Run in non-interactive (CI/CD) mode."),
    ] = False,
) -> None:
    """Resume a paused mission."""
    from sutra.mission.executor import run_mission_resume

    try:
        run_mission_resume(parallel=parallel, worktree=worktree, non_interactive=non_interactive, console=console)
    except Exception as e:
        console.print(f"[bold red]Error:[/] {e}")
        raise typer.Exit(1)


@mission_app.command("retry")
def mission_retry(
    parallel: Annotated[
        Optional[int],
        typer.Option("--parallel", "-p", help="Override the number of parallel workers."),
    ] = None,
    worktree: Annotated[
        Optional[bool],
        typer.Option("--worktree/--no-worktree", help="Enable or disable git worktree isolation."),
    ] = None,
    non_interactive: Annotated[
        bool,
        typer.Option("--non-interactive", "--ci", help="Run in non-interactive (CI/CD) mode."),
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
        typer.Option("--parallel", "-p", help="Override the number of parallel workers."),
    ] = None,
    worktree: Annotated[
        Optional[bool],
        typer.Option("--worktree/--no-worktree", help="Enable or disable git worktree isolation."),
    ] = None,
    non_interactive: Annotated[
        bool,
        typer.Option("--non-interactive", "--ci", help="Run in non-interactive (CI/CD) mode."),
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
    evidence_file: Annotated[str, typer.Argument(help="Path to the evidence.md report to verify.")],
) -> None:
    """Verify the cryptographic integrity of an evidence report."""
    from sutra.mission.reporter import run_verify_report

    try:
        run_verify_report(evidence_path=evidence_file, console=console)
    except Exception as e:
        console.print(f"[bold red]Error:[/] {e}")
        raise typer.Exit(1)


@ci_app.command("verify")
def ci_verify(
    target: Annotated[
        str,
        typer.Option("--target", "-t", help="Target branch to compare changes against."),
    ] = "main",
    strict: Annotated[
        bool,
        typer.Option("--strict/--no-strict", help="Fail build on integrity warnings or missing evidence."),
    ] = True,
) -> None:
    """Verify cryptographic integrity, guardrails, and validation status for CI/CD."""
    from sutra.core.ci import run_ci_verify

    try:
        run_ci_verify(target_branch=target, strict=strict, console=console)
    except Exception as e:
        console.print(f"[bold red]Error:[/] {e}")
        raise typer.Exit(1)



def main() -> None:
    """CLI entry point catching SutraError exceptions."""
    from sutra.core.errors import SutraError
    try:
        app()
    except SutraError as e:
        console.print(f"[bold red]Error:[/] {e}")
        raise SystemExit(e.code)


if __name__ == "__main__":
    main()
