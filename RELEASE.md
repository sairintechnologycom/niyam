# Release Process

This document outlines the standard process for releasing a new version of Niyam CLI.

## Release Steps

1.  **Prepare the version bump:**
    *   Update the `VERSION` string in `niyam/main.py`.
    *   Ensure all tests pass: `pytest tests/test_cli_smoke.py`.
    *   Update `docs/progress.md` or `CHANGELOG.md` if applicable.

2.  **Commit and Push:**
    *   Commit the changes: `git commit -m "chore: bump version to X.Y.Z"`.
    *   Push to `main`: `git push origin main`.

3.  **Create and Push Tag:**
    *   The PyPI and GitHub release workflow is triggered by a version tag.
    *   Create a tag: `git tag -a vX.Y.Z -m "Release vX.Y.Z"`.
    *   Push the tag: `git push origin vX.Y.Z`.

4.  **Verify Automation:**
    *   Monitor the [GitHub Actions](https://github.com/sairintechnologycom/niyam/actions) tab.
    *   The `pypi-release` job will publish to PyPI.
    *   The `create-release` job will create a GitHub Release with standalone binaries.

## Automation Guardrails

The GitHub workflow is configured to:
- Only publish when a tag matching `v*` is pushed.
- Fail if the version in `niyam/main.py` does not match the git tag (added in v0.3.8+).

---

## Release Notes: v0.4.0 (Experimental Governance Release)

### 1. New Experimental Governance Capabilities
This release introduces a suite of local-first governance and observability capabilities designed to help teams audit, measure, and safely execute AI-assisted development:
- **Repository Scanning (`niyam scan`):** A fast, rule-based scanner verifying environment configurations, dependency lockfiles, test coverage, CI/CD integrations, infrastructure-as-code pin settings, and AI placeholder stubs.
- **Guard Observe Mode (`niyam guard run`):** A command wrapper that logs executed commands, durations, outcomes, and metadata with built-in recursive secret redaction.
- **MCP & Tool Registry (`niyam mcp`):** A lightweight database (`.niyam/mcp-registry.json`) to register, audit, and heuristic-assess risk levels of agent tools and MCP servers.
- **AI Token Cost Tracking (`niyam cost`):** Local ledger to log inputs, outputs, model usage, and session information. Summarizes daily/repository/task cost using a customizable pricing file (`.niyam/pricing.json`).
- **Unified Evidence Report (`niyam evidence generate`):** Synthesizes scan outputs, command history, tool registry risks, and costs into a standardized sign-off markdown document.

### 2. Backward Compatibility Statement
- **Runtimes & Missions:** All core mission execution paths, slash commands (`/implement`, `/review`, `/ship`), and runtime projections remain fully backward-compatible.
- **Migration Path:** Legacy configuration setups using `.sutra/` are migrated seamlessly via `niyam migrate`.
- **Zero-Block Observability:** `niyam guard run` executes wrapped commands without modifying environmental behavior or blocking execution streams.

### 3. Known Limitations
- **Experimental Status:** All new governance features are marked *experimental*. Command-line parameters and configuration schemas are subject to change in upcoming minor releases.
- **Heuristic-Based Risk Assessment:** Tool registry risk classification operates on text keywords and cannot verify dynamic runtime tool behavior.
- **Local Pricing Sync:** Rates are configured manually in `.niyam/pricing.json` and are not updated dynamically from vendor API endpoints.

### 4. Roadmap
- **Active Guardrail Enforcement:** Implementing runtime interception to actively block/warn against unsafe files or commands.
- **Dynamic Cost APIs:** Integrating cost endpoints for automated live pricing sync.
- **Advanced Scan Profiles:** Adding domain-specific rules (e.g., Python, Node, Go best practices).

