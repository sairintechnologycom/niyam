"""CLI commands for AI agent skill governance."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table
from pathlib import Path
from typing import Optional

from niyam.cli import console, skills_app
from niyam.core.skills import (
    load_skill_registry,
    register_skill,
    skill_registry_lock,
    save_skill_registry,
)

@skills_app.command(name="list")
def list_skills() -> None:
    """List all registered agent skills and their governance status."""
    registry = load_skill_registry()
    
    if not registry.skills:
        console.print("[yellow]No skills registered in the governance registry.[/]")
        return

    table = Table(title="Agent Skill Governance Registry")
    table.add_column("Skill Name", style="cyan")
    table.add_column("Version", style="magenta")
    table.add_column("Risk Level", style="bold")
    table.add_column("Approved", style="green")
    table.add_column("Registered At", style="dim")

    for name, skill in sorted(registry.skills.items()):
        risk_style = "green"
        if skill.risk_level == "critical":
            risk_style = "bold red"
        elif skill.risk_level == "high":
            risk_style = "red"
        elif skill.risk_level == "medium":
            risk_style = "yellow"
            
        approved_str = "[green]Yes[/]" if skill.approved else "[red]No (PENDING)[/]"
        
        table.add_row(
            name,
            skill.manifest.version,
            f"[{risk_style}]{skill.risk_level.upper()}[/]",
            approved_str,
            skill.registered_at[:10],
        )

    console.print(table)


@skills_app.command(name="register")
def register(
    path: Path = typer.Argument(..., help="Path to the skill directory or SKILL.md file."),
    approved: bool = typer.Option(False, "--approved", help="Explicitly approve the skill during registration."),
) -> None:
    """Register a skill for governance oversight."""
    skill_file = path
    if path.is_dir():
        skill_file = path / "SKILL.md"
        
    if not skill_file.exists():
        console.print(f"[bold red]Error:[/] Skill file not found at {skill_file}")
        raise typer.Exit(1)

    try:
        skill = register_skill(skill_file, approved=approved)
        console.print(f"[green]Successfully registered skill:[/] [cyan]{skill.manifest.name}[/]")
        console.print(f"  Risk Level: {skill.risk_level.upper()}")
        console.print(f"  Approved: {'Yes' if skill.approved else 'No (Requires operator approval)'}")
    except Exception as e:
        console.print(f"[bold red]Error:[/] Failed to register skill: {e}")
        raise typer.Exit(1)


@skills_app.command(name="approve")
def approve_skill(
    name: str = typer.Argument(..., help="Name of the skill to approve.")
) -> None:
    """Approve a high-risk skill for use."""
    with skill_registry_lock():
        registry = load_skill_registry()
        if name not in registry.skills:
            console.print(f"[bold red]Error:[/] Skill '{name}' not found in registry.")
            raise typer.Exit(1)
            
        registry.skills[name].approved = True
        save_skill_registry(registry, locked=True)
        console.print(f"[green]Skill '{name}' has been approved.[/]")


@skills_app.command(name="check")
def check_skill(
    path: Path = typer.Argument(..., help="Path to the skill directory or SKILL.md file.")
) -> None:
    """Check a skill against the registry and report governance status."""
    from niyam.core.skills import parse_skill_file
    
    skill_file = path
    if path.is_dir():
        skill_file = path / "SKILL.md"
        
    if not skill_file.exists():
        console.print(f"[bold red]Error:[/] Skill file not found at {skill_file}")
        raise typer.Exit(1)

    manifest, checksum, prompt = parse_skill_file(skill_file)
    registry = load_skill_registry()
    
    if manifest.name not in registry.skills:
        console.print(f"[yellow]Skill '{manifest.name}' is not registered.[/]")
        console.print("Run [cyan]niyam skills register[/] to register it.")
        raise typer.Exit(1)
        
    registered = registry.skills[manifest.name]
    
    console.print(f"Skill: [cyan]{manifest.name}[/]")
    if registered.checksum != checksum:
        console.print("[bold red]WARNING: Skill content has changed since registration![/]")
        console.print(f"  Registered Checksum: {registered.checksum[:12]}...")
        console.print(f"  Current Checksum:    {checksum[:12]}...")
    else:
        console.print("[green]Integrity: Verified (Matches registry)[/]")
        
    if not registered.approved:
        console.print("[bold red]Status: UNAPPROVED[/]")
    else:
        console.print("[green]Status: Approved[/]")
