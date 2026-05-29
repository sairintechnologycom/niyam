# Codebase Concerns

**Analysis Date:** 2025-05-24

## Tech Debt

**Large File Complexity:**
- Issue: `sutra/mission/executor.py` (1490 lines) and `sutra/cli.py` (1004 lines) are exceeding manageable sizes, combining multiple responsibilities.
- Files: `sutra/mission/executor.py`, `sutra/cli.py`
- Impact: Harder to maintain, test, and understand the flow of mission execution.
- Fix approach: Refactor `executor.py` by extracting git operations, worktree management, and hook execution into separate modules within `sutra/mission/`.

**Hardcoded Stack Detection:**
- Issue: Manifest mapping and framework indicators are hardcoded in the module.
- Files: `sutra/core/context.py`
- Impact: Adding support for new languages or frameworks requires code changes.
- Fix approach: Move these definitions to a configuration file (e.g., `stack-rules.yaml`) that can be updated without code changes.

**Duplicate Logging Logic:**
- Issue: `log_policy_event` and file locking logic is duplicated between the executor and runtime adapters.
- Files: `sutra/mission/executor.py`, `sutra/runtimes/claude.py`
- Impact: Inconsistent logging behavior and maintenance overhead.
- Fix approach: Centralize logging and locking utilities in `sutra/core/`.

## Security Considerations

**Shell Execution:**
- Issue: `subprocess.run(cmd, shell=True)` is used for executing hooks.
- Files: `sutra/mission/executor.py`
- Risk: Potential for command injection if hook commands or context variables are not strictly sanitized.
- Current mitigation: Basic variable replacement.
- Recommendations: Avoid `shell=True` where possible; use `shlex.split` for command parsing if necessary.

## Fragile Areas

**Platform Specificity:**
- Issue: Use of `fcntl` for file locking.
- Files: `sutra/mission/executor.py`, `sutra/runtimes/claude.py`
- Why fragile: `fcntl` is not available on Windows, making the CLI non-portable to a significant portion of developer environments.
- Safe modification: Use a cross-platform locking library like `portalocker` or implement a fallback mechanism for Windows.

**Placeholder Replacement:**
- Issue: Simple string `.replace("{{key}}", value)` for command formatting.
- Files: `sutra/mission/executor.py`
- Why fragile: Error-prone and lacks validation for required placeholders.
- Safe modification: Use a more robust templating approach or structured command builder.

## Test Coverage Gaps

**Mission Execution Lifecycle:**
- What's not tested: Complex multi-task mission state transitions (pause, resume, retry) with real or mocked filesystem side effects.
- Files: `sutra/mission/executor.py`
- Risk: Regressions in mission state management or file restoration (backups) during failures.
- Priority: High

---

*Concerns audit: 2025-05-24*
