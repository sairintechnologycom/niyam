"""Niyam CLI runtime commands."""

from __future__ import annotations

from typing import Annotated

import typer

from niyam.cli import console, runtime_app
from niyam.cli.main_cmds import Runtime


@runtime_app.command("add")
def runtime_add(
    runtime: Annotated[
        Runtime,
        typer.Argument(help="Runtime to add."),
    ],
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Preview changes without writing."),
    ] = False,
) -> None:
    """Add and configure a new AI runtime."""
    from niyam.core.sync import run_runtime_add

    run_runtime_add(runtime=runtime.value, console=console, dry_run=dry_run)
