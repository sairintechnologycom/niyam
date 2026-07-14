# Niyam End-to-End Validation Report

**Date:** 2026-07-14  
**Version:** 1.0.0  
**Method:** Live CLI workflow on fixture apps under `/tmp/niyam-e2e-20260714/`  
**Fixtures:** `test-fixtures/apps/risky-vibe-app`, `test-fixtures/apps/clean-nextjs-app`  
**Env:** `NIYAM_TEST=1`, local `.venv`, semgrep present; gitleaks/trivy/checkov absent

Related: `docs/strategy/capability-matrix.md`

---

## 1. Executive summary

| Verdict | Detail |
| --- | --- |
| **Core Trust path works** | init → context → scan → guard → cost → mcp → memory → evidence (with `--from`) → identity |
| **AgentOps planning works** | mission plan / show / validate / approve (product role) without live model for plan fallback |
| **Control Room basics work** | workspace create/list/show, approval request, timeline, evidence export |
| **Portal API works** | `/health`, `/mcp`, `/guard`, `/workspace/sessions` return live state |
| **Fleet basics work** | register, discover, list, status across repos |
| **Biggest product bugs** | (1) missing optional scanners score as **HIGH** and can force **NO_GO** on clean apps; (2) evidence without `--from` reports score 0 / NOT SCANNED even after a scan; (3) mission AI-fallback plan ignores actual requirement text |

**Overall live E2E maturity (repo AgentOps):** strong green path for Trust + local governance.  
**Enterprise control-tower thesis:** still not exercised (no inventory graph, no multi-cloud, no exec Trust Center queries).

---

## 2. Workflow exercised

```text
risky-app & clean-app
  niyam init --profile startup-saas --runtime claude
  niyam doctor / info / context refresh
  niyam scan -p startup|enterprise|regulated
  niyam guard enable / status / run (observe + block)
  niyam mcp register / approve / list / risk-report
  niyam cost log / summary / report / scorecard / pricing
  niyam memory init / add / list / recall / policy-check
  niyam policy list / validate / exception-list
  niyam identity init / show
  niyam evidence [--from scan.json] markdown|json|html
  niyam workspace create / list / show / request-approval / timeline / evidence
  niyam swarm init / status
  niyam ci verify
  niyam mission plan / show / validate-plan / approve
  niyam fleet register / discover / list / status
  portal API health + mcp + guard + workspace sessions
```

Mission **start/execute** against live Claude was **not** run (avoids external agent spend / hang). Plan + approve only.

---

## 3. Scorecard: what works well

### 3.1 Production readiness scan — excellent

| App | Score | Decision | Findings |
| --- | --- | --- | --- |
| **risky-app** | **44** | **NO_GO** | 18 (5 critical, 4 high, …) |
| **clean-app** | **47** | **NO_GO** | 4 (0 critical, 3 high) |

Risky app correctly caught:

- committed `.env` / `.env.local`
- hardcoded secrets in chat route
- missing lockfile, gitignore, tests, health, CI
- AI stub / placeholder
- Semgrep: GitHub token, Terraform RDS password / no logging

Outputs: JSON, Markdown, text; scoring breakdown by 8 dimensions; redaction status present; exit code **2** on NO_GO (good for CI).

### 3.2 Guardrails — excellent

| Mode | Command | Result |
| --- | --- | --- |
| observe | `echo hello-safe` | allow, exit 0 |
| observe | `rm -rf …` | **policy_decision=block** but **decision=allowed** (logged, executed) exit 0 |
| block | `rm -rf …` | blocked, exit 1 |

Append-only `/.niyam/logs/guard-actions.jsonl` with schema, session_id, matched_rule. Evidence and portal `/guard` surface the log.

### 3.3 Evidence packs — strong when wired

With `niyam evidence --from <scan.json> --include scan,guard,mcp,cost,memory,workspace`:

- Score **44/100**, decision **NO GO**, critical/high table, remediation section
- Guard summary (actions blocked/allowed)
- Multi-format: markdown, json, html

Identity signing: `identity init/show` works (Ed25519).

### 3.4 MCP / tool governance — works

- Register high-risk API tool
- Approve (`--approved-by e2e` works)
- List + risk-report
- Portal `/mcp` returns registry JSON

### 3.5 Cost / FinOps MVP — works

- Log 1200 in / 400 out tokens → **$0.0096**
- Summary by day/repo/task
- pricing + scorecard commands succeed

### 3.6 Memory ledger — works

- init, add positional `file note`, list, recall keyword, policy-check

### 3.7 Policy — works

- list, validate, exception-list (empty) on fresh workspace

### 3.8 Mission planning — works (with quality caveats)

- Fallback plan generated without live AI hang
- 5 tasks, agents (backend-specialist, qa-reviewer), dependency chain
- validate-plan OK
- approve `--role product` records approval

### 3.9 Control Room workspace — works

- create session `TASK-C62F9D54`
- list/show
- request-approval → status `approval_required`
- timeline shows approval_request
- workspace evidence markdown export

### 3.10 Fleet — works for Niyam workspaces

- discover 2 repos under temp root
- register clean + risky
- list + status (mission progress for risky: 0/5 PLANNED)

### 3.11 Portal API — works

```text
GET /health → {"status":"ok","service":"niyam-portal"}
GET /mcp → registry with demo-http
GET /guard → guard action log
GET /workspace/sessions → live sessions
```

(`niyam portal` CLI also starts; prefer binding and health check via uvicorn for automation.)

### 3.12 Bootstrap / doctor — works

- init creates `.niyam/`, projections, profiles, CLAUDE.md
- doctor / info / context refresh succeed on both fixtures

---

## 4. Gaps and issues found (live)

### P0 — product correctness

| ID | Issue | Impact | Evidence |
| --- | --- | --- | --- |
| **E2E-01** | Missing optional external scanners (gitleaks/trivy/checkov) emit **HIGH** findings and pull readiness below 50 → **NO_GO** even on clean apps | False failures; unusable CI default | clean-app score 47, only high findings are EXT-SCAN-MISSING-* |
| **E2E-02** | `niyam evidence` without `--from` does not discover latest scan; reports **0/100**, **NOT SCANNED**, empty findings | Operators think scan never ran; audit packs wrong | first evidence.md after successful scan |
| **E2E-03** | Mission AI-fallback plan ignores requirement: asked for **GET /health**, plan implements **GET /api/v1/resource** | Wrong work; trust erosion for autonomous missions | `task-list.yaml` T2/T3 titles |

### P1 — product / UX

| ID | Issue | Impact |
| --- | --- | --- |
| **E2E-04** | Fleet status **Readiness N/A** / **Risks 0/0** even after scans on repos | Fleet is not a Trust rollup yet |
| **E2E-05** | `ci verify` fails with “No scan report found” / missing mission evidence / npm scripts from stack defaults | CI path not auto-linked to prior `scan` output |
| **E2E-06** | Git metadata in evidence often `Branch: unknown, Commit: unknown` on temp repos | Audit quality |
| **E2E-07** | Workspace UX: session ID must be known (`TASK-…`); easy to misuse directory name `sessions` | Operator friction |
| **E2E-08** | Observe mode records `policy_decision=block` but still allows execution — correct for observe, but evidence wording “Blocked: 2” can confuse (counts policy match not hard block) | Reporting clarity |

### P2 — platform thesis gaps (expected, not regressions)

| ID | Gap | Status in live test |
| --- | --- | --- |
| **E2E-09** | Org AI inventory / AI Application identity | Not present |
| **E2E-10** | Architecture intelligence / lineage | Only context/stack |
| **E2E-11** | Business-outcome FinOps | Token $ only |
| **E2E-12** | Executive Trust Center queries | Portal is operator API only |
| **E2E-13** | Multi-cloud connectors | Not present |
| **E2E-14** | Full mission execute + auto-heal against live coding agent | Not run in this session |

### Operator/CLI notes (not bugs, friction)

- Positional args: `mcp register NAME`, `memory add FILE NOTE`, `workspace create TITLE`, `memory recall QUERY`
- Flags differ from naive guesses (`--command-or-url` not `--url`; cost has no `--session`)
- `mcp approve --approved-by` **does** work when tested correctly

---

## 5. Exit-code interpretation

| Exit | Meaning in this run |
| --- | --- |
| **0** | Success |
| **1** | Guard blocked command; or CI verify failed |
| **2** | Scan NO_GO / Typer usage error / some CLI validation failures |

Do not treat scan exit 2 as a product crash when decision is intentionally NO_GO.

---

## 6. Comparative: risky vs clean

| Signal | risky-app | clean-app |
| --- | --- | --- |
| Secrets critical | Yes (env + source) | No |
| Real security value of scan | High | Low (mostly missing-scanner high) |
| Should block production | Yes | Debatable — currently NO_GO due to missing scanners |
| Health/CI/tests docs | Missing | Partially present (has CI workflow, tests dummy) |

**Insight:** Built-in rules differentiate risk well. External-scanner-missing policy currently **dominates** clean-app outcomes and weakens the commercial “readiness score” story.

---

## 7. Module pass map (live)

| Module | Live result |
| --- | --- |
| Init / doctor / context | **PASS** |
| Scan + decision | **PASS** (quality issue E2E-01) |
| Guard | **PASS** |
| MCP | **PASS** |
| Skills list | **PASS** (register not deeply exercised) |
| Cost | **PASS** |
| Memory | **PASS** |
| Policy | **PASS** |
| Identity | **PASS** |
| Evidence | **PASS** with `--from`; **FAIL** auto-discovery |
| Workspace Control Room | **PASS** (basics) |
| Swarm | **PASS** init/status |
| Mission plan/approve | **PASS** with plan quality gap E2E-03 |
| Mission execute | **NOT RUN** |
| Fleet | **PASS** inventory of workspaces; readiness rollup weak |
| CI verify | **FAIL** expected without linked scan/mission evidence |
| Portal API | **PASS** |
| SaaS upload | **NOT RUN** (no remote) |

---

## 8. Recommended fixes (priority order)

1. **E2E-01:** Treat missing external scanners as **info/warn**, or only HIGH when `external_scanners.*.required: true`. Do not NO_GO clean projects solely for absent optional binaries.  
2. **E2E-02:** Auto-load latest scan from `.niyam/` or cwd report paths when `--from` omitted; never claim perfect dimension scores with total 0.  
3. **E2E-03:** Fallback planner must ground tasks in requirement text (healthcheck ≠ `/api/v1/resource`).  
4. **E2E-04 / E2E-05:** Wire fleet status + `ci verify` to last scan JSON and evidence artifacts.  
5. Document CLI positional conventions in quickstart (reduce operator error rate).

---

## 9. Artifacts location

```text
/tmp/niyam-e2e-20260714/
  risky-app/                 # full governed workspace
  clean-app/
  risky-scan-startup.json
  risky-evidence-from-scan.md
  risky-evidence-from-scan.json
  clean-scan.json
  clean-evidence.md
  e2e-results.log
  e2e-round2.log
  step-status.tsv
  step-status-round2.tsv
```

Reproduce core path:

```bash
export NIYAM_TEST=1
PY=/path/to/sutra/.venv/bin/python
cd /tmp/niyam-e2e-20260714/risky-app
$PY -m niyam scan -p startup -o json -f /tmp/scan.json
$PY -m niyam evidence --from /tmp/scan.json -o /tmp/evidence.md
```

---

## 10. Bottom line

**Working well:** Niyam already delivers a credible **local Trust + AgentOps** loop — especially scan/decision, guard enforcement, MCP approval, cost ledger, evidence packs (when wired), mission planning/approval, control-room sessions, fleet workspace discovery, and portal APIs.

**Gaps that hurt the story today:** false NO_GO from missing scanners, evidence not auto-attaching scans, fleet not rolling up readiness, fallback mission plans that ignore requirements, and everything above repo AgentOps for the company platform thesis.

**If selling Phase 1 Trust:** fix E2E-01 and E2E-02 first — those are credibility blockers for production readiness as a product.
