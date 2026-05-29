# Codebase Structure

**Analysis Date:** 2025-05-23

## Directory Layout

```
sutra/
├── core/           # Core infrastructure and shared services
├── evidence/       # Reporting and cryptographic evidence
├── mission/        # Mission lifecycle management (plan/execute)
├── policies/       # Safety guardrails and policy validation
├── runtimes/       # AI runtime adapters (Claude, Gemini, etc.)
├── templates/      # Workspace profiles and modular packs
└── cli.py          # Main CLI entry point
tests/              # Comprehensive test suite
.sutra/             # Default workspace state directory (local projects)
```

## Directory Purposes

**sutra/core/:**
- Purpose: Infrastructure and shared logic.
- Contains: Configuration models, security primitives, context scanning, project memory, and sync logic.
- Key files: `config.py`, `security.py`, `context.py`, `sync.py`.

**sutra/mission/:**
- Purpose: Single-agent mission lifecycle orchestration.
- Contains: AI-powered planner, task executor with worktree isolation, dashboard, and status reporting.
- Key files: `planner.py`, `executor.py`, `validator.py`, `dashboard.py`.

**sutra/policies/:**
- Purpose: Safety and security guardrails.
- Contains: Command validation, write restriction enforcement, and policy YAML schema validation.
- Key files: `guard.py`, `validator.py`.

**sutra/runtimes/:**
- Purpose: Adapters for external AI coding tools.
- Contains: Base adapter class and implementations for Claude Code, Gemini, and Codex.
- Key files: `base.py`, `claude.py`, `gemini.py`, `codex.py`.

**sutra/templates/:**
- Purpose: Blueprints for workspace initialization.
- Contains: Project profiles (frontend, backend, etc.) and modular packs (A/B testing, security scanning).
- Key files: `packs/`, `profiles/`.

## Key File Locations

**Entry Points:**
- `sutra/cli.py`: Main Typer-based CLI entry point.

**Configuration:**
- `sutra/core/config.py`: Pydantic models for all YAML configuration.

**Core Logic:**
- `sutra/mission/executor.py`: Logic for running tasks, managing worktrees, and enforcing boundaries.
- `sutra/core/context.py`: Repository scanning and architecture metadata extraction.

**Testing:**
- `tests/`: Project-wide tests covering all modules.

## Naming Conventions

**Files:**
- Snake case for all Python files: `planner.py`, `config.py`.
- Kebab case for YAML/Markdown templates: `api-endpoint.yaml`.

**Directories:**
- Plural for collection directories: `runtimes/`, `policies/`, `templates/`.

## Where to Add New Code

**New Feature:**
- Add command to `sutra/cli.py`.
- Implementation in `sutra/core/` or `sutra/mission/` depending on scope.
- Tests in `tests/test_[feature].py`.

**New AI Runtime:**
- Implementation in `sutra/runtimes/[runtime].py` inheriting from `BaseRuntimeAdapter`.
- Register in `sutra/core/config.py` and `sutra/cli.py`.

**New Security Guardrail:**
- Logic in `sutra/policies/guard.py` or `sutra/core/security.py`.
- Configuration in `sutra/core/config.py`.

**New Project Template:**
- Add profile to `sutra/templates/profiles/`.
- Add pack to `sutra/templates/packs/`.

## Special Directories

**.sutra/:**
- Purpose: Stores project-specific Sutra state, context, and mission logs.
- Generated: Yes (via `sutra init`).
- Committed: Yes (typically, except for `runs/` and `worktrees/`).

**.sutra/runs/:**
- Purpose: Contains all files related to specific mission executions.
- Generated: Yes.
- Committed: Optional (usually ignored via `.gitignore`).

---

*Structure analysis: 2025-05-23*
