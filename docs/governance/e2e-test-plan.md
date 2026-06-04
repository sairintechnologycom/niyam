# Niyam Governance End-to-End Test Plan

This document describes the testing strategy, test fixtures, coverage, and E2E workflow for validating the Niyam AI governance capabilities.

## 1. Overview
The testing strategy validates Niyam's governance features at three levels:
1. **Phase-level validation** (verifying each individual governance capability acts independently).
2. **Backward compatibility validation** (ensuring existing Niyam behaviors and configs are not regressed).
3. **Full E2E governance flow** (scanning repositories, applying policies, managing tool risk registries, logging AI cost, and compiling integrated evidence reports).

## 2. Test Environments (Fixtures)
Three sample workspaces are provided under `test-fixtures/` to simulate different project states:

1. **Clean Minimal App** (`test-fixtures/apps/clean-nextjs-app/`):
   - A healthy codebase containing standard configs, README, lockfile, `.gitignore`, dummy tests, and CI/CD workflow.
   - *Expected result:* Readiness score >= 85, decision `GO` or `CONDITIONAL_GO`, and zero critical findings.

2. **Risky Vibe-Coded App** (`test-fixtures/apps/risky-vibe-app/`):
   - A risky repository containing unprotected `.env`/`.env.local` files, hardcoded secrets, placeholder stubs, and missing test suites, README, or CI/CD pipelines.
   - *Expected result:* Readiness score = 0, decision `NO_GO` or `HIGH_RISK`, and multiple critical/high findings.

3. **Existing Niyam Project** (`test-fixtures/niyam/existing-project/`):
   - A workspace containing pre-governance Niyam YAML configurations.
   - *Expected result:* Legacy commands run without error, old config formats remain valid, and governance blocks are optional.

## 3. Test Suites & Coverage
The automated test suite in `tests/test_governance_integration.py` contains 59 test cases covering:
- **CLI Commands:** Validates command availability and additive behavior of `--help` structures.
- **Scanner MVP:** Evaluates empty directory scans, clean app scans, and risky app scans (checks for `.env`, secrets, stubs, missing readme/tests/CI).
- **Rule Engine:** Checks loading default profiles (`startup`, `team`, `enterprise`) and custom rule evaluators (`file_exists`, `file_missing`, `filename_pattern`, `content_contains`, `content_regex`).
- **Evidence:** Checks report compilation in JSON, Markdown, and HTML, error handling, and sensitive credential/secret redaction.
- **Guard Observe Mode:** Confirms command logging, exit code preservation, and logging details under `observe` mode.
- **Guard Policy Mode:** Asserts blocked command restrictions, warning outputs, and confirmation prompts under `block`/`warn`/`approve` modes.
- **MCP Tool Registry:** Checks registration, listing, detail view, duplicate prevention, and risk report metrics.
- **AI Cost Tracking:** Verifies FinOps token cost logging, summary tables, and category reports.
- **Integrated Evidence Report:** Generates one integrated report containing scan, guard, MCP tool registry, and cost analytics.

## 4. E2E Execution Script
The test suite is verified via the executable bash script `scripts/test-governance-e2e.sh`.

### How to Run Tests
1. **To run the full E2E workflow script:**
   ```bash
   ./scripts/test-governance-e2e.sh
   ```
2. **To run the automated tests via pytest:**
   ```bash
   uv run pytest tests/test_governance_integration.py
   ```

## 5. Limitations
- Guard policy confirmation prompts are simulated in non-interactive testing environments using mocked inputs to Typer's confirmation prompts.
- Subprocess command execution output capturing is disabled by default to prevent secret leak hazards unless `--capture-output` is explicitly supplied.
