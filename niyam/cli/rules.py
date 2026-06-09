"""Niyam CLI rules commands."""

from __future__ import annotations

from typing import Annotated, Optional
from pathlib import Path

import typer
from rich.table import Table

from niyam.cli import console, rules_app


@rules_app.command("list")
def rules_list(
    profile: Annotated[
        str,
        typer.Option(
            "--profile", "-p", help="Profile to list rules for: startup, team, enterprise."
        ),
    ] = "startup",
) -> None:
    """List available scan and policy rules for a profile."""
    from niyam.core.scan import load_profile_rules

    try:
        rules = load_profile_rules(profile)
        
        table = Table(title=f"Niyam Rules: {profile.title()} Profile", box=None)
        table.add_column("ID", style="cyan")
        table.add_column("Severity")
        table.add_column("Category", style="magenta")
        table.add_column("Title")
        
        severity_styles = {
            "critical": "[bold red]CRITICAL[/]",
            "high": "[red]HIGH[/]",
            "medium": "[yellow]MEDIUM[/]",
            "low": "[green]LOW[/]",
            "info": "[blue]INFO[/]",
        }
        
        for rule in rules:
            sev_str = severity_styles.get(rule.severity, rule.severity.upper())
            table.add_row(
                rule.id,
                sev_str,
                rule.category,
                rule.title,
            )
            
        console.print(table)
        console.print(f"\n[dim]Total rules: {len(rules)}[/]")

    except Exception as e:
        console.print(f"[bold red]Error loading rules:[/] {e}")
        raise typer.Exit(1)
