# /context-refresh

Re-scan the repository and update project context.

## Usage

```
/context-refresh
```

## Workflow

1. Run `niyam context refresh` to scan the repository
2. Run `niyam sync` to propagate changes to runtime files
3. Report what changed

## When to Use

- After adding new dependencies
- After restructuring the project
- After adding new CI/CD configuration
- Periodically to keep context fresh
