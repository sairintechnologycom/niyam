# Evidence Report — niyam

**Branch:** `main`
**Generated:** 2026-05-30 15:56 UTC
**Generator:** Niyam v0.1.0

---

# Diff Summary

## Unstaged Changes

```
.claude/hooks/pre_tool_guard.py |  4 +-
 .niyam/context/architecture.md  | 75 +++++++++++++++++++++++++++++++--
 .niyam/context/validation.md    | 17 +++++++-
 CLAUDE.md                       | 92 ++++++++++++++++++++++++++++++++++++++---
 niyam/cli/main_cmds.py          | 14 +++++++
 niyam/core/compare.py           | 42 ++++++++++++-------
 niyam/mission/executor.py       | 16 ++++---
 niyam/mission/reporter.py       |  4 +-
 tests/test_compare.py           | 16 ++++---
 tests/test_mission.py           |  4 +-
 10 files changed, 240 insertions(+), 44 deletions(-)
```

## Recent Commits

```
c6a6fd6 Add multi-runtime comparison, GitHub Actions integration, and token parsing for Gemini/Codex
8514f6f Enhance mission orchestration and memory evidence
bc54094 refactor: split cli monolith into niyam/cli package and complete robustness plan
0461dc3 feat(dx): implement non-interactive planning, extension-aware mock writer, auto-stashing merges, and dynamic pricing
6224c11 Complete task T5
206ceaf Complete task T4
e619a52 Complete task T3
eba0785 Complete task T2
3512904 Complete task T1
26a79e9 docs: generate initial codebase map
b21e90e feat(dx): implement 10 developer experience enhancements and comprehensive unit tests
0aadaa3 chore: commit generated Claude Code instruction and adapter files
7f5681c fix: resolve write boundary violations in mock executor task execution
f8aa785 Hardened task contract, DAG validation, writes_files boundaries, review limits, and standardized project root resolution
1f36a29 Update gitignore and add AGENTS.md memory context
5c33093 Fix Claude runtime pre-tool hook formatting compliance with Ruff format
ac816c9 Fix validation bypass, report failure status, hook unused import, and context diff false positives
362c70d feat(security): implement security hardening and robustness roadmap (Phase 1 & 2)
c7f511b feat(packs): add ab-testing-setup, api-governance, security-scanning, and tdd-quality-gate packs
f0a9a31 feat(roadmap,init): add ROADMAP.md and update niyam init to create MVP directories
```

---

# Validation Results

### Test
Command: `pytest`
Status: ✓ Passed
```
============================= test session starts ==============================
platform darwin -- Python 3.14.3, pytest-9.0.3, pluggy-1.6.0 -- /opt/homebrew/opt/python@3.14/bin/python3.14
cachedir: .pytest_cache
rootdir: /Users/bhushan/Documents/Projects/niyam
configfile: pyproject.toml
testpaths: tests
plugins: cov-7.1.0, pytest_tmp_files-0.0.2, anyio-4.13.0
collecting ... collected 126 items

tests/test_ci.py::test_non_interactive_fails_unapproved PASSED           [  0%]
tests/test_ci.py::test_non_interactive_auto_approve PASSED               [  1%]
tests/test_ci.py::test_remote_policy_fetching PASSED                     [  2%]
tests/test_ci.py::test_remote_policy_fallback PASSED                     [  3%]
tests/test_ci.py::test_ci_verify_strict_missing_evidence PASSED          [  3%]
tests/test_ci.py::test_ci_verify_non_strict_missing_evidence PASSED      [  4%]
tests/test_ci.py::test_ci_verify_write_violation PASSED                  [  5%]
tests/test_cli.py::TestCLI::test_version PASSED                          [  6%]
tests/test_cli.py::TestCLI::test_help PASSED                             [  7%]
tests/test_cli.py::TestCLI::test_context_help PASSED                     [  7%]
tests/test_cli.py::TestCLI::test_guard_help PASSED                       [  8%]
tests/test_cli.py::TestCLI::test_runtime_help PASSED                     [  9%]
tests/test_cli.py::TestCLI::test_policy_help PASSED                      [ 10%]
tests/test_compare.py::test_comparison_runs_multiple_executors PASSED    [ 11%]
tests/test_compare.py::test_compare_cli_command PASSED                   [ 11%]
tests/test_context.py::TestContextRefresh::test_context_refresh_creates_architecture PASSED [ 12%]
tests/test_context.py::TestContextRefresh::test_context_refresh_creates_validation PASSED [ 13%]
tests/test_context.py::TestContextRefresh::test_context_refresh_detects_python PASSED [ 14%]
tests/test_context.py::TestContextRefresh::test_context_refresh_detects_node PASSED [ 15%]
tests/test_context.p
... (truncated)
```

### Lint
Command: `ruff check .`
Status: ✓ Passed
```
All checks passed!
```

### Format
Command: `ruff format --check .`
Status: ✓ Passed
```
80 files already formatted
```


---

# Policy Events

No policy events recorded.

---

<!-- End of Niyam Evidence Report -->
