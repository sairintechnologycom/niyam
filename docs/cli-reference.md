# Niyam CLI Reference Guide

This document lists all available CLI commands, subcommands, and options supported by the Niyam CLI tool.

---

## Global Options

The following options can be passed to the root `niyam` command:
- `--verbose` / `-v`: Enable verbose logs and debug output.
- `--json-logs`: Emit structured JSON logs where supported.
- `--help`: Show global command listing and exit.

---

## Core Workspace Commands

### `niyam init`
Initialize a governed AI-development workspace in the current directory.
- **Options:**
  - `--profile` (e.g. `fullstack`, `backend`, `frontend`, `startup-saas`)
  - `--runtime` (e.g. `claude`, `gemini`, `codex`)

### `niyam info`
Display system and workspace information.
- Shows OS, Python version, Niyam version, and workspace status.

### `niyam sync`
Synchronize files and settings under `.niyam/` source of truth to all active AI runtime environments (e.g., `CLAUDE.md`, `.claude/`, `AGENTS.md`).

### `niyam doctor`
Validate `.niyam/` workspace structure, syntax correctness of configuration and policies files, and runtime projections.

### `niyam context refresh`
Scan project codebase to build and update the project context directory (`.niyam/context/`).

### `niyam context show`
Display structural project context, components, schemas, and API definitions.

### `niyam context diff`
Compare the current project workspace file structure with the cached context files.

### `niyam policy validate`
Validate policy definitions, active guardrails, and environment check settings.

### `niyam runtime add`
Activate an additional AI runtime client adapter.
- **Arguments:**
  - `runtime` (e.g. `claude`, `gemini`, `codex`)

---

## Governance & Readiness Commands

### `niyam scan`
Scan the codebase for production readiness, configuration errors, and code risk factors.
- **Arguments:**
  - `[path]`: Directory path to scan. Defaults to `.`.
- **Options:**
  - `--profile` / `-p`: Selection profile (`startup`, `team`, `enterprise`, `regulated`).
  - `--output` / `-o`: Output reporting format (`text`, `json`, `markdown`, `sarif`).
  - `--report-file` / `-f`: Path to write the generated report to.
  - `--rules`: Path to custom rules YAML file.
  - `--fail-on`: Exit non-zero when findings reach the selected severity.

### `niyam rules list`
List available scan and policy rules for a profile.
- **Options:**
  - `--profile` / `-p`: Profile to list rules for (default: `startup`).

---

### `niyam guard`
Manage AI security guardrails, path edit permissions, and observe execution history.

#### `niyam guard observe`
Wrap and run a command under observation mode (Alias for `guard run --mode observe`).
- **Arguments:**
  - Command args following `--` (e.g., `niyam guard observe -- npm test`).

#### `niyam guard policy`
Validate guard policy files (Alias for `policy validate`).

#### `niyam guard enable`
Activate all configured path freeze restrictions and destructive command blocks.
- **Options:**
  - `--dry-run`: Preview changes without writing them.

#### `niyam guard disable`
Deactivate path freeze blocks and destructive command guardrails.
- **Options:**
  - `--dry-run`: Preview changes without writing them.

#### `niyam guard run`
Wrap and run a shell command under guardrails.
- **Arguments:**
  - Command args following `--` (e.g., `niyam guard run -- npm test`).
- **Options:**
  - `--capture-output`: Record stdout/stderr stream outputs in log database.
  - `--dry-run`: Evaluate policies and print what would happen without executing.
  - `--mode`: Override guard mode (`observe`, `warn`, `block`, `approve`).

#### `niyam guard status`
Display active guard status, frozen paths, and observed execution metrics.

#### `niyam guard logs`
Output a list of observed commands executed by the wrapper.
- **Options:**
  - `--limit` / `-l`: Number of logs to fetch (default: 10).

---

### `niyam mcp`
Manage registered agent tools, external web APIs, and Model Context Protocol (MCP) servers.

#### `niyam mcp register`
Insert or update a tool in the local catalog (`.niyam/mcp-registry.json`).
- **Arguments:**
  - `name`: Name of the tool.
- **Options:**
  - `--type`: `mcp_server`, `api`, `cli`, `local_tool`, `browser`, `other`.
  - `--command-or-url`: Execution command or URL endpoint.
  - `--owner`: Tool provider owner.
  - `--risk`: Risk level: `low`, `medium`, `high`, `critical`.

#### `niyam mcp list`
Renders a tabular view of all registered tools.

#### `niyam mcp approve`
Approves a registered tool or MCP server for usage.
- **Arguments:**
  - `name`: Name of the tool to approve.

#### `niyam mcp register-memory-server`
Registers Niyam's local Memory Ledger MCP server in `.niyam/mcp-registry.json`.
- **Options:**
  - `--name`: Registry name. Defaults to `niyam-memory-ledger`.
  - `--approved` / `--no-approved`: Approval state for the server.
  - `--update`: Update an existing registry entry.

---

### `niyam cost`
Audit AI engineering session token consumption and model pricing rates.

#### `niyam cost summary`
Print a high-level summary of total logged sessions, token count, and spend.

#### `niyam cost report`
Generate structured tables showing breakdowns of daily spend, repo spend, and task spend.

---

## Workspace & Execution Commands

### `niyam workspace`
Manage supervised human-agent task rooms, timelines, and approvals.

#### `niyam workspace create`
Create a new supervised human-agent task room.
- **Arguments:**
  - `title`: Title of the session.
- **Options:**
  - `--agent-type`: Type of agent (manual, cli, code, browser, mcp).
  - `--risk`: Risk level (low, medium, high, critical).
  - `--objective`: Objective of the session.
  - `--session-id`: Custom session ID.

#### `niyam workspace list`
List all workspace sessions.

#### `niyam workspace show`
Show details of a specific workspace session.
- **Arguments:**
  - `session_id`: Session ID.

#### `niyam workspace log`
Log an action to the session timeline.
- **Arguments:**
  - `session_id`: Session ID.
- **Options:**
  - `--type`: Action type.
  - `--actor`: Actor (human, agent, system).
  - `--input`: Action input.
  - `--output`: Action output.
  - `--risk`: Risk level.

#### `niyam workspace pause`
Pause a workspace session.
- **Arguments:**
  - `session_id`: Session ID.

#### `niyam workspace resume`
Resume a paused workspace session.
- **Arguments:**
  - `session_id`: Session ID.

#### `niyam workspace request-approval`
Request approval for an action in a session.
- **Arguments:**
  - `session_id`: Session ID.
- **Options:**
  - `--action`: Action requiring approval.
  - `--risk`: Risk level.
  - `--reason`: Reason for approval.
  - `--by`: User requesting approval.

#### `niyam workspace approve`
Approve a pending request.
- **Arguments:**
  - `session_id`: Session ID.
- **Options:**
  - `--approval`: Approval ID.
  - `--by`: User approving.

#### `niyam workspace reject`
Reject a pending request.
- **Arguments:**
  - `session_id`: Session ID.
- **Options:**
  - `--approval`: Approval ID.
  - `--by`: User rejecting.

#### `niyam workspace timeline`
View the timeline of a session.
- **Arguments:**
  - `session_id`: Session ID.

#### `niyam workspace evidence`
Export evidence for a workspace session.
- **Arguments:**
  - `session_id`: Session ID.
- **Options:**
  - `--format`: Export format (markdown or json).

#### `niyam workspace browser-start`
Start a sandboxed browser session.
- **Arguments:**
  - `session_id`: Session ID.
- **Options:**
  - `--url`: Start URL.

#### `niyam workspace browser-action`
Log a browser action to the workspace timeline and backend.
- **Arguments:**
  - `session_id`: Session ID.
- **Options:**
  - `--type`: Action type (navigate, click, type, submit, screenshot, extract, wait).
  - `--target`: Action target (URL or selector).
  - `--input`: Action input text.

#### `niyam workspace browser-pause`
Pause a browser session.
- **Arguments:**
  - `session_id`: Session ID.

#### `niyam workspace browser-resume`
Resume a browser session.
- **Arguments:**
  - `session_id`: Session ID.

#### `niyam workspace takeover`
Human takeover of a session.
- **Arguments:**
  - `session_id`: Session ID.
- **Options:**
  - `--by`: User taking over.

#### `niyam workspace release`
Release human takeover of a session.
- **Arguments:**
  - `session_id`: Session ID.
- **Options:**
  - `--by`: User releasing.

---

### `niyam evidence`
Build audit-ready evidence and readiness report generation.

#### `niyam evidence [PATH]`
Generate human-readable evidence report locally.
- **Arguments:**
  - `[path]`: Directory path or scan result JSON file. Defaults to latest scan result.
- **Options:**
  - `--from`: Scan report JSON path.
  - `--format`: File format (`markdown`, `json`, `html`).
  - `--output` / `-o`: Output file path. Prints to console if omitted.
  - `--include`: Sections to include (e.g. `scan,guard,mcp,cost,memory,workspace`).

---

## Memory Ledger Commands

### `niyam memory init`
Initialize structured Memory Ledger storage under `.niyam/memory/`.

### `niyam memory list`
List structured Memory Ledger records.

### `niyam memory validate`
Validate Memory Ledger records against the portable memory schema.

### `niyam memory export`
Export Memory Ledger records as JSON or YAML.

### `niyam memory import`
Import Memory Ledger records from JSON or YAML.

### `niyam memory diff`
Compare two Memory Ledger manifests and show added, removed, and changed records.

### `niyam memory redact`
Redact sensitive values from structured memory records.

### `niyam memory policy-check`
Evaluate Memory Ledger records against scope, retention, confidence, and access
rules.

### `niyam memory trace`
Inspect source and recall lineage for a memory record.

### `niyam memory recall`
Recall relevant memory records for a task or query.

### `niyam memory serve-mcp`
Start the local MCP-compatible Memory Ledger server over stdio.

---

## Planned Commands (AgentOps & Control Room)

The following commands are planned for upcoming releases. They are documented
here to show roadmap direction and are not part of the current stable CLI
surface unless noted otherwise.

### `niyam workspace`
*Candidate command group for Phase E.*

The Control Room concept will first build on existing `mission`, `portal`,
`guard`, `swarm`, and `evidence` surfaces. A dedicated `workspace` command group
is intentionally deferred until the CLI shape is validated.
