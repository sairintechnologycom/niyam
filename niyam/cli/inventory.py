"""CLI commands for model, prompt, and data inventory."""

from __future__ import annotations

from typing import Annotated, Optional

import typer
from rich.panel import Panel
from rich.table import Table

from niyam.cli import console, inventory_app
from niyam.core.graph import parse_object_ref
from niyam.core.inventory import load_inventory, register_inventory_object


INVENTORY_TYPES = {
    "model",
    "prompt",
    "dataset",
    "vector-store",
    "knowledge-base",
}


@inventory_app.command("register")
def inventory_register(
    object_type: Annotated[str, typer.Argument(help="Inventory object type.")],
    object_id: Annotated[str, typer.Argument(help="Stable object ID.")],
    name: Annotated[Optional[str], typer.Option("--name")] = None,
    version: Annotated[Optional[str], typer.Option("--version")] = None,
    owner: Annotated[Optional[str], typer.Option("--owner")] = None,
    location: Annotated[Optional[str], typer.Option("--location")] = None,
    description: Annotated[Optional[str], typer.Option("--description")] = None,
    tags: Annotated[Optional[str], typer.Option("--tags")] = None,
    application: Annotated[Optional[str], typer.Option("--application")] = None,
    update: Annotated[bool, typer.Option("--update")] = False,
) -> None:
    """Register or update a versioned inventory object."""
    if object_type not in INVENTORY_TYPES:
        console.print(f"[bold red]Error:[/] Invalid inventory type '{object_type}'.")
        raise typer.Exit(1)
    try:
        record = register_inventory_object(
            object_type,  # type: ignore[arg-type]
            object_id,
            name=name,
            version=version,
            owner=owner,
            location=location,
            description=description,
            tags=[value.strip() for value in tags.split(",") if value.strip()]
            if tags is not None
            else None,
            application_id=application,
            update=update,
        )
    except ValueError as exc:
        console.print(f"[bold red]Error:[/] {exc}")
        raise typer.Exit(1)
    console.print(
        f"[bold green]✓[/] Registered {record.object_type}:{record.object_id}"
    )


@inventory_app.command("list")
def inventory_list(
    object_type: Annotated[
        Optional[str], typer.Option("--type", help="Filter by object type.")
    ] = None,
) -> None:
    """List inventory objects."""
    if object_type is not None and object_type not in INVENTORY_TYPES:
        console.print(f"[bold red]Error:[/] Invalid inventory type '{object_type}'.")
        raise typer.Exit(1)
    records = [
        record
        for record in load_inventory().objects.values()
        if object_type is None or record.object_type == object_type
    ]
    if not records:
        console.print("[yellow]No inventory objects found.[/]")
        return
    table = Table(title="AI Inventory")
    for heading in ("Type", "ID", "Name", "Version", "Owner"):
        table.add_column(heading)
    for record in records:
        table.add_row(
            record.object_type,
            record.object_id,
            record.name,
            record.version,
            record.owner or "",
        )
    console.print(table)


@inventory_app.command("show")
def inventory_show(
    object_ref: Annotated[str, typer.Argument(help="Object as TYPE:ID.")],
) -> None:
    """Show one inventory object."""
    try:
        object_type, object_id = parse_object_ref(object_ref)
    except ValueError as exc:
        console.print(f"[bold red]Error:[/] {exc}")
        raise typer.Exit(1)
    record = load_inventory().objects.get(f"{object_type}:{object_id}")
    if record is None:
        console.print(f"[bold red]Error:[/] Inventory object '{object_ref}' not found.")
        raise typer.Exit(1)
    console.print(
        Panel(
            "\n".join(
                [
                    f"Name: {record.name}",
                    f"Version: {record.version}",
                    f"Owner: {record.owner or '-'}",
                    f"Location: {record.location or '-'}",
                    f"Tags: {', '.join(record.tags) or '-'}",
                    f"Description: {record.description or '-'}",
                ]
            ),
            title=f"[bold cyan]{object_ref}[/]",
        )
    )
