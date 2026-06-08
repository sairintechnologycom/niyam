"""Niyam CLI context commands."""

from __future__ import annotations

import os
import sys
from typing import Annotated, Optional

import typer
from rich.console import Console

from niyam.cli import console, context_app


def is_interactive() -> bool:
    """Return True when the CLI can safely prompt or show live terminal UI."""
    return sys.stdout.isatty() and sys.stdin.isatty() and not os.getenv("CI")


def rich_console() -> Console:
    """Return a console configured for the current environment."""
    return Console(no_color=not is_interactive())


def prompt_text(message: str, default: str) -> str:
    """Prompt for text when interactive, with a no-dependency fallback."""
    if not is_interactive():
        return default

    try:
        import questionary

        answer = questionary.text(message, default=default).ask()
        return answer or default
    except Exception:
        return typer.prompt(message, default=default)


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


@context_app.command("add")
def context_add(
    text: Annotated[
        Optional[str],
        typer.Argument(
            help="Inline text content for the context document (PRD, overview, etc.).",
        ),
    ] = None,
    context_type: Annotated[
        str,
        typer.Option(
            "--type",
            "-t",
            help="Context document type: prd, overview, user-stories, tech-spec, custom.",
        ),
    ] = "prd",
    file: Annotated[
        Optional[str],
        typer.Option(
            "--file",
            "-f",
            help="Path to a file to import as context.",
        ),
    ] = None,
    stdin: Annotated[
        bool,
        typer.Option(
            "--stdin",
            help="Read context content from stdin (for piping).",
        ),
    ] = False,
    name: Annotated[
        Optional[str],
        typer.Option(
            "--name",
            "-n",
            help="Custom name for the context document.",
        ),
    ] = None,
) -> None:
    """Add a project context document (PRD, user stories, tech spec, etc.).

    Provide content via inline text, --file, or --stdin. Examples:

        niyam context add --type prd "Build a todo app with auth"
        niyam context add --type prd --file ./docs/PRD.md
        echo "Build X" | niyam context add --type prd --stdin
        niyam context add --type user-stories --file ./stories.md
    """
    from niyam.core.context import run_context_add
    from niyam.core.sync import run_sync

    run_context_add(
        context_type=context_type,
        text=text,
        file_path=file,
        from_stdin=stdin,
        name=name,
        console=console,
    )
    # Sync to runtimes so context is available
    try:
        run_sync(runtime=None, console=console)
    except SystemExit:
        pass  # Not fatal if sync fails (e.g. no runtimes configured)


@context_app.command("list")
def context_list() -> None:
    """List all manually-added context documents."""
    from niyam.core.context import run_context_list

    run_context_list(console=console)


@context_app.command("remove")
def context_remove(
    identifier: Annotated[
        str,
        typer.Argument(
            help="Filename or type-name identifier of the context document to remove (e.g. prd-main).",
        ),
    ],
) -> None:
    """Remove a context document by name or identifier."""
    from niyam.core.context import run_context_remove
    from niyam.core.sync import run_sync

    run_context_remove(identifier=identifier, console=console)
    try:
        run_sync(runtime=None, console=console)
    except SystemExit:
        pass
