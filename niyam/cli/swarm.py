"""Niyam CLI swarm commands."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
import typer
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
import time

from niyam.cli import console, swarm_app
from niyam.core.swarm import (
    load_swarm_state,
    load_ledger_messages,
    acquire_lock,
    release_lock,
    append_ledger_message,
    heartbeat,
    prune_stale_agents,
    is_agent_stale,
    get_swarm_dir,
    get_pending_requests,
    deregister_agent,
    save_swarm_state,
    swarm_state_lock,
    _normalize_resource_path,
)
from niyam.core.config import find_niyam_root


# ── Helpers ───────────────────────────────────────────────────────────


def _require_root() -> Path:
    """Get the workspace root or exit with an error."""
    root = find_niyam_root()
    if not root:
        console.print(
            "[bold red]Error:[/] Not a Niyam workspace. Run [cyan]niyam init[/] first."
        )
        raise typer.Exit(1)
    return root


def _human_age(iso_timestamp: str) -> str:
    """Convert ISO timestamp to human-friendly relative age."""
    try:
        ts = datetime.fromisoformat(iso_timestamp)
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        diff = (datetime.now(timezone.utc) - ts).total_seconds()

        if diff < 0:
            return "just now"
        elif diff < 60:
            return f"{int(diff)}s ago"
        elif diff < 3600:
            return f"{int(diff // 60)}m {int(diff % 60)}s ago"
        elif diff < 86400:
            return f"{int(diff // 3600)}h {int((diff % 3600) // 60)}m ago"
        else:
            return f"{int(diff // 86400)}d ago"
    except Exception:
        return iso_timestamp


# ── Commands ──────────────────────────────────────────────────────────


@swarm_app.command("init")
def swarm_init() -> None:
    """Initialize the swarm coordination directory."""
    root = _require_root()
    swarm_dir = get_swarm_dir(root)

    # Create initial files for discoverability
    state_path = swarm_dir / "state.json"
    ledger_path = swarm_dir / "ledger.jsonl"

    if not state_path.exists():
        state_path.write_text("{}", encoding="utf-8")
    if not ledger_path.exists():
        ledger_path.touch()

    console.print(
        f"[bold green]✓[/] Swarm mode initialized in [bold]{swarm_dir}[/]"
    )


@swarm_app.command("status")
def swarm_status(
    watch: bool = typer.Option(
        False, "--watch", "-w", help="Periodically refresh the status."
    ),
) -> None:
    """Show the real-time status of the autonomous workspace swarm."""
    root = _require_root()

    def generate_tables():
        with swarm_state_lock(root):
            state = load_swarm_state(root)

        # 1. Agents Table
        agent_table = Table(title="Active Swarm Agents")
        agent_table.add_column("Agent ID", style="bold cyan")
        agent_table.add_column("Role", style="magenta")
        agent_table.add_column("Status", style="bold")
        agent_table.add_column("Current Task", style="dim")
        agent_table.add_column("Last Seen", style="italic")

        for agent in state.agents.values():
            stale = is_agent_stale(agent)
            status_text = agent.status.upper()
            if stale:
                status_text = f"[bold red]STALE ({status_text})[/]"

            status_colors = {
                "idle": "green",
                "busy": "yellow",
                "waiting": "red",
                "offline": "dim white",
            }
            color = status_colors.get(agent.status, "white")
            if not stale:
                status_text = f"[{color}]{status_text}[/]"

            agent_table.add_row(
                agent.id,
                agent.role,
                status_text,
                agent.current_task or "None",
                _human_age(agent.last_seen),
            )

        # 2. Locks Table
        lock_table = Table(title="Resource Locks")
        lock_table.add_column("Resource (File)", style="bold yellow")
        lock_table.add_column("Held By", style="bold cyan")
        lock_table.add_column("Age", style="dim")
        lock_table.add_column("Reason", style="italic")

        for lock in state.locks.values():
            lock_table.add_row(
                lock.resource_path,
                lock.agent_id,
                _human_age(lock.acquired_at),
                lock.reason or "-",
            )

        # 3. Pending Negotiation Requests
        pending = get_pending_requests(root)
        request_table = Table(title="Pending Negotiation Requests")
        request_table.add_column("Requester", style="cyan")
        request_table.add_column("Holder", style="cyan")
        request_table.add_column("Resource", style="yellow")
        request_table.add_column("Age", style="dim")

        for msg in pending:
            request_table.add_row(
                msg.sender,
                msg.receiver,
                msg.resource or "-",
                _human_age(msg.timestamp),
            )

        return agent_table, lock_table, request_table

    if watch:
        from rich.console import Group

        with Live(console=console, refresh_per_second=1) as live:
            while True:
                tables = generate_tables()
                live.update(
                    Panel.fit(
                        Group(*tables),
                        title="Niyam Swarm Monitor",
                    )
                )
                time.sleep(1)
    else:
        agent_table, lock_table, request_table = generate_tables()
        console.print(agent_table)
        console.print("\n")
        console.print(lock_table)
        console.print("\n")
        console.print(request_table)


@swarm_app.command("clean")
def swarm_clean() -> None:
    """Remove stale agents and release their locks."""
    root = _require_root()
    count = prune_stale_agents(root)
    if count > 0:
        console.print(
            f"[bold green]✓[/] Removed [bold cyan]{count}[/] stale agents and released their locks."
        )
    else:
        console.print("[yellow]No stale agents found.[/]")


@swarm_app.command("lock")
def swarm_lock(
    resource: str = typer.Argument(..., help="Path to the file to lock."),
    agent: str = typer.Option(
        ..., "--agent", help="Agent ID acquiring the lock."
    ),
    reason: Optional[str] = typer.Option(
        None, "--reason", help="Reason for locking."
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Force acquire the lock even if held by an active agent.",
    ),
) -> None:
    """Acquire an exclusive lock on a resource."""
    root = _require_root()

    if force:
        with swarm_state_lock(root):
            state = load_swarm_state(root)
            res_key = _normalize_resource_path(resource)
            if res_key in state.locks:
                del state.locks[res_key]
                save_swarm_state(state, root)

    success = acquire_lock(resource, agent, reason=reason, repo_root=root)

    if success:
        console.print(
            f"[bold green]✓[/] Lock acquired on [bold yellow]{resource}[/] by [bold cyan]{agent}[/]"
        )
    else:
        console.print(
            "[bold red]✗[/] Failed to acquire lock. Resource is already held."
        )
        raise typer.Exit(1)


@swarm_app.command("unlock")
def swarm_unlock(
    resource: str = typer.Argument(..., help="Path to the file to unlock."),
    agent: str = typer.Option(
        ..., "--agent", help="Agent ID releasing the lock."
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Force release the lock even if you do not hold it.",
    ),
) -> None:
    """Release an exclusive lock on a resource."""
    root = _require_root()

    if force:
        with swarm_state_lock(root):
            state = load_swarm_state(root)
            res_key = _normalize_resource_path(resource)
            if res_key in state.locks:
                del state.locks[res_key]
                save_swarm_state(state, root)
                console.print(
                    f"[bold green]✓[/] Force-released lock on [bold yellow]{resource}[/]"
                )
                return

    success = release_lock(resource, agent, repo_root=root)

    if success:
        console.print(
            f"[bold green]✓[/] Lock released on [bold yellow]{resource}[/] by [bold cyan]{agent}[/]"
        )
    else:
        console.print(
            "[bold red]✗[/] Failed to release lock. You do not hold this lock."
        )
        raise typer.Exit(1)


@swarm_app.command("request-lock")
def swarm_request_lock(
    resource: str = typer.Argument(..., help="Path to the file requested."),
    agent: str = typer.Option(
        ..., "--from", help="Agent ID requesting the lock."
    ),
    target: str = typer.Option(
        ..., "--to", help="Agent ID holding the lock."
    ),
) -> None:
    """Send a lock request message to another agent."""
    root = _require_root()
    append_ledger_message(
        sender=agent,
        receiver=target,
        action="request_lock",
        resource=resource,
        repo_root=root,
    )
    console.print(
        f"[bold blue]ℹ[/] Negotiation request sent: "
        f"[bold cyan]{agent}[/] -> [bold cyan]{target}[/] for [bold yellow]{resource}[/]"
    )


@swarm_app.command("yield-lock")
def swarm_yield_lock(
    resource: str = typer.Argument(..., help="Path to the file being yielded."),
    agent: str = typer.Option(
        ..., "--from", help="Agent ID yielding the lock."
    ),
    target: str = typer.Option(
        ..., "--to", help="Agent ID that requested the lock."
    ),
) -> None:
    """Yield a lock to a requesting agent (release + notify)."""
    root = _require_root()

    # Release the lock first
    release_lock(resource, agent, repo_root=root)

    # Notify via ledger
    append_ledger_message(
        sender=agent,
        receiver=target,
        action="yield_lock",
        resource=resource,
        repo_root=root,
    )
    console.print(
        f"[bold green]✓[/] Lock yielded on [bold yellow]{resource}[/]: "
        f"[bold cyan]{agent}[/] -> [bold cyan]{target}[/]"
    )


@swarm_app.command("deny-lock")
def swarm_deny_lock(
    resource: str = typer.Argument(
        ..., help="Path to the file being denied."
    ),
    agent: str = typer.Option(
        ..., "--from", help="Agent ID denying the request."
    ),
    target: str = typer.Option(
        ..., "--to", help="Agent ID that requested the lock."
    ),
    reason: Optional[str] = typer.Option(
        None, "--reason", help="Reason for denial."
    ),
) -> None:
    """Deny a lock request from another agent."""
    root = _require_root()
    append_ledger_message(
        sender=agent,
        receiver=target,
        action="deny_lock",
        resource=resource,
        payload={"reason": reason} if reason else {},
        repo_root=root,
    )
    console.print(
        f"[bold red]✗[/] Lock denied on [bold yellow]{resource}[/]: "
        f"[bold cyan]{agent}[/] -> [bold cyan]{target}[/]"
        + (f" (reason: {reason})" if reason else "")
    )


@swarm_app.command("logs")
def swarm_logs() -> None:
    """View the coordination and negotiation ledger logs."""
    _print_logs()


@swarm_app.command("ledger")
def swarm_ledger() -> None:
    """Alias for 'swarm logs'."""
    _print_logs()


def _print_logs() -> None:
    root = _require_root()
    messages = load_ledger_messages(root)

    if not messages:
        console.print("[yellow]No swarm ledger entries found.[/]")
        return

    table = Table(title="Swarm Negotiation Ledger")
    table.add_column("Timestamp", style="dim")
    table.add_column("Sender", style="cyan")
    table.add_column("Receiver", style="cyan")
    table.add_column("Action", style="bold magenta")
    table.add_column("Resource", style="yellow")

    for msg in messages:
        table.add_row(
            msg.timestamp,
            msg.sender,
            msg.receiver,
            msg.action,
            msg.resource or "-",
        )

    console.print(table)


@swarm_app.command("heartbeat")
def swarm_heartbeat(
    agent: str = typer.Option(..., "--agent", help="Agent ID."),
    role: str = typer.Option(..., "--role", help="Agent role."),
    status: str = typer.Option("idle", "--status", help="Current status."),
    task: Optional[str] = typer.Option(None, "--task", help="Current task ID."),
) -> None:
    """Update agent heartbeat (internal use)."""
    root = _require_root()
    try:
        heartbeat(agent, role, status, task, root)  # type: ignore[arg-type]
    except ValueError as e:
        console.print(f"[bold red]Error:[/] {e}")
        raise typer.Exit(1)
    console.print(f"[dim]Heartbeat updated for {agent}.[/]")


@swarm_app.command("deregister")
def swarm_deregister(
    agent: str = typer.Option(..., "--agent", help="Agent ID to deregister."),
) -> None:
    """Gracefully remove an agent from the swarm and release its locks."""
    root = _require_root()
    removed = deregister_agent(agent, repo_root=root)
    if removed:
        console.print(
            f"[bold green]✓[/] Agent [bold cyan]{agent}[/] deregistered and all locks released."
        )
    else:
        console.print(
            f"[yellow]Agent [bold cyan]{agent}[/] not found in swarm state.[/]"
        )
