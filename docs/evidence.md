# Niyam Evidence Report Generation (`niyam evidence`)

> [!WARNING]
> The evidence generation feature is currently **experimental**. Generated schemas, markdown layouts, and option names are subject to change.

The `niyam evidence` module allows compiling all local auditing logs, repository scan results, model token costs, and registered tool lists into a single, unified audit-ready **Evidence Report**. This serves as a production gate or compliance record.

---

## 1. Evidence Commands

To generate an evidence report locally:

```bash
# Generate a complete report in markdown (default) including all sections
niyam evidence generate

# Save report to a specific file
niyam evidence generate --output docs/production-evidence.md

# Compile report from a specific scan results file
niyam evidence generate --from .niyam/scan-results.json

# Specify format as HTML
niyam evidence generate --format html --output docs/evidence.html
```

---

## 2. Command Options

The `niyam evidence generate` command supports these options:

- `--from`: Specifies a path to an existing scan results JSON file. If omitted, a fresh scan is run.
- `--format`: Format of the report output. Supported values are:
  - `markdown` (default)
  - `json`
  - `html`
- `--output` / `-o`: Output file path. If omitted, the report is printed to standard output.
- `--include`: Comma-separated sections to include. Defaults to `scan,guard,mcp,cost`. If a section data file is missing (e.g. no guard actions logged yet), it is skipped gracefully.

---

## 3. Generated Report Sections

A fully compiled report includes:

1. **Executive Summary:** Overview of project, git branch, commit ID, scan profile, and timestamp.
2. **Production Readiness Score:** Gate decision (`GO`, `CONDITIONAL_GO`, `HIGH_RISK`, `NO_GO`) and score (0-100).
3. **Critical & High Findings:** Prioritized security/configuration risks that must be resolved.
4. **Recommended Remediation Plan:** Detailed list of warnings and steps to fix them.
5. **Agent Governance Activity:** Session audit trail extracted from `.niyam/logs/guard-actions.jsonl`.
6. **Tool/MCP Risk Posture:** Catalog of registered tools, API servers, and their respective heuristic risk levels.
7. **AI Engineering Cost Summary:** High-level token count and budget totals.

---

## 4. Security & Redaction

The evidence engine enforces strict security filters before writing the report:
- **Recursive Redaction:** Niyam's key/credentials regex checks are run recursively on all fields (dicts, lists, text strings) extracted from the logs.
- **Credential Masking:** Environment variables, authorization headers, passwords, and private keys are replaced with `[REDACTED]`.
- **Local Isolation:** Report compiling does not connect to external servers or send data outside the local system.
