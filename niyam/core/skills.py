"""Agent Skill Governance core module."""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Literal, Optional
from datetime import datetime
from contextlib import contextmanager

import yaml
from filelock import FileLock
from pydantic import BaseModel, Field

from niyam.core.config import find_niyam_root
from niyam.governance.common.redaction import redact_secrets


class SkillManifest(BaseModel):
    """Declarative manifest for an AI agent skill (parsed from SKILL.md frontmatter)."""

    name: str
    version: str = "1.0.0"
    description: str = ""
    capabilities: list[str] = Field(default_factory=list)
    allowed_paths: list[str] = Field(default_factory=list)
    blocked_paths: list[str] = Field(default_factory=list)
    network_access: list[str] = Field(default_factory=list)
    notes: Optional[str] = None


class RegisteredSkill(BaseModel):
    """A skill registered in the Niyam governance registry."""

    manifest: SkillManifest
    checksum: str
    risk_level: Literal["low", "medium", "high", "critical"]
    approved: bool = False
    registered_at: str
    updated_at: str
    requires_approval: bool = True
    application_id: str | None = None


class SkillRegistry(BaseModel):
    """The local skill registry file model."""

    schema_version: str = "1.0.0"
    skills: dict[str, RegisteredSkill] = Field(default_factory=dict)


def get_skill_registry_path(root: Path | None = None) -> Path:
    """Get the path to the local skill registry file."""
    if root is None:
        root = find_niyam_root()
    if root is None:
        root = Path.cwd()
    return root / ".niyam" / "skill-registry.json"


def get_skill_registry_lock_path(root: Path | None = None) -> Path:
    """Get the lock path used to serialize skill registry writes."""
    return get_skill_registry_path(root).with_suffix(".json.lock")


@contextmanager
def skill_registry_lock(root: Path | None = None):
    """Serialize read-modify-write operations on the skill registry."""
    lock_path = get_skill_registry_lock_path(root)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with FileLock(str(lock_path)):
        yield


def load_skill_registry(root: Path | None = None) -> SkillRegistry:
    """Load the local skill registry from JSON file."""
    path = get_skill_registry_path(root)
    if not path.exists():
        return SkillRegistry()
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return SkillRegistry.model_validate(data)
    except Exception as e:
        raise ValueError(f"Failed to load skill registry at {path}: {e}") from e


def save_skill_registry(
    registry: SkillRegistry, root: Path | None = None, *, locked: bool = False
) -> None:
    """Save the skill registry locally to the JSON file with secret redaction."""
    path = get_skill_registry_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)

    redacted_data = redact_secrets(registry.model_dump())

    def _write() -> None:
        tmp_path = path.with_name(f"{path.name}.tmp.{os.getpid()}")
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(redacted_data, f, indent=2)
            f.write("\n")
        os.replace(tmp_path, path)

    if locked:
        _write()
    else:
        lock_path = get_skill_registry_lock_path(root)
        with FileLock(str(lock_path)):
            _write()


def parse_skill_file(skill_path: Path) -> tuple[SkillManifest, str, str]:
    """Parse SKILL.md for frontmatter and calculate checksum of the prompt content."""
    if not skill_path.exists():
        raise FileNotFoundError(f"Skill file not found at {skill_path}")

    content = skill_path.read_text(encoding="utf-8")
    
    # Extract YAML frontmatter
    # Matches --- (yaml) --- followed by any content
    frontmatter_match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", content, re.DOTALL)
    
    if not frontmatter_match:
        # Default manifest if no frontmatter found
        manifest = SkillManifest(name=skill_path.parent.name)
        prompt_content = content
    else:
        yaml_text = frontmatter_match.group(1)
        prompt_content = frontmatter_match.group(2)
        try:
            data = yaml.safe_load(yaml_text)
            if not isinstance(data, dict):
                data = {}
            if "name" not in data:
                data["name"] = skill_path.parent.name
            manifest = SkillManifest.model_validate(data)
        except Exception as e:
            # Fallback on parse error
            manifest = SkillManifest(name=skill_path.parent.name, notes=f"Frontmatter parse error: {e}")
            prompt_content = content

    checksum = hashlib.sha256(prompt_content.encode("utf-8")).hexdigest()
    return manifest, checksum, prompt_content


def classify_skill_risk(
    manifest: SkillManifest, prompt_content: str
) -> Literal["low", "medium", "high", "critical"]:
    """Classify the risk level of a skill based on requested capabilities and prompt content."""
    
    # 1. Base risk from capabilities
    max_risk_val = 1  # default low
    risk_map = {1: "low", 2: "medium", 3: "high", 4: "critical"}
    
    capability_risks = {
        "run_command": 4,
        "shell_execute": 4,
        "execute": 4,
        "write_file": 3,
        "delete_file": 4,
        "network": 4,
        "secrets_access": 4,
        "read_file": 2,
        "list_directory": 2,
    }

    for cap in manifest.capabilities:
        if cap in capability_risks:
            max_risk_val = max(max_risk_val, capability_risks[cap])

    # 2. Heuristics on prompt content
    text = (prompt_content or "").lower()
    
    critical_patterns = [
        r"\bdelete\s+all\b",
        r"\brm\s+-rf\b",
        r"\bcurl\b",
        r"\bwget\b",
        r"\bdisable\s+safety\b",
        r"\bbypass\s+guardrails\b",
    ]
    
    high_patterns = [
        r"\bdelete\b",
        r"\boverwrite\b",
        r"\bmodify\s+system\b",
    ]

    for p in critical_patterns:
        if re.search(p, text):
            max_risk_val = 4
            break
    
    if max_risk_val < 3:
        for p in high_patterns:
            if re.search(p, text):
                max_risk_val = 3
                break

    return risk_map[max_risk_val]  # type: ignore


def register_skill(
    skill_path: Path,
    root: Path | None = None,
    approved: bool = False,
    application_id: str | None = None,
) -> RegisteredSkill:
    """Parse, classify, and register a skill in the local registry."""
    from niyam.core.applications import require_application

    application_id = require_application(application_id, root)
    manifest, checksum, prompt_content = parse_skill_file(skill_path)
    risk_level = classify_skill_risk(manifest, prompt_content)
    
    now = datetime.now().isoformat()
    
    # High/Critical risk requires approval unless explicitly approved during registration
    requires_approval = risk_level in ("high", "critical")
    if not approved and not requires_approval:
        approved = True  # Auto-approve low/medium risk
        
    skill = RegisteredSkill(
        manifest=manifest,
        checksum=checksum,
        risk_level=risk_level,
        approved=approved,
        registered_at=now,
        updated_at=now,
        requires_approval=requires_approval,
        application_id=application_id,
    )
    
    with skill_registry_lock(root):
        registry = load_skill_registry(root)
        registry.skills[manifest.name] = skill
        save_skill_registry(registry, root, locked=True)
        
    return skill
