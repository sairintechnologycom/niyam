# Niyam Scanner (`niyam scan`)

The `niyam scan` command is a local repository scanner that assesses production readiness for AI-assisted or "vibe-coded" applications. It identifies security issues, environment risks, missing best practices, and AI-risk indicators.

---

## Usage

```bash
# Scan the current directory using the default startup profile
niyam scan .

# Scan a subdirectory using a specific profile
niyam scan ./my-app --profile team

# Run scan and format output as JSON or Markdown
niyam scan . --output json
niyam scan . --output markdown

# Save the markdown report to a file
niyam scan . --report-file niyam-readiness.md
```

---

## Scan Profiles

Niyam supports three scan profiles depending on the target strictness:

| Profile | Strictness | Target Audience | Key Behavior |
| --- | --- | --- | --- |
| `startup` | Lenient | Early-stage products / rapid MVPs | Minimal warnings. Focuses on critical secrets exposure. |
| `team` | Medium | Collaborative projects | Flags missing lockfiles, missing test files, and high AI stubs. |
| `enterprise` | Strict | Production enterprise codebases | Strict requirements. Elevates lack of testing, health routes, CI/CD pipelines, and IaC policies to high/critical severity. |

---

## Supported Checks

The scanner checks the codebase across nine categories:

1. **Secrets Exposure (`secrets`):** Detects hardcoded API keys (AWS, GitHub, Slack, OpenAI), PEM private keys, database connections with credentials, and unprotected `.env` files tracked in the repository.
2. **Dependency Manifests (`dependencies`):** Verifies that standard manifest files (`package.json`, `requirements.txt`, `pyproject.toml`, `Cargo.toml`, `go.mod`) have corresponding version-pinning lockfiles (`package-lock.json`, `uv.lock`, `poetry.lock`, `Cargo.lock`, `go.sum`).
3. **Environment and Config (`env_config`):** Ensures `.env` files have a corresponding `.env.example` or `.env.template`, and that `.gitignore` is present in the workspace.
4. **Health Check Endpoints (`health`):** Scans source code files to verify the presence of active diagnostic check routes (like `/health`, `/healthz`, `/ping`).
5. **Documentation (`docs`):** Checks for repository README file and general documentation folders.
6. **Testing Suite (`tests`):** Checks for the presence of a test directory or files matching test filename structures (e.g. `test_*.py`, `*.test.js`).
7. **CI/CD Configuration (`cicd`):** Confirms validation runs automatically on VCS push/merge (e.g., GitHub Actions, GitLab CI).
8. **AI-Risk Mitigation (`ai_risk`):** Searches for commented-out assertions (e.g. `# assert`, `// assert`) that might mask failed test verifications, and placeholder stubs (e.g. `pass # TODO`, `NotImplementedError`).
9. **Infrastructure-as-Code Security (`iac`):** Evaluates Dockerfiles to ensure base image tags are pinned (not using `latest`) and that containers do not default to running as `root` (lack of `USER` statement).

---

## Report Output

### Console Summary (Default)
Outputs a clean Rich table of findings along with the final score, grade, and execution decision:
* **85–100:** `GO`
* **70–84:** `CONDITIONAL_GO`
* **50–69:** `HIGH_RISK`
* **<50:** `NO_GO`

### JSON Report
Contains complete machine-readable structures suitable for automated CI pipeline ingestion:
```json
{
  "profile": "startup",
  "score": 89,
  "decision": "GO",
  "findings": [
    {
      "id": "ENV002",
      "title": "Missing .gitignore File",
      "category": "env_config",
      "severity": "medium",
      "file_path": "",
      "description": "The repository does not contain a '.gitignore' file in the root.",
      "recommendation": "Create a '.gitignore' to prevent committing environment secrets and build artifacts."
    }
  ]
}
```

### Markdown Report
Generates a structured report detailing findings and actionable recommendation steps.
