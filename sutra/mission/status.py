"""Sutra mission status — view progress of a running mission."""

from __future__ import annotations

from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from sutra.core.config import get_sutra_dir
from sutra.mission.planner import get_latest_mission_id
from sutra.mission.executor import load_plan


def run_mission_status(console: Console) -> None:
    """Show status of the latest mission."""
    repo_root = Path.cwd()
    sutra_dir = get_sutra_dir(repo_root)

    mission_id = get_latest_mission_id(sutra_dir)
    if not mission_id:
        console.print("[yellow]No missions found.[/]")
        return

    run_dir = sutra_dir / "runs" / mission_id
    plan_data = load_plan(run_dir)
    mission_meta = plan_data.get("mission", {})

    status = mission_meta.get("status", "unknown")
    created = mission_meta.get("created", "")

    status_colors = {
        "planned": "cyan",
        "approved": "magenta",
        "running": "green",
        "paused": "yellow",
        "completed": "bold green",
        "failed": "bold red",
    }
    color = status_colors.get(status, "white")

    console.print(Panel(
        f"Mission ID: [bold cyan]{mission_id}[/]\n"
        f"Status: [{color}]{status.upper()}[/]\n"
        f"Created: [dim]{created}[/]\n"
        f"Orchestrator: [bold]{mission_meta.get('orchestrator', 'claude')}[/]",
        title="[bold]Mission Status Overview[/]",
        border_style=status_colors.get(status, "cyan")
    ))

    table = Table(title="Mission Task Checklist")
    table.add_column("ID", style="dim", width=4)
    table.add_column("Task Title", style="bold", width=45)
    table.add_column("Agent", style="cyan", width=20)
    table.add_column("Status", style="magenta", width=12)

    status_icons = {
        "pending": "[dim]Pending[/]",
        "running": "[yellow]▶ Running[/]",
        "completed": "[green]✓ Completed[/]",
        "failed": "[red]✗ Failed[/]",
        "skipped": "[dim]Skipped[/]",
    }

    for task in plan_data.get("tasks", []):
        t_status = task.get("status", "pending")
        icon = status_icons.get(t_status, t_status)
        table.add_row(
            task.get("id", ""),
            task.get("title", ""),
            task.get("agent", ""),
            icon
        )

    console.print(table)
