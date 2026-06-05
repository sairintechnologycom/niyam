# PRD: Niyam Governance & Production Readiness

## 1. Executive Summary & Problem Statement
Autonomous AI coding agents (such as Claude Code, Codex, or custom developer loops) dramatically accelerate software delivery. However, they introduce significant risks to software quality, compliance, and security:
* **The "Vibe-to-Production" Gap:** AI agents often produce functional code but omit comprehensive unit tests, bypass security checkups, leave raw placeholder stubs, or ignore enterprise infrastructure requirements (e.g., unpinned Docker images).
* **Credential Leaks:** Agents can accidentally print sensitive keys, database passwords, or auth tokens into logs or commit files to public repositories.
* **Ungoverned Action Paths:** Rogue or misconfigured agent sessions may run destructive shell scripts (e.g., `rm -rf` or database table drops) or modify critical project configs without human oversight.
* **Unvetted Third-Party Tools:** Agents frequently consume Model Context Protocol (MCP) servers and external web APIs without cataloging their host privileges or verifying security authorization.
* **Token Cost Runaways:** Engineering managers lack visibility into token cost structures or budget wasted on failed/infinite loops during AI agent runs.

**Niyam Governance** bridges these gaps by providing a local-first, agent-agnostic, zero-trust governance and production-readiness layer. It enforces safety gates and audits AI-generated changes before code hits production.

---

## 2. Target Personas
The Niyam governance capabilities are built to serve five key personas across the software delivery lifecycle:

### A. The Developer
* **Needs:** Speed and clarity.
* **Pain Point:** Security policies that block their agent's execution without explanation.
* **Niyam Value:** Provides immediate terminal feedback and actionable remediation guidelines (e.g., specific instructions on how to resolve failing scan rules).

### B. The Senior Engineer
* **Needs:** Code hygiene and structural consistency.
* **Pain Point:** Reviewing pull requests with incomplete tests, commented-out assertions, or placeholder stubs.
* **Niyam Value:** Standardizes readiness expectations using customizable scan profiles (`team`, `enterprise`) that gate builds based on clear quality rules.

### C. The Architect
* **Needs:** Compliance with system patterns.
* **Pain Point:** Keeping track of external APIs, microservices, and base image vulnerabilities introduced by AI-generated files.
* **Niyam Value:** Enforces infrastructure checks (e.g., Dockerfile base image pinning) and maps architectural boundaries.

### D. The Security Reviewer
* **Needs:** Prevention of secrets exposure and host privilege abuse.
* **Pain Point:** Lack of visibility into commands executed by autonomous agents and risks from external MCP tool registries.
* **Niyam Value:** Sanitizes agent outputs with the inline Redaction Pipeline, restricts files via Path Freeze rules, and classifies MCP server risks.

### E. The Platform / DevOps Team
* **Needs:** Clean CI/CD validation gates.
* **Pain Point:** Complex integrations and slow build checks.
* **Niyam Value:** Provides lightweight, standardized exit codes and CLI options (e.g., `niyam ci verify` and `niyam scan --fail-on`) that integrate into GitHub Actions or Azure DevOps in minutes.

---

## 3. Product Vision & Evolved Capabilities

| Capability | Current Context (v0.3.0) | Evolved Direction (v0.4.0+) |
| --- | --- | --- |
| **Orchestration** | Runs shell tasks, updates markdown context. | Coordinates safety policies, wraps agent command runs. |
| **Workspace Setup** | Initializes directory layouts via `niyam init`. | Configures governance rule profiles and tool registries. |
| **Validation** | Runs tests and lints via `niyam doctor`. | Enforces strict, profile-based launch gates via `niyam scan`. |

---

## 4. Key Use Cases

### Use Case 1: Repository Scan Gating (`niyam scan`)
* **Goal:** Verify that AI-generated code meets strict quality and security standards before being pushed.
* **Trigger:** Pre-commit hooks or CI/CD pipelines run `niyam scan` on the project root.
* **Flow:** The scanner parses rules based on the selected profile (`startup`, `team`, `enterprise`, or `regulated`), computes a readiness score ($0 - 100$), and returns an exit code of `2` if findings violate policy limits.

### Use Case 2: Safe Subprocess Execution (`niyam guard run`)
* **Goal:** Run agent shell commands inside a monitored, redacted environment.
* **Trigger:** The agent executes commands prefixed by `niyam guard run -- <command>`.
* **Flow:** Niyam interceptors block access to frozen directories, scan inputs for destructive patterns, redact sensitive credentials in stdout/stderr, and append execution metrics to a local append-only ledger (`.niyam/logs/guard-actions.jsonl`).

### Use Case 3: MCP Server Risk Vetting (`niyam mcp`)
* **Goal:** Track host-level capabilities granted to agents via Model Context Protocol (MCP) servers.
* **Trigger:** Platform teams register new tools via `niyam mcp register`.
* **Flow:** Niyam uses heuristic analysis to classify tool risk (e.g., marking shell/filesystem write capabilities as `critical` or `high`) and warns the developer if unapproved high-risk tools are enabled.

### Use Case 4: FinOps Cost Tracking & Budget Leak Spotting (`niyam cost`)
* **Goal:** Audit session expenses and capture financial leaks from looping agents.
* **Trigger:** Runtimes record token counts to `.niyam/logs/cost-events.jsonl` upon task completion.
* **Flow:** Engineering managers run `niyam cost summary` or `niyam cost report` to view calculated USD expenses against local pricing rates (`.niyam/pricing.json`) and isolate wasted budgets.

### Use Case 5: Compliance-Ready Joint Evidence (`niyam evidence`)
* **Goal:** Generate a unified audit trail for security auditors.
* **Trigger:** Developers or release tools run `niyam evidence generate`.
* **Flow:** The evidence engine compiles readiness scores, observed command records, tool registry risk states, and token cost summaries into a redacted Markdown, HTML, or JSON report.

---

## 5. MVP Scope vs. Future Capabilities

### In MVP Scope (v0.4.0)
* **Local-First Design:** Entirely self-contained configuration store under `.niyam/`. Zero dependencies on external database engines or cloud SaaS platforms.
* **Five Governance CLI Commands:** `scan`, `guard`, `mcp`, `cost`, and `evidence`.
* **Standard Profiles:** Support for `startup` (lenient), `team` (medium), `enterprise` (strict), and `regulated` (hardened).
* **Regex Redaction Engine:** Core filter scrubbing AWS keys, private tokens, passwords, and private PEM keys from reports and logs.
* **Heuristic Risk Classifier:** Classifying tools based on declared capabilities and types.
* **CI/CD Integrations:** Support for structured JSON/SARIF output and customizable exit codes.

### Out of MVP Scope (Non-Goals)
* **No Remote SaaS Portal:** Niyam does not serve a centralized, multi-tenant cloud dashboard. All data remains local.
* **No Auto-Remediation:** Niyam flags violations and provides advice, but it **never** automatically writes code modifications to resolve scan issues.
* **No Agent Integration Blockers:** Niyam works alongside agents as a wrapper/gating framework, not as a replacement for the agent's internal reasoning loop.

---

## 6. Success Metrics
* **Performance:** Running `niyam scan` on a codebase of 10,000 files completes in under $3$ seconds.
* **Data Leak Prevention:** Zero plain-text credentials (matching defined redaction patterns) written to `.niyam/logs/` or evidence outputs.
* **Token Cost Tracking Accuracy:** Estimated token costs deviate by less than $\pm 1\%$ from actual API provider billing rates.
* **Offline Execution Integrity:** 100% of CLI capabilities run fully offline without external network queries.
* **Developer Friction:** Scan failures print clear, actionable remediation tips, reducing resolution time to under $5$ minutes per finding.
