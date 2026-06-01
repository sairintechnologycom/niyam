# /implement

Plan and implement a feature or change.

## Usage

```
/implement <description>
```

## Workflow

1. **Understand** — Read the description carefully. Check `.niyam/context/` for project context.
2. **Plan** — Use the `implementation-planning` skill to create a plan. List affected files, approach, tests, and acceptance criteria.
3. **Get approval** — Present the plan for review before writing code.
4. **Implement** — Use the `test-driven-development` skill. RED → GREEN → REFACTOR.
5. **Validate** — Run all validation commands from `.niyam/context/validation.md`.
6. **Summary** — Summarize what was done, what was tested, and what to review.

## Rules

- Do not skip the planning step.
- Do not skip tests.
- Run validation before declaring the task complete.
- If the scope is larger than expected, stop and re-plan.
