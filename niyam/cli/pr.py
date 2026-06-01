"""Niyam CLI PR commands."""

from __future__ import annotations

from typing import Annotated, Optional

import typer

from niyam.cli import console, pr_app


@pr_app.command("create")
def pr_create(
    title: Annotated[str, typer.Option("--title", "-t", help="Pull Request title.")],
    body: Annotated[
        Optional[str],
        typer.Option("--body", "-b", help="Pull Request body/description."),
    ] = None,
    base: Annotated[
        str,
        typer.Option("--base", help="Target branch for the pull request."),
    ] = "main",
    token: Annotated[
        Optional[str],
        typer.Option(
            "--token",
            help="GitHub token (overrides GITHUB_TOKEN environment variable).",
        ),
    ] = None,
) -> None:
    """Push the active branch and create a GitHub pull request with evidence report attached."""
    from niyam.core.pr import run_pr_create

    try:
        run_pr_create(
            title=title,
            body=body,
            base=base,
            token=token,
            console=console,
        )
    except Exception as e:
        console.print(f"[bold red]Error:[/] {e}")
        raise typer.Exit(1)
