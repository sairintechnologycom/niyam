"""Niyam CLI identity commands."""

from __future__ import annotations

import hashlib
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
        # Use hashlib for fingerprint
        content = key_path.read_bytes()
        fp = hashlib.sha256(content).hexdigest()
        table.add_row("Key Fingerprint", f"sha256:{fp[:12]}...")
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


@identity_app.command("public-key")
def identity_public_key() -> None:
    """Export the local identity public key in PEM format."""
    from niyam.core.identity import get_public_key_bytes
    
    try:
        pub_key = get_public_key_bytes()
        console.print("[bold cyan]Niyam Public Key (PEM):[/]\n")
        console.print(pub_key.decode("utf-8"))
        console.print("\n[dim]Configure this key in your CI/CD pipeline (NIYAM_PUBLIC_KEY) to verify evidence reports.[/]")
    except Exception as e:
        console.print(f"[bold red]Error:[/] {e}")
        raise SystemExit(1)
