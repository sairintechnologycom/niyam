# Niyam Evidence Report Generation (`niyam evidence`)

The `niyam evidence` module compiles all local auditing logs, repository scan results, model token costs, and registered tool lists into a single, unified audit-ready **Evidence Report**. This serves as a production gate or compliance record.

---

## 1. Evidence Commands

To generate an evidence report locally:

```bash
# Generate a complete report in markdown (default) including all sections
niyam evidence generate

# Save report to a specific file
niyam evidence generate --output docs/production-evidence.md

# Compile report from a specific scan results file
niyam evidence generate --from .niyam/reports/scan.json

# Specify format as JSON
niyam evidence generate --format json --output docs/evidence.json

# Specify format as HTML
niyam evidence generate --format html --output docs/evidence.html
```

---

## 2. Command Options

The `niyam evidence generate` command supports these options:

- `--from`: Specifies a path to an existing scan results JSON file. If omitted, Niyam searches for a default scan report under `.niyam/reports/scan.json` (or falling back to `.sutra/reports/scan.json`). If no default report is found, the command fails cleanly with a descriptive error.
- `--format`: Format of the report output. Supported values are:
  - `markdown` (default)
  - `json`
  - `html`
- `--output` / `-o`: Output file path. If omitted, the report is printed to standard output.
- `--include`: Comma-separated sections to include. Defaults to `scan,guard,mcp,cost`. If a section data file is missing, it is skipped gracefully.

---

## 3. Generated Report Sections

A fully compiled report includes these 10 sections:

1. **Executive Summary:** High-level summary of repository readiness status.
2. **Project Metadata:** Details about the project name, branch, and generation timestamp.
3. **Readiness Score:** Production readiness percentage (0-100).
4. **Launch Decision:** Gate recommendation (`GO`, `CONDITIONAL GO`, `HIGH RISK`, `NO GO`).
5. **Decision Reason:** Rationale explaining score deductions or blocker triggers.
6. **Critical and High Findings:** Prioritized list of major findings.
7. **Risk Register:** Summary count table of findings categorized by severity.
8. **Recommended Remediation Plan:** Step-by-step guidance to resolve identified findings.
9. **AI-Assisted Development Governance Notes:** Active policy status, Niyam Guard action summary metrics (total actions, blocked, warned, failed, top categories, latest session), registered tool posture, and cost logs.
10. **Appendix Summary:** Git commit details, author info, and redaction metadata.

---

## 4. Evidence Output Schema (JSON Format)

When outputting to JSON (`--format json`), the report conforms to the following schema structure:

- `schema_version`: Semantic version of the evidence schema (e.g., `"1.0.0"`).
- `generated_at`: ISO 8601 UTC timestamp of report generation.
- `source`: Git metadata descriptor containing the branch and commit SHA.
- `project`: Project name configured in `niyam.yaml`.
- `readiness_score`: Integer (0-100) representing project readiness.
- `decision`: Decision status string (`GO`, `CONDITIONAL_GO`, `HIGH_RISK`, `NO_GO`).
- `decision_reason`: Detailed textual explanation of the final gate status.
- `risk_summary`: Object summarizing finding counts by severity.
- `findings_summary`: List of brief finding details (ID, severity, category, title, file_path).
- `remediation_plan`: List of remediation instructions mapped from findings.
- `redaction_status`: Object indicating that the report passed through redaction (`{"redacted": true, "engine": "niyam-redaction"}`).
- `guard_summary`: Object containing Niyam Guard action summaries:
  - `total_actions`: Total commands observed.
  - `total_blocked`: Total commands blocked before execution.
  - `total_warned`: Total commands that printed warnings.
  - `total_approval_required`: Total commands requiring user confirmation.
  - `total_failed`: Total commands that exited with code != 0.
  - `top_command_categories`: List of the top executed command categories.
  - `latest_session`: Breakdown of metrics for the latest active session.
  - `latest_actions_summary`: List of recent command details.

---

## 5. Security & Redaction

Niyam enforces strict data security to ensure report shareability:
- **No Raw Secrets:** The shared redaction engine recursively filters all dictionary keys and text values, replacing matched secrets (e.g., API keys, private keys, database URLs, git tokens) with `[REDACTED_SECRET]`.
- **No Source Code:** Full file contents are omitted; only path names and line numbers are listed in finding registers.
- **Local Isolation:** All formatting, templating, and redaction logic runs completely offline. No data is sent to external APIs or cloud platforms.

---

## 6. Audit & Shareability Guidance

When sharing evidence reports with external auditors or security reviewers:
1. **Prefer Markdown for Human Review:** Exporting to Markdown produces a clean, structured document suitable for commit-based code reviews and release notes.
2. **Prefer JSON for Automated CI/CD Gates:** If integrating Niyam into a CI/CD pipeline, parse the JSON output to automatically block deployment if `decision` is `NO_GO`.
3. **Commit Reports Safely:** Reports written to the default directory `.niyam/reports/` are redacted. Ensure they are kept in source control or ignored according to your team policy.
4. **Sample Report:** Refer to [evidence-sample.md](file:///Users/bhushan/Documents/Projects/sutra/docs/evidence-sample.md) for a reference report showing all 10 sections in action.
