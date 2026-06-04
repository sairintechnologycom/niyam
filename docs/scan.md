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
```
