# Progress

## 2026-06-09 Roadmap Status Validation

Validated the implemented roadmap surface against the governance, orchestration,
swarm, fleet, and PR test suites.

Command:

```bash
pytest tests/test_rules.py tests/test_readiness_scoring.py tests/e2e/test_scan_e2e.py tests/test_guard_observe.py tests/test_redaction.py tests/test_path_freeze.py tests/e2e/test_mcp_e2e.py tests/test_cost.py tests/e2e/test_evidence_e2e.py tests/test_scan_ci_gates.py tests/test_mission.py tests/test_parallelism.py tests/test_swarm.py tests/test_fleet_cli.py tests/test_pr.py
```

Result:

```text
144 passed, 1 warning in 75.95s
```

Warning:

- `tests/test_swarm.py::TestHeartbeat::test_naive_timestamp_handled` emits a
  Python 3.14 deprecation warning for `datetime.utcnow()`.

Validated complete:

- Scanner core, built-in profiles, custom rules, readiness scoring, CLI output,
  report generation, and CI gate behavior.
- Guard subprocess observation, policy modes, audit logging, redaction, and path
  freeze behavior.
- MCP/tool registry workflow and FinOps token cost logging/reporting.
- Evidence compiler with redaction.
- Mission planning/execution lifecycle, approvals, budgets, metrics, audit, and
  SaaS telemetry integration.
- Parallel discovery, serialized implementation behavior, and DAG ordering.
- Swarm state locking, atomic writes, heartbeat, stale recovery, negotiation
  ledger, and CLI commands.
- Fleet discovery/status/policy sync and PR evidence flows.

Research-informed pending roadmap:

| Priority | Item | Status |
| --- | --- | --- |
| P0 | `1.0.0-rc1` release readiness | Pending |
| P1 | Dashboard/operator evidence UX | Pending |
| P1 | CI/CD and supply-chain hardening | Pending |
| P1 | Task-contract canonical model | Pending |
| P2 | Agent skill/tool governance | Pending |
| P2 | Enterprise policy workflows | Pending |
| P3 | Fleet-level mission dispatch | Pending |
| P3 | Agent performance analytics | Pending |

Research inputs:

- NIST AI RMF and Generative AI Profile for evidence-backed AI risk management.
- OWASP Agentic Skills Top 10 for agent skill inventory, least privilege,
  isolation, monitoring, and incident response.
- OpenSSF SLSA and Scorecard for software supply-chain provenance and automated
  repository security posture measurement.

## 2026-06-09 AgentOps Roadmap Alignment

Reviewed the proposed "Governed Execution + Portable Memory" strategy against
the current Niyam structure.

Current structure alignment:

- `niyam memory` already exists with `show`, `add`, and `clear`.
- `niyam/core/memory.py` already writes markdown memory and appends a structured
  `.niyam/memory/index.jsonl` record.
- `niyam mcp`, `guard`, `cost`, `evidence`, `mission`, `swarm`, `fleet`, and
  the portal/API already provide the foundation for AgentOps governance.
- `niyam workspace` does not exist today, so Control Room should initially build
  on `mission` and `portal`; a dedicated `workspace` command remains a future
  naming decision.

Phased roadmap added to `ROADMAP.md`:

| Phase | Focus | Status |
| --- | --- | --- |
| A | Documentation and release alignment | Done |
| B | Memory Ledger core | Done |
| C | Memory policy, redaction, and lineage | Done |
| D | MCP-compatible memory server | Done |
| E | Control Room MVP on current mission/portal foundations | Pending |
| F | Browser sandbox and human takeover | Pending |
| G | Evidence and portal integration | Pending |
| H | Enterprise and fleet expansion | Pending |

Non-breaking constraints:

- Preserve existing `niyam memory show/add/clear`.
- Keep the Memory Ledger MVP local-first.
- Add evidence sections for memory/workspace as opt-in includes.
- Do not introduce `niyam workspace` until command naming is validated.
- Keep existing scan, guard, MCP, cost, evidence, mission, swarm, fleet, and PR
  functionality green while adding AgentOps modules.
