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
