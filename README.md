# Sutra

**Governed AI-development workspaces for Claude Code, Codex CLI, and future coding runtimes.**

> One `.sutra/` source of truth. Many AI runtimes. Policy-driven autonomy. Evidence-backed delivery.

## What is Sutra?

Sutra turns any repository into a governed AI-development workspace with:

- **Reusable agents** — specialized AI roles (backend, frontend, security, QA)
- **Skills** — composable methodology packs (TDD, code review, planning)
- **Commands** — structured workflows (`/implement`, `/review`, `/ship`)
- **Guardrails** — command deny lists, approval gates, path restrictions
- **Evidence** — audit trails for every AI-assisted session

## Quick Start

```bash
# Install
pip install -e .

# Initialize a workspace
cd your-project
sutra init --profile fullstack --runtime claude

# Add Codex as a second runtime
sutra runtime add codex

# Detect your stack
sutra context refresh

# Validate setup
sutra policy validate
sutra doctor

# Sync changes to runtimes
sutra sync
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
| `sutra init` | Initialize a governed workspace |
| `sutra sync` | Sync .sutra/ to configured runtimes |
| `sutra doctor` | Validate workspace integrity |
| `sutra context refresh` | Scan repo and update context |
| `sutra context show` | Display current context |
| `sutra context diff` | Show context changes |
| `sutra policy validate` | Validate policy files |
| `sutra guard enable` | Enable all guardrails |
| `sutra guard disable` | Disable guardrails |
| `sutra guard careful` | Enable destructive-command warnings |
| `sutra guard freeze <path>` | Restrict edits to a path |
| `sutra runtime add <runtime>` | Add a new runtime |
| `sutra report` | Generate evidence report |

## Architecture

```
.sutra/              ← Source of truth (you own this)
├── sutra.yaml       ← Workspace config
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

## License

MIT
