"""Niyam CLI evidence commands."""

from __future__ import annotations

from typing import Annotated

import typer

from niyam.cli import console, evidence_app


@evidence_app.command("generate")
def generate_evidence(
    from_scan: Annotated[
        str, typer.Option("--from", help="Path to input scan results JSON file.")
    ] = None,
    mission: Annotated[
        str, typer.Option("--mission", help="Mission ID to associate evidence with.")
    ] = None,
    format: Annotated[
        str,
        typer.Option("--format", help="Report output format: markdown, json, html."),
    ] = "markdown",
    output: Annotated[
        str,
        typer.Option("--output", "-o", help="File path to save the generated report."),
    ] = None,
    include: Annotated[
        str,
        typer.Option(
            "--include",
            help="Comma-separated sections to include: scan, guard, mcp, cost.",
        ),
    ] = "scan,guard,mcp,cost",
) -> None:
    """[Experimental] Generate human-readable evidence and readiness reports locally."""
    fmt = format.lower()
    if fmt not in ("markdown", "json", "html"):
        console.print(
            f"[bold red]Error:[/] Unsupported format '{format}'. Use markdown, json, or html."
        )
        raise typer.Exit(1)

    try:
        from niyam.governance.evidence.command import execute_generate_evidence

        report_str = execute_generate_evidence(
            from_scan_json=from_scan, fmt=fmt, output=output, include=include, mission_id=mission
        )

        # If output file is not specified, write the report to console stdout
        if not output:
            print(report_str)
        else:
            console.print(
                f"[bold green]✓ Evidence report successfully saved to {output}[/]"
            )

    except FileNotFoundError as fnfe:
        console.print(f"[bold red]Error:[/] {fnfe}")
        raise typer.Exit(1)
    except ValueError as ve:
        console.print(f"[bold red]Error:[/] {ve}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[bold red]Error generating report:[/] {e}")
        raise typer.Exit(1)
