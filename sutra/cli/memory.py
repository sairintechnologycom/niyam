"""Sutra CLI memory commands."""

from __future__ import annotations

from typing import Annotated

import typer

from sutra.cli import console, memory_app


@memory_app.command("show")
def memory_show() -> None:
    """Display all memory files and their content."""
    from sutra.core.memory import run_memory_show

    run_memory_show(console=console)


@memory_app.command("add")
def memory_add(
    file: Annotated[
        str,
        typer.Argument(help="Memory file to append to (e.g. project-lessons)."),
    ],
    note: Annotated[str, typer.Argument(help="Note to append.")],
) -> None:
    """Append a note to a memory file."""
    from sutra.core.memory import run_memory_add
    from sutra.core.sync import run_sync

    run_memory_add(file=file, note=note, console=console)
    run_sync(runtime=None, console=console)


@memory_app.command("clear")
def memory_clear(
    file: Annotated[str, typer.Argument(help="Memory file to clear.")],
) -> None:
    """Clear a memory file, resetting it to its title/headers."""
    from sutra.core.memory import run_memory_clear
    from sutra.core.sync import run_sync

    run_memory_clear(file=file, console=console)
    run_sync(runtime=None, console=console)
