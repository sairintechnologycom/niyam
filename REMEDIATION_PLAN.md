# Niyam Remediation Plan — Phased Development Approach

Source: senior full-stack review (2026-06-11) covering governance core, architecture,
orchestration, and developer experience.

**Guiding principle:** Niyam sells governance. Anything that makes the guard
bypassable or the audit trail corruptible is a release blocker; everything else is
sequenced by user-visible value per unit of risk.

**GA gate:** Phases 0–2 complete + Phase 3 worktree/output fixes. Phases 4–6 can land
in 1.0.x point releases.

---

## Phase 0 — Bug triage & quick wins

**Goal:** Eliminate known live bugs and cheap corruption risks before deeper work churns the same files.
**Duration:** 1–2 days · **Risk:** Low · **Depends on:** nothing

| # | Task | Files | Notes |
|---|------|-------|-------|
| 0.1 | Remove duplicate `policy_app` definition (second overwrites first, orphaning registered commands) | `niyam/cli/__init__.py:116,137` | Verify which command set survives today; keep the union |
| 0.2 | Remove duplicate `policy` import | `niyam/cli/__main__.py:271,281` | |
| 0.3 | Make `save_niyam_config()` atomic (tempfile + `os.replace`, mirroring `memory_ledger/local_store.py`) | `niyam/core/config.py` | Add crash-safety test |
| 0.4 | Fix `E402` late imports in API server (circular-import smell — break the cycle, don't suppress) | `niyam/api/server.py:48-56` | |
| 0.5 | Standardize the 3 naive `datetime.now()` call sites to `datetime.now(timezone.utc)`; add a `utc_now()` helper | `core/skills.py:212`, `cli/main_cmds.py:545`, `mission/planner.py:544` | |
| 0.6 | `ruff check --fix` sweep; fix remaining E501/F401/F811 manually; add ruff to CI as a hard gate if not already | repo-wide | |

**Exit criteria:** `ruff check .` clean · `pytest` green · new `test_config.py` roundtrip + atomic-write tests pass.

---

## Phase 1 — Guard enforcement hardening  ⛔ RELEASE BLOCKER

**Goal:** The guard either genuinely enforces, or honestly documents its trust model — no silent middle ground.
**Duration:** ~2 weeks · **Risk:** High (core behavior change) · **Depends on:** Phase 0

### Workstream 1A — Semantic command matching
- Replace token-sequence matching in `_match_command_pattern()` (`niyam/policies/guard.py:477-515`) with semantic parsing:
  - `shlex` parse → canonicalize flags for high-risk binaries (`rm`: `-rf` ≡ `-r -f` ≡ `-fr`; `git push`: `-f` ≡ `--force`; `chmod`, `git reset`, etc.).
  - Resolve binary paths so `/bin/rm`, `command rm`, `env rm` match `rm`.
  - Recursively evaluate wrapper payloads: `bash -c "..."`, `sh -c`, `xargs`, `find -exec`, heredoc-fed shells.
  - Detect undecidable cases (command built from variables, base64, eval) and **fail closed with an approval prompt** rather than allow.
- Build a table-driven bypass-vector regression suite (`tests/test_guard_bypass_vectors.py`) seeded with every vector from the review; this suite becomes the permanent contract.

### Workstream 1B — Unified path/freeze matching
- One function: `is_path_frozen(path, frozen_paths)` using `Path.resolve()` + `is_relative_to()` with symlink resolution.
- Replace all three divergent implementations: `guard.py:186-189` (string prefix), `guard.py:542` (already correct — promote it), generated runtime hook (`runtimes/base.py:_render_hook_script` → `pre_tool_guard.py` fnmatch/startswith).
- Symlink test cases: link inside workspace → frozen target; link escaping workspace root.

### Workstream 1C — Trust model & config integrity
- Write `docs/trust-model.md`: what Niyam can and cannot enforce when the agent has workspace write access. Honest tiers: *advisory* (instructions only) / *cooperative* (hooks + CLI guard) / *hardened* (config pinned outside workspace).
- Config tamper detection: store a hash of `.niyam/niyam.yaml` + policy files outside the workspace (`~/.niyam/pins/<repo-id>` or `git config`); guard verifies on every invocation, fails closed on mismatch with a clear remediation message.
- Environment hardening: `NIYAM_TEST` / `NIYAM_TEST_NON_INTERACTIVE` (`guard.py:554-635`) only honored when `PYTEST_CURRENT_TEST` is set by an actual pytest process; never lets non-interactive mode *weaken* a decision — non-interactive always denies approval-gated actions.
- Remote policies (`guard.py:297-407`): HMAC-SHA256 signature verification, reject unsigned; expired cache → fail closed (deny + surface error), never silent fallback.
- Optional `niyam guard lock` → chmod `0o555` on `.niyam/` for hardened mode.

### Workstream 1D — Redaction expansion
- Extend `niyam/governance/common/redaction.py`: AWS secret access keys (40-char base64 in AWS context), Stripe (`sk_live_`, `rk_live_`), Slack (`xox[abprs]-`), GitHub PATs (`ghp_`, `github_pat_`), GitLab, npm, JWTs, connection strings with credentials.
- Lower generic-assignment minimum length; add benchmark test corpus of real-format fakes.

**Exit criteria:** bypass-vector suite green · all path checks route through one helper · trust-model doc published · tamper test (agent edits `.niyam/niyam.yaml` → guard refuses) green · redaction benchmark ≥ agreed recall on corpus.

---

## Phase 2 — Data integrity & memory consolidation

**Goal:** One memory system, tested config layer, no shared-file corruption paths.
**Duration:** ~1 week · **Risk:** Medium (data path migration) · **Depends on:** Phase 0

| # | Task | Notes |
|---|------|-------|
| 2.1 | Deprecate `niyam/core/memory.py`; route all callers (CLI `memory` commands, MCP memory server) to `memory_ledger/LocalMemoryLedgerStore` | Keep thin compat shims emitting `DeprecationWarning` for one minor version |
| 2.2 | Migration utility `migrate_legacy_index_jsonl()` — validate/upgrade legacy records into schema 1.0.0; run automatically on first ledger access, back up original | |
| 2.3 | Concurrent-access tests: two processes appending/replacing simultaneously; corrupted-line recovery (skip+report, don't crash) | |
| 2.4 | Add `tests/test_config.py` (roundtrip, schema validation, corruption recovery, unknown-key forward compat) and `tests/test_analytics.py` | These modules currently have **zero** tests |
| 2.5 | mypy baseline: add `[tool.mypy]` to pyproject, strict on `core/config.py`, `memory_ledger/`, `policies/`; permissive elsewhere; CI gate on the strict set | Expand module-by-module in later phases |

**Exit criteria:** `core/memory.py` callers = 0 (grep-verified) · migration test on real-shape legacy data green · mypy strict set passes in CI.

---

## Phase 3 — Orchestration reliability

**Goal:** Missions survive crashes, kills, chatty agents, and merge conflicts without manual repo surgery.
**Duration:** ~1 week · **Risk:** Medium · **Depends on:** Phase 0 (parallel-safe with Phase 2)

| # | Task | Files | Notes |
|---|------|-------|-------|
| 3.1 | Worktree reaper: at mission start, prune stale niyam worktrees/branches (age > threshold, no live heartbeat); add `niyam mission cleanup` for manual sweep | `mission/worktree.py`, `mission/executor.py` | Fixes "branch already exists" failures + disk leak |
| 3.2 | Bounded output capture: stream subprocess output to rotating log file with max-size cap; truncate marker in evidence | `mission/task_runner.py:1141-1147` | |
| 3.3 | Kill process group on timeout (`start_new_session=True` + `os.killpg`) instead of relying on OS cleanup after `TimeoutExpired` | `task_runner.py:1109-1152` | |
| 3.4 | Merge-conflict cleanup: on final-integration conflict, `git merge --abort`, restore stash, leave repo clean, then fail the mission with conflicting-file list in the report | `worktree.py:294-381` | |
| 3.5 | Replace 1s busy-wait lock loop with exponential backoff + jitter; document single-filesystem locking limitation | `executor.py:237-241`, `core/swarm.py` | |
| 3.6 | Extract shared `PolicyGenerator` / `SettingsGenerator` / context-doc renderer from the 3 runtime adapters (~40% duplication) | `runtimes/claude.py:96-134`, `codex.py:184-212`, `gemini.py:145-173` → `runtimes/generators.py` | Makes Phase 1 policy-schema changes propagate from one place |

**Exit criteria:** kill -9 a mid-mission run → next mission starts clean · 100MB-output agent test stays under memory cap · forced merge conflict leaves `git status` clean · adapter golden-file tests prove identical output pre/post refactor.

---

## Phase 4 — CLI surface & developer experience

**Goal:** Scriptable, consistent CLI; reduced cognitive load before users build muscle memory on 1.0 naming.
**Duration:** ~1.5 weeks · **Risk:** Low–medium (deprecations, not removals) · **Depends on:** Phase 0

| # | Task | Notes |
|---|------|-------|
| 4.1 | Central exception handler mapping `NiyamError` subclasses to exit codes from `core/errors.py`; sweep ad-hoc `typer.Exit(1)` / `SystemExit(1)` (131 sites) to raise typed errors | Publish exit-code table in docs |
| 4.2 | `--json` + `--quiet` on the high-value command set first: `status`, `mission list/status/report`, `guard status`, `cost report`, `scan`, `doctor`, `policy validate` | Pattern: command builds a dict, renderer chooses Rich vs JSON |
| 4.3 | Resolve the 5 command collisions: top-level `start`/`status`/`report`/`dashboard`/`validate` become documented aliases of their subgroup forms, with deprecation warnings on a 2-release clock | No breaking removals at 1.0 |
| 4.4 | Delete the `typer.core.TyperCommand.main` monkeypatch (`cli/__init__.py:290-342`); use native `--flag/--no-flag` | Will break on a Typer upgrade otherwise |
| 4.5 | `niyam init` prints "what's next" (sync → doctor → first mission); add a guided `niyam init --interactive` using questionary (already a dependency) | |
| 4.6 | Write `docs/concepts.md` — the mental model: workspace vs mission vs swarm vs fleet vs guard, with one diagram and a 5-minute golden path | Prerequisite for any surface reduction conversation |
| 4.7 | Verb style guide (`docs/cli-conventions.md`): `show`/`list`/`add`/`remove` conventions; freeze "no new top-level commands" policy for 12 months | |

**Exit criteria:** exit codes documented + enforced by tests · `--json` output schema-stable on the listed commands · zero new top-level commands · deprecation warnings tested.

---

## Phase 5 — Portal security & packaging

**Goal:** The portal is opt-in, locked down, and doesn't leak its own token.
**Duration:** 3–4 days · **Risk:** Low · **Depends on:** Phase 0

| # | Task | Files |
|---|------|-------|
| 5.1 | Move `fastapi`/`uvicorn` to `[project.optional-dependencies] portal`; lazy-import in `niyam portal` with a friendly `pip install niyam[portal]` error | `pyproject.toml`, `cli/main_cmds.py` |
| 5.2 | Stop injecting the auth token into HTML (`server.py:91`); serve it via an authenticated bootstrap endpoint or session cookie (HttpOnly) | `api/server.py` |
| 5.3 | CORS: restrict to `http://127.0.0.1:<port>`; remove `allow_origins=["*"]` | `server.py:65-70` |
| 5.4 | Token lifecycle: expiry (e.g., 30 days), rotation on each `niyam portal` start; the "no workspace → allow" fallback (`server.py:37`) becomes deny | |
| 5.5 | Update PyInstaller build (`build_binary.py`) for the optional-extra split; CI matrix installs both base and `[portal]` | |

**Exit criteria:** base install has no fastapi/uvicorn · portal endpoints 401 without valid token in all states · token absent from page source.

---

## Phase 6 — GA polish & long tail

**Goal:** Sustained quality floor for 1.0 GA and beyond.
**Duration:** ongoing / ~1 week focused · **Depends on:** Phases 1–5

- Split god modules: `core/evidence.py` (1,083 LOC → Collector / Formatter / GitAuditTrail), `mission/planner.py` (1,847 LOC → PlanGenerator / JSONExtractor / TaskPlanner), `mission/task_runner.py` (1,646 LOC). Do this *after* Phases 1–3 so refactors don't collide with behavior fixes.
- Expand mypy strict set to `mission/`, `runtimes/`, `governance/`.
- Coverage gate in CI (`pytest-cov` is already a dev dep — start at current % and ratchet).
- Scoring/decision-engine category aliases (`governance/scoring.py:73-159`, `governance/decision.py:64-126`): broaden secrets-category matching; add active secret scan fallback when external scanners are absent.
- Command-count review against `docs/concepts.md`: target 60–80 high-signal commands by deprecating low-traffic subcommands (measure via opt-in telemetry or GitHub issue feedback first — don't guess).

---

## Sequencing & parallelism

```
Phase 0 ──► Phase 1 (guard) ──────────────┐
   │                                       ├──► GA gate ──► Phase 4 ──► Phase 6
   ├──────► Phase 2 (memory/config) ───────┤                Phase 5 (any time after 0)
   └──────► Phase 3 (orchestration) ───────┘
```

- Phases 1, 2, 3 are independent after Phase 0 and can run as parallel workstreams if multiple contributors are available; single-developer order is 0 → 1 → 2 → 3 → 5 → 4 → 6.
- **Total estimate:** ~6–7 weeks single developer; ~4 weeks with two.

## Risk register

| Risk | Phase | Mitigation |
|------|-------|------------|
| Guard rewrite breaks legitimate commands (false positives) | 1 | Ship behind `guard.matching: semantic|legacy` config flag for one release; bypass suite + allowlist suite both gate CI |
| Memory migration corrupts user ledgers | 2 | Automatic backup before migration; dry-run mode; migration is idempotent |
| Alias deprecations annoy existing users | 4 | Warnings only at 1.0; removal earliest 1.2; CHANGELOG + migration notes |
| Adapter refactor changes generated files | 3 | Golden-file tests asserting byte-identical output before behavioral changes |
| Phases drift / scope creep | all | Each phase has exit criteria; no phase merges without its new tests green |

## Validation per phase

Every phase ends with: `pytest` (full suite) · `ruff check .` · `ruff format --check .` · the phase's new regression suite added to CI permanently. Phase 1 additionally requires a red-team pass: someone (or an agent) attempts the documented bypass vectors against a live workspace.
