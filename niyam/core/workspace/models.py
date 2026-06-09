"""Workspace models for Niyam."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class WorkspaceSession(BaseModel):
    id: str
    title: str
    objective: Optional[str] = None
    agent_type: Literal["manual", "cli", "code", "browser", "mcp"]
    status: Literal[
        "created", "running", "paused", "approval_required", "completed", "failed"
    ]
    risk: Literal["low", "medium", "high", "critical"]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    owner: Optional[str] = None
    memory_refs: List[str] = Field(default_factory=list)
    evidence_refs: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorkspaceAction(BaseModel):
    id: str
    session_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    actor: Literal["human", "agent", "system"]
    action_type: Literal[
        "prompt",
        "tool_call",
        "command",
        "file_change",
        "approval_request",
        "approval_decision",
        "memory_recall",
        "memory_write",
        "output",
        "error",
        "status_change",
    ]
    target: Optional[str] = None
    input: Optional[str] = None
    output: Optional[str] = None
    risk: Literal["low", "medium", "high", "critical"] = "low"
    requires_approval: bool = False
    approval_id: Optional[str] = None
    approved_by: Optional[str] = None
    redacted: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorkspaceApproval(BaseModel):
    id: str
    session_id: str
    action: str
    reason: Optional[str] = None
    risk: Literal["low", "medium", "high", "critical"] = "medium"
    status: Literal["pending", "approved", "rejected"] = "pending"
    requested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    decided_at: Optional[datetime] = None
    requested_by: Optional[str] = None
    decided_by: Optional[str] = None

class BrowserSession(BaseModel):
    id: str
    workspace_session_id: str
    status: Literal["created", "running", "paused", "takeover", "completed", "failed"]
    start_url: Optional[str] = None
    current_url: Optional[str] = None
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    takeover_by: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BrowserAction(BaseModel):
    id: str
    browser_session_id: str
    workspace_session_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    action_type: Literal[
        "navigate",
        "click",
        "type",
        "select",
        "submit",
        "screenshot",
        "extract",
        "wait",
    ]
    target: Optional[str] = None
    input: Optional[str] = None
    output: Optional[str] = None
    url_before: Optional[str] = None
    url_after: Optional[str] = None
    risk: Literal["low", "medium", "high", "critical"]
    requires_approval: bool = False
    approval_id: Optional[str] = None
    status: Literal[
        "recorded", "approval_required", "approved", "rejected", "executed", "failed"
    ]
    redacted: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)
