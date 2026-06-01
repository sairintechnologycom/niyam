# External Integrations

**Analysis Date:** 2025-03-05

## APIs & External Services

**Version Control:**
- GitHub REST API - Used for Pull Request lifecycle management.
  - SDK/Client: `urllib.request` (raw integration in `niyam/core/pr.py`)
  - Auth: `GITHUB_TOKEN` environment variable.
- GitHub CLI (`gh`) - Fallback for PR operations if token is missing or API fails.
  - Implementation: `niyam/core/pr.py`

**AI Runtimes:**
- Claude Code - Primary AI development runtime integration.
  - Implementation: Generates `CLAUDE.md` and `.claude/` config via `niyam/runtimes/claude.py`.
- Google Gemini CLI - Secondary AI development runtime integration.
  - Implementation: Generates `GEMINI.md` and `.gemini/` config via `niyam/runtimes/gemini.py`.
- OpenAI Codex CLI - Legacy or alternative runtime integration.
  - Implementation: Generates `AGENTS.md` via `niyam/runtimes/codex.py`.

## Data Storage

**Databases:**
- None (Filesystem-based persistence)

**File Storage:**
- Local filesystem only - Project state and run logs are stored in the `.niyam/` directory of the target repository.

**Caching:**
- Local hook cache - Policy data and guard configurations are cached in `.niyam/hook-cache/` for use by runtime hooks.

## Authentication & Identity

**Auth Provider:**
- GitHub Personal Access Tokens - Used for API access.
  - Implementation: Read from `GITHUB_TOKEN` environment variable.

## Monitoring & Observability

**Error Tracking:**
- None (Local console logging)

**Logs:**
- Mission Evidence - Cryptographically signed markdown reports stored in `.niyam/runs/[mission_id]/evidence.md`.
- Policy Events - JSON logs of blocked/warned actions in `.niyam/evidence/policy-events.json`.

## CI/CD & Deployment

**Hosting:**
- Not applicable (CLI tool)

**CI Pipeline:**
- Niyam CI Verify - Internal verification logic for CI environments.
  - Implementation: `niyam/core/ci.py`
  - Validates: Evidence integrity, policy compliance, and workspace validation commands.

## Environment Configuration

**Required env vars:**
- `GITHUB_TOKEN` - Required for GitHub API integrations (PR review, PR creation).
- `NIYAM_TEST` - Used to trigger mock behaviors during internal testing.

**Secrets location:**
- Not stored by Niyam; relies on environment variables or external CLI (`gh`) auth state.

## Webhooks & Callbacks

**Incoming:**
- None

**Outgoing:**
- GitHub PR Comments - Posted during `niyam review` command.
- GitHub PR Creation - Triggered by `niyam ship` command.

---

*Integration audit: 2025-03-05*
