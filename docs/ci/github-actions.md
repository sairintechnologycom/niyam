# Integrating Niyam with GitHub Actions

This guide explains how to set up `niyam scan` as a pull request quality gate and static analysis reporting tool in GitHub Actions.

## 1. Using the Official Niyam GitHub Action

The easiest way to integrate Niyam is using the official action. This automatically handles Python setup, Niyam installation, and readiness scoring.

```yaml
name: Niyam Governance Verify

on:
  pull_request:
    branches: [ main, dev ]

jobs:
  niyam-verify:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Niyam Governance Verify
        uses: sairintechnology/niyam@main  # Or use a specific version tag
        with:
          target-branch: 'main'
          min-score: 70
          strict: true
          public-key: ${{ secrets.NIYAM_PUBLIC_KEY }}
```

## 2. Basic Pull Request Gate (Manual Script)

If you prefer to run the CLI manually, you can use the following steps:

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
