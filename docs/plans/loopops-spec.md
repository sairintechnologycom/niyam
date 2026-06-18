# Niyam LoopOps / Loop Engineering Framework
Governed feedback loops for AI agents, coding assistants, MCP tools, and autonomous workflows.

## 1. What Loop Engineering Means Inside Niyam

In Niyam terms:

> **Loop Engineering is the discipline of defining, running, observing, evaluating, and governing AI agent feedback loops.**

A loop is not just:

```text
Prompt → Response
```

It becomes:

```text
Goal → Plan → Execute → Observe → Evaluate → Correct → Evidence → Policy Decision → Repeat / Stop
```

For enterprise use, Niyam should make every loop:

| Loop Attribute       | Niyam Responsibility                                       |
| -------------------- | ---------------------------------------------------------- |
| **Observable**       | Capture every step, tool call, prompt, output, error, cost |
| **Governed**         | Apply policies before and after each action                |
| **Bounded**          | Stop runaway loops, excessive cost, repeated failures      |
| **Evidence-backed**  | Store proof of what happened and why                       |
| **Auditable**        | Generate trace, decision log, compliance report            |
| **Measurable**       | Track loop quality, success rate, retries, drift           |
| **Human-controlled** | Require approval at risk thresholds                        |

This is extremely relevant because recent agent research and production patterns are increasingly built around iterative feedback loops rather than static prompting. For example, agent-in-the-loop customer support research shows how operational feedback signals can improve retrieval, generation quality, and adoption, while other recent work shows feedback loops improving scientific discovery agents when feedback is structured and meaningful.

---

## 2. Where It Fits in Current Niyam Architecture

Niyam already has the right foundation:

```text
Niyam Core
├── scan
├── readiness
├── rule engine
├── evidence
├── guard observe
├── guard policy
├── MCP registry
├── cost tracking
└── reports
```

Add:

```text
Niyam Core
└── loopops
    ├── loop spec
    ├── loop runner
    ├── loop observer
    ├── loop evaluator
    ├── loop policy engine
    ├── loop evidence pack
    ├── loop replay
    └── loop scorecard
```

The key is: **LoopOps should reuse Niyam’s existing policy, evidence, scan, MCP registry, and cost modules**. Do not build a detached subsystem.

---

## 3. Core Capabilities to Add

### A. Loop Specification

Create a declarative file:

```yaml
apiVersion: niyam.dev/v1
kind: LoopSpec
metadata:
  name: codex-feature-implementation-loop
  owner: platform-engineering
  riskTier: medium

goal:
  type: code_change
  description: Implement a requested feature safely with validation

actors:
  planner: claude
  implementer: codex
  reviewer: gemini
  approver: human

steps:
  - name: understand
    action: inspect_repository
    requiredEvidence:
      - repo_tree
      - relevant_files

  - name: plan
    action: generate_implementation_plan
    maxAttempts: 2

  - name: implement
    action: modify_code
    policy:
      requireBranch: true
      blockSecrets: true
      maxFilesChanged: 20

  - name: validate
    action: run_tests
    requiredEvidence:
      - test_output
      - lint_output

  - name: review
    action: ai_review
    evaluator: gemini

  - name: decide
    action: policy_decision
    gates:
      - no_critical_vulnerabilities
      - tests_passed
      - cost_under_budget
      - no_secret_leakage

budgets:
  maxIterations: 5
  maxTokens: 150000
  maxCostUsd: 3.00
  maxRuntimeMinutes: 30

stopConditions:
  - repeatedFailureCount >= 3
  - sameErrorRepeated >= 2
  - policyViolation == critical
  - humanApprovalRequired == true
```

This becomes the “contract” for how an agentic task is allowed to run.

---

### B. Loop Runner

New CLI:

```bash
niyam loop run loops/codex-feature-loop.yaml
```

Expected output:

```text
Niyam LoopOps

Loop: codex-feature-implementation-loop
Status: STOPPED_FOR_APPROVAL
Iterations: 3/5
Cost: $1.42 / $3.00
Risk: Medium → High
Reason: Modified authentication middleware

Evidence Pack:
./.niyam/evidence/loops/codex-feature-implementation-loop/2026-06-17/
```

---

### C. Loop Observer

Capture each iteration:

```json
{
  "loop_id": "codex-feature-implementation-loop",
  "iteration": 2,
  "actor": "codex",
  "step": "implement",
  "input_hash": "sha256:...",
  "output_hash": "sha256:...",
  "tools_used": ["filesystem", "test_runner"],
  "files_changed": [
    "src/auth/middleware.ts",
    "tests/auth.middleware.test.ts"
  ],
  "tokens": {
    "input": 18420,
    "output": 6220
  },
  "cost_usd": 0.42,
  "duration_ms": 81234,
  "policy_result": "warn",
  "risk_flags": [
    "auth_sensitive_file_changed"
  ]
}
```

This is where Niyam becomes very powerful: it can show not only what the agent produced, but **how the agent got there**.

---

### D. Loop Evaluator

Add evaluators for:

| Evaluator                  | Purpose                                                |
| -------------------------- | ------------------------------------------------------ |
| **Correctness evaluator**  | Did the task pass tests and acceptance criteria?       |
| **Security evaluator**     | Did the agent touch secrets, auth, infra, permissions? |
| **Cost evaluator**         | Did the loop exceed budget or token thresholds?        |
| **Drift evaluator**        | Is the agent moving away from the original goal?       |
| **Repetition evaluator**   | Is it stuck repeating the same fix?                    |
| **Evidence evaluator**     | Is enough proof captured?                              |
| **Human-review evaluator** | Should this stop for approval?                         |

This is especially important because loop systems can improve, but they can also compound mistakes if the feedback signal is weak or wrong.

---

### E. Loop Policy Engine

Example rules:

```yaml
rules:
  - id: loop.max_iterations
    severity: high
    condition: loop.iterations > 5
    action: stop

  - id: loop.repeated_error
    severity: medium
    condition: same_error_count >= 2
    action: require_human_review

  - id: loop.auth_file_modified
    severity: high
    condition: files.changed matches "src/auth/**"
    action: require_human_approval

  - id: loop.cost_exceeded
    severity: high
    condition: loop.cost_usd > budget.maxCostUsd
    action: stop

  - id: loop.no_tests_run
    severity: high
    condition: step.name == "validate" and evidence.test_output missing
    action: fail
```

This aligns directly with Niyam’s governance DNA.

---

## 4. Suggested CLI Commands

```bash
# Create a starter loop spec
niyam loop init --type code-change --name codex-feature-loop

# Validate loop definition
niyam loop validate loops/codex-feature-loop.yaml

# Run a loop
niyam loop run loops/codex-feature-loop.yaml

# Show current loop status
niyam loop status <loop-id>

# Replay loop from evidence
niyam loop replay <loop-id>

# Generate loop report
niyam loop report <loop-id> --format html

# Score a loop
niyam loop score <loop-id>

# List risky loops
niyam loop list --risk high

# Export evidence
niyam loop evidence <loop-id> --bundle
```

---

## 5. Loop Scorecard

Every loop should get a score:

```text
Loop Score: 78 / 100

Correctness:       24 / 30
Security:          16 / 20
Cost Control:      12 / 15
Evidence Quality:  13 / 15
Human Oversight:    8 / 10
Efficiency:         5 / 10
```

Decision:

```text
Result: CONDITIONAL_PASS
Reason: Tests passed, but authentication files changed. Human review required.
```

This becomes useful for enterprise approval, audit, and engineering governance.

---

## 6. Best Initial Use Cases for Niyam

1. **Codex Implementation Loop**
   ```text
   Claude plans → Codex implements → Gemini reviews → Niyam validates → Human approves
   ```
   Niyam controls: Scope, Files changed, Test evidence, Security risk, Cost, Retries, Final approval.

2. **AI App Readiness Remediation Loop**
   ```text
   Scan app → find gaps → propose fixes → implement → rescan → generate evidence
   ```
   This turns Niyam from a scanner into a **self-improving readiness engine**.

3. **MCP Tool Governance Loop**
   ```text
   Register MCP tool → inspect permissions → run safe test → observe behavior → approve/block
   ```

4. **FinOps Loop**
   ```text
   Detect token/cost anomaly → identify agent/prompt/tool → recommend fix → validate savings
   ```

5. **Policy Tuning Loop**
   ```text
   Policy violation → classify false positive/real risk → adjust rule → rerun evidence
   ```

---

## 7. Proposed Architecture

```text
┌──────────────────────────────────────────────────────────────┐
│                         Niyam CLI                             │
│ scan | guard | evidence | mcp | cost | loop                   │
└──────────────────────────────┬───────────────────────────────┘
                               │
┌──────────────────────────────▼───────────────────────────────┐
│                      LoopOps Engine                           │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────┐ │
│  │ Loop Spec    │  │ Loop Runner  │  │ Loop State Machine  │ │
│  └──────────────┘  └──────────────┘  └─────────────────────┘ │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────┐ │
│  │ Observer     │  │ Evaluator    │  │ Policy Decision     │ │
│  └──────────────┘  └──────────────┘  └─────────────────────┘ │
└──────────────────────────────┬───────────────────────────────┘
                               │
┌──────────────────────────────▼───────────────────────────────┐
│                    Existing Niyam Services                    │
│                                                              │
│  Rule Engine | Evidence Store | Cost Tracker | MCP Registry   │
│  Readiness Scanner | Guard Observe | Guard Policy | Reports   │
└──────────────────────────────┬───────────────────────────────┘
                               │
┌──────────────────────────────▼───────────────────────────────┐
│                    Agent / Tool Execution Layer               │
│                                                              │
│  Claude | Codex | Gemini | MCP Tools | Test Runner | GitHub   │
└──────────────────────────────────────────────────────────────┘
```

---

## 8. Data Model

Add these entities:
- LoopSpec
- LoopRun
- LoopIteration
- LoopStep
- LoopObservation
- LoopEvaluation
- LoopPolicyDecision
- LoopEvidenceArtifact
- LoopScore
- LoopBudget
- LoopRiskFlag

Minimal TypeScript model:

```ts
export type LoopRunStatus =
  | "pending"
  | "running"
  | "passed"
  | "failed"
  | "stopped"
  | "requires_approval";

export interface LoopRun {
  id: string;
  specName: string;
  goal: string;
  status: LoopRunStatus;
  startedAt: string;
  completedAt?: string;
  iterationCount: number;
  maxIterations: number;
  costUsd: number;
  maxCostUsd?: number;
  riskLevel: "low" | "medium" | "high" | "critical";
  evidencePath: string;
}

export interface LoopIteration {
  id: string;
  loopRunId: string;
  index: number;
  actor: string;
  stepName: string;
  action: string;
  startedAt: string;
  completedAt?: string;
  inputHash?: string;
  outputHash?: string;
  tokensIn?: number;
  tokensOut?: number;
  costUsd?: number;
  result: "success" | "failure" | "warning" | "blocked";
  observations: LoopObservation[];
  policyDecisions: LoopPolicyDecision[];
}
```

---

## 9. Phased Implementation Plan

### Phase 1 — LoopSpec + Validation
- **Goal:** Add declarative loop definitions.
- **Deliverables:**
  - `src/loopops/schema.ts`
  - `src/loopops/validate.ts`
  - `src/commands/loop.ts`
  - `fixtures/loops/basic-code-change.yaml`
  - `tests/loopops/schema.test.ts`
- **CLI:** `niyam loop validate fixtures/loops/basic-code-change.yaml`
- **Acceptance:** Valid LoopSpec passes, missing budgets fail, invalid stop conditions fail, invalid actor names fail.

### Phase 2 — LoopRun State Machine
- **Goal:** Add controlled execution lifecycle.
- **States:** `pending → running → evaluating → passed/failed/requires_approval/stopped`
- **Deliverables:**
  - `src/loopops/state-machine.ts`
  - `src/loopops/runner.ts`
  - `tests/loopops/state-machine.test.ts`
- **Acceptance:** Max iteration stop works, repeated failure stop works, approval gate works.

### Phase 3 — Evidence Capture
- **Goal:** Store loop evidence in Niyam evidence format.
- **Folder structure:**
  ```text
  .niyam/evidence/loops/<loop-id>/
  ├── loop-spec.yaml
  ├── run.json
  ├── iterations/
  │   ├── 001.json
  │   ├── 002.json
  ├── artifacts/
  │   ├── test-output.txt
  │   ├── diff.patch
  │   └── policy-results.json
  └── report.md
  ```
- **Acceptance:** Every loop run creates evidence, every iteration creates trace, evidence bundle can be exported.

### Phase 4 — Policy Integration
- **Goal:** Reuse Niyam rule engine for loop governance.
- **Policies:** Cost exceeded, Sensitive file changed, No tests run, Repeated failure, High-risk MCP tool used, Missing evidence.
- **Acceptance:** Policy can warn, fail, stop, or request approval; Loop reports policy decisions clearly.

### Phase 5 — Cost + Token Tracking
- **Goal:** Add LoopOps FinOps.
- **Metrics:** Cost per loop, cost per iteration, tokens per actor, wasted retries, cost per successful outcome.
- **Acceptance:** Loop stops when budget exceeded, report shows token/cost breakdown, repeated failed loops flagged as waste.

### Phase 6 — AI Reviewer / Critic Loop
- **Goal:** Add evaluator abstraction.
- **Example:**
  ```yaml
  evaluators:
    - name: security-review
      type: ai_critic
      actor: gemini
      required: true
    - name: test-review
      type: command
      command: npm test
      required: true
  ```
- **Acceptance:** Evaluator results are stored, failed evaluator blocks loop, human approval required for high-risk result.

### Phase 7 — HTML Loop Report
- **Goal:** Generate Design-Council-grade report.
- **Sections:** Executive summary, Goal, Actors, Iterations, Evidence, Policy decisions, Cost, Risks, Approval status, Final recommendation.
- **CLI:** `niyam loop report <loop-id> --format html`

---

## 10. Codex Implementation Prompt

Use this prompt directly:

```text
You are a principal TypeScript/Python platform engineer working on the Niyam AI governance platform.

Objective:
Add a new Loop Engineering capability called LoopOps to Niyam. This capability must allow users to define, validate, run, observe, evaluate, and report on governed AI agent feedback loops.

Context:
Niyam already has or will have these capabilities:
- CLI command structure
- Readiness scanning
- Rule engine
- Evidence generation
- Guard observe
- Guard policy
- MCP/tool registry
- Cost tracking
- Reports

Do not create a disconnected subsystem. LoopOps must reuse existing Niyam patterns, folder structure, evidence conventions, rule engine conventions, and test style.

Build this incrementally.

Phase 1 scope:
1. Add LoopSpec schema.
2. Add LoopSpec validation.
3. Add CLI commands:
   - niyam loop init
   - niyam loop validate <file>
4. Add fixture loop specs.
5. Add unit tests.

LoopSpec requirements:
- metadata.name
- metadata.owner
- goal.type
- goal.description
- actors
- steps
- budgets.maxIterations
- stopConditions
- requiredEvidence where applicable

Validation must fail when:
- metadata.name is missing
- no steps are defined
- maxIterations is missing or less than 1
- a step references an unknown actor
- stop condition syntax is invalid
- required evidence is malformed

Create:
- src/loopops/schema.ts
- src/loopops/validate.ts
- src/loopops/init.ts
- src/commands/loop.ts
- fixtures/loops/basic-code-change.yaml
- fixtures/loops/invalid-missing-budget.yaml
- tests/loopops/schema.test.ts
- tests/loopops/validate.test.ts

CLI behavior:
- niyam loop init --name my-loop --type code-change
  should generate a starter YAML LoopSpec.
- niyam loop validate fixtures/loops/basic-code-change.yaml
  should print PASS with normalized summary.
- invalid specs should print FAIL with actionable validation errors.

Design constraints:
- Keep APIs typed.
- Keep implementation modular.
- Avoid hardcoding future agent providers.
- Do not execute external tools in Phase 1.
- Do not add network calls.
- Do not break existing tests.

Expected output:
- Working CLI commands
- Passing tests
- Example fixture files
- Clear error messages
- Minimal documentation update explaining LoopOps
```

---

## 11. Strategic View

This is worth adding because it makes Niyam more than an AI governance scanner.

It becomes:

```text
Niyam = Governance control plane for AI engineering loops
```

That positions Niyam around a serious enterprise problem:

> “How do we let AI agents work iteratively without losing control?”

That is a stronger wedge than generic AI app scanning.

### Final Recommendation

Add Loop Engineering as a first-class Niyam module:

```text
niyam loop
```

Start with:
1. **LoopSpec**
2. **Validation**
3. **Evidence capture**
4. **Policy gates**
5. **Cost controls**
6. **Loop scorecard**
7. **HTML reports**

This gives Niyam a differentiated enterprise story:

> **Niyam does not just check whether AI systems are ready. It governs how AI systems improve.**
