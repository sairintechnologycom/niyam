# Codebase Structure

**Analysis Date:** 2025-05-23

## Directory Layout

```
niyam/
├── core/           # Core infrastructure and shared services
├── evidence/       # Reporting and cryptographic evidence
├── mission/        # Mission lifecycle management (plan/execute)
├── policies/       # Safety guardrails and policy validation
├── runtimes/       # AI runtime adapters (Claude, Gemini, etc.)
├── templates/      # Workspace profiles and modular packs
└── cli.py          # Main CLI entry point
tests/              # Comprehensive test suite
.niyam/             # Default workspace state directory (local projects)
```

## Directory Purposes

**niyam/core/:**
- Purpose: Infrastructure and shared logic.
- Contains: Configuration models, security primitives, context scanning, project memory, and sync logic.
- Key files: `config.py`, `security.py`, `context.py`, `sync.py`.

**niyam/mission/:**
- Purpose: Single-agent mission lifecycle orchestration.
- Contains: AI-powered planner, task executor with worktree isolation, dashboard, and status reporting.
- Key files: `planner.py`, `executor.py`, `validator.py`, `dashboard.py`.

**niyam/policies/:**
- Purpose: Safety and security guardrails.
- Contains: Command validation, write restriction enforcement, and policy YAML schema validation.
- Key files: `guard.py`, `validator.py`.

**niyam/runtimes/:**
- Purpose: Adapters for external AI coding tools.
- Contains: Base adapter class and implementations for Claude Code, Gemini, and Codex.
- Key files: `base.py`, `claude.py`, `gemini.py`, `codex.py`.

**niyam/templates/:**
- Purpose: Blueprints for workspace initialization.
- Contains: Project profiles (frontend, backend, etc.) and modular packs (A/B testing, security scanning).
- Key files: `packs/`, `profiles/`.

## Key File Locations

**Entry Points:**
- `niyam/cli.py`: Main Typer-based CLI entry point.

**Configuration:**
- `niyam/core/config.py`: Pydantic models for all YAML configuration.

**Core Logic:**
- `niyam/mission/executor.py`: Logic for running tasks, managing worktrees, and enforcing boundaries.
- `niyam/core/context.py`: Repository scanning and architecture metadata extraction.

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
- Add command to `niyam/cli.py`.
- Implementation in `niyam/core/` or `niyam/mission/` depending on scope.
- Tests in `tests/test_[feature].py`.

**New AI Runtime:**
- Implementation in `niyam/runtimes/[runtime].py` inheriting from `BaseRuntimeAdapter`.
- Register in `niyam/core/config.py` and `niyam/cli.py`.

**New Security Guardrail:**
- Logic in `niyam/policies/guard.py` or `niyam/core/security.py`.
- Configuration in `niyam/core/config.py`.

**New Project Template:**
- Add profile to `niyam/templates/profiles/`.
- Add pack to `niyam/templates/packs/`.

## Special Directories

**.niyam/:**
- Purpose: Stores project-specific Niyam state, context, and mission logs.
- Generated: Yes (via `niyam init`).
- Committed: Yes (typically, except for `runs/` and `worktrees/`).

**.niyam/runs/:**
- Purpose: Contains all files related to specific mission executions.
- Generated: Yes.
- Committed: Optional (usually ignored via `.gitignore`).

---

*Structure analysis: 2025-05-23*
