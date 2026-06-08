"""Niyam CLI scan commands."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Annotated

import typer
from rich.panel import Panel
from rich.table import Table

from niyam.cli import app, console
from niyam.cli.context import is_interactive, prompt_text


_SCAN_OPTIONS_WITH_VALUES = {
    "--profile",
    "-p",
    "--output",
    "-o",
    "--report-file",
    "-f",
    "--rules",
    "--fail-on",
    "--baseline",
    "--create-baseline",
}


def _scan_path_was_omitted() -> bool:
    """Best-effort detection for prompting without changing the public CLI shape."""
    try:
        scan_index = sys.argv.index("scan")
    except ValueError:
        return False

    skip_next = False
    for arg in sys.argv[scan_index + 1 :]:
        if arg == "--":
            return False
        if skip_next:
            skip_next = False
            continue
        if arg in _SCAN_OPTIONS_WITH_VALUES:
            skip_next = True
            continue
        if arg.startswith("-"):
            continue
        return False
    return True


def generate_sarif_report(results: dict) -> str:
    """Generate a valid SARIF v2.1.0 JSON string from scan results."""
    findings = results.get("findings", [])

    severity_map = {
        "critical": "error",
        "high": "error",
        "medium": "warning",
        "low": "note",
        "info": "note",
    }

    rules_dict = {}
    sarif_results = []

    for f in findings:
        rule_id = f.get("id", "UNKNOWN")
        severity = f.get("severity", "info").lower()
        level = severity_map.get(severity, "note")

        if rule_id not in rules_dict:
            rules_dict[rule_id] = {
                "id": rule_id,
                "shortDescription": {"text": f.get("title", rule_id)},
                "fullDescription": {"text": f.get("description", "")},
                "help": {"text": f"Recommendation: {f.get('recommendation', '')}"},
            }

        location = {}
        file_path = f.get("file_path", "")
        if file_path:
            artifact_loc = {"uri": file_path}
            region = {}
            line_num = f.get("line_number")
            if line_num is not None:
                region["startLine"] = int(line_num)
                location = {
                    "physicalLocation": {
                        "artifactLocation": artifact_loc,
                        "region": region,
                    }
                }
            else:
                location = {"physicalLocation": {"artifactLocation": artifact_loc}}

        result_entry = {
            "ruleId": rule_id,
            "level": level,
            "message": {
                "text": f"{f.get('description', '')}\nRecommendation: {f.get('recommendation', '')}"
            },
        }
        if location:
            result_entry["locations"] = [location]

        sarif_results.append(result_entry)

    sarif_log = {
        "$schema": "https://schemastore.azurewebsites.net/schemas/json/sarif-2.1.0-rtm.5.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "Niyam Scanner",
                        "rules": list(rules_dict.values()),
                        "version": "0.4.0",
                    }
                },
                "results": sarif_results,
            }
        ],
    }

    return json.dumps(sarif_log, indent=2)


def generate_markdown_report(results: dict) -> str:
    """Generate a clean markdown report from scan results."""
    from datetime import datetime, timezone
    from niyam.governance.scoring import PROFILE_WEIGHTS, DIMENSION_LABELS

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    score = results["score"]
    decision = results["decision"]
    profile = results["profile"]
    decision_reason = results.get("decision_reason", "Scan completed successfully.")

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
    ]
    if decision_reason and decision_reason != "Scan completed successfully.":
        lines.append(f"**Decision Reason:** *{decision_reason}*")

    lines.extend(
        [
            "",
            "## Readiness Score Breakdown",
            "",
            "| Dimension | Weight | Score |",
            "| --- | --- | --- |",
        ]
    )

    weights = PROFILE_WEIGHTS.get(profile.lower(), PROFILE_WEIGHTS["startup"])
    scoring_bd = results.get("scoring_breakdown", {})
    for dim, weight in weights.items():
        label = DIMENSION_LABELS.get(dim, dim.replace("_", " ").title())
        score_val = scoring_bd.get(dim, weight)
        lines.append(f"| {label} | {weight}% | {score_val}/{weight} |")

    lines.extend(
        [
            f"| **Total** | **100%** | **{score}/100** |",
            "",
            "---",
            "",
            "## Summary of Findings",
            "",
        ]
    )

    findings = results["findings"]
    if not findings:
        lines.append("✓ No findings! Your repository is production-ready.")
    else:
        # Table header
        lines.extend(
            [
                "| ID | Severity | Status | Category | Description | File Path |",
                "| --- | --- | --- | --- | --- | --- |",
            ]
        )
        for f in findings:
            fpath = f"`{f['file_path']}`" if f["file_path"] else "*Global*"
            status_val = (
                "ACCEPTED" if f.get("status") == "accepted_existing" else "OPEN"
            )
            lines.append(
                f"| {f['id']} | **{f['severity'].upper()}** | **{status_val}** | {f['category']} | {f['description']} | {fpath} |"
            )

        lines.extend(["", "## Recommendations & Remediation", ""])
        for i, f in enumerate(findings, 1):
            status_val = (
                "ACCEPTED" if f.get("status") == "accepted_existing" else "OPEN"
            )
            lines.extend(
                [
                    f"### {i}. [{f['id']}] {f['title']}",
                    f"- **Severity:** {f['severity'].upper()}",
                    f"- **Status:** {status_val}",
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
    fail_on: Annotated[
        str,
        typer.Option(
            "--fail-on",
            help="Fail scan (exit code 2) if finding with this severity or higher is found: critical, high, medium, low, info.",
        ),
    ] = None,
    baseline: Annotated[
        str, typer.Option("--baseline", help="Path to baseline JSON file.")
    ] = None,
    create_baseline: Annotated[
        str,
        typer.Option("--create-baseline", help="Path to write the baseline JSON file."),
    ] = None,
) -> None:
    """[Experimental] Scan the repository for production-readiness and code risk factors."""
    if output == "text" and path == "." and _scan_path_was_omitted():
        path = prompt_text("Directory to scan", ".")

    scan_path = Path(path).resolve()
    if not scan_path.exists():
        console.print(f"[bold red]Error:[/] Directory '{path}' does not exist.")
        raise typer.Exit(3)  # Invalid config/input paths

    if output not in ("text", "json", "markdown", "sarif"):
        console.print(
            f"[bold red]Error:[/] Invalid --output format '{output}'. Allowed values: text, json, markdown, sarif."
        )
        raise typer.Exit(3)

    custom_rules = Path(rules).resolve() if rules else None
    baseline_path = Path(baseline).resolve() if baseline else None
    create_baseline_path = Path(create_baseline).resolve() if create_baseline else None
    from niyam.governance.scan.command import execute_scan

    try:
        if output == "text" and is_interactive():
            with console.status("[cyan]Analyzing repository...[/]", spinner="dots"):
                results = execute_scan(
                    str(scan_path),
                    profile=profile,
                    custom_rules_path=custom_rules,
                    baseline_path=baseline_path,
                    create_baseline_path=create_baseline_path,
                )
        else:
            results = execute_scan(
                str(scan_path),
                profile=profile,
                custom_rules_path=custom_rules,
                baseline_path=baseline_path,
                create_baseline_path=create_baseline_path,
            )
    except (ValueError, FileNotFoundError) as e:
        console.print(f"[bold red]Configuration Error:[/] {e}")
        raise typer.Exit(3)
    except PermissionError as e:
        console.print(f"[bold red]Permission/Access Error:[/] {e}")
        raise typer.Exit(5)
    except OSError as e:
        console.print(f"[bold red]Scan Runtime Error:[/] {e}")
        raise typer.Exit(4)
    except Exception as e:
        console.print(f"[bold red]Unexpected Error:[/] {e}")
        raise typer.Exit(1)

    try:
        from niyam.core.config import find_niyam_root
        from niyam.core.memory import CodebaseIndexer

        repo_root = find_niyam_root(scan_path) or scan_path
        CodebaseIndexer(repo_root).build_index()
    except Exception:
        pass

    # Redact all results before writing or printing
    from niyam.governance.common.redaction import redact_secrets, redact_text

    results = redact_secrets(results)

    # Save file if requested
    if report_file:
        report_path = Path(report_file).resolve()
        if output == "json":
            content = json.dumps(results, indent=2)
        elif output == "sarif":
            content = generate_sarif_report(results)
        else:
            content = generate_markdown_report(results)
        content = redact_text(content)
        try:
            report_path.write_text(content, encoding="utf-8")
        except Exception as e:
            console.print(f"[bold red]Error writing report file:[/] {e}")
            raise typer.Exit(4)

    if output == "json":
        # Print pure json to stdout
        json_str = json.dumps(results, indent=2)
        print(redact_text(json_str))
    elif output == "sarif":
        # Print pure sarif to stdout
        sarif_str = generate_sarif_report(results)
        print(redact_text(sarif_str))
    elif output == "markdown":
        # Print markdown to stdout
        md_str = generate_markdown_report(results)
        print(redact_text(md_str))
    else:
        # Default Text output
        score = results["score"]
        decision = results["decision"]
        findings = results["findings"]

        console.print(redact_text("\n[bold cyan]🔍 Niyam Repository Readiness Scan[/]"))
        console.print(
            redact_text(
                f"[dim]Workspace:[/] {scan_path}   [dim]Profile:[/] {profile}\n"
            )
        )

        if not findings:
            console.print(
                "[bold green]✓ No findings! Your repository is production-ready.[/]"
            )
        else:
            table = Table(show_lines=False, box=None)
            table.add_column("ID", style="cyan", width=8)
            table.add_column("Severity", width=12)
            table.add_column("Status", width=12)
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
                status_str = (
                    "[green]ACCEPTED[/]"
                    if f.get("status") == "accepted_existing"
                    else "[red]OPEN[/]"
                )
                fpath = f["file_path"] if f["file_path"] else "-"
                # Redact cell text
                desc_redacted = redact_text(f["description"])
                fpath_redacted = redact_text(fpath)
                table.add_row(
                    f["id"],
                    sev_str,
                    status_str,
                    f["category"],
                    desc_redacted,
                    fpath_redacted,
                )

            console.print(table)
            console.print()

        # Print severity count summary
        summary = results.get("summary", {})
        console.print("[bold]Scan Findings Summary by Severity:[/]")
        for sev in ["critical", "high", "medium", "low", "info"]:
            count = summary.get(sev, 0)
            console.print(f"  • {sev.upper()}: {count}")
        console.print()

        decision_colors = {
            "GO": "bold green",
            "CONDITIONAL_GO": "bold yellow",
            "HIGH_RISK": "bold red",
            "NO_GO": "bold red",
        }
        color = decision_colors.get(decision, "white")

        panel_content = f"Readiness Score: [bold cyan]{score}/100[/]\nDecision: [{color}]{decision}[/]"
        if (
            "decision_reason" in results
            and results["decision_reason"] != "Scan completed successfully."
        ):
            panel_content += f"\nReason: {results['decision_reason']}"

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

    # Check fail-on exit code logic
    exceeded = False
    fail_reason = ""
    severity_levels = {"info": 1, "low": 2, "medium": 3, "high": 4, "critical": 5}

    if fail_on:
        fail_on_lower = fail_on.lower()
        if fail_on_lower in severity_levels:
            threshold = severity_levels[fail_on_lower]
            for f in results["findings"]:
                sev = f.get("severity", "info").lower()
                if severity_levels.get(sev, 0) >= threshold:
                    exceeded = True
                    fail_reason = f"Severity '{sev.upper()}' finding found: [{f['id']}] {f['title']}"
                    break
        else:
            console.print(
                f"[bold red]Error:[/] Invalid --fail-on value '{fail_on}'. Allowed values: critical, high, medium, low, info."
            )
            raise typer.Exit(3)

    # If scan decision is NO_GO, fail with exit code 2 (blocking findings) regardless of --fail-on
    if not exceeded and results["decision"] == "NO_GO":
        exceeded = True
        fail_reason = f"Scan decision is NO_GO. Reason: {results.get('decision_reason', 'Readiness score is below 50.')}"

    if exceeded:
        import sys

        sys.stderr.write(redact_text(f"\n❌ Scan failed: {fail_reason}\n"))
        summary = results.get("summary", {})
        sys.stderr.write("\nSeverity Summary:\n")
        for sev in ["critical", "high", "medium", "low", "info"]:
            count = summary.get(sev, 0)
            sys.stderr.write(f"  • {sev.upper()}: {count}\n")
        if report_file:
            sys.stderr.write(f"\nReport Path: {report_file}\n")
        raise typer.Exit(2)
