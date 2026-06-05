# Niyam E2E Governance Testing

This document outlines the architecture, layout, and instructions for running the Niyam end-to-end (E2E) test suite.

## Testing Architecture

The E2E tests validate Niyam's command-line interface and governance lifecycle under isolated sandbox conditions. Each test runs Niyam in a temporary directory containing dedicated application fixtures, ensuring deterministic and offline behavior.

```
tests/e2e/
├── conftest.py                       # Shared test fixtures & run_cli helper
├── fixtures/                         # Static test application layouts
│   ├── clean_app/                    # Passing repository configuration
│   ├── risky_app/                    # High/critical risks & exposed secrets
│   ├── ai_app/                       # AI-governance risk files
│   └── iac_app/                      # IaC config layout
├── test_scan_e2e.py                  # Scan execution & readiness scoring
├── test_guard_e2e.py                 # Observe mode & command blocking
├── test_mcp_e2e.py                   # Tool registry operations
├── test_evidence_e2e.py              # Audit report generation & redaction
└── test_backward_compatibility_e2e.py # Legacy config loading & help output
```

## E2E Scenarios Covered

The test suite asserts the following behaviors:

1. **Legacy Commands**: Commands like `niyam doctor` and `niyam init` remain functional.
2. **Help Information**: All governance command categories display help prompts correctly.
3. **Clean Scan**: Scans of standard codebases return optimal scores ($\ge 85$) and `GO` decisions.
4. **Risky Scan**: Scans of risky codebases report critical/high findings.
5. **Score Overrides**: Blockers correctly force final status to `NO_GO` or `HIGH_RISK`.
6. **JSON Output**: Reports can be formatted and written to standard JSON.
7. **Markdown Output**: Markdown reports include readiness summaries.
8. **Observe Logs**: Operations under `guard run` are tracked in log buffers.
9. **Block Command**: Denied command patterns trigger immediate block responses and exit code 1.
10. **MCP Registry**: Registers, lists, describes, and approves agent-accessible tools.
11. **Evidence Consolidation**: Consolidates registry posture, execution metrics, and scan results.
12. **Secret Redaction**: Sensitive strings (AWS keys, OpenAI tokens) are redacted from logs and reports.
13. **Backward Compatibility**: Workspaces lacking the newer `governance` schema load defaults safely.
14. **CI Readiness**: Commands operate cleanly offline and respond to environment hooks.

## Run Instructions

Execute the E2E tests using `pytest`:

```bash
pytest tests/e2e/
```

To run a specific test file:

```bash
pytest tests/e2e/test_scan_e2e.py
```

## Mock Environment

To ensure tests execute deterministically without cloud credentials or external dependencies, `conftest.py` configures a local mock directory containing mock scripts for external scanners (e.g. `checkov`, `gitleaks`, `semgrep`, `trivy`) and prepends it to the `PATH` during CLI runs.
