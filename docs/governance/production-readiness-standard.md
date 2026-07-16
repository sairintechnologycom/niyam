# Niyam Production-Grade Readiness Standard

Niyam is production-ready only when it passes every mandatory gate below. Feature
completion, a successful demo, or a model completion claim are not sufficient.

## Decision rule

Niyam must not be rated production-grade while any critical policy bypass,
sandbox escape, raw-secret exposure, cross-tenant leak, or accepted false
completion remains unresolved—regardless of its numerical score.

## 1. Functional harness correctness

The governed lifecycle must be repeatable:

```text
Task received → contract validated → plan generated → tools authorized
→ actions executed → evidence captured → completion evaluated
→ completed, failed, escalated, cancelled, or waiting for approval
```

| Metric | Exit criterion |
| --- | ---: |
| Deterministic E2E pass rate | 100% |
| Invalid state transitions | 0 |
| Accepted false completions | 0 |
| Unbounded execution loops | 0 |
| Missing required terminal states | 0 |

All 15 scenarios in the [harness E2E tracker](harness-e2e-validation-tracker.md)
must be covered and passing. `COMPLETED` requires independent evaluation.

## 2. Real execution isolation

Every side-effecting run must execute in this minimum boundary:

```text
Ephemeral Git worktree → rootless container → read-only base filesystem
→ allowlisted writable workspace → network denied by default
→ resource limits → artifact extraction → sandbox destruction
```

The sandbox must not mount host home directories, Docker sockets, unrestricted
`/var/run`, or inherited cloud/Git credentials. It must drop capabilities,
enforce syscall restrictions or equivalent controls, set CPU/memory/process/
time/output limits, and verify cleanup.

| Test | Required result |
| --- | --- |
| Read `~/.ssh/id_rsa`, `/etc/shadow`, or a host project | Blocked |
| Access cloud metadata or external network without approval | Blocked |
| Run privileged process or retain a process after teardown | Blocked/impossible |
| Read inherited cloud credentials | No credentials available |

One host escape or credential exposure blocks release.

## 3. Independent completion enforcement

```text
Model claim → contract evaluator → deterministic checks → policy evaluation
→ evidence verification → required approval → COMPLETED
```

Completion requires task criteria, expected commands and exit codes, passing
tests, valid scope/diff, passing security policy, valid approvals, valid
evidence hashes, no blocking findings, and budget compliance. A passing test
suite cannot override a failed scope, security, approval, or evidence check.

The suite must prove rejection of: completion without tests, modified tests,
failed scans, missing evidence, expired approvals, and approvals from another
run.

## 4. Recovery and resumability

Each checkpoint must bind the run ID, task-contract hash, policy and skill
versions, plan version/active step, repository fingerprint/base commit/diff
hash, iteration/tool/cost budgets, pinned-context hash, and pending approvals
and retries.

Resume must validate checkpoint integrity, task contract, compatible repository
state, current policy, approval validity, tool compatibility, and workspace
reconstruction before executing anything.

| Metric | Exit criterion |
| --- | ---: |
| Successful deterministic resume | 100% |
| Lost approved action state | 0 |
| Duplicate side effects | 0 |
| Resume against wrong repository state | 0 |
| Unbounded retries | 0 |

Test process/container/provider/tool/database failure, delayed approvals,
machine restart, repository change, and policy change before resume.

## 5. Evidence integrity and auditability

Each run must retain a versioned evidence pack under `.niyam/runs/<run-id>/`:

```text
manifest.json, task-contract.yaml, resolved policy/skills, execution plan,
checkpoints, events/tool-calls, approvals, repository fingerprint, changed-files,
diff, test/security/evaluator results, cost and memory decisions, provenance,
and final report.
```

Every artifact needs SHA-256, size, timestamp, producer identity, run ID,
sequence number, and schema version. The manifest hashes all artifacts and is
digitally signed where configured.

`niyam evidence verify <run-id>` must reject missing, modified, reordered,
wrong-run, mismatched, or unsupported evidence; it must validate event order,
approval/action binding, test claims, changed files, hashes, and signatures.

## 6. Security hardening

Source files, READMEs, issues, web/package metadata, tool/test output, MCP
servers, memory, and other agents are untrusted input. They cannot change
policy, grant capabilities, or become persisted facts without validation.

Required controls:

- prompt-injection detection and data/instruction separation;
- secret redaction before prompts, logs, and evidence persistence;
- scoped short-lived credentials, never inherited by sandboxes;
- schema-validated tools, canonical paths, symlink-escape prevention, safe
  command parsing, SSRF protection, and output/time limits;
- locked dependencies, SBOMs, vulnerability scans, signed artifacts, release
  provenance, and verified sandbox images.

Zero critical findings are allowed in injection, secret exfiltration, sandbox
escape, traversal/symlink escape, SSRF, command injection, evidence tampering,
and dependency integrity suites.

## 7. Operational reliability and observability

Production control-plane capabilities require durable run storage, idempotent
transitions, locks, concurrency/backpressure limits, retries and dead-letter
handling, cancellation, graceful shutdown, health/readiness checks, migration,
backup/restore, and retention.

Side-effecting tools use the idempotency key:

```text
run-id + plan-step-id + tool-call-sequence
```

Instrument OpenTelemetry-compatible traces, metrics, and structured logs. Each
event includes run/trace/span/workspace/agent/tool/plan-step identifiers,
policy decision, risk, and duration; raw sensitive prompts and output are not
logged by default.

| SLI | Initial target |
| --- | ---: |
| Control-plane availability | 99.9% |
| Checkpoint/evidence write success | 99.99% |
| Sandbox creation success | >=99.5% |
| Resume success | >=99% |
| Duplicate side effects / critical bypass / accepted false completion | 0 |

Track verified completion, denials, approval latency, sandbox/provider failure,
checkpoint recovery, tool latency, cost per verified run, evidence failures,
loops, and memory precision.

## 8. Multi-tenant, compatibility, and provider controls

Service deployments require tenant-scoped data, memory, policies, budgets,
limits, workspaces, tool registries, evidence access, encryption where
practical, and retention/deletion. Tenant A must never retrieve, resume, or
read artifacts or credentials belonging to Tenant B.

Version and migrate TaskContract, skills, policies, tools, scenarios, events,
checkpoints, evidence manifests, provider adapters, and memory objects. A
supported old checkpoint must resume after upgrade; old evidence must remain
verifiable; unsupported versions must fail clearly without corruption.

Every provider adapter must prove normalized tool calls, usage/cost capture,
timeouts, cancellation, malformed-response handling, structured-output
validation, parallel tool policy checks, checkpoint compatibility, and
redaction. Provider fallback must preserve state and never broaden context.

## Approval and memory lifecycle

Approvals are `REQUESTED → PENDING → APPROVED/DENIED/EXPIRED/CANCELLED →
CONSUMED`. They are exact-action/resource scoped, single-use, expiring,
identity- and run-bound, policy-version-bound, auditable, and subject to
separation of duties. Broader, expired, reused, cross-run, cross-tenant, or
self-approved-when-prohibited actions must be rejected.

Memory flows through candidate, classification, source validation, sensitivity
scan, deduplication, approval/rejection, storage, retrieval, revalidation, and
expiry/amendment. The first production release defaults to:

```yaml
memory:
  automaticPersistence: proposed_only
```

Arbitrary model claims, cross-scope entries, expired memories, repository-text
policies, and unapproved sensitive data are production blockers.

## Performance, release, and operational readiness

Capacity validation must cover 10 concurrent read-only and 50 concurrent
sandboxed runs, high tool-output volume, approval waits, throttling, storage
latency, database failover, checkpoint bursts, mass cancellation, large
repositories, and compression pressure. Publish capacity, overload rejection,
backpressure, latency, resource, and recovery evidence for the target
deployment.

Releases require reproducible and signed builds, SBOM, vulnerability scan,
provenance, protected branch/review gates, migration dry run, canary rollout,
rollback package, and versioned notes. Active runs stay pinned to their starting
policy/skill/tool/provider versions unless explicitly migrated.

Required documents and rehearsed runbooks include architecture/threat and data
flows, trust boundaries, deployment/configuration, backup/restore, incident and
disaster recovery, key/secrets handling, upgrades/rollbacks, retention,
support, provider outage, sandbox exhaustion, checkpoint/evidence failures,
secret or escape incidents, stuck runs, memory leakage, and policy errors.

## Staged validation

| Stage | Promotion condition |
| --- | --- |
| Deterministic qualification | All deterministic suites pass; no critical bypass; evidence and recovery verified. |
| Controlled internal dogfooding | At least 100 restricted internal runs across repository/task types; manual evidence review; no critical violation. |
| Limited external pilot | At least 500 governed non-production runs with explicit approvals, limits, monitoring, and incident rehearsal; >=95% evidence completeness; no isolation failure or unauthorized side effect. |

## Scorecard

| Domain | Weight | Current state |
| --- | ---: | --- |
| Harness correctness | 15% | Partial |
| Sandbox isolation | 15% | Not proven |
| Policy enforcement | 15% | Partial |
| Completion evaluation | 10% | Early |
| Recovery | 10% | Not proven |
| Evidence integrity | 10% | Partial |
| Security hardening | 10% | Not proven |
| Operational reliability | 5% | Early |
| Observability | 5% | Partial |
| Deployment and support | 5% | Early |

| Score | Classification |
| --- | --- |
| 0–39 | Prototype |
| 40–59 | Internal alpha |
| 60–74 | Controlled beta |
| 75–89 | Limited production |
| 90–100 | Production-grade |

## Production definition of done

```yaml
productionReadiness:
  deterministicValidation:
    e2ePassRate: 1.0
    providerConformancePassRate: 1.0
    falseCompletionsAccepted: 0
    criticalPolicyBypasses: 0
  sandbox:
    hostIsolationProven: true
    networkDefaultDeny: true
    credentialsNotInherited: true
    resourceLimitsProven: true
    cleanupVerified: true
  evaluation:
    independentCompletionCheck: true
    scopeValidationMandatory: true
    securityValidationMandatory: true
    evidenceValidationMandatory: true
  recovery:
    checkpointResumeProven: true
    duplicateSideEffects: 0
    retryLimitsEnforced: true
    incompatibleResumeBlocked: true
  evidence:
    mandatoryArtifactsPresent: true
    hashesVerified: true
    tamperDetectionProven: true
    evidenceVerificationCommandAvailable: true
  security:
    secretExposureCount: 0
    sandboxEscapeCount: 0
    promptInjectionBypassCount: 0
    pathEscapeCount: 0
    crossTenantLeakCount: 0
  operations:
    observabilityEnabled: true
    alertsConfigured: true
    incidentRunbooksComplete: true
    backupRestoreTested: true
    rollbackTested: true
  release:
    signedArtifacts: true
    sbomPublished: true
    vulnerabilitiesWithinPolicy: true
    stagedRolloutComplete: true
  validation:
    internalRunsCompleted: 100
    pilotRunsCompleted: 500
    unresolvedCriticalIncidents: 0
```

## Priority and current classification

**P0 before autonomous pilot:** real sandbox, default-deny tool registry,
independent completion evaluation, scope/diff enforcement, redaction, immutable
evidence manifest, checkpoint/resume, 15 deterministic E2E scenarios,
adversarial suite, and release-blocking CI.

**P1 before limited production:** durable control plane, OpenTelemetry,
provider conformance, approval lifecycle, idempotency, load/failure tests,
backup/restore, upgrade/rollback validation, signed release/SBOM, and runbooks.

**P2 before enterprise positioning:** tenant isolation, separation of duties,
enterprise identity and retention, signed evidence/audit export, DR validation,
and support SLAs.

Niyam is currently a **harness prototype / early internal alpha**. Its next
promotion target is **Controlled Harness Alpha**: all 15 deterministic E2E
scenarios passing, real sandbox isolation, independent evaluator,
checkpoint/resume, verified evidence, and zero critical security bypasses.
