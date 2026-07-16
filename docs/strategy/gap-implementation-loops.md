# Enterprise Gap Implementation Loops

Each loop follows: **contract → failing acceptance test → minimum implementation → full validation → evidence**. A loop ships independently and does not start until its dependency is green.

| Loop | Deliverable | Depends on | Acceptance gate |
| --- | --- | --- | --- |
| 1 | First-class AI Application registry | — | Register, update, list, show, and persist stable application IDs |
| 2 | Local relationship graph | 1 | Link applications to repos, tools, models, prompts, and data assets; query direct relationships |
| 3 | Application attribution | 2 | Cost, evidence, fleet, missions, MCP tools, and skills accept an optional `application_id` without breaking old records |
| 4 | Architecture inventory | 2 | Extract local services, external calls, identity boundaries, storage, and data flows with source locations |
| 5 | Source-control discovery | 1 | Read-only GitHub/GitLab/ADO adapters normalize repositories and detected AI applications into the registry |
| 6 | Runtime and cloud discovery | 2, 5 | Read-only AWS/Azure/GCP/Kubernetes adapters normalize models, agents, endpoints, and ownership |
| 7 | Model, prompt, and data inventory | 2 | Versioned model, prompt, dataset, vector-store, and knowledge-base objects participate in graph queries |
| 8 | Cross-application policy mesh | 3, 6, 7 | Policies target application/model/data attributes and fail closed before governed execution |
| 9 | Trust Center query API | 3, 4, 8 | Answer deterministic ownership, data-use, model-use, risk, cost, and evidence questions from the graph |
| 10 | Business FinOps and SIEM export | 3, 9 | Attribute spend/outcomes by application/team and export versioned security events |
| 11 | Closed improvement loop | 8, 10 | Incident or failed control proposes a policy/remediation, requires approval, applies safely, and records evidence |
| 12 | Multi-tenant enterprise delivery | 9–11 | Tenant isolation, SSO/RBAC, private deployment, and operational packaging pass security tests |

## Loop rules

- Keep schemas backward-compatible; new attribution fields are optional until migration is explicitly approved.
- Discovery connectors are read-only by default and store provenance plus collection time.
- No automated remediation writes without policy evaluation, human approval, rollback, and evidence.
- Loops 6 and 12 require human approval before infrastructure, production configuration, secrets, or authentication changes.
- One focused acceptance test per behavior; run the full suite before closing a loop.

## Current state

- Loops 1–8: implemented on 2026-07-14.
- Loops 9–12: planned, not started.
