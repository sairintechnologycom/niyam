"""Niyam CLI CI commands."""

from __future__ import annotations

from typing import Annotated, Optional

import typer

from niyam.cli import console, ci_app


@ci_app.command("verify")
def ci_verify(
    target: Annotated[
        str,
        typer.Option(
            "--target",
            "-t",
            help="Target branch to compare changes against.",
        ),
    ] = "main",
    strict: Annotated[
        bool,
        typer.Option(
            "--strict/--no-strict",
            help="Fail build on integrity warnings or missing evidence.",
        ),
    ] = True,
    min_score: Annotated[
        int,
        typer.Option(
            "--min-score",
            help="Minimum readiness score required to pass.",
        ),
    ] = 50,
    public_key: Annotated[
        Optional[str],
        typer.Option(
            "--public-key",
            help="Public key PEM string for evidence verification.",
        ),
    ] = None,
) -> None:
    """Verify cryptographic integrity, guardrails, and validation status for CI/CD."""
    from niyam.core.ci import run_ci_verify

    try:
        run_ci_verify(
            target_branch=target, 
            strict=strict, 
            min_score=min_score,
            console=console,
            public_key_pem=public_key
        )
    except Exception as e:
        console.print(f"[bold red]Error:[/] {e}")
        raise typer.Exit(1)


@ci_app.command("generate")
def ci_generate(
    provider: Annotated[
        str,
        typer.Argument(
            help="CI/CD provider to generate templates for (github, azure, gitlab).",
        ),
    ],
) -> None:
    """Generate CI/CD pipeline configuration files for Niyam governance."""
    from niyam.core.config import find_niyam_root
    from niyam.core.ci_generators import generate_ci_integration

    repo_root = find_niyam_root()
    if not repo_root:
        console.print("[bold red]Error:[/] Not a Niyam workspace. Run 'niyam init' first.")
        raise typer.Exit(1)

    try:
        success = generate_ci_integration(provider, repo_root, console)
        if not success:
            raise typer.Exit(1)
    except Exception as e:
        console.print(f"[bold red]Error:[/] {e}")
        raise typer.Exit(1)
