# Niyam CLI Reference Guide

This document lists all available CLI commands, subcommands, and options supported by the Niyam CLI tool.

---

## Global Options

The following options can be passed to the root `niyam` command:
- `--verbose` / `-v`: Enable verbose logs and debug output.
- `--help`: Show global command listing and exit.

---

## Core Workspace Commands

### `niyam init`
Initialize a governed AI-development workspace in the current directory.
- **Options:**
  - `--profile` (e.g. `fullstack`, `backend`, `frontend`)
  - `--runtime` (e.g. `claude`, `gemini`, `codex`)

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

## Experimental Governance Commands

> [!NOTE]
> The commands listed below are **experimental** and undergo frequent updates.

### `niyam scan`
Scan the codebase for production readiness, configuration errors, and code risk factors.
- **Arguments:**
  - `[path]`: Directory path to scan. Defaults to `.`.
- **Options:**
  - `--profile` / `-p`: Selection profile (`startup`, `team`, `enterprise`).
  - `--output` / `-o`: Output reporting format (`text`, `json`, `markdown`).
  - `--report-file` / `-f`: Path to write the generated report to.
  - `--rules`: Path to custom rules YAML file.

---

### `niyam guard`
Manage AI security guardrails, path edit permissions, and observe execution history.

#### `niyam guard enable`
Activate all configured path freeze restrictions and destructive command blocks.
- **Options:**
  - `--dry-run`: Preview changes without writing them.

#### `niyam guard disable`
Deactivate path freeze blocks and destructive command guardrails.
- **Options:**
  - `--dry-run`: Preview changes without writing them.

#### `niyam guard careful`
Activate warnings on destructive CLI commands.
- **Options:**
  - `--dry-run`: Preview changes without writing them.

#### `niyam guard freeze`
Restrict agent writes/edits to a specific directory path.
- **Arguments:**
  - `path`: Directory or file path to freeze.
- **Options:**
  - `--dry-run`: Preview changes without writing them.

#### `niyam guard run`
Wrap and run a shell command under observation mode.
- **Arguments:**
  - Command args following `--` (e.g., `niyam guard run -- npm test`).
- **Options:**
  - `--capture-output`: Record stdout/stderr stream outputs in log database.

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
  - `--type` (Required): `mcp_server`, `api`, `cli`, `local_tool`, `browser`, `other`.
  - `--command-or-url`: Execution command or URL endpoint.
  - `--owner`: Tool provider owner.
  - `--risk`: Manual risk rating (`low`, `medium`, `high`, `critical`).
  - `--approved` / `--no-approved`: Explicit approval status.
  - `--capabilities`: Comma-separated list of tool methods.
  - `--data-access`: Description of data accessed by the tool.
  - `--notes`: Additional descriptions.

#### `niyam mcp list`
Renders a tabular view of all registered tools.

#### `niyam mcp show`
Display detailed configuration parameters, owner, and notes for a tool.
- **Arguments:**
  - `name`: Name of the registered tool to view.

#### `niyam mcp risk-report`
Perform a security risk analysis of registered tools based on heuristic indicators.

---

### `niyam cost`
Audit AI engineering session token consumption and model pricing rates.

#### `niyam cost log`
Record a single token consumption session log.
- **Options:**
  - `--tool`: Client agent tool (default: `unknown`).
  - `--model`: Model name (default: `unknown`).
  - `--input-tokens`: Prompt token count (default: 0).
  - `--output-tokens`: Completion token count (default: 0).
  - `--task`: Name/ID of task.
  - `--status`: Execution outcome (`success`, `failed`, `repeated`).
  - `--notes`: Additional text notes.

#### `niyam cost summary`
Print a high-level summary of total logged sessions, token count, and spend.

#### `niyam cost report`
Generate structured tables showing breakdowns of daily spend, repo spend, task spend, top expensive runs, and wasted budget.

---

### `niyam evidence`
Build compliance-ready governance documentation.

#### `niyam evidence generate`
Synthesizes logs, tool lists, scan outputs, and token costs into a single report.
- **Options:**
  - `--from`: Scan report JSON path. Run fresh scan if omitted.
  - `--format`: File format (`markdown`, `json`, `html`).
  - `--output` / `-o`: Output file path. Prints to console if omitted.
  - `--include`: Sections to include, comma-separated (e.g. `scan,guard,mcp,cost`).
