"""Sutra CLI review commands."""

from __future__ import annotations

from enum import Enum
from typing import Annotated, Optional

import typer

from sutra.cli import console, review_app
from sutra.cli.main_cmds import Runtime


class ReviewLens(str, Enum):
    product = "product"
    engineering = "engineering"
    design = "design"
    security = "security"


class ReviewMode(str, Enum):
    collaborative = "collaborative"
    adversarial = "adversarial"


@review_app.callback(invoke_without_command=True)
def review(
    ctx: typer.Context,
    lens: Annotated[
        ReviewLens,
        typer.Option("--lens", "-l", help="Review lens/perspective."),
    ] = ReviewLens.engineering,
    runtime: Annotated[
        Runtime,
        typer.Option("--runtime", "-r", help="Runtime to execute the review with."),
    ] = Runtime.claude,
    mode: Annotated[
        ReviewMode,
        typer.Option("--mode", "-m", help="Review mode."),
    ] = ReviewMode.collaborative,
) -> None:
    """Run a structured code review on current changes."""
    if ctx.invoked_subcommand is not None:
        return
    from sutra.core.review import run_review

    run_review(
        lens=lens.value,
        runtime=runtime.value,
        mode=mode.value,
        console=console,
    )


@review_app.command("pr")
def review_pr(
    pr: Annotated[str, typer.Argument(help="Pull Request ID.")],
    lens: Annotated[
        ReviewLens,
        typer.Option("--lens", "-l", help="Review lens/perspective."),
    ] = ReviewLens.engineering,
    runtime: Annotated[
        Runtime,
        typer.Option("--runtime", "-r", help="Runtime to execute the review with."),
    ] = Runtime.claude,
    mode: Annotated[
        ReviewMode,
        typer.Option("--mode", "-m", help="Review mode."),
    ] = ReviewMode.collaborative,
    token: Annotated[
        Optional[str],
        typer.Option(
            "--token",
            help="GitHub token (overrides GITHUB_TOKEN environment variable).",
        ),
    ] = None,
) -> None:
    """Run a structured code review on a GitHub pull request."""
    from sutra.core.pr import run_pr_review

    try:
        run_pr_review(
            pr_id=pr,
            lens=lens.value,
            runtime=runtime.value,
            mode=mode.value,
            token=token,
            console=console,
        )
    except Exception as e:
        console.print(f"[bold red]Error:[/] {e}")
        raise typer.Exit(1)
