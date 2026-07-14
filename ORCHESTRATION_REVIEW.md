# Niyam Multi-Agent Orchestration Review

Date: 2026-07-11  
**Update 2026-07-14:** Phases 0–1 (+ core of Phase 2 invocation) implemented:

- `niyam/runtimes/specs.py` — `RuntimeSpec` + built-in claude/codex/gemini grammars  
- `niyam/runtimes/registry.py` — open registry + `.niyam/runtimes.yaml` `execution_specs`  
- `niyam/runtimes/executor.py` — `build_runtime_invocation` / `run_runtime` / usage parsers  
- Mission `task_runner` + LoopOps adapters + planner call `run_runtime`  
- Fake CLIs in `tests/fakes/bin/` + `tests/test_runtime_orchestration.py`  
- Swarm heartbeat thread during task exec; `STALE_HEARTBEAT_TIMEOUT=900`  
- Docs: `docs/runtime-execution.md`  

Remaining from original plan: Phase 3 routing/tiers, Phase 4 supervision loop,
Phase 5 PATH-shim governance for hookless runtimes.

Scope (original): review only — no code changes. This document is the work order for follow-up
implementation (each task has file pointers and acceptance criteria so it can be
handed to any implementation agent).

Focus: the product vision — **Claude orchestrates; Codex / Gemini / Antigravity /
Grok / GLM and other subscription-CLI agents implement tasks under Niyam's
governance, staying in sync** — and how far the current code actually delivers it.

---

## 1. Current understanding (what exists and is real)

The vision is already codified in `ROADMAP.md` ("Claude defines. Codex/Gemini build.
Niyam controls. CI validates. Claude reviews only evidence.") and a large fraction
of the machinery genuinely exists:

| Layer | Where | Status |
| --- | --- | --- |
| Source of truth | `.niyam/` (context, policies, agents, memory, runs) | Real |
| Runtime projection | `niyam/runtimes/{base,claude,codex,gemini}.py` — generates CLAUDE.md / AGENTS.md / GEMINI.md, hooks, settings | Real, one-way |
| Task contracts | `TaskContract` Pydantic model, `niyam/core/config.py:213-264` — agent, runtime, depends_on, allowed/blocked files, acceptance criteria, validation commands, risk, retries | Real |
| Planning | `niyam/mission/planner.py` — shells out to orchestrator CLI, retries with corrective prompts, RAG context via `CodebaseIndexer`, DAG validation with cycle detection | Real |
| Execution | `niyam/mission/executor.py` + `task_runner.py` — ThreadPoolExecutor, dependency-gated scheduling, file-overlap collision checks, swarm locks, approval gates | Real |
| Isolation | `niyam/mission/worktree.py` — per-task git worktree + branch, branch inherits from first dependency, extra deps merged in, leaf branches merged at the end | Real |
| Failure handling | retries with healing prompts, AI "delta replan", skip/rollback/checkpoint, 17-state task state machine with legal-transition enforcement | Real |
| Governance | write-scope enforcement with git revert of out-of-scope changes (`task_runner.py:1235-1321`), budget enforcement mission+task level (`executor.py:439-481`, `task_runner.py:1548-1606`), policy hooks, evidence/audit JSONL everywhere | Real |
| Swarm coordination | `niyam/core/swarm.py` — FileLock + JSON state, heartbeat, stale-agent lock recovery, negotiation ledger | Real |
| Shared memory | `core/memory_ledger/` JSONL ledger + lineage, MCP memory server (`mcp/memory_server.py`) usable by any MCP-capable runtime | Real |
| Portal/API | `api/server.py` FastAPI dashboard, mission pause/resume/approve, per-task approve/deny | Real |
| Cost tracking | token ledger, cost events, budget alerts at 80% | Real |

**Verdict on the vision:** the *skeleton* of "Claude orchestrates, other CLIs
execute" is genuinely implemented — per-task `runtime` field, runtime failover
chain on rate-limit/quota errors, cross-runtime shared memory, evidence trail.
This is not vaporware. The problem is the **seam where Niyam meets the real
vendor CLIs**: invocation flags, output parsing, hook schemas, and the runtime
registry were modeled on Claude Code and *assumed* for everything else. Most of
the multi-runtime path likely works in tests (which fake the CLIs) but not
against the real `codex` / `gemini` binaries, and there is no way to add new
runtimes (Antigravity, Grok, GLM, Qwen…) without editing Niyam source.

---

## 2. Critical gaps (ranked)

### GAP-1 — Runtime invocation does not match the real vendor CLIs  (CRITICAL)

The single most important defect. Evidence:

1. **Executor invocation** (`task_runner.py:1125-1150`): builds
   `[runtime, prompt_path]` — the *path to prompt.md* as a bare positional arg.
   - Claude Code: a positional arg is treated as the **prompt text**, so Claude
     receives the literal string ".niyam/runs/…/prompt.md" and only "works"
     because an agent with file tools may decide to read that path. Fragile,
     non-deterministic.
   - Codex CLI: a bare positional arg opens the **interactive TUI**; with
     `stdin=DEVNULL` (parallel mode) it hangs or dies. Non-interactive mode
     requires `codex exec "<prompt>"`.
   - Gemini CLI: needs `-p/--prompt` or stdin; a positional path is not a prompt file.
2. **Planner invocation** (`planner.py:771-773`): `[orchestrator, "-p", prompt]`
   for all runtimes plus `--skip-trust` for gemini.
   - On Codex CLI `-p` means `--profile` — the prompt becomes a profile name.
   - `--skip-trust` is not a real Gemini CLI flag (approval bypass is `--yolo` /
     `--approval-mode`).
   - The full prompt is passed via **argv** — breaks on ARG_MAX for large
     plans; 180s timeout is small for real planning runs.
3. **Token parsing** (`parse_cli_token_usage`, `task_runner.py:176-255`): regexes
   match invented formats ("`Gemini tokens: N (prompt: X / candidates: Y)`",
   "`Codex tokens: …`") that no real CLI prints. Real usage never parses; the
   engine silently falls back to char-count estimation, so all cost/budget
   governance runs on fabricated numbers.
4. **No JSON output modes used.** All three CLIs have machine-readable output
   (`claude -p --output-format json`, `codex exec --json`, `gemini -o json`)
   which would give reliable result/usage/error extraction. None is used.
5. **No `--model` is ever passed** to any CLI, so per-model routing or cost
   tiering is impossible today, and the cost ledger records `model="claude"`
   (the runtime name) rather than an actual model id (`task_runner.py:399-400`).

### GAP-2 — Runtime registry is closed: exactly 3 hardcoded runtimes  (CRITICAL for the vision)

- `Runtime` enum = `claude | codex | gemini` (`niyam/cli/main_cmds.py:14-17`);
  dispatch is a literal if/elif in `core/sync.py:46-63`. Adding Antigravity,
  Grok, GLM, Qwen, opencode, etc. requires editing the enum, the dispatch, a new
  adapter class, planner special cases, and pricing tables.
- There is **no runtime spec**: no binary path, no args template, no
  prompt-delivery mode, no output parser, no model list, no sandbox flags, no
  auth mode. The vision of "any subscription CLI as an executor" has no
  extension point.
- Dead/missing config: `RuntimesConfig` (`config.py:166-171`) models only
  `claude` and `codex` — the `gemini:` block written by `runtime add`
  (`core/sync.py:108-112`) is silently dropped on load; the
  `generate_*` boolean flags exist but no code reads them to gate generation.

### GAP-3 — Governance is not actually enforced on non-Claude runtimes  (HIGH)

- The generated `.codex/settings.json` and `.gemini/settings.json` declare
  `pre_tool_use` hooks in **Claude Code's hook schema** (`codex.py:94-127`,
  `gemini.py:109-143`). Neither Codex CLI (config lives in `~/.codex/config.toml`)
  nor Gemini CLI honors that file/schema — the deny-list hook is fictional for
  both. Real enforcement for non-Claude executors today is only:
  (a) prose in AGENTS.md/GEMINI.md (advisory), and
  (b) **post-hoc** write-scope revert after the task finishes.
- Niyam never configures the vendors' own sandboxes (`codex --sandbox
  workspace-write`, gemini sandbox/approval flags), which is the real mechanism
  available for those CLIs.
- Command deny-lists (`rm -rf`, `git push --force`, …) are therefore
  unenforced at runtime for Codex/Gemini executors.

### GAP-4 — "Claude orchestrates" is one-shot, not a supervision loop  (HIGH)

- The orchestrator's intelligence is used exactly twice: initial plan generation
  and failure-triggered "delta replan". There is no per-task evidence review
  loop wired into mission execution (the ROADMAP's "Claude reviews only
  evidence → PASS / REWORK_REQUIRED verdict" flow): `review`-type tasks are just
  another CLI subprocess with a prompt, and no structured verdict model gates
  task completion.
- Worktree merge conflicts abort the entire mission (`worktree.py:237-244`,
  `:356-362`) instead of spawning a conflict-resolution/rework task for the
  orchestrator to adjudicate.
- The scheduler in `executor.py` re-implements DAG readiness inline instead of
  using `DAGPlanner.executable_layers()` — two divergent readiness computations
  to maintain.

### GAP-5 — Swarm lock stealing from live agents  (HIGH, concrete bug)

- `STALE_HEARTBEAT_TIMEOUT = 60` s (`core/swarm.py:22`) but agents heartbeat
  **only at lock acquisition** (`executor.py:83,113`); tasks then run up to
  `timeout_seconds` (default 600 s, `config.py:249`). Any contender arriving
  >60 s into a running task classifies the holder as dead and **steals its file
  locks** (`swarm.py:165-176`), defeating collision protection exactly when two
  missions/agents overlap. Needs a periodic heartbeat thread during execution
  (or a much larger timeout tied to task timeout).
- The `handoff` ledger action is defined but never emitted — inter-agent
  handoff messaging is unimplemented.

### GAP-6 — Token-efficiency story leaks  (MEDIUM)

- CLAUDE.md is generated by concatenating **all** memory files + architecture +
  validation + commands + policies — always-loaded bloat contradicting the
  "keep CLAUDE.md minimal" roadmap rule.
- `_load_agent_context` (`core/loopops/runner.py:783`) injects **every**
  `.niyam/memory/*.md` into **every** agent iteration.
- Two divergent pricing tables (`core/cost.py:DEFAULT_PRICING` per-model vs.
  hardcoded per-runtime rates in `task_runner.py:281-285`) with stale prices.
- "Marketing savings" metrics fabricate a baseline via a configurable
  multiplier (`task_runner.py:331-348`) — fine that it's labeled, but it should
  never appear in evidence reports next to measured numbers.

### GAP-7 — Sync is one-way with no drift guard for projected files  (MEDIUM)

- Only generated hooks get SHA-256 checksums (`base.py:205-219`). CLAUDE.md /
  AGENTS.md / GEMINI.md / settings have no tamper/drift detection; hand edits
  are silently clobbered on next `niyam sync` (or silently diverge until then).
  `niyam doctor` checks presence, not content.

### GAP-8 — Portal/API security (previously identified, still relevant to orchestration)

- GET endpoints (missions, swarm state, logs, evidence) are unauthenticated;
  only mutating POSTs require `X-Niyam-Token`. Combined with earlier findings
  (token injected into HTML, CORS wildcard) this is the weakest wall around
  remote mission control.

---

## 3. Improvements beyond gap-fixes

1. **Runtime capability probing** — `niyam doctor` should run `<binary> --version`
   and a 1-token smoke prompt per configured runtime and record capabilities
   (JSON output? model flag? non-interactive mode?) into `.niyam/runtimes.yaml`.
2. **Cost-aware routing policy** — a `routing:` block in `niyam.yaml`
   (planner/reviewer → premium tier; implementation → mid; docs/tests/mechanical →
   cheapest) consumed by the planner instead of "AI may optionally pick a runtime".
3. **Executor result contract** — require executors to end with a structured
   summary (JSON block: files changed, commands run, self-assessment) parsed from
   JSON output mode, stored as `executor-summary.json` in the task dir; feeds the
   reviewer without re-reading the repo.
4. **Cross-runtime comparison** — `niyam compare TASK --executors codex,gemini`
   exists as a CLI stub concept in the roadmap; once RuntimeSpec lands it becomes
   a loop over executors + a judge review.
5. **Periodic sync of task state to the memory ledger** so a later agent
   (any runtime) can recall "what did TASK-003 decide" via the MCP memory server —
   the plumbing exists; missions just don't write decisions into it.

---

## 4. Implementation plan (phased; hand each phase to an implementation agent)

Ground rules for implementers: Python 3.11+, Typer/Pydantic/Rich per existing
style; every phase lands with pytest coverage (`tests/` follows feature-named
test files); run `pytest`, `ruff check .`, `ruff format --check .` before done;
never break the existing CLI surface (regression suite:
`tests/regression/test_existing_cli_compatibility.py`).

### Phase 0 — Truth harness (prereq for everything)  [S]

Goal: make "does it work against the real CLI" testable without subscriptions.

- T0.1 Build fake vendor CLIs under `tests/fakes/` (`fake-claude`, `fake-codex`,
  `fake-gemini`) that emulate the *real* argument grammar and output of each
  vendor CLI (including JSON output modes and their real failure behaviors:
  codex TUI-on-positional-arg, gemini unknown-flag error, etc.).
- T0.2 Integration tests that run a 2-task mission end-to-end against the fakes
  via PATH injection; assert prompts arrive intact, usage is parsed, states
  transition.
- Acceptance: current invocation code **fails** these tests for codex/gemini
  (documenting GAP-1), passes for claude.

### Phase 1 — Declarative RuntimeSpec + open registry  [L]

Goal: kill the closed enum; make Grok/GLM/Antigravity/Qwen addable via config only.

- T1.1 New `RuntimeSpec` Pydantic model in `niyam/core/config.py`:
  `name`, `binary`, `exec_args` (template list, e.g. `["exec", "--json",
  "{prompt}"]`), `prompt_delivery` ∈ `argv|stdin|file-flag`, `plan_args`,
  `model_flag`, `models` (tier map: `premium|standard|economy` → model id),
  `sandbox_args`, `env`, `output_format` ∈ `json|text`, `usage_parser` (named
  strategy), `pricing`, `exhaustion_patterns`, `capabilities`.
- T1.2 Registry: `niyam/runtimes/registry.py` loading built-in specs
  (claude/codex/gemini, with **correct** real-CLI grammars) merged with user
  specs from `.niyam/runtimes.yaml`. Replace the `Runtime` enum in CLI with a
  dynamic completion + validation against the registry (keep enum values
  working for back-compat).
- T1.3 Split adapters: `ProjectionAdapter` (today's sync/clean, unchanged) vs.
  new `ExecutionAdapter` that renders invocation from `RuntimeSpec`. A
  `GenericProjectionAdapter` (AGENTS.md-style) covers unknown runtimes so
  `niyam runtime add grok --binary grok ...` works with zero code changes.
- T1.4 Fix dead config: add `gemini` (and generic entries) to `RuntimesConfig`
  with `extra="allow"`; make adapters honor the `generate_*` flags or delete
  the flags.
- Acceptance: `niyam runtime add` accepts a custom spec; a fake "grok" CLI from
  Phase 0 executes a task with no Niyam source edits; regression suite green.

### Phase 2 — Correct vendor invocations + structured output  [M]

Goal: the three built-ins actually work against real CLIs.

- T2.1 Claude: task exec → `claude -p "$(cat prompt)" --output-format json
  --permission-mode acceptEdits [--model X]` with prompt via **stdin**;
  planner same. Parse `result`/`usage` from JSON.
- T2.2 Codex: `codex exec --json [--model X] [--sandbox workspace-write] -` with
  prompt on stdin; parse JSONL events for result + `token_usage`. Remove `-p`.
- T2.3 Gemini: `gemini -o json [-m X] [--approval-mode auto_edit]`, prompt via
  stdin; drop `--skip-trust`; parse JSON `stats` for usage.
- T2.4 Delete the invented regexes in `parse_cli_token_usage`; usage comes from
  the per-runtime `usage_parser` strategy; keep char-count estimate only as a
  labeled fallback (`estimated: true`).
- T2.5 Single pricing source: delete the hardcoded rates in
  `task_runner.py:281-285`; route everything through `core/cost.py` keyed by
  **actual model id** now available from JSON output; record real model in
  `CostEvent`.
- T2.6 Raise planner timeout (config-driven, default 600s); prompt via stdin
  everywhere (no ARG_MAX).
- Acceptance: Phase-0 integration tests pass for all three; a manual smoke
  against at least one real CLI documented in `docs/`.

### Phase 3 — Model tiering & cost-aware routing  [M]

- T3.1 Add `model: Optional[str]` and `tier: Optional[premium|standard|economy]`
  to `TaskContract`; executor resolves tier → model via RuntimeSpec.
- T3.2 `routing:` block in `niyam.yaml`: defaults per task `type`
  (discovery/review → premium; implementation → standard; validation/docs →
  economy) + per-agent overrides. Planner prompt instructs the orchestrator to
  assign tiers; post-normalization enforces routing policy over AI whims.
- T3.3 Budget-aware degradation: at 80% mission budget, new task submissions
  drop one tier (log an event); at 100% keep the existing hard fail.
- T3.4 Failover stays runtime-level but must preserve tier when hopping
  runtimes (map tier → the fallback runtime's model list).
- Acceptance: token-ledger events show real model ids and per-tier costs; test
  proves an over-budget mission degrades tier before failing.

### Phase 4 — Orchestrator supervision loop  [L]

Goal: Claude actually orchestrates, not just plans.

- T4.1 Evidence-pack reviewer: after each `implementation` task completes
  validation, build an evidence pack (contract + `git diff` + validation output
  + executor summary) and invoke the **reviewer runtime** (config:
  `orchestrator.reviewer`, default claude premium) for a structured verdict
  `PASS | REWORK_REQUIRED | REJECT` (+ `required_changes`). Persist
  `review-verdict.yaml` in the task dir.
- T4.2 Wire verdict into the state machine: `reviewing → completed` on PASS;
  `reviewing → retry_ready` with `healing_prompt := required_changes` on
  REWORK (bounded by existing `max_retries`); REJECT → `failed`.
- T4.3 Merge-conflict recovery: on final-merge conflict, instead of aborting,
  generate a `recovery` task (conflict files + both branch diffs in the prompt)
  and pause for approval — reuse the existing delta-replan machinery.
- T4.4 Replace the executor's inline readiness computation with
  `DAGPlanner.executable_layers()` (single source of scheduling truth).
- Acceptance: integration test where a fake executor produces a bad diff →
  reviewer REWORK → healed rerun → PASS; merge-conflict test produces a
  recovery task instead of mission failure.

### Phase 5 — Real governance for non-Claude executors  [M]

- T5.1 Remove the fictional `pre_tool_use` hook generation for codex/gemini
  (or gate behind a capability flag that defaults off). Document that Claude
  hooks are the only in-loop enforcement today.
- T5.2 Configure vendor sandboxes from policy: RuntimeSpec `sandbox_args`
  driven by `.niyam/policies/` (e.g. codex `--sandbox workspace-write`,
  gemini approval mode). Guard-enabled ⇒ sandbox flags mandatory.
- T5.3 PATH-shim command guard for hookless runtimes: generate a shim dir
  (wrappers for `git`, `rm`, `npm`, …) prepended to the executor subprocess
  PATH that consults `guard-config.json` and blocks/logs denied commands —
  runtime-agnostic in-loop enforcement.
- T5.4 Periodic heartbeat: background thread in `execute_single_task`
  heartbeating every 20s while the subprocess runs; make
  `STALE_HEARTBEAT_TIMEOUT` configurable. Fixes GAP-5 lock stealing.
- Acceptance: fake-codex attempting `git push --force` via shim is blocked and
  logged to policy-events; lock-stealing regression test (two missions, long
  task) passes.

### Phase 6 — Sync hardening + token diet  [S]

- T6.1 Checksum **all** projected files (extend `hook_checksums.json` →
  `projection-manifest.json`); `niyam sync` warns on hand-edited drift and
  requires `--force` to clobber; `niyam doctor` reports drift.
- T6.2 CLAUDE.md diet: generate a compact core (project brief, validation
  commands, policy summary) and move long context to scoped files referenced
  by path; memory injection becomes top-K relevant records via the existing
  `CodebaseIndexer`/ledger search instead of "all .md files".
- T6.3 Keep marketing metrics out of evidence: `show_marketing_metrics`
  affects dashboards only.
- Acceptance: generated CLAUDE.md under a configurable token budget; drift test.

### Phase sequencing & sizing

| Phase | Size | Depends on | Value |
| --- | --- | --- | --- |
| 0 Truth harness | S | — | Makes every later claim testable |
| 1 RuntimeSpec registry | L | 0 | Unlocks "any CLI" vision |
| 2 Correct invocations | M | 0,1 | Multi-runtime actually works |
| 3 Tiering & routing | M | 2 | The "cheaper models implement" economics |
| 4 Supervision loop | L | 2 | The "Claude orchestrates" promise |
| 5 Governance parity | M | 1,2 | Enterprise trust story |
| 6 Sync + token diet | S | — (parallel) | Token-cost credibility |

Suggested order: 0 → 1 → 2 → (3 ∥ 5) → 4 → 6. Phases 0+2 alone turn the
existing engine from "works in tests" into "works with real Codex/Gemini",
which is the fastest credibility win.

---

## 5. Post-gap enhancement roadmap (Phases E1–E5)

Prerequisites: Phases 0–3 above (RuntimeSpec registry, correct invocations with
JSON output + real model ids, tier routing). Everything below builds on those.
Theme: **role-based model assignment, higher useful parallelism, and aggressive
token reduction — all user-configurable.**

### E1 — Role-based agents with user-preference model binding  [M]

Today agents are plain prose `.md` files; role → model binding doesn't exist.

- E1.1 **Structured agent definitions.** Add optional YAML frontmatter to
  `.niyam/agents/*.md` (backward compatible — files without frontmatter behave
  as today):

  ```yaml
  ---
  role: tester            # engineer | tester | qa | security | uiux | docs | architect | reviewer
  default_tier: economy   # premium | standard | economy
  preferred_runtimes: [gemini, codex]
  context_profile: tests  # see E3.1
  tools: [bash, edit]     # advisory; enforced where the runtime supports it
  ---
  ```

  Parse in the planner where agents are loaded (`planner.py:558-564`) and
  surface role/tier into the planner prompt so task→agent assignment is
  role-aware rather than filename-string matching.
- E1.2 **Built-in role catalog.** Ship agent templates for the standard roles
  (engineer-backend, engineer-frontend, tester, qa-verifier,
  security-reviewer, uiux-designer, docs-writer, architect) under
  `niyam/templates/profiles/*/agents/`, each with a role frontmatter and a
  role-appropriate context profile.
- E1.3 **User preference layer.** New `roles:` block resolvable from three
  levels — project `niyam.yaml`, user `~/.niyam/preferences.yaml`, and CLI
  flags — with precedence CLI > user > project > built-in default:

  ```yaml
  roles:
    engineer:  {runtime: codex,  tier: standard}
    tester:    {runtime: gemini, tier: economy}
    security:  {runtime: claude, tier: premium}
    qa:        {runtime: gemini, tier: economy}
    uiux:      {runtime: claude, tier: standard}
    reviewer:  {runtime: claude, tier: premium}
  ```

  CLI surface: `niyam role list` (effective bindings + source of each),
  `niyam role set tester gemini:economy [--user|--project]`,
  `niyam run --role-override security=claude:premium`.
- E1.4 **Resolution order at execution time:** task.model (explicit) →
  task.tier → role binding (E1.3) → routing defaults (Phase 3) → mission
  orchestrator. Log the resolved (runtime, model, source) into the task dir so
  evidence shows *why* a model was chosen.
- E1.5 **Mission presets.** `niyam run --preset economy|balanced|quality`
  mapping to prepackaged role-binding sets, so a user preference is one flag,
  not eight bindings.
- Acceptance: integration test proving a mission with engineer/tester/security
  tasks resolves three different (runtime, model) pairs from a preferences
  file; `role list` shows precedence correctly; missions without any
  preferences behave exactly as before.

### E2 — True multi-model parallelism  [M]

Parallelism today is a single `parallel: N` thread pool; all tasks contend for
one implicit vendor. Multiple subscriptions are an unexploited *capacity
multiplier* — different vendors' rate limits are independent pools.

- E2.1 **Per-runtime concurrency pools.** `RuntimeSpec.max_parallel` (e.g.
  claude 2, gemini 4, codex 3). Scheduler submits a ready task only when its
  resolved runtime has a free slot; global `parallel` becomes a cap, not the
  only knob. Implementation: per-runtime semaphores around the
  `executor.submit` gate (`executor.py:579`).
- E2.2 **Runtime-aware wave packing.** When multiple tasks are ready, prefer
  interleaving runtimes (round-robin across vendors) instead of FIFO, so a
  wave of 6 tasks spreads across 3 subscriptions rather than queueing on one.
- E2.3 **Pipelined review.** Reviewer (Phase 4) runs as its own pooled stage:
  task B implements while task A is under review — reviewer slots come from
  the reviewer role's runtime pool, so review never blocks implementation
  throughput.
- E2.4 **Racing / N-version for high-risk tasks.** Optional
  `strategy: race` on a task: run the same contract on 2 executors in separate
  worktrees in parallel, reviewer judges, winner's branch is kept, loser's
  worktree discarded. Reuses `niyam compare` semantics inside a mission.
  Guard with tier policy (race only economy models by default).
- E2.5 **Cross-mission fairness.** With the E5.4/T5.4 heartbeat fix in place,
  allow two missions to run concurrently, sharing the per-runtime pools via
  swarm state (pool counts recorded in `.niyam/swarm/state.json`) instead of
  per-process semaphores only.
- Acceptance: fake-CLI integration test with 6 independent tasks across 3
  runtimes shows ≥3 concurrent subprocesses with per-runtime caps honored;
  race test produces one merged winner + evidence of the judgment.

### E3 — Token-reduction program  [L, highest ROI]

Measured target: cut input tokens per mission substantially; every item below
is independently landable and measurable via the (now real) JSON usage data.

- E3.1 **Role-scoped context profiles.** Extend `ContextRouter`
  (`task_runner.py:934-948`) with named profiles: `tests` (test dirs + task
  contract + failing output), `uiux` (component/styles dirs), `security`
  (diff + dependency manifests + auth paths), `docs` (README/docs only),
  `code` (pruned repo map as today). Agent frontmatter picks the profile
  (E1.1). Stop giving every agent the same repo map.
- E3.2 **Mission context pack.** The discovery task's output becomes a
  structured, cached artifact (`.niyam/runs/<mid>/context-pack.json`: file
  inventory, key symbols, conventions). Sibling tasks receive the pack
  *section* relevant to their files instead of re-exploring the repo — the
  single biggest duplicate-token sink in multi-task missions.
- E3.3 **Stable prompt prefix for vendor prompt caching.** Order every task
  prompt as [agent md → project context → policies] (stable across tasks)
  followed by task-specific material, so Claude/Gemini prompt caches hit.
  Record `cache_read_tokens` from JSON usage in the token ledger and show
  cache-hit rate in `mission metrics`.
- E3.4 **Session resume for healing loops.** On retry/heal, resume the
  executor's previous session (`claude --resume <id>`, `codex exec resume`)
  with only the corrective delta instead of resending the full prompt.
  `RuntimeSpec.capabilities.session_resume` gates it; fall back to full prompt.
- E3.5 **Log & diff summarization before review.** Reviewer receives: diff
  stat + hunks for changed files only, last-failure excerpt of test output
  (not full logs), executor summary JSON. Cap review input with a per-role
  token budget; summarize overflow with an economy-tier model.
- E3.6 **Retry context diet.** Healing prompts include only failing-file
  contents + validation errors, never the full original context (today the
  full prompt is rebuilt each retry).
- E3.7 **Memory recall top-K.** Replace inject-all `.niyam/memory/*.md`
  (`loopops/runner.py:783`) with ledger/`CodebaseIndexer` top-K scoped by the
  task's files and role (shared with Phase 6 T6.2).
- Acceptance: a benchmark mission (fixed fixture repo, 5 tasks) measured
  before/after each item via the token ledger; target ≥40% input-token
  reduction for the full program; cache-hit rate visible in metrics.

### E4 — Data-driven routing feedback  [M]

Make the role→model preferences self-tuning instead of guesswork.

- E4.1 **Per-(role × runtime × model) analytics** from existing ledgers:
  success rate, avg retries, avg cost, avg wall-time, review-verdict
  distribution. Surface as `niyam cost by-role` and in the portal.
- E4.2 **Routing suggestions.** `niyam role tune` reports "tester on
  gemini:economy has the same pass rate as codex:standard at 30% of the cost —
  suggest switching" (suggestion only; user applies via `niyam role set`).
- E4.3 **Escalation ladder.** Optional per-role policy
  `escalate_on_rework: true`: first attempt at the bound tier; a REWORK verdict
  re-runs at the next tier up (bounded by max_retries). Cheap-first with a
  quality backstop — this is where "use cheaper models to implement" pays off
  safely.
- Acceptance: analytics computed from existing `token-ledger.json` +
  `review-verdict.yaml` fixtures; escalation test shows economy→standard hop
  after a REWORK verdict.

### E5 — Operator experience for multi-agent runs  [S]

- E5.1 **Lane view** in `niyam watch` / portal: one lane per active agent
  showing role, runtime:model, current task, live token/cost burn, and state —
  the "mission control" picture for parallel runs.
- E5.2 **Per-role budget bars** (role budgets = sum of task budgets by role)
  with the existing 80%/100% thresholds.
- E5.3 **Preference doctor.** `niyam doctor` validates role bindings against
  installed runtimes/models (catches "tester bound to gemini but gemini not on
  PATH") and reports effective preference resolution.

### Sequencing after Phases 0–6

| Phase | Size | Depends on | Value |
| --- | --- | --- | --- |
| E1 roles + preferences | M | 1–3 | The user-facing "assign models to roles" feature |
| E2 multi-model parallelism | M | 1–2, T5.4 | Subscriptions become parallel capacity |
| E3 token program | L | 2, 4 | Direct cost reduction, measurable |
| E4 routing feedback | M | E1, 4 | Preferences become data-driven |
| E5 operator UX | S | E1–E2 | Trust/visibility for parallel runs |

Suggested order: E1 → E3.1–E3.3 (quick token wins) → E2 → E3.4–E3.7 → E4 → E5.
E1 first because every other enhancement keys off the role concept.

---

## 6. One-paragraph summary

Niyam's orchestration engine is far more built-out than a typical prototype —
contracts, DAG execution, worktree isolation, healing, budgets, swarm locks,
shared memory, and evidence are all real. What's missing is precisely the seam
the product is named for: the runtime layer speaks Claude's dialect to every
CLI (wrong flags, invented output formats, fictional hook schemas), supports
exactly three hardcoded runtimes with no extension point, never selects models
(so no cheap-model economics), and uses the orchestrator's intelligence only at
plan time rather than as a supervising reviewer. Fix the invocation seam
(Phases 0–2) first — everything else in the vision is already standing on top
of it.
