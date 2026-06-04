"""Niyam CLI guard commands."""

from __future__ import annotations

from typing import Annotated, Optional

import typer

from niyam.cli import console, guard_app


@guard_app.command("enable")
def guard_enable(
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Preview changes without writing."),
    ] = False,
) -> None:
    """Enable all configured guardrails."""
    from niyam.policies.guard import run_guard_enable

    run_guard_enable(console=console, dry_run=dry_run)


@guard_app.command("disable")
def guard_disable(
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Preview changes without writing."),
    ] = False,
) -> None:
    """Disable all guardrails."""
    from niyam.policies.guard import run_guard_disable

    run_guard_disable(console=console, dry_run=dry_run)


@guard_app.command("careful")
def guard_careful(
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Preview changes without writing."),
    ] = False,
) -> None:
    """Enable destructive-command warnings."""
    from niyam.policies.guard import run_guard_careful

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
    from niyam.policies.guard import run_guard_freeze

    run_guard_freeze(path=path, console=console, dry_run=dry_run)


@guard_app.command(
    "run",
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)
def guard_run(
    ctx: typer.Context,
    capture_output: Annotated[
        bool,
        typer.Option(
            "--capture-output", help="Capture command stdout/stderr output in logs."
        ),
    ] = False,
    mode: Annotated[
        Optional[str],
        typer.Option(
            "--mode", help="Guard mode: observe, block, warn, approve."
        ),
    ] = None,
) -> None:
    """Run a shell command under Niyam guard observation."""
    from niyam.policies.guard import run_guard_run

    run_guard_run(
        cmd_args=ctx.args,
        capture_output=capture_output,
        console=console,
        mode_override=mode,
    )


@guard_app.command("status")
def guard_status() -> None:
    """Display the current Niyam guard configuration and observation metrics."""
    from niyam.policies.guard import run_guard_status_metrics

    run_guard_status_metrics(console=console)


@guard_app.command("logs")
def guard_logs(
    limit: Annotated[
        int,
        typer.Option("--limit", "-l", help="Number of logs to display."),
    ] = 10,
) -> None:
    """Show recent observed actions logged by Niyam guard."""
    from niyam.policies.guard import run_guard_show_logs

    run_guard_show_logs(limit=limit, console=console)
