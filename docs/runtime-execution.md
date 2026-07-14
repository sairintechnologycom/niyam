# Runtime execution (orchestration)

Niyam invokes coding-agent CLIs through a declarative **RuntimeSpec** registry
rather than hard-coding Claude-only argv shapes.

## Built-in specs

| Runtime | Non-interactive shape | Prompt delivery | Usage parser |
| --- | --- | --- | --- |
| `claude` | `claude -p <prompt> --output-format json --permission-mode acceptEdits` | argv (`-p`) | `claude_json` |
| `codex` | `codex exec --sandbox workspace-write --json -` | stdin | `codex_jsonl` |
| `gemini` | `gemini -p <prompt> -o json` | argv (`-p`) | `gemini_json` |

Source: `niyam/runtimes/specs.py`, registry merge in `niyam/runtimes/registry.py`,
invocation in `niyam/runtimes/executor.py`.

Mission task execution (`mission/task_runner.py`) and LoopOps adapters call
`run_runtime()` so plan/exec share one path.

## Custom runtimes

Add under `.niyam/runtimes.yaml`:

```yaml
execution_specs:
  grok:
    binary: grok
    prompt_delivery: stdin
    exec_args: ["exec", "-"]
    plan_args: ["exec", "-"]
    usage_parser: generic_json
    capabilities: ["implementation"]
```

Unknown names still get a generic `binary exec -` stdin fallback.

## Truth harness

Fake CLIs live under `tests/fakes/bin/{claude,codex,gemini}` and emulate real
failure modes (e.g. Codex without `exec` rejects non-interactive use).

```bash
export PATH="$PWD/tests/fakes/bin:$PATH"
pytest tests/test_runtime_orchestration.py -q
```

## Swarm heartbeats

Long mission tasks start a background heartbeat thread so locks are not stolen
after 60s. `STALE_HEARTBEAT_TIMEOUT` is 900s as a floor.

## Cost-aware routing (Phase 3)

`niyam.yaml`:

```yaml
routing:
  by_type:
    discovery: premium
    review: premium
    implementation: standard
    validation: economy
  by_agent: {}
  default_tier: standard

governance:
  budget:
    max_mission_cost_usd: 25.0
    degrade_tier_at: 0.8   # drop one tier at 80% spend
```

Task contracts may set `tier` and/or `model`. Planner post-normalization fills
defaults; at 80% mission budget the next task drops one tier
(premium→standard→economy). Failover keeps the same tier and re-resolves the
model on the fallback runtime.

## Evidence review (Phase 4)

After implementation validation, Niyam runs an orchestrator evidence review
(configurable via `orchestrator.reviewer` / `evidence_review`). Verdicts:

- `PASS` → continue
- `REWORK_REQUIRED` → `retry_ready` with `healing_prompt`
- `REJECT` → task failed

Artifacts: `tasks/T*/evidence-pack.md`, `review-verdict.yaml`.
