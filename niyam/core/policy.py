"""Enterprise Policy Workflows core module."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal, Optional, Any
from contextlib import contextmanager

import yaml
from filelock import FileLock
from pydantic import BaseModel, Field

from niyam.core.config import find_niyam_root
from niyam.governance.common.redaction import redact_secrets


# ── Team Policy Models ──────────────────────────────────────────────────

class PolicyRole(BaseModel):
    """A role within a team policy."""
    name: str
    users: list[str] = Field(default_factory=lambda: ["*"])
    permissions: list[str] = Field(default_factory=list)


class PolicyRule(BaseModel):
    """A granular governance rule."""
    id: str
    type: Literal["block", "warn", "approval_required", "observe"]
    pattern: str
    description: str = ""
    exception_allowed: bool = True


class TeamPolicy(BaseModel):
    """Enterprise team policy configuration."""
    schema_version: str = "1.0.0"
    name: str
    roles: list[PolicyRole] = Field(default_factory=list)
    rules: list[PolicyRule] = Field(default_factory=list)


# ── Policy Exception (Risk Acceptance) Models ──────────────────────────

class PolicyException(BaseModel):
    """A record of an accepted policy violation (Risk Acceptance)."""
    id: str
    rule_id: Optional[str] = None
    pattern: str
    accepted_by: str
    reason: str
    created_at: str
    expires_at: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExceptionRegistry(BaseModel):
    """Registry of active policy exceptions."""
    schema_version: str = "1.0.0"
    exceptions: list[PolicyException] = Field(default_factory=list)


# ── Registry Operations ───────────────────────────────────────────────

def get_exception_registry_path(root: Path | None = None) -> Path:
    """Get the path to the policy exceptions registry."""
    if root is None:
        root = find_niyam_root()
    if root is None:
        root = Path.cwd()
    return root / ".niyam" / "governance" / "policy-exceptions.jsonl"


def get_exception_registry_lock_path(root: Path | None = None) -> Path:
    """Get the lock path for exceptions registry."""
    return get_exception_registry_path(root).with_suffix(".lock")


@contextmanager
def exception_registry_lock(root: Path | None = None):
    """Lock the exceptions registry for atomic writes."""
    lock_path = get_exception_registry_lock_path(root)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with FileLock(str(lock_path)):
        yield


def load_exceptions(root: Path | None = None) -> list[PolicyException]:
    """Load active policy exceptions."""
    path = get_exception_registry_path(root)
    if not path.exists():
        return []
    
    exceptions = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    exceptions.append(PolicyException.model_validate(json.loads(line)))
    except Exception as e:
        # Don't fail the whole mission if exceptions can't be loaded, but log it
        import logging
        logging.getLogger("niyam.policy").error(f"Failed to load exceptions: {e}")
        
    return exceptions


def add_exception(
    exception: PolicyException, root: Path | None = None
) -> None:
    """Add a new policy exception."""
    path = get_exception_registry_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with exception_registry_lock(root):
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(exception.model_dump()) + "\n")


def is_exception_active(
    pattern: str, root: Path | None = None
) -> Optional[PolicyException]:
    """Check if a specific pattern has an active exception."""
    exceptions = load_exceptions(root)
    now = datetime.now(timezone.utc)
    
    for ex in exceptions:
        # Check expiry
        if ex.expires_at:
            try:
                expires = datetime.fromisoformat(ex.expires_at)
                if expires < now:
                    continue
            except ValueError:
                continue
        
        # Check pattern match (simple equality for now, could use regex/glob)
        if ex.pattern == pattern:
            return ex
            
    return None


# ── Policy Loading ───────────────────────────────────────────────────

def load_team_policy(root: Path | None = None) -> Optional[TeamPolicy]:
    """Load the team policy from .niyam/policies/team-policy.yaml."""
    if root is None:
        root = find_niyam_root()
    if root is None:
        return None
        
    path = root / ".niyam" / "policies" / "team-policy.yaml"
    if not path.exists():
        return None
        
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return TeamPolicy.model_validate(data)
    except Exception as e:
        import logging
        logging.getLogger("niyam.policy").error(f"Failed to load team policy: {e}")
        return None
