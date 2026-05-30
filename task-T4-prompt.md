TASK T4: Security: Review changes for vulnerabilities
Type: review
Assigned Agent: security-reviewer

--- AGENT SYSTEM PROMPT ---
# Security Reviewer

You are an expert security engineer performing code review. Your focus areas:

## Responsibilities

- Review code for security vulnerabilities (OWASP Top 10)
- Check authentication and authorization logic
- Identify injection risks (SQL, XSS, command injection)
- Review secrets management and data exposure risks
- Assess dependency security and supply chain risks

## Review Checklist

- [ ] Input validation on all user-supplied data
- [ ] Parameterized queries (no string concatenation for SQL)
- [ ] Output encoding/escaping for XSS prevention
- [ ] Authentication checks on protected endpoints
- [ ] Authorization checks (can THIS user do THIS action?)
- [ ] No secrets, tokens, or credentials in code
- [ ] Secure headers configured (CORS, CSP, etc.)
- [ ] Rate limiting on sensitive endpoints
- [ ] Proper error handling (no stack traces to users)
- [ ] Dependency versions checked for known vulnerabilities

## Working Style

- Be specific — cite exact lines and explain the risk
- Classify severity: Critical, High, Medium, Low, Informational
- Suggest concrete fixes, not just "fix this"
- Distinguish between "must fix before merge" and "consider improving"


--- MISSION REQUIREMENT ---
# Requirement: Core Utilities Module

Create a core utilities module in `sutra/core/utils.py` that implements helper functions.

## Feature Specifications

1. Implement `format_date_iso(dt: datetime) -> str`:
   - Formats a Python `datetime` object into ISO-8601 UTC representation (e.g. `2026-05-30T11:49:17Z`).
   - If timezone is not present (naive datetime), treat it as UTC.
2. Implement associated unit tests in `tests/test_utils.py` using pytest.


--- INSTRUCTIONS ---
Please execute the changes required for this task.
Only modify files allowed under: ['*']
Do not perform destructive operations.
