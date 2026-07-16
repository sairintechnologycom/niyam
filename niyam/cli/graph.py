"""CLI commands for direct Niyam Graph relationships."""

from __future__ import annotations

from typing import Annotated

import typer
from rich.table import Table

from niyam.cli import console, graph_app
from niyam.core.graph import get_relationships, link_objects, parse_object_ref


@graph_app.command("link")
def graph_link(
    source: Annotated[str, typer.Argument(help="Source as TYPE:ID.")],
    relationship: Annotated[str, typer.Argument(help="Relationship name.")],
    target: Annotated[str, typer.Argument(help="Target as TYPE:ID.")],
) -> None:
    """Link two governed objects."""
    try:
        source_type, source_id = parse_object_ref(source)
        target_type, target_id = parse_object_ref(target)
        edge = link_objects(
            source_type,
            source_id,
            relationship,
            target_type,
            target_id,
        )
    except ValueError as exc:
        console.print(f"[bold red]Error:[/] {exc}")
        raise typer.Exit(1)
    console.print(
        f"[bold green]✓[/] Linked {edge.source_type}:{edge.source_id} "
        f"[cyan]{edge.relationship}[/] {edge.target_type}:{edge.target_id}"
    )


@graph_app.command("show")
def graph_show(
    object_ref: Annotated[str, typer.Argument(help="Object as TYPE:ID.")],
) -> None:
    """Show direct relationships for one object."""
    try:
        object_type, object_id = parse_object_ref(object_ref)
        edges = get_relationships(object_type, object_id)
    except ValueError as exc:
        console.print(f"[bold red]Error:[/] {exc}")
        raise typer.Exit(1)
    if not edges:
        console.print(f"[yellow]No relationships found for {object_ref}.[/]")
        return
    table = Table(title=f"Relationships for {object_ref}")
    table.add_column("Source")
    table.add_column("Relationship", style="cyan")
    table.add_column("Target")
    for edge in edges:
        table.add_row(
            f"{edge.source_type}:{edge.source_id}",
            edge.relationship,
            f"{edge.target_type}:{edge.target_id}",
        )
    console.print(table)
