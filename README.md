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
pipx install niyam-dev
```

Alternatively, you can run it on the fly without installing using `uvx`:

```bash
uvx --from niyam-dev niyam --help
```

For local development installation:

```bash
git clone https://github.com/aincloudtools/niyam.git
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

## Experimental Governance Capabilities

Niyam now includes experimental capabilities for advanced governance and auditing of AI-assisted development. These features are designed to be run locally without requiring SaaS backends:

- **Local Readiness Scan (`niyam scan`):** A rule-based scan evaluating credentials exposure, dependency files/lockfiles, health endpoints, test suites, pinned images, and masked test assertions.
- **Guard Observation (`niyam guard run`):** Shell wrapper logging execution times, outcomes, and commands (with automated secret redaction) to audit agent behavior.
- **MCP & Tool Registry (`niyam mcp`):** Local catalog of tools, APIs, and MCP servers used by agents, utilizing heuristic risk classification for security posture analysis.
- **AI Cost Tracking (`niyam cost`):** Audits token consumption and estimated spend using configurable local pricing tables.
- **Unified Evidence Report (`niyam evidence generate`):** Compiles scan results, observed actions, MCP registry status, and cost reports into a single, sign-off-ready markdown or HTML document.

Refer to the [Governance Overview](file:///Users/bhushan/Documents/Projects/sutra/docs/governance.md) for more details.


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
