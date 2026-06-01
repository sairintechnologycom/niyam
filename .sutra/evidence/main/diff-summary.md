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
