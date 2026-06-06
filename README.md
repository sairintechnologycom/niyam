# Niyam

**Governed autonomous development for AI coding agents.**

> One `.niyam/` source of truth. Many AI runtimes. Policy-driven autonomy. Evidence-backed delivery.

> [!NOTE]
> Niyam was previously developed under the Sutra codename. New projects should use `.niyam/`.

## What is Niyam?

Niyam turns any repository into a governed AI-development workspace with:

- **Reusable agents** — specialized AI roles (backend, frontend, security, QA)
- **Skills** — composable methodology packs (TDD, code review, planning)
- **Commands** — structured workflows (`/implement`, `/review`, `/ship`)
- **Guardrails** — command deny lists, approval gates, path restrictions
- **Evidence** — audit trails for every AI-assisted session

## Installation

You can install Niyam CLI globally using [pipx](https://github.com/pypa/pipx):

```bash
pipx install niyam
```

Alternatively, you can run it on the fly without installing using `uvx`:

```bash
uvx --from niyam niyam --help
```

For local development installation:

```bash
git clone https://github.com/sairintechnologycom/niyam.git
cd niyam
pip install -e .
```

## Quick Start

```bash
# Initialize a workspace in your target repository
cd your-project
niyam init --profile fullstack --runtime claude

# Add Codex as a second runtime
niyam runtime add codex

# Detect your stack
niyam context refresh

# Validate setup
niyam policy validate
niyam doctor

# Sync changes to runtimes
niyam sync
```

Then open Claude Code and use:
```
/implement add login validation
/review
/ship
```

## Commands

| Command | Description |
|---------|-------------|
| `niyam init` | Initialize a governed workspace |
| `niyam sync` | Sync .niyam/ to configured runtimes |
| `niyam doctor` | Validate workspace integrity |
| `niyam context refresh` | Scan repo and update context |
| `niyam context show` | Display current context |
| `niyam context diff` | Show context changes |
| `niyam policy validate` | Validate policy files |
| `niyam guard enable` | Enable all guardrails |
| `niyam guard disable` | Disable guardrails |
| `niyam guard careful` | Enable destructive-command warnings |
| `niyam guard freeze <path>` | Restrict edits to a path |
| `niyam runtime add <runtime>` | Add a new runtime |
| `niyam report` | Generate evidence report |
| `niyam scan [path]` | *[Experimental]* Scan repository for readiness/risks |
| `niyam guard run -- <cmd>`| *[Experimental]* Run a command under observation |
| `niyam guard status` | *[Experimental]* Display guard settings and metrics |
| `niyam guard logs` | *[Experimental]* Show recent observed actions |
| `niyam mcp register` | *[Experimental]* Register a tool or MCP server |
| `niyam mcp list` | *[Experimental]* List registered tools/servers |
| `niyam mcp risk-report` | *[Experimental]* Report risks of registered tools |
| `niyam cost log` | *[Experimental]* Log token usage and model expenses |
| `niyam cost summary` | *[Experimental]* Display AI engineering cost summary |
| `niyam cost report` | *[Experimental]* View detailed breakdowns of expenses |
| `niyam evidence generate`| *[Experimental]* Generate local evidence & readiness report |

## Enterprise Governance Capabilities

Niyam includes robust, local-first enterprise governance capabilities to bridge the "vibe-to-production" gap, audit agent actions, and compile compliance-ready evidence reports:

* **Repository Scanning (`niyam scan`):** Evaluates repository readiness scores against strict quality and security profiles (`startup`, `team`, `enterprise`, `regulated`).
* **Action Governance (`niyam guard`):** Intercepts shell commands, redacts credentials in real-time, blocks destructive patterns, and enforces directory read-only freezes.
* **MCP & Tool Registry (`niyam mcp`):** Catalogs and heuristics-classifies risk profiles (`low`, `medium`, `high`, `critical`) for external Model Context Protocol servers.
* **AI Cost Tracking (`niyam cost`):** Logs LLM token metrics and session costs against a local rate-card table to prevent budget leaks.
* **Joint Evidence Compiler (`niyam evidence`):** Synthesizes readiness scores, observed logs, registered tools, and token pricing into a unified, audit-ready compliance document.

### Governance Documentation Pack
For deep dives into policies, specifications, and architecture, refer to the following guides:
1. [01. Product Requirements (PRD)](file:///Users/bhushan/Documents/Projects/sutra/docs/governance/01-niyam-governance-prd.md)
2. [02. Technical Architecture](file:///Users/bhushan/Documents/Projects/sutra/docs/governance/02-niyam-technical-architecture.md)
3. [03. Security & Access Governance](file:///Users/bhushan/Documents/Projects/sutra/docs/governance/03-niyam-security-access-governance.md)
4. [04. CLI & CI/CD Specification](file:///Users/bhushan/Documents/Projects/sutra/docs/governance/04-niyam-cli-and-ci-spec.md)
5. [05. Feature Implementation Tickets](file:///Users/bhushan/Documents/Projects/sutra/docs/governance/05-niyam-feature-ticket-list.md)
6. [06. Backward Compatibility & Migration Plan](file:///Users/bhushan/Documents/Projects/sutra/docs/governance/06-niyam-backward-compatibility-and-migration-plan.md)


## Architecture

```
.niyam/              ← Source of truth (you own this)
├── niyam.yaml       ← Workspace config
├── project.yaml     ← Stack and validation
├── runtimes.yaml    ← Runtime settings
├── context/         ← AI project context
├── agents/          ← Agent role definitions
├── skills/          ← Composable skill packs
├── commands/        ← Slash command workflows
├── policies/        ← Guardrails and approval gates
└── evidence/        ← Audit trails

CLAUDE.md            ← Generated for Claude Code
.claude/             ← Generated for Claude Code
AGENTS.md            ← Generated for Codex CLI
```

## Profiles

| Profile | Agents | Best For |
|---------|--------|----------|
| `fullstack` | backend, frontend, security, QA | Full-stack web apps |
| `backend` | backend, security, QA | API/service projects |
| `frontend` | frontend, QA | Frontend-only projects |

## Roadmap

See [ROADMAP.md](file:///Users/bhushan/Documents/Projects/niyam/ROADMAP.md) for the detailed vision, target architecture, and target build phases.

## License

MIT
