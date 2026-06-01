---
name: test-driven-development
description: Write tests before implementation code using RED-GREEN-REFACTOR.
---

# Test-Driven Development

Follow the RED-GREEN-REFACTOR cycle for all implementation work.

## When to Use

- For all new features and bug fixes
- When modifying existing behavior

## Process

### 1. RED — Write a failing test
- Write a test that describes the desired behavior
- Run the test — it MUST fail
- If it passes, the test is wrong or the feature already exists

### 2. GREEN — Make it pass
- Write the minimum code to make the test pass
- Do NOT write more than needed
- Run the test — it MUST pass now

### 3. REFACTOR — Clean up
- Improve the code without changing behavior
- Run all tests — they MUST still pass
- Clean up any duplication or naming issues

## Rules

- **Never skip RED** — always see the test fail first
- **Minimum viable code** — don't gold-plate during GREEN
- **Tests are documentation** — write them clearly
- **Run validation** — run the full test suite after refactoring
- **Evidence over claims** — paste test output, don't just say "tests pass"
