"""Enterprise Policy Workflows core module."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal, Optional, Any
from contextlib import contextmanager

import yaml
from filelock import FileLock
from pydantic import BaseModel, Field

from niyam.core.config import find_niyam_root


# ── Team Policy Models ──────────────────────────────────────────────────

class PolicyRole(BaseModel):
    """A role within a team policy."""
    name: str
    users: list[str] = Field(default_factory=lambda: ["*"])
    permissions: list[str] = Field(default_factory=list)


class PolicySelector(BaseModel):
    """Typed attributes used to select an Application or linked inventory object."""

    object_type: Literal[
        "application",
        "model",
        "prompt",
        "dataset",
        "vector-store",
        "knowledge-base",
    ]
    owner: str | None = None
    status: Literal["prototype", "production", "retired"] | None = None
    version: str | None = None
    tag: str | None = None


class PolicyRule(BaseModel):
    """A granular governance rule."""
    id: str
    type: Literal["block", "warn", "approval_required", "observe"]
    pattern: str = ""
    selector: PolicySelector | None = None
    description: str = ""
    exception_allowed: bool = True


class TeamPolicy(BaseModel):
    """Enterprise team policy configuration."""
    schema_version: str = "1.0.0"
    name: str
    roles: list[PolicyRole] = Field(default_factory=list)
    rules: list[PolicyRule] = Field(default_factory=list)


class ApplicationPolicyDecision(BaseModel):
    """One pre-execution Application policy decision."""

    result: Literal["allow", "block", "warn", "approval_required", "observe"]
    rule_id: str | None = None
    reason: str = ""


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
            return TeamPolicy.model_validate(yaml.safe_load(f))
    except Exception as exc:
        raise ValueError(f"Failed to load team policy at {path}: {exc}") from exc


def evaluate_application_policy(
    application_id: str | None, root: Path | None = None
) -> ApplicationPolicyDecision:
    """Evaluate attribute selectors against an Application and its graph objects."""
    try:
        policy = load_team_policy(root)
    except ValueError as exc:
        return ApplicationPolicyDecision(
            result="block", rule_id="policy-invalid", reason=str(exc)
        )
    selector_rules = [rule for rule in policy.rules if rule.selector] if policy else []
    if not selector_rules:
        return ApplicationPolicyDecision(result="allow")
    if not application_id:
        return ApplicationPolicyDecision(
            result="block",
            rule_id="application-context-required",
            reason="Application context is required by attribute policy.",
        )

    try:
        from niyam.core.applications import load_application_registry
        from niyam.core.graph import get_relationships
        from niyam.core.inventory import load_inventory

        application = load_application_registry(root).applications.get(application_id)
        if application is None:
            raise ValueError(f"AI Application '{application_id}' is not registered.")
        subjects = [{"object_type": "application", **application.model_dump()}]
        selected_types = {
            rule.selector.object_type
            for rule in selector_rules
            if rule.selector and rule.selector.object_type != "application"
        }
        if selected_types:
            inventory = load_inventory(root)
            for edge in get_relationships(
                "application", application_id, direction="outgoing", root=root
            ):
                if edge.target_type not in selected_types:
                    continue
                key = f"{edge.target_type}:{edge.target_id}"
                record = inventory.objects.get(key)
                if record is None:
                    raise ValueError(f"Linked inventory object '{key}' is not registered.")
                subjects.append(record.model_dump())
    except Exception as exc:
        return ApplicationPolicyDecision(
            result="block", rule_id="policy-context-invalid", reason=str(exc)
        )

    matches: list[PolicyRule] = []
    for rule in selector_rules:
        selector = rule.selector
        if selector is None:
            continue
        for subject in subjects:
            if subject.get("object_type") != selector.object_type:
                continue
            if selector.owner is not None and subject.get("owner") != selector.owner:
                continue
            if selector.status is not None and subject.get("status") != selector.status:
                continue
            if selector.version is not None and subject.get("version") != selector.version:
                continue
            if selector.tag is not None and selector.tag not in subject.get("tags", []):
                continue
            matches.append(rule)
            break

    if not matches:
        return ApplicationPolicyDecision(result="allow")
    priority = {"block": 4, "approval_required": 3, "warn": 2, "observe": 1}
    rule = max(matches, key=lambda item: priority[item.type])
    return ApplicationPolicyDecision(
        result=rule.type,
        rule_id=rule.id,
        reason=rule.description or f"Application policy '{rule.id}' matched.",
    )
