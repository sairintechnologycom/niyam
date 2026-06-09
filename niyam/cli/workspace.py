"""CLI commands for Niyam workspace."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
import uuid

import typer

from niyam.cli import console, workspace_app
from niyam.core.workspace import (
    WorkspaceAction,
    WorkspaceApproval,
    WorkspaceSession,
    WorkspaceStore,
    WorkspaceTimeline,
    WorkspaceApprovals,
    WorkspaceEvidence,
)
from niyam.core.workspace.browser import BrowserStore, RecorderBrowserBackend
from niyam.core.errors import NiyamError
from niyam.core.config import find_niyam_root

def _get_workspace_dir() -> Path:
    root = find_niyam_root()
    if root is None:
        raise NiyamError("Not a Niyam workspace. Run 'niyam init' first.", code=1)
    p = root / ".niyam" / "workspace"
    p.mkdir(parents=True, exist_ok=True)
    return p

def _get_store() -> WorkspaceStore:
    return WorkspaceStore(_get_workspace_dir())

def _get_timeline() -> WorkspaceTimeline:
    return WorkspaceTimeline(_get_workspace_dir())

def _get_approvals() -> WorkspaceApprovals:
    return WorkspaceApprovals(_get_workspace_dir())

@workspace_app.command("create")
def create_session(
    title: str = typer.Argument(..., help="Title of the session"),
    agent_type: str = typer.Option("manual", help="Type of agent (manual, cli, code, browser, mcp)"),
    risk: str = typer.Option("low", help="Risk level (low, medium, high, critical)"),
    objective: Optional[str] = typer.Option(None, help="Objective of the session"),
    session_id: Optional[str] = typer.Option(None, help="Custom session ID (auto-generated if not provided)"),
) -> None:
    """Create a new supervised human-agent task room."""
    store = _get_store()
    s_id = session_id or f"TASK-{uuid.uuid4().hex[:8].upper()}"

    session = WorkspaceSession(
        id=s_id,
        title=title,
        agent_type=agent_type,
        risk=risk,
        objective=objective,
        status="created",
    )
    store.create_session(session)
    console.print(f"[green]Created workspace session: {s_id}[/]")

@workspace_app.command("list")
def list_sessions() -> None:
    """List all workspace sessions."""
    store = _get_store()
    sessions = store.list_sessions()
    if not sessions:
        console.print("No workspace sessions found.")
        return
    for s in sessions:
        console.print(f"- [cyan]{s.id}[/] ({s.status}): {s.title}")

@workspace_app.command("show")
def show_session(session_id: str) -> None:
    """Show details of a specific workspace session."""
    store = _get_store()
    session = store.get_session(session_id)
    if not session:
        raise NiyamError(f"Session {session_id} not found.")
    console.print_json(session.model_dump_json())

@workspace_app.command("log")
def log_action(
    session_id: str = typer.Argument(..., help="Session ID"),
    type: str = typer.Option(..., "--type", help="Action type"),
    actor: str = typer.Option(..., help="Actor (human, agent, system)"),
    input: Optional[str] = typer.Option(None, help="Action input"),
    output: Optional[str] = typer.Option(None, help="Action output"),
    risk: str = typer.Option("low", help="Risk level"),
) -> None:
    """Log an action to the session timeline."""
    store = _get_store()
    if not store.get_session(session_id):
        raise NiyamError(f"Session {session_id} not found.")

    timeline = _get_timeline()
    action = WorkspaceAction(
        id=f"ACT-{uuid.uuid4().hex[:8].upper()}",
        session_id=session_id,
        actor=actor,
        action_type=type,
        input=input,
        output=output,
        risk=risk,
    )
    timeline.log_action(action)
    console.print(f"[green]Logged action {action.id} to session {session_id}.[/]")

@workspace_app.command("pause")
def pause_session(session_id: str) -> None:
    """Pause a workspace session."""
    store = _get_store()
    session = store.get_session(session_id)
    if not session:
        raise NiyamError(f"Session {session_id} not found.")
    session.status = "paused"
    store.update_session(session)

    # Log status change
    action = WorkspaceAction(
        id=f"ACT-{uuid.uuid4().hex[:8].upper()}",
        session_id=session_id,
        actor="system",
        action_type="status_change",
        output="Session paused",
    )
    _get_timeline().log_action(action)
    console.print(f"[yellow]Session {session_id} paused.[/]")

@workspace_app.command("resume")
def resume_session(session_id: str) -> None:
    """Resume a paused workspace session."""
    store = _get_store()
    session = store.get_session(session_id)
    if not session:
        raise NiyamError(f"Session {session_id} not found.")
    session.status = "running"
    store.update_session(session)

    # Log status change
    action = WorkspaceAction(
        id=f"ACT-{uuid.uuid4().hex[:8].upper()}",
        session_id=session_id,
        actor="system",
        action_type="status_change",
        output="Session resumed",
    )
    _get_timeline().log_action(action)
    console.print(f"[green]Session {session_id} resumed.[/]")

@workspace_app.command("request-approval")
def request_approval(
    session_id: str = typer.Argument(..., help="Session ID"),
    action: str = typer.Option(..., "--action", help="Action requiring approval"),
    risk: str = typer.Option("high", "--risk", help="Risk level"),
    reason: Optional[str] = typer.Option(None, "--reason", help="Reason for approval"),
    by: Optional[str] = typer.Option(None, "--by", help="User requesting approval"),
) -> None:
    """Request approval for an action in a session."""
    store = _get_store()
    session = store.get_session(session_id)
    if not session:
        raise NiyamError(f"Session {session_id} not found.")

    approvals = _get_approvals()
    approval_id = f"APP-{uuid.uuid4().hex[:8].upper()}"
    appr = WorkspaceApproval(
        id=approval_id,
        session_id=session_id,
        action=action,
        risk=risk,
        reason=reason,
        requested_by=by,
    )
    approvals.request_approval(appr)

    session.status = "approval_required"
    store.update_session(session)

    # Log request
    timeline_action = WorkspaceAction(
        id=f"ACT-{uuid.uuid4().hex[:8].upper()}",
        session_id=session_id,
        actor="system",
        action_type="approval_request",
        output=f"Approval requested: {action}",
        requires_approval=True,
        approval_id=approval_id,
    )
    _get_timeline().log_action(timeline_action)
    console.print(f"[yellow]Approval requested {approval_id} for session {session_id}.[/]")

@workspace_app.command("approve")
def approve_action(
    session_id: str = typer.Argument(..., help="Session ID"),
    approval_id: str = typer.Option(..., "--approval", help="Approval ID"),
    by: str = typer.Option(..., "--by", help="User approving"),
) -> None:
    """Approve a pending request."""
    store = _get_store()
    session = store.get_session(session_id)
    if not session:
        raise NiyamError(f"Session {session_id} not found.")

    approvals = _get_approvals()
    all_appr = approvals.get_approvals(session_id)
    appr = next((a for a in all_appr if a.id == approval_id), None)
    if not appr:
        raise NiyamError(f"Approval {approval_id} not found.")

    appr.status = "approved"
    appr.decided_at = datetime.now(timezone.utc)
    appr.decided_by = by
    approvals.update_approval(appr)

    session.status = "running"
    store.update_session(session)

    # Log decision
    timeline_action = WorkspaceAction(
        id=f"ACT-{uuid.uuid4().hex[:8].upper()}",
        session_id=session_id,
        actor="human",
        action_type="approval_decision",
        output=f"Approval {approval_id} granted by {by}",
        approval_id=approval_id,
        approved_by=by,
    )
    _get_timeline().log_action(timeline_action)
    console.print(f"[green]Approval {approval_id} granted.[/]")

@workspace_app.command("reject")
def reject_action(
    session_id: str = typer.Argument(..., help="Session ID"),
    approval_id: str = typer.Option(..., "--approval", help="Approval ID"),
    by: str = typer.Option(..., "--by", help="User rejecting"),
) -> None:
    """Reject a pending request."""
    store = _get_store()
    session = store.get_session(session_id)
    if not session:
        raise NiyamError(f"Session {session_id} not found.")

    approvals = _get_approvals()
    all_appr = approvals.get_approvals(session_id)
    appr = next((a for a in all_appr if a.id == approval_id), None)
    if not appr:
        raise NiyamError(f"Approval {approval_id} not found.")

    appr.status = "rejected"
    appr.decided_at = datetime.now(timezone.utc)
    appr.decided_by = by
    approvals.update_approval(appr)

    session.status = "running"
    store.update_session(session)

    # Log decision
    timeline_action = WorkspaceAction(
        id=f"ACT-{uuid.uuid4().hex[:8].upper()}",
        session_id=session_id,
        actor="human",
        action_type="approval_decision",
        output=f"Approval {approval_id} rejected by {by}",
        approval_id=approval_id,
    )
    _get_timeline().log_action(timeline_action)
    console.print(f"[red]Approval {approval_id} rejected.[/]")

@workspace_app.command("timeline")
def view_timeline(session_id: str) -> None:
    """View the timeline of a session."""
    store = _get_store()
    if not store.get_session(session_id):
        raise NiyamError(f"Session {session_id} not found.")

    timeline = _get_timeline()
    actions = timeline.get_actions(session_id)
    if not actions:
        console.print("No actions found.")
        return

    for a in actions:
        console.print(f"[{a.timestamp}] {a.action_type} by {a.actor}: {a.output or a.input}")

@workspace_app.command("evidence")
def export_evidence(
    session_id: str = typer.Argument(..., help="Session ID"),
    format: str = typer.Option("markdown", help="Export format (markdown or json)"),
) -> None:
    """Export evidence for a workspace session."""
    # Note: we need to pass BrowserStore for evidence if we want to include browser data
    # We will update WorkspaceEvidence to accept BrowserStore shortly
    browser_store = BrowserStore(_get_workspace_dir())
    evidence = WorkspaceEvidence(_get_store(), _get_timeline(), _get_approvals(), browser_store)
    if format == "json":
        data = evidence.generate_json(session_id)
        if not data:
            raise NiyamError(f"Session {session_id} not found.")
        console.print_json(json.dumps(data))
    else:
        text = evidence.generate_markdown(session_id)
        console.print(text)

@workspace_app.command("browser-start")
def browser_start(
    session_id: str = typer.Argument(..., help="Session ID"),
    url: Optional[str] = typer.Option(None, "--url", help="Start URL"),
) -> None:
    """Start a sandboxed browser session."""
    store = _get_store()
    if not store.get_session(session_id):
        raise NiyamError(f"Session {session_id} not found.")

    b_store = BrowserStore(_get_workspace_dir())
    backend = RecorderBrowserBackend(session_id, b_store)
    backend.start(url)

    # Log timeline event
    action = WorkspaceAction(
        id=f"ACT-{uuid.uuid4().hex[:8].upper()}",
        session_id=session_id,
        actor="system",
        action_type="status_change",
        output=f"Browser session started at {url}",
    )
    _get_timeline().log_action(action)
    console.print(f"[green]Browser session started for {session_id}[/]")


@workspace_app.command("browser-action")
def browser_action(
    session_id: str = typer.Argument(..., help="Session ID"),
    type: str = typer.Option(
        ...,
        "--type",
        help="Action type (navigate, click, type, submit, screenshot, extract, wait)",
    ),
    target: Optional[str] = typer.Option(
        None,
        "--target",
        help="Action target (URL or selector)",
    ),
    input: Optional[str] = typer.Option(None, "--input", help="Action input text"),
) -> None:
    """Log a browser action to the workspace timeline and backend."""
    store = _get_store()
    w_session = store.get_session(session_id)
    if not w_session:
        raise NiyamError(f"Session {session_id} not found.")

    b_store = BrowserStore(_get_workspace_dir())
    b_session = b_store.get_session(session_id)
    if not b_session:
        raise NiyamError(f"Browser session for {session_id} not found.")

    backend = RecorderBrowserBackend(session_id, b_store)

    valid_action_types = {
        "navigate",
        "click",
        "type",
        "submit",
        "screenshot",
        "select",
        "extract",
        "wait",
    }
    if type not in valid_action_types:
        raise NiyamError(f"Unsupported browser action type: {type}", code=1)

    if type == "navigate":
        b_action = backend.navigate(target or "")
    elif type == "click":
        b_action = backend.click(target or "")
    elif type == "type":
        b_action = backend.type(target or "", input or "")
    elif type == "submit":
        b_action = backend.submit(target)
    elif type == "screenshot":
        output_path = (
            _get_workspace_dir()
            / "artifacts"
            / session_id
            / "screenshots"
            / f"shot-{uuid.uuid4().hex[:8]}.png"
        )
        b_action = backend.screenshot(output_path)
    else:
        b_action = backend._create_action(type, "low", target=target, input=input)

    # Check if high risk and requires approval
    if b_action.risk in ["high", "critical"]:
        approvals = _get_approvals()
        approval_id = f"APP-{uuid.uuid4().hex[:8].upper()}"
        appr = WorkspaceApproval(
            id=approval_id,
            session_id=session_id,
            action=f"Browser {type} on {target}",
            risk=b_action.risk,
            reason="High risk browser action",
        )
        approvals.request_approval(appr)

        b_action.status = "approval_required"
        b_action.requires_approval = True
        b_action.approval_id = approval_id

        w_session.status = "approval_required"
        store.update_session(w_session)

        timeline_action = WorkspaceAction(
            id=f"ACT-{uuid.uuid4().hex[:8].upper()}",
            session_id=session_id,
            actor="agent",
            action_type="approval_request",
            output=f"Approval requested: Browser {type} on {target}",
            requires_approval=True,
            approval_id=approval_id,
            risk=b_action.risk,
        )
        _get_timeline().log_action(timeline_action)
        b_store.log_action(b_action)
        console.print(f"[yellow]Approval {approval_id} requested for {type}.[/]")
    else:
        b_action.status = "executed"
        b_store.log_action(b_action)

        timeline_action = WorkspaceAction(
            id=f"ACT-{uuid.uuid4().hex[:8].upper()}",
            session_id=session_id,
            actor="agent",
            action_type="command",
            output=f"Executed browser {type} on {target}",
            risk=b_action.risk,
        )
        _get_timeline().log_action(timeline_action)
        console.print(f"[green]Executed {type}.[/]")


@workspace_app.command("browser-pause")
def browser_pause(session_id: str) -> None:
    """Pause a browser session."""
    b_store = BrowserStore(_get_workspace_dir())
    b_session = b_store.get_session(session_id)
    if not b_session:
        raise NiyamError(f"Browser session for {session_id} not found.")
    b_session.status = "paused"
    b_store.save_session(b_session)
    action = WorkspaceAction(
        id=f"ACT-{uuid.uuid4().hex[:8].upper()}",
        session_id=session_id,
        actor="system",
        action_type="status_change",
        output="Browser session paused",
    )
    _get_timeline().log_action(action)
    console.print(f"[yellow]Browser session {session_id} paused.[/]")


@workspace_app.command("browser-resume")
def browser_resume(session_id: str) -> None:
    """Resume a browser session."""
    b_store = BrowserStore(_get_workspace_dir())
    b_session = b_store.get_session(session_id)
    if not b_session:
        raise NiyamError(f"Browser session for {session_id} not found.")
    b_session.status = "running"
    b_store.save_session(b_session)
    action = WorkspaceAction(
        id=f"ACT-{uuid.uuid4().hex[:8].upper()}",
        session_id=session_id,
        actor="system",
        action_type="status_change",
        output="Browser session resumed",
    )
    _get_timeline().log_action(action)
    console.print(f"[green]Browser session {session_id} resumed.[/]")


@workspace_app.command("takeover")
def takeover(
    session_id: str = typer.Argument(..., help="Session ID"),
    by: str = typer.Option(..., "--by", help="User taking over"),
) -> None:
    """Human takeover of a session."""
    store = _get_store()
    w_session = store.get_session(session_id)
    if not w_session:
        raise NiyamError(f"Session {session_id} not found.")

    b_store = BrowserStore(_get_workspace_dir())
    b_session = b_store.get_session(session_id)
    if b_session:
        b_session.status = "takeover"
        b_session.takeover_by = by
        b_store.save_session(b_session)

    w_session.status = "paused"
    store.update_session(w_session)

    action = WorkspaceAction(
        id=f"ACT-{uuid.uuid4().hex[:8].upper()}",
        session_id=session_id,
        actor="system",
        action_type="status_change",
        output=f"Human takeover by {by}",
    )
    _get_timeline().log_action(action)
    console.print(f"[yellow]Human takeover by {by} for session {session_id}.[/]")


@workspace_app.command("release")
def release(
    session_id: str = typer.Argument(..., help="Session ID"),
    by: str = typer.Option(..., "--by", help="User releasing"),
) -> None:
    """Release human takeover of a session."""
    store = _get_store()
    w_session = store.get_session(session_id)
    if not w_session:
        raise NiyamError(f"Session {session_id} not found.")

    b_store = BrowserStore(_get_workspace_dir())
    b_session = b_store.get_session(session_id)
    if b_session:
        b_session.status = "running"
        b_session.takeover_by = None
        b_store.save_session(b_session)

    w_session.status = "running"
    store.update_session(w_session)

    action = WorkspaceAction(
        id=f"ACT-{uuid.uuid4().hex[:8].upper()}",
        session_id=session_id,
        actor="system",
        action_type="status_change",
        output=f"Takeover released by {by}",
    )
    _get_timeline().log_action(action)
    console.print(f"[green]Takeover released by {by} for session {session_id}.[/]")
