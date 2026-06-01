"""Niyam mission dashboard — live-monitoring of active mission status, tasks, and token metrics."""

from __future__ import annotations

import json
import time
from pathlib import Path
from datetime import datetime, timezone
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.columns import Columns
from rich.live import Live

from niyam.core.config import get_niyam_dir
from niyam.mission.planner import resolve_mission_id


def load_plan(run_dir: Path) -> dict:
    """Load mission plan YAML."""
    import yaml

    plan_path = run_dir / "mission-plan.yaml"
    with open(plan_path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def get_task_durations(run_dir: Path) -> dict[str, float]:
    """Parse execution log to get durations (seconds) of tasks."""
    durations = {}
    started_times = {}
    log_path = run_dir / "execution-log.json"
    if not log_path.exists():
        return durations

    try:
        with open(log_path, encoding="utf-8") as f:
            events = json.load(f) or []
    except Exception:
        events = []

    for ev in events:
        t_id = ev.get("task_id")
        if not t_id:
            continue
        event_name = ev.get("event")
        timestamp_str = ev.get("timestamp")
        if not timestamp_str:
            continue
        try:
            dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        except Exception:
            continue

        if event_name == "TASK_STARTED":
            started_times[t_id] = dt
        elif event_name in ("TASK_COMPLETED", "TASK_FAILED", "TASK_SKIPPED"):
            if t_id in started_times:
                durations[t_id] = (dt - started_times[t_id]).total_seconds()
            else:
                durations[t_id] = 0.0

    # For currently running tasks, estimate duration based on start time and current time
    for t_id, start_dt in started_times.items():
        if t_id not in durations:
            now_dt = datetime.now(timezone.utc)
            durations[t_id] = (now_dt - start_dt).total_seconds()

    return durations


def generate_dashboard_renderable(
    run_dir: Path, niyam_dir: Path, mission_id: str
) -> Panel:
    """Construct a beautiful dashboard layout."""
    try:
        plan_data = load_plan(run_dir)
    except Exception as e:
        return Panel(
            f"[bold yellow]Refreshing dashboard...[/]\n[dim]({e})[/]",
            title="[bold cyan]Niyam Dashboard[/]",
        )

    mission_meta = plan_data.get("mission", {})
    status = mission_meta.get("status", "planned")
    orchestrator = mission_meta.get("orchestrator", "claude")
    parallel = mission_meta.get("parallel", 1)
    worktree = mission_meta.get("worktree", True)
    created = mission_meta.get("created", "")

    status_colors = {
        "planned": "cyan",
        "running": "yellow",
        "completed": "green",
        "failed": "red",
        "paused": "magenta",
    }
    status_color = status_colors.get(status.lower(), "white")
    status_text = f"[{status_color} bold]{status.upper()}[/]"

    # Metadata table
    meta_table = Table.grid(padding=(0, 2))
    meta_table.add_column(style="bold cyan")
    meta_table.add_column()

    meta_table.add_row("Mission ID:", mission_id)
    meta_table.add_row("Status:", status_text)
    meta_table.add_row("Orchestrator:", orchestrator)
    meta_table.add_row("Concurrency:", f"{parallel} worker(s)")
    meta_table.add_row("Worktree Isolation:", "Enabled" if worktree else "Disabled")
    if created:
        meta_table.add_row("Created:", created)

    # Get durations
    durations = get_task_durations(run_dir)

    # Build tasks table
    tasks = plan_data.get("tasks", [])
    tasks_table = Table(
        title="[bold cyan]Mission Tasks[/]", show_header=True, expand=True
    )
    tasks_table.add_column("ID", width=6, style="bold magenta", justify="center")
    tasks_table.add_column("Title", style="white")
    tasks_table.add_column("Agent", style="yellow")
    tasks_table.add_column("Status", width=14, justify="center")
    tasks_table.add_column("Depends On", style="dim white")
    tasks_table.add_column("Duration", style="green", justify="right")

    status_icons = {
        "pending": "[white]⧖ pending[/]",
        "running": "[yellow]⚡ running[/]",
        "completed": "[green]✓ completed[/]",
        "failed": "[red]❌ failed[/]",
        "skipped": "[dim]↷ skipped[/]",
    }

    for t in tasks:
        t_id = t.get("id")
        t_title = t.get("title")
        t_agent = t.get("agent")
        t_status = t.get("status", "pending")
        t_deps = ", ".join(t.get("depends_on", [])) or "-"

        status_disp = status_icons.get(t_status.lower(), t_status)

        dur = durations.get(t_id, 0.0)
        dur_disp = f"{dur:.1f}s" if dur > 0 else "-"

        tasks_table.add_row(t_id, t_title, t_agent, status_disp, t_deps, dur_disp)

    # Token Ledger panel
    ledger_path = run_dir / "token-ledger.json"
    ledger = {}
    if ledger_path.exists():
        try:
            with open(ledger_path, encoding="utf-8") as f:
                ledger = json.load(f) or {}
        except Exception:
            pass

    summary = ledger.get("summary", {})

    ledger_table = Table(
        title="[bold green]Token & Cost Ledger[/]", show_header=False, expand=True
    )
    ledger_table.add_column(style="bold yellow")
    ledger_table.add_column(justify="right")

    total_tokens = summary.get("total_tokens", 0)
    total_cost = summary.get("total_cost_usd", 0.0)
    baseline_tokens = summary.get("total_baseline_tokens", 0)
    baseline_cost = summary.get("total_baseline_cost_usd", 0.0)
    savings_tokens = max(0, baseline_tokens - total_tokens)
    savings_cost = max(0.0, baseline_cost - total_cost)
    savings_pct = summary.get("savings_percent", 0.0)

    ledger_table.add_row("Actual Tokens used:", f"{total_tokens:,}")
    ledger_table.add_row("Actual Cost:", f"${total_cost:.4f}")
    ledger_table.add_row("Baseline Est. Tokens:", f"{baseline_tokens:,}")
    ledger_table.add_row("Baseline Est. Cost:", f"${baseline_cost:.4f}")
    ledger_table.add_row("Tokens Saved:", f"[green]{savings_tokens:,}[/]")
    ledger_table.add_row("Cost Saved:", f"[green]${savings_cost:.4f}[/]")
    ledger_table.add_row("Efficiency Savings %:", f"[bold green]{savings_pct:.1f}%[/]")

    # Layout assembly
    meta_panel = Panel(meta_table, title="[bold]Mission Config[/]", border_style="cyan")
    ledger_panel = Panel(
        ledger_table, title="[bold]Resource Metrics[/]", border_style="green"
    )

    header_cols = Columns([meta_panel, ledger_panel], expand=True)

    # Active log tail
    running_task_ids = [t.get("id") for t in tasks if t.get("status") == "running"]
    log_contents = []
    for r_id in running_task_ids:
        log_path = run_dir / "worktrees" / r_id / f"task-{r_id}-output.log"
        if not log_path.exists():
            log_path = run_dir / f"task-{r_id}-output.log"
        if log_path.exists():
            try:
                with open(log_path, encoding="utf-8") as lf:
                    lines = lf.readlines()
                    last_lines = [line.rstrip() for line in lines[-12:]]
                    log_contents.append(
                        f"[bold cyan]Task {r_id} Log Output:[/]\n"
                        + "\n".join(last_lines)
                    )
            except Exception:
                pass

    if not log_contents:
        log_disp = "[dim]No active task logs. Execution is either paused, completed, or waiting...[/]"
    else:
        log_disp = "\n\n".join(log_contents)

    log_panel = Panel(
        log_disp, title="[bold]Active Task Logs[/]", border_style="magenta", expand=True
    )

    # Validation results tail
    val_path = run_dir / "validation-results.md"
    val_disp = "[dim]No validation checks run yet for this mission.[/]"
    if val_path.exists():
        try:
            with open(val_path, encoding="utf-8") as vf:
                lines = vf.readlines()
                last_val_lines = [line.rstrip() for line in lines[-12:]]
                val_disp = "\n".join(last_val_lines)
        except Exception:
            pass

    val_panel = Panel(
        val_disp,
        title="[bold]Validation Suite Output[/]",
        border_style="blue",
        expand=True,
    )

    main_group = Table.grid(expand=True)
    main_group.add_row(header_cols)
    main_group.add_row("")
    main_group.add_row(tasks_table)
    main_group.add_row("")

    lower_cols = Columns([log_panel, val_panel], expand=True)
    main_group.add_row(lower_cols)

    return Panel(
        main_group,
        title="[bold magenta]NIYAM[/] [bold cyan]MISSION DASHBOARD[/]",
        border_style="cyan",
    )


def run_mission_dashboard(
    watch: bool, console: Console, mission_id: str | None = None
) -> None:
    """Render the mission dashboard."""
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
    if not run_dir.exists():
        console.print(f"[bold red]Error:[/] Mission directory not found at {run_dir}")
        raise SystemExit(1)

    if watch:
        console.print(
            "[dim]Starting dashboard in live-monitoring mode. Press Ctrl+C to exit.[/]"
        )
        with Live(
            generate_dashboard_renderable(run_dir, niyam_dir, mission_id),
            console=console,
            auto_refresh=True,
            refresh_per_second=2,
        ) as live:
            try:
                while True:
                    time.sleep(0.5)
                    live.update(
                        generate_dashboard_renderable(run_dir, niyam_dir, mission_id)
                    )
            except KeyboardInterrupt:
                pass
    else:
        console.print(generate_dashboard_renderable(run_dir, niyam_dir, mission_id))
