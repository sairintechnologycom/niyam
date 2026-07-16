"""CLI commands for the local AI Application inventory."""

from __future__ import annotations

from typing import Annotated, Optional

import typer
from rich.panel import Panel
from rich.table import Table

from niyam.cli import applications_app, console
from niyam.core.applications import load_application_registry, register_application


@applications_app.command("register")
def applications_register(
    application_id: Annotated[str, typer.Argument(help="Stable application ID.")],
    name: Annotated[Optional[str], typer.Option("--name", help="Display name.")] = None,
    owner: Annotated[
        Optional[str], typer.Option("--owner", help="Owning team or person.")
    ] = None,
    repository: Annotated[
        Optional[str], typer.Option("--repository", help="Repository path or URL.")
    ] = None,
    description: Annotated[Optional[str], typer.Option("--description")] = None,
    status: Annotated[
        Optional[str],
        typer.Option("--status", help="prototype, production, or retired."),
    ] = None,
    tags: Annotated[
        Optional[str], typer.Option("--tags", help="Comma-separated tags.")
    ] = None,
    update: Annotated[
        bool, typer.Option("--update", help="Update an existing application.")
    ] = False,
) -> None:
    """Register or update an AI Application."""
    valid_statuses = {"prototype", "production", "retired"}
    if status is not None and status not in valid_statuses:
        console.print(f"[bold red]Error:[/] Invalid status '{status}'.")
        raise typer.Exit(1)
    try:
        application = register_application(
            application_id,
            name=name,
            owner=owner,
            repository=repository,
            description=description,
            status=status,  # type: ignore[arg-type]
            tags=[tag.strip() for tag in tags.split(",") if tag.strip()]
            if tags is not None
            else None,
            update=update,
        )
    except ValueError as exc:
        console.print(f"[bold red]Error:[/] {exc}")
        raise typer.Exit(1)
    console.print(
        f"[bold green]✓[/] Registered AI Application [bold cyan]{application.application_id}[/]"
    )


@applications_app.command("list")
def applications_list() -> None:
    """List registered AI Applications."""
    registry = load_application_registry()
    if not registry.applications:
        console.print("[yellow]No AI Applications registered yet.[/]")
        return
    table = Table(title="AI Applications")
    table.add_column("ID", style="bold cyan")
    table.add_column("Name")
    table.add_column("Owner")
    table.add_column("Status")
    table.add_column("Tags")
    for application in registry.applications.values():
        table.add_row(
            application.application_id,
            application.name,
            application.owner or "",
            application.status,
            ", ".join(application.tags),
        )
    console.print(table)


@applications_app.command("show")
def applications_show(
    application_id: Annotated[str, typer.Argument(help="Application ID.")],
) -> None:
    """Show one AI Application."""
    application = load_application_registry().applications.get(application_id)
    if application is None:
        console.print(
            f"[bold red]Error:[/] AI Application '{application_id}' not found."
        )
        raise typer.Exit(1)
    console.print(
        Panel(
            "\n".join(
                [
                    f"Name: {application.name}",
                    f"Owner: {application.owner or '-'}",
                    f"Status: {application.status}",
                    f"Repository: {application.repository or '-'}",
                    f"Tags: {', '.join(application.tags) or '-'}",
                    f"Description: {application.description or '-'}",
                ]
            ),
            title=f"[bold cyan]{application.application_id}[/]",
        )
    )
