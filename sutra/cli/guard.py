"""Sutra CLI guard commands."""

from __future__ import annotations

from typing import Annotated

import typer

from sutra.cli import console, guard_app


@guard_app.command("enable")
def guard_enable(
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Preview changes without writing."),
    ] = False,
) -> None:
    """Enable all configured guardrails."""
    from sutra.policies.guard import run_guard_enable

    run_guard_enable(console=console, dry_run=dry_run)


@guard_app.command("disable")
def guard_disable(
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Preview changes without writing."),
    ] = False,
) -> None:
    """Disable all guardrails."""
    from sutra.policies.guard import run_guard_disable

    run_guard_disable(console=console, dry_run=dry_run)


@guard_app.command("careful")
def guard_careful(
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Preview changes without writing."),
    ] = False,
) -> None:
    """Enable destructive-command warnings."""
    from sutra.policies.guard import run_guard_careful

    run_guard_careful(console=console, dry_run=dry_run)


@guard_app.command("freeze")
def guard_freeze(
    path: Annotated[
        str,
        typer.Argument(help="Path to restrict edits to."),
    ],
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Preview changes without writing."),
    ] = False,
) -> None:
    """Restrict AI edits to a specific directory."""
    from sutra.policies.guard import run_guard_freeze

    run_guard_freeze(path=path, console=console, dry_run=dry_run)
