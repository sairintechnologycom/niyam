"""Sutra CLI pack commands."""

from __future__ import annotations

from typing import Annotated

import typer
from rich.table import Table

from sutra.cli import console, pack_app


@pack_app.command("list")
def pack_list() -> None:
    """Show available and installed packs."""
    from sutra.core.config import find_sutra_root
    from sutra.core.errors import SutraConfigError
    from sutra.core.packs import list_packs

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
    force: Annotated[
        bool, typer.Option("--force", help="Overwrite existing files.")
    ] = False,
) -> None:
    """Install a pack into the workspace."""
    from sutra.core.config import find_sutra_root
    from sutra.core.errors import SutraConfigError
    from sutra.core.packs import add_pack
    from sutra.core.sync import run_sync

    try:
        root = find_sutra_root()
        if not root:
            raise SutraConfigError("Not a Sutra workspace. Run 'sutra init' first.")
        add_pack(root, name, force=force, console=console)
        console.print(
            f"[bold green]✓[/] Pack '[cyan]{name}[/]' successfully installed."
        )
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
    from sutra.core.config import find_sutra_root
    from sutra.core.errors import SutraConfigError
    from sutra.core.packs import remove_pack
    from sutra.core.sync import run_sync

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
    from sutra.core.config import find_sutra_root
    from sutra.core.errors import SutraConfigError
    from sutra.core.packs import sync_packs
    from sutra.core.sync import run_sync

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
