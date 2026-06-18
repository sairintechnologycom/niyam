# Niyam Feature Catalog

This document records the features present in the current codebase and how each feature is expected to work. It is based on the CLI registration in `niyam/cli/`, the implementation modules under `niyam/core/`, `niyam/mission/`, `niyam/api/`, and the existing product docs.

Generated reference artifacts:

- `graphify-out/graph.json`: Graphify code graph for Python source and tests.
- `graphify-out/GRAPH_TREE.html`: Browsable code graph tree.
- `graphify-out/sutra-callflow.html`: Graphify call-flow HTML.
- `docs/codebase/code-structure.md`: Human-readable structure map.

## Product Model

Niyam is a local-first AgentOps control plane for governed AI-assisted development. A repository becomes a governed workspace through a `.niyam/` directory that stores configuration, runtime projections, context, memory, policies, logs, mission state, approvals, and evidence. The CLI is the primary interface; the Portal API and workspace/session modules expose the same local state to dashboard-style tooling.

## Workspace Bootstrap and Runtime Sync

Commands:

- `niyam init`
- `niyam setup`
- `niyam sync`
- `niyam migrate --from-sutra`
- `niyam runtime add`
- `niyam doctor`
- `niyam info`

Expected behavior:

- `init` creates a `.niyam/` workspace from a selected profile such as `fullstack`, `backend`, `frontend`, `startup-saas`, `platform-engineering`, or `governed-enterprise`.
- `setup` runs an interactive onboarding flow.
- `sync` projects the `.niyam/` source of truth into runtime-specific files for Claude, Codex, and Gemini.
- `migrate --from-sutra` copies or moves a legacy `.sutra/` workspace into `.niyam/` while preserving compatibility.
- `runtime add` enables an additional runtime adapter.
- `doctor` validates workspace structure, runtime projections, and optionally configured lint/test checks.
- `info` reports version, system, and workspace status.

Primary code:

- `niyam/cli/main_cmds.py`
- `niyam/core/init.py`
- `niyam/core/setup.py`
- `niyam/core/sync.py`
- `niyam/core/migrate.py`
- `niyam/core/doctor.py`
- `niyam/runtimes/`

## Project Context

Commands:

- `niyam context refresh`
- `niyam context show`
- `niyam context diff`
- `niyam context add`
- `niyam context list`
- `niyam context remove`

Expected behavior:

- Context refresh scans the repository and writes project context files under `.niyam/context/`.
- Show and diff expose the cached context and changes since the last refresh.
- Add/list/remove manage custom context files that should be included for AI agents.

Primary code:

- `niyam/cli/context.py`
- `niyam/core/context.py`

## Mission Planning and Execution

Commands:

- `niyam run`
- `niyam plan`
- `niyam status`
- `niyam dashboard`
- `niyam watch`
- `niyam next`
- `niyam replan`
- `niyam mission ingest`
- `niyam mission plan`
- `niyam mission show`
- `niyam mission explain`
- `niyam mission dashboard`
- `niyam mission validate-plan`
- `niyam mission approve`
- `niyam mission start`
- `niyam mission status`
- `niyam mission pause`
- `niyam mission resume`
- `niyam mission retry`
- `niyam mission replan`
- `niyam mission skip`
- `niyam mission rollback`
- `niyam mission report`
- `niyam mission verify-report`
- `niyam mission active`
- `niyam mission next`
- `niyam mission inspect`
- `niyam mission timeline`
- `niyam mission metrics`
- `niyam mission audit`
- `niyam mission approve-task`
- `niyam mission reject-task`

Expected behavior:

- `run` is the high-level workflow: refresh context, sync runtimes, plan a mission, approve it, and start execution.
- Mission planning turns a requirement or PRD into a structured task graph with dependencies, allowed file scopes, validation commands, and approval metadata.
- Execution runs tasks in dependency order, optionally in parallel and optionally isolated by Git worktrees.
- The mission state machine records status transitions and timelines.
- Pause/resume/retry/skip/rollback/replan operate on the active or selected mission.
- Reports and verification produce evidence for the mission, including changed files, validations, logs, and signatures where identity is configured.

Primary code:

- `niyam/cli/main_cmds.py`
- `niyam/cli/mission.py`
- `niyam/mission/planner.py`
- `niyam/mission/executor.py`
- `niyam/mission/task_runner.py`
- `niyam/mission/state_machine.py`
- `niyam/mission/dashboard.py`
- `niyam/mission/reporter.py`
- `niyam/mission/validator.py`
- `niyam/mission/worktree.py`

## Repository Readiness Scan

Commands:

- `niyam scan`
- `niyam rules list`

Expected behavior:

- `scan` evaluates a target path against a profile such as `startup`, `team`, `enterprise`, or `regulated`.
- Rules are YAML-defined and support file existence, missing files, filename patterns, directory checks, content inclusion, content regex, and content-missing checks.
- The scanner skips build/cache/vendor directories and can optionally include tests/fixtures when requested by implementation paths.
- Results produce findings with severity, category, recommendations, confidence, remediation effort, and stable fingerprints.
- Scoring computes readiness from findings and emits `GO`, `CONDITIONAL_GO`, `HIGH_RISK`, or `NO_GO`.
- Output formats include text, JSON, Markdown, and SARIF; `--report-file` writes the selected report.
- Baseline support accepts known findings while surfacing newly introduced issues.

Primary code:

- `niyam/cli/scan.py`
- `niyam/core/scan.py`
- `niyam/core/baseline.py`
- `niyam/core/external_scanners.py`
- `niyam/governance/scoring.py`
- `niyam/governance/decision.py`
- `niyam/governance/rules/profiles/*.yaml`

## Guardrails and Command Observation

Commands:

- `niyam guard enable`
- `niyam guard disable`
- `niyam guard careful`
- `niyam guard freeze`
- `niyam guard run`
- `niyam guard observe`
- `niyam guard verify-commit`
- `niyam guard status`
- `niyam guard logs`
- `niyam guard policy`

Expected behavior:

- Guard wraps shell commands and enforces modes such as observe, warn, block, and approve.
- Dangerous command patterns are detected before execution.
- Captured output is redacted before it is written to logs.
- Path freeze rules block edits to protected paths and can be verified during commit flows.
- Logs are append-only JSONL records under `.niyam/logs/` and feed evidence generation.

Primary code:

- `niyam/cli/guard.py`
- `niyam/core/security.py`
- `niyam/policies/guard.py`
- `niyam/policies/validator.py`

## MCP and Tool Registry Governance

Commands:

- `niyam mcp register`
- `niyam mcp register-memory-server`
- `niyam mcp list`
- `niyam mcp show`
- `niyam mcp approve`
- `niyam mcp approve-all`
- `niyam mcp risk-report`

Expected behavior:

- MCP and external tools are registered in `.niyam/mcp-registry.json`.
- Registration stores tool type, command or URL, owner, capabilities, access characteristics, risk level, approval state, and notes.
- Risk is either explicit or inferred from capabilities and access.
- Registry writes are protected with file locking and atomic replacement.
- The Memory Ledger MCP server can be registered as a first-class local tool.
- Risk reports and evidence sections surface unapproved or high-risk tools.

Primary code:

- `niyam/cli/mcp.py`
- `niyam/core/mcp.py`
- `niyam/mcp/memory_server.py`

## Skill Governance

Commands:

- `niyam skills list`
- `niyam skills register`
- `niyam skills approve`
- `niyam skills check`

Expected behavior:

- Skills can be inventoried and governed similarly to MCP tools.
- Registration records skill metadata, source, risk, approval state, and provenance where supplied.
- Checks should flag missing approval, high-risk capabilities, and policy concerns.

Primary code:

- `niyam/cli/skills.py`
- `niyam/core/skills.py`
- `tests/test_skills_governance.py`

Note: these files are currently uncommitted in the worktree, so this section reflects current local state rather than committed mainline only.

## Cost and FinOps

Commands:

- `niyam cost log`
- `niyam cost summary`
- `niyam cost report`
- `niyam cost pricing`

Expected behavior:

- Cost logging records runtime/model token usage, task/session metadata, status, and estimated spend.
- Pricing maps models to input/output rates per million tokens.
- Summary and report commands aggregate spend by session, task, model, day, and repository where available.
- Negative token counts and invalid pricing are rejected.

Primary code:

- `niyam/cli/cost.py`
- `niyam/core/cost.py`

## Evidence and Reports

Commands:

- `niyam evidence`
- `niyam report`
- `niyam mission report`
- `niyam mission verify-report`

Expected behavior:

- Evidence combines scan results, guard logs, MCP posture, cost logs, Memory Ledger posture, Control Room workspace activity, browser actions, approvals, mission state, and optional signatures.
- Markdown and HTML are generated through templates.
- Missing data is represented honestly as unavailable or not scanned, rather than fabricated as passing.
- Mission report verification checks integrity/signatures when a public key or strict mode is supplied.

Primary code:

- `niyam/cli/evidence.py`
- `niyam/core/evidence.py`
- `niyam/evidence/reporter.py`
- `niyam/templates/evidence_markdown.j2`
- `niyam/templates/evidence_html.j2`
- `niyam/mission/reporter.py`

## Memory Ledger

Commands:

- `niyam memory show`
- `niyam memory add`
- `niyam memory clear`
- `niyam memory init`
- `niyam memory list`
- `niyam memory validate`
- `niyam memory export`
- `niyam memory import`
- `niyam memory diff`
- `niyam memory redact`
- `niyam memory policy-check`
- `niyam memory trace`
- `niyam memory recall`
- `niyam memory serve-mcp`

Expected behavior:

- Legacy memory commands remain available for simple project memory.
- The Memory Ledger stores structured records in local JSONL files.
- Export/import supports portable manifests.
- Diff compares before/after memory sets.
- Redaction removes sensitive values before long-term storage or sharing.
- Policy checks enforce retention, sensitivity, source, and approval rules.
- Trace records lineage for memory creation and recall.
- Recall returns relevant records for a query.
- `serve-mcp` exposes memory operations as a local MCP-compatible server.

Primary code:

- `niyam/cli/memory.py`
- `niyam/core/memory.py`
- `niyam/core/memory_ledger/`
- `niyam/mcp/memory_server.py`

## Control Room Workspace and Browser Sessions

Commands:

- `niyam workspace create`
- `niyam workspace list`
- `niyam workspace show`
- `niyam workspace log`
- `niyam workspace pause`
- `niyam workspace resume`
- `niyam workspace request-approval`
- `niyam workspace approve`
- `niyam workspace reject`
- `niyam workspace timeline`
- `niyam workspace evidence`
- `niyam workspace browser-start`
- `niyam workspace browser-action`
- `niyam workspace browser-pause`
- `niyam workspace browser-resume`
- `niyam workspace takeover`
- `niyam workspace release`

Expected behavior:

- Workspace sessions model supervised human-agent task rooms.
- Timeline entries are append-only session actions.
- Approvals track requested, approved, and rejected high-risk actions.
- Pause/resume and takeover/release model human supervision states.
- Browser sessions record navigation, clicks, typing, submit, screenshot, and close actions through a local abstraction.
- Workspace evidence exports session state, timeline, browser actions, and approvals as Markdown or JSON.

Primary code:

- `niyam/cli/workspace.py`
- `niyam/core/workspace/store.py`
- `niyam/core/workspace/timeline.py`
- `niyam/core/workspace/approvals.py`
- `niyam/core/workspace/browser.py`
- `niyam/core/workspace/evidence.py`
- `niyam/core/workspace/models.py`

## Portal API and Dashboard

Commands:

- `niyam portal`

Expected behavior:

- Starts a local FastAPI/Uvicorn server for portal/dashboard access.
- Serves health, policies, MCP registry, fleet config, swarm state, guard logs, prompt audits, missions, mission evidence, SARIF, logs, and approval/action endpoints.
- Uses an `X-Niyam-Token` header when a token is configured.

Primary code:

- `niyam/cli/main_cmds.py`
- `niyam/api/server.py`
- `niyam/api/models.py`
- `niyam/templates/portal/index.html`

## Swarm Coordination

Commands:

- `niyam swarm init`
- `niyam swarm status`
- `niyam swarm clean`
- `niyam swarm lock`
- `niyam swarm unlock`
- `niyam swarm request-lock`
- `niyam swarm yield-lock`
- `niyam swarm deny-lock`
- `niyam swarm logs`
- `niyam swarm ledger`
- `niyam swarm heartbeat`
- `niyam swarm deregister`

Expected behavior:

- Swarm state tracks agents, heartbeats, locks, lock requests, and coordination logs.
- Lock commands reserve file/resource scopes for agents.
- Request/yield/deny commands negotiate contested resources.
- Status renders live views and can watch repeatedly.
- Cleanup removes stale agents and locks.

Primary code:

- `niyam/cli/swarm.py`
- `niyam/core/swarm.py`

## Fleet Management

Commands:

- `niyam fleet register`
- `niyam fleet discover`
- `niyam fleet list`
- `niyam fleet status`
- `niyam fleet sync`
- `niyam fleet run`

Expected behavior:

- Fleet commands register and discover multiple repositories.
- Status aggregates workspace health across repos.
- Sync propagates Niyam configuration patterns across registered repos.
- Run dispatches commands or missions across selected repositories.

Primary code:

- `niyam/cli/fleet.py`
- `niyam/core/fleet.py`

## CI/CD and Pull Requests

Commands:

- `niyam ci verify`
- `niyam ci generate`
- `niyam pr create`
- `niyam review`
- `niyam review pr`

Expected behavior:

- `ci verify` runs production-readiness checks suitable for CI gates.
- `ci generate` scaffolds CI configuration for supported providers.
- `pr create` integrates evidence/report generation into pull request workflows.
- Review commands run structured review templates against code or PR context.

Primary code:

- `niyam/cli/ci.py`
- `niyam/core/ci.py`
- `niyam/core/ci_generators.py`
- `niyam/cli/pr.py`
- `niyam/core/pr.py`
- `niyam/cli/review.py`
- `niyam/core/review.py`
- `niyam/templates/reviews/`

## Identity and Signing

Commands:

- `niyam identity show`
- `niyam identity init`
- `niyam identity public-key`

Expected behavior:

- Local cryptographic identity is created and stored for signing evidence reports.
- Public keys can be printed for verification.
- Report generation uses the configured identity when signatures are required.

Primary code:

- `niyam/cli/identity.py`
- `niyam/core/identity.py`
- `niyam/mission/reporter.py`

## Packs, Policies, and Templates

Commands:

- `niyam pack list`
- `niyam pack add`
- `niyam pack remove`
- `niyam pack sync`
- `niyam policy validate`

Expected behavior:

- Packs install modular bundles of commands, skills, agents, memory, and policy templates.
- Policy validation checks configured governance files and command policies.
- Templates under `niyam/templates/` are copied or rendered into workspaces by init, sync, pack, and evidence flows.

Primary code:

- `niyam/cli/pack.py`
- `niyam/core/packs.py`
- `niyam/cli/policy.py`
- `niyam/policies/validator.py`
- `niyam/templates/`

## SaaS Control Plane Hooks

Commands:

- `niyam saas config`
- `niyam saas upload`

Expected behavior:

- Local configuration stores endpoint/auth settings for a remote dashboard where configured.
- Upload sends local evidence or mission telemetry to the configured SaaS endpoint.
- The rest of the product remains local-first and should not require SaaS by default.

Primary code:

- `niyam/cli/saas.py`
- `niyam/core/saas.py`

