"""Niyam CLI scan commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer
from rich.panel import Panel
from rich.table import Table

from niyam.cli import app, console
from niyam.core.scan import run_scanner_checks


def generate_markdown_report(results: dict) -> str:
    """Generate a clean markdown report from scan results."""
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    score = results["score"]
    decision = results["decision"]
    profile = results["profile"]

    # Decision formatting
    decision_emojis = {
        "GO": "🟢 GO",
        "CONDITIONAL_GO": "🟡 CONDITIONAL GO",
        "HIGH_RISK": "🟠 HIGH RISK",
        "NO_GO": "🔴 NO GO",
    }
    decision_str = decision_emojis.get(decision, decision)

    lines = [
        "# Niyam Production Readiness Report",
        "",
        f"**Generated:** {now}",
        f"**Scan Profile:** `{profile}`",
        f"**Readiness Score:** `{score}/100`",
        f"**Decision:** {decision_str}",
        "",
        "---",
        "",
        "## Summary of Findings",
        "",
    ]

    findings = results["findings"]
    if not findings:
        lines.append("✓ No findings! Your repository is production-ready.")
    else:
        # Table header
        lines.extend(
            [
                "| ID | Severity | Category | Description | File Path |",
                "| --- | --- | --- | --- | --- |",
            ]
        )
        for f in findings:
            fpath = f"`{f['file_path']}`" if f["file_path"] else "*Global*"
            lines.append(
                f"| {f['id']} | **{f['severity'].upper()}** | {f['category']} | {f['description']} | {fpath} |"
            )

        lines.extend(["", "## Recommendations & Remediation", ""])
        for i, f in enumerate(findings, 1):
            lines.extend(
                [
                    f"### {i}. [{f['id']}] {f['title']}",
                    f"- **Severity:** {f['severity'].upper()}",
                    f"- **Category:** {f['category']}",
                    f"- **Description:** {f['description']}",
                    f"- **Recommendation:** {f['recommendation']}",
                    "",
                ]
            )

    return "\n".join(lines)


@app.command("scan")
def scan_command(
    path: Annotated[
        str, typer.Argument(help="Path to scan (defaults to current directory).")
    ] = ".",
    profile: Annotated[
        str,
        typer.Option(
            "--profile", "-p", help="Scan profile: startup, team, enterprise."
        ),
    ] = "startup",
    output: Annotated[
        str, typer.Option("--output", "-o", help="Output format: text, json, markdown.")
    ] = "text",
    report_file: Annotated[
        str,
        typer.Option(
            "--report-file", "-f", help="Output file path to save the report."
        ),
    ] = None,
    rules: Annotated[
        str, typer.Option("--rules", help="Path to custom rules YAML file.")
    ] = None,
) -> None:
    """Scan the repository for production-readiness and code risk factors."""
    scan_path = Path(path).resolve()
    if not scan_path.exists():
        console.print(f"[bold red]Error:[/] Directory '{path}' does not exist.")
        raise typer.Exit(1)

    custom_rules = Path(rules).resolve() if rules else None
    results = run_scanner_checks(
        scan_path, profile=profile, custom_rules_path=custom_rules
    )

    # Save file if requested
    if report_file:
        report_path = Path(report_file).resolve()
        md_content = generate_markdown_report(results)
        try:
            report_path.write_text(md_content, encoding="utf-8")
        except Exception as e:
            console.print(f"[bold red]Error writing report file:[/] {e}")
            raise typer.Exit(1)

    if output == "json":
        # Print pure json to stdout
        print(json.dumps(results, indent=2))
        return
    elif output == "markdown":
        # Print markdown to stdout
        print(generate_markdown_report(results))
        return

    # Default Text output
    score = results["score"]
    decision = results["decision"]
    findings = results["findings"]

    console.print("\n[bold cyan]🔍 Niyam Repository Readiness Scan[/]")
    console.print(f"[dim]Workspace:[/] {scan_path}   [dim]Profile:[/] {profile}\n")

    if not findings:
        console.print(
            "[bold green]✓ No findings! Your repository is production-ready.[/]"
        )
    else:
        table = Table(show_lines=False, box=None)
        table.add_column("ID", style="cyan", width=8)
        table.add_column("Severity", width=12)
        table.add_column("Category", style="magenta", width=15)
        table.add_column("Description")
        table.add_column("File Path", style="dim")

        severity_styles = {
            "critical": "[bold red]CRITICAL[/]",
            "high": "[red]HIGH[/]",
            "medium": "[yellow]MEDIUM[/]",
            "low": "[green]LOW[/]",
            "info": "[blue]INFO[/]",
        }

        for f in findings:
            sev_str = severity_styles.get(f["severity"], f["severity"].upper())
            fpath = f["file_path"] if f["file_path"] else "-"
            table.add_row(f["id"], sev_str, f["category"], f["description"], fpath)

        console.print(table)
        console.print()

    decision_colors = {
        "GO": "bold green",
        "CONDITIONAL_GO": "bold yellow",
        "HIGH_RISK": "bold red",
        "NO_GO": "bold red",
    }
    color = decision_colors.get(decision, "white")

    panel_content = (
        f"Readiness Score: [bold cyan]{score}/100[/]\nDecision: [{color}]{decision}[/]"
    )
    console.print(
        Panel(
            panel_content,
            title="[bold]Readiness Summary[/]",
            border_style="cyan" if score >= 70 else "red",
        )
    )

    # Print warnings for skipped external scanners
    skipped = results.get("skipped_scanners", [])
    if skipped:
        console.print("\n[bold yellow]⚠ Missing External Scanners (Skipped):[/]")
        install_help = {
            "gitleaks": "brew install gitleaks (secrets scanning)",
            "semgrep": "brew install semgrep (code vulnerability scan)",
            "trivy": "brew install trivy (dependency check)",
            "checkov": "pip install checkov (IaC scanning)",
        }
        for name in skipped:
            help_str = install_help.get(name, f"install {name}")
            console.print(f"  [dim]• {name} - Run: {help_str}[/]")

    if report_file:
        console.print(f"\n[green]✓ Report written to {report_file}[/]")
