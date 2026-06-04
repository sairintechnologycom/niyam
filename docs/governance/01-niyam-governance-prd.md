# PRD: Niyam Governance & Production Readiness

## 1. Executive Summary
Niyam is evolving from an AI development orchestrator into a comprehensive **governance and production-readiness layer** for AI-assisted development. This Product Requirements Document (PRD) outlines the features required to validate codebase readiness, audit agent actions, catalog and classify external tool risks, track model token costs, and compile compliance-ready audit reports. All operations are local-first, agent-agnostic, and zero-trust by design.

---

## 2. Product Vision & Goals
* **Bridge the "Vibe-to-Production" Gap:** AI coding agents write code quickly but often omit tests, leave placeholder stubs, bypass health endpoints, or expose credentials. Niyam provides the guardrails and scanners to verify code quality and compliance before promotion.
* **Local-First & Zero-Trust:** All security analysis, logs, and token pricing rates are processed and stored locally inside the project's `.niyam/` folder. No proprietary codebase context or credentials are leaked to remote SaaS tracking platforms.
* **Agent-Agnostic Governance:** Works regardless of whether the developer uses Claude Code, Codex, Gemini, or custom local scripts.

---

## 3. Product Context vs. Evolved Capabilities

| Capability | Current Context (v0.3.0) | Evolved Direction (v0.4.0+) |
| --- | --- | --- |
| **Orchestration** | Runs shell tasks, updates markdown context. | Coordinates safety policies, wraps agent command runs. |
| **Workspace Setup** | Initializes directory layouts via `niyam init`. | Configures governance rule profiles and tool registries. |
| **Validation** | Runs tests and lints via `niyam doctor`. | Enforces strict, profile-based launch gates via `niyam scan`. |

---

## 4. Key Capabilities & User Stories

### I. Repository Scanning (`niyam scan`)
Evaluates the codebase using rulesets categorized by strictness profiles: `startup`, `team`, and `enterprise`.
* **As a** Release Engineer,
* **I want to** run a local scan of my repository using an `enterprise` profile,
* **So that** I can automatically block build promotions if critical vulnerabilities (like hardcoded keys or unpinned container base images) are found.

#### Key Features:
* **Configurable Rule Profiles:**
  * `startup` (Lenient): Flags critical security exposures (keys, passwords).
  * `team` (Medium): Flags missing dependency lockfiles, commented assertions, and placeholder TODO stubs.
  * `enterprise` (Strict): Requires tests (minimum file presence), Dockerfile base image pinning, health-check routes, CI/CD config validation, and IaC checkups.
* **Launch Gates:** Evaluates a project readiness score ($0 - 100$) based on severity deductions:
  * **Critical Findings:** Deducts $25$ points each.
  * **High Findings:** Deducts $15$ points each.
  * **Medium Findings:** Deducts $8$ points each.
  * **Low Findings:** Deducts $3$ points each.
  * **Info Findings:** Deducts $0$ points.
* **Decision Matrix:**
  * **Score 90 - 100:** `GO`
  * **Score 75 - 89:** `CONDITIONAL_GO` (passes, but lists issues to resolve).
  * **Score 50 - 74:** `HIGH_RISK` (warns heavily, requires override).
  * **Score < 50:** `NO_GO` (hard failure, blocks automation).

---

### II. Action Governance (`niyam guard`)
Monitors agent commands and actively enforces file/path and command constraints.
* **As a** Security Officer,
* **I want to** freeze access to my database migrations directory (`/db/migrations`) during automated agent runs,
* **So that** the agent cannot accidentally drop tables or run unapproved schema alterations.

#### Key Features:
* **Passive Observation (`niyam guard run`):** Executes commands within a subprocess, recording duration, exit code, timestamp, and working directory to `.niyam/logs/guard-actions.jsonl`.
* **Active Constraint Enforcement:**
  * `niyam guard freeze <path>`: Blocks file writes/edits in specified folders.
  * `niyam guard careful`: Intercepts and flags destructive shell patterns (e.g. `rm -rf`, `DROP DATABASE`) and prompts for approval.
* **Credential Redaction:** Sanitizes all logs to redact environment variables, authorization headers, passwords, and private keys using regex rules before writing to the ledger.

---

### III. MCP & Tool Registry (`niyam mcp`)
A catalog of external APIs, CLI commands, and Model Context Protocol (MCP) servers accessible to AI agents.
* **As a** Devops Lead,
* **I want to** register our local file-system MCP server and mark it as high-risk,
* **So that** the audit report clearly notes what host capabilities were granted to the AI.

#### Key Features:
* **Heuristic Risk Classification:** Evaluates tools and assigns levels (`low`, `medium`, `high`, `critical`):
  * **Critical:** Shell executions, raw command-line tools.
  * **High:** Filesystem write access, database modification, root privilege.
  * **Medium:** Remote cloud API connections, read/write SaaS access (e.g. Slack, Jira).
  * **Low:** Static reference search tools, read-only documentation APIs.
* **Approval Status:** Explicitly tracks `approved: true/false`. If a tool is high/critical and unapproved, it flags a warning in the readiness scan.

---

### IV. AI Cost & Token Tracking (`niyam cost`)
Estimates financial expenses incurred during AI development sessions using local rates tables.
* **As an** Engineering Manager,
* **I want to** run a cost summary of my team's AI token spending,
* **So that** I can track the "wasted budget" from failed or repeated agent loops.

#### Key Features:
* **Local Pricing rate Table (`.niyam/pricing.json`):** Tracks pricing for key models (Claude, GPT, Gemini) per million tokens (input vs. output).
* **Cost Summary & Reports:** Renders markdown tables grouped by day, repository, task, and session.
* **Wasted Budget Calculator:** Specifically highlights the cost and count of failed or repeated runs, highlighting agent inefficiencies.

---

### V. Joint Evidence Report (`niyam evidence`)
Compiles readiness scores, observed command logs, registered tool risks, and estimated session costs into a single audit-ready report.
* **As a** Compliance Auditor,
* **I want to** export a unified Markdown or HTML report of the workspace,
* **So that** I have a permanent, timestamped evidence record of all AI actions and code checks.

#### Key Features:
* **Multi-Format Compilation:** Supports `markdown`, `json`, and `html` exports.
* **Strict Masking:** Enforces strict data-loss prevention policies, running the secret redaction engine over all exported JSON/Markdown fields.

---

## 5. Non-Functional Requirements
1. **Performance:** Running `niyam scan` on a codebase of 10,000 files must complete in under $3$ seconds.
2. **Offline Mode:** The CLI must work completely offline without sending any code or token statistics to external APIs.
3. **Low Footprint:** Local logs and configurations must not exceed $50\text{ MB}$ of storage space per repository.
4. **Compatibility:** Must integrate seamlessly with existing Niyam core modules without modifying existing product flows.
