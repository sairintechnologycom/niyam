You are the Niyam planning engine.
Convert the following requirement into a bounded, dependency-resolved task plan.
Each task must be small, bounded, and assigned to a specific agent from the available agents in the workspace.

Available Agents in this workspace:
security-reviewer, frontend-specialist, backend-specialist, qa-reviewer

Repository Structure (File Map):
.claude/agents/backend-specialist.md
.claude/agents/frontend-specialist.md
.claude/agents/qa-reviewer.md
.claude/agents/security-reviewer.md
.claude/commands/context-refresh.md
.claude/commands/implement.md
.claude/commands/review.md
.claude/commands/ship.md
.claude/commands/niyam-ci-verify.md
.claude/commands/niyam-compare.md
.claude/commands/niyam-context-diff.md
.claude/commands/niyam-context-refresh.md
.claude/commands/niyam-context-show.md
.claude/commands/niyam-dashboard.md
.claude/commands/niyam-doctor.md
.claude/commands/niyam-guard-careful.md
.claude/commands/niyam-guard-disable.md
.claude/commands/niyam-guard-enable.md
.claude/commands/niyam-guard-freeze.md
.claude/commands/niyam-hello.md
.claude/commands/niyam-init.md
.claude/commands/niyam-memory-add.md
.claude/commands/niyam-memory-clear.md
.claude/commands/niyam-memory-show.md
.claude/commands/niyam-mission-active.md
.claude/commands/niyam-mission-approve.md
.claude/commands/niyam-mission-dashboard.md
.claude/commands/niyam-mission-pause.md
.claude/commands/niyam-mission-plan.md
.claude/commands/niyam-mission-report.md
.claude/commands/niyam-mission-resume.md
.claude/commands/niyam-mission-retry.md
.claude/commands/niyam-mission-rollback.md
.claude/commands/niyam-mission-show.md
.claude/commands/niyam-mission-skip.md
.claude/commands/niyam-mission-start.md
.claude/commands/niyam-mission-status.md
.claude/commands/niyam-mission-validate-plan.md
.claude/commands/niyam-mission-verify-report.md
.claude/commands/niyam-pack-add.md
.claude/commands/niyam-pack-list.md
.claude/commands/niyam-pack-remove.md
.claude/commands/niyam-pack-sync.md
.claude/commands/niyam-plan.md
.claude/commands/niyam-policy-validate.md
.claude/commands/niyam-pr-create.md
.claude/commands/niyam-report.md
.claude/commands/niyam-review-pr.md
.claude/commands/niyam-run.md
.claude/commands/niyam-runtime-add.md
.claude/commands/niyam-setup.md
.claude/commands/niyam-sync.md
.claude/commands/niyam-version.md
.claude/commands/niyam-watch.md
.claude/hooks/pre_tool_guard.py
.claude/settings.json
.claude/skills/implement-task/SKILL.md
.claude/skills/implementation-planning/SKILL.md
.claude/skills/repo-context/SKILL.md
.claude/skills/secure-code-review/SKILL.md
.claude/skills/test-driven-development/SKILL.md
.github/workflows/publish.yml
.github/workflows/niyam-ci.yml
.gitignore
.planning/codebase/ARCHITECTURE.md
.planning/codebase/CONCERNS.md
.planning/codebase/CONVENTIONS.md
.planning/codebase/INTEGRATIONS.md
.planning/codebase/STACK.md
.planning/codebase/STRUCTURE.md
.planning/codebase/TESTING.md
.niyam/agents/backend-specialist.md
.niyam/agents/frontend-specialist.md
.niyam/agents/qa-reviewer.md
.niyam/agents/security-reviewer.md
.niyam/commands/context-refresh.md
.niyam/commands/implement.md
.niyam/commands/review.md
.niyam/commands/ship.md
.niyam/commands/niyam-ci-verify.md
.niyam/commands/niyam-compare.md
.niyam/commands/niyam-context-diff.md
.niyam/commands/niyam-context-refresh.md
.niyam/commands/niyam-context-show.md
.niyam/commands/niyam-dashboard.md
.niyam/commands/niyam-doctor.md
.niyam/commands/niyam-guard-careful.md
.niyam/commands/niyam-guard-disable.md
.niyam/commands/niyam-guard-enable.md
.niyam/commands/niyam-guard-freeze.md
.niyam/commands/niyam-hello.md
.niyam/commands/niyam-init.md
.niyam/commands/niyam-memory-add.md
.niyam/commands/niyam-memory-clear.md
.niyam/commands/niyam-memory-show.md
.niyam/commands/niyam-mission-active.md
.niyam/commands/niyam-mission-approve.md
.niyam/commands/niyam-mission-dashboard.md
.niyam/commands/niyam-mission-pause.md
.niyam/commands/niyam-mission-plan.md
.niyam/commands/niyam-mission-report.md
.niyam/commands/niyam-mission-resume.md
.niyam/commands/niyam-mission-retry.md
.niyam/commands/niyam-mission-rollback.md
.niyam/commands/niyam-mission-show.md
.niyam/commands/niyam-mission-skip.md
.niyam/commands/niyam-mission-start.md
.niyam/commands/niyam-mission-status.md
.niyam/commands/niyam-mission-validate-plan.md
.niyam/commands/niyam-mission-verify-report.md
.niyam/commands/niyam-pack-add.md
.niyam/commands/niyam-pack-list.md
.niyam/commands/niyam-pack-remove.md
.niyam/commands/niyam-pack-sync.md
.niyam/commands/niyam-plan.md
.niyam/commands/niyam-policy-validate.md
.niyam/commands/niyam-pr-create.md
.niyam/commands/niyam-report.md
.niyam/commands/niyam-review-pr.md
.niyam/commands/niyam-run.md
.niyam/commands/niyam-runtime-add.md
.niyam/commands/niyam-setup.md
.niyam/commands/niyam-sync.md
.niyam/commands/niyam-version.md
.niyam/commands/niyam-watch.md
.niyam/context/architecture.md
.niyam/context/commands.md
.niyam/context/project-memory.md
.niyam/context/validation.md
.niyam/memory/architecture-decisions.md
.niyam/memory/design-taste.md
.niyam/memory/project-lessons.md
.niyam/memory/recurring-pitfalls.md
.niyam/policies/approvals.yaml
.niyam/policies/commands.yaml
.niyam/policies/evidence.yaml
.niyam/policies/security.yaml
.niyam/skills/implementation-planning/SKILL.md
.niyam/skills/repo-context/SKILL.md
.niyam/skills/secure-code-review/SKILL.md
.niyam/skills/test-driven-development/SKILL.md
AGENTS.md
CLAUDE.md
GEMINI.md
LICENSE
README.md
RELEASE.md
ROADMAP.md
build_binary.py
change-T3.txt
change-T5.txt
docs/decisions.md
docs/progress.md
examples/REQ-001.md
install.sh
pyproject.toml
requirements/REQ-001.md
scratch/hello-requirement.md
scratch/requirements-utils.md
niyam/__init__.py
niyam/__main__.py
niyam/cli/__init__.py
niyam/cli/__main__.py
niyam/cli/ci.py
niyam/cli/context.py
niyam/cli/guard.py
niyam/cli/main_cmds.py
niyam/cli/memory.py
niyam/cli/mission.py
niyam/cli/pack.py
niyam/cli/policy.py
niyam/cli/pr.py
niyam/cli/review.py
niyam/cli/runtime.py
niyam/core/__init__.py
niyam/core/ci.py
niyam/core/compare.py
niyam/core/config.py
niyam/core/context.py
niyam/core/doctor.py
niyam/core/errors.py
niyam/core/init.py
niyam/core/memory.py
niyam/core/packs.py
niyam/core/pr.py
niyam/core/review.py
niyam/core/security.py
niyam/core/setup.py
niyam/core/sync.py
niyam/core/utils.py
niyam/evidence/__init__.py
niyam/evidence/reporter.py
niyam/mission/__init__.py
niyam/mission/dashboard.py
niyam/mission/executor.py
niyam/mission/planner.py
niyam/mission/reporter.py
niyam/mission/status.py
niyam/mission/validator.py
niyam/policies/__init__.py
niyam/policies/guard.py
niyam/policies/validator.py
niyam/runtimes/__init__.py
niyam/runtimes/base.py
niyam/runtimes/claude.py
niyam/runtimes/codex.py
niyam/runtimes/gemini.py
niyam/templates/packs/ab-testing-setup/agents/ab-testing-specialist.md
niyam/templates/packs/ab-testing-setup/pack.yaml
niyam/templates/packs/ab-testing-setup/skills/ab-testing/SKILL.md
niyam/templates/packs/agentic-engineering/agents/architect.md
niyam/templates/packs/agentic-engineering/commands/brief.md
niyam/templates/packs/agentic-engineering/commands/plan-review.md
niyam/templates/packs/agentic-engineering/pack.yaml
niyam/templates/packs/agentic-engineering/skills/brainstorming/SKILL.md
niyam/templates/packs/agentic-engineering/skills/executing-plans/SKILL.md
niyam/templates/packs/agentic-engineering/skills/verification-before-completion/SKILL.md
niyam/templates/packs/agentic-engineering/skills/writing-plans/SKILL.md
niyam/templates/packs/api-governance/agents/api-architect.md
niyam/templates/packs/api-governance/pack.yaml
niyam/templates/packs/api-governance/skills/api-design/SKILL.md
niyam/templates/packs/security-scanning/agents/security-auditor.md
niyam/templates/packs/security-scanning/pack.yaml
niyam/templates/packs/security-scanning/skills/vulnerability-scanning/SKILL.md
niyam/templates/packs/superpowers-methodology/commands/superpower.md
niyam/templates/packs/superpowers-methodology/pack.yaml
niyam/templates/packs/superpowers-methodology/skills/superpowers/SKILL.md
niyam/templates/packs/tdd-quality-gate/agents/tdd-executor.md
niyam/templates/packs/tdd-quality-gate/pack.yaml
niyam/templates/packs/tdd-quality-gate/skills/tdd-workflow/SKILL.md
niyam/templates/profiles/backend/agents/backend-specialist.md
niyam/templates/profiles/backend/agents/qa-reviewer.md
niyam/templates/profiles/backend/agents/security-reviewer.md
niyam/templates/profiles/backend/commands/context-refresh.md
niyam/templates/profiles/backend/commands/implement.md
niyam/templates/profiles/backend/commands/review.md
niyam/templates/profiles/backend/commands/ship.md
niyam/templates/profiles/backend/context/architecture.md
niyam/templates/profiles/backend/context/commands.md
niyam/templates/profiles/backend/context/project-memory.md
niyam/templates/profiles/backend/context/validation.md
niyam/templates/profiles/backend/memory/architecture-decisions.md
niyam/templates/profiles/backend/memory/design-taste.md
niyam/templates/profiles/backend/memory/project-lessons.md
niyam/templates/profiles/backend/memory/recurring-pitfalls.md
niyam/templates/profiles/backend/policies/approvals.yaml
niyam/templates/profiles/backend/policies/commands.yaml
niyam/templates/profiles/backend/policies/evidence.yaml
niyam/templates/profiles/backend/policies/security.yaml
niyam/templates/profiles/backend/project.yaml
niyam/templates/profiles/backend/runtimes.yaml
niyam/templates/profiles/backend/skills/implementation-planning/SKILL.md
niyam/templates/profiles/backend/skills/repo-context/SKILL.md
niyam/templates/profiles/backend/skills/secure-code-review/SKILL.md
niyam/templates/profiles/backend/skills/test-driven-development/SKILL.md
niyam/templates/profiles/frontend/agents/frontend-specialist.md
niyam/templates/profiles/frontend/agents/qa-reviewer.md
niyam/templates/profiles/frontend/commands/context-refresh.md
niyam/templates/profiles/frontend/commands/implement.md
niyam/templates/profiles/frontend/commands/review.md
niyam/templates/profiles/frontend/commands/ship.md
niyam/templates/profiles/frontend/context/architecture.md
niyam/templates/profiles/frontend/context/commands.md
niyam/templates/profiles/frontend/context/project-memory.md
niyam/templates/profiles/frontend/context/validation.md
niyam/templates/profiles/frontend/memory/architecture-decisions.md
niyam/templates/profiles/frontend/memory/design-taste.md
niyam/templates/profiles/frontend/memory/project-lessons.md
niyam/templates/profiles/frontend/memory/recurring-pitfalls.md
niyam/templates/profiles/frontend/policies/approvals.yaml
niyam/templates/profiles/frontend/policies/commands.yaml
niyam/templates/profiles/frontend/policies/evidence.yaml
niyam/templates/profiles/frontend/policies/security.yaml
niyam/templates/profiles/frontend/project.yaml
niyam/templates/profiles/frontend/runtimes.yaml
niyam/templates/profiles/frontend/skills/implementation-planning/SKILL.md
niyam/templates/profiles/frontend/skills/repo-context/SKILL.md
niyam/templates/profiles/frontend/skills/secure-code-review/SKILL.md
niyam/templates/profiles/frontend/skills/test-driven-development/SKILL.md
niyam/templates/profiles/fullstack/agents/backend-specialist.md
niyam/templates/profiles/fullstack/agents/frontend-specialist.md
niyam/templates/profiles/fullstack/agents/qa-reviewer.md
niyam/templates/profiles/fullstack/agents/security-reviewer.md
niyam/templates/profiles/fullstack/commands/context-refresh.md
niyam/templates/profiles/fullstack/commands/implement.md
niyam/templates/profiles/fullstack/commands/review.md
niyam/templates/profiles/fullstack/commands/ship.md
niyam/templates/profiles/fullstack/context/architecture.md
niyam/templates/profiles/fullstack/context/commands.md
niyam/templates/profiles/fullstack/context/project-memory.md
niyam/templates/profiles/fullstack/context/validation.md
niyam/templates/profiles/fullstack/memory/architecture-decisions.md
niyam/templates/profiles/fullstack/memory/design-taste.md
niyam/templates/profiles/fullstack/memory/project-lessons.md
niyam/templates/profiles/fullstack/memory/recurring-pitfalls.md
niyam/templates/profiles/fullstack/policies/approvals.yaml
niyam/templates/profiles/fullstack/policies/commands.yaml
niyam/templates/profiles/fullstack/policies/evidence.yaml
niyam/templates/profiles/fullstack/policies/security.yaml
niyam/templates/profiles/fullstack/project.yaml
niyam/templates/profiles/fullstack/runtimes.yaml
niyam/templates/profiles/fullstack/skills/implementation-planning/SKILL.md
niyam/templates/profiles/fullstack/skills/repo-context/SKILL.md
niyam/templates/profiles/fullstack/skills/secure-code-review/SKILL.md
niyam/templates/profiles/fullstack/skills/test-driven-development/SKILL.md
niyam/templates/profiles/governed-enterprise/agents/architect.md
niyam/templates/profiles/governed-enterprise/agents/documentation-engineer.md
niyam/templates/profiles/governed-enterprise/agents/engineering-manager.md
niyam/templates/profiles/governed-enterprise/agents/qa-reviewer.md
niyam/templates/profiles/governed-enterprise/agents/release-manager.md
niyam/templates/profiles/governed-enterprise/agents/security-reviewer.md
niyam/templates/profiles/governed-enterprise/commands/context-refresh.md
niyam/templates/profiles/governed-enterprise/commands/implement.md
niyam/templates/profiles/governed-enterprise/commands/review.md
niyam/templates/profiles/governed-enterprise/commands/ship.md
niyam/templates/profiles/governed-enterprise/context/architecture.md
niyam/templates/profiles/governed-enterprise/context/commands.md
niyam/templates/profiles/governed-enterprise/context/project-memory.md
niyam/templates/profiles/governed-enterprise/context/validation.md
niyam/templates/profiles/governed-enterprise/memory/architecture-decisions.md
niyam/templates/profiles/governed-enterprise/memory/design-taste.md
niyam/templates/profiles/governed-enterprise/memory/project-lessons.md
niyam/templates/profiles/governed-enterprise/memory/recurring-pitfalls.md
niyam/templates/profiles/governed-enterprise/policies/approvals.yaml
niyam/templates/profiles/governed-enterprise/policies/commands.yaml
niyam/templates/profiles/governed-enterprise/policies/evidence.yaml
niyam/templates/profiles/governed-enterprise/policies/security.yaml
niyam/templates/profiles/governed-enterprise/project.yaml
niyam/templates/profiles/governed-enterprise/runtimes.yaml
niyam/templates/profiles/governed-enterprise/skills/implementation-planning/SKILL.md
niyam/templates/profiles/governed-enterprise/skills/repo-context/SKILL.md
niyam/templates/profiles/governed-enterprise/skills/secure-code-review/SKILL.md
niyam/templates/profiles/governed-enterprise/skills/test-driven-development/SKILL.md
niyam/templates/profiles/platform-engineering/agents/architect.md
niyam/templates/profiles/platform-engineering/agents/backend-specialist.md
niyam/templates/profiles/platform-engineering/agents/devops-specialist.md
niyam/templates/profiles/platform-engineering/agents/documentation-engineer.md
niyam/templates/profiles/platform-engineering/agents/qa-reviewer.md
niyam/templates/profiles/platform-engineering/agents/security-reviewer.md
niyam/templates/profiles/platform-engineering/commands/context-refresh.md
niyam/templates/profiles/platform-engineering/commands/implement.md
niyam/templates/profiles/platform-engineering/commands/review.md
niyam/templates/profiles/platform-engineering/commands/ship.md
niyam/templates/profiles/platform-engineering/context/architecture.md
niyam/templates/profiles/platform-engineering/context/commands.md
niyam/templates/profiles/platform-engineering/context/project-memory.md
niyam/templates/profiles/platform-engineering/context/validation.md
niyam/templates/profiles/platform-engineering/memory/architecture-decisions.md
niyam/templates/profiles/platform-engineering/memory/design-taste.md
niyam/templates/profiles/platform-engineering/memory/project-lessons.md
niyam/templates/profiles/platform-engineering/memory/recurring-pitfalls.md
niyam/templates/profiles/platform-engineering/policies/approvals.yaml
niyam/templates/profiles/platform-engineering/policies/commands.yaml
niyam/templates/profiles/platform-engineering/policies/evidence.yaml
niyam/templates/profiles/platform-engineering/policies/security.yaml
niyam/templates/profiles/platform-engineering/project.yaml
niyam/templates/profiles/platform-engineering/runtimes.yaml
niyam/templates/profiles/platform-engineering/skills/implementation-planning/SKILL.md
niyam/templates/profiles/platform-engineering/skills/repo-context/SKILL.md
niyam/templates/profiles/platform-engineering/skills/secure-code-review/SKILL.md
niyam/templates/profiles/platform-engineering/skills/test-driven-development/SKILL.md
niyam/templates/profiles/startup-saas/agents/backend-specialist.md
niyam/templates/profiles/startup-saas/agents/designer.md
niyam/templates/profiles/startup-saas/agents/frontend-specialist.md
niyam/templates/profiles/startup-saas/agents/product-strategist.md
niyam/templates/profiles/startup-saas/agents/qa-reviewer.md
niyam/templates/profiles/startup-saas/agents/release-manager.md
niyam/templates/profiles/startup-saas/commands/context-refresh.md
niyam/templates/profiles/startup-saas/commands/implement.md
niyam/templates/profiles/startup-saas/commands/review.md
niyam/templates/profiles/startup-saas/commands/ship.md
niyam/templates/profiles/startup-saas/context/architecture.md
niyam/templates/profiles/startup-saas/context/commands.md
niyam/templates/profiles/startup-saas/context/project-memory.md
niyam/templates/profiles/startup-saas/context/validation.md
niyam/templates/profiles/startup-saas/memory/architecture-decisions.md
niyam/templates/profiles/startup-saas/memory/design-taste.md
niyam/templates/profiles/startup-saas/memory/project-lessons.md
niyam/templates/profiles/startup-saas/memory/recurring-pitfalls.md
niyam/templates/profiles/startup-saas/policies/approvals.yaml
niyam/templates/profiles/startup-saas/policies/commands.yaml
niyam/templates/profiles/startup-saas/policies/evidence.yaml
niyam/templates/profiles/startup-saas/policies/security.yaml
niyam/templates/profiles/startup-saas/project.yaml
niyam/templates/profiles/startup-saas/runtimes.yaml
niyam/templates/profiles/startup-saas/skills/implementation-planning/SKILL.md
niyam/templates/profiles/startup-saas/skills/repo-context/SKILL.md
niyam/templates/profiles/startup-saas/skills/secure-code-review/SKILL.md
niyam/templates/profiles/startup-saas/skills/test-driven-development/SKILL.md
niyam/templates/reviews/design.md
niyam/templates/reviews/engineering.md
niyam/templates/reviews/product.md
niyam/templates/reviews/security.md
task-T1-prompt.md
task-T2-prompt.md
task-T3-prompt.md
task-T4-prompt.md
task-T5-prompt.md
tests/change-T2.txt
tests/conftest.py
tests/test_ci.py
tests/test_cli.py
tests/test_cli_refinement.py
tests/test_compare.py
tests/test_context.py
tests/test_contract_enforcement.py
tests/test_dashboard.py
tests/test_doctor.py
tests/test_doctor_check.py
tests/test_doctor_enhanced.py
tests/test_fleet.py
tests/test_guard.py
tests/test_guardrails.py
tests/test_hello.py
tests/test_hooks.py
tests/test_init.py
tests/test_memory.py
tests/test_mission.py
tests/test_multi_runtime.py
tests/test_packs.py
tests/test_planner_robust.py
tests/test_pr.py
tests/test_recovery.py
tests/test_remediation.py
tests/test_review.py
tests/test_run_composite.py
tests/test_setup.py
tests/test_sync.py
tests/test_template_boilerplating.py
tests/test_templates.py
tests/test_token_parsing.py
tests/test_utils.py
tests/test_verification.py
uv.lock

Requirement to implement:
# Requirement: Add Niyam Info Command

## Goal
Add a new top-level command `niyam info` that displays basic information about the system and the current Niyam workspace.

## Expected Outcome
- A new command `niyam info` is available in the CLI.
- The command prints:
    - OS type
    - Python version
    - Niyam version
    - Whether the current directory is a Niyam workspace.
- Unit tests for the new command are added.

## Constraints
- Use `typer` for the new command implementation in `niyam/cli/main_cmds.py`.
- Use `rich` for formatting the output.
- Follow existing coding style and conventions.

## Validation
- `niyam info` runs without errors.
- New tests pass using `pytest`.


Instructions:
1. Break down the requirement into a list of tasks.
2. The tasks must be ordered logically. Any task depending on another task must list it in `depends_on`.
3. Assign each task to the most appropriate agent from the list of Available Agents. For example, assign development to 'backend-specialist' or 'frontend-specialist', code review to 'security-reviewer', and verification/testing to 'qa-reviewer'.
4. Optionally, you can assign a custom execution `runtime` (such as `claude`, `gemini`, or `codex`) to a task if a specific runtime is better suited for it (e.g. `gemini` for coding, `codex` for scripting). If omitted, the task will use the default global runtime.
5. Ensure the first task is a discovery/analysis task, and the last task is a validation task.
6. Return ONLY a valid YAML or JSON block matching the schema below. Do not output any markdown prose, chat, warnings, or explanation. Only output the content inside ```yaml or ```json code fences.

Schema (YAML format):
```yaml
tasks:
  - id: T1
    title: "Discovery: analyze requirements and code structure"
    type: "discovery"
    agent: "security-reviewer"
    writes_files: false
  - id: T2
    title: "Implementation: write failing tests"
    type: "implementation"
    agent: "security-reviewer"
    runtime: "claude"
    depends_on: ["T1"]
    files_allowed: ["tests/**"]
    tdd_required: true
  - id: T3
    title: "Implementation: implement the feature changes"
    type: "implementation"
    agent: "security-reviewer"
    runtime: "gemini"
    depends_on: ["T2"]
    files_allowed: ["*"]
  - id: T4
    title: "Review: security check"
    type: "review"
    agent: "security-reviewer"
    depends_on: ["T3"]
    writes_files: false
  - id: T5
    title: "Validation: verify all tests pass"
    type: "validation"
    agent: "security-reviewer"
    runtime: "codex"
    depends_on: ["T4"]
```
