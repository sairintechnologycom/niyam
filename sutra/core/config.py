"""Pydantic models for all Sutra YAML configuration schemas."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Literal

from pydantic import BaseModel, Field


# ── Constants ──────────────────────────────────────────────────────────

SUTRA_DIR = ".sutra"
SUTRA_YAML = "sutra.yaml"
PROJECT_YAML = "project.yaml"
RUNTIMES_YAML = "runtimes.yaml"

CONTEXT_DIR = "context"
AGENTS_DIR = "agents"
SKILLS_DIR = "skills"
COMMANDS_DIR = "commands"
POLICIES_DIR = "policies"
EVIDENCE_DIR = "evidence"


# ── Guard State ────────────────────────────────────────────────────────


class GuardState(BaseModel):
    """Current guard mode configuration."""

    enabled: bool = False
    careful: bool = False
    frozen_paths: list[str] = Field(default_factory=list)
    remote_policy_url: Optional[str] = None


# ── sutra.yaml ─────────────────────────────────────────────────────────


class SutraConfig(BaseModel):
    """Top-level Sutra workspace configuration."""

    version: str = "0.1.0"
    project_name: str = ""
    profile: str = "fullstack"
    runtimes: list[str] = Field(default_factory=list)
    packs: list[str] = Field(default_factory=list)
    guard: GuardState = Field(default_factory=GuardState)


# ── project.yaml ───────────────────────────────────────────────────────


class StackInfo(BaseModel):
    """Detected technology stack."""

    languages: list[str] = Field(default_factory=list)
    frameworks: list[str] = Field(default_factory=list)
    package_managers: list[str] = Field(default_factory=list)
    databases: list[str] = Field(default_factory=list)


class ValidationCommands(BaseModel):
    """Detected validation commands."""

    build: Optional[str] = None
    test: Optional[str] = None
    lint: Optional[str] = None
    format: Optional[str] = None
    typecheck: Optional[str] = None


class ProjectConfig(BaseModel):
    """Project-specific configuration."""

    name: str = ""
    description: str = ""
    stack: StackInfo = Field(default_factory=StackInfo)
    validation: ValidationCommands = Field(default_factory=ValidationCommands)
    source_dirs: list[str] = Field(default_factory=list)
    test_dirs: list[str] = Field(default_factory=list)


# ── runtimes.yaml ──────────────────────────────────────────────────────


class ClaudeRuntimeConfig(BaseModel):
    """Claude Code runtime-specific settings."""

    generate_claude_md: bool = True
    generate_hooks: bool = True
    generate_settings: bool = True


class CodexRuntimeConfig(BaseModel):
    """Codex CLI runtime-specific settings."""

    generate_agents_md: bool = True


class RuntimesConfig(BaseModel):
    """Runtime adapters configuration."""

    claude: Optional[ClaudeRuntimeConfig] = None
    codex: Optional[CodexRuntimeConfig] = None


# ── Policy schemas ─────────────────────────────────────────────────────


class CommandPolicy(BaseModel):
    """Allow/deny command policy."""

    deny: list[str] = Field(default_factory=list)
    warn: list[str] = Field(default_factory=list)


class ApprovalPolicy(BaseModel):
    """Actions requiring human approval."""

    approval_required_for: list[str] = Field(default_factory=list)


class SecurityPolicy(BaseModel):
    """Security-specific policies."""

    block_secrets_in_code: bool = True
    require_auth_review: bool = True
    require_input_validation: bool = True
    deny_write_patterns: list[str] = Field(default_factory=list)
    allow_write_patterns: list[str] = Field(default_factory=list)


class EvidencePolicy(BaseModel):
    """Evidence collection requirements."""

    require_diff_summary: bool = True
    require_validation_results: bool = True
    require_policy_events: bool = True


# ── Task & Mission Plan schemas ───────────────────────────────────────


class TaskContract(BaseModel):
    """Pydantic model for task contracts to enforce schema and defaults."""

    model_config = {"extra": "allow"}

    id: str
    title: str
    type: Literal["discovery", "implementation", "review", "validation"]
    status: Literal["pending", "running", "completed", "failed", "paused", "skipped"]
    agent: str
    runtime: Optional[str] = None
    depends_on: list[str] = Field(default_factory=list)
    files_allowed: list[str] = Field(default_factory=lambda: ["*"])
    writes_files: bool = True
    timeout_seconds: int = 600
    risk: Literal["low", "medium", "high"] = "medium"


class MissionMeta(BaseModel):
    """Pydantic model for mission metadata."""

    model_config = {"extra": "allow"}

    id: str
    requirement: str
    created: str
    status: str
    orchestrator: str
    parallel: int = 1


class MissionPlan(BaseModel):
    """Pydantic model for the complete mission-plan.yaml schema."""

    model_config = {"extra": "allow"}

    mission: MissionMeta
    tasks: list[TaskContract]


# ── Helpers ────────────────────────────────────────────────────────────


def get_sutra_dir(repo_root: Path | None = None) -> Path:
    """Get the .sutra directory path."""
    root = repo_root or Path.cwd()
    return root / SUTRA_DIR


def find_sutra_root(start: Path | None = None) -> Path | None:
    """Walk up from start to find a directory containing .sutra/."""
    current = start or Path.cwd()
    for parent in [current, *current.parents]:
        if (parent / SUTRA_DIR).is_dir():
            return parent
    return None


def load_sutra_config(repo_root: Path | None = None) -> SutraConfig:
    """Load and validate sutra.yaml."""
    from sutra.core.security import safe_load_yaml

    sutra_dir = get_sutra_dir(repo_root)
    config_path = sutra_dir / SUTRA_YAML
    data = safe_load_yaml(config_path)
    return SutraConfig(**data)


def save_sutra_config(config: SutraConfig, repo_root: Path | None = None) -> None:
    """Save sutra.yaml."""
    import yaml

    sutra_dir = get_sutra_dir(repo_root)
    config_path = sutra_dir / SUTRA_YAML

    with open(config_path, "w") as f:
        yaml.dump(
            config.model_dump(exclude_none=True),
            f,
            default_flow_style=False,
            sort_keys=False,
        )


def load_project_config(repo_root: Path | None = None) -> ProjectConfig:
    """Load and validate project.yaml."""
    from sutra.core.security import safe_load_yaml

    sutra_dir = get_sutra_dir(repo_root)
    config_path = sutra_dir / PROJECT_YAML
    data = safe_load_yaml(config_path)
    return ProjectConfig(**data)


def load_runtimes_config(repo_root: Path | None = None) -> RuntimesConfig:
    """Load and validate runtimes.yaml."""
    from sutra.core.security import safe_load_yaml

    sutra_dir = get_sutra_dir(repo_root)
    config_path = sutra_dir / RUNTIMES_YAML
    data = safe_load_yaml(config_path)
    return RuntimesConfig(**data)
