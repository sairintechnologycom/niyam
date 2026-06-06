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
*Niyam plans the mission, spawns sub-agents in isolated **Git worktrees**, runs parallel validations, and merges only what passes.*

---

## 💎 Key Features

### 🛡️ Active Action Governance
*   **Command Guardrails:** Intercept and block dangerous shell commands (e.g., destructive database drops or global file deletions) before execution.
*   **Path Freezing:** Restrict agents to specific scopes. Protect core files like `LICENSE` or sensitive `infra/` folders from unauthorized AI writes.
*   **Credential Redaction:** A built-in engine that identifies and redacts secrets, API keys, and PII from agent logs and CLI outputs in real-time.

![Niyam Action Governance](https://raw.githubusercontent.com/sairintechnologycom/niyam/main/docs/images/niyam-guard.png)

### 🔍 Production Readiness Scanning
*   **Repo Audits:** Scan your repository against strict profiles (`startup`, `team`, `enterprise`, `regulated`) to detect missing documentation, unpinned dependencies, or secret exposures.
*   **Readiness Scoring:** Get a numerical **Readiness Score (0-100)** and a clear **GO / NO-GO** decision for every branch or mission.

![Niyam Readiness Scan](https://raw.githubusercontent.com/sairintechnologycom/niyam/main/docs/images/niyam-scan.png)

### 🤖 Multi-Agent Orchestration
*   **Agent Roles:** Define specialized AI personas (e.g., `security-reviewer`, `qa-engineer`) with tailored system prompts and dedicated toolsets.
*   **Isolated Execution:** Run tasks in parallel using **Git Worktrees**, preventing agent cross-talk and ensuring clean, atomic PRs.

### 📑 Evidence & Compliance Hub
*   **Joint Evidence Reports:** Automatically synthesize scan findings, observed command logs, and cost data into standardized, audit-ready compliance documents.
*   **FinOps Cost Tracking:** A local ledger that logs every token consumed and estimates USD spend against customizable pricing tables.

---

## 📊 Live Mission Dashboard

Monitor your autonomous agents in real-time with the built-in terminal dashboard:

```bash
niyam dashboard --watch
```

![Niyam Mission Dashboard](https://raw.githubusercontent.com/sairintechnologycom/niyam/main/docs/images/niyam-dashboard.png)

### What the Dashboard Tracks:
*   **Live Task Progress:** Visual status of all mission tasks (Planned, Running, Completed, Failed).
*   **Real-time Logs:** View active output from implementation agents as they work in isolated worktrees.
*   **Validation Monitor:** Watch unit tests and lint checks run and report results live.
*   **Resource Efficiency:** Track actual token spend vs. baseline estimates to optimize your AI engineering budget.

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
