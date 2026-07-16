"""CLI commands for local architecture inventory."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.table import Table

from niyam.cli import architecture_app, console
from niyam.core.architecture import (
    build_architecture_inventory,
    load_architecture_inventory,
    save_architecture_inventory,
)


@architecture_app.command("scan")
def architecture_scan(
    path: Annotated[Path, typer.Argument(help="Repository path to analyze.")] = Path(
        "."
    ),
) -> None:
    """Build and persist a source-linked architecture inventory."""
    if not path.is_dir():
        console.print(f"[bold red]Error:[/] Directory not found: {path}")
        raise typer.Exit(1)
    path = path.resolve()
    inventory = build_architecture_inventory(path)
    output = save_architecture_inventory(inventory, path)
    console.print(f"[bold green]✓[/] Architecture inventory saved to {output}")


@architecture_app.command("show")
def architecture_show() -> None:
    """Show the latest architecture inventory."""
    try:
        inventory = load_architecture_inventory()
    except FileNotFoundError as exc:
        console.print(f"[bold red]Error:[/] {exc}")
        raise typer.Exit(1)

    table = Table(title="Local Architecture Inventory")
    table.add_column("Kind", style="cyan")
    table.add_column("Name")
    table.add_column("Source", style="dim")
    for kind, items in (
        ("Service", inventory.services),
        ("External", inventory.external_calls),
        ("Identity", inventory.identity_boundaries),
        ("Storage", inventory.storage),
    ):
        for item in items:
            table.add_row(kind, item.name, f"{item.file_path}:{item.line}")
    for flow in inventory.data_flows:
        table.add_row(
            "Data flow",
            f"{flow.function}: {', '.join(flow.sources)} -> {', '.join(flow.sinks)}",
            f"{flow.file_path}:{flow.line}",
        )
    console.print(table)
