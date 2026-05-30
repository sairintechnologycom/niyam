"""Sutra CLI guard commands."""

from __future__ import annotations

from typing import Annotated

import typer

from sutra.cli import console, guard_app


@guard_app.command("enable")
def guard_enable() -> None:
    """Enable all configured guardrails."""
    from sutra.policies.guard import run_guard_enable

    run_guard_enable(console=console)


@guard_app.command("disable")
def guard_disable() -> None:
    """Disable all guardrails."""
    from sutra.policies.guard import run_guard_disable

    run_guard_disable(console=console)


@guard_app.command("careful")
def guard_careful() -> None:
    """Enable destructive-command warnings."""
    from sutra.policies.guard import run_guard_careful

    run_guard_careful(console=console)


@guard_app.command("freeze")
def guard_freeze(
    path: Annotated[
        str,
        typer.Argument(help="Path to restrict edits to."),
    ],
) -> None:
    """Restrict AI edits to a specific directory."""
    from sutra.policies.guard import run_guard_freeze

    run_guard_freeze(path=path, console=console)
