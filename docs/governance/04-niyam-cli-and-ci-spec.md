# CLI & CI/CD Specification: Niyam Governance

This document provides a reference for the Niyam Command Line Interface (CLI) commands, options, exit codes, CI/CD pipeline integrations (GitHub Actions, Azure DevOps), and supported output formats.

---

## 1. CLI Commands & Options

Niyam provides five primary subcommands for repository governance under the main CLI package:

### A. Repository Scanning (`niyam scan`)
Scan the repository for production-readiness and code risk factors.
* **Syntax:** `niyam scan [PATH] [OPTIONS]`
* **Arguments:**
  - `PATH`: Absolute or relative path to the project directory to scan (defaults to `.`).
* **Options:**
  - `--profile`, `-p`: The strictness rules profile to apply: `startup` (lenient), `team` (medium), `enterprise` (strict), or `regulated` (hardened). Defaults to `startup`.
  - `--output`, `-o`: Output format type: `text`, `json`, `markdown`, or `sarif`. Defaults to `text`.
  - `--report-file`, `-f`: Path to write the formatted report (e.g., `niyam-report.md`).
  - `--rules`: Path to custom rules YAML file to append to the profile rules.
  - `--fail-on`: Fail scan (exit code `2`) if a finding with this severity or higher is discovered: `critical`, `high`, `medium`, `low`, `info`.
  - `--baseline`: Path to baseline JSON file containing accepted findings to ignore during evaluation.
  - `--create-baseline`: Path to write the current scan findings as a baseline JSON file.

### B. Action Governance (`niyam guard`)
Manage runtime security guardrails, command wrapping, and path restrictions.
* **Commands:**
  - `niyam guard enable`: Enable all configured guardrails (installs pre-commit/pre-push Git hooks).
  - `niyam guard disable`: Disable all active guardrails.
  - `niyam guard careful`: Toggle destructive command warnings (warn on patterns like `rm -rf` or database drops).
  - `niyam guard freeze <PATH>`: Mark a directory path as read-only, preventing any edits or writes by AI agents.
  - `niyam guard run [OPTIONS] -- <COMMAND>`: Run a shell command under Niyam guard observation.
    * *Options:*
      - `--capture-output`: Capture standard output and error streams in local logs.
      - `--mode`: Override current guard policy mode: `observe`, `warn`, `approve`, `block`.
  - `niyam guard status`: Display current active guard metrics, frozen paths, and Git hook status.
  - `niyam guard logs [OPTIONS]`: Show recent observed actions logged by Niyam guard.
    * *Options:*
      - `--limit`, `-l`: Number of log entries to display (defaults to `10`).

### C. MCP & Tool Registry (`niyam mcp`)
Manage third-party Model Context Protocol (MCP) servers and external tools.
* **Commands:**
  - `niyam mcp register <NAME> [OPTIONS]`: Register a new tool or MCP server.
    * *Options:*
      - `--type`: Tool type: `mcp_server`, `api`, `cli`, `local_tool`, `browser`, `other`.
      - `--command-or-url`: Execution command or URL location of the tool.
      - `--owner`: Department or individual responsible for the tool.
      - `--risk`: Risk classification: `low`, `medium`, `high`, `critical`.
      - `--approved`: Approve the tool for agent consumption: `true` or `false`.
      - `--capabilities`: Comma-separated capabilities of the tool (e.g., `read_file,write_file`).
      - `--data-access`: Description of data accessed by the tool.
      - `--network-access`: Description of network endpoints accessed by the tool.
      - `--requires-approval`: Set if tool execution needs explicit confirmation: `true` or `false`.
      - `--notes`: Description or context for the registration.
      - `--update`: Update tool definition if already registered.
  - `niyam mcp list`: Display all registered tools, owners, risk levels, and approval status.
  - `niyam mcp show <NAME>`: Render detailed parameters for a registered tool.
  - `niyam mcp approve <NAME>`: Approve a registered tool.
  - `niyam mcp risk-report`: Output risk metrics and security classification stats of all registered tools.

### D. FinOps Cost Engine (`niyam cost`)
Track AI session token consumption and calculate software budgets.
* **Commands:**
  - `niyam cost log [OPTIONS]`: Record an LLM token transaction event.
    * *Options:*
      - `--task-id`: Unique identifier for the developer task.
      - `--tool-name`: Tool name (e.g., `claude-code`).
      - `--model`: Model used (e.g., `claude-3-5-sonnet`).
      - `--input-tokens`: Count of prompt tokens.
      - `--output-tokens`: Count of completion tokens.
      - `--status`: Transaction status: `success` or `failed`.
  - `niyam cost summary`: Display aggregate input/output tokens and cost in USD.
  - `niyam cost report`: Output detailed cost table breakdown grouped by session, model, and wasted budget.

### E. Evidence Hub (`niyam evidence`)
Compile audit-ready evidence reports.
* **Syntax:** `niyam evidence generate [OPTIONS]`
* **Options:**
  - `--from`: Path to a pre-generated scan results JSON file.
  - `--format`: Report output format: `markdown`, `json`, `html`. Defaults to `markdown`.
  - `--output`, `-o`: File path to save the generated report.
  - `--include`: Comma-separated sections to include in the joint report: `scan,guard,mcp,cost`. Defaults to all.

---

## 2. Command Exit Codes

To ensure seamless integration with script automations and CI/CD pipelines, Niyam implements standardized CLI exit codes:

| Exit Code | Classification | Description |
| --- | --- | --- |
| **`0`** | Success | Command completed successfully. For scans, the project readiness status is `GO`, `CONDITIONAL_GO`, or `HIGH_RISK` (with no blocking findings). |
| **`1`** | General Error | Unexpected runtime crash, unhandled code exceptions, or general command failures. |
| **`2`** | Gating Failure | Scan failed due to policy breaches. Triggered when the readiness status is `NO_GO` (readiness score $< 50$) or when findings exceed the `--fail-on` severity threshold. |
| **`3`** | Config Error | Invalid configuration, bad input/output paths, or unsupported CLI options. |
| **`4`** | System I/O Error | File read/write failures (e.g., unable to save the evidence report to the specified destination). |
| **`5`** | Access Denied | Permission issues or unauthorized operations (e.g., trying to modify files inside a frozen path). |

---

## 3. Output Formats

Niyam supports multiple output formats to accommodate both human review and automated parsing:

1. **`text` (Default):** Prints structured, color-coded terminal interfaces using the `rich` console library. Best for developer interactive loops.
2. **`json`:** Outputs standard parseable JSON representations of scan results, tool catalogs, or cost events. Best for custom scripting.
3. **`markdown`:** Generates clean, GitHub-flavored Markdown documents containing tables, bullet points, and callouts. Best for pull request comments or static documentation.
4. **`sarif`:** Static Analysis Results Interchange Format (SARIF v2.1.0) JSON payload. Enables native security integration with GitHub Code Scanning alerts and security dashboards.

---

## 4. CI/CD Pipeline Integration

### A. GitHub Actions Integration
Add a workflow file under `.github/workflows/niyam-governance.yml` to gate pull requests based on readiness checks.

```yaml
name: Niyam Governance Scan

on:
  pull_request:
    branches: [ main ]

jobs:
  governance-check:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-size: '3.11'

      - name: Install Dependencies & Niyam
        run: |
          pip install --upgrade pip
          pip install .
          # Optional: Install external scanners to enhance check depth
          sudo apt-get update && sudo apt-get install -y gitleaks

      - name: Run Niyam readiness check
        run: |
          # Fails build if any critical or high findings are found, or if score is < 50
          niyam scan . --profile enterprise --fail-on high --output sarif --report-file niyam-report.sarif

      - name: Upload SARIF report to GitHub Security
        uses: github/codeql-action/upload-sarif@v3
        if: always()
        with:
          sarif_file: niyam-report.sarif
```

### B. Azure DevOps Pipeline Integration
Configure `azure-pipelines.yml` to execute Niyam checks in Azure Repos environments.

```yaml
trigger:
  - main

pr:
  - main

pool:
  vmImage: 'ubuntu-latest'

steps:
  - task: UsePythonVersion@0
    inputs:
      versionSpec: '3.11'
    displayName: 'Set up Python'

  - script: |
      pip install --upgrade pip
      pip install .
    displayName: 'Install Niyam'

  - script: |
      # Run scan and output Markdown report
      niyam scan $(System.DefaultWorkingDirectory) --profile team --fail-on high --output markdown --report-file $(Build.ArtifactStagingDirectory)/niyam-report.md
    displayName: 'Execute Niyam Readiness Scan'

  - task: PublishBuildArtifacts@1
    inputs:
      PathtoPublish: '$(Build.ArtifactStagingDirectory)/niyam-report.md'
      ArtifactName: 'NiyamGovernanceReport'
      publishLocation: 'Container'
    displayName: 'Publish Governance Report'
```
