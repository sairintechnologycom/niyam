"""Niyam CLI identity commands."""

from __future__ import annotations

import typer
from rich.panel import Panel
from rich.table import Table

from niyam.cli import console, identity_app
from niyam.core.identity import ensure_identity, get_identity_key_path


@identity_app.command("show")
def identity_show() -> None:
    """Display the current local identity status."""
    key_path = get_identity_key_path()
    
    table = Table(title="Niyam Local Identity", box=None)
    table.add_column("Property", style="bold cyan")
    table.add_column("Value")
    
    if key_path.exists():
        table.add_row("Status", "[bold green]Active[/]")
        table.add_row("Key Path", str(key_path))
        # Don't show the full key for safety
        key = key_path.read_text(encoding="utf-8").strip()
        table.add_row("Key Fingerprint", f"sha256:{key[:8]}...")
    else:
        table.add_row("Status", "[bold yellow]Not Initialized[/]")
        table.add_row("Action", "Run `niyam identity init` to create a new key.")
        
    console.print(Panel(table, border_style="blue"))


@identity_app.command("init")
def identity_init(
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing identity key.")
) -> None:
    """Initialize or rotate the local identity key."""
    key_path = get_identity_key_path()
    
    if key_path.exists() and not force:
        console.print(f"[bold yellow]Identity already exists at:[/] {key_path}")
        console.print("Use [bold]--force[/] if you want to rotate/overwrite it.")
        raise SystemExit(1)
        
    if key_path.exists() and force:
        import os
        key_path.unlink()
        
    key = ensure_identity()
    console.print(f"[bold green]✓[/] Identity key generated successfully.")
    console.print(f"  - [dim]Location:[/] {key_path}")
    console.print("This key will be used to sign all future evidence reports.")
