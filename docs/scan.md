# Niyam Repository Scanner (`niyam scan`)

> [!WARNING]
> The scanner and rule engine are currently **experimental**. Custom rule structures and profile schemas are subject to change.

The `niyam scan` command is a local repository scanner that assesses production readiness for AI-assisted applications. It validates security postures, configuration files, test suites, and AI-risk indicators.

---

## 1. Profiles & Severity Gates

Niyam supports three built-in scan profiles depending on the target strictness:

| Profile | Strictness | Target Audience | Key Behavior |
| --- | --- | --- | --- |
| `startup` | Lenient | Early-stage products / rapid MVPs | Minimal warnings. Focuses on critical secrets exposure. |
| `team` | Medium | Collaborative projects | Flags missing lockfiles, missing test files, and high AI stubs. |
| `enterprise` | Strict | Production enterprise codebases | Strict requirements. Elevates lack of testing, health routes, CI/CD pipelines, and IaC policies to high/critical severity. |

Use `--profile` option to toggle profiles:
```bash
niyam scan . --profile team
```

---

## 2. Rule Engine & Match Types

The scanner uses a lightweight YAML-based rule engine. Standard rules are defined under:
```
niyam/governance/rules/
  ├── startup.yaml
  ├── team.yaml
  └── enterprise.yaml
```

Each rule supports the following attributes:
- `id`: Unique identifier (e.g. `SEC001`, `DEP001`).
- `title`: Short title of the rule.
- `category`: Category identifier (e.g., `secrets`, `dependencies`, `env_config`, `health`, `docs`, `tests`, `cicd`, `ai_risk`, `iac`).
- `severity`: Rule severity (`critical`, `high`, `medium`, `low`, `info`).
- `description`: Detailed explanation of the risk.
- `recommendation`: Remediation steps.
- `match`: The match block defining how the rule evaluates.

### Supported Match Types
The scanner evaluates repositories using 7 core match types:

1. **`file_exists`**: Verifies that a specific file is present (e.g. `README.md`).
2. **`file_missing`**: Verifies that a file is not present (e.g. flagging left-over local env files).
3. **`filename_pattern`**: Searches for files matching glob patterns (e.g. `.env.*`).
4. **`directory_exists`**: Verifies the presence of a folder (e.g. `tests/`).
5. **`directory_missing`**: Ensures a folder is absent (e.g. `tmp/`).
6. **`content_contains`**: Searches files for raw string matches (e.g. `TODO` placeholder stubs).
7. **`content_regex`**: Runs regex matches to find patterns like API keys, secrets, or unpinned base images.

### Example Custom Rule Configuration
To run scanning with custom rules, pass a path to your rules file via `--rules`:
```yaml
# custom-rules.yaml
rules:
  - id: custom-secrets-check
    title: Custom Password Indicator
    category: secrets
    severity: critical
    description: Code contains hardcoded credentials.
    recommendation: Extract secrets to environment variables.
    match:
      type: content_regex
      patterns:
        - "password\\s*=\\s*['\"][^'\"]+['\"]"
```
Execute with:
```bash
niyam scan . --rules custom-rules.yaml
```

---

## 3. Command Usage

```bash
# Scan the current directory using default profile
niyam scan .

# Run scan and format output as JSON or Markdown
niyam scan . --output json
niyam scan . --output markdown

# Save scan report to a file
niyam scan . --report-file niyam-readiness.md

# Fail CLI execution (exit code 2) if finding is critical or higher
niyam scan . --fail-on critical
```

---

## 4. CLI Options

* `--profile, -p`: The strictness profile to apply (`startup`, `team`, `enterprise`).
* `--output, -o`: Format print type (`text`, `json`, `markdown`).
* `--report-file, -f`: Output path to save the generated markdown report.
* `--rules`: Path to custom rules YAML file.
* `--fail-on`: Exits with code `2` if a finding meets or exceeds this severity threshold (`critical`, `high`, `medium`, `low`, `info`).

---

## 5. Exit Codes

Niyam's repository scanner returns standardized exit codes:

* `0`: Success (no findings exceeded `--fail-on` threshold, decision is `GO` or `CONDITIONAL_GO`).
* `2`: Findings exceed fail threshold (or decision is `NO_GO` due to hard blockers).
* `3`: Invalid configuration (e.g. invalid profile, file not found, bad CLI options, invalid YAML).
* `4`: Scan runtime error (e.g. workspace parsing error, read/write permissions exception).
* `1`: Unexpected error.

---

## 6. Hard Blockers (Force NO_GO)

Certain critical findings act as hard blockers, immediately dropping the readiness score to $\le 49$ and overriding the decision to `NO_GO`:
1. **Committed environment files with possible secrets:** A committed `.env` or configuration file that is not empty and matches credential markers.
2. **Obvious Private Keys:** A committed file containing a PEM-encoded private key (`-----BEGIN ... PRIVATE KEY-----`).
3. **Public Cloud Exposure:** Hardcoded identifiers resembling public cloud credential patterns (such as AWS key IDs `AKIA...` or Azure connection strings containing `AccountKey=`).

---

## 7. Security & Redaction Behavior

* **100% Offline by Default:** The rule engine evaluates checks completely locally. It does not call remote API endpoints.
* **Auto-Sanitization:** All outputs (stdout console summaries, JSON, and Markdown reports) pass through Niyam's central redaction utility. Before any output is written, hardcoded secrets (API keys, connection strings, private keys, passwords) are automatically replaced with `[REDACTED_SECRET]` to prevent leaks in logs, reports, or CI/CD logs.

