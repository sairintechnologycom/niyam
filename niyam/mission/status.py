"""Niyam mission status — view progress of a running mission."""

from __future__ import annotations

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from niyam.core.config import get_niyam_dir
from niyam.mission.planner import resolve_mission_id
from niyam.mission.utils import load_plan


def run_mission_status(console: Console, mission_id: str | None = None) -> None:
    """Show status of the selected or active mission."""
    from niyam.core.config import find_niyam_root
    from niyam.core.errors import NiyamConfigError

    repo_root = find_niyam_root()
    if not repo_root:
        raise NiyamConfigError("Not a Niyam workspace. Run 'niyam init' first.")
    niyam_dir = get_niyam_dir(repo_root)

    mission_id = resolve_mission_id(niyam_dir, mission_id)
    if not mission_id:
        console.print("[yellow]No missions found.[/]")
        return

    run_dir = niyam_dir / "runs" / mission_id
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
        "cancelled": "dim white",
        "rolled_back": "bold yellow",
    }
    color = status_colors.get(status, "white")

    console.print(
        Panel(
            f"Mission ID: [bold cyan]{mission_id}[/]\n"
            f"Status: [{color}]{status.upper()}[/]\n"
            f"Created: [dim]{created}[/]\n"
            f"Orchestrator: [bold]{mission_meta.get('orchestrator', 'claude')}[/]",
            title="[bold]Mission Status Overview[/]",
            border_style=status_colors.get(status, "cyan"),
        )
    )

    table = Table(title="Mission Task Checklist")
    table.add_column("ID", style="dim", width=4)
    table.add_column("Task Title", style="bold", width=45)
    table.add_column("Agent", style="cyan", width=20)
    table.add_column("Status", style="magenta", width=15)

    status_icons = {
        "planned": "[dim]Planned[/]",
        "approved": "[magenta]Approved[/]",
        "queued": "[cyan]Queued[/]",
        "preparing": "[blue]Preparing[/]",
        "awaiting_approval": "[yellow]! Needs Approval[/]",
        "running": "[yellow]▶ Running[/]",
        "validating": "[green]Validating[/]",
        "reviewing": "[magenta]Reviewing[/]",
        "merging": "[blue]Merging[/]",
        "blocked": "[red]✖ Blocked[/]",
        "needs_human": "[bold yellow]? Needs Human[/]",
        "retry_ready": "[cyan]Retry Ready[/]",
        "completed": "[green]✓ Completed[/]",
        "failed": "[red]✗ Failed[/]",
        "skipped": "[dim]Skipped[/]",
        "cancelled": "[dim]Cancelled[/]",
        "rolled_back": "[yellow]Rolled Back[/]",
    }

    for task in plan_data.get("tasks", []):
        t_status = task.get("status", "planned")
        icon = status_icons.get(t_status, t_status)
        table.add_row(
            task.get("id", ""), task.get("title", ""), task.get("agent", ""), icon
        )

    console.print(table)
