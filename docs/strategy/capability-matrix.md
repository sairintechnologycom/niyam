# Niyam Capability Matrix

**Status date:** 2026-07-14  
**Codebase version:** 1.0.0  
**Scope:** What is built, partial, early, or not built relative to the company platform thesis.

---

## 1. Executive one-pager

### Company thesis

> **Niyam is the Trust & Execution Platform for Enterprise AI** — enable every enterprise AI system to safely move from prototype to trusted production.

Governance, compliance, guardrails, FinOps, runtime control, and evidence are **modules**, not the brand.

### Current product truth (honest)

| Layer | Reality today |
| --- | --- |
| **What Niyam is** | Local-first **AgentOps control plane** for governed AI coding agents and AI-assisted repositories |
| **Strongest commercial surface** | Production readiness scoring + policy enforcement + evidence packs |
| **What Niyam is not yet** | Org-wide AI inventory, multi-cloud discovery, enterprise Trust Center, or universal agent fabric |
| **Platform maturity (full vision)** | ~**3.5 / 10** — deep vertical product; shallow enterprise platform breadth |
| **AgentOps maturity (coding agents)** | ~**8 / 10** — multi-module, CLI-complete, tested |

### Status legend

| Status | Meaning |
| --- | --- |
| **Built** | CLI/API + core logic + meaningful tests |
| **Partial** | Real capability, narrower than platform thesis (scope, depth, or polish) |
| **Early** | Shell, hooks, or scaffolding — not a full product surface |
| **Not built** | Vision only |

### Domain snapshot

| Domain | Status | One line |
| --- | --- | --- |
| Production readiness scoring | **Built** | Strongest commercial wedge |
| Policy / guardrails (repo/agent) | **Built** | Enforce at shell/path/MCP/skill |
| Evidence packs | **Built** | Multi-section, identity-signable |
| Agent execution (mission/loop/swarm) | **Built** | Coding-agent runtime |
| FinOps (token cost) | **Partial** | Ledger + scorecard; no outcome ROI |
| Discovery / inventory | **Early–Partial** | Fleet = Niyam workspaces only |
| Architecture intelligence | **Early** | Stack/context refresh |
| Trust Center (exec Q&A) | **Early** | Local portal + evidence |
| Niyam Graph / AI Application identity | **Not built** | Objects exist in silos |
| Multi-cloud connectors | **Not built** | PR/CI delivery hooks only |
| SaaS control plane | **Early** | Client upload hook |
| Continuous improvement loop | **Partial** | Memory lineage, auto-heal, analytics seeds |

### Positioning guardrails

**Can say today:**

> Niyam is the AgentOps control plane that helps teams put AI coding agents and AI-assisted repos into production with readiness scoring, policy enforcement, runtime supervision, FinOps, and audit evidence.

**Must not claim yet:**

> Niyam discovers and governs every AI system in the enterprise (ChatGPT, Copilot, RAG, multi-cloud agents).

**Bridge to company vision:**

> The same trust stack — inventory, readiness, policy, cost, evidence — expands from coding agents to the full enterprise AI control tower.

---

## 2. Lifecycle coverage

Target lifecycle:

```text
Discover → Understand → Assess → Govern → Execute → Observe → Learn → Improve
```

| Stage | Status | Primary code / CLI |
| --- | --- | --- |
| Discover | **Early** | `fleet discover`, `mcp list`, `skills list` |
| Understand | **Early** | `context refresh`, stack detector |
| Assess | **Built** | `scan`, scoring, decision engine |
| Govern | **Built** | `guard`, `policy`, MCP/skill approval |
| Execute | **Built** | `mission`, `loop`, `swarm`, `workspace` |
| Observe | **Partial** | portal, dashboard, cost, guard logs |
| Learn | **Partial** | memory ledger, baselines, analytics |
| Improve | **Early** | auto-heal, replan; no closed enterprise loop |

---

## 3. Eight pillars vs codebase

### Pillar 1 — AI Discovery

| Capability | Status | Code / CLI |
| --- | --- | --- |
| Discover Niyam workspaces | **Built** | `niyam/core/fleet.py`, `niyam fleet discover/register/list` |
| MCP / tool inventory | **Built** | `niyam/core/mcp.py`, `niyam mcp *` |
| Skill inventory | **Built** | `niyam/core/skills.py`, `niyam skills *` |
| Runtime inventory | **Built** | `niyam/runtimes/`, `niyam runtime add` |
| Org-wide AI apps / shadow AI | **Not built** | — |
| GitHub / ADO / GitLab inventory crawlers | **Not built** | PR/CI helpers only |
| AWS / Azure / GCP / K8s AI asset discovery | **Not built** | — |
| Model / prompt-chain inventory at org scale | **Not built** | model is a field on cost events only |
| Enterprise inventory dashboard | **Not built** | — |

**Verdict:** Partial — local AgentOps inventory only.

### Pillar 2 — AI Architecture Intelligence

| Capability | Status | Code / CLI |
| --- | --- | --- |
| Stack detection | **Built** | `niyam/core/scanner/stack_detector.py` |
| Project context refresh | **Built** | `niyam/core/context.py`, `niyam context *` |
| Manual architecture docs in context | **Partial** | `context add` (prd / tech-spec / custom) |
| Auto flow diagrams / dependency graphs | **Not built** | `graphify-out/` is dev tooling, not product |
| Data lineage / trust boundaries | **Not built** | — |
| External calls / identity / storage map | **Not built** | — |

**Verdict:** Early.

### Pillar 3 — AI Production Readiness ⭐ strongest product

| Capability | Status | Code / CLI |
| --- | --- | --- |
| Multi-profile scan | **Built** | `niyam scan -p startup|team|enterprise|regulated` |
| 8 scoring dimensions | **Built** | `niyam/governance/scoring.py` — secrets, auth, dependencies, cloud, production_ops, ai_risk, data_protection, documentation |
| GO / CONDITIONAL_GO / HIGH_RISK / NO_GO | **Built** | `niyam/governance/decision.py` |
| Findings + remediation effort | **Built** | `niyam/core/scan.py` |
| External scanners (gitleaks, semgrep, trivy, checkov) | **Built** | `niyam/core/external_scanners.py` |
| Baseline known findings | **Built** | `--baseline`, `--create-baseline` |
| CI gates | **Built** | `niyam ci verify/generate`, `action.yml`, `azure-devops/` |
| Auto remediation (fix PRs) | **Partial** | recommendations + evidence `remediation_plan`; not auto-fixer |
| Vision score dims (Cost / Resilience / Monitoring) | **Partial** | different taxonomy; cost not a readiness dimension |
| Non-repo AI systems (RAG, SaaS agents) | **Not built** | repo-centric only |

**Verdict:** Built for repos / AI-dev workspaces. Phase-1 commercial hero.

### Pillar 4 — AI Policy Engine

| Capability | Status | Code / CLI |
| --- | --- | --- |
| Command observe / warn / block / approve | **Built** | `niyam/policies/guard.py`, `niyam guard *` |
| Path freeze | **Built** | `guard freeze`, commit verify |
| Secret redaction | **Built** | `niyam/governance/common/redaction.py` |
| Team policy YAML + roles/rules | **Built** | `niyam/core/policy.py`, `niyam policy *` |
| Risk acceptance / exceptions | **Built** | `policy exception-add/list` |
| MCP tool approval | **Built** | `mcp approve` |
| Skill approval | **Built** | `skills approve` |
| Memory policy checks | **Built** | `memory policy-check` |
| LoopOps budgets / approval-on-risk | **Built** | `niyam loop run` |
| Org model allowlists (e.g. no GPT-4o for finance) | **Partial** | patterns possible; no multi-app policy mesh |
| Continuous enforce across cloud AI runtimes | **Not built** | local/agent path only |

**Verdict:** Built for AgentOps enforcement; Partial as enterprise policy fabric.

### Pillar 5 — Agent Runtime

| Capability | Status | Code / CLI |
| --- | --- | --- |
| Mission lifecycle | **Built** | `niyam/mission/*`, `niyam mission *` |
| Task contracts / scopes / validation | **Built** | planner, `niyam validate` |
| Worktree isolation / parallel DAG | **Built** | `mission/worktree.py`, parallelism tests |
| Swarm locks / heartbeats | **Built** | `niyam/core/swarm.py` |
| Control Room sessions | **Built** | `niyam/core/workspace/*`, `niyam workspace *` |
| Browser sandbox + takeover | **Built** | `workspace browser-*`, `takeover` |
| LoopOps | **Built** | `niyam/core/loopops/*` |
| Multi-runtime (Claude / Codex / Gemini) | **Built** | `niyam/runtimes/` |
| Auto-heal on failure | **Partial** | mission executor `auto_heal` |
| Universal agent registry (owner, authority, budget, expiry) | **Partial** | MCP/skills/swarm only |
| Pre-exec validate for any enterprise agent | **Not built** | coding-agent / loop path only |
| Multi-agent enterprise orchestration (Phase 4) | **Not built** | — |

**Verdict:** Built for coding-agent runtime; Partial as general Agent Runtime pillar.

### Pillar 6 — AI FinOps

| Capability | Status | Code / CLI |
| --- | --- | --- |
| Token/cost event log | **Built** | `niyam/core/cost.py`, `cost log` |
| Pricing tables | **Built** | `cost pricing` |
| Summary / report | **Built** | `cost summary/report` |
| Agent performance scorecard | **Built** | `cost scorecard`, `niyam/core/analytics.py` |
| Mission token waste metrics | **Partial** | analytics wasted cost / retries |
| Latency / failure signals | **Partial** | mission metrics |
| Attribution by team / AI Application | **Not built** | repo/task/session only |
| Business outcome / ROI | **Not built** | — |
| Prompt efficiency / cache hit / reasoning cost | **Not built** | — |

**Verdict:** Partial — token FinOps MVP, not business FinOps.

### Pillar 7 — AI Trust Center

| Capability | Status | Code / CLI |
| --- | --- | --- |
| Evidence packs | **Built** | `niyam/core/evidence.py`, `niyam evidence --include scan,guard,mcp,cost,memory,workspace` |
| Mission reports + verify signatures | **Built** | `mission report/verify-report`, `niyam/core/identity.py` |
| Local portal API | **Built** | `niyam/api/server.py`, `niyam portal` |
| Terminal dashboard / watch | **Built** | `dashboard`, `watch` |
| Instant exec queries (“which AI uses HR data?”) | **Not built** | no enterprise query layer |
| Org Trust Center UX | **Not built** | portal is local operator |
| SaaS dashboard as Trust Center | **Early** | `niyam/core/saas.py`, `saas config/upload` |

**Verdict:** Partial (evidence + local control room). Trust Center product = Early / Not built.

### Pillar 8 — Continuous Improvement

| Capability | Status | Code / CLI |
| --- | --- | --- |
| Memory ledger + recall lineage | **Built** | `niyam/core/memory_ledger/*` |
| Scan baselines | **Built** | `niyam/core/baseline.py` |
| Auto-heal / replan | **Partial** | mission executor, `mission replan` |
| Agent performance analytics | **Partial** | `analytics.py`, scorecard |
| Incident → policy learning loop | **Not built** | exceptions exist; no closed learning |
| Enterprise AI digital twin | **Not built** | — |
| Automated remediation at scale | **Not built** | — |

**Verdict:** Partial locally; not a continuous enterprise improvement system.

---

## 4. Ten product modules

| # | Module | Status | Primary surface |
| --- | --- | --- | --- |
| 1 | AI Inventory | **Early–Partial** | fleet + mcp + skills (Niyam objects only) |
| 2 | Architecture Discovery | **Early** | `context refresh`, stack detector |
| 3 | Production Readiness | **Built** | `scan`, scoring, decision, CI gates |
| 4 | AI Security | **Built (partial breadth)** | secrets/auth/cloud rules, redaction, external scanners, guard |
| 5 | Compliance | **Partial** | evidence packs, regulated profile, identity signing |
| 6 | AI FinOps | **Partial** | cost + analytics scorecard |
| 7 | Runtime Governance | **Built (AgentOps)** | guard, policy, MCP/skill approval, freezes |
| 8 | Agent Operations | **Built (coding agents)** | mission, loop, swarm, workspace |
| 9 | Evidence Management | **Built** | evidence/report + mission verify + templates |
| 10 | Executive AI Dashboard | **Early** | local portal + SaaS upload hook |

---

## 5. Internal engines

| Engine | Status | Notes |
| --- | --- | --- |
| Discovery Engine | **Early** | Fleet discover; no enterprise connectors |
| Architecture Engine | **Early** | Context/stack only |
| Policy Engine | **Built** | Guard + team policy + exceptions + MCP/skills |
| Runtime Engine | **Built** | Mission / loop / swarm / workspace |
| FinOps Engine | **Partial** | Token cost ledger + scorecard |
| Evidence Engine | **Built** | Multi-section compiler + HTML/MD/JSON |
| Intelligence Engine | **Early** | Analytics + memory recall; no graph intelligence |
| Portal / Control Room | **Partial–Built (local)** | FastAPI portal + workspace; not multi-tenant SaaS |
| Connectors (cloud, ITSM, IdP) | **Not built** | GitHub PR, GHA, ADO as delivery hooks only |

---

## 6. First-class objects (future Niyam Graph)

| Object | Status today |
| --- | --- |
| Repo / Niyam workspace | Implicit, strong |
| Mission / Task / LoopRun | **First-class** |
| MCP tool | **First-class** (registry) |
| Skill | **First-class** (registry) |
| Cost event | **First-class** |
| Policy / exception | **First-class** |
| Memory record | **First-class** |
| Workspace session / approval | **First-class** |
| Cryptographic identity | **First-class** (local signing) |
| **AI Application** | **Not built** |
| Model (inventory) | **Partial** (cost event field) |
| Prompt / prompt version | **Partial** (portal prompt-audit path; full audit still polish) |
| Dataset / vector store / knowledge base | **Not built** |
| **Niyam Graph (relationships)** | **Not built** |

Without **AI Application** as root identity, Inventory + Trust Center + FinOps attribution cannot become the platform thesis.

---

## 7. Company rollout phases vs maturity

| Phase | Intent | Current fit |
| --- | --- | --- |
| **P1 Trust** (0–6m): Discovery, Inventory, Readiness, Evidence | Sell trust at ship time | **~55–65% of the repo slice.** Readiness + Evidence Built. Inventory/Discovery Early. |
| **P2 Control** (6–12m): Policy, FinOps, Architecture, Exec dashboards | Policy + cost + architecture | Policy Built (local). FinOps Partial. Architecture/exec Early. |
| **P3 Execution** (12–18m): Agent registry, runtime gov, approvals, safe action | Runtime path | Coding-agent runtime Built. Universal agent registry / safe action Not built. |
| **P4 Autonomy** (18–24m): orchestration, auto-remediation, digital twin | Optimize | Auto-heal/replan Partial. Rest Not built. |

### ROADMAP Phase H (enterprise / fleet) open items

| Item | Status |
| --- | --- |
| Team policies + risk acceptance | **Built** |
| Fleet discover / status / policy sync | **Built** |
| Fleet mission dispatch | **Built** (`fleet run`) — ops UX polish remains |
| Fleet evidence rollups | **Partial** |
| Prompt / version audit | **Partial / planned polish** |
| SIEM export schemas | **Not built** |
| SSO / private deployment | **Not built** |
| Web dashboard polish | **Partial** (portal exists) |
| Azure DevOps packaging/release validation | **Partial** (extension present) |

---

## 8. Solidly shipped capabilities

Trust these as real product, not vapor:

1. Workspace bootstrap — init, setup, sync, profiles, packs, doctor  
2. Production readiness scan + decision engine  
3. Guardrails — observe/warn/block, freeze, redaction, logs  
4. MCP + skills governance  
5. Mission orchestration — plan/approve/start/pause/retry/rollback/report  
6. LoopOps — budgeted governed loops  
7. Swarm coordination  
8. Control Room workspace — sessions, timeline, browser, takeover  
9. Memory Ledger + MCP memory server  
10. Cost ledger + scorecard  
11. Evidence compiler (scan/guard/mcp/cost + opt-in memory/workspace)  
12. Identity signing for reports  
13. CI gates + GHA / ADO hooks  
14. PR create with evidence  
15. Local portal API  
16. Multi-runtime projections (Claude / Codex / Gemini)

**Related docs:** `docs/codebase/feature-catalog.md`, `ROADMAP.md`, `docs/agentops-platform.md`

---

## 9. Maturity scores (against full platform vision)

| Area | Score (0–10) | Comment |
| --- | --- | --- |
| AgentOps control plane (coding agents) | **8** | Deep, multi-module |
| Production readiness (repo) | **8** | Best commercial wedge |
| Evidence / audit trail | **8** | Strong differentiator |
| Policy enforcement (local) | **7** | Real enforce, not docs |
| FinOps | **4** | Token cost only |
| Discovery / inventory (enterprise) | **2** | Fleet ≠ AI inventory |
| Architecture intelligence | **2** | Context only |
| Trust Center (executive) | **2** | Local portal ≠ Trust Center |
| Niyam Graph / object platform | **1** | Objects in silos |
| Cross-cloud control plane | **1** | Hooks only |
| **Company platform thesis overall** | **~3.5** | Vertical depth high; platform breadth low |

This is a classic infrastructure pattern: **one sharp beachhead product**, then platform expansion.

---

## 10. Phase 1 gap backlog (Trust)

Map gaps to existing modules so work extends the product, not a greenfield rewrite.

### P0 — make “Trust platform” true beyond a single repo

| ID | Gap | Extend from | Outcome |
| --- | --- | --- | --- |
| T-01 | **AI Application** as root identity | config + fleet registry + evidence schema | System of record for “what AI exists” |
| T-02 | Inventory beyond Niyam workspaces | `fleet` + MCP/skills patterns | Register AI apps; aggregate across fleet |
| T-03 | Map readiness dims to commercial language | `governance/scoring.py` | Security / Cost / Governance / Privacy / Resilience / Monitoring views (or explicit mapping) |
| T-04 | Remediation as product path | scan findings + evidence `remediation_plan` | Actionable fix plan; later auto-PR |
| T-05 | Queryable Trust answers over local/fleet state | portal API + evidence + fleet status | “Unapproved MCP”, “no owner”, “highest cost agent” |

### P1 — Control foundation (after Trust)

| ID | Gap | Extend from |
| --- | --- | --- |
| C-01 | Org model / data policy mesh | `policy`, guard, cost model field |
| C-02 | FinOps attribution (app / team / model) | `cost`, `analytics` |
| C-03 | Architecture export for inventoried apps | `context`, stack detector |
| C-04 | Executive dashboard | `portal`, SaaS client |

### P2 — Execution / Autonomy (later)

| ID | Gap | Extend from |
| --- | --- | --- |
| E-01 | Universal agent registry | MCP/skills registry + swarm |
| E-02 | Safe action framework (non-coding agents) | guard + workspace approvals |
| E-03 | Cloud / ITSM / IdP connectors | new; keep PR/CI as delivery only |
| E-04 | Relationship graph + incident learning | memory lineage + policy exceptions |

### Phase 1 non-goals (do not boil the ocean)

- Multi-cloud AI asset discovery across AWS/Azure/GCP  
- Enterprise AI digital twin  
- Outcome-based ROI FinOps  
- Replacing Vanta / Datadog / Wiz / ServiceNow  
- Generic agent marketplace  

---

## 11. Strategic validation checklist

| Claim | Validated? |
| --- | --- |
| Niyam is already multi-module (company-shaped product surface) | **Yes** |
| Best current product = Production Readiness + Evidence | **Yes** |
| “AI Governance Platform” undersells / boxes the brand | **Yes** — code is execution + evidence, not only GRC |
| Ready to claim control tower for all enterprise AI | **No** — inventory + graph + connectors missing |
| Phase 1 should stay Trust (inventory / readiness / evidence) | **Yes** |
| Agent Runtime is purely future | **Partially wrong** — coding-agent runtime is Built; general agent runtime is future |
| FinOps is a large opportunity | **Yes** — current product is token accounting only |

---

## 12. Recommended near-term narrative

**External (website / README hero):**

> Niyam is the production trust layer for AI coding agents and AI-assisted development — readiness scoring, policy enforcement, supervised execution, and audit evidence.

**Internal (company doctrine):**

> Niyam the company builds the Trust & Execution Platform for Enterprise AI. The open-source AgentOps control plane is the beachhead. Phase 1 adds AI Application identity, inventory, and Trust queries on top of readiness + evidence.

**Commercial hero SKU (Phase 1):**

> **Niyam Production Readiness** — score AI systems, block unsafe promotion, produce evidence packs.

---

## 13. Related documents

| Doc | Role |
| --- | --- |
| `ROADMAP.md` | Phased AgentOps roadmap (Phases A–H) |
| `docs/agentops-platform.md` | Control plane concepts |
| `docs/codebase/feature-catalog.md` | Feature → CLI → code map |
| `docs/governance/` | Original governance PRD / architecture |
| `ORCHESTRATION_REVIEW.md` | Multi-agent orchestration gaps |
| `README.md` | Public product positioning |

---

## 14. How to refresh this matrix

When capabilities change:

1. Re-scan CLI: `python -m niyam --help` and major subgroups.  
2. Diff against sections 3–6 of this file.  
3. Update status cells only; keep thesis sections stable unless strategy changes.  
4. Bump **Status date** and **Codebase version** at the top.

Validation commands (local):

```bash
python -m niyam --help
python -m niyam scan --help
python -m niyam evidence --help
python -m niyam fleet --help
python -m niyam cost --help
pytest   # full suite when environment has test deps
```

---

*Generated from codebase audit 2026-07-14. Treat as strategy/product truth for planning; not a marketing claim sheet.*
