---
name: secure-code-review
description: Review code for security vulnerabilities and best practices.
---

# Secure Code Review

Review code changes for security vulnerabilities before they reach production.

## When to Use

- Before merging any code that handles user input
- When authentication, authorization, or payment code changes
- When new API endpoints are added
- When dependencies are updated

## Checklist

### Input & Output
- [ ] All user input is validated and sanitized
- [ ] SQL queries use parameterized statements
- [ ] Output is properly encoded/escaped
- [ ] File uploads are validated (type, size, content)

### Authentication & Authorization
- [ ] Auth checks on every protected endpoint
- [ ] Authorization checks (role/permission-based)
- [ ] Session management is secure
- [ ] Password handling follows best practices

### Data Protection
- [ ] No secrets in code or logs
- [ ] Sensitive data is encrypted at rest and in transit
- [ ] PII handling follows policy
- [ ] Error messages don't leak internal details

### Dependencies
- [ ] No known vulnerable dependencies
- [ ] Dependency versions are pinned
- [ ] New dependencies are reviewed for trust

## Severity Levels

- **Critical**: Exploitable now, data at risk
- **High**: Likely exploitable, needs fix before merge
- **Medium**: Potential risk, should fix soon
- **Low**: Minor concern, consider improving
- **Info**: Best practice suggestion
