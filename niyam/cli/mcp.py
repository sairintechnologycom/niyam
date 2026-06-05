"""Niyam CLI MCP and tool registry commands."""

from __future__ import annotations

from typing import Annotated, Optional

import typer

from niyam.cli import console, mcp_app


@mcp_app.command("register")
def mcp_register(
    name: Annotated[str, typer.Argument(help="Name of the tool/MCP server.")],
    type: Annotated[
        Optional[str],
        typer.Option(
            "--type", help="Type of tool: mcp_server/api/cli/local_tool/browser/other."
        ),
    ] = None,
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
        Optional[str],
        typer.Option("--approved", help="Approve the tool for usage: true/false."),
    ] = None,
    capabilities: Annotated[
        Optional[str],
        typer.Option(
            "--capabilities", help="Comma-separated capabilities of the tool."
        ),
    ] = None,
    capability: Annotated[
        Optional[list[str]],
        typer.Option(
            "--capability",
            help="Capability of the tool (can be specified multiple times).",
        ),
    ] = None,
    data_access: Annotated[
        Optional[str],
        typer.Option("--data-access", help="Data access details."),
    ] = None,
    network_access: Annotated[
        Optional[str],
        typer.Option("--network-access", help="Network access details."),
    ] = None,
    requires_approval: Annotated[
        Optional[str],
        typer.Option("--requires-approval", help="Requires approval: true/false."),
    ] = None,
    notes: Annotated[
        Optional[str],
        typer.Option("--notes", help="Notes/description of the tool."),
    ] = None,
    update: Annotated[
        bool,
        typer.Option("--update", help="Update the tool if it is already registered."),
    ] = False,
) -> None:
    """Register a new tool or MCP server in the registry."""
    import datetime
    from niyam.governance.common.redaction import redact_text
    from niyam.core.mcp import (
        load_mcp_registry,
        save_mcp_registry,
        classify_risk,
        MCPTool,
    )

    def redact_if_str(val: Optional[str]) -> Optional[str]:
        if val is None:
            return None
        return redact_text(val)

    # Load registry
    registry = load_mcp_registry()

    # Existence check
    existing_tool = None
    if name in registry.tools:
        if not update:
            console.print(f"[bold red]Error:[/] Tool '{name}' is already registered.")
            raise SystemExit(1)
        existing_tool = registry.tools[name]

    # Type validation
    valid_types = {"mcp_server", "api", "cli", "local_tool", "browser", "other"}
    if type is not None:
        if type not in valid_types:
            console.print(
                f"[bold red]Error:[/] Invalid type '{type}'. Must be one of {', '.join(valid_types)}"
            )
            raise SystemExit(1)
    elif existing_tool is None:
        console.print("[bold red]Error:[/] Type must be specified for new tools.")
        raise SystemExit(1)

    # Risk validation
    if risk is not None:
        valid_risks = {"low", "medium", "high", "critical"}
        if risk not in valid_risks:
            console.print(
                f"[bold red]Error:[/] Invalid risk level '{risk}'. Must be one of {', '.join(valid_risks)}"
            )
            raise SystemExit(1)

    # Boolean parsers
    approved_val = None
    if approved is not None:
        approved_val = approved.lower() in ("true", "yes", "1")

    requires_approval_val = None
    if requires_approval is not None:
        requires_approval_val = requires_approval.lower() in ("true", "yes", "1")

    # Capabilities merging
    if capabilities is not None or capability is not None:
        caps_list = []
        if capabilities:
            caps_list.extend([c.strip() for c in capabilities.split(",") if c.strip()])
        if capability:
            caps_list.extend([c.strip() for c in capability if c.strip()])
        seen = set()
        deduped_caps = []
        for cap in caps_list:
            if cap not in seen:
                seen.add(cap)
                deduped_caps.append(cap)
        final_capabilities = deduped_caps
    else:
        if existing_tool is not None:
            final_capabilities = existing_tool.capabilities
        else:
            final_capabilities = []

    # Heuristic risk calculation if not explicitly provided
    if risk is not None:
        risk_level = risk
    elif existing_tool is not None:
        risk_level = existing_tool.risk_level
    else:
        risk_level = classify_risk(
            name=name,
            type=type,
            command_or_url=redact_if_str(command_or_url),
            capabilities=final_capabilities,
            data_access=redact_if_str(data_access),
            notes=redact_if_str(notes),
        )

    now_str = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )

    # Redact string inputs
    redacted_command_or_url = redact_if_str(command_or_url)
    redacted_owner = redact_if_str(owner)
    redacted_notes = redact_if_str(notes)
    redacted_data_access = redact_if_str(data_access)
    redacted_network_access = redact_if_str(network_access)

    # Determine final field values
    if existing_tool is not None:
        final_type = type if type is not None else existing_tool.type
        final_command_or_url = (
            redacted_command_or_url
            if redacted_command_or_url is not None
            else existing_tool.command_or_url
        )
        final_owner = (
            redacted_owner if redacted_owner is not None else existing_tool.owner
        )
        final_approved = (
            approved_val if approved_val is not None else existing_tool.approved
        )
        final_data_access = (
            redacted_data_access
            if redacted_data_access is not None
            else existing_tool.data_access
        )
        final_network_access = (
            redacted_network_access
            if redacted_network_access is not None
            else existing_tool.network_access
        )
        final_requires_approval = (
            requires_approval_val
            if requires_approval_val is not None
            else existing_tool.requires_approval
        )
        final_notes = (
            redacted_notes if redacted_notes is not None else existing_tool.notes
        )
        final_created_at = (
            existing_tool.created_at if existing_tool.created_at else now_str
        )
        final_updated_at = now_str
    else:
        final_type = type
        final_command_or_url = redacted_command_or_url
        final_owner = redacted_owner
        final_approved = approved_val if approved_val is not None else False
        final_data_access = redacted_data_access
        final_network_access = redacted_network_access
        final_requires_approval = (
            requires_approval_val if requires_approval_val is not None else True
        )
        final_notes = redacted_notes
        final_created_at = now_str
        final_updated_at = now_str

    tool = MCPTool(
        name=name,
        type=final_type,
        command_or_url=final_command_or_url,
        owner=final_owner,
        risk_level=risk_level,
        approved=final_approved,
        capabilities=final_capabilities,
        data_access=final_data_access,
        network_access=final_network_access,
        requires_approval=final_requires_approval,
        notes=final_notes,
        created_at=final_created_at,
        updated_at=final_updated_at,
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
        f"[bold]Schema Version:[/] {tool.schema_version}\n"
        f"[bold]Name:[/] {tool.name}\n"
        f"[bold]Type:[/] {tool.type}\n"
        f"[bold]Risk Level:[/] [{risk_style}]{tool.risk_level}[/]\n"
        f"[bold]Approved:[/] {approved_text}\n"
        f"[bold]Owner:[/] {tool.owner or 'N/A'}\n"
        f"[bold]Command/URL:[/] {tool.command_or_url or 'N/A'}\n"
        f"[bold]Capabilities:[/] {', '.join(tool.capabilities) if tool.capabilities else 'None'}\n"
        f"[bold]Data Access:[/] {tool.data_access or 'N/A'}\n"
        f"[bold]Network Access:[/] {tool.network_access or 'N/A'}\n"
        f"[bold]Requires Approval:[/] {'Yes' if tool.requires_approval else 'No'}\n"
        f"[bold]Notes:[/] {tool.notes or 'N/A'}\n"
        f"[bold]Created At:[/] {tool.created_at or 'N/A'}\n"
        f"[bold]Updated At:[/] {tool.updated_at or 'N/A'}"
    )

    console.print(
        Panel(content, title=f"[bold cyan]Tool: {tool.name}[/]", border_style="cyan")
    )


@mcp_app.command("approve")
def mcp_approve(
    name: Annotated[str, typer.Argument(help="Name of the tool to approve.")],
) -> None:
    """Approve a registered tool or MCP server for agent usage."""
    from niyam.core.mcp import load_mcp_registry, save_mcp_registry
    import datetime

    registry = load_mcp_registry()
    if name not in registry.tools:
        console.print(f"[bold red]Error:[/] Tool '{name}' not found in registry.")
        raise SystemExit(1)

    tool = registry.tools[name]
    if tool.approved:
        console.print(f"[yellow]Tool '{name}' is already approved.[/]")
        return

    tool.approved = True
    tool.updated_at = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    registry.tools[name] = tool
    save_mcp_registry(registry)

    console.print(f"[bold green]✓[/] Tool [bold]{name}[/] successfully approved.")


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
