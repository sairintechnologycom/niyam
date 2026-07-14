# Niyam Feature Validation Report

**Date:** 2026-07-14  
**Code under test:** workspace package **1.0.0** (`.venv` / `python3 -m niyam`)  
**Method:** Automated unit suite + live CLI smoke on fixture apps  
**Fixtures:** `test-fixtures/apps/risky-vibe-app`, `test-fixtures/apps/clean-nextjs-app`  
**Env:** `NIYAM_TEST=1`, local venv  

Related: [capability-matrix.md](capability-matrix.md), [e2e-validation-2026-07-14.md](e2e-validation-2026-07-14.md)

---

## 1. Executive summary

| Dimension | Verdict | Evidence |
| --- | --- | --- |
| **Correctness** | **Strong** | Live smoke **45/46 PASS**; scan differentiates risky (49/NO_GO) vs clean (92/GO) |
| **Security** | **Good with caveats** | Block mode + redaction work; path-write revert under mission has failing tests |
| **Control** | **Good with caveats** | GO/NO-GO, approvals, CI fail-closed work; observe mode does not block; mission replan/executor gaps |
| **Unit suite** | **Mostly green** | **688 passed, 6 failed** (non-e2e) |

### Bottom line

Use **Niyam 1.0.0 from this repo** (venv / editable install) as the governed AgentOps path. It correctly **assesses**, **guards shell in block mode**, **redacts secrets**, **gates tools/missions**, and **emits evidence**.

Do **not** rely on the older global CLI (**0.3.9** via `~/.local/bin/niyam`) — it lacks `scan`, `mcp`, `cost`, `workspace`, and most governance surface.

**Not validated end-to-end here:** live multi-agent mission **execution** against Claude/Codex (cost + interactive hang risk). Plan / validate / approve paths were exercised.

---

## 2. Critical environment finding

| CLI | Version | Governance surface |
| --- | --- | --- |
| `~/.local/bin/niyam` (pipx default) | **0.3.9** | Missing `scan`, `mcp`, `cost`, `workspace`, full evidence stack |
| `.venv/bin/niyam` / `python3 -m niyam` | **1.0.0** | Full feature set |

**Action:** `pipx install --force` from this tree, or always use `.venv/bin/niyam` until the published package matches.

---

## 3. Live smoke scorecard (1.0.0)

Workdir: `/tmp/niyam-validate-v1-20260714155808`  
**Result: 45 PASS · 1 FAIL · 1 INFO**

### 3.1 Correctness

| Feature | Result | Notes |
| --- | --- | --- |
| `init` (startup-saas / fullstack) | **PASS** | Profiles + runtime projection |
| `doctor` | **PASS** | Config sanity |
| `context refresh` | **PASS** | Stack context |
| `sync` | **PASS** | CLAUDE.md projection |
| `scan` risky app | **PASS** | Score **49**, decision **NO_GO**, **18** findings (5 critical) |
| `scan` clean app | **PASS** | Score **92**, decision **GO**, 4 findings |
| Score separation | **PASS** | risky 49 ≪ clean 92 (control of readiness signal) |
| `cost log` / `summary` | **PASS** | FinOps ledger |
| `memory init` / `recall` / `policy-check` | **PASS** | Ledger present |
| `memory add` (wrong argv) | **FAIL** | Needs `memory add <file> <note>` — UX trap, not engine failure |
| `skills list` | **PASS** | Inventory |
| `mission plan` / `show` / `validate-plan` | **PASS** | No live model required for fallback plan |
| `mission approve` | **PASS** | Role gate path |
| `workspace` create/list/show/timeline/evidence | **PASS** | Control Room basics |
| `swarm` / `fleet list` / `loop --help` | **PASS** | Smoke only |
| `evidence --from scan.json` | **PASS** | Score 49, NO GO, dimensions, critical table |

### 3.2 Security

| Control | Result | Notes |
| --- | --- | --- |
| `policy validate` | **PASS** | Policy YAML valid after init |
| `guard enable` | **PASS** | Guard mode on |
| `guard run --mode block -- rm -rf …` | **PASS** | Message “Blocked…”, **exit 1** |
| Default `guard run -- rm -rf …` | **PASS** | Blocks with **exit 1** (re-verified) |
| `guard run --mode observe -- rm -rf …` | **BY DESIGN / RISK** | **exit 0** — command executes; log shows `policy_decision=block`, `decision=allowed` |
| Secret redaction in guard logs | **PASS** | `password=[REDACTED_SECRET]`, `api_key=[REDACTED_SECRET]` |
| `identity init` / `show` | **PASS** | Local Ed25519 identity |
| Hardcoded secrets in risky fixture | **PASS** | SEC001/SEC002 critical findings force NO_GO |

### 3.3 Control / governance

| Control | Result | Notes |
| --- | --- | --- |
| Scan exit non-zero on NO_GO | **PASS** | exit 2 + report file |
| MCP register (high, unapproved) | **PASS** | Registry entry |
| MCP risk-report | **PASS** | Risk visibility |
| MCP approve `--approved-by` | **PASS** | Explicit approval trail |
| `guard freeze` | **PASS** | Path restriction set; hooks regenerated |
| Workspace `request-approval` | **PASS** | HITL request recorded |
| `ci verify` on incomplete app | **PASS** | Fail-closed (missing evidence, lint/test/build) |
| Mission validate-plan before start | **PASS** | Plan gate |
| Evidence includes scan+guard+mcp+cost+memory | **PASS** | Multi-section pack |

---

## 4. Automated tests (non-e2e)

```text
688 passed, 6 failed in ~6m21s
```

### Failing tests (control / orchestration gaps)

| Test | Risk | Interpretation |
| --- | --- | --- |
| `test_guardrails.py::test_path_write_denial_and_revert` | **Security / control** | Denied path write during mission was **not** fully reverted / failed as expected |
| `test_remediation.py::test_writes_files_false_violation_and_revert` | **Security / control** | Task with `writes_files: false` still left files behind |
| `test_adaptive_orchestration.py::test_run_mission_replan_integration` | Control | Replan integration path fails (interactive / planner) |
| `test_replan.py::test_mission_replan_logic` | Control | Planner replan `SystemExit(1)` |
| `test_multi_runtime.py::test_planner_parses_runtime_field` | Correctness | Task without runtime got default `claude` instead of empty/None |
| `test_multi_runtime.py::test_executor_resolves_task_runtime` | Control | Mission start exited (interactive “Press Enter…” / missing agent path) |

**Implication:** Shell **command** governance is strong. **File-scope enforcement during mission execution** has regressions and should not be treated as fully proven in CI green status until those tests pass.

---

## 5. Feature matrix: correct · secure · controlled

Legend: ✅ solid · ⚠️ partial / caveats · ❌ gap · ⬜ not exercised this session

| Feature area | Correct | Secure | Controlled | Notes |
| --- | --- | --- | --- | --- |
| Workspace init / sync / doctor | ✅ | ✅ | ✅ | Foundation solid |
| Context refresh | ✅ | ⬜ | ✅ | Stack detection works |
| Production readiness **scan** | ✅ | ✅ | ✅ | Best product surface; GO/NO-GO reliable on fixtures |
| **Guard** block mode | ✅ | ✅ | ✅ | Denies destructive cmds |
| Guard observe mode | ✅ | ⚠️ | ⚠️ | Logs policy but **executes** denied cmds |
| Guard path **freeze** | ✅ | ⚠️ | ⚠️ | Status works; commit/mission enforcement needs more proof |
| Mission path deny / writes_files=false | ⚠️ | ❌ | ❌ | **Unit tests failing** |
| Secret **redaction** | ✅ | ✅ | ✅ | Guard JSONL redacts |
| **MCP** registry + approve | ✅ | ✅ | ✅ | High-risk tools require approval path |
| Skills inventory | ✅ | ⬜ | ⚠️ | List works; approval not deeply smoke-tested |
| **Policy** validate / exceptions | ✅ | ✅ | ✅ | Validate green; exception lifecycle not fully smoked |
| **Cost** ledger | ✅ | ⬜ | ✅ | Tracking works; ROI claims not validated |
| **Memory** ledger | ✅ | ✅ | ✅ | init/recall/policy-check OK; CLI `add` needs file arg |
| **Evidence** packs | ✅ | ✅ | ✅ | Multi-section audit report with decision reason |
| **Identity** signing | ✅ | ✅ | ✅ | Local key material |
| **Mission** plan/validate/approve | ✅ | ⬜ | ✅ | No live agent execution |
| Mission **start/execute/replan** | ⚠️ | ⚠️ | ⚠️ | Unit failures; interactive fallback risk |
| **Workspace** Control Room | ✅ | ⬜ | ✅ | Sessions, approval, timeline, evidence |
| Browser sandbox | ⬜ | ⬜ | ⬜ | Not live-exercised this session |
| **CI** verify | ✅ | ✅ | ✅ | Fail-closed without evidence/build |
| **Fleet** / **swarm** / **loop** | ✅ | ⬜ | ⚠️ | Help/list/init only |
| Portal API | ⬜ | ⬜ | ⬜ | Not re-hit this session (see prior e2e doc) |
| SaaS upload | ⬜ | ⬜ | ⬜ | Out of scope for local trust path |

---

## 6. Security & control findings (prioritized)

### P0 — Treat carefully in production autonomy

1. **Mission file-scope enforcement incomplete**  
   - Failing tests for deny-write patterns and `writes_files: false` reverts.  
   - **Do not** claim “agents cannot touch frozen/denied paths during missions” until fixed and tests green.

2. **Observe mode is not enforcement**  
   - `policy_decision=block` + `decision=allowed` + exit 0.  
   - Safe for telemetry; unsafe if operators assume “guard is on” without **block** mode.

### P1 — Operational correctness

3. **Global CLI version skew (0.3.9 vs 1.0.0)**  
   - Users may think governance is enabled while running a truncated CLI.

4. **Mission replan / multi-runtime executor paths flaky or interactive**  
   - Automated tests show SystemExit / “Press Enter once you have completed the task manually”.

5. **Memory add CLI ergonomics**  
   - Requires `niyam memory add <file> <note>`; single-string usage fails.

### P2 — Product polish (from prior e2e notes; partially improved)

6. Optional external scanners missing can inflate risk on clean apps (historical).  
7. Evidence wiring is solid **with** scan JSON; prefer explicit `--from` for CI determinism.

---

## 7. Recommended validation checklist (repeatable)

```bash
# Always pin to 1.0.0
export PATH="/path/to/sutra/.venv/bin:$PATH"
export NIYAM_TEST=1

# Unit / integration
python3 -m pytest tests/ -q --ignore=tests/e2e

# Live trust path on a fixture
cp -R test-fixtures/apps/risky-vibe-app /tmp/niyam-val && cd /tmp/niyam-val
niyam init --profile startup-saas --runtime claude --force
niyam doctor && niyam context refresh && niyam sync
niyam scan . -p startup -o json -f scan.json          # expect NO_GO
niyam guard enable
niyam guard run --mode block -- rm -rf /tmp/x          # expect block exit 1
niyam mcp register t --type api --risk high --approved false
niyam cost log --tool claude-code --model test --input-tokens 1 --output-tokens 1 --task t
niyam memory init && niyam memory policy-check
niyam evidence --from scan.json --include scan,guard,mcp,cost,memory -o md --output e.md
niyam mission plan requirements.md && niyam mission validate-plan && niyam mission approve
niyam workspace create "check" --session-id V1
niyam ci verify                                        # expect fail without full app CI
```

**Security-focused extra:**

```bash
# Redaction
niyam guard run --mode observe -- bash -c 'echo api_key=sk-TESTSECRET'
grep -q sk-TESTSECRET .niyam/logs/guard-actions.jsonl && echo FAIL || echo OK

# Block vs observe
niyam guard run --mode block -- rm -rf /tmp/x ; echo $?   # want 1
niyam guard run --mode observe -- rm -rf /tmp/x ; echo $? # want 0 + log
```

---

## 8. What “good enough to use” means today

### Safe to use now (with 1.0.0)

- Repo readiness scoring and GO/NO-GO gates  
- Guard **block** mode for shell deny lists  
- Secret redaction in observation logs  
- MCP tool registration / approval  
- Evidence packs for audit / PR attachment  
- Mission **planning** + human approval  
- Control Room session bookkeeping  
- CI verify as a fail-closed gate  

### Use with supervision

- Mission **execution** and replan (fix unit gaps first)  
- Path freeze / deny-write as the *sole* write control  
- Observe mode (logging only)  
- Swarm / fleet / loop beyond smoke  

### Not claimed

- Org-wide AI inventory / multi-cloud discovery  
- Fully closed enterprise Trust Center  
- Auto-remediation that always reverts unauthorized writes  

---

## 9. Suggested next engineering fixes (from this validation)

1. Fix `writes_files: false` and deny-write **revert** so path guardrail tests pass.  
2. Make multi-runtime planner preserve empty/null runtime when unspecified (or document defaulting).  
3. Remove interactive “Press Enter…” from automated mission paths under `NIYAM_TEST`.  
4. Ship/publish **1.0.0** so global `niyam` matches repo.  
5. Improve `memory add` UX (optional single-arg note to default file).  
6. Document clearly: **observe ≠ block**.  

---

## 10. Appendix — risky scan sample (control proof)

| Metric | Value |
| --- | --- |
| Score | 49/100 |
| Decision | **NO_GO** |
| Critical | 5 (env files + hardcoded secrets) |
| High | 1 |
| Decision reason (excerpt) | Hard blocker: Critical secrets (SEC001/SEC002) |
| Clean contrast | 92/GO |

This is the strongest proof that readiness **control** works: a vibe-coded risky app cannot honestly claim production readiness under Niyam.
