"""CLI commands for Enterprise Policy Workflows."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import typer
import yaml
from rich.console import Console
from rich.table import Table

from niyam.cli import console, policy_app
from niyam.core.policy import (
    load_team_policy,
    load_exceptions,
    add_exception,
    PolicyException,
    get_exception_registry_path,
)

app = typer.Typer(
    name="policy",
    help="Manage enterprise governance policies and risk acceptance.",
    no_args_is_help=True,
)


@policy_app.command(name="list")
def list_policies() -> None:
    """List active team policies and rules."""
    policy = load_team_policy()
    
    if not policy:
        console.print("[yellow]No team policy found at .niyam/policies/team-policy.yaml[/]")
        return

    console.print(f"[bold cyan]Team Policy:[/] {policy.name}")
    
    # Roles Table
    if policy.roles:
        roles_table = Table(title="Defined Roles")
        roles_table.add_column("Role", style="magenta")
        roles_table.add_column("Users", style="dim")
        roles_table.add_column("Permissions", style="green")
        
        for role in policy.roles:
            roles_table.add_row(
                role.name,
                ", ".join(role.users),
                ", ".join(role.permissions),
            )
        console.print(roles_table)

    # Rules Table
    if policy.rules:
        rules_table = Table(title="Governance Rules")
        rules_table.add_column("ID", style="cyan")
        rules_table.add_column("Type", style="bold")
        rules_table.add_column("Pattern", style="yellow")
        rules_table.add_column("Exception Allowed", justify="center")
        
        for rule in policy.rules:
            rules_table.add_row(
                rule.id,
                rule.type.upper(),
                rule.pattern,
                "[green]Yes[/]" if rule.exception_allowed else "[red]No[/]",
            )
        console.print(rules_table)


@policy_app.command(name="exception-add")
def exception_add(
    pattern: str = typer.Argument(..., help="The command pattern or path to allow."),
    reason: str = typer.Option(..., "--reason", "-r", help="Reason for risk acceptance."),
    days: int = typer.Option(1, "--days", "-d", help="Number of days the exception is valid."),
    rule_id: Optional[str] = typer.Option(None, "--rule-id", help="Associated rule ID."),
) -> None:
    """Add a temporary policy exception (Risk Acceptance)."""
    import os
    
    # Get current user
    accepted_by = os.environ.get("USER", "unknown")
    
    now = datetime.now(timezone.utc)
    expires = now + timedelta(days=days)
    
    exception = PolicyException(
        id=f"EX-{uuid.uuid4().hex[:8].upper()}",
        rule_id=rule_id,
        pattern=pattern,
        accepted_by=accepted_by,
        reason=reason,
        created_at=now.isoformat(),
        expires_at=expires.isoformat(),
    )
    
    add_exception(exception)
    
    console.print(f"[bold green]✓[/] Risk Acceptance recorded: [cyan]{exception.id}[/]")
    console.print(f"  Pattern: {pattern}")
    console.print(f"  Expires: {expires.strftime('%Y-%m-%d %H:%M:%S UTC')}")


@policy_app.command(name="exception-list")
def exception_list() -> None:
    """List active policy exceptions."""
    exceptions = load_exceptions()
    
    if not exceptions:
        console.print("[yellow]No active policy exceptions found.[/]")
        return

    table = Table(title="Active Policy Exceptions (Risk Acceptance)")
    table.add_column("ID", style="cyan")
    table.add_column("Pattern", style="yellow")
    table.add_column("Accepted By", style="magenta")
    table.add_column("Reason")
    table.add_column("Expires", style="dim")

    now = datetime.now(timezone.utc)
    
    for ex in exceptions:
        is_expired = False
        if ex.expires_at:
            try:
                expires = datetime.fromisoformat(ex.expires_at)
                if expires < now:
                    is_expired = True
            except ValueError:
                pass
        
        status_style = "dim" if is_expired else "green"
        expiry_str = f"{ex.expires_at[:19]} UTC" if ex.expires_at else "Never"
        if is_expired:
            expiry_str += " [red](EXPIRED)[/]"
            
        table.add_row(
            ex.id,
            ex.pattern,
            ex.accepted_by,
            ex.reason,
            expiry_str,
        )

    console.print(table)


@policy_app.command(name="validate")
def validate() -> None:
    """Validate team-policy.yaml schema."""
    from niyam.policies.validator import validate_policies
    validate_policies()
