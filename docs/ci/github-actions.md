# Integrating Niyam with GitHub Actions

This guide explains how to set up `niyam scan` as a pull request quality gate and static analysis reporting tool in GitHub Actions.

## 1. Basic Pull Request Gate

This workflow scans the repository on every PR, failing the run if any `high` or `critical` severity findings are detected:

```yaml
name: Niyam Governance Scan

on:
  pull_request:
    branches: [ main, dev ]

jobs:
  governance-scan:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install Dependencies
        run: |
          python -m pip install --upgrade pip
          pip install niyam

      - name: Run Niyam scan
        run: |
          niyam scan . --profile enterprise --fail-on high --report-file niyam-report.md

      - name: Upload Scan Report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: niyam-readiness-report
          path: niyam-report.md
```

## 2. Using Baselines to Prevent Failure on Legacy Code

For existing repositories with known legacy issues, run with a baseline so only new findings trigger build failures:

```yaml
      - name: Run Niyam scan with Baseline
        run: |
          niyam scan . --profile enterprise --baseline .niyam/baseline.json --fail-on high
```

## 3. GitHub Security Upload (SARIF)

If you are using GitHub Advanced Security, you can output findings in SARIF format and upload them to the GitHub Security tab:

```yaml
      - name: Run Niyam scan (SARIF)
        run: |
          niyam scan . --output sarif --report-file niyam-findings.sarif

      - name: Upload SARIF report
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: niyam-findings.sarif
```
