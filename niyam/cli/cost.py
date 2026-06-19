"""Niyam CLI cost tracking commands."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Optional

import typer

from niyam.cli import console, cost_app
from niyam.core.config import find_niyam_root


@cost_app.command("log")
def cost_log(
    tool: Annotated[
        str, typer.Option("--tool", help="Name of the AI tool used.")
    ] = "unknown",
    model: Annotated[
        str, typer.Option("--model", help="Name of the AI model.")
    ] = "unknown",
    input_tokens: Annotated[
        int, typer.Option("--input-tokens", help="Number of input tokens.")
    ] = 0,
    output_tokens: Annotated[
        int, typer.Option("--output-tokens", help="Number of output tokens.")
    ] = 0,
    task: Annotated[
        Optional[str], typer.Option("--task", help="Task name or ID.")
    ] = None,
    status: Annotated[
        str, typer.Option("--status", help="Execution status: success/failed/repeated.")
    ] = "success",
    notes: Annotated[
        Optional[str], typer.Option("--notes", help="Additional notes.")
    ] = None,
) -> None:
    """Log an AI cost and token usage event."""
    from niyam.core.cost import (
        calculate_cost,
        get_branch_name,
        get_repo_name,
        load_pricing,
        log_cost_event,
        CostEvent,
    )

    root = find_niyam_root() or Path.cwd()

    if input_tokens < 0 or output_tokens < 0:
        console.print("[bold red]Error:[/] Token counts must be non-negative.")
        raise typer.Exit(1)

    pricing = load_pricing(root)
    estimated_cost = calculate_cost(model, input_tokens, output_tokens, pricing)

    # Session ID calculation
    session_id = (
        os.environ.get("NIYAM_SESSION_ID") or get_branch_name(root) or "default-session"
    )

    # Task ID calculation
    task_id = task or os.environ.get("NIYAM_TASK_ID") or "default-task"

    event = CostEvent(
        timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        session_id=session_id,
        task_id=task_id,
        tool_name=tool,
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        estimated_cost=estimated_cost,
        repo=get_repo_name(root),
        branch=get_branch_name(root),
        status=status,
        notes=notes,
    )

    log_cost_event(event, root)

    console.print(
        f"[bold green]✓[/] Logged AI session usage: [bold cyan]{model}[/] "
        f"([dim]{input_tokens} In / {output_tokens} Out[/]) -> [bold green]${estimated_cost:.4f}[/]"
    )


@cost_app.command("summary")
def cost_summary() -> None:
    """Display a high-level summary of AI cost and token usage."""
    from niyam.core.cost import generate_cost_metrics, load_cost_events
    from rich.panel import Panel
    from rich.table import Table

    root = find_niyam_root() or Path.cwd()
    events = load_cost_events(root)

    if not events:
        console.print("[yellow]No logged cost events found.[/]")
        return

    metrics = generate_cost_metrics(events)

    summary_text = (
        f"Total Logged Events: [bold cyan]{len(events)}[/]\n"
        f"Total Estimated Cost: [bold green]${metrics['total_cost']:.4f}[/]\n"
        f"Total Input Tokens: [bold]{metrics['total_input_tokens']:,}[/]\n"
        f"Total Output Tokens: [bold]{metrics['total_output_tokens']:,}[/]\n"
    )

    console.print(
        Panel(
            summary_text,
            title="[bold]Niyam AI Cost Summary[/]",
            border_style="green",
        )
    )

    # Grouped mini-tables
    table = Table(box=None, padding=(0, 2))
    table.add_column("By Category", style="dim")
    table.add_column("Top Entry", style="cyan")
    table.add_column("Cost", justify="right", style="green")

    if metrics["by_day"]:
        top_day = max(metrics["by_day"].items(), key=lambda x: x[1])
        table.add_row("Day", top_day[0], f"${top_day[1]:.2f}")
    
    if metrics["by_repo"]:
        top_repo = max(metrics["by_repo"].items(), key=lambda x: x[1])
        table.add_row("Repo", top_repo[0], f"${top_repo[1]:.2f}")

    if metrics["by_task"]:
        top_task = max(metrics["by_task"].items(), key=lambda x: x[1])
        table.add_row("Task", top_task[0], f"${top_task[1]:.2f}")

    console.print(table)


@cost_app.command("report")
def cost_report() -> None:
    """Display detailed cost reports categorized by day, repository, task, and status."""
    from niyam.core.cost import generate_cost_metrics, load_cost_events
    from rich.panel import Panel
    from rich.table import Table

    root = find_niyam_root() or Path.cwd()
    events = load_cost_events(root)

    if not events:
        console.print("[yellow]No logged cost events found to report.[/]")
        return

    metrics = generate_cost_metrics(events)

    # 1. Total estimated cost by day
    day_table = Table(title="Cost by Day")
    day_table.add_column("Day", style="cyan")
    day_table.add_column("Cost", justify="right", style="green")

    for day, cost in sorted(metrics["by_day"].items()):
        day_table.add_row(day, f"${cost:.4f}")

    # 2. Total estimated cost by repo
    repo_table = Table(title="Cost by Repository")
    repo_table.add_column("Repository", style="cyan")
    repo_table.add_column("Cost", justify="right", style="green")

    for repo, cost in sorted(metrics["by_repo"].items()):
        repo_table.add_row(repo, f"${cost:.4f}")

    # 3. Total estimated cost by task
    task_table = Table(title="Cost by Task")
    task_table.add_column("Task ID", style="cyan")
    task_table.add_column("Cost", justify="right", style="green")

    for task, cost in sorted(metrics["by_task"].items()):
        task_table.add_row(task, f"${cost:.4f}")

    # 4. Total estimated cost by tool (Wastage Focus)
    tool_table = Table(title="Wastage Analysis by Tool")
    tool_table.add_column("Tool", style="cyan")
    tool_table.add_column("Total Cost", justify="right", style="dim")
    tool_table.add_column("Wasted (Fail/Repeat)", justify="right", style="red")

    for tool, cost in sorted(metrics["by_tool"].items()):
        wasted = metrics["wastage_by_tool"].get(tool, 0.0)
        tool_table.add_row(tool, f"${cost:.4f}", f"${wasted:.4f}")

    # 4. Top expensive sessions
    session_table = Table(title="Top Expensive Sessions")
    session_table.add_column("Session ID", style="cyan")
    session_table.add_column("Cost", justify="right", style="green")

    # Sort descending and display
    sorted_sessions = sorted(
        metrics["by_session"].items(), key=lambda x: x[1], reverse=True
    )
    for session, cost in sorted_sessions[:5]:
        session_table.add_row(session, f"${cost:.4f}")

    # 5. Failed/repeated task cost summary
    failed_cost = metrics["failed_repeated_cost"]
    failed_count = metrics["failed_repeated_count"]
    success_cost = metrics["success_cost"]
    success_count = metrics["success_count"]

    status_text = (
        f"Successful Tasks: [bold green]{success_count}[/] (Cost: [green]${success_cost:.4f}[/])\n"
        f"Failed/Repeated Tasks: [bold red]{failed_count}[/] (Cost: [red]${failed_cost:.4f}[/])"
    )
    status_panel = Panel(
        status_text,
        title="Failed/Repeated Task Cost Summary (Wasted Budget)",
        border_style="red" if failed_cost > 0 else "green",
    )

    console.print(day_table)
    console.print()
    console.print(repo_table)
    console.print()
    console.print(task_table)
    console.print()
    console.print(tool_table)
    console.print()
    console.print(session_table)
    console.print()
    console.print(status_panel)


@cost_app.command("pricing")
def cost_pricing(
    update: Annotated[bool, typer.Option("--update", help="Update local pricing from remote URL.")] = False,
    show: Annotated[bool, typer.Option("--show", help="Show current pricing table.")] = True,
) -> None:
    """View or update AI model pricing configuration."""
    from niyam.core.cost import load_pricing, get_pricing_path
    from rich.table import Table

    root = find_niyam_root() or Path.cwd()
    
    if update:
        # Check if remote URL is configured first to provide clear feedback
        from niyam.core.config import load_niyam_config
        remote_url = None
        try:
            config = load_niyam_config(root)
            remote_url = config.saas.pricing_url if config.saas else None
        except Exception:
            pass

        if not remote_url:
            console.print("[yellow]Warning: saas.pricing_url is not configured in niyam.yaml. Cannot sync remote pricing.[/]")
            pricing = load_pricing(root)
        else:
            console.print(f"Fetching remote pricing from: [cyan]{remote_url}[/]...")
            pricing = load_pricing(root)
            console.print("[green]Pricing table successfully synchronized with remote endpoint.[/]")
    else:
        pricing = load_pricing(root)

    if show:
        table = Table(title="Model Pricing Table (USD per Million Tokens)")
        table.add_column("Model", style="cyan")
        table.add_column("Input Rate", justify="right", style="green")
        table.add_column("Output Rate", justify="right", style="green")

        for model, rates in sorted(pricing.items()):
            table.add_row(
                model, 
                f"${rates.get('input_cost_per_million', 0.0):.2f}",
                f"${rates.get('output_cost_per_million', 0.0):.2f}"
            )
        console.print(table)
        
        
@cost_app.command("scorecard")
def cost_scorecard() -> None:
    """Display an agent performance scorecard with usefulness, retries, and efficiency."""
    from niyam.core.analytics import PerformanceMetrics
    from rich.table import Table
    from rich.panel import Panel

    root = find_niyam_root() or Path.cwd()
    metrics_engine = PerformanceMetrics(root)
    summary = metrics_engine.get_fleet_summary()

    if not summary or not summary.get("agent_performance"):
        console.print("[yellow]No agent performance data found. Run some missions first.[/]")
        return

    table = Table(title="Agent Performance Scorecard")
    table.add_column("Agent", style="cyan")
    table.add_column("Tasks", justify="center")
    table.add_column("Usefulness", justify="center")
    table.add_column("Avg Retries", justify="center")
    table.add_column("Val Fails", justify="center")
    table.add_column("Cost (USD)", justify="right", style="green")
    table.add_column("Cost / Success", justify="right", style="bold green")

    for agent, stats in sorted(summary["agent_performance"].items(), key=lambda x: x[1]["success_rate"], reverse=True):
        usefulness = stats["success_rate"]
        u_color = "green" if usefulness >= 80 else "yellow" if usefulness >= 50 else "red"
        
        avg_retries = stats["avg_retries"]
        r_color = "green" if avg_retries < 0.2 else "yellow" if avg_retries < 0.5 else "red"

        table.add_row(
            agent,
            f"{stats['completed']}/{stats['tasks']}",
            f"[{u_color}]{usefulness:.1f}%[/]",
            f"[{r_color}]{avg_retries:.2f}[/]",
            str(stats["val_fails"]),
            f"${stats['cost']:.2f}",
            f"${stats['cost_per_success']:.4f}"
        )

    console.print(table)

    # Fleet summary
    avg_success = summary["avg_success_rate"]
    total_cost = summary["total_cost_usd"]
    total_retries = summary["total_retries"]
    
    summary_text = (
        f"Total Missions: [bold]{summary['total_missions']}[/]\n"
        f"Avg Fleet Success Rate: [bold green]{avg_success:.1f}%[/]\n"
        f"Total Fleet Cost: [bold green]${total_cost:.2f}[/]\n"
        f"Total Retries/Heals: [bold yellow]{total_retries}[/]"
    )
    console.print(Panel(summary_text, title="Fleet Efficiency Summary", border_style="cyan"))
