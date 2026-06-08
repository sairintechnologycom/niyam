# Niyam

**Governed autonomous development for AI coding agents.**

> One `.niyam/` source of truth. Many AI runtimes. Policy-driven autonomy. Evidence-backed delivery.

[![PyPI version](https://badge.fury.io/py/niyam.svg)](https://badge.fury.io/py/niyam)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🚀 What is Niyam?

Niyam bridges the gap between fast "vibe coding" and production-grade safety. It turns any repository into a governed AI-development workspace where you define the rules, and AI agents (Claude Code, Codex, Gemini) follow them.

---

## 🎬 Niyam in Action

### 1. Interactive Development (Day-to-Day)
Niyam acts as a governance layer inside your AI agent. Use team-standard slash commands:
```bash
/implement "add password complexity rules to auth service"
```
*Niyam ensures the agent writes tests first, respects file freezes, and follows the approved TDD workflow.*

### 2. Autonomous Missions (Batch Tasks)
Orchestrate complex migrations or large-scale refactors with ease:
```bash
niyam run "migrate all API endpoints to v2"
```
*Niyam plans the mission, executes dependency-aware task layers, can isolate write tasks in **Git worktrees**, and records validation evidence.*

---

## 💎 Key Features

### 🛡️ Active Action Governance & Approvals
*   **Command Guardrails:** Intercept and block dangerous shell commands (e.g., destructive database drops or global file deletions) before execution.
*   **Path Freezing:** Restrict agents to specific scopes. Protect core files like `LICENSE` or sensitive `infra/` folders from unauthorized AI writes.
*   **Credential Redaction:** A built-in engine that identifies and redacts secrets, API keys, and PII from agent logs and CLI outputs in real-time.
*   **Enterprise Approval Gates:** Role-based (e.g., Product, QA, Security) manual approval gates for critical tasks and mission plans directly from the CLI or Portal UI.

![Niyam Action Governance](https://raw.githubusercontent.com/sairintechnologycom/niyam/main/docs/images/niyam-guard.png)

### 🤖 Multi-Agent Orchestration & Resilience
*   **Agent Roles:** Define specialized AI personas (e.g., `security-reviewer`, `qa-engineer`) with tailored system prompts and dedicated toolsets.
*   **Isolated Multi-Worktree Parallelism:** Run tasks in parallel using isolated **Git Worktrees**, preventing agent cross-talk and ensuring clean, atomic PRs.
*   **Swarm Coordination:** Track active agents, heartbeats, file locks, and negotiation requests through local swarm state.
*   **Autonomous Environment Healing:** Experimental auto-heal retries feed validation failures back into task prompts and can trigger AI re-planning.

### 🔍 Compliance & Readiness Checking
*   **Repo Audits:** Scan your repository against strict profiles (`startup`, `team`, `enterprise`, `regulated`) to detect missing documentation, unpinned dependencies, or secret exposures.
*   **Readiness Scoring:** Get a numerical **Readiness Score (0-100)** and a clear **GO / NO-GO** decision for every branch or mission.
*   **CI/CD Pipeline Scaffolding:** Generate ready-to-use CI/CD workflows (`niyam ci generate [github/gitlab/azure]`) that run strict policy validations (`niyam ci verify`) directly in your pull requests.

### 📑 Evidence & FinOps Cost Tracking
*   **Joint Evidence Reports:** Automatically synthesize scan findings, observed command logs, and cost data into standardized, audit-ready compliance documents.
*   **FinOps Cost Tracking:** A local ledger that logs every token consumed and estimates USD spend against customizable pricing tables.

---

## 📊 Live Mission Dashboard & Web Portal

Niyam provides both terminal-based and browser-based interfaces to monitor your autonomous agents and manage approvals:

### 1. Terminal Dashboard
```bash
niyam dashboard --watch
```
*   **Live Task Progress:** Visual status of all mission tasks (Planned, Running, Completed, Failed).
*   **Real-time Logs:** View active output from implementation agents as they work in isolated worktrees.
*   **Validation Monitor & Resource Efficiency:** Watch unit tests and lint checks run and report results live, alongside actual token spend.

### 2. Browser-Based Portal UI
```bash
niyam portal
```
*   **Policy Analytics:** Visual cards detailing Active Guardrails, Command Filters, Security Isolation, and active Path Freezing.
*   **Interactive Approval Center:** Review pending tasks/missions and authorize execution by role directly from the Web UI.
*   **FinOps & Agent Metrics:** Monitor token consumption, cost breakdowns, and agent success rates.

---

## 🛠️ Installation

**Global Install (Recommended)**
```bash
pipx install niyam
```

**Run on the fly (No install)**
```bash
uvx --from niyam niyam --help
```

---

## ⏱️ Quick Start

1. **Initialize your workspace:**
   ```bash
   niyam init --profile fullstack --runtime claude
   ```
2. **Synchronize with AI agent:**
   ```bash
   niyam sync
   ```
3. **Start building:**
   Open your agent (e.g. `claude`) and use `/implement`, `/review`, or `/ship`.

## 🧭 Maturity Guide

| Capability | Status |
| --- | --- |
| Workspace init, runtime sync, context refresh | Stable |
| Scan, guard, evidence, cost tracking | Experimental but covered by tests |
| Mission planning/execution, worktree isolation | Experimental |
| Swarm coordination, RAG indexing, auto-heal | Preview |

Preview features are local-first and test-covered, but their command shape and defaults may evolve before GA.

---

## 📚 Documentation & Architecture

*   [**CLI Reference Guide**](docs/cli-reference.md)
*   [**Governance Specification**](docs/governance.md)
*   [**MCP Registry Guide**](docs/mcp.md)
*   [**Migration Guide**](docs/migration-from-sutra.md)

---

## 🗺️ Roadmap

See [ROADMAP.md](ROADMAP.md) for our vision on parallel worker pools, web dashboards, and enterprise CI/CD integration.

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.
