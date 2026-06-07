"""Autonomous workspace swarm coordination and resource locking."""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import List, Optional, Dict, Literal
from pydantic import BaseModel, Field
from filelock import FileLock
from contextlib import contextmanager

from niyam.core.config import get_niyam_dir


# ── Constants ──────────────────────────────────────────────────────────

STALE_HEARTBEAT_TIMEOUT = 60  # seconds

AgentStatus = Literal["idle", "busy", "waiting", "offline"]
LedgerAction = Literal["request_lock", "yield_lock", "deny_lock", "handoff", "info"]


# ── Models ───────────────────────────────────────────────────────────


class SwarmAgent(BaseModel):
    """An active agent participating in the swarm."""
    id: str
    role: str
    status: AgentStatus = "idle"
    current_task: Optional[str] = None
    last_seen: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ResourceLock(BaseModel):
    """An exclusive lock on a file resource."""
    resource_path: str
    agent_id: str
    acquired_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    reason: Optional[str] = None


class LedgerMessage(BaseModel):
    """A coordination message between agents."""
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    sender: str
    receiver: str
    action: LedgerAction
    resource: Optional[str] = None
    payload: Dict = Field(default_factory=dict)


class SwarmState(BaseModel):
    """Global state of the autonomous workspace swarm."""
    agents: Dict[str, SwarmAgent] = Field(default_factory=dict)
    locks: Dict[str, ResourceLock] = Field(default_factory=dict)


# ── State Management ──────────────────────────────────────────────────


def get_swarm_dir(repo_root: Path | None = None) -> Path:
    """Get the swarm state directory."""
    swarm_dir = get_niyam_dir(repo_root) / "swarm"
    swarm_dir.mkdir(parents=True, exist_ok=True)
    return swarm_dir


@contextmanager
def swarm_state_lock(repo_root: Path | None = None, timeout: int = 10):
    """Context manager for thread-safe/process-safe access to swarm state."""
    lock_path = get_swarm_dir(repo_root) / "state.json.lock"
    lock = FileLock(lock_path, timeout=timeout)
    with lock:
        yield


def load_swarm_state(repo_root: Path | None = None) -> SwarmState:
    """Load the current swarm state from disk."""
    state_path = get_swarm_dir(repo_root) / "state.json"
    if not state_path.exists():
        return SwarmState()
    
    try:
        with open(state_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return SwarmState(**data)
    except Exception:
        return SwarmState()


def save_swarm_state(state: SwarmState, repo_root: Path | None = None) -> None:
    """Save the swarm state to disk atomically."""
    swarm_dir = get_swarm_dir(repo_root)
    state_path = swarm_dir / "state.json"
    temp_path = swarm_dir / "state.json.tmp"
    
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(state.model_dump(), f, indent=2)
    
    os.replace(temp_path, state_path)


def is_agent_stale(agent: SwarmAgent) -> bool:
    """Check if an agent has missed its heartbeat timeout."""
    try:
        last_seen = datetime.fromisoformat(agent.last_seen)
        # Handle both offset-aware and naive datetimes
        if last_seen.tzinfo is None:
            last_seen = last_seen.replace(tzinfo=timezone.utc)
        
        diff = (datetime.now(timezone.utc) - last_seen).total_seconds()
        return diff > STALE_HEARTBEAT_TIMEOUT
    except Exception:
        return True


# ── Locking Primitives ────────────────────────────────────────────────


def _normalize_resource_path(resource_path: str) -> str:
    """Normalize a resource path to a canonical POSIX string.
    
    Replaces backslashes with forward slashes before Path conversion
    so that Windows-style paths are correctly normalized on POSIX systems.
    """
    return str(PurePosixPath(resource_path.replace("\\", "/")))


def acquire_lock(
    resource_path: str, 
    agent_id: str, 
    reason: Optional[str] = None,
    repo_root: Path | None = None
) -> bool:
    """Attempt to acquire an exclusive lock on a resource. Automatically recovers from dead agents."""
    with swarm_state_lock(repo_root):
        state = load_swarm_state(repo_root)
        
        # Normalize path
        res_key = _normalize_resource_path(resource_path)
        
        if res_key in state.locks:
            existing_lock = state.locks[res_key]
            
            # 1. If held by self, just return True
            if existing_lock.agent_id == agent_id:
                return True
                
            # 2. Check if current holder is stale
            holder_id = existing_lock.agent_id
            if holder_id in state.agents:
                if is_agent_stale(state.agents[holder_id]):
                    # Holder is dead! Release their locks and grant to self.
                    _release_all_locks_internal(state, holder_id)
                else:
                    return False  # Held by active agent
            else:
                # Holder is not in agents list? Treat as dead.
                del state.locks[res_key]

        # 3. Create new lock
        state.locks[res_key] = ResourceLock(
            resource_path=res_key,
            agent_id=agent_id,
            reason=reason
        )
        save_swarm_state(state, repo_root)
        return True


def release_lock(
    resource_path: str, 
    agent_id: str,
    repo_root: Path | None = None
) -> bool:
    """Release a held lock."""
    with swarm_state_lock(repo_root):
        state = load_swarm_state(repo_root)
        res_key = _normalize_resource_path(resource_path)
        
        if res_key in state.locks:
            lock = state.locks[res_key]
            if lock.agent_id == agent_id:
                del state.locks[res_key]
                save_swarm_state(state, repo_root)
                return True
                
        return False


def release_all_locks(agent_id: str, repo_root: Path | None = None) -> int:
    """Release all locks held by a specific agent."""
    with swarm_state_lock(repo_root):
        state = load_swarm_state(repo_root)
        count = _release_all_locks_internal(state, agent_id)
        if count > 0:
            save_swarm_state(state, repo_root)
        return count


def _release_all_locks_internal(state: SwarmState, agent_id: str) -> int:
    """Internal helper to remove all locks for an agent from state (no save)."""
    to_remove = [k for k, v in state.locks.items() if v.agent_id == agent_id]
    for k in to_remove:
        del state.locks[k]
    return len(to_remove)


# ── Ledger Operations ─────────────────────────────────────────────────


def append_ledger_message(
    sender: str,
    receiver: str,
    action: LedgerAction,
    resource: Optional[str] = None,
    payload: Optional[Dict] = None,
    repo_root: Path | None = None
) -> None:
    """Append a coordination message to the swarm ledger (lock-protected)."""
    message = LedgerMessage(
        sender=sender,
        receiver=receiver,
        action=action,
        resource=resource,
        payload=payload or {}
    )
    
    with swarm_state_lock(repo_root):
        ledger_path = get_swarm_dir(repo_root) / "ledger.jsonl"
        with open(ledger_path, "a", encoding="utf-8") as f:
            f.write(message.model_dump_json() + "\n")


def load_ledger_messages(repo_root: Path | None = None) -> List[LedgerMessage]:
    """Load all messages from the swarm ledger."""
    ledger_path = get_swarm_dir(repo_root) / "ledger.jsonl"
    if not ledger_path.exists():
        return []
        
    messages = []
    with open(ledger_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    messages.append(LedgerMessage(**json.loads(line)))
                except Exception:
                    continue
    return messages


def get_pending_requests(repo_root: Path | None = None) -> List[LedgerMessage]:
    """Get unresolved lock requests (request_lock without a matching yield/deny)."""
    messages = load_ledger_messages(repo_root)
    
    # Track which request_lock messages have been resolved
    pending: Dict[str, LedgerMessage] = {}  # key: "sender:resource"
    
    for msg in messages:
        if msg.action == "request_lock" and msg.resource:
            key = f"{msg.sender}:{msg.resource}"
            pending[key] = msg
        elif msg.action in ("yield_lock", "deny_lock") and msg.resource:
            # A yield/deny from the receiver resolves the matching request
            key = f"{msg.receiver}:{msg.resource}"
            pending.pop(key, None)
    
    return list(pending.values())


# ── Agent Management ──────────────────────────────────────────────────


VALID_AGENT_STATUSES = {"idle", "busy", "waiting", "offline"}


def heartbeat(
    agent_id: str,
    role: str,
    status: AgentStatus = "idle",
    task_id: Optional[str] = None,
    repo_root: Path | None = None,
) -> None:
    """Update an agent's heartbeat in the swarm state."""
    if status not in VALID_AGENT_STATUSES:
        raise ValueError(
            f"Invalid agent status '{status}'. Must be one of: {', '.join(sorted(VALID_AGENT_STATUSES))}"
        )
    
    with swarm_state_lock(repo_root):
        state = load_swarm_state(repo_root)
        
        agent = SwarmAgent(
            id=agent_id,
            role=role,
            status=status,
            current_task=task_id,
            last_seen=datetime.now(timezone.utc).isoformat()
        )
        state.agents[agent_id] = agent
        save_swarm_state(state, repo_root)


def deregister_agent(agent_id: str, repo_root: Path | None = None) -> bool:
    """Gracefully remove an agent from the swarm and release all its locks.
    
    Returns True if the agent was found and removed, False otherwise.
    """
    with swarm_state_lock(repo_root):
        state = load_swarm_state(repo_root)
        
        if agent_id not in state.agents:
            return False
        
        _release_all_locks_internal(state, agent_id)
        del state.agents[agent_id]
        save_swarm_state(state, repo_root)
        return True


def prune_stale_agents(repo_root: Path | None = None) -> int:
    """Remove agents that have missed their heartbeat and release their locks."""
    with swarm_state_lock(repo_root):
        state = load_swarm_state(repo_root)
        stale_ids = [agent_id for agent_id, agent in state.agents.items() if is_agent_stale(agent)]
        
        for agent_id in stale_ids:
            _release_all_locks_internal(state, agent_id)
            del state.agents[agent_id]
            
        if stale_ids:
            save_swarm_state(state, repo_root)
            
        return len(stale_ids)
