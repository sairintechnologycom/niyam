# /ship

Validate all changes and prepare for merge.

## Usage

```
/ship
```

## Workflow

1. **Run all validation commands** — build, test, lint, typecheck from `.niyam/context/validation.md`
2. **Check for uncommitted changes** — ensure everything is committed or staged
3. **Generate evidence** — Run `niyam report` to create the evidence pack
4. **Create summary** — Write a clear summary of:
   - What was implemented
   - What was tested
   - Any known limitations
   - Evidence location

## Pre-ship Checklist

- [ ] All validation commands pass
- [ ] No uncommitted changes
- [ ] Tests cover the new functionality
- [ ] No security review issues open
- [ ] Evidence report generated

## Rules

- Do NOT ship if validation fails.
- Do NOT ship if there are unresolved blocking review issues.
- Always generate evidence before declaring "ready to merge."
