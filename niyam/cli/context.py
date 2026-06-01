"""Niyam CLI context commands."""

from __future__ import annotations

from typing import Annotated

import typer

from niyam.cli import console, context_app


@context_app.command("refresh")
def context_refresh(
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Preview changes without writing."),
    ] = False,
) -> None:
    """Scan the repo and update project context."""
    if dry_run:
        from niyam.core.context import run_context_diff

        run_context_diff(console=console)
    else:
        from niyam.core.context import run_context_refresh

        run_context_refresh(console=console)


@context_app.command("show")
def context_show() -> None:
    """Display current project context."""
    from niyam.core.context import run_context_show

    run_context_show(console=console)


@context_app.command("diff")
def context_diff() -> None:
    """Show changes since last context refresh."""
    from niyam.core.context import run_context_diff

    run_context_diff(console=console)
