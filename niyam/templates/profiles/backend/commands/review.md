# /review

Review recent changes for quality, security, and correctness.

## Usage

```
/review
```

## Workflow

1. **Identify changes** — Run `git diff` to see what changed.
2. **Code quality review** — Check for:
   - Code clarity and readability
   - Proper error handling
   - Test coverage
   - Consistent patterns with the rest of the codebase
3. **Security review** — Use the `secure-code-review` skill to check for vulnerabilities.
4. **Report** — Provide a structured review with:
   - **Must Fix** — blocking issues
   - **Should Fix** — important but not blocking
   - **Consider** — suggestions for improvement
   - **Looks Good** — what's well done

## Rules

- Be specific — cite exact lines and explain why.
- Distinguish between blocking and non-blocking issues.
- Check that tests actually test the right things.
- Verify claims — don't trust comments, read the code.
