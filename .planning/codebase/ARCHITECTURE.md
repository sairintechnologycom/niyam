# Architecture

**Analysis Date:** 2025-05-23

## Pattern Overview

**Overall:** Layered Modular CLI with Adapter-based Orchestration.

**Key Characteristics:**
- **State-driven Execution:** Uses a `.niyam/` directory as the source of truth for workspace configuration, project memory, and mission state.
- **Runtime Isolation via Worktrees:** Leverages `git worktree` to isolate task execution, enabling parallelization and safe rollbacks.
- **Security-First Command Execution:** Implements a strict command allowlist and path validation to prevent shell injection and path traversal during AI-driven operations.

## Layers

**CLI Layer:**
- Purpose: Provides the user interface via subcommands.
- Location: `niyam/cli.py`
- Contains: Typer command definitions and high-level orchestration logic.
- Depends on: `niyam.core`, `niyam.mission`, `niyam.policies`.
- Used by: End users via the `niyam` command.

**Mission Lifecycle Layer:**
- Purpose: Manages the planning, approval, and execution of agentic missions.
- Location: `niyam/mission/`
- Contains: `planner.py`, `executor.py`, `validator.py`, `dashboard.py`.
- Depends on: `niyam.core`, `niyam.runtimes`, `niyam.policies`.
- Used by: `niyam/cli.py`.

**Core Infrastructure Layer:**
- Purpose: Provides shared services like configuration, sync, memory, and security.
- Location: `niyam/core/`
- Contains: `config.py`, `security.py`, `context.py`, `memory.py`, `sync.py`.
- Depends on: External libraries (Pydantic, YAML, Typer).
- Used by: All other layers.

**Runtime Adapter Layer:**
- Purpose: Interfaces with different AI runtimes (Claude, Gemini, Codex).
- Location: `niyam/runtimes/`
- Contains: `base.py` (interface), `claude.py`, `gemini.py`, `codex.py`.
- Depends on: Subprocess/CLI of respective runtimes.
- Used by: `niyam/mission/planner.py` and `niyam/mission/executor.py`.

## Data Flow

**Mission Lifecycle:**

1. **Plan:** `planner.py` uses an LLM (via a runtime adapter) or a template to generate a `mission-plan.yaml` from a requirement.
2. **Approve:** `planner.py` (via `run_mission_approve`) validates the plan and records user approval in `approval.json`.
3. **Execute:** `executor.py` manages the state machine, spinning up `git worktree` instances for tasks, invoking runtimes, and enforcing policy guardrails.
4. **Report:** `reporter.py` aggregates execution logs and cryptographic evidence into a final report.

**State Management:**
- Workspace state is managed in the `.niyam/` directory.
- Configuration is strictly typed using Pydantic models in `niyam/core/config.py`.
- Mission-specific state (runs, tasks, logs) is stored in `.niyam/runs/[mission-id]/`.

## Key Abstractions

**MissionPlan:**
- Purpose: Represents the complete set of tasks and metadata for a requirement.
- Examples: `niyam/core/config.py` (`MissionPlan` model).
- Pattern: Schema-validated YAML.

**Runtime Adapter:**
- Purpose: Abstract interface for interacting with various AI coding assistants.
- Examples: `niyam/runtimes/base.py`, `niyam/runtimes/claude.py`.
- Pattern: Adapter Pattern.

**Guardrail Policy:**
- Purpose: Defines security and safety restrictions for AI operations.
- Examples: `niyam/policies/guard.py`, `niyam/core/security.py`.
- Pattern: Policy-based Access Control (PBAC).

## Entry Points

**CLI Main:**
- Location: `niyam/cli.py`
- Triggers: Execution of the `niyam` command.
- Responsibilities: Routing subcommands, handling global options, and error reporting.

## Error Handling

**Strategy:** Centralized exception handling in the CLI entry point.

**Patterns:**
- **NiyamError:** Base exception class in `niyam/core/errors.py` used for all domain-specific errors.
- **Fail-Fast Validation:** Early validation of configuration and mission plans using Pydantic and `niyam/mission/validator.py`.

## Cross-Cutting Concerns

**Logging:** Uses a dual approach—Rich-based console output for users and JSON-based event logging (`execution-log.json`) for auditing.
**Validation:** Enforced via `niyam/core/security.py` for commands and `niyam/mission/validator.py` for mission plans.
**Authentication:** Managed via environment variables and checked by `niyam/core/doctor.py`.

---

*Architecture analysis: 2025-05-23*
