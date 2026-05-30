"""Sutra CLI context commands."""

from __future__ import annotations

from sutra.cli import console, context_app


@context_app.command("refresh")
def context_refresh() -> None:
    """Scan the repo and update project context."""
    from sutra.core.context import run_context_refresh

    run_context_refresh(console=console)


@context_app.command("show")
def context_show() -> None:
    """Display current project context."""
    from sutra.core.context import run_context_show

    run_context_show(console=console)


@context_app.command("diff")
def context_diff() -> None:
    """Show changes since last context refresh."""
    from sutra.core.context import run_context_diff

    run_context_diff(console=console)
