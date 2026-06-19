"""Pydantic models for all Niyam YAML configuration schemas."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Literal

from pydantic import BaseModel, Field, AliasChoices


# ── Constants ──────────────────────────────────────────────────────────

NIYAM_DIR = ".niyam"
NIYAM_YAML = "niyam.yaml"
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
    """Legacy guard state configuration.

    Controls simple enable/disable toggles, destructive warning careful mode,
    path freezing restrictions, and remote policy URL endpoint. Used primarily
    by 'niyam guard enable/disable/careful/freeze' commands.
    """

    enabled: bool = False
    careful: bool = False
    frozen_paths: list[str] = Field(default_factory=list)
    remote_policy_url: Optional[str] = None


# ── niyam.yaml ─────────────────────────────────────────────────────────


class ScanConfig(BaseModel):
    """Configuration for local repository scanning."""

    profile: str = "startup"
    fail_on: list[str] = Field(default_factory=list)
    include: list[str] = Field(default_factory=list)
    min_test_coverage: Optional[float] = None


class GuardConfig(BaseModel):
    """Configuration for new governance guard policies.

    Defines active governance policy enforcement mode (observe, block, warn, approve),
    along with lists of blocked commands, protected files, and commands requiring human approval.
    Used by the modern governance 'niyam guard run' engine.
    """

    mode: str = "observe"
    blocked_commands: list[str] = Field(default_factory=list)
    protected_files: list[str] = Field(default_factory=list)
    approval_required: list[str] = Field(default_factory=list)
    mission_approval_roles: list[str] = Field(default_factory=lambda: ["default"])


class SaaSConfig(BaseModel):
    """Configuration for Niyam Dashboard integration."""

    enabled: bool = False
    base_url: str = "https://api.niyam.ai"
    api_key: Optional[str] = None
    project_id: Optional[str] = None
    organization_id: Optional[str] = None
    pricing_url: Optional[str] = None


class BudgetConfig(BaseModel):
    """Configuration for token and cost budget enforcement."""

    max_mission_cost_usd: Optional[float] = None
    max_task_cost_usd: Optional[float] = None
    max_mission_tokens: Optional[int] = None
    max_task_tokens: Optional[int] = None



class GovernanceConfig(BaseModel):
    """Governance and production-readiness configuration."""

    scan: ScanConfig = Field(default_factory=ScanConfig)
    guard: GuardConfig = Field(default_factory=GuardConfig)
    budget: BudgetConfig = Field(default_factory=BudgetConfig)


class NiyamConfig(BaseModel):
    """Top-level Niyam workspace configuration."""

    model_config = {"extra": "allow"}

    version: str = "0.1.0"
    project_name: str = ""
    profile: str = "fullstack"
    runtimes: list[str] = Field(default_factory=list)
    packs: list[str] = Field(default_factory=list)
    guard: GuardState = Field(default_factory=GuardState)
    governance: Optional[GovernanceConfig] = None
    saas: SaaSConfig = Field(default_factory=SaaSConfig)
    show_marketing_metrics: bool = False
    baseline_multiplier: float = 5.0


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


class TaskValidationConfig(BaseModel):
    """Validation commands configuration for a task."""

    commands: list[str] = Field(default_factory=list)


class TaskContract(BaseModel):
    """Pydantic model for task contracts to enforce schema and defaults."""

    model_config = {"extra": "forbid"}

    id: str
    title: str
    type: Literal["discovery", "implementation", "review", "validation", "recovery"]
    status: Literal[
        "planned",
        "approved",
        "queued",
        "preparing",
        "awaiting_approval",
        "running",
        "validating",
        "reviewing",
        "merging",
        "blocked",
        "needs_human",
        "retry_ready",
        "completed",
        "failed",
        "skipped",
        "cancelled",
        "rolled_back",
    ]
    agent: str
    runtime: Optional[str] = None
    depends_on: list[str] = Field(default_factory=list)
    allowed_files: list[str] = Field(
        default_factory=lambda: ["*"],
        validation_alias=AliasChoices("allowed_files", "files_allowed"),
    )
    blocked_files: list[str] = Field(default_factory=list)
    writes_files: bool = True
    timeout_seconds: int = Field(
        default=600, validation_alias=AliasChoices("timeout_seconds", "timeout")
    )
    risk: Literal["low", "medium", "high"] = "medium"
    objective: str = ""
    acceptance_criteria: list[str] = Field(default_factory=list)
    validation: TaskValidationConfig = Field(default_factory=TaskValidationConfig)
    approval_required: bool = False
    tdd_required: Optional[bool] = None
    commit_sha: Optional[str] = None
    healing_prompt: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 2
    retry_policy: Literal["auto", "manual", "none"] = "auto"
    version: str = "1.0"
    evidence_refs: list[str] = Field(default_factory=list)


class MissionMeta(BaseModel):
    """Pydantic model for mission metadata."""

    model_config = {"extra": "allow"}

    id: str
    schema_version: str = "1.0"
    requirement: str
    created: str
    status: Literal[
        "planned",
        "approved",
        "running",
        "paused",
        "completed",
        "failed",
        "cancelled",
        "rolled_back",
    ]
    orchestrator: str
    parallel: int = 1
    worktree: bool = True
    auto_heal: bool = False
    base_sha: Optional[str] = None


class MissionPlan(BaseModel):
    """Pydantic model for the complete mission-plan.yaml schema."""

    model_config = {"extra": "allow"}

    mission: MissionMeta
    tasks: list[TaskContract]


# ── Helpers ────────────────────────────────────────────────────────────


def get_niyam_dir(repo_root: Path | None = None) -> Path:
    """Get the .niyam directory path."""
    root = repo_root or Path.cwd()
    niyam_dir = root / NIYAM_DIR
    if not niyam_dir.is_dir() and (root / ".sutra").is_dir():
        return root / ".sutra"
    return niyam_dir


def find_niyam_root(start: Path | None = None) -> Path | None:
    """Walk up from start to find a directory containing .niyam/ or .sutra/."""
    current = start or Path.cwd()
    for parent in [current, *current.parents]:
        if (parent / NIYAM_DIR).is_dir():
            return parent
    for parent in [current, *current.parents]:
        if (parent / ".sutra").is_dir():
            import sys

            sys.stderr.write(
                "WARNING: Legacy .sutra/ directory found. Please migrate by running:\n  niyam migrate --from-sutra\n\n"
            )
            return parent
    return None


def load_niyam_config(repo_root: Path | None = None) -> NiyamConfig:
    """Load and validate niyam.yaml with environment variable overrides."""
    import os
    from niyam.core.security import safe_load_yaml

    niyam_dir = get_niyam_dir(repo_root)
    config_path = niyam_dir / NIYAM_YAML
    if not config_path.exists() and (niyam_dir / "sutra.yaml").exists():
        config_path = niyam_dir / "sutra.yaml"
    data = safe_load_yaml(config_path) or {}

    # Overlay environment variable overrides for SaaS configuration
    if "saas" not in data or data["saas"] is None:
        data["saas"] = {}

    saas = data["saas"]

    env_enabled = os.getenv("NIYAM_SAAS_ENABLED")
    if env_enabled is not None:
        saas["enabled"] = env_enabled.lower() in ("true", "1", "yes")

    env_base_url = os.getenv("NIYAM_SAAS_BASE_URL")
    if env_base_url is not None:
        saas["base_url"] = env_base_url

    env_api_key = os.getenv("NIYAM_SAAS_API_KEY")
    if env_api_key is not None:
        saas["api_key"] = env_api_key

    env_project_id = os.getenv("NIYAM_SAAS_PROJECT_ID")
    if env_project_id is not None:
        saas["project_id"] = env_project_id

    env_org_id = os.getenv("NIYAM_SAAS_ORGANIZATION_ID")
    if env_org_id is not None:
        saas["organization_id"] = env_org_id

    env_pricing_url = os.getenv("NIYAM_SAAS_PRICING_URL")
    if env_pricing_url is not None:
        saas["pricing_url"] = env_pricing_url

    return NiyamConfig(**data)


def save_niyam_config(config: NiyamConfig, repo_root: Path | None = None) -> None:
    """Save niyam.yaml."""
    import yaml

    niyam_dir = get_niyam_dir(repo_root)
    config_path = niyam_dir / NIYAM_YAML

    with open(config_path, "w") as f:
        yaml.dump(
            config.model_dump(exclude_none=True),
            f,
            default_flow_style=False,
            sort_keys=False,
        )


def load_project_config(repo_root: Path | None = None) -> ProjectConfig:
    """Load and validate project.yaml."""
    from niyam.core.security import safe_load_yaml

    niyam_dir = get_niyam_dir(repo_root)
    config_path = niyam_dir / PROJECT_YAML
    data = safe_load_yaml(config_path)
    return ProjectConfig(**data)


def load_runtimes_config(repo_root: Path | None = None) -> RuntimesConfig:
    """Load and validate runtimes.yaml."""
    from niyam.core.security import safe_load_yaml

    niyam_dir = get_niyam_dir(repo_root)
    config_path = niyam_dir / RUNTIMES_YAML
    data = safe_load_yaml(config_path)
    return RuntimesConfig(**data)
