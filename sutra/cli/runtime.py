"""Sutra CLI runtime commands."""

from __future__ import annotations

from typing import Annotated

import typer

from sutra.cli import console, runtime_app
from sutra.cli.main_cmds import Runtime


@runtime_app.command("add")
def runtime_add(
    runtime: Annotated[
        Runtime,
        typer.Argument(help="Runtime to add."),
    ],
) -> None:
    """Add and configure a new AI runtime."""
    from sutra.core.sync import run_runtime_add

    run_runtime_add(runtime=runtime.value, console=console)
