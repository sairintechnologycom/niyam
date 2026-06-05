# Niyam Repository Scanner (`niyam scan`)

> [!WARNING]
> The scanner and rule engine are currently **experimental**. Custom rule structures and profile schemas are subject to change.

The `niyam scan` command is a local repository scanner that assesses production readiness for AI-assisted applications. It validates security postures, configuration files, test suites, and AI-risk indicators.

---

## 1. Profiles & Severity Gates

Niyam supports four built-in scan profiles depending on the target strictness:

| Profile | Strictness | Target Audience | Key Behavior |
| --- | --- | --- | --- |
| `startup` | Lenient | Early-stage products / rapid MVPs | Minimal warnings. Focuses on critical secrets exposure. |
| `team` | Medium | Collaborative projects | Flags missing lockfiles, missing test files, and high AI stubs. |
| `enterprise` | Strict | Production enterprise codebases | Strict requirements. Elevates lack of testing, health routes, CI/CD pipelines, and IaC policies to high/critical severity. |
| `regulated` | Very Strict | Regulated compliance environments | Strictest validation. Elevates all key gaps (testing, CI/CD, lockfiles, etc.) to critical severity blockers. |

Use `--profile` option to toggle profiles:
```bash
niyam scan . --profile team
```

---

## 2. Rule Engine & Match Types

The scanner uses a lightweight YAML-based rule engine. Standard rules are defined under:
```
niyam/governance/rules/profiles/
  ├── startup.yaml
  ├── team.yaml
  ├── enterprise.yaml
  └── regulated.yaml
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

## 6. Deterministic Readiness Scoring

Niyam uses a deterministic scoring engine to assess readiness across 8 distinct dimensions, weighted by profile strictness (Startup, Team, and Enterprise):

| Dimension | Category Mapping | Startup Weight | Team Weight | Enterprise Weight |
| --- | --- | --- | --- | --- |
| **Secrets and credentials** | `secrets` | 20% | 25% | 30% |
| **Authentication and authorization** | `auth`, `authentication`, `authorization` | 15% | 15% | 20% |
| **Dependencies and supply chain** | `dependencies` | 15% | 10% | 10% |
| **Cloud/IaC exposure** | `iac`, `cloud`, `env_config` | 15% | 15% | 15% |
| **Production operations** | `health`, `cicd`, `tests`, `ops` | 10% | 10% | 10% |
| **AI-specific risks** | `ai_risk`, `ai` | 10% | 10% | 5% |
| **Data protection** | `data_protection`, `data`, `privacy` | 10% | 10% | 7% |
| **Documentation and runbook** | `docs`, `documentation` | 5% | 5% | 3% |
| **Total** | | **100%** | **100%** | **100%** |

Deductions are calculated per-finding based on severity:
- `critical`: 25 points deduction
- `high`: 15 points deduction
- `medium`: 8 points deduction
- `low`: 3 points deduction
- `info`: 0 points deduction

The score for each dimension is calculated as `max(0, weight - sum(deductions))`, and the total readiness score is the sum of all dimension scores (clamped between 0 and 100).

---

## 7. Decision Engine & Thresholds

Based on the final readiness score, Niyam maps the repository state to a launch readiness decision:

* **`85–100`**: `GO` — The repository meets all major quality and safety standards.
* **`70–84`**: `CONDITIONAL_GO` — Mild risks detected. Suitable to proceed with caution.
* **`50–69`**: `HIGH_RISK` — Moderate or multiple safety issues. Not recommended for automated production release.
* **`0–49`**: `NO_GO` — Critical safety/security risks present. Blocking launch.

---

## 8. Hard Blocker Rules (Overrides)

Certain blocker rules bypass the numeric score and enforce a maximum decision and score caps:

1. **Critical Secrets finding:** Any critical severity secrets leak forces decision to `NO_GO` (score capped at $\le 49$).
2. **Private Key exposure:** Any private key detected in code/files forces decision to `NO_GO` (score capped at $\le 49$).
3. **Missing Authentication on API (Enterprise profile):** If profile is `enterprise` and an unauthenticated API endpoint/route is detected, it forces decision to `NO_GO` (score capped at $\le 49$).
4. **High/Critical public IaC exposure:** Any high/critical public exposure finding in IaC/cloud configs forces decision to `HIGH_RISK` or `NO_GO` (score capped at $\le 69$ or $\le 49$).
5. **More than 3 High findings:** If there are more than 3 high severity findings of any category, the decision is capped at `HIGH_RISK` maximum (score capped at $\le 69$).

---

## 9. Security & Redaction Behavior

* **100% Offline by Default:** The rule engine evaluates checks completely locally. It does not call remote API endpoints.
* **Auto-Sanitization:** All outputs (stdout console summaries, JSON, and Markdown reports) pass through Niyam's central redaction utility. Before any output is written, hardcoded secrets (API keys, connection strings, private keys, passwords) are automatically replaced with `[REDACTED_SECRET]` to prevent leaks in logs, reports, or CI/CD logs.

---

## 10. Rule Authoring Guide

Each governance rule is a YAML object that defines a check performed against the repository files.

### Rule Attributes
A valid rule must specify:
* `id` (string): Unique rule identifier (e.g. `SEC001`, `DEP001`).
* `title` (string): Short title summarizing the finding.
* `category` (string): Mapping category (e.g. `secrets`, `dependencies`, `env_config`, `health`, `docs`, `tests`, `cicd`, `ai_risk`).
* `severity` (string): Severity level (`critical`, `high`, `medium`, `low`, `info`).
* `description` (string): Description of the risk or issue.
* `recommendation` (string): Recommended steps to fix the issue.
* `match` (mapping): The match definition structure.

Optional attributes:
* `confidence` (string): Finding confidence level (`high`, `medium`, `low`). If not set, defaults based on match type.
* `remediation_effort` (string): Level of effort (`low`, `medium`, `high`). If not set, defaults based on category.
* `tags` (list of strings): Custom tags (e.g. `['security', 'secrets']`).

### Match Definition Schema
The `match` block must support:
* `type` (string): The match type (see below).
* `patterns` (list of strings): Patterns to look for (filenames, directories, regexes, strings).
* `files` (list of strings, optional): Sub-selection of files to check when running `content_contains` or `content_regex` (e.g. `['*.py', '*.ts']`).
* `if_exists` (string or list of strings, optional): Pre-condition pattern; rule is evaluated only if a file matching this exists.

### Supported Match Types
1. **`file_exists`**: Match matches if a file matching any pattern exists.
2. **`file_missing`**: Match matches if NO files match any pattern.
3. **`directory_exists`**: Match matches if a directory matches any pattern.
4. **`directory_missing`**: Match matches if NO directory matches any pattern.
5. **`filename_pattern`**: Match matches files whose names match the glob patterns.
6. **`content_contains`**: Match searches for raw string patterns in files.
7. **`content_regex`**: Match searches for regular expression patterns in files.

---

## 11. Custom Rule Example

Here is a custom rules file that ensures a specific security configuration is set and a legacy config folder is absent:

```yaml
# custom-rules.yaml
rules:
  - id: custom-auth-config
    title: Custom Auth Policy File Missing
    category: auth
    severity: high
    description: Highly-regulated applications must contain a standard auth-policy.json file.
    recommendation: Add and define auth-policy.json in the repository root.
    match:
      type: file_missing
      patterns:
        - "auth-policy.json"

  - id: legacy-config-dir
    title: Legacy Config Directory Exposed
    category: env_config
    severity: medium
    description: Old legacy-config folder should not be present in production-bound builds.
    recommendation: Delete the legacy-config folder from the workspace.
    match:
      type: directory_exists
      patterns:
        - "legacy-config"
```

To run:
```bash
niyam scan . --rules ./custom-rules.yaml
```

---

## 12. Rule Validation & Errors

Rules are strictly validated against their schema prior to execution. If a rule fails validation:
1. The scan execution halts immediately.
2. An error is printed to stderr indicating the rule `id` and the specific fields that are missing or malformed.
3. The CLI exits with code `3` (Invalid configuration).

### Example Validation Errors

* **Missing Required Field:**
  ```
  Configuration Error: Validation error: Rule 'custom-rule-1' is missing required field: description, recommendation, match
  ```
* **Unsupported Match Type:**
  ```
  Configuration Error: Rule 'custom-rule-2' has unsupported match type 'invalid_type'. Supported types: content_contains, content_regex, directory_exists, directory_missing, file_exists, file_missing, filename_pattern
  ```
* **Missing Patterns for Match Type:**
  ```
  Configuration Error: Rule 'custom-rule-3' of type 'file_exists' must specify 'patterns'.
  ```

---

## 13. Scan Baseline & Risk Acceptance

Niyam supports baseline suppression to help teams adopt the tool in existing repositories without causing builds/gating checks to fail on day one due to legacy issues.

### Creating a Baseline
To capture all current scan findings and save them to a baseline file:
```bash
niyam scan . --create-baseline .niyam/baseline.json
```
This runs a normal repository scan and creates a `.niyam/baseline.json` file. All existing findings are serialized with a stable fingerprint.

### Consuming a Baseline
To run the scanner while suppressing findings already recorded in the baseline:
```bash
niyam scan . --baseline .niyam/baseline.json
```
Findings present in the baseline are marked as `accepted_existing`. They do not deduct points from the readiness score and do not trigger gating or exit failures.

### Risk Acceptance Behavior
* **Awareness vs Gating:** Baseline suppression only suppresses gating/failures; it does not hide findings. All findings (including suppressed ones) are still printed in JSON, Markdown, and console reports. Suppressed findings will display a status of `ACCEPTED`, whereas new findings display `OPEN`.
* **Hard Blocker Suppression:** Hard blockers (such as critical secrets or exposed private keys) are NOT suppressed by the baseline unless they are explicitly accepted with a non-empty `reason` in the baseline file.
* **Expiration Dates:** Each accepted finding in the baseline JSON can optionally contain an `expires_at` ISO-8601 timestamp. Once this date is exceeded, the suppression expires and the finding reverts to `OPEN`.

---

## 14. Enterprise Rollout Guidance

Adopting Niyam across large engineering organizations should be phased:

1. **Phase 1: Shadow / Monitoring Mode**
   Integrate `niyam scan` into your CI/CD pipelines without the `--fail-on` flag. This allows teams to build awareness and inspect reports without blocking build runs.
2. **Phase 2: Establish Baselines**
   Have each team run `niyam scan . --create-baseline .niyam/baseline.json` on their default branch. Commit the baseline file to the repository.
3. **Phase 3: Active Gating on Delta (New Findings)**
   Configure CI/CD pipelines to run with baseline checks and gating:
   ```bash
   niyam scan . --baseline .niyam/baseline.json --fail-on high
   ```
   This ensures that any new security risks or quality issues added in PRs fail the build immediately, while keeping legacy findings accepted under the baseline.
4. **Phase 4: Baseline Burn-down**
   Track and schedule burn-down sprints to resolve legacy findings, removing them from the baseline as they get remediated. Use `expires_at` in the baseline entries to enforce remediation timelines.

