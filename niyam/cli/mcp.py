"""Niyam CLI MCP and tool registry commands."""

from __future__ import annotations

from typing import Annotated, Optional

import typer

from niyam.cli import console, mcp_app


@mcp_app.command("register")
def mcp_register(
    name: Annotated[str, typer.Argument(help="Name of the tool/MCP server.")],
    type: Annotated[
        str,
        typer.Option(
            "--type", help="Type of tool: mcp_server/api/cli/local_tool/browser/other."
        ),
    ],
    command_or_url: Annotated[
        Optional[str],
        typer.Option("--command-or-url", help="Command or URL for the tool."),
    ] = None,
    owner: Annotated[
        Optional[str],
        typer.Option("--owner", help="Owner of the tool."),
    ] = None,
    risk: Annotated[
        Optional[str],
        typer.Option(
            "--risk",
            help="Risk level: low/medium/high/critical. If omitted, heuristic is used.",
        ),
    ] = None,
    approved: Annotated[
        bool,
        typer.Option("--approved/--no-approved", help="Approve the tool for usage."),
    ] = False,
    capabilities: Annotated[
        Optional[str],
        typer.Option(
            "--capabilities", help="Comma-separated capabilities of the tool."
        ),
    ] = None,
    data_access: Annotated[
        Optional[str],
        typer.Option("--data-access", help="Data access details."),
    ] = None,
    notes: Annotated[
        Optional[str],
        typer.Option("--notes", help="Notes/description of the tool."),
    ] = None,
) -> None:
    """Register a new tool or MCP server in the registry."""
    from niyam.core.mcp import (
        load_mcp_registry,
        save_mcp_registry,
        classify_risk,
        MCPTool,
    )

    # Validation
    valid_types = {"mcp_server", "api", "cli", "local_tool", "browser", "other"}
    if type not in valid_types:
        console.print(
            f"[bold red]Error:[/] Invalid type '{type}'. Must be one of {', '.join(valid_types)}"
        )
        raise SystemExit(1)

    if risk is not None:
        valid_risks = {"low", "medium", "high", "critical"}
        if risk not in valid_risks:
            console.print(
                f"[bold red]Error:[/] Invalid risk level '{risk}'. Must be one of {', '.join(valid_risks)}"
            )
            raise SystemExit(1)

    registry = load_mcp_registry()
    if name in registry.tools:
        console.print(f"[bold red]Error:[/] Tool '{name}' is already registered.")
        raise SystemExit(1)

    caps_list = [c.strip() for c in capabilities.split(",")] if capabilities else []

    # Heuristic risk calculation if not explicitly provided
    if risk is None:
        risk_level = classify_risk(
            name=name,
            type=type,
            command_or_url=command_or_url,
            capabilities=caps_list,
            data_access=data_access,
            notes=notes,
        )
    else:
        # Pydantic validation handles casting toLiteral, but let's cast here for safety
        risk_level = risk

    tool = MCPTool(
        name=name,
        type=type,
        command_or_url=command_or_url,
        owner=owner,
        risk_level=risk_level,
        approved=approved,
        capabilities=caps_list,
        data_access=data_access,
        notes=notes,
    )

    registry.tools[name] = tool
    save_mcp_registry(registry)

    console.print(f"[bold green]✓[/] Tool [bold]{name}[/] successfully registered.")


@mcp_app.command("list")
def mcp_list() -> None:
    """List all registered tools."""
    from niyam.core.mcp import load_mcp_registry
    from rich.table import Table

    registry = load_mcp_registry()
    if not registry.tools:
        console.print("[yellow]No tools registered yet.[/]")
        return

    table = Table(title="Registered AI Agent Tools / MCP Servers")
    table.add_column("Name", style="cyan")
    table.add_column("Type", style="magenta")
    table.add_column("Risk Level", justify="center")
    table.add_column("Approved", justify="center")
    table.add_column("Owner", style="dim")

    for tool in registry.tools.values():
        risk_style = (
            "green"
            if tool.risk_level == "low"
            else "yellow"
            if tool.risk_level == "medium"
            else "red"
            if tool.risk_level == "high"
            else "bold red"
        )
        approved_text = "[green]Yes[/]" if tool.approved else "[red]No[/]"
        table.add_row(
            tool.name,
            tool.type,
            f"[{risk_style}]{tool.risk_level}[/]",
            approved_text,
            tool.owner or "N/A",
        )

    console.print(table)


@mcp_app.command("show")
def mcp_show(
    name: Annotated[str, typer.Argument(help="Name of the tool to display.")],
) -> None:
    """Show details of a registered tool."""
    from niyam.core.mcp import load_mcp_registry
    from rich.panel import Panel

    registry = load_mcp_registry()
    if name not in registry.tools:
        console.print(f"[bold red]Error:[/] Tool '{name}' not found in registry.")
        raise SystemExit(1)

    tool = registry.tools[name]
    risk_style = (
        "green"
        if tool.risk_level == "low"
        else "yellow"
        if tool.risk_level == "medium"
        else "red"
        if tool.risk_level == "high"
        else "bold red"
    )
    approved_text = "[green]Yes[/]" if tool.approved else "[red]No[/]"

    content = (
        f"[bold]Name:[/] {tool.name}\n"
        f"[bold]Type:[/] {tool.type}\n"
        f"[bold]Risk Level:[/] [{risk_style}]{tool.risk_level}[/]\n"
        f"[bold]Approved:[/] {approved_text}\n"
        f"[bold]Owner:[/] {tool.owner or 'N/A'}\n"
        f"[bold]Command/URL:[/] {tool.command_or_url or 'N/A'}\n"
        f"[bold]Capabilities:[/] {', '.join(tool.capabilities) if tool.capabilities else 'None'}\n"
        f"[bold]Data Access:[/] {tool.data_access or 'N/A'}\n"
        f"[bold]Notes:[/] {tool.notes or 'N/A'}"
    )

    console.print(
        Panel(content, title=f"[bold cyan]Tool: {tool.name}[/]", border_style="cyan")
    )


@mcp_app.command("risk-report")
def mcp_risk_report() -> None:
    """Generate a risk and security report for all registered tools."""
    from niyam.core.mcp import load_mcp_registry
    from rich.panel import Panel
    from rich.table import Table

    registry = load_mcp_registry()
    if not registry.tools:
        console.print("[yellow]No tools registered to analyze.[/]")
        return

    # Count statistics
    total = len(registry.tools)
    by_risk = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    approved_count = 0
    unapproved_count = 0
    unapproved_high_risk = []

    for tool in registry.tools.values():
        by_risk[tool.risk_level] += 1
        if tool.approved:
            approved_count += 1
        else:
            unapproved_count += 1
            if tool.risk_level in ("high", "critical"):
                unapproved_high_risk.append(tool)

    summary_table = Table.grid(padding=(0, 2))
    summary_table.add_column("Metric", style="bold")
    summary_table.add_column("Value")

    summary_table.add_row("Total Registered Tools", str(total))
    summary_table.add_row("Approved Tools", f"[green]{approved_count}[/]")
    summary_table.add_row("Unapproved Tools", f"[red]{unapproved_count}[/]")

    risk_stats = (
        f"Critical: [bold red]{by_risk['critical']}[/] | "
        f"High: [red]{by_risk['high']}[/] | "
        f"Medium: [yellow]{by_risk['medium']}[/] | "
        f"Low: [green]{by_risk['low']}[/]"
    )
    summary_table.add_row("Risk Distribution", risk_stats)

    console.print(
        Panel(
            summary_table,
            title="[bold]MCP Tool Security & Risk Summary[/]",
            border_style="cyan",
        )
    )

    if unapproved_high_risk:
        warn_table = Table(
            title="[bold red]⚠ Action Required: Unapproved High/Critical Risk Tools[/]",
            border_style="red",
        )
        warn_table.add_column("Name", style="cyan")
        warn_table.add_column("Type", style="magenta")
        warn_table.add_column("Risk Level", justify="center")
        warn_table.add_column("Notes")

        for tool in unapproved_high_risk:
            risk_style = "red" if tool.risk_level == "high" else "bold red"
            warn_table.add_row(
                tool.name,
                tool.type,
                f"[{risk_style}]{tool.risk_level}[/]",
                tool.notes or "No notes provided.",
            )
        console.print(warn_table)
    else:
        console.print(
            "[bold green]✓ No unapproved High or Critical risk tools found.[/]"
        )
