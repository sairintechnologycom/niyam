# External Integrations

**Analysis Date:** 2025-03-05

## APIs & External Services

**Version Control:**
- GitHub REST API - Used for Pull Request lifecycle management.
  - SDK/Client: `urllib.request` (raw integration in `sutra/core/pr.py`)
  - Auth: `GITHUB_TOKEN` environment variable.
- GitHub CLI (`gh`) - Fallback for PR operations if token is missing or API fails.
  - Implementation: `sutra/core/pr.py`

**AI Runtimes:**
- Claude Code - Primary AI development runtime integration.
  - Implementation: Generates `CLAUDE.md` and `.claude/` config via `sutra/runtimes/claude.py`.
- Google Gemini CLI - Secondary AI development runtime integration.
  - Implementation: Generates `GEMINI.md` and `.gemini/` config via `sutra/runtimes/gemini.py`.
- OpenAI Codex CLI - Legacy or alternative runtime integration.
  - Implementation: Generates `AGENTS.md` via `sutra/runtimes/codex.py`.

## Data Storage

**Databases:**
- None (Filesystem-based persistence)

**File Storage:**
- Local filesystem only - Project state and run logs are stored in the `.sutra/` directory of the target repository.

**Caching:**
- Local hook cache - Policy data and guard configurations are cached in `.sutra/hook-cache/` for use by runtime hooks.

## Authentication & Identity

**Auth Provider:**
- GitHub Personal Access Tokens - Used for API access.
  - Implementation: Read from `GITHUB_TOKEN` environment variable.

## Monitoring & Observability

**Error Tracking:**
- None (Local console logging)

**Logs:**
- Mission Evidence - Cryptographically signed markdown reports stored in `.sutra/runs/[mission_id]/evidence.md`.
- Policy Events - JSON logs of blocked/warned actions in `.sutra/evidence/policy-events.json`.

## CI/CD & Deployment

**Hosting:**
- Not applicable (CLI tool)

**CI Pipeline:**
- Sutra CI Verify - Internal verification logic for CI environments.
  - Implementation: `sutra/core/ci.py`
  - Validates: Evidence integrity, policy compliance, and workspace validation commands.

## Environment Configuration

**Required env vars:**
- `GITHUB_TOKEN` - Required for GitHub API integrations (PR review, PR creation).
- `SUTRA_TEST` - Used to trigger mock behaviors during internal testing.

**Secrets location:**
- Not stored by Sutra; relies on environment variables or external CLI (`gh`) auth state.

## Webhooks & Callbacks

**Incoming:**
- None

**Outgoing:**
- GitHub PR Comments - Posted during `sutra review` command.
- GitHub PR Creation - Triggered by `sutra ship` command.

---

*Integration audit: 2025-03-05*
