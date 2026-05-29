# Architecture

**Analysis Date:** 2025-05-23

## Pattern Overview

**Overall:** Layered Modular CLI with Adapter-based Orchestration.

**Key Characteristics:**
- **State-driven Execution:** Uses a `.sutra/` directory as the source of truth for workspace configuration, project memory, and mission state.
- **Runtime Isolation via Worktrees:** Leverages `git worktree` to isolate task execution, enabling parallelization and safe rollbacks.
- **Security-First Command Execution:** Implements a strict command allowlist and path validation to prevent shell injection and path traversal during AI-driven operations.

## Layers

**CLI Layer:**
- Purpose: Provides the user interface via subcommands.
- Location: `sutra/cli.py`
- Contains: Typer command definitions and high-level orchestration logic.
- Depends on: `sutra.core`, `sutra.mission`, `sutra.policies`.
- Used by: End users via the `sutra` command.

**Mission Lifecycle Layer:**
- Purpose: Manages the planning, approval, and execution of agentic missions.
- Location: `sutra/mission/`
- Contains: `planner.py`, `executor.py`, `validator.py`, `dashboard.py`.
- Depends on: `sutra.core`, `sutra.runtimes`, `sutra.policies`.
- Used by: `sutra/cli.py`.

**Core Infrastructure Layer:**
- Purpose: Provides shared services like configuration, sync, memory, and security.
- Location: `sutra/core/`
- Contains: `config.py`, `security.py`, `context.py`, `memory.py`, `sync.py`.
- Depends on: External libraries (Pydantic, YAML, Typer).
- Used by: All other layers.

**Runtime Adapter Layer:**
- Purpose: Interfaces with different AI runtimes (Claude, Gemini, Codex).
- Location: `sutra/runtimes/`
- Contains: `base.py` (interface), `claude.py`, `gemini.py`, `codex.py`.
- Depends on: Subprocess/CLI of respective runtimes.
- Used by: `sutra/mission/planner.py` and `sutra/mission/executor.py`.

## Data Flow

**Mission Lifecycle:**

1. **Plan:** `planner.py` uses an LLM (via a runtime adapter) or a template to generate a `mission-plan.yaml` from a requirement.
2. **Approve:** `planner.py` (via `run_mission_approve`) validates the plan and records user approval in `approval.json`.
3. **Execute:** `executor.py` manages the state machine, spinning up `git worktree` instances for tasks, invoking runtimes, and enforcing policy guardrails.
4. **Report:** `reporter.py` aggregates execution logs and cryptographic evidence into a final report.

**State Management:**
- Workspace state is managed in the `.sutra/` directory.
- Configuration is strictly typed using Pydantic models in `sutra/core/config.py`.
- Mission-specific state (runs, tasks, logs) is stored in `.sutra/runs/[mission-id]/`.

## Key Abstractions

**MissionPlan:**
- Purpose: Represents the complete set of tasks and metadata for a requirement.
- Examples: `sutra/core/config.py` (`MissionPlan` model).
- Pattern: Schema-validated YAML.

**Runtime Adapter:**
- Purpose: Abstract interface for interacting with various AI coding assistants.
- Examples: `sutra/runtimes/base.py`, `sutra/runtimes/claude.py`.
- Pattern: Adapter Pattern.

**Guardrail Policy:**
- Purpose: Defines security and safety restrictions for AI operations.
- Examples: `sutra/policies/guard.py`, `sutra/core/security.py`.
- Pattern: Policy-based Access Control (PBAC).

## Entry Points

**CLI Main:**
- Location: `sutra/cli.py`
- Triggers: Execution of the `sutra` command.
- Responsibilities: Routing subcommands, handling global options, and error reporting.

## Error Handling

**Strategy:** Centralized exception handling in the CLI entry point.

**Patterns:**
- **SutraError:** Base exception class in `sutra/core/errors.py` used for all domain-specific errors.
- **Fail-Fast Validation:** Early validation of configuration and mission plans using Pydantic and `sutra/mission/validator.py`.

## Cross-Cutting Concerns

**Logging:** Uses a dual approach—Rich-based console output for users and JSON-based event logging (`execution-log.json`) for auditing.
**Validation:** Enforced via `sutra/core/security.py` for commands and `sutra/mission/validator.py` for mission plans.
**Authentication:** Managed via environment variables and checked by `sutra/core/doctor.py`.

---

*Architecture analysis: 2025-05-23*
