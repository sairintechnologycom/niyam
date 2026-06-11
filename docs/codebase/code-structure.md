# Niyam Code Structure

This is a maintainer-oriented map of the current repository. It complements the generated Graphify files under `graphify-out/`.

## Generated Graph Reference

Graphify was installed as the official PyPI package `graphifyy==0.8.37`.

Generated files:

- `graphify-out/graph.json`
- `graphify-out/GRAPH_TREE.html`
- `graphify-out/sutra-callflow.html`
- `graphify-out/README.md`

The graph was generated from a temporary Python-only mirror of `niyam/` and `tests/` because full-repo extraction requires an LLM API key for Markdown/docs/images. The resulting graph contains Python source/test structure only, not the Markdown docs, YAML rule files, Jinja templates, fixture lockfiles, or images.

## Top-Level Layout

| Path | Purpose |
| --- | --- |
| `niyam/` | Product package and CLI implementation. |
| `niyam/cli/` | Typer command registration and thin CLI adapters. |
| `niyam/core/` | Core engines for workspace setup, scans, guardrails, evidence, memory, packs, CI, PRs, and related business logic. |
| `niyam/mission/` | Mission planning, validation, execution, dashboards, state transitions, reporting, and worktree isolation. |
| `niyam/api/` | FastAPI portal/control-room API. |
| `niyam/governance/` | Readiness scoring, decision logic, rules, and compatibility wrappers. |
| `niyam/policies/` | Guard and policy validation helpers. |
| `niyam/runtimes/` | Runtime adapters for Claude, Codex, and Gemini. |
| `niyam/mcp/` | MCP-compatible Memory Ledger server. |
| `niyam/evidence/` | Evidence reporting namespace. |
| `niyam/templates/` | Profiles, packs, review templates, portal template, evidence templates, and generated workspace files. |
| `docs/` | Human product, architecture, feature, testing, and operational docs. |
| `tests/` | Unit, integration, regression, and e2e tests. |
| `test-fixtures/` | Fixture projects and rules used by scans and e2e tests. |
| `examples/` | Example governance outputs and requirements. |
| `scratch/` | Local experimental/e2e output; not part of stable product surface. |

## CLI Boundary

`niyam/cli/__init__.py` creates the root Typer app, registers command groups, and imports each command module for side-effect registration.

Important behavior:

- Top-level command typo suggestions are generated before execution.
- `NiyamError` exceptions are caught and converted into CLI exit codes.
- The deprecated `sutra` console script points to a warning function.
- Command groups are registered for context, guard, MCP, rules, skills, cost, runtime, policy, pack, memory, mission, review, PR, CI, identity, SaaS, fleet, swarm, and workspace.

Pattern:

- CLI modules parse Typer arguments and options.
- Core/mission modules implement behavior.
- Tests usually exercise both command and core boundaries.

## Core Engines

### Workspace Setup

Files:

- `niyam/core/init.py`
- `niyam/core/setup.py`
- `niyam/core/sync.py`
- `niyam/core/config.py`
- `niyam/core/migrate.py`
- `niyam/core/doctor.py`

Responsibilities:

- Discover `.niyam/` or legacy `.sutra/` roots.
- Load and validate YAML configuration.
- Copy profile templates into a workspace.
- Render runtime-specific instructions.
- Validate the workspace and runtime projections.

### Scanner and Readiness

Files:

- `niyam/core/scan.py`
- `niyam/core/baseline.py`
- `niyam/core/external_scanners.py`
- `niyam/governance/scoring.py`
- `niyam/governance/decision.py`
- `niyam/governance/rules/profiles/*.yaml`

Flow:

1. Load profile or custom YAML rules.
2. Walk relevant text files while excluding metadata, build, vendor, scratch, examples, and usually tests/fixtures.
3. Evaluate declarative match types.
4. Add fingerprints, confidence, remediation effort, and status.
5. Apply baseline acceptance where configured.
6. Compute readiness score and decision.
7. Render CLI, JSON, Markdown, or SARIF output.

### Guard and Security

Files:

- `niyam/core/security.py`
- `niyam/policies/guard.py`
- `niyam/policies/validator.py`

Flow:

1. Load guard policy and selected execution mode.
2. Detect blocked/destructive commands.
3. Enforce path freeze rules.
4. Optionally run command as a subprocess.
5. Redact command/output data.
6. Append JSONL action logs for evidence and portal display.

### MCP Registry and Skills

Files:

- `niyam/core/mcp.py`
- `niyam/core/skills.py`
- `niyam/mcp/memory_server.py`

Flow:

1. Register tools or skills into local governance stores.
2. Infer or validate risk metadata.
3. Preserve existing entries during updates.
4. Use file locks, temp files, and atomic replacement for registry writes.
5. Surface approval and risk state in CLI reports and evidence.

### Cost

Files:

- `niyam/core/cost.py`
- `niyam/mission/task_runner.py`

Flow:

1. Parse or receive model token usage.
2. Validate token counts and status.
3. Apply local pricing tables.
4. Append cost events to JSONL.
5. Aggregate by session, task, model, day, and repo.

### Evidence

Files:

- `niyam/core/evidence.py`
- `niyam/evidence/reporter.py`
- `niyam/templates/evidence_markdown.j2`
- `niyam/templates/evidence_html.j2`
- `niyam/mission/reporter.py`

Flow:

1. Collect requested sections: scan, guard, MCP, cost, memory, workspace, mission, browser, approvals.
2. Represent missing inputs as unavailable/not scanned.
3. Render Markdown/HTML through templates.
4. Include signatures and verification metadata where identity is configured.

### Memory Ledger

Files:

- `niyam/core/memory.py`
- `niyam/core/memory_ledger/local_store.py`
- `niyam/core/memory_ledger/models.py`
- `niyam/core/memory_ledger/manifest.py`
- `niyam/core/memory_ledger/diff.py`
- `niyam/core/memory_ledger/redaction.py`
- `niyam/core/memory_ledger/policy.py`
- `niyam/core/memory_ledger/lineage.py`
- `niyam/core/memory_ledger/recall.py`
- `niyam/mcp/memory_server.py`

Flow:

1. Initialize local JSONL memory stores.
2. Append structured records.
3. Export/import portable manifests.
4. Diff record sets.
5. Redact sensitive content.
6. Check memory policy.
7. Track lineage events.
8. Recall records by query.
9. Serve memory over MCP stdio.

### Control Room Workspace

Files:

- `niyam/core/workspace/models.py`
- `niyam/core/workspace/store.py`
- `niyam/core/workspace/timeline.py`
- `niyam/core/workspace/approvals.py`
- `niyam/core/workspace/browser.py`
- `niyam/core/workspace/evidence.py`

Flow:

1. Create workspace sessions.
2. Persist session state atomically.
3. Append timeline events.
4. Record approval requests and decisions.
5. Track browser actions and takeover state.
6. Export session evidence.

## Mission System

Files:

- `niyam/mission/planner.py`
- `niyam/mission/validator.py`
- `niyam/mission/executor.py`
- `niyam/mission/task_runner.py`
- `niyam/mission/state_machine.py`
- `niyam/mission/worktree.py`
- `niyam/mission/dashboard.py`
- `niyam/mission/reporter.py`
- `niyam/mission/status.py`
- `niyam/mission/utils.py`

Expected control flow:

1. Ingest a requirement or PRD.
2. Build a planner prompt from repo context, templates, runtime overrides, and validation requirements.
3. Parse AI-produced YAML/JSON, or use fallback planning where allowed.
4. Validate task IDs, dependencies, allowed files, and cycles.
5. Persist mission state under `.niyam/runs/`.
6. Approve the plan.
7. Execute dependency layers, using worktrees when enabled.
8. Run hooks and validation commands.
9. Capture logs, acceptance criteria, token usage, and state transitions.
10. Generate evidence, dashboards, timelines, metrics, and audits.

## API Server

Files:

- `niyam/api/server.py`
- `niyam/api/models.py`

Responsibilities:

- Serve the local portal template.
- Provide health, policy, MCP, fleet, swarm, guard, prompt-audit, mission, evidence, SARIF, task-log, approval, and mission-action endpoints.
- Verify `X-Niyam-Token` when configured.
- Read local repo state rather than requiring cloud services.

## Templates

Template areas:

- `niyam/templates/profiles/`: workspace profiles with policies, agents, commands, skills, memory, context, runtime config.
- `niyam/templates/packs/`: modular feature packs.
- `niyam/templates/reviews/`: structured review templates.
- `niyam/templates/evidence_*.j2`: evidence renderers.
- `niyam/templates/portal/index.html`: local portal UI.
- `niyam/templates/init_docs/`: governance docs copied during initialization.

The templates are product surface. Changes here affect what `init`, `sync`, packs, evidence, and runtime integrations produce.

## Tests

Test layout:

- `tests/test_*.py`: unit and integration coverage for core engines and CLI surfaces.
- `tests/e2e/`: end-to-end command behavior and fixture projects.
- `tests/regression/`: compatibility and additive behavior tests.
- `test-fixtures/`: reusable fixture apps and custom rule files.

Validation expectation:

- Run focused tests for touched areas.
- Run the full suite before release-level changes.
- This documentation pass used `uv run niyam --help` as a CLI smoke check and generated Graphify artifacts as structure evidence.

## Current Worktree Caveat

At the time this map was written, the worktree already contained uncommitted changes in:

- `niyam/cli/__init__.py`
- `niyam/core/evidence.py`
- `niyam/core/packs.py`
- `niyam/core/scan.py`
- `niyam/governance/decision.py`
- `niyam/templates/evidence_html.j2`
- `niyam/templates/evidence_markdown.j2`
- `niyam/cli/skills.py`
- `niyam/core/skills.py`
- `tests/test_skills_governance.py`

This document describes the current local state and does not imply those changes are committed.

