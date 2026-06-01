# Niyam Mission Evidence Package - requirements-utils-20260530-115131

- **Requirement Source:** `scratch/requirements-utils.md`
- **Generated:** `2026-05-30T06:26:05.978513Z`
- **Status:** `FAILED`
- **Orchestrator:** `claude`

## Task Checklist

- [✓] **T1**: Discovery: analyze utils requirement and existing core module conventions (backend-specialist)
- [✓] **T2**: Implementation: write failing pytest tests for format_date_iso in tests/test_utils.py (qa-reviewer)
- [✓] **T3**: Implementation: implement format_date_iso in niyam/core/utils.py (backend-specialist)
- [✓] **T4**: Review: security and code-quality check of utils module and tests (security-reviewer)
- [✓] **T5**: Validation: run pytest and confirm all tests pass (qa-reviewer)

## Execution Log

- `2026-05-30T06:23:46.047424Z` **MISSION_STARTED**: Mission execution started (parallel=1, worktree=True).
- `2026-05-30T06:23:46.065435Z` **TASK_STARTED** [T1]: Running task: Discovery: analyze utils requirement and existing core module conventions
- `2026-05-30T06:23:46.252522Z` **TASK_EXECUTION_MOCK** [T1]: Mocked execution successfully.
- `2026-05-30T06:23:59.433178Z` **TASK_COMPLETED** [T1]: Completed task: Discovery: analyze utils requirement and existing core module conventions
- `2026-05-30T06:23:59.443955Z` **TASK_STARTED** [T2]: Running task: Implementation: write failing pytest tests for format_date_iso in tests/test_utils.py
- `2026-05-30T06:23:59.604873Z` **TASK_EXECUTION_MOCK** [T2]: Mocked execution successfully.
- `2026-05-30T06:24:00.651482Z` **TASK_FAILED** [T2]: Task execution failed.
- `2026-05-30T06:24:00.661550Z` **TASK_SKIPPED** [T3]: Dependency failed, skipping task.
- `2026-05-30T06:24:00.666684Z` **TASK_STARTED** [T4]: Running task: Review: security and code-quality check of utils module and tests
- `2026-05-30T06:24:00.760383Z` **TASK_FAILED** [T4]: Task execution failed.
- `2026-05-30T06:24:00.783369Z` **TASK_SKIPPED** [T5]: Dependency failed, skipping task.
- `2026-05-30T06:24:00.797903Z` **MISSION_FAILED**: Mission execution failed due to task failures.
- `2026-05-30T06:24:56.659622Z` **MISSION_RETRIED**: Retrying failed/skipped tasks.
- `2026-05-30T06:24:56.704590Z` **MISSION_STARTED**: Mission execution started (parallel=1, worktree=True).
- `2026-05-30T06:24:56.721678Z` **TASK_STARTED** [T2]: Running task: Implementation: write failing pytest tests for format_date_iso in tests/test_utils.py
- `2026-05-30T06:24:56.933345Z` **TASK_EXECUTION_MOCK** [T2]: Mocked execution successfully.
- `2026-05-30T06:25:10.245124Z` **TASK_COMPLETED** [T2]: Completed task: Implementation: write failing pytest tests for format_date_iso in tests/test_utils.py
- `2026-05-30T06:25:10.254202Z` **TASK_STARTED** [T3]: Running task: Implementation: implement format_date_iso in niyam/core/utils.py
- `2026-05-30T06:25:10.408523Z` **TASK_EXECUTION_MOCK** [T3]: Mocked execution successfully.
- `2026-05-30T06:25:23.174058Z` **TASK_COMPLETED** [T3]: Completed task: Implementation: implement format_date_iso in niyam/core/utils.py
- `2026-05-30T06:25:23.184860Z` **TASK_STARTED** [T4]: Running task: Review: security and code-quality check of utils module and tests
- `2026-05-30T06:25:23.592533Z` **TASK_EXECUTION_MOCK** [T4]: Mocked execution successfully.
- `2026-05-30T06:25:36.983769Z` **TASK_COMPLETED** [T4]: Completed task: Review: security and code-quality check of utils module and tests
- `2026-05-30T06:25:36.993215Z` **TASK_STARTED** [T5]: Running task: Validation: run pytest and confirm all tests pass
- `2026-05-30T06:25:37.155140Z` **TASK_EXECUTION_MOCK** [T5]: Mocked execution successfully.
- `2026-05-30T06:25:51.975866Z` **TASK_COMPLETED** [T5]: Completed task: Validation: run pytest and confirm all tests pass

## Policy Guard Audit Trail

*No policy events triggered.*

## Validation Results


## Validation Check - format - 2026-05-30T06:23:46.279310Z
**Status:** ℹ SKIPPED — Not configured


## Validation Check - lint - 2026-05-30T06:23:46.279453Z
**Status:** ℹ SKIPPED — Not configured


## Validation Check - typecheck - 2026-05-30T06:23:46.279503Z
**Status:** ℹ SKIPPED — Not configured


## Validation Check - build - 2026-05-30T06:23:46.279543Z
**Status:** ℹ SKIPPED — Not configured


## Validation Run - 2026-05-30T06:23:59.197916Z
**Command:** `pytest`
**Exit Code:** `0`

### stdout
```
============================= test session starts ==============================
platform darwin -- Python 3.14.3, pytest-9.0.3, pluggy-1.6.0 -- /opt/homebrew/opt/python@3.14/bin/python3.14
cachedir: .pytest_cache
rootdir: /Users/bhushan/Documents/Projects/niyam/.niyam/runs/requirements-utils-20260530-115131/worktrees/T1
configfile: pyproject.toml
testpaths: tests
plugins: cov-7.1.0, pytest_tmp_files-0.0.2, anyio-4.13.0
collecting ... collected 107 items

tests/test_ci.py::test_non_interactive_fails_unapproved PASSED           [  0%]
tests/test_ci.py::test_non_interactive_auto_approve PASSED               [  1%]
tests/test_ci.py::test_remote_policy_fetching PASSED                     [  2%]
tests/test_ci.py::test_remote_policy_fallback PASSED                     [  3%]
tests/test_ci.py::test_ci_verify_strict_missing_evidence PASSED          [  4%]
tests/test_ci.py::test_ci_verify_non_strict_missing_evidence PASSED      [  5%]
tests/test_ci.py::test_ci_verify_write_violation PASSED                  [  6%]
tests/test_cli.py::TestCLI::test_version PASSED                          [  7%]
tests/test_cli.py::TestCLI::test_help PASSED                             [  8%]
tests/test_cli.py::TestCLI::test_context_help PASSED                     [  9%]
tests/test_cli.py::TestCLI::test_guard_help PASSED                       [ 10%]
tests/test_cli.py::TestCLI::test_runtime_help PASSED                     [ 11%]
tests/test_cli.py::TestCLI::test_policy_help PASSED                      [ 12%]
tests/test_context.py::TestContextRefresh::test_context_refresh_creates_architecture PASSED [ 13%]
tests/test_context.py::TestContextRefresh::test_context_refresh_creates_validation PASSED [ 14%]
tests/test_context.py::TestContextRefresh::test_context_refresh_detects_python PASSED [ 14%]
tests/test_context.py::TestContextRefresh::test_context_refresh_detects_node PASSED [ 15%]
tests/test_context.py::TestContextRefresh::test_context_refresh_preserves_manual_section PASSED [ 16%]
tests/test_dashboard.py::test_dashboard_rendering PASSED                 [ 17%]
tests/test_dashboard.py::test_dashboard_watch_mode PASSED                [ 18%]
tests/test_doctor.py::TestDoctor::test_doctor_passes_on_fresh_init PASSED [ 19%]
tests/test_doctor.py::TestDoctor::test_doctor_fails_without_niyam PASSED [ 20%]
tests/test_doctor.py::TestDoctor::test_doctor_detects_missing_files PASSED [ 21%]
tests/test_doctor.py::TestDoctor::test_doctor_detects_invalid_yaml PASSED [ 22%]
tests/test_doctor_enhanced.py::test_doctor_runtimes_in_path PASSED       [ 23%]
tests/test_doctor_enhanced.py::test_doctor_agents_validity PASSED        [ 24%]
tests/test_doctor_enhanced.py::test_doctor_validation_commands PASSED    [ 25%]
tests/test_doctor_enhanced.py::test_doctor_git_status_dirty PASSED       [ 26%]
tests/test_fleet.py::test_fleet_parallel_execution PASSED                [ 27%]
tests/test_fleet.py::test_fleet_dependency_failure PASSED                [ 28%]
tests/test_fleet.py::test_fleet_worktree_fallback_when_no_git PASSED     [ 28%]
tests/test_guard.py::TestGuard::test_guard_enable PASSED                 [ 29%]
tests/test_guard.py::TestGuard::test_guard_disable PASSED                [ 30%]
tests/test_guard.py::TestGuard::test_guard_careful_adds_warn_list PASSED [ 31%]
tests/test_guard.py::TestGuard::test_guard_freeze_adds_path PASSED       [ 32%]
tests/test_guard.py::TestGuard::test_guard_freeze_enables_guard PASSED   [ 33%]
tests/test_guardrails.py::test_path_write_denial_and_revert PASSED       [ 34%]
tests/test_hooks.py::test_hooks_lifecycle_triggers PASSED                [ 35%]
tests/test_init.py::TestInit::test_init_creates_niyam_directory PASSED   [ 36%]
tests/test_init.py::TestInit::test_init_creates_mvp_directories PASSED   [ 37%]
tests/test_init.py::TestInit::test_init_creates_niyam_yaml PASSED        [ 38%]
tests/test_init.py::TestInit::test_init_creates_agents PASSED            [ 39%]
tests/test_init.py::TestInit::test_init_creates_skills PASSED            [ 40%]
tests/test_init.py::TestInit::test_init_creates_commands PASSED          [ 41%]
tests/test_init.py::TestInit::test_init_creates_policies PASSED          [ 42%]
tests/test_init.py::TestInit::test_init_fails_if_already_exists PASSED   [ 42%]
tests/test_init.py::TestInit::test_init_force_overwrites PASSED          [ 43%]
tests/test_init.py::TestInit::test_init_dry_run_creates_nothing PASSED   [ 44%]
tests/test_init.py::TestInit::test_init_with_claude_runtime PASSED       [ 45%]
tests/test_init.py::TestInit::test_init_invalid_profile_fails PASSED     [ 46%]
tests/test_init.py::TestInit::test_init_backend_profile PASSED           [ 47%]
tests/test_init.py::TestInit::test_init_frontend_profile PASSED          [ 48%]
tests/test_memory.py::TestMemory::test_memory_show PASSED                [ 49%]
tests/test_memory.py::TestMemory::test_memory_add PASSED                 [ 50%]
tests/test_memory.py::TestMemory::test_memory_clear PASSED               [ 51%]
tests/test_memory.py::TestMemory::test_memory_sync_propagates_to_runtimes PASSED [ 52%]
tests/test_mission.py::TestMission::test_mission_plan_creates_files PASSED [ 53%]
tests/test_mission.py::TestMission::test_mission_approve PASSED          [ 54%]
tests/test_mission.py::TestMission::test_mission_execution_lifecycle PASSED [ 55%]
tests/test_mission.py::TestMission::test_mission_pause_resume PASSED     [ 56%]
tests/test_mission.py::TestMission::test_mission_plan_strict PASSED      [ 57%]
tests/test_multi_runtime.py::test_planner_prompt_contains_runtime PASSED [ 57%]
tests/test_multi_runtime.py::test_planner_parses_runtime_field PASSED    [ 58%]
tests/test_multi_runtime.py::test_executor_resolves_task_runtime PASSED  [ 59%]
tests/test_packs.py::TestPacks::test_list_packs PASSED                   [ 60%]
tests/test_packs.py::TestPacks::test_add_pack_copies_files PASSED        [ 61%]
tests/test_packs.py::TestPacks::test_add_pack_conflict PASSED            [ 62%]
tests/test_packs.py::TestPacks::test_remove_pack PASSED                  [ 63%]
tests/test_packs.py::TestPacks::test_sync_packs PASSED                   [ 64%]
tests/test_pr.py::test_pr_review_mocked PASSED                           [ 65%]
tests/test_pr.py::test_pr_create_mocked PASSED                           [ 66%]
tests/test_recovery.py::test_mission_skip_unblocks_downstream PASSED     [ 67%]
tests/test_recovery.py::test_mission_retry_requeues_tasks PASSED         [ 68%]
tests/test_recovery.py::test_mission_rollback_git_checkout PASSED        [ 69%]
tests/test_remediation.py::test_bash_sh_blocked PASSED                   [ 70%]
tests/test_remediation.py::test_report_fails_on_validation_failure PASSED [ 71%]
tests/test_remediation.py::test_context_diff_ignores_manual_sections PASSED [ 71%]
tests/test_remediation.py::test_claude_hook_script_formatting_and_imports PASSED [ 72%]
tests/test_remediation.py::test_validate_mission_plan_cycle PASSED       [ 73%]
tests/test_remediation.py::test_validate_mission_plan_unknown_dependency PASSED [ 74%]
tests/test_remediation.py::test_writes_files_false_violation_and_revert PASSED [ 75%]
tests/test_review.py::TestReview::test_get_git_diff_untracked_file PASSED [ 76%]
tests/test_review.py::TestReview::test_run_review_engineering_lens PASSED [ 77%]
tests/test_review.py::TestReview::test_run_review_adversarial_mode PASSED [ 78%]
tests/test_review.py::TestReview::test_get_git_diff_file_size_limit PASSED [ 79%]
tests/test_review.py::TestReview::test_get_git_diff_budget_limit PASSED  [ 80%]
tests/test_review.py::TestReview::test_get_git_diff_skip_binary_files PASSED [ 81%]
tests/test_review.py::TestReview::test_get_git_diff_redact_secrets PASSED [ 82%]
tests/test_run_composite.py::test_run_composite_command_file PASSED      [ 83%]
tests/test_run_composite.py::test_run_composite_command_inline_string PASSED [ 84%]
tests/test_setup.py::test_setup_wizard_fresh_initialization PASSED       [ 85%]
tests/test_sync.py::TestClaudeSync::test_claude_sync_creates_claude_md PASSED [ 85%]
tests/test_sync.py::TestClaudeSync::test_claude_sync_creates_claude_dir PASSED [ 86%]
tests/test_sync.py::TestClaudeSync::test_claude_sync_creates_agents PASSED [ 87%]
tests/test_sync.py::TestClaudeSync::test_claude_sync_creates_hooks PASSED [ 88%]
tests/test_sync.py::TestClaudeSync::test_claude_sync_creates_settings PASSED [ 89%]
tests/test_sync.py::TestClaudeSync::test_claude_md_contains_policies PASSED [ 90%]
tests/test_sync.py::TestCodexSync::test_codex_sync_creates_agents_md PASSED [ 91%]
tests/test_sync.py::TestCodexSync::test_agents_md_contains_policies PASSED [ 92%]
tests/test_sync.py::TestGeminiSync::test_gemini_sync_creates_gemini_md PASSED [ 93%]
tests/test_sync.py::TestGeminiSync::test_gemini_sync_creates_gemini_dir PASSED [ 94%]
tests/test_sync.py::TestGeminiSync::test_gemini_md_contains_policies PASSED [ 95%]
tests/test_sync.py::TestRuntimeAdd::test_runtime_add_updates_config PASSED [ 96%]
tests/test_sync.py::TestRuntimeAdd::test_runtime_add_duplicate_is_safe PASSED [ 97%]
tests/test_templates.py::test_builtin_template_planning PASSED           [ 98%]
tests/test_templates.py::test_custom_template_planning PASSED            [ 99%]
tests/test_verification.py::test_verification_lifecycle PASSED           [100%]

=============================== warnings summary ===============================
tests/test_mission.py::TestMission::test_mission_execution_lifecycle
tests/test_verification.py::test_verification_lifecycle
  /Users/bhushan/Documents/Projects/niyam/niyam/mission/reporter.py:172: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    report_sections.append(f"- **Generated:** `{datetime.utcnow().isoformat()}Z`")

tests/test_mission.py::TestMission::test_mission_execution_lifecycle
tests/test_verification.py::test_verification_lifecycle
  /Users/bhushan/Documents/Projects/niyam/niyam/mission/reporter.py:244: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    "timestamp": datetime.utcnow().isoformat() + "Z",

tests/test_mission.py::TestMission::test_mission_execution_lifecycle
tests/test_verification.py::test_verification_lifecycle
  /Users/bhushan/Documents/Projects/niyam/niyam/mission/reporter.py:273: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    "completed": datetime.utcnow().isoformat() + "Z",

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================= 107 passed, 6 warnings in 12.54s =======================

```

## Validation Check - format - 2026-05-30T06:23:59.627985Z
**Status:** ℹ SKIPPED — Not configured


## Validation Check - lint - 2026-05-30T06:23:59.628102Z
**Status:** ℹ SKIPPED — Not configured


## Validation Check - typecheck - 2026-05-30T06:23:59.628153Z
**Status:** ℹ SKIPPED — Not configured


## Validation Check - build - 2026-05-30T06:23:59.628196Z
**Status:** ℹ SKIPPED — Not configured


## Validation Run - 2026-05-30T06:24:00.490622Z
**Command:** `pytest`
**Exit Code:** `2`

### stdout
```
============================= test session starts ==============================
platform darwin -- Python 3.14.3, pytest-9.0.3, pluggy-1.6.0 -- /opt/homebrew/opt/python@3.14/bin/python3.14
cachedir: .pytest_cache
rootdir: /Users/bhushan/Documents/Projects/niyam/.niyam/runs/requirements-utils-20260530-115131/worktrees/T2
configfile: pyproject.toml
testpaths: tests
plugins: cov-7.1.0, pytest_tmp_files-0.0.2, anyio-4.13.0
collecting ... collected 107 items / 1 error

==================================== ERRORS ====================================
_____________________ ERROR collecting tests/test_utils.py _____________________
/opt/homebrew/lib/python3.14/site-packages/_pytest/python.py:507: in importtestmodule
    mod = import_path(
/opt/homebrew/lib/python3.14/site-packages/_pytest/pathlib.py:587: in import_path
    importlib.import_module(module_name)
/opt/homebrew/Cellar/python@3.14/3.14.3_1/Frameworks/Python.framework/Versions/3.14/lib/python3.14/importlib/__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
<frozen importlib._bootstrap>:1398: in _gcd_import
    ???
<frozen importlib._bootstrap>:1371: in _find_and_load
    ???
<frozen importlib._bootstrap>:1342: in _find_and_load_unlocked
    ???
<frozen importlib._bootstrap>:938: in _load_unlocked
    ???
/opt/homebrew/lib/python3.14/site-packages/_pytest/assertion/rewrite.py:188: in exec_module
    source_stat, co = _rewrite_test(fn, self.config)
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
/opt/homebrew/lib/python3.14/site-packages/_pytest/assertion/rewrite.py:357: in _rewrite_test
    tree = ast.parse(source, filename=strfn)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
/opt/homebrew/Cellar/python@3.14/3.14.3_1/Frameworks/Python.framework/Versions/3.14/lib/python3.14/ast.py:46: in parse
    return compile(source, filename, mode, flags,
E     File "/Users/bhushan/Documents/Projects/niyam/.niyam/runs/requirements-utils-20260530-115131/worktrees/T2/tests/test_utils.py", line 1
E       Changes by task T2
E               ^^
E   SyntaxError: invalid syntax
=========================== short test summary info ============================
ERROR tests/test_utils.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
=============================== 1 error in 0.39s ===============================

```

## Validation Check - format - 2026-05-30T06:24:56.961730Z
**Status:** ℹ SKIPPED — Not configured


## Validation Check - lint - 2026-05-30T06:24:56.962011Z
**Status:** ℹ SKIPPED — Not configured


## Validation Check - typecheck - 2026-05-30T06:24:56.962071Z
**Status:** ℹ SKIPPED — Not configured


## Validation Check - build - 2026-05-30T06:24:56.962121Z
**Status:** ℹ SKIPPED — Not configured


## Validation Run - 2026-05-30T06:25:10.071693Z
**Command:** `pytest`
**Exit Code:** `0`

### stdout
```
============================= test session starts ==============================
platform darwin -- Python 3.14.3, pytest-9.0.3, pluggy-1.6.0 -- /opt/homebrew/opt/python@3.14/bin/python3.14
cachedir: .pytest_cache
rootdir: /Users/bhushan/Documents/Projects/niyam/.niyam/runs/requirements-utils-20260530-115131/worktrees/T2
configfile: pyproject.toml
testpaths: tests
plugins: cov-7.1.0, pytest_tmp_files-0.0.2, anyio-4.13.0
collecting ... collected 107 items

tests/test_ci.py::test_non_interactive_fails_unapproved PASSED           [  0%]
tests/test_ci.py::test_non_interactive_auto_approve PASSED               [  1%]
tests/test_ci.py::test_remote_policy_fetching PASSED                     [  2%]
tests/test_ci.py::test_remote_policy_fallback PASSED                     [  3%]
tests/test_ci.py::test_ci_verify_strict_missing_evidence PASSED          [  4%]
tests/test_ci.py::test_ci_verify_non_strict_missing_evidence PASSED      [  5%]
tests/test_ci.py::test_ci_verify_write_violation PASSED                  [  6%]
tests/test_cli.py::TestCLI::test_version PASSED                          [  7%]
tests/test_cli.py::TestCLI::test_help PASSED                             [  8%]
tests/test_cli.py::TestCLI::test_context_help PASSED                     [  9%]
tests/test_cli.py::TestCLI::test_guard_help PASSED                       [ 10%]
tests/test_cli.py::TestCLI::test_runtime_help PASSED                     [ 11%]
tests/test_cli.py::TestCLI::test_policy_help PASSED                      [ 12%]
tests/test_context.py::TestContextRefresh::test_context_refresh_creates_architecture PASSED [ 13%]
tests/test_context.py::TestContextRefresh::test_context_refresh_creates_validation PASSED [ 14%]
tests/test_context.py::TestContextRefresh::test_context_refresh_detects_python PASSED [ 14%]
tests/test_context.py::TestContextRefresh::test_context_refresh_detects_node PASSED [ 15%]
tests/test_context.py::TestContextRefresh::test_context_refresh_preserves_manual_section PASSED [ 16%]
tests/test_dashboard.py::test_dashboard_rendering PASSED                 [ 17%]
tests/test_dashboard.py::test_dashboard_watch_mode PASSED                [ 18%]
tests/test_doctor.py::TestDoctor::test_doctor_passes_on_fresh_init PASSED [ 19%]
tests/test_doctor.py::TestDoctor::test_doctor_fails_without_niyam PASSED [ 20%]
tests/test_doctor.py::TestDoctor::test_doctor_detects_missing_files PASSED [ 21%]
tests/test_doctor.py::TestDoctor::test_doctor_detects_invalid_yaml PASSED [ 22%]
tests/test_doctor_enhanced.py::test_doctor_runtimes_in_path PASSED       [ 23%]
tests/test_doctor_enhanced.py::test_doctor_agents_validity PASSED        [ 24%]
tests/test_doctor_enhanced.py::test_doctor_validation_commands PASSED    [ 25%]
tests/test_doctor_enhanced.py::test_doctor_git_status_dirty PASSED       [ 26%]
tests/test_fleet.py::test_fleet_parallel_execution PASSED                [ 27%]
tests/test_fleet.py::test_fleet_dependency_failure PASSED                [ 28%]
tests/test_fleet.py::test_fleet_worktree_fallback_when_no_git PASSED     [ 28%]
tests/test_guard.py::TestGuard::test_guard_enable PASSED                 [ 29%]
tests/test_guard.py::TestGuard::test_guard_disable PASSED                [ 30%]
tests/test_guard.py::TestGuard::test_guard_careful_adds_warn_list PASSED [ 31%]
tests/test_guard.py::TestGuard::test_guard_freeze_adds_path PASSED       [ 32%]
tests/test_guard.py::TestGuard::test_guard_freeze_enables_guard PASSED   [ 33%]
tests/test_guardrails.py::test_path_write_denial_and_revert PASSED       [ 34%]
tests/test_hooks.py::test_hooks_lifecycle_triggers PASSED                [ 35%]
tests/test_init.py::TestInit::test_init_creates_niyam_directory PASSED   [ 36%]
tests/test_init.py::TestInit::test_init_creates_mvp_directories PASSED   [ 37%]
tests/test_init.py::TestInit::test_init_creates_niyam_yaml PASSED        [ 38%]
tests/test_init.py::TestInit::test_init_creates_agents PASSED            [ 39%]
tests/test_init.py::TestInit::test_init_creates_skills PASSED            [ 40%]
tests/test_init.py::TestInit::test_init_creates_commands PASSED          [ 41%]
tests/test_init.py::TestInit::test_init_creates_policies PASSED          [ 42%]
tests/test_init.py::TestInit::test_init_fails_if_already_exists PASSED   [ 42%]
tests/test_init.py::TestInit::test_init_force_overwrites PASSED          [ 43%]
tests/test_init.py::TestInit::test_init_dry_run_creates_nothing PASSED   [ 44%]
tests/test_init.py::TestInit::test_init_with_claude_runtime PASSED       [ 45%]
tests/test_init.py::TestInit::test_init_invalid_profile_fails PASSED     [ 46%]
tests/test_init.py::TestInit::test_init_backend_profile PASSED           [ 47%]
tests/test_init.py::TestInit::test_init_frontend_profile PASSED          [ 48%]
tests/test_memory.py::TestMemory::test_memory_show PASSED                [ 49%]
tests/test_memory.py::TestMemory::test_memory_add PASSED                 [ 50%]
tests/test_memory.py::TestMemory::test_memory_clear PASSED               [ 51%]
tests/test_memory.py::TestMemory::test_memory_sync_propagates_to_runtimes PASSED [ 52%]
tests/test_mission.py::TestMission::test_mission_plan_creates_files PASSED [ 53%]
tests/test_mission.py::TestMission::test_mission_approve PASSED          [ 54%]
tests/test_mission.py::TestMission::test_mission_execution_lifecycle PASSED [ 55%]
tests/test_mission.py::TestMission::test_mission_pause_resume PASSED     [ 56%]
tests/test_mission.py::TestMission::test_mission_plan_strict PASSED      [ 57%]
tests/test_multi_runtime.py::test_planner_prompt_contains_runtime PASSED [ 57%]
tests/test_multi_runtime.py::test_planner_parses_runtime_field PASSED    [ 58%]
tests/test_multi_runtime.py::test_executor_resolves_task_runtime PASSED  [ 59%]
tests/test_packs.py::TestPacks::test_list_packs PASSED                   [ 60%]
tests/test_packs.py::TestPacks::test_add_pack_copies_files PASSED        [ 61%]
tests/test_packs.py::TestPacks::test_add_pack_conflict PASSED            [ 62%]
tests/test_packs.py::TestPacks::test_remove_pack PASSED                  [ 63%]
tests/test_packs.py::TestPacks::test_sync_packs PASSED                   [ 64%]
tests/test_pr.py::test_pr_review_mocked PASSED                           [ 65%]
tests/test_pr.py::test_pr_create_mocked PASSED                           [ 66%]
tests/test_recovery.py::test_mission_skip_unblocks_downstream PASSED     [ 67%]
tests/test_recovery.py::test_mission_retry_requeues_tasks PASSED         [ 68%]
tests/test_recovery.py::test_mission_rollback_git_checkout PASSED        [ 69%]
tests/test_remediation.py::test_bash_sh_blocked PASSED                   [ 70%]
tests/test_remediation.py::test_report_fails_on_validation_failure PASSED [ 71%]
tests/test_remediation.py::test_context_diff_ignores_manual_sections PASSED [ 71%]
tests/test_remediation.py::test_claude_hook_script_formatting_and_imports PASSED [ 72%]
tests/test_remediation.py::test_validate_mission_plan_cycle PASSED       [ 73%]
tests/test_remediation.py::test_validate_mission_plan_unknown_dependency PASSED [ 74%]
tests/test_remediation.py::test_writes_files_false_violation_and_revert PASSED [ 75%]
tests/test_review.py::TestReview::test_get_git_diff_untracked_file PASSED [ 76%]
tests/test_review.py::TestReview::test_run_review_engineering_lens PASSED [ 77%]
tests/test_review.py::TestReview::test_run_review_adversarial_mode PASSED [ 78%]
tests/test_review.py::TestReview::test_get_git_diff_file_size_limit PASSED [ 79%]
tests/test_review.py::TestReview::test_get_git_diff_budget_limit PASSED  [ 80%]
tests/test_review.py::TestReview::test_get_git_diff_skip_binary_files PASSED [ 81%]
tests/test_review.py::TestReview::test_get_git_diff_redact_secrets PASSED [ 82%]
tests/test_run_composite.py::test_run_composite_command_file PASSED      [ 83%]
tests/test_run_composite.py::test_run_composite_command_inline_string PASSED [ 84%]
tests/test_setup.py::test_setup_wizard_fresh_initialization PASSED       [ 85%]
tests/test_sync.py::TestClaudeSync::test_claude_sync_creates_claude_md PASSED [ 85%]
tests/test_sync.py::TestClaudeSync::test_claude_sync_creates_claude_dir PASSED [ 86%]
tests/test_sync.py::TestClaudeSync::test_claude_sync_creates_agents PASSED [ 87%]
tests/test_sync.py::TestClaudeSync::test_claude_sync_creates_hooks PASSED [ 88%]
tests/test_sync.py::TestClaudeSync::test_claude_sync_creates_settings PASSED [ 89%]
tests/test_sync.py::TestClaudeSync::test_claude_md_contains_policies PASSED [ 90%]
tests/test_sync.py::TestCodexSync::test_codex_sync_creates_agents_md PASSED [ 91%]
tests/test_sync.py::TestCodexSync::test_agents_md_contains_policies PASSED [ 92%]
tests/test_sync.py::TestGeminiSync::test_gemini_sync_creates_gemini_md PASSED [ 93%]
tests/test_sync.py::TestGeminiSync::test_gemini_sync_creates_gemini_dir PASSED [ 94%]
tests/test_sync.py::TestGeminiSync::test_gemini_md_contains_policies PASSED [ 95%]
tests/test_sync.py::TestRuntimeAdd::test_runtime_add_updates_config PASSED [ 96%]
tests/test_sync.py::TestRuntimeAdd::test_runtime_add_duplicate_is_safe PASSED [ 97%]
tests/test_templates.py::test_builtin_template_planning PASSED           [ 98%]
tests/test_templates.py::test_custom_template_planning PASSED            [ 99%]
tests/test_verification.py::test_verification_lifecycle PASSED           [100%]

=============================== warnings summary ===============================
tests/test_mission.py::TestMission::test_mission_execution_lifecycle
tests/test_verification.py::test_verification_lifecycle
  /Users/bhushan/Documents/Projects/niyam/niyam/mission/reporter.py:172: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    report_sections.append(f"- **Generated:** `{datetime.utcnow().isoformat()}Z`")

tests/test_mission.py::TestMission::test_mission_execution_lifecycle
tests/test_verification.py::test_verification_lifecycle
  /Users/bhushan/Documents/Projects/niyam/niyam/mission/reporter.py:244: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    "timestamp": datetime.utcnow().isoformat() + "Z",

tests/test_mission.py::TestMission::test_mission_execution_lifecycle
tests/test_verification.py::test_verification_lifecycle
  /Users/bhushan/Documents/Projects/niyam/niyam/mission/reporter.py:273: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    "completed": datetime.utcnow().isoformat() + "Z",

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================= 107 passed, 6 warnings in 12.16s =======================

```

## Validation Check - format - 2026-05-30T06:25:10.432614Z
**Status:** ℹ SKIPPED — Not configured


## Validation Check - lint - 2026-05-30T06:25:10.432731Z
**Status:** ℹ SKIPPED — Not configured


## Validation Check - typecheck - 2026-05-30T06:25:10.432779Z
**Status:** ℹ SKIPPED — Not configured


## Validation Check - build - 2026-05-30T06:25:10.432820Z
**Status:** ℹ SKIPPED — Not configured


## Validation Run - 2026-05-30T06:25:23.007343Z
**Command:** `pytest`
**Exit Code:** `0`

### stdout
```
============================= test session starts ==============================
platform darwin -- Python 3.14.3, pytest-9.0.3, pluggy-1.6.0 -- /opt/homebrew/opt/python@3.14/bin/python3.14
cachedir: .pytest_cache
rootdir: /Users/bhushan/Documents/Projects/niyam/.niyam/runs/requirements-utils-20260530-115131/worktrees/T3
configfile: pyproject.toml
testpaths: tests
plugins: cov-7.1.0, pytest_tmp_files-0.0.2, anyio-4.13.0
collecting ... collected 107 items

tests/test_ci.py::test_non_interactive_fails_unapproved PASSED           [  0%]
tests/test_ci.py::test_non_interactive_auto_approve PASSED               [  1%]
tests/test_ci.py::test_remote_policy_fetching PASSED                     [  2%]
tests/test_ci.py::test_remote_policy_fallback PASSED                     [  3%]
tests/test_ci.py::test_ci_verify_strict_missing_evidence PASSED          [  4%]
tests/test_ci.py::test_ci_verify_non_strict_missing_evidence PASSED      [  5%]
tests/test_ci.py::test_ci_verify_write_violation PASSED                  [  6%]
tests/test_cli.py::TestCLI::test_version PASSED                          [  7%]
tests/test_cli.py::TestCLI::test_help PASSED                             [  8%]
tests/test_cli.py::TestCLI::test_context_help PASSED                     [  9%]
tests/test_cli.py::TestCLI::test_guard_help PASSED                       [ 10%]
tests/test_cli.py::TestCLI::test_runtime_help PASSED                     [ 11%]
tests/test_cli.py::TestCLI::test_policy_help PASSED                      [ 12%]
tests/test_context.py::TestContextRefresh::test_context_refresh_creates_architecture PASSED [ 13%]
tests/test_context.py::TestContextRefresh::test_context_refresh_creates_validation PASSED [ 14%]
tests/test_context.py::TestContextRefresh::test_context_refresh_detects_python PASSED [ 14%]
tests/test_context.py::TestContextRefresh::test_context_refresh_detects_node PASSED [ 15%]
tests/test_context.py::TestContextRefresh::test_context_refresh_preserves_manual_section PASSED [ 16%]
tests/test_dashboard.py::test_dashboard_rendering PASSED                 [ 17%]
tests/test_dashboard.py::test_dashboard_watch_mode PASSED                [ 18%]
tests/test_doctor.py::TestDoctor::test_doctor_passes_on_fresh_init PASSED [ 19%]
tests/test_doctor.py::TestDoctor::test_doctor_fails_without_niyam PASSED [ 20%]
tests/test_doctor.py::TestDoctor::test_doctor_detects_missing_files PASSED [ 21%]
tests/test_doctor.py::TestDoctor::test_doctor_detects_invalid_yaml PASSED [ 22%]
tests/test_doctor_enhanced.py::test_doctor_runtimes_in_path PASSED       [ 23%]
tests/test_doctor_enhanced.py::test_doctor_agents_validity PASSED        [ 24%]
tests/test_doctor_enhanced.py::test_doctor_validation_commands PASSED    [ 25%]
tests/test_doctor_enhanced.py::test_doctor_git_status_dirty PASSED       [ 26%]
tests/test_fleet.py::test_fleet_parallel_execution PASSED                [ 27%]
tests/test_fleet.py::test_fleet_dependency_failure PASSED                [ 28%]
tests/test_fleet.py::test_fleet_worktree_fallback_when_no_git PASSED     [ 28%]
tests/test_guard.py::TestGuard::test_guard_enable PASSED                 [ 29%]
tests/test_guard.py::TestGuard::test_guard_disable PASSED                [ 30%]
tests/test_guard.py::TestGuard::test_guard_careful_adds_warn_list PASSED [ 31%]
tests/test_guard.py::TestGuard::test_guard_freeze_adds_path PASSED       [ 32%]
tests/test_guard.py::TestGuard::test_guard_freeze_enables_guard PASSED   [ 33%]
tests/test_guardrails.py::test_path_write_denial_and_revert PASSED       [ 34%]
tests/test_hooks.py::test_hooks_lifecycle_triggers PASSED                [ 35%]
tests/test_init.py::TestInit::test_init_creates_niyam_directory PASSED   [ 36%]
tests/test_init.py::TestInit::test_init_creates_mvp_directories PASSED   [ 37%]
tests/test_init.py::TestInit::test_init_creates_niyam_yaml PASSED        [ 38%]
tests/test_init.py::TestInit::test_init_creates_agents PASSED            [ 39%]
tests/test_init.py::TestInit::test_init_creates_skills PASSED            [ 40%]
tests/test_init.py::TestInit::test_init_creates_commands PASSED          [ 41%]
tests/test_init.py::TestInit::test_init_creates_policies PASSED          [ 42%]
tests/test_init.py::TestInit::test_init_fails_if_already_exists PASSED   [ 42%]
tests/test_init.py::TestInit::test_init_force_overwrites PASSED          [ 43%]
tests/test_init.py::TestInit::test_init_dry_run_creates_nothing PASSED   [ 44%]
tests/test_init.py::TestInit::test_init_with_claude_runtime PASSED       [ 45%]
tests/test_init.py::TestInit::test_init_invalid_profile_fails PASSED     [ 46%]
tests/test_init.py::TestInit::test_init_backend_profile PASSED           [ 47%]
tests/test_init.py::TestInit::test_init_frontend_profile PASSED          [ 48%]
tests/test_memory.py::TestMemory::test_memory_show PASSED                [ 49%]
tests/test_memory.py::TestMemory::test_memory_add PASSED                 [ 50%]
tests/test_memory.py::TestMemory::test_memory_clear PASSED               [ 51%]
tests/test_memory.py::TestMemory::test_memory_sync_propagates_to_runtimes PASSED [ 52%]
tests/test_mission.py::TestMission::test_mission_plan_creates_files PASSED [ 53%]
tests/test_mission.py::TestMission::test_mission_approve PASSED          [ 54%]
tests/test_mission.py::TestMission::test_mission_execution_lifecycle PASSED [ 55%]
tests/test_mission.py::TestMission::test_mission_pause_resume PASSED     [ 56%]
tests/test_mission.py::TestMission::test_mission_plan_strict PASSED      [ 57%]
tests/test_multi_runtime.py::test_planner_prompt_contains_runtime PASSED [ 57%]
tests/test_multi_runtime.py::test_planner_parses_runtime_field PASSED    [ 58%]
tests/test_multi_runtime.py::test_executor_resolves_task_runtime PASSED  [ 59%]
tests/test_packs.py::TestPacks::test_list_packs PASSED                   [ 60%]
tests/test_packs.py::TestPacks::test_add_pack_copies_files PASSED        [ 61%]
tests/test_packs.py::TestPacks::test_add_pack_conflict PASSED            [ 62%]
tests/test_packs.py::TestPacks::test_remove_pack PASSED                  [ 63%]
tests/test_packs.py::TestPacks::test_sync_packs PASSED                   [ 64%]
tests/test_pr.py::test_pr_review_mocked PASSED                           [ 65%]
tests/test_pr.py::test_pr_create_mocked PASSED                           [ 66%]
tests/test_recovery.py::test_mission_skip_unblocks_downstream PASSED     [ 67%]
tests/test_recovery.py::test_mission_retry_requeues_tasks PASSED         [ 68%]
tests/test_recovery.py::test_mission_rollback_git_checkout PASSED        [ 69%]
tests/test_remediation.py::test_bash_sh_blocked PASSED                   [ 70%]
tests/test_remediation.py::test_report_fails_on_validation_failure PASSED [ 71%]
tests/test_remediation.py::test_context_diff_ignores_manual_sections PASSED [ 71%]
tests/test_remediation.py::test_claude_hook_script_formatting_and_imports PASSED [ 72%]
tests/test_remediation.py::test_validate_mission_plan_cycle PASSED       [ 73%]
tests/test_remediation.py::test_validate_mission_plan_unknown_dependency PASSED [ 74%]
tests/test_remediation.py::test_writes_files_false_violation_and_revert PASSED [ 75%]
tests/test_review.py::TestReview::test_get_git_diff_untracked_file PASSED [ 76%]
tests/test_review.py::TestReview::test_run_review_engineering_lens PASSED [ 77%]
tests/test_review.py::TestReview::test_run_review_adversarial_mode PASSED [ 78%]
tests/test_review.py::TestReview::test_get_git_diff_file_size_limit PASSED [ 79%]
tests/test_review.py::TestReview::test_get_git_diff_budget_limit PASSED  [ 80%]
tests/test_review.py::TestReview::test_get_git_diff_skip_binary_files PASSED [ 81%]
tests/test_review.py::TestReview::test_get_git_diff_redact_secrets PASSED [ 82%]
tests/test_run_composite.py::test_run_composite_command_file PASSED      [ 83%]
tests/test_run_composite.py::test_run_composite_command_inline_string PASSED [ 84%]
tests/test_setup.py::test_setup_wizard_fresh_initialization PASSED       [ 85%]
tests/test_sync.py::TestClaudeSync::test_claude_sync_creates_claude_md PASSED [ 85%]
tests/test_sync.py::TestClaudeSync::test_claude_sync_creates_claude_dir PASSED [ 86%]
tests/test_sync.py::TestClaudeSync::test_claude_sync_creates_agents PASSED [ 87%]
tests/test_sync.py::TestClaudeSync::test_claude_sync_creates_hooks PASSED [ 88%]
tests/test_sync.py::TestClaudeSync::test_claude_sync_creates_settings PASSED [ 89%]
tests/test_sync.py::TestClaudeSync::test_claude_md_contains_policies PASSED [ 90%]
tests/test_sync.py::TestCodexSync::test_codex_sync_creates_agents_md PASSED [ 91%]
tests/test_sync.py::TestCodexSync::test_agents_md_contains_policies PASSED [ 92%]
tests/test_sync.py::TestGeminiSync::test_gemini_sync_creates_gemini_md PASSED [ 93%]
tests/test_sync.py::TestGeminiSync::test_gemini_sync_creates_gemini_dir PASSED [ 94%]
tests/test_sync.py::TestGeminiSync::test_gemini_md_contains_policies PASSED [ 95%]
tests/test_sync.py::TestRuntimeAdd::test_runtime_add_updates_config PASSED [ 96%]
tests/test_sync.py::TestRuntimeAdd::test_runtime_add_duplicate_is_safe PASSED [ 97%]
tests/test_templates.py::test_builtin_template_planning PASSED           [ 98%]
tests/test_templates.py::test_custom_template_planning PASSED            [ 99%]
tests/test_verification.py::test_verification_lifecycle PASSED           [100%]

=============================== warnings summary ===============================
tests/test_mission.py::TestMission::test_mission_execution_lifecycle
tests/test_verification.py::test_verification_lifecycle
  /Users/bhushan/Documents/Projects/niyam/niyam/mission/reporter.py:172: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    report_sections.append(f"- **Generated:** `{datetime.utcnow().isoformat()}Z`")

tests/test_mission.py::TestMission::test_mission_execution_lifecycle
tests/test_verification.py::test_verification_lifecycle
  /Users/bhushan/Documents/Projects/niyam/niyam/mission/reporter.py:244: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    "timestamp": datetime.utcnow().isoformat() + "Z",

tests/test_mission.py::TestMission::test_mission_execution_lifecycle
tests/test_verification.py::test_verification_lifecycle
  /Users/bhushan/Documents/Projects/niyam/niyam/mission/reporter.py:273: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    "completed": datetime.utcnow().isoformat() + "Z",

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================= 107 passed, 6 warnings in 11.66s =======================

```

## Validation Check - format - 2026-05-30T06:25:23.624914Z
**Status:** ℹ SKIPPED — Not configured


## Validation Check - lint - 2026-05-30T06:25:23.625038Z
**Status:** ℹ SKIPPED — Not configured


## Validation Check - typecheck - 2026-05-30T06:25:23.625097Z
**Status:** ℹ SKIPPED — Not configured


## Validation Check - build - 2026-05-30T06:25:23.625149Z
**Status:** ℹ SKIPPED — Not configured


## Validation Run - 2026-05-30T06:25:36.804785Z
**Command:** `pytest`
**Exit Code:** `0`

### stdout
```
============================= test session starts ==============================
platform darwin -- Python 3.14.3, pytest-9.0.3, pluggy-1.6.0 -- /opt/homebrew/opt/python@3.14/bin/python3.14
cachedir: .pytest_cache
rootdir: /Users/bhushan/Documents/Projects/niyam/.niyam/runs/requirements-utils-20260530-115131/worktrees/T4
configfile: pyproject.toml
testpaths: tests
plugins: cov-7.1.0, pytest_tmp_files-0.0.2, anyio-4.13.0
collecting ... collected 107 items

tests/test_ci.py::test_non_interactive_fails_unapproved PASSED           [  0%]
tests/test_ci.py::test_non_interactive_auto_approve PASSED               [  1%]
tests/test_ci.py::test_remote_policy_fetching PASSED                     [  2%]
tests/test_ci.py::test_remote_policy_fallback PASSED                     [  3%]
tests/test_ci.py::test_ci_verify_strict_missing_evidence PASSED          [  4%]
tests/test_ci.py::test_ci_verify_non_strict_missing_evidence PASSED      [  5%]
tests/test_ci.py::test_ci_verify_write_violation PASSED                  [  6%]
tests/test_cli.py::TestCLI::test_version PASSED                          [  7%]
tests/test_cli.py::TestCLI::test_help PASSED                             [  8%]
tests/test_cli.py::TestCLI::test_context_help PASSED                     [  9%]
tests/test_cli.py::TestCLI::test_guard_help PASSED                       [ 10%]
tests/test_cli.py::TestCLI::test_runtime_help PASSED                     [ 11%]
tests/test_cli.py::TestCLI::test_policy_help PASSED                      [ 12%]
tests/test_context.py::TestContextRefresh::test_context_refresh_creates_architecture PASSED [ 13%]
tests/test_context.py::TestContextRefresh::test_context_refresh_creates_validation PASSED [ 14%]
tests/test_context.py::TestContextRefresh::test_context_refresh_detects_python PASSED [ 14%]
tests/test_context.py::TestContextRefresh::test_context_refresh_detects_node PASSED [ 15%]
tests/test_context.py::TestContextRefresh::test_context_refresh_preserves_manual_section PASSED [ 16%]
tests/test_dashboard.py::test_dashboard_rendering PASSED                 [ 17%]
tests/test_dashboard.py::test_dashboard_watch_mode PASSED                [ 18%]
tests/test_doctor.py::TestDoctor::test_doctor_passes_on_fresh_init PASSED [ 19%]
tests/test_doctor.py::TestDoctor::test_doctor_fails_without_niyam PASSED [ 20%]
tests/test_doctor.py::TestDoctor::test_doctor_detects_missing_files PASSED [ 21%]
tests/test_doctor.py::TestDoctor::test_doctor_detects_invalid_yaml PASSED [ 22%]
tests/test_doctor_enhanced.py::test_doctor_runtimes_in_path PASSED       [ 23%]
tests/test_doctor_enhanced.py::test_doctor_agents_validity PASSED        [ 24%]
tests/test_doctor_enhanced.py::test_doctor_validation_commands PASSED    [ 25%]
tests/test_doctor_enhanced.py::test_doctor_git_status_dirty PASSED       [ 26%]
tests/test_fleet.py::test_fleet_parallel_execution PASSED                [ 27%]
tests/test_fleet.py::test_fleet_dependency_failure PASSED                [ 28%]
tests/test_fleet.py::test_fleet_worktree_fallback_when_no_git PASSED     [ 28%]
tests/test_guard.py::TestGuard::test_guard_enable PASSED                 [ 29%]
tests/test_guard.py::TestGuard::test_guard_disable PASSED                [ 30%]
tests/test_guard.py::TestGuard::test_guard_careful_adds_warn_list PASSED [ 31%]
tests/test_guard.py::TestGuard::test_guard_freeze_adds_path PASSED       [ 32%]
tests/test_guard.py::TestGuard::test_guard_freeze_enables_guard PASSED   [ 33%]
tests/test_guardrails.py::test_path_write_denial_and_revert PASSED       [ 34%]
tests/test_hooks.py::test_hooks_lifecycle_triggers PASSED                [ 35%]
tests/test_init.py::TestInit::test_init_creates_niyam_directory PASSED   [ 36%]
tests/test_init.py::TestInit::test_init_creates_mvp_directories PASSED   [ 37%]
tests/test_init.py::TestInit::test_init_creates_niyam_yaml PASSED        [ 38%]
tests/test_init.py::TestInit::test_init_creates_agents PASSED            [ 39%]
tests/test_init.py::TestInit::test_init_creates_skills PASSED            [ 40%]
tests/test_init.py::TestInit::test_init_creates_commands PASSED          [ 41%]
tests/test_init.py::TestInit::test_init_creates_policies PASSED          [ 42%]
tests/test_init.py::TestInit::test_init_fails_if_already_exists PASSED   [ 42%]
tests/test_init.py::TestInit::test_init_force_overwrites PASSED          [ 43%]
tests/test_init.py::TestInit::test_init_dry_run_creates_nothing PASSED   [ 44%]
tests/test_init.py::TestInit::test_init_with_claude_runtime PASSED       [ 45%]
tests/test_init.py::TestInit::test_init_invalid_profile_fails PASSED     [ 46%]
tests/test_init.py::TestInit::test_init_backend_profile PASSED           [ 47%]
tests/test_init.py::TestInit::test_init_frontend_profile PASSED          [ 48%]
tests/test_memory.py::TestMemory::test_memory_show PASSED                [ 49%]
tests/test_memory.py::TestMemory::test_memory_add PASSED                 [ 50%]
tests/test_memory.py::TestMemory::test_memory_clear PASSED               [ 51%]
tests/test_memory.py::TestMemory::test_memory_sync_propagates_to_runtimes PASSED [ 52%]
tests/test_mission.py::TestMission::test_mission_plan_creates_files PASSED [ 53%]
tests/test_mission.py::TestMission::test_mission_approve PASSED          [ 54%]
tests/test_mission.py::TestMission::test_mission_execution_lifecycle PASSED [ 55%]
tests/test_mission.py::TestMission::test_mission_pause_resume PASSED     [ 56%]
tests/test_mission.py::TestMission::test_mission_plan_strict PASSED      [ 57%]
tests/test_multi_runtime.py::test_planner_prompt_contains_runtime PASSED [ 57%]
tests/test_multi_runtime.py::test_planner_parses_runtime_field PASSED    [ 58%]
tests/test_multi_runtime.py::test_executor_resolves_task_runtime PASSED  [ 59%]
tests/test_packs.py::TestPacks::test_list_packs PASSED                   [ 60%]
tests/test_packs.py::TestPacks::test_add_pack_copies_files PASSED        [ 61%]
tests/test_packs.py::TestPacks::test_add_pack_conflict PASSED            [ 62%]
tests/test_packs.py::TestPacks::test_remove_pack PASSED                  [ 63%]
tests/test_packs.py::TestPacks::test_sync_packs PASSED                   [ 64%]
tests/test_pr.py::test_pr_review_mocked PASSED                           [ 65%]
tests/test_pr.py::test_pr_create_mocked PASSED                           [ 66%]
tests/test_recovery.py::test_mission_skip_unblocks_downstream PASSED     [ 67%]
tests/test_recovery.py::test_mission_retry_requeues_tasks PASSED         [ 68%]
tests/test_recovery.py::test_mission_rollback_git_checkout PASSED        [ 69%]
tests/test_remediation.py::test_bash_sh_blocked PASSED                   [ 70%]
tests/test_remediation.py::test_report_fails_on_validation_failure PASSED [ 71%]
tests/test_remediation.py::test_context_diff_ignores_manual_sections PASSED [ 71%]
tests/test_remediation.py::test_claude_hook_script_formatting_and_imports PASSED [ 72%]
tests/test_remediation.py::test_validate_mission_plan_cycle PASSED       [ 73%]
tests/test_remediation.py::test_validate_mission_plan_unknown_dependency PASSED [ 74%]
tests/test_remediation.py::test_writes_files_false_violation_and_revert PASSED [ 75%]
tests/test_review.py::TestReview::test_get_git_diff_untracked_file PASSED [ 76%]
tests/test_review.py::TestReview::test_run_review_engineering_lens PASSED [ 77%]
tests/test_review.py::TestReview::test_run_review_adversarial_mode PASSED [ 78%]
tests/test_review.py::TestReview::test_get_git_diff_file_size_limit PASSED [ 79%]
tests/test_review.py::TestReview::test_get_git_diff_budget_limit PASSED  [ 80%]
tests/test_review.py::TestReview::test_get_git_diff_skip_binary_files PASSED [ 81%]
tests/test_review.py::TestReview::test_get_git_diff_redact_secrets PASSED [ 82%]
tests/test_run_composite.py::test_run_composite_command_file PASSED      [ 83%]
tests/test_run_composite.py::test_run_composite_command_inline_string PASSED [ 84%]
tests/test_setup.py::test_setup_wizard_fresh_initialization PASSED       [ 85%]
tests/test_sync.py::TestClaudeSync::test_claude_sync_creates_claude_md PASSED [ 85%]
tests/test_sync.py::TestClaudeSync::test_claude_sync_creates_claude_dir PASSED [ 86%]
tests/test_sync.py::TestClaudeSync::test_claude_sync_creates_agents PASSED [ 87%]
tests/test_sync.py::TestClaudeSync::test_claude_sync_creates_hooks PASSED [ 88%]
tests/test_sync.py::TestClaudeSync::test_claude_sync_creates_settings PASSED [ 89%]
tests/test_sync.py::TestClaudeSync::test_claude_md_contains_policies PASSED [ 90%]
tests/test_sync.py::TestCodexSync::test_codex_sync_creates_agents_md PASSED [ 91%]
tests/test_sync.py::TestCodexSync::test_agents_md_contains_policies PASSED [ 92%]
tests/test_sync.py::TestGeminiSync::test_gemini_sync_creates_gemini_md PASSED [ 93%]
tests/test_sync.py::TestGeminiSync::test_gemini_sync_creates_gemini_dir PASSED [ 94%]
tests/test_sync.py::TestGeminiSync::test_gemini_md_contains_policies PASSED [ 95%]
tests/test_sync.py::TestRuntimeAdd::test_runtime_add_updates_config PASSED [ 96%]
tests/test_sync.py::TestRuntimeAdd::test_runtime_add_duplicate_is_safe PASSED [ 97%]
tests/test_templates.py::test_builtin_template_planning PASSED           [ 98%]
tests/test_templates.py::test_custom_template_planning PASSED            [ 99%]
tests/test_verification.py::test_verification_lifecycle PASSED           [100%]

=============================== warnings summary ===============================
tests/test_mission.py::TestMission::test_mission_execution_lifecycle
tests/test_verification.py::test_verification_lifecycle
  /Users/bhushan/Documents/Projects/niyam/niyam/mission/reporter.py:172: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    report_sections.append(f"- **Generated:** `{datetime.utcnow().isoformat()}Z`")

tests/test_mission.py::TestMission::test_mission_execution_lifecycle
tests/test_verification.py::test_verification_lifecycle
  /Users/bhushan/Documents/Projects/niyam/niyam/mission/reporter.py:244: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    "timestamp": datetime.utcnow().isoformat() + "Z",

tests/test_mission.py::TestMission::test_mission_execution_lifecycle
tests/test_verification.py::test_verification_lifecycle
  /Users/bhushan/Documents/Projects/niyam/niyam/mission/reporter.py:273: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    "completed": datetime.utcnow().isoformat() + "Z",

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================= 107 passed, 6 warnings in 12.23s =======================

```

## Validation Check - format - 2026-05-30T06:25:37.178584Z
**Status:** ℹ SKIPPED — Not configured


## Validation Check - lint - 2026-05-30T06:25:37.178684Z
**Status:** ℹ SKIPPED — Not configured


## Validation Check - typecheck - 2026-05-30T06:25:37.178732Z
**Status:** ℹ SKIPPED — Not configured


## Validation Check - build - 2026-05-30T06:25:37.178780Z
**Status:** ℹ SKIPPED — Not configured


## Validation Run - 2026-05-30T06:25:51.791487Z
**Command:** `pytest`
**Exit Code:** `0`

### stdout
```
============================= test session starts ==============================
platform darwin -- Python 3.14.3, pytest-9.0.3, pluggy-1.6.0 -- /opt/homebrew/opt/python@3.14/bin/python3.14
cachedir: .pytest_cache
rootdir: /Users/bhushan/Documents/Projects/niyam/.niyam/runs/requirements-utils-20260530-115131/worktrees/T5
configfile: pyproject.toml
testpaths: tests
plugins: cov-7.1.0, pytest_tmp_files-0.0.2, anyio-4.13.0
collecting ... collected 107 items

tests/test_ci.py::test_non_interactive_fails_unapproved PASSED           [  0%]
tests/test_ci.py::test_non_interactive_auto_approve PASSED               [  1%]
tests/test_ci.py::test_remote_policy_fetching PASSED                     [  2%]
tests/test_ci.py::test_remote_policy_fallback PASSED                     [  3%]
tests/test_ci.py::test_ci_verify_strict_missing_evidence PASSED          [  4%]
tests/test_ci.py::test_ci_verify_non_strict_missing_evidence PASSED      [  5%]
tests/test_ci.py::test_ci_verify_write_violation PASSED                  [  6%]
tests/test_cli.py::TestCLI::test_version PASSED                          [  7%]
tests/test_cli.py::TestCLI::test_help PASSED                             [  8%]
tests/test_cli.py::TestCLI::test_context_help PASSED                     [  9%]
tests/test_cli.py::TestCLI::test_guard_help PASSED                       [ 10%]
tests/test_cli.py::TestCLI::test_runtime_help PASSED                     [ 11%]
tests/test_cli.py::TestCLI::test_policy_help PASSED                      [ 12%]
tests/test_context.py::TestContextRefresh::test_context_refresh_creates_architecture PASSED [ 13%]
tests/test_context.py::TestContextRefresh::test_context_refresh_creates_validation PASSED [ 14%]
tests/test_context.py::TestContextRefresh::test_context_refresh_detects_python PASSED [ 14%]
tests/test_context.py::TestContextRefresh::test_context_refresh_detects_node PASSED [ 15%]
tests/test_context.py::TestContextRefresh::test_context_refresh_preserves_manual_section PASSED [ 16%]
tests/test_dashboard.py::test_dashboard_rendering PASSED                 [ 17%]
tests/test_dashboard.py::test_dashboard_watch_mode PASSED                [ 18%]
tests/test_doctor.py::TestDoctor::test_doctor_passes_on_fresh_init PASSED [ 19%]
tests/test_doctor.py::TestDoctor::test_doctor_fails_without_niyam PASSED [ 20%]
tests/test_doctor.py::TestDoctor::test_doctor_detects_missing_files PASSED [ 21%]
tests/test_doctor.py::TestDoctor::test_doctor_detects_invalid_yaml PASSED [ 22%]
tests/test_doctor_enhanced.py::test_doctor_runtimes_in_path PASSED       [ 23%]
tests/test_doctor_enhanced.py::test_doctor_agents_validity PASSED        [ 24%]
tests/test_doctor_enhanced.py::test_doctor_validation_commands PASSED    [ 25%]
tests/test_doctor_enhanced.py::test_doctor_git_status_dirty PASSED       [ 26%]
tests/test_fleet.py::test_fleet_parallel_execution PASSED                [ 27%]
tests/test_fleet.py::test_fleet_dependency_failure PASSED                [ 28%]
tests/test_fleet.py::test_fleet_worktree_fallback_when_no_git PASSED     [ 28%]
tests/test_guard.py::TestGuard::test_guard_enable PASSED                 [ 29%]
tests/test_guard.py::TestGuard::test_guard_disable PASSED                [ 30%]
tests/test_guard.py::TestGuard::test_guard_careful_adds_warn_list PASSED [ 31%]
tests/test_guard.py::TestGuard::test_guard_freeze_adds_path PASSED       [ 32%]
tests/test_guard.py::TestGuard::test_guard_freeze_enables_guard PASSED   [ 33%]
tests/test_guardrails.py::test_path_write_denial_and_revert PASSED       [ 34%]
tests/test_hooks.py::test_hooks_lifecycle_triggers PASSED                [ 35%]
tests/test_init.py::TestInit::test_init_creates_niyam_directory PASSED   [ 36%]
tests/test_init.py::TestInit::test_init_creates_mvp_directories PASSED   [ 37%]
tests/test_init.py::TestInit::test_init_creates_niyam_yaml PASSED        [ 38%]
tests/test_init.py::TestInit::test_init_creates_agents PASSED            [ 39%]
tests/test_init.py::TestInit::test_init_creates_skills PASSED            [ 40%]
tests/test_init.py::TestInit::test_init_creates_commands PASSED          [ 41%]
tests/test_init.py::TestInit::test_init_creates_policies PASSED          [ 42%]
tests/test_init.py::TestInit::test_init_fails_if_already_exists PASSED   [ 42%]
tests/test_init.py::TestInit::test_init_force_overwrites PASSED          [ 43%]
tests/test_init.py::TestInit::test_init_dry_run_creates_nothing PASSED   [ 44%]
tests/test_init.py::TestInit::test_init_with_claude_runtime PASSED       [ 45%]
tests/test_init.py::TestInit::test_init_invalid_profile_fails PASSED     [ 46%]
tests/test_init.py::TestInit::test_init_backend_profile PASSED           [ 47%]
tests/test_init.py::TestInit::test_init_frontend_profile PASSED          [ 48%]
tests/test_memory.py::TestMemory::test_memory_show PASSED                [ 49%]
tests/test_memory.py::TestMemory::test_memory_add PASSED                 [ 50%]
tests/test_memory.py::TestMemory::test_memory_clear PASSED               [ 51%]
tests/test_memory.py::TestMemory::test_memory_sync_propagates_to_runtimes PASSED [ 52%]
tests/test_mission.py::TestMission::test_mission_plan_creates_files PASSED [ 53%]
tests/test_mission.py::TestMission::test_mission_approve PASSED          [ 54%]
tests/test_mission.py::TestMission::test_mission_execution_lifecycle PASSED [ 55%]
tests/test_mission.py::TestMission::test_mission_pause_resume PASSED     [ 56%]
tests/test_mission.py::TestMission::test_mission_plan_strict PASSED      [ 57%]
tests/test_multi_runtime.py::test_planner_prompt_contains_runtime PASSED [ 57%]
tests/test_multi_runtime.py::test_planner_parses_runtime_field PASSED    [ 58%]
tests/test_multi_runtime.py::test_executor_resolves_task_runtime PASSED  [ 59%]
tests/test_packs.py::TestPacks::test_list_packs PASSED                   [ 60%]
tests/test_packs.py::TestPacks::test_add_pack_copies_files PASSED        [ 61%]
tests/test_packs.py::TestPacks::test_add_pack_conflict PASSED            [ 62%]
tests/test_packs.py::TestPacks::test_remove_pack PASSED                  [ 63%]
tests/test_packs.py::TestPacks::test_sync_packs PASSED                   [ 64%]
tests/test_pr.py::test_pr_review_mocked PASSED                           [ 65%]
tests/test_pr.py::test_pr_create_mocked PASSED                           [ 66%]
tests/test_recovery.py::test_mission_skip_unblocks_downstream PASSED     [ 67%]
tests/test_recovery.py::test_mission_retry_requeues_tasks PASSED         [ 68%]
tests/test_recovery.py::test_mission_rollback_git_checkout PASSED        [ 69%]
tests/test_remediation.py::test_bash_sh_blocked PASSED                   [ 70%]
tests/test_remediation.py::test_report_fails_on_validation_failure PASSED [ 71%]
tests/test_remediation.py::test_context_diff_ignores_manual_sections PASSED [ 71%]
tests/test_remediation.py::test_claude_hook_script_formatting_and_imports PASSED [ 72%]
tests/test_remediation.py::test_validate_mission_plan_cycle PASSED       [ 73%]
tests/test_remediation.py::test_validate_mission_plan_unknown_dependency PASSED [ 74%]
tests/test_remediation.py::test_writes_files_false_violation_and_revert PASSED [ 75%]
tests/test_review.py::TestReview::test_get_git_diff_untracked_file PASSED [ 76%]
tests/test_review.py::TestReview::test_run_review_engineering_lens PASSED [ 77%]
tests/test_review.py::TestReview::test_run_review_adversarial_mode PASSED [ 78%]
tests/test_review.py::TestReview::test_get_git_diff_file_size_limit PASSED [ 79%]
tests/test_review.py::TestReview::test_get_git_diff_budget_limit PASSED  [ 80%]
tests/test_review.py::TestReview::test_get_git_diff_skip_binary_files PASSED [ 81%]
tests/test_review.py::TestReview::test_get_git_diff_redact_secrets PASSED [ 82%]
tests/test_run_composite.py::test_run_composite_command_file PASSED      [ 83%]
tests/test_run_composite.py::test_run_composite_command_inline_string PASSED [ 84%]
tests/test_setup.py::test_setup_wizard_fresh_initialization PASSED       [ 85%]
tests/test_sync.py::TestClaudeSync::test_claude_sync_creates_claude_md PASSED [ 85%]
tests/test_sync.py::TestClaudeSync::test_claude_sync_creates_claude_dir PASSED [ 86%]
tests/test_sync.py::TestClaudeSync::test_claude_sync_creates_agents PASSED [ 87%]
tests/test_sync.py::TestClaudeSync::test_claude_sync_creates_hooks PASSED [ 88%]
tests/test_sync.py::TestClaudeSync::test_claude_sync_creates_settings PASSED [ 89%]
tests/test_sync.py::TestClaudeSync::test_claude_md_contains_policies PASSED [ 90%]
tests/test_sync.py::TestCodexSync::test_codex_sync_creates_agents_md PASSED [ 91%]
tests/test_sync.py::TestCodexSync::test_agents_md_contains_policies PASSED [ 92%]
tests/test_sync.py::TestGeminiSync::test_gemini_sync_creates_gemini_md PASSED [ 93%]
tests/test_sync.py::TestGeminiSync::test_gemini_sync_creates_gemini_dir PASSED [ 94%]
tests/test_sync.py::TestGeminiSync::test_gemini_md_contains_policies PASSED [ 95%]
tests/test_sync.py::TestRuntimeAdd::test_runtime_add_updates_config PASSED [ 96%]
tests/test_sync.py::TestRuntimeAdd::test_runtime_add_duplicate_is_safe PASSED [ 97%]
tests/test_templates.py::test_builtin_template_planning PASSED           [ 98%]
tests/test_templates.py::test_custom_template_planning PASSED            [ 99%]
tests/test_verification.py::test_verification_lifecycle PASSED           [100%]

=============================== warnings summary ===============================
tests/test_mission.py::TestMission::test_mission_execution_lifecycle
tests/test_verification.py::test_verification_lifecycle
  /Users/bhushan/Documents/Projects/niyam/niyam/mission/reporter.py:172: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    report_sections.append(f"- **Generated:** `{datetime.utcnow().isoformat()}Z`")

tests/test_mission.py::TestMission::test_mission_execution_lifecycle
tests/test_verification.py::test_verification_lifecycle
  /Users/bhushan/Documents/Projects/niyam/niyam/mission/reporter.py:244: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    "timestamp": datetime.utcnow().isoformat() + "Z",

tests/test_mission.py::TestMission::test_mission_execution_lifecycle
tests/test_verification.py::test_verification_lifecycle
  /Users/bhushan/Documents/Projects/niyam/niyam/mission/reporter.py:273: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    "completed": datetime.utcnow().isoformat() + "Z",

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================= 107 passed, 6 warnings in 13.72s =======================

```


## Changes Made (Git Diff)

```diff
diff --git a/.niyam/context/architecture.md b/.niyam/context/architecture.md
index 1a777ca..f0442c4 100644
--- a/.niyam/context/architecture.md
+++ b/.niyam/context/architecture.md
@@ -1,8 +1,74 @@
-# Architecture
+# niyam — Architecture
 
-<!-- AUTO-GENERATED by niyam context refresh — run `niyam context refresh` to update. -->
+<!-- AUTO-GENERATED by niyam context refresh — edits below the manual section will be overwritten -->
 
-Architecture details will be populated when you run `niyam context refresh`.
+## Languages
+- Python
+
+## Dependency Versions
+- typer>=0.15.0,<1.0
+- rich>=13.0.0,<14.0
+- pydantic>=2.0.0,<3.0
+- pyyaml>=6.0,<7.0
+- jinja2>=3.1.0,<4.0
+- gitpython>=3.1.0,<4.0
+
+## Project Readme Summary
+```markdown
+# Niyam
+
+**Governed AI-development workspaces for Claude Code, Codex CLI, and future coding runtimes.**
+
+> One `.niyam/` source of truth. Many AI runtimes. Policy-driven autonomy. Evidence-backed delivery.
+
+## What is Niyam?
+
+Niyam turns any repository into a governed AI-development workspace with:
+
+- **Reusable agents** — specialized AI roles (backend, frontend, security, QA)
+- **Skills** — composable methodology packs (TDD, code review, planning)
+- **Commands** — structured workflows (`/implement`, `/review`, `/ship`)
+- **Guardrails** — command deny lists, approval gates, path restrictions
+- **Evidence** — audit trails for every AI-assisted session
+
+## Quick Start
+
+```bash
+# Install
+pip install -e .
+
+# Initialize a workspace
+cd your-project
+niyam init --profile fullstack --runtime claude
+
+# Add Codex as a second runtime
+niyam runtime add codex
+
+# Detect your stack
+niyam context refresh
+
+# Validate setup
+niyam policy validate
+niyam doctor
+
+# Sync changes to runtimes
+niyam sync
+```
+
+Then open Claude Code and use:
+```
+/implement add login validation
+/review
+/ship
+```
+
+## Commands
+
+| Command | Description |
+```
+
+## Test Directories
+- `tests/`
 
 ---
 
diff --git a/.niyam/context/validation.md b/.niyam/context/validation.md
index ac1ebe8..48a4c95 100644
--- a/.niyam/context/validation.md
+++ b/.niyam/context/validation.md
@@ -1,8 +1,21 @@
 # Validation Commands
 
-<!-- AUTO-GENERATED by niyam context refresh — run `niyam context refresh` to update. -->
+<!-- AUTO-GENERATED by niyam context refresh -->
 
-Validation commands will be populated when you run `niyam context refresh`.
+## Test
+```bash
+pytest
+```
+
+## Lint
+```bash
+ruff check .
+```
+
+## Format
+```bash
+ruff format --check .
+```
 
 ---
 
diff --git a/CLAUDE.md b/CLAUDE.md
index 6e2aa75..b4ca4e6 100644
--- a/CLAUDE.md
+++ b/CLAUDE.md
@@ -47,11 +47,77 @@ This project is managed by Niyam — a governed AI-development workspace.
 <!-- Common mistakes to avoid. -->
 
 
-# Architecture
+# niyam — Architecture
 
-<!-- AUTO-GENERATED by niyam context refresh — run `niyam context refresh` to update. -->
+<!-- AUTO-GENERATED by niyam context refresh — edits below the manual section will be overwritten -->
 
-Architecture details will be populated when you run `niyam context refresh`.
+## Languages
+- Python
+
+## Dependency Versions
+- typer>=0.15.0,<1.0
+- rich>=13.0.0,<14.0
+- pydantic>=2.0.0,<3.0
+- pyyaml>=6.0,<7.0
+- jinja2>=3.1.0,<4.0
+- gitpython>=3.1.0,<4.0
+
+## Project Readme Summary
+```markdown
+# Niyam
+
+**Governed AI-development workspaces for Claude Code, Codex CLI, and future coding runtimes.**
+
+> One `.niyam/` source of truth. Many AI runtimes. Policy-driven autonomy. Evidence-backed delivery.
+
+## What is Niyam?
+
+Niyam turns any repository into a governed AI-development workspace with:
+
+- **Reusable agents** — specialized AI roles (backend, frontend, security, QA)
+- **Skills** — composable methodology packs (TDD, code review, planning)
+- **Commands** — structured workflows (`/implement`, `/review`, `/ship`)
+- **Guardrails** — command deny lists, approval gates, path restrictions
+- **Evidence** — audit trails for every AI-assisted session
+
+## Quick Start
+
+```bash
+# Install
+pip install -e .
+
+# Initialize a workspace
+cd your-project
+niyam init --profile fullstack --runtime claude
+
+# Add Codex as a second runtime
+niyam runtime add codex
+
+# Detect your stack
+niyam context refresh
+
+# Validate setup
+niyam policy validate
+niyam doctor
+
+# Sync changes to runtimes
+niyam sync
+```
+
+Then open Claude Code and use:
+```
+/implement add login validation
+/review
+/ship
+```
+
+## Commands
+
+| Command | Description |
+```
+
+## Test Directories
+- `tests/`
 
 ---
 
@@ -60,9 +126,22 @@ Architecture details will be populated when you run `niyam context refresh`.
 
 # Validation Commands
 
-<!-- AUTO-GENERATED by niyam context refresh — run `niyam context refresh` to update. -->
+<!-- AUTO-GENERATED by niyam context refresh -->
+
+## Test
+```bash
+pytest
+```
+
+## Lint
+```bash
+ruff check .
+```
 
-Validation commands will be populated when you run `niyam context refresh`.
+## Format
+```bash
+ruff format --check .
+```
 
 ---
 
diff --git a/niyam/cli.py b/niyam/cli.py
index f7e7c5f..ebde9d1 100644
--- a/niyam/cli.py
+++ b/niyam/cli.py
@@ -3,7 +3,6 @@
 from __future__ import annotations
 
 from enum import Enum
-from pathlib import Path
 from typing import Annotated, Optional
 
 import typer
@@ -94,7 +93,6 @@ ci_app = typer.Typer(
 app.add_typer(ci_app)
 
 
-
 # ── Enums ──────────────────────────────────────────────────────────────
 
 
@@ -134,7 +132,11 @@ def version() -> None:
 def init(
     profile: Annotated[
         str,
-        typer.Option("--profile", "-p", help="Project profile to use (e.g., fullstack, backend, frontend, startup-saas, platform-engineering, governed-enterprise)."),
+        typer.Option(
+            "--profile",
+            "-p",
+            help="Project profile to use (e.g., fullstack, backend, frontend, startup-saas, platform-engineering, governed-enterprise).",
+        ),
     ] = "fullstack",
     runtime: Annotated[
         Optional[Runtime],
@@ -177,15 +179,22 @@ def run(
     ] = None,
     auto_approve: Annotated[
         bool,
-        typer.Option("--auto-approve", help="Skip approval gate and execute immediately."),
+        typer.Option(
+            "--auto-approve", help="Skip approval gate and execute immediately."
+        ),
     ] = False,
     strict: Annotated[
         bool,
-        typer.Option("--strict", help="Fail if AI-powered planning fails, instead of falling back."),
+        typer.Option(
+            "--strict",
+            help="Fail if AI-powered planning fails, instead of falling back.",
+        ),
     ] = False,
     worktree: Annotated[
         Optional[bool],
-        typer.Option("--worktree/--no-worktree", help="Enable or disable git worktree isolation."),
+        typer.Option(
+            "--worktree/--no-worktree", help="Enable or disable git worktree isolation."
+        ),
     ] = None,
     template: Annotated[
         Optional[str],
@@ -207,17 +216,17 @@ def run(
     run_sync(runtime=None, console=console)
 
     # 3. Plan the mission
-    console.print(f"\n[cyan]3. Generating mission plan...[/]")
+    console.print("\n[cyan]3. Generating mission plan...[/]")
     mission_id = run_mission_plan(
         requirements_path=requirement,
         strict=strict,
         console=console,
         template=template,
-        runtime_override=runtime.value if runtime else None
+        runtime_override=runtime.value if runtime else None,
     )
 
     # 4. Approve plan
-    console.print(f"\n[cyan]4. Checking plan approval...[/]")
+    console.print("\n[cyan]4. Checking plan approval...[/]")
     run_mission_approve(console=console, interactive=not auto_approve)
 
     # 5. Start execution
@@ -226,7 +235,7 @@ def run(
         parallel=parallel,
         worktree=worktree,
         non_interactive=auto_approve,
-        console=console
+        console=console,
     )
 
 
@@ -323,7 +332,10 @@ def review_pr(
     ] = ReviewMode.collaborative,
     token: Annotated[
         Optional[str],
-        typer.Option("--token", help="GitHub token (overrides GITHUB_TOKEN environment variable)."),
+        typer.Option(
+            "--token",
+            help="GitHub token (overrides GITHUB_TOKEN environment variable).",
+        ),
     ] = None,
 ) -> None:
     """Run a structured code review on a GitHub pull request."""
@@ -346,11 +358,19 @@ def review_pr(
 @pr_app.command("create")
 def pr_create(
     title: Annotated[str, typer.Option("--title", "-t", help="Pull Request title.")],
-    body: Annotated[Optional[str], typer.Option("--body", "-b", help="Pull Request body/description.")] = None,
-    base: Annotated[str, typer.Option("--base", help="Target branch for the pull request.")] = "main",
+    body: Annotated[
+        Optional[str],
+        typer.Option("--body", "-b", help="Pull Request body/description."),
+    ] = None,
+    base: Annotated[
+        str, typer.Option("--base", help="Target branch for the pull request.")
+    ] = "main",
     token: Annotated[
         Optional[str],
-        typer.Option("--token", help="GitHub token (overrides GITHUB_TOKEN environment variable)."),
+        typer.Option(
+            "--token",
+            help="GitHub token (overrides GITHUB_TOKEN environment variable).",
+        ),
     ] = None,
 ) -> None:
     """Push the active branch and create a GitHub pull request with evidence report attached."""
@@ -373,7 +393,9 @@ def pr_create(
 def dashboard(
     watch: Annotated[
         bool,
-        typer.Option("--watch", "-w", help="Periodically refresh the dashboard (live mode)."),
+        typer.Option(
+            "--watch", "-w", help="Periodically refresh the dashboard (live mode)."
+        ),
     ] = False,
 ) -> None:
     """Show real-time dashboard of the active or latest mission."""
@@ -528,7 +550,9 @@ def pack_list() -> None:
 @pack_app.command("add")
 def pack_add(
     name: Annotated[str, typer.Argument(help="Name of the pack to add.")],
-    force: Annotated[bool, typer.Option("--force", help="Overwrite existing files.")] = False,
+    force: Annotated[
+        bool, typer.Option("--force", help="Overwrite existing files.")
+    ] = False,
 ) -> None:
     """Install a pack into the workspace."""
     from niyam.core.packs import add_pack
@@ -541,7 +565,9 @@ def pack_add(
         if not root:
             raise NiyamConfigError("Not a Niyam workspace. Run 'niyam init' first.")
         add_pack(root, name, force=force, console=console)
-        console.print(f"[bold green]✓[/] Pack '[cyan]{name}[/]' successfully installed.")
+        console.print(
+            f"[bold green]✓[/] Pack '[cyan]{name}[/]' successfully installed."
+        )
         # Trigger run_sync to sync config/runtimes
         run_sync(runtime=None, console=console)
     except Exception as e:
@@ -604,7 +630,9 @@ def memory_show() -> None:
 
 @memory_app.command("add")
 def memory_add(
-    file: Annotated[str, typer.Argument(help="Memory file to append to (e.g. project-lessons).")],
+    file: Annotated[
+        str, typer.Argument(help="Memory file to append to (e.g. project-lessons).")
+    ],
     note: Annotated[str, typer.Argument(help="Note to append.")],
 ) -> None:
     """Append a note to a memory file."""
@@ -632,10 +660,15 @@ def memory_clear(
 
 @mission_app.command("plan")
 def mission_plan(
-    requirements: Annotated[str, typer.Argument(help="Path to requirements markdown file.")],
+    requirements: Annotated[
+        str, typer.Argument(help="Path to requirements markdown file.")
+    ],
     strict: Annotated[
         bool,
-        typer.Option("--strict", help="Fail if AI-powered planning fails, instead of falling back."),
+        typer.Option(
+            "--strict",
+            help="Fail if AI-powered planning fails, instead of falling back.",
+        ),
     ] = False,
     template: Annotated[
         Optional[str],
@@ -655,7 +688,7 @@ def mission_plan(
             strict=strict,
             console=console,
             template=template,
-            runtime_override=runtime.value if runtime else None
+            runtime_override=runtime.value if runtime else None,
         )
     except Exception as e:
         console.print(f"[bold red]Error:[/] {e}")
@@ -721,7 +754,9 @@ def mission_show() -> None:
         t_writes = "Yes" if t.get("writes_files", True) else "No"
         t_status = t.get("status", "pending")
         col = status_colors.get(t_status.lower(), "white")
-        table.add_row(t_id, t_title, t_agent, t_rt, t_deps, t_writes, f"[{col}]{t_status}[/]")
+        table.add_row(
+            t_id, t_title, t_agent, t_rt, t_deps, t_writes, f"[{col}]{t_status}[/]"
+        )
 
     console.print(Panel(table, border_style="magenta"))
 
@@ -730,7 +765,9 @@ def mission_show() -> None:
 def mission_dashboard(
     watch: Annotated[
         bool,
-        typer.Option("--watch", "-w", help="Periodically refresh the dashboard (live mode)."),
+        typer.Option(
+            "--watch", "-w", help="Periodically refresh the dashboard (live mode)."
+        ),
     ] = False,
 ) -> None:
     """Show real-time dashboard of the active or latest mission."""
@@ -765,9 +802,13 @@ def mission_validate_plan() -> None:
 
     try:
         validate_mission_plan(plan_path, repo_root)
-        console.print(f"[bold green]✓[/] Mission plan '{mission_id}' is valid and ready for approval.")
+        console.print(
+            f"[bold green]✓[/] Mission plan '{mission_id}' is valid and ready for approval."
+        )
     except PlanValidationError as e:
-        console.print(f"[bold red]❌ Mission plan validation failed with {len(e.errors)} error(s):[/]")
+        console.print(
+            f"[bold red]❌ Mission plan validation failed with {len(e.errors)} error(s):[/]"
+        )
         for err in e.errors:
             console.print(f"  • [red]{err}[/]")
         raise typer.Exit(1)
@@ -780,7 +821,11 @@ def mission_validate_plan() -> None:
 def mission_approve(
     interactive: Annotated[
         bool,
-        typer.Option("--interactive", "-i", help="Approve tasks interactively with option to edit the plan."),
+        typer.Option(
+            "--interactive",
+            "-i",
+            help="Approve tasks interactively with option to edit the plan.",
+        ),
     ] = False,
 ) -> None:
     """Approve the latest planned mission."""
@@ -793,27 +838,37 @@ def mission_approve(
         raise typer.Exit(1)
 
 
-
 @mission_app.command("start")
 def mission_start(
     parallel: Annotated[
         Optional[int],
-        typer.Option("--parallel", "-p", help="Override the number of parallel workers."),
+        typer.Option(
+            "--parallel", "-p", help="Override the number of parallel workers."
+        ),
     ] = None,
     worktree: Annotated[
         Optional[bool],
-        typer.Option("--worktree/--no-worktree", help="Enable or disable git worktree isolation."),
+        typer.Option(
+            "--worktree/--no-worktree", help="Enable or disable git worktree isolation."
+        ),
     ] = None,
     non_interactive: Annotated[
         bool,
-        typer.Option("--non-interactive", "--ci", help="Run in non-interactive (CI/CD) mode."),
+        typer.Option(
+            "--non-interactive", "--ci", help="Run in non-interactive (CI/CD) mode."
+        ),
     ] = False,
 ) -> None:
     """Start or resume the latest approved mission."""
     from niyam.mission.executor import run_mission_start
 
     try:
-        run_mission_start(parallel=parallel, worktree=worktree, non_interactive=non_interactive, console=console)
+        run_mission_start(
+            parallel=parallel,
+            worktree=worktree,
+            non_interactive=non_interactive,
+            console=console,
+        )
     except Exception as e:
         console.print(f"[bold red]Error:[/] {e}")
         raise typer.Exit(1)
@@ -847,22 +902,33 @@ def mission_pause() -> None:
 def mission_resume(
     parallel: Annotated[
         Optional[int],
-        typer.Option("--parallel", "-p", help="Override the number of parallel workers."),
+        typer.Option(
+            "--parallel", "-p", help="Override the number of parallel workers."
+        ),
     ] = None,
     worktree: Annotated[
         Optional[bool],
-        typer.Option("--worktree/--no-worktree", help="Enable or disable git worktree isolation."),
+        typer.Option(
+            "--worktree/--no-worktree", help="Enable or disable git worktree isolation."
+        ),
     ] = None,
     non_interactive: Annotated[
         bool,
-        typer.Option("--non-interactive", "--ci", help="Run in non-interactive (CI/CD) mode."),
+        typer.Option(
+            "--non-interactive", "--ci", help="Run in non-interactive (CI/CD) mode."
+        ),
     ] = False,
 ) -> None:
     """Resume a paused mission."""
     from niyam.mission.executor import run_mission_resume
 
     try:
-        run_mission_resume(parallel=parallel, worktree=worktree, non_interactive=non_interactive, console=console)
+        run_mission_resume(
+            parallel=parallel,
+            worktree=worktree,
+            non_interactive=non_interactive,
+            console=console,
+        )
     except Exception as e:
         console.print(f"[bold red]Error:[/] {e}")
         raise typer.Exit(1)
@@ -872,15 +938,21 @@ def mission_resume(
 def mission_retry(
     parallel: Annotated[
         Optional[int],
-        typer.Option("--parallel", "-p", help="Override the number of parallel workers."),
+        typer.Option(
+            "--parallel", "-p", help="Override the number of parallel workers."
+        ),
     ] = None,
     worktree: Annotated[
         Optional[bool],
-        typer.Option("--worktree/--no-worktree", help="Enable or disable git worktree isolation."),
+        typer.Option(
+            "--worktree/--no-worktree", help="Enable or disable git worktree isolation."
+        ),
     ] = None,
     non_interactive: Annotated[
         bool,
-        typer.Option("--non-interactive", "--ci", help="Run in non-interactive (CI/CD) mode."),
+        typer.Option(
+            "--non-interactive", "--ci", help="Run in non-interactive (CI/CD) mode."
+        ),
     ] = False,
 ) -> None:
     """Retry failed or skipped tasks of the latest mission."""
@@ -903,15 +975,21 @@ def mission_skip(
     task_id: Annotated[str, typer.Argument(help="ID of the task to skip.")],
     parallel: Annotated[
         Optional[int],
-        typer.Option("--parallel", "-p", help="Override the number of parallel workers."),
+        typer.Option(
+            "--parallel", "-p", help="Override the number of parallel workers."
+        ),
     ] = None,
     worktree: Annotated[
         Optional[bool],
-        typer.Option("--worktree/--no-worktree", help="Enable or disable git worktree isolation."),
+        typer.Option(
+            "--worktree/--no-worktree", help="Enable or disable git worktree isolation."
+        ),
     ] = None,
     non_interactive: Annotated[
         bool,
-        typer.Option("--non-interactive", "--ci", help="Run in non-interactive (CI/CD) mode."),
+        typer.Option(
+            "--non-interactive", "--ci", help="Run in non-interactive (CI/CD) mode."
+        ),
     ] = False,
 ) -> None:
     """Skip a specific task and resume the mission execution."""
@@ -956,7 +1034,9 @@ def mission_report() -> None:
 
 @mission_app.command("verify-report")
 def mission_verify_report(
-    evidence_file: Annotated[str, typer.Argument(help="Path to the evidence.md report to verify.")],
+    evidence_file: Annotated[
+        str, typer.Argument(help="Path to the evidence.md report to verify.")
+    ],
 ) -> None:
     """Verify the cryptographic integrity of an evidence report."""
     from niyam.mission.reporter import run_verify_report
@@ -972,11 +1052,16 @@ def mission_verify_report(
 def ci_verify(
     target: Annotated[
         str,
-        typer.Option("--target", "-t", help="Target branch to compare changes against."),
+        typer.Option(
+            "--target", "-t", help="Target branch to compare changes against."
+        ),
     ] = "main",
     strict: Annotated[
         bool,
-        typer.Option("--strict/--no-strict", help="Fail build on integrity warnings or missing evidence."),
+        typer.Option(
+            "--strict/--no-strict",
+            help="Fail build on integrity warnings or missing evidence.",
+        ),
     ] = True,
 ) -> None:
     """Verify cryptographic integrity, guardrails, and validation status for CI/CD."""
@@ -989,10 +1074,10 @@ def ci_verify(
         raise typer.Exit(1)
 
 
-
 def main() -> None:
     """CLI entry point catching NiyamError exceptions."""
     from niyam.core.errors import NiyamError
+
     try:
         app()
     except NiyamError as e:
diff --git a/niyam/core/ci.py b/niyam/core/ci.py
index 5c7445b..c75cdbe 100644
--- a/niyam/core/ci.py
+++ b/niyam/core/ci.py
@@ -3,36 +3,35 @@
 from __future__ import annotations
 
 import json
-import os
 import fnmatch
 import subprocess
 from datetime import datetime, timezone
-from pathlib import Path
 
-import yaml
 from rich.console import Console
 from rich.panel import Panel
-from rich.table import Table
 
 from niyam.core.config import (
     find_niyam_root,
     get_niyam_dir,
     load_project_config,
-    load_niyam_config,
 )
 from niyam.mission.planner import get_latest_mission_id
-from niyam.mission.reporter import run_verify_report, compute_sha256
+from niyam.mission.reporter import run_verify_report
 from niyam.policies.guard import load_security_policy
 
 
-def run_ci_verify(target_branch: str = "main", strict: bool = True, console: Console = None) -> None:
+def run_ci_verify(
+    target_branch: str = "main", strict: bool = True, console: Console = None
+) -> None:
     """Verify cryptographic integrity, guardrails, and validation status for CI/CD."""
     if console is None:
         console = Console()
 
     root = find_niyam_root()
     if root is None:
-        console.print("[bold red]❌ CI Validation Failed:[/] Not a Niyam workspace. Run [bold]niyam init[/] first.")
+        console.print(
+            "[bold red]❌ CI Validation Failed:[/] Not a Niyam workspace. Run [bold]niyam init[/] first."
+        )
         raise SystemExit(1)
 
     niyam_dir = get_niyam_dir(root)
@@ -45,7 +44,7 @@ def run_ci_verify(target_branch: str = "main", strict: bool = True, console: Con
     validation_status = "passed"
     failures = []
 
-    console.print(f"[cyan]Niyam CI/CD Verification[/]")
+    console.print("[cyan]Niyam CI/CD Verification[/]")
     console.print(f"Target Branch: [bold cyan]{target_branch}[/]")
     console.print(f"Strict Mode: [bold]{'Enabled' if strict else 'Disabled'}[/]")
     console.print(f"Latest Mission: [bold cyan]{mission_id or 'None'}[/]\n")
@@ -55,9 +54,13 @@ def run_ci_verify(target_branch: str = "main", strict: bool = True, console: Con
         if strict:
             failures.append("Evidence report (evidence.md) not found.")
             integrity_status = "failed"
-            console.print("[bold red]❌ Integrity check failed:[/] evidence.md not found in run directory.")
+            console.print(
+                "[bold red]❌ Integrity check failed:[/] evidence.md not found in run directory."
+            )
         else:
-            console.print("[bold yellow]⚠ Warning:[/] evidence.md not found. Skipping integrity checks (non-strict mode).")
+            console.print(
+                "[bold yellow]⚠ Warning:[/] evidence.md not found. Skipping integrity checks (non-strict mode)."
+            )
     else:
         console.print("[cyan]Verifying evidence report integrity...[/]")
         try:
@@ -66,7 +69,7 @@ def run_ci_verify(target_branch: str = "main", strict: bool = True, console: Con
             integrity_status = "passed"
         except SystemExit as e:
             if e.code != 0:
-                failures.append(f"Evidence integrity check failed.")
+                failures.append("Evidence integrity check failed.")
                 integrity_status = "failed"
             else:
                 integrity_status = "passed"
@@ -80,7 +83,9 @@ def run_ci_verify(target_branch: str = "main", strict: bool = True, console: Con
     try:
         # Check if it is a Git repository
         if not (root / ".git").exists():
-            console.print("[bold yellow]⚠ Warning:[/] Not a Git repository. Skipping diff policy checks.")
+            console.print(
+                "[bold yellow]⚠ Warning:[/] Not a Git repository. Skipping diff policy checks."
+            )
         else:
             # Get changes between HEAD and target branch
             res = subprocess.run(
@@ -102,7 +107,11 @@ def run_ci_verify(target_branch: str = "main", strict: bool = True, console: Con
                 changed_files = []
                 for line in res.stdout.splitlines():
                     f = line.strip()
-                    if f and not f.startswith(".niyam") and f not in ("evidence.md", "evidence.json"):
+                    if (
+                        f
+                        and not f.startswith(".niyam")
+                        and f not in ("evidence.md", "evidence.json")
+                    ):
                         changed_files.append(f)
 
                 # Load security policy
@@ -113,9 +122,13 @@ def run_ci_verify(target_branch: str = "main", strict: bool = True, console: Con
                 if deny_patterns or allow_patterns:
                     violated_files = []
                     for f in changed_files:
-                        if deny_patterns and any(fnmatch.fnmatch(f, pat) for pat in deny_patterns):
+                        if deny_patterns and any(
+                            fnmatch.fnmatch(f, pat) for pat in deny_patterns
+                        ):
                             violated_files.append((f, "Denied pattern matched"))
-                        elif allow_patterns and not any(fnmatch.fnmatch(f, pat) for pat in allow_patterns):
+                        elif allow_patterns and not any(
+                            fnmatch.fnmatch(f, pat) for pat in allow_patterns
+                        ):
                             violated_files.append((f, "Not in allow list"))
 
                     if violated_files:
@@ -123,13 +136,21 @@ def run_ci_verify(target_branch: str = "main", strict: bool = True, console: Con
                         for f, reason in violated_files:
                             err_msg = f"Write violation on {f} ({reason})"
                             failures.append(err_msg)
-                            console.print(f"[bold red]❌ Write Restriction Violation:[/] {f} - {reason}")
+                            console.print(
+                                f"[bold red]❌ Write Restriction Violation:[/] {f} - {reason}"
+                            )
                     else:
-                        console.print("[bold green]✓[/] Git diff conforms to write restriction policies.")
+                        console.print(
+                            "[bold green]✓[/] Git diff conforms to write restriction policies."
+                        )
                 else:
-                    console.print("[dim]No write restriction policies (deny/allow lists) defined.[/]")
+                    console.print(
+                        "[dim]No write restriction policies (deny/allow lists) defined.[/]"
+                    )
             else:
-                console.print("[bold yellow]⚠ Warning:[/] git diff execution failed. Skipping diff checks.")
+                console.print(
+                    "[bold yellow]⚠ Warning:[/] git diff execution failed. Skipping diff checks."
+                )
     except Exception as e:
         failures.append(f"Write restriction check encountered error: {e}")
         policy_status = "failed"
@@ -161,19 +182,27 @@ def run_ci_verify(target_branch: str = "main", strict: bool = True, console: Con
                 try:
                     res = safe_run_command(cmd, cwd=root, timeout=120)
                 except CommandSecurityError as e:
-                    failures.append(f"Validation command '{name}' blocked by security policy: {e}")
+                    failures.append(
+                        f"Validation command '{name}' blocked by security policy: {e}"
+                    )
                     validation_status = "failed"
                     console.print(f"[bold red]🛑 Validation '{name}' blocked:[/] {e}")
                     continue
 
                 if res.returncode != 0:
-                    failures.append(f"Validation command '{name}' failed with code {res.returncode}.")
+                    failures.append(
+                        f"Validation command '{name}' failed with code {res.returncode}."
+                    )
                     validation_status = "failed"
                     console.print(f"[bold red]❌ Validation failed for {name}[/]")
                     if res.stderr or res.stdout:
-                        console.print(f"[dim]Output snippet:\n{res.stderr or res.stdout}[/]")
+                        console.print(
+                            f"[dim]Output snippet:\n{res.stderr or res.stdout}[/]"
+                        )
                 else:
-                    console.print(f"[bold green]✓[/] Validation [green]{name}[/] passed.")
+                    console.print(
+                        f"[bold green]✓[/] Validation [green]{name}[/] passed."
+                    )
 
     # 4. Save JSON Report
     report_data = {
@@ -193,7 +222,7 @@ def run_ci_verify(target_branch: str = "main", strict: bool = True, console: Con
         console.print(f"[bold yellow]Warning: Failed to save CI report:[/] {e}")
 
     # Summary Panel
-    success = (len(failures) == 0)
+    success = len(failures) == 0
     summary_text = (
         f"Integrity check: [bold {'green]PASSED' if integrity_status == 'passed' else 'red]FAILED' if integrity_status == 'failed' else 'yellow]SKIPPED'}\n"
         f"Policy checks: [bold {'green]PASSED' if policy_status == 'passed' else 'red]FAILED'}\n"
@@ -201,16 +230,22 @@ def run_ci_verify(target_branch: str = "main", strict: bool = True, console: Con
     )
 
     if success:
-        console.print(Panel(
-            summary_text + "\n[bold green]✓ CI/CD Verification Successful. All gates passed![/]",
-            title="[bold green]CI/CD Verification Passed[/]",
-            border_style="green",
-        ))
+        console.print(
+            Panel(
+                summary_text
+                + "\n[bold green]✓ CI/CD Verification Successful. All gates passed![/]",
+                title="[bold green]CI/CD Verification Passed[/]",
+                border_style="green",
+            )
+        )
     else:
-        console.print(Panel(
-            summary_text + f"\n[bold red]❌ CI/CD Verification Failed with {len(failures)} error(s):[/]\n" +
-            "\n".join(f"  • {f}" for f in failures),
-            title="[bold red]CI/CD Verification Failed[/]",
-            border_style="red",
-        ))
+        console.print(
+            Panel(
+                summary_text
+                + f"\n[bold red]❌ CI/CD Verification Failed with {len(failures)} error(s):[/]\n"
+                + "\n".join(f"  • {f}" for f in failures),
+                title="[bold red]CI/CD Verification Failed[/]",
+                border_style="red",
+            )
+        )
         raise SystemExit(1)
diff --git a/niyam/core/config.py b/niyam/core/config.py
index 9009f34..a54991f 100644
--- a/niyam/core/config.py
+++ b/niyam/core/config.py
@@ -142,6 +142,7 @@ class EvidencePolicy(BaseModel):
 
 from pydantic import BaseModel, Field, AliasChoices
 
+
 class TaskValidationConfig(BaseModel):
     """Validation commands configuration for a task."""
 
@@ -162,13 +163,12 @@ class TaskContract(BaseModel):
     depends_on: list[str] = Field(default_factory=list)
     allowed_files: list[str] = Field(
         default_factory=lambda: ["*"],
-        validation_alias=AliasChoices("allowed_files", "files_allowed")
+        validation_alias=AliasChoices("allowed_files", "files_allowed"),
     )
     blocked_files: list[str] = Field(default_factory=list)
     writes_files: bool = True
     timeout_seconds: int = Field(
-        default=600,
-        validation_alias=AliasChoices("timeout_seconds", "timeout")
+        default=600, validation_alias=AliasChoices("timeout_seconds", "timeout")
     )
     risk: Literal["low", "medium", "high"] = "medium"
     objective: str = ""
@@ -179,9 +179,6 @@ class TaskContract(BaseModel):
     commit_sha: Optional[str] = None
 
 
-
-
-
 class MissionMeta(BaseModel):
     """Pydantic model for mission metadata."""
 
@@ -197,8 +194,6 @@ class MissionMeta(BaseModel):
     base_sha: Optional[str] = None
 
 
-
-
 class MissionPlan(BaseModel):
     """Pydantic model for the complete mission-plan.yaml schema."""
 
diff --git a/niyam/core/context.py b/niyam/core/context.py
index aabe331..fa4a598 100644
--- a/niyam/core/context.py
+++ b/niyam/core/context.py
@@ -81,15 +81,34 @@ VALIDATION_RULES: dict[str, dict] = {
 }
 
 SOURCE_DIR_CANDIDATES = [
-    "src", "lib", "app", "apps", "packages",
-    "services", "server", "client", "api",
-    "components", "pages", "views", "controllers",
-    "models", "utils", "helpers", "core",
+    "src",
+    "lib",
+    "app",
+    "apps",
+    "packages",
+    "services",
+    "server",
+    "client",
+    "api",
+    "components",
+    "pages",
+    "views",
+    "controllers",
+    "models",
+    "utils",
+    "helpers",
+    "core",
 ]
 
 TEST_DIR_CANDIDATES = [
-    "tests", "test", "__tests__", "spec", "specs",
-    "e2e", "integration", "cypress",
+    "tests",
+    "test",
+    "__tests__",
+    "spec",
+    "specs",
+    "e2e",
+    "integration",
+    "cypress",
 ]
 
 CI_FILES = [
@@ -129,7 +148,9 @@ def _extract_dependency_versions(repo_root: Path) -> list[str]:
             try:
                 with open(pyproject, "rb") as f:
                     data = tomllib.load(f)
-                poetry_deps = data.get("tool", {}).get("poetry", {}).get("dependencies", {})
+                poetry_deps = (
+                    data.get("tool", {}).get("poetry", {}).get("dependencies", {})
+                )
                 project_deps = data.get("project", {}).get("dependencies", [])
                 for name, ver in sorted(poetry_deps.items()):
                     if name != "python":
@@ -199,13 +220,15 @@ def _extract_db_schema(repo_root: Path) -> list[str]:
         if mig_path.is_dir():
             files = sorted([f.name for f in mig_path.glob("**/*") if f.is_file()])
             if files:
-                info.append(f"Database migrations found in {m_dir}/ ({len(files)} files)")
+                info.append(
+                    f"Database migrations found in {m_dir}/ ({len(files)} files)"
+                )
 
     for sql_name in ["schema.sql", "db.sql", "init.sql"]:
         sql_path = repo_root / sql_name
         if sql_path.exists():
             info.append(f"SQL Schema file found: {sql_name}")
-            
+
     return info
 
 
@@ -214,9 +237,16 @@ def _extract_api_routes(repo_root: Path) -> list[str]:
     for r_dir in ["api", "routes", "controllers"]:
         dir_path = repo_root / r_dir
         if dir_path.is_dir():
-            files = [str(f.relative_to(repo_root)) for f in dir_path.glob("**/*") if f.is_file() and f.suffix in (".py", ".js", ".ts", ".go", ".rs")]
+            files = [
+                str(f.relative_to(repo_root))
+                for f in dir_path.glob("**/*")
+                if f.is_file() and f.suffix in (".py", ".js", ".ts", ".go", ".rs")
+            ]
             if files:
-                routes.append(f"Routes / controllers in {r_dir}/: {', '.join(files[:10])}" + ("..." if len(files) > 10 else ""))
+                routes.append(
+                    f"Routes / controllers in {r_dir}/: {', '.join(files[:10])}"
+                    + ("..." if len(files) > 10 else "")
+                )
     return routes
 
 
@@ -386,12 +416,14 @@ def _generate_architecture_md(scan_result: dict, project_name: str) -> str:
             lines.append(f"- `{ci}`")
         lines.append("")
 
-    lines.extend([
-        "---",
-        "",
-        "<!-- MANUAL SECTION: Add your own architecture notes below this line -->",
-        "",
-    ])
+    lines.extend(
+        [
+            "---",
+            "",
+            "<!-- MANUAL SECTION: Add your own architecture notes below this line -->",
+            "",
+        ]
+    )
 
     return "\n".join(lines)
 
@@ -408,20 +440,22 @@ def _generate_validation_md(scan_result: dict) -> str:
     if scan_result["validation"]:
         for cmd_type, cmd in scan_result["validation"].items():
             lines.append(f"## {cmd_type.title()}")
-            lines.append(f"```bash")
+            lines.append("```bash")
             lines.append(f"{cmd}")
-            lines.append(f"```")
+            lines.append("```")
             lines.append("")
     else:
         lines.append("No validation commands detected. Add them manually.")
         lines.append("")
 
-    lines.extend([
-        "---",
-        "",
-        "<!-- MANUAL SECTION: Add your own validation commands below this line -->",
-        "",
-    ])
+    lines.extend(
+        [
+            "---",
+            "",
+            "<!-- MANUAL SECTION: Add your own validation commands below this line -->",
+            "",
+        ]
+    )
 
     return "\n".join(lines)
 
@@ -437,7 +471,9 @@ def _preserve_manual_section(existing_content: str, new_content: str) -> str:
         # Get everything after the marker line
         after_marker = existing_content[idx:]
         # Find the end of the marker line
-        newline_idx = after_marker.index("\n") if "\n" in after_marker else len(after_marker)
+        newline_idx = (
+            after_marker.index("\n") if "\n" in after_marker else len(after_marker)
+        )
         manual_section = after_marker[newline_idx:].strip()
 
     # If there's manual content, append it to the new content
@@ -445,7 +481,9 @@ def _preserve_manual_section(existing_content: str, new_content: str) -> str:
         if manual_marker in new_content:
             idx = new_content.index(manual_marker)
             after_marker = new_content[idx:]
-            newline_idx = after_marker.index("\n") if "\n" in after_marker else len(after_marker)
+            newline_idx = (
+                after_marker.index("\n") if "\n" in after_marker else len(after_marker)
+            )
             marker_line = after_marker[: newline_idx + 1]
             return new_content[:idx] + marker_line + "\n" + manual_section + "\n"
 
@@ -456,7 +494,9 @@ def run_context_refresh(console: Console) -> None:
     """Scan the repo and update context files."""
     root = find_niyam_root()
     if root is None:
-        console.print("[bold red]Error:[/] Not a Niyam workspace. Run [bold]niyam init[/] first.")
+        console.print(
+            "[bold red]Error:[/] Not a Niyam workspace. Run [bold]niyam init[/] first."
+        )
         raise SystemExit(1)
 
     config = load_niyam_config(root)
@@ -533,16 +573,20 @@ def run_context_show(console: Console) -> None:
 
     context_dir = root / ".niyam" / "context"
     if not context_dir.is_dir():
-        console.print("[yellow]No context files found. Run [bold]niyam context refresh[/] first.[/]")
+        console.print(
+            "[yellow]No context files found. Run [bold]niyam context refresh[/] first.[/]"
+        )
         return
 
     for md_file in sorted(context_dir.glob("*.md")):
         content = md_file.read_text(encoding="utf-8")
-        console.print(Panel(
-            Syntax(content, "markdown", theme="monokai"),
-            title=f"[bold cyan]{md_file.name}[/]",
-            border_style="cyan",
-        ))
+        console.print(
+            Panel(
+                Syntax(content, "markdown", theme="monokai"),
+                title=f"[bold cyan]{md_file.name}[/]",
+                border_style="cyan",
+            )
+        )
 
 
 def run_context_diff(console: Console) -> None:
@@ -557,7 +601,9 @@ def run_context_diff(console: Console) -> None:
     context_dir = root / ".niyam" / "context"
 
     if not context_dir.is_dir():
-        console.print("[yellow]No existing context. Run [bold]niyam context refresh[/] to create it.[/]")
+        console.print(
+            "[yellow]No existing context. Run [bold]niyam context refresh[/] to create it.[/]"
+        )
         return
 
     # Compare architecture
diff --git a/niyam/core/doctor.py b/niyam/core/doctor.py
index 730bcea..47be1af 100644
--- a/niyam/core/doctor.py
+++ b/niyam/core/doctor.py
@@ -6,7 +6,6 @@ from pathlib import Path
 
 import yaml
 from rich.console import Console
-from rich.panel import Panel
 from rich.table import Table
 
 from niyam.core.config import (
@@ -45,35 +44,50 @@ def _check_niyam_structure(repo_root: Path) -> list[DiagnosticResult]:
     for fname in required_files:
         fpath = niyam_dir / fname
         if fpath.exists():
-            results.append(DiagnosticResult(
-                f".niyam/{fname}",
-                True,
-                "Present",
-            ))
+            results.append(
+                DiagnosticResult(
+                    f".niyam/{fname}",
+                    True,
+                    "Present",
+                )
+            )
         else:
-            results.append(DiagnosticResult(
-                f".niyam/{fname}",
-                False,
-                "Missing",
-            ))
+            results.append(
+                DiagnosticResult(
+                    f".niyam/{fname}",
+                    False,
+                    "Missing",
+                )
+            )
 
     # Required directories
-    required_dirs = [CONTEXT_DIR, AGENTS_DIR, SKILLS_DIR, COMMANDS_DIR, POLICIES_DIR, EVIDENCE_DIR]
+    required_dirs = [
+        CONTEXT_DIR,
+        AGENTS_DIR,
+        SKILLS_DIR,
+        COMMANDS_DIR,
+        POLICIES_DIR,
+        EVIDENCE_DIR,
+    ]
     for dname in required_dirs:
         dpath = niyam_dir / dname
         if dpath.is_dir():
             children = list(dpath.iterdir())
-            results.append(DiagnosticResult(
-                f".niyam/{dname}/",
-                True,
-                f"{len(children)} items",
-            ))
+            results.append(
+                DiagnosticResult(
+                    f".niyam/{dname}/",
+                    True,
+                    f"{len(children)} items",
+                )
+            )
         else:
-            results.append(DiagnosticResult(
-                f".niyam/{dname}/",
-                False,
-                "Missing directory",
-            ))
+            results.append(
+                DiagnosticResult(
+                    f".niyam/{dname}/",
+                    False,
+                    "Missing directory",
+                )
+            )
 
     return results
 
@@ -88,18 +102,22 @@ def _check_yaml_validity(repo_root: Path) -> list[DiagnosticResult]:
         try:
             with open(yaml_file) as f:
                 yaml.safe_load(f)
-            results.append(DiagnosticResult(
-                f".niyam/{rel}",
-                True,
-                "Valid YAML",
-                severity="info",
-            ))
+            results.append(
+                DiagnosticResult(
+                    f".niyam/{rel}",
+                    True,
+                    "Valid YAML",
+                    severity="info",
+                )
+            )
         except yaml.YAMLError as e:
-            results.append(DiagnosticResult(
-                f".niyam/{rel}",
-                False,
-                f"Invalid YAML: {e}",
-            ))
+            results.append(
+                DiagnosticResult(
+                    f".niyam/{rel}",
+                    False,
+                    f"Invalid YAML: {e}",
+                )
+            )
 
     return results
 
@@ -116,32 +134,40 @@ def _check_config_schema(repo_root: Path) -> list[DiagnosticResult]:
         known_runtimes = {"claude", "codex", "gemini"}
         for rt in config.runtimes:
             if rt in known_runtimes:
-                results.append(DiagnosticResult(
-                    f"Runtime: {rt}",
-                    True,
-                    "Known runtime",
-                    severity="info",
-                ))
+                results.append(
+                    DiagnosticResult(
+                        f"Runtime: {rt}",
+                        True,
+                        "Known runtime",
+                        severity="info",
+                    )
+                )
             else:
-                results.append(DiagnosticResult(
-                    f"Runtime: {rt}",
-                    False,
-                    f"Unknown runtime '{rt}'",
-                    severity="warning",
-                ))
+                results.append(
+                    DiagnosticResult(
+                        f"Runtime: {rt}",
+                        False,
+                        f"Unknown runtime '{rt}'",
+                        severity="warning",
+                    )
+                )
 
     except FileNotFoundError:
-        results.append(DiagnosticResult(
-            "niyam.yaml schema",
-            False,
-            "File not found",
-        ))
+        results.append(
+            DiagnosticResult(
+                "niyam.yaml schema",
+                False,
+                "File not found",
+            )
+        )
     except Exception as e:
-        results.append(DiagnosticResult(
-            "niyam.yaml schema",
-            False,
-            f"Validation error: {e}",
-        ))
+        results.append(
+            DiagnosticResult(
+                "niyam.yaml schema",
+                False,
+                f"Validation error: {e}",
+            )
+        )
 
     return results
 
@@ -162,28 +188,34 @@ def _check_claude_runtime(repo_root: Path) -> list[DiagnosticResult]:
     for dname in expected_dirs:
         dpath = claude_dir / dname
         if dpath.is_dir():
-            results.append(DiagnosticResult(
-                f".claude/{dname}/",
-                True,
-                f"{len(list(dpath.iterdir()))} items",
-            ))
+            results.append(
+                DiagnosticResult(
+                    f".claude/{dname}/",
+                    True,
+                    f"{len(list(dpath.iterdir()))} items",
+                )
+            )
         else:
-            results.append(DiagnosticResult(
-                f".claude/{dname}/",
-                False,
-                "Missing — run niyam sync",
-            ))
+            results.append(
+                DiagnosticResult(
+                    f".claude/{dname}/",
+                    False,
+                    "Missing — run niyam sync",
+                )
+            )
 
     settings = claude_dir / "settings.json"
     if settings.exists():
         results.append(DiagnosticResult(".claude/settings.json", True, "Present"))
     else:
-        results.append(DiagnosticResult(
-            ".claude/settings.json",
-            False,
-            "Missing — run niyam sync",
-            severity="warning",
-        ))
+        results.append(
+            DiagnosticResult(
+                ".claude/settings.json",
+                False,
+                "Missing — run niyam sync",
+                severity="warning",
+            )
+        )
 
     return results
 
@@ -217,30 +249,46 @@ def _check_gemini_runtime(repo_root: Path) -> list[DiagnosticResult]:
     if style_md.exists():
         results.append(DiagnosticResult(".gemini/STYLE.md", True, "Present"))
     else:
-        results.append(DiagnosticResult(".gemini/STYLE.md", False, "Missing — run niyam sync"))
+        results.append(
+            DiagnosticResult(".gemini/STYLE.md", False, "Missing — run niyam sync")
+        )
 
     settings = gemini_dir / "settings.json"
     if settings.exists():
         results.append(DiagnosticResult(".gemini/settings.json", True, "Present"))
     else:
-        results.append(DiagnosticResult(
-            ".gemini/settings.json",
-            False,
-            "Missing — run niyam sync",
-            severity="warning",
-        ))
+        results.append(
+            DiagnosticResult(
+                ".gemini/settings.json",
+                False,
+                "Missing — run niyam sync",
+                severity="warning",
+            )
+        )
 
     return results
 
 
-def _check_runtimes_in_path(repo_root: Path, config: NiyamConfig) -> list[DiagnosticResult]:
+def _check_runtimes_in_path(
+    repo_root: Path, config: NiyamConfig
+) -> list[DiagnosticResult]:
     import shutil
+
     results = []
     for rt in config.runtimes:
         if shutil.which(rt):
-            results.append(DiagnosticResult(f"Runtime in PATH: {rt}", True, "Found in PATH"))
+            results.append(
+                DiagnosticResult(f"Runtime in PATH: {rt}", True, "Found in PATH")
+            )
         else:
-            results.append(DiagnosticResult(f"Runtime in PATH: {rt}", False, f"Binary '{rt}' not found in PATH", severity="warning"))
+            results.append(
+                DiagnosticResult(
+                    f"Runtime in PATH: {rt}",
+                    False,
+                    f"Binary '{rt}' not found in PATH",
+                    severity="warning",
+                )
+            )
     return results
 
 
@@ -252,17 +300,39 @@ def _check_agents_validity(repo_root: Path) -> list[DiagnosticResult]:
             try:
                 content = agent_file.read_text(encoding="utf-8").strip()
                 if not content:
-                    results.append(DiagnosticResult(f"Agent persona: {agent_file.name}", False, "File is empty", severity="warning"))
+                    results.append(
+                        DiagnosticResult(
+                            f"Agent persona: {agent_file.name}",
+                            False,
+                            "File is empty",
+                            severity="warning",
+                        )
+                    )
                 else:
-                    results.append(DiagnosticResult(f"Agent persona: {agent_file.name}", True, "Valid and non-empty", severity="info"))
+                    results.append(
+                        DiagnosticResult(
+                            f"Agent persona: {agent_file.name}",
+                            True,
+                            "Valid and non-empty",
+                            severity="info",
+                        )
+                    )
             except Exception as e:
-                results.append(DiagnosticResult(f"Agent persona: {agent_file.name}", False, f"Failed to read: {e}", severity="warning"))
+                results.append(
+                    DiagnosticResult(
+                        f"Agent persona: {agent_file.name}",
+                        False,
+                        f"Failed to read: {e}",
+                        severity="warning",
+                    )
+                )
     return results
 
 
 def _check_validation_commands_in_path(repo_root: Path) -> list[DiagnosticResult]:
     import shutil
     from niyam.core.config import load_project_config
+
     results = []
     try:
         project_config = load_project_config(repo_root)
@@ -279,9 +349,22 @@ def _check_validation_commands_in_path(repo_root: Path) -> list[DiagnosticResult
                 if cmd:
                     binary = cmd.split()[0]
                     if shutil.which(binary):
-                        results.append(DiagnosticResult(f"Validation: {name} command", True, f"Binary '{binary}' found"))
+                        results.append(
+                            DiagnosticResult(
+                                f"Validation: {name} command",
+                                True,
+                                f"Binary '{binary}' found",
+                            )
+                        )
                     else:
-                        results.append(DiagnosticResult(f"Validation: {name} command", False, f"Binary '{binary}' (from '{cmd}') not found in PATH", severity="warning"))
+                        results.append(
+                            DiagnosticResult(
+                                f"Validation: {name} command",
+                                False,
+                                f"Binary '{binary}' (from '{cmd}') not found in PATH",
+                                severity="warning",
+                            )
+                        )
     except Exception:
         pass
     return results
@@ -289,31 +372,58 @@ def _check_validation_commands_in_path(repo_root: Path) -> list[DiagnosticResult
 
 def _check_git_status(repo_root: Path) -> list[DiagnosticResult]:
     import subprocess
+
     results = []
     git_dir = repo_root / ".git"
     if not git_dir.exists():
-        results.append(DiagnosticResult("Git Repository", False, "Not a Git repository", severity="warning"))
+        results.append(
+            DiagnosticResult(
+                "Git Repository", False, "Not a Git repository", severity="warning"
+            )
+        )
         return results
 
     results.append(DiagnosticResult("Git Repository", True, "Detected"))
 
     # Check commits
-    res = subprocess.run(["git", "rev-parse", "--verify", "HEAD"], cwd=repo_root, capture_output=True)
+    res = subprocess.run(
+        ["git", "rev-parse", "--verify", "HEAD"], cwd=repo_root, capture_output=True
+    )
     if res.returncode != 0:
-        results.append(DiagnosticResult("Git Commits", False, "No commits found in repository", severity="warning"))
+        results.append(
+            DiagnosticResult(
+                "Git Commits",
+                False,
+                "No commits found in repository",
+                severity="warning",
+            )
+        )
         return results
     else:
         results.append(DiagnosticResult("Git Commits", True, "Commits found"))
 
     # Check clean
-    res = subprocess.run(["git", "status", "--porcelain"], cwd=repo_root, capture_output=True, text=True)
+    res = subprocess.run(
+        ["git", "status", "--porcelain"], cwd=repo_root, capture_output=True, text=True
+    )
     if res.returncode == 0:
         clean = not res.stdout.strip()
         if clean:
-            results.append(DiagnosticResult("Git Status", True, "Working directory clean", severity="info"))
+            results.append(
+                DiagnosticResult(
+                    "Git Status", True, "Working directory clean", severity="info"
+                )
+            )
         else:
-            results.append(DiagnosticResult("Git Status", False, "Uncommitted changes present (may conflict with worktree isolation)", severity="warning"))
-            
+            results.append(
+                DiagnosticResult(
+                    "Git Status",
+                    False,
+                    "Uncommitted changes present (may conflict with worktree isolation)",
+                    severity="warning",
+                )
+            )
+
     return results
 
 
@@ -332,7 +442,7 @@ def run_doctor(
     all_results: list[DiagnosticResult] = []
 
     # core load config
-    from niyam.core.config import NiyamConfig
+
     config = load_niyam_config(root)
 
     # Core checks
diff --git a/niyam/core/init.py b/niyam/core/init.py
index c1147f7..49606ef 100644
--- a/niyam/core/init.py
+++ b/niyam/core/init.py
@@ -152,7 +152,9 @@ def run_init(
         )
         tree = _build_file_tree(files, repo_root)
         console.print(tree)
-        console.print(f"\n[dim]{len([f for f in files if f[1] is not None])} files would be created.[/]")
+        console.print(
+            f"\n[dim]{len([f for f in files if f[1] is not None])} files would be created.[/]"
+        )
         return
 
     # Remove existing if --force
@@ -193,6 +195,7 @@ def run_init(
     # Write default mission templates
     (niyam_dir / "templates" / "missions").mkdir(parents=True, exist_ok=True)
     from niyam.mission.planner import DEFAULT_TEMPLATES
+
     for name, template_data in DEFAULT_TEMPLATES.items():
         template_file = niyam_dir / "templates" / "missions" / f"{name}.yaml"
         with open(template_file, "w", encoding="utf-8") as f:
@@ -209,7 +212,11 @@ def run_init(
         Panel(
             f"[bold green]✓[/] Created Niyam workspace with [cyan]{profile}[/] profile\n"
             f"  [dim]•[/] {created_count} files written to .niyam/\n"
-            + (f"  [dim]•[/] Runtime [cyan]{runtime}[/] configured\n" if runtime else "")
+            + (
+                f"  [dim]•[/] Runtime [cyan]{runtime}[/] configured\n"
+                if runtime
+                else ""
+            )
             + f"  [dim]•[/] Project: [bold]{project_name}[/]\n"
             "\n"
             "[dim]Next steps:[/]\n"
diff --git a/niyam/core/memory.py b/niyam/core/memory.py
index aed2c55..3e48ce8 100644
--- a/niyam/core/memory.py
+++ b/niyam/core/memory.py
@@ -50,7 +50,9 @@ def run_memory_show(console: Console) -> None:
     mem_dir = get_memory_dir(repo_root)
 
     if not mem_dir.exists():
-        console.print("[yellow]No memory directory found. Initialize workspace first.[/]")
+        console.print(
+            "[yellow]No memory directory found. Initialize workspace first.[/]"
+        )
         return
 
     files = sorted(mem_dir.glob("*.md"))
@@ -61,7 +63,9 @@ def run_memory_show(console: Console) -> None:
     for filepath in files:
         title = filepath.stem.replace("-", " ").title()
         content = filepath.read_text(encoding="utf-8")
-        console.print(Panel(content, title=f"[bold cyan]{title}[/]", border_style="cyan"))
+        console.print(
+            Panel(content, title=f"[bold cyan]{title}[/]", border_style="cyan")
+        )
 
 
 def run_memory_add(file: str, note: str, console: Console) -> None:
@@ -81,7 +85,7 @@ def run_memory_add(file: str, note: str, console: Console) -> None:
     # Check if we need a leading newline
     content = filepath.read_text(encoding="utf-8")
     suffix = "\n" if not content.endswith("\n") else ""
-    
+
     # Append the note as a bullet point
     filepath.write_text(content + suffix + f"- {note}\n", encoding="utf-8")
     console.print(f"[bold green]✓[/] Added note to memory '[cyan]{filepath.name}[/]'.")
@@ -114,6 +118,8 @@ def run_memory_clear(file: str, console: Console) -> None:
         # Fallback to file name
         title_line = f"# {filepath.stem.replace('-', ' ').title()}"
 
-    initial_content = f"{title_line}\n\n<!-- Cleared memory. Add new entries below. -->\n"
+    initial_content = (
+        f"{title_line}\n\n<!-- Cleared memory. Add new entries below. -->\n"
+    )
     filepath.write_text(initial_content, encoding="utf-8")
     console.print(f"[bold green]✓[/] Cleared memory '[cyan]{filepath.name}[/]'.")
diff --git a/niyam/core/packs.py b/niyam/core/packs.py
index 9f0762a..1bbcc2e 100644
--- a/niyam/core/packs.py
+++ b/niyam/core/packs.py
@@ -2,13 +2,11 @@
 
 from __future__ import annotations
 
-import shutil
 from pathlib import Path
 import yaml
 from rich.console import Console
 
 from niyam.core.config import (
-    NIYAM_DIR,
     get_niyam_dir,
     load_niyam_config,
     save_niyam_config,
@@ -50,25 +48,31 @@ def list_packs(repo_root: Path) -> list[dict]:
             if d.is_dir() and (d / "pack.yaml").exists():
                 try:
                     manifest = load_pack_manifest(d.name)
-                    packs.append({
-                        "name": d.name,
-                        "version": manifest.get("version", "0.1.0"),
-                        "description": manifest.get("description", ""),
-                        "installed": d.name in installed_packs,
-                    })
+                    packs.append(
+                        {
+                            "name": d.name,
+                            "version": manifest.get("version", "0.1.0"),
+                            "description": manifest.get("description", ""),
+                            "installed": d.name in installed_packs,
+                        }
+                    )
                 except Exception:
                     pass
     return packs
 
 
-def add_pack(repo_root: Path, name: str, force: bool = False, console: Console | None = None) -> None:
+def add_pack(
+    repo_root: Path, name: str, force: bool = False, console: Console | None = None
+) -> None:
     """Install a pack into the .niyam/ directory."""
     pack_dir = get_pack_dir(name)
     manifest = load_pack_manifest(name)
     niyam_dir = get_niyam_dir(repo_root)
 
     if not niyam_dir.exists():
-        raise FileNotFoundError("Niyam workspace is not initialized. Run `niyam init` first.")
+        raise FileNotFoundError(
+            "Niyam workspace is not initialized. Run `niyam init` first."
+        )
 
     config = load_niyam_config(repo_root)
 
@@ -93,7 +97,11 @@ def add_pack(repo_root: Path, name: str, force: bool = False, console: Console |
                     # Read target content
                     content = src.read_text(encoding="utf-8")
                     # Construct expected content with header
-                    header = f"<!-- pack: {name} -->\n\n" if dst.suffix == ".md" else f"# pack: {name}\n\n"
+                    header = (
+                        f"<!-- pack: {name} -->\n\n"
+                        if dst.suffix == ".md"
+                        else f"# pack: {name}\n\n"
+                    )
                     expected_content = header + content
                     if existing_content != expected_content:
                         conflicts.append(str(rel))
@@ -102,7 +110,7 @@ def add_pack(repo_root: Path, name: str, force: bool = False, console: Console |
 
         if conflicts:
             raise ValueError(
-                f"Conflict detected! The following files already exist in .niyam/:\n"
+                "Conflict detected! The following files already exist in .niyam/:\n"
                 + "\n".join(f"  - {c}" for c in conflicts)
                 + "\nUse --force to overwrite them."
             )
diff --git a/niyam/core/pr.py b/niyam/core/pr.py
index 4229085..0ccb5c1 100644
--- a/niyam/core/pr.py
+++ b/niyam/core/pr.py
@@ -51,7 +51,9 @@ def fetch_pr_diff_api(owner: str, repo: str, pr_id: str, token: str) -> str:
         with urllib.request.urlopen(req) as response:
             return response.read().decode("utf-8")
     except urllib.error.HTTPError as e:
-        raise RuntimeError(f"GitHub API returned HTTP {e.code}: {e.read().decode('utf-8')}")
+        raise RuntimeError(
+            f"GitHub API returned HTTP {e.code}: {e.read().decode('utf-8')}"
+        )
     except urllib.error.URLError as e:
         raise RuntimeError(f"Failed to fetch PR diff from GitHub API: {e}")
 
@@ -59,10 +61,16 @@ def fetch_pr_diff_api(owner: str, repo: str, pr_id: str, token: str) -> str:
 def fetch_pr_diff_gh(pr_id: str, repo_root: Path) -> str:
     """Fetch PR diff using gh CLI."""
     if not shutil.which("gh"):
-        raise RuntimeError("GitHub CLI ('gh') is not installed and GITHUB_TOKEN is not set.")
-    res = subprocess.run(["gh", "pr", "diff", pr_id], cwd=repo_root, capture_output=True, text=True)
+        raise RuntimeError(
+            "GitHub CLI ('gh') is not installed and GITHUB_TOKEN is not set."
+        )
+    res = subprocess.run(
+        ["gh", "pr", "diff", pr_id], cwd=repo_root, capture_output=True, text=True
+    )
     if res.returncode != 0:
-        raise RuntimeError(f"GitHub CLI failed to fetch PR diff:\n{res.stderr or res.stdout}")
+        raise RuntimeError(
+            f"GitHub CLI failed to fetch PR diff:\n{res.stderr or res.stdout}"
+        )
     return res.stdout
 
 
@@ -83,7 +91,9 @@ def get_pr_diff(pr_id: str, token: str | None, repo_root: Path) -> str:
         return fetch_pr_diff_gh(pr_id, repo_root)
 
 
-def post_pr_comment_api(owner: str, repo: str, pr_id: str, token: str, body: str) -> None:
+def post_pr_comment_api(
+    owner: str, repo: str, pr_id: str, token: str, body: str
+) -> None:
     """Post comment to PR using raw GitHub REST API."""
     url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_id}/comments"
     data = json.dumps({"body": body}).encode("utf-8")
@@ -102,10 +112,19 @@ def post_pr_comment_api(owner: str, repo: str, pr_id: str, token: str, body: str
 def post_pr_comment_gh(pr_id: str, body: str, repo_root: Path) -> None:
     """Post comment to PR using gh CLI."""
     if not shutil.which("gh"):
-        raise RuntimeError("GitHub CLI ('gh') is not installed and GITHUB_TOKEN is not set.")
-    res = subprocess.run(["gh", "pr", "comment", pr_id, "--body", body], cwd=repo_root, capture_output=True, text=True)
+        raise RuntimeError(
+            "GitHub CLI ('gh') is not installed and GITHUB_TOKEN is not set."
+        )
+    res = subprocess.run(
+        ["gh", "pr", "comment", pr_id, "--body", body],
+        cwd=repo_root,
+        capture_output=True,
+        text=True,
+    )
     if res.returncode != 0:
-        raise RuntimeError(f"GitHub CLI failed to post comment:\n{res.stderr or res.stdout}")
+        raise RuntimeError(
+            f"GitHub CLI failed to post comment:\n{res.stderr or res.stdout}"
+        )
 
 
 def post_pr_comment(pr_id: str, body: str, token: str | None, repo_root: Path) -> None:
@@ -125,15 +144,14 @@ def post_pr_comment(pr_id: str, body: str, token: str | None, repo_root: Path) -
         post_pr_comment_gh(pr_id, body, repo_root)
 
 
-def create_pr_api(owner: str, repo: str, title: str, body: str, head: str, base: str, token: str) -> str:
+def create_pr_api(
+    owner: str, repo: str, title: str, body: str, head: str, base: str, token: str
+) -> str:
     """Create a pull request via raw GitHub REST API."""
     url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
-    data = json.dumps({
-        "title": title,
-        "body": body,
-        "head": head,
-        "base": base
-    }).encode("utf-8")
+    data = json.dumps(
+        {"title": title, "body": body, "head": head, "base": base}
+    ).encode("utf-8")
     req = urllib.request.Request(url, data=data, method="POST")
     req.add_header("Authorization", f"token {token}")
     req.add_header("Content-Type", "application/json")
@@ -149,7 +167,9 @@ def create_pr_api(owner: str, repo: str, title: str, body: str, head: str, base:
 def create_pr_gh(title: str, body: str, base: str, repo_root: Path) -> str:
     """Create a pull request using gh CLI."""
     if not shutil.which("gh"):
-        raise RuntimeError("GitHub CLI ('gh') is not installed and GITHUB_TOKEN is not set.")
+        raise RuntimeError(
+            "GitHub CLI ('gh') is not installed and GITHUB_TOKEN is not set."
+        )
     res = subprocess.run(
         ["gh", "pr", "create", "--title", title, "--body", body, "--base", base],
         cwd=repo_root,
@@ -157,7 +177,9 @@ def create_pr_gh(title: str, body: str, base: str, repo_root: Path) -> str:
         text=True,
     )
     if res.returncode != 0:
-        raise RuntimeError(f"GitHub CLI failed to create PR:\n{res.stderr or res.stdout}")
+        raise RuntimeError(
+            f"GitHub CLI failed to create PR:\n{res.stderr or res.stdout}"
+        )
     return res.stdout.strip()
 
 
@@ -192,7 +214,7 @@ def run_pr_review(
         raise FileNotFoundError(f"Review template for lens '{lens}' not found.")
 
     template_content = template_path.read_text(encoding="utf-8")
-    
+
     # Apply mode modifications
     prefix = ""
     if mode == "adversarial":
@@ -203,7 +225,7 @@ def run_pr_review(
             "Aggressively seek out bugs, race conditions, design flaws, styling inconsistencies, and security issues. "
             "Do not accept compromises. Critique every line of the changes below.\n\n"
         )
-    
+
     compiled_prompt = prefix + template_content.replace("{{git_diff}}", diff)
 
     # 3. Save to a temporary prompt file for runtime reference
@@ -217,7 +239,9 @@ def run_pr_review(
 
     if is_test:
         console.print("[dim]Mocking review execution...[/]")
-        review_output = f"Mocked structured code review for PR #{pr_id} using {lens} lens."
+        review_output = (
+            f"Mocked structured code review for PR #{pr_id} using {lens} lens."
+        )
     else:
         if shutil.which(runtime):
             console.print(f"[cyan]Invoking {runtime} CLI for PR review...[/]")
@@ -246,7 +270,9 @@ def run_pr_review(
     # 4. Post comment
     console.print(f"[cyan]Posting review comment to Pull Request #{pr_id}...[/]")
     post_pr_comment(pr_id, review_output, token, repo_root)
-    console.print(f"[bold green]✓[/] Code review comment successfully posted to PR #{pr_id}.")
+    console.print(
+        f"[bold green]✓[/] Code review comment successfully posted to PR #{pr_id}."
+    )
 
 
 def run_pr_create(
@@ -281,7 +307,12 @@ def run_pr_create(
     console.print(f"[cyan]Pushing branch '{branch_name}' to remote origin...[/]")
     is_test = os.environ.get("NIYAM_TEST") == "1"
     if not is_test:
-        res_push = subprocess.run(["git", "push", "-u", "origin", branch_name], cwd=repo_root, capture_output=True, text=True)
+        res_push = subprocess.run(
+            ["git", "push", "-u", "origin", branch_name],
+            cwd=repo_root,
+            capture_output=True,
+            text=True,
+        )
         if res_push.returncode != 0:
             raise RuntimeError(f"Failed to push branch to remote:\n{res_push.stderr}")
 
@@ -292,8 +323,11 @@ def run_pr_create(
         run_dir = niyam_dir / "runs" / mission_id
         evidence_path = run_dir / "evidence.md"
         if not evidence_path.exists():
-            console.print("[yellow]Evidence report not found. Generating it automatically...[/]")
+            console.print(
+                "[yellow]Evidence report not found. Generating it automatically...[/]"
+            )
             from niyam.mission.reporter import run_mission_report
+
             run_mission_report(console=console)
         if evidence_path.exists():
             evidence_content = evidence_path.read_text(encoding="utf-8")
@@ -304,18 +338,22 @@ def run_pr_create(
         pr_body += f"\n\n## Niyam Mission Evidence\n\n{evidence_content}"
 
     # 3. Create PR
-    console.print(f"[cyan]Creating Pull Request for branch '{branch_name}' targeting '{base}'...[/]")
+    console.print(
+        f"[cyan]Creating Pull Request for branch '{branch_name}' targeting '{base}'...[/]"
+    )
     pr_url = ""
     if is_test:
         console.print("[dim]Mocking PR creation...[/]")
-        pr_url = f"https://github.com/mock/repo/pull/42"
+        pr_url = "https://github.com/mock/repo/pull/42"
     else:
         token = token or os.environ.get("GITHUB_TOKEN")
         owner_repo = get_github_repo_owner_name(repo_root)
         if token and owner_repo:
             owner, repo = owner_repo
             try:
-                pr_url = create_pr_api(owner, repo, title, pr_body, branch_name, base, token)
+                pr_url = create_pr_api(
+                    owner, repo, title, pr_body, branch_name, base, token
+                )
             except Exception as e:
                 try:
                     pr_url = create_pr_gh(title, pr_body, base, repo_root)
@@ -324,8 +362,10 @@ def run_pr_create(
         else:
             pr_url = create_pr_gh(title, pr_body, base, repo_root)
 
-    console.print(Panel(
-        f"[bold green]✓ Pull Request Created Successfully![/]\n[cyan]{pr_url}[/]",
-        title="[bold green]PR Created[/]",
-        border_style="green"
-    ))
+    console.print(
+        Panel(
+            f"[bold green]✓ Pull Request Created Successfully![/]\n[cyan]{pr_url}[/]",
+            title="[bold green]PR Created[/]",
+            border_style="green",
+        )
+    )
diff --git a/niyam/core/review.py b/niyam/core/review.py
index 0f083d8..0162ebf 100644
--- a/niyam/core/review.py
+++ b/niyam/core/review.py
@@ -24,12 +24,13 @@ def is_binary_file(path: Path) -> bool:
 
 def redact_secrets(content: str) -> str:
     import re
+
     # AWS access key ID
     content = re.sub(r"AKIA[A-Z0-9]{16}", "[REDACTED_AWS_KEY]", content)
     # Generic secret pattern
     secret_pattern = re.compile(
         r"(?i)(api[_-]?key|secret|password|passwd|token|private[_-]?key)\s*[:=]\s*([\"'])([a-zA-Z0-9_\-\.\:\/\+]{12,})(\2)",
-        re.IGNORECASE
+        re.IGNORECASE,
     )
     content = secret_pattern.sub(r"\1 = \2[REDACTED_SECRET]\4", content)
     return content
@@ -39,23 +40,35 @@ def get_git_diff(repo_root: Path | None = None) -> str:
     """Fetch the current git diff of tracked and untracked changes with safety caps."""
     if repo_root is None:
         from niyam.core.config import find_niyam_root
+
         repo_root = find_niyam_root() or Path.cwd()
 
     try:
         # Get diff of tracked files
-        res = subprocess.run(["git", "diff"], cwd=repo_root, capture_output=True, text=True)
+        res = subprocess.run(
+            ["git", "diff"], cwd=repo_root, capture_output=True, text=True
+        )
         tracked = res.stdout if res.returncode == 0 else ""
 
         # Get diff of staged files
-        res_staged = subprocess.run(["git", "diff", "--cached"], cwd=repo_root, capture_output=True, text=True)
+        res_staged = subprocess.run(
+            ["git", "diff", "--cached"], cwd=repo_root, capture_output=True, text=True
+        )
         staged = res_staged.stdout if res_staged.returncode == 0 else ""
 
         # Get untracked files
-        res_untracked = subprocess.run(["git", "ls-files", "--others", "--exclude-standard"], cwd=repo_root, capture_output=True, text=True)
-        untracked_files = res_untracked.stdout.splitlines() if res_untracked.returncode == 0 else []
+        res_untracked = subprocess.run(
+            ["git", "ls-files", "--others", "--exclude-standard"],
+            cwd=repo_root,
+            capture_output=True,
+            text=True,
+        )
+        untracked_files = (
+            res_untracked.stdout.splitlines() if res_untracked.returncode == 0 else []
+        )
 
         MAX_UNTRACKED_FILE_SIZE = 50 * 1024  # 50 KB
-        MAX_UNTRACKED_BUDGET = 200 * 1024   # 200 KB
+        MAX_UNTRACKED_BUDGET = 200 * 1024  # 200 KB
         total_budget_used = 0
 
         untracked = ""
@@ -67,12 +80,12 @@ def get_git_diff(repo_root: Path | None = None) -> str:
 
                 file_size = file_path.stat().st_size
                 if file_size > MAX_UNTRACKED_FILE_SIZE:
-                     untracked += f"\n\n--- Untracked File: {f} (Skipped: exceeds 50 KB size limit) ---\n"
-                     continue
+                    untracked += f"\n\n--- Untracked File: {f} (Skipped: exceeds 50 KB size limit) ---\n"
+                    continue
 
                 if total_budget_used + file_size > MAX_UNTRACKED_BUDGET:
-                     untracked += f"\n\n--- Untracked File: {f} (Skipped: exceeds total prompt budget limit) ---\n"
-                     continue
+                    untracked += f"\n\n--- Untracked File: {f} (Skipped: exceeds total prompt budget limit) ---\n"
+                    continue
 
                 try:
                     content = file_path.read_text(encoding="utf-8")
@@ -89,7 +102,6 @@ def get_git_diff(repo_root: Path | None = None) -> str:
         return ""
 
 
-
 def run_review(
     lens: str,
     runtime: str,
@@ -107,17 +119,21 @@ def run_review(
     # 1. Fetch git diff
     diff = get_git_diff(repo_root)
     if not diff:
-        console.print("[yellow]No local changes detected to review. Try making some changes first.[/]")
+        console.print(
+            "[yellow]No local changes detected to review. Try making some changes first.[/]"
+        )
         return
 
     # 2. Get template
     template_path = REVIEWS_DIR / f"{lens}.md"
     if not template_path.exists():
-        console.print(f"[bold red]Error:[/] Review template for lens '{lens}' not found.")
+        console.print(
+            f"[bold red]Error:[/] Review template for lens '{lens}' not found."
+        )
         return
 
     template_content = template_path.read_text(encoding="utf-8")
-    
+
     # 3. Apply mode modification
     prefix = ""
     if mode == "adversarial":
@@ -128,17 +144,19 @@ def run_review(
             "Aggressively seek out bugs, race conditions, design flaws, styling inconsistencies, and security issues. "
             "Do not accept compromises. Critique every line of the changes below.\n\n"
         )
-    
+
     compiled_prompt = prefix + template_content.replace("{{git_diff}}", diff)
 
     # 4. Show or run prompt
-    console.print(Panel(
-        f"Lens: [bold cyan]{lens.upper()}[/]\n"
-        f"Runtime: [bold cyan]{runtime}[/]\n"
-        f"Mode: [bold cyan]{mode.upper()}[/]",
-        title="[bold]Code Review Plan[/]",
-        border_style="cyan"
-    ))
+    console.print(
+        Panel(
+            f"Lens: [bold cyan]{lens.upper()}[/]\n"
+            f"Runtime: [bold cyan]{runtime}[/]\n"
+            f"Mode: [bold cyan]{mode.upper()}[/]",
+            title="[bold]Code Review Plan[/]",
+            border_style="cyan",
+        )
+    )
 
     # Save to a temporary prompt file for reference
     temp_dir = repo_root / ".niyam" / "runs"
@@ -150,7 +168,7 @@ def run_review(
 
     if is_test:
         console.print("[dim]Mocking review execution...[/]")
-        console.print(f"[green]✓[/] Code review successfully generated.")
+        console.print("[green]✓[/] Code review successfully generated.")
     else:
         if shutil.which(runtime):
             console.print(f"[cyan]Invoking {runtime} CLI for review...[/]")
@@ -158,10 +176,14 @@ def run_review(
                 subprocess.run([runtime, str(prompt_file)], check=True)
             except Exception:
                 console.print(f"[yellow]Warning: {runtime} execution failed.[/]")
-                console.print(f"Here is the review prompt. You can copy-paste it into your AI session:\n")
+                console.print(
+                    "Here is the review prompt. You can copy-paste it into your AI session:\n"
+                )
                 console.print(compiled_prompt)
         else:
             console.print(f"[yellow]CLI '{runtime}' not found in PATH.[/]")
-            console.print(f"Here is the generated review prompt. You can copy-paste it into your session:\n")
+            console.print(
+                "Here is the generated review prompt. You can copy-paste it into your session:\n"
+            )
             console.print(compiled_prompt)
             console.print(f"\n[dim]Prompt also saved to: {prompt_file}[/]")
diff --git a/niyam/core/security.py b/niyam/core/security.py
index e0b4d4f..7086c26 100644
--- a/niyam/core/security.py
+++ b/niyam/core/security.py
@@ -16,20 +16,52 @@ import yaml
 # Only the first token of the command is checked against this set.
 ALLOWED_VALIDATION_EXECUTABLES: set[str] = {
     # Python
-    "pytest", "python", "python3", "mypy", "ruff", "black", "isort", "flake8",
-    "pylint", "pyright", "bandit", "safety", "pip-audit",
+    "pytest",
+    "python",
+    "python3",
+    "mypy",
+    "ruff",
+    "black",
+    "isort",
+    "flake8",
+    "pylint",
+    "pyright",
+    "bandit",
+    "safety",
+    "pip-audit",
     # Node / JS
-    "npm", "npx", "yarn", "pnpm", "bun", "node", "tsc", "eslint", "prettier",
+    "npm",
+    "npx",
+    "yarn",
+    "pnpm",
+    "bun",
+    "node",
+    "tsc",
+    "eslint",
+    "prettier",
     # Rust
-    "cargo", "clippy",
+    "cargo",
+    "clippy",
     # Go
     "go",
     # General build
-    "make", "cmake", "gradle", "mvn",
+    "make",
+    "cmake",
+    "gradle",
+    "mvn",
     # Security scanners
-    "semgrep", "gitleaks", "detect-secrets", "trivy", "grype",
+    "semgrep",
+    "gitleaks",
+    "detect-secrets",
+    "trivy",
+    "grype",
     # Shell utilities commonly used in validation
-    "echo", "cat", "grep", "wc", "diff", "test",
+    "echo",
+    "cat",
+    "grep",
+    "wc",
+    "diff",
+    "test",
 }
 
 
@@ -55,7 +87,9 @@ def validate_command(cmd: str) -> list[str]:
     if not parts:
         raise CommandSecurityError("Empty command after parsing")
 
-    executable = Path(parts[0]).name  # Strip any path prefix (e.g. /usr/bin/pytest → pytest)
+    executable = Path(
+        parts[0]
+    ).name  # Strip any path prefix (e.g. /usr/bin/pytest → pytest)
 
     if executable not in ALLOWED_VALIDATION_EXECUTABLES:
         raise CommandSecurityError(
diff --git a/niyam/core/setup.py b/niyam/core/setup.py
index af29301..824695a 100644
--- a/niyam/core/setup.py
+++ b/niyam/core/setup.py
@@ -2,7 +2,6 @@
 
 from __future__ import annotations
 
-import os
 import shutil
 from pathlib import Path
 from rich.console import Console
@@ -36,14 +35,25 @@ def run_setup(console: Console) -> None:
 
     # 1. Initialize if not exists
     if not niyam_dir.exists():
-        console.print("[yellow]No .niyam/ directory detected. Let's initialize your workspace![/]")
+        console.print(
+            "[yellow]No .niyam/ directory detected. Let's initialize your workspace![/]"
+        )
         profile = Prompt.ask(
             "Which project profile fits your stack?",
-            choices=["fullstack", "backend", "frontend", "startup-saas", "platform-engineering", "governed-enterprise"],
+            choices=[
+                "fullstack",
+                "backend",
+                "frontend",
+                "startup-saas",
+                "platform-engineering",
+                "governed-enterprise",
+            ],
             default="fullstack",
         )
         console.print(f"[cyan]Initializing Niyam with profile: {profile}...[/]")
-        run_init(profile=profile, runtime=None, dry_run=False, force=False, console=console)
+        run_init(
+            profile=profile, runtime=None, dry_run=False, force=False, console=console
+        )
         # Refresh root
         repo_root = find_niyam_root() or repo_root
         niyam_dir = get_niyam_dir(repo_root)
@@ -66,7 +76,9 @@ def run_setup(console: Console) -> None:
 
     runtimes_to_enable = []
     if not detected_runtimes:
-        console.print("\n[yellow]⚠️ No AI runtimes (claude, gemini, codex) were detected in your PATH.[/]")
+        console.print(
+            "\n[yellow]⚠️ No AI runtimes (claude, gemini, codex) were detected in your PATH.[/]"
+        )
         console.print("Please install them or specify the one you plan to use.")
         chosen_rt = Prompt.ask(
             "Which runtime would you like to configure anyway?",
@@ -77,7 +89,10 @@ def run_setup(console: Console) -> None:
             runtimes_to_enable.append(chosen_rt)
     else:
         for rt in detected_runtimes:
-            enable = Confirm.ask(f"Would you like to enable the [bold cyan]{rt}[/] runtime?", default=True)
+            enable = Confirm.ask(
+                f"Would you like to enable the [bold cyan]{rt}[/] runtime?",
+                default=True,
+            )
             if enable:
                 runtimes_to_enable.append(rt)
 
@@ -91,12 +106,19 @@ def run_setup(console: Console) -> None:
     if agents_dir.is_dir():
         agents = [f.stem for f in agents_dir.glob("*.md")]
         console.print(f"Detected agents in .niyam/agents/: {', '.join(agents)}")
-        console.print("You can customize these markdown files to adjust agent personas and expertise.")
+        console.print(
+            "You can customize these markdown files to adjust agent personas and expertise."
+        )
 
     # 5. Policies & Guardrails
     console.print("\n[cyan]Configuring Guardrails & Security Policies[/]")
-    guard_enabled = Confirm.ask("Would you like to enable safety guardrails?", default=True)
-    careful_mode = Confirm.ask("Would you like careful mode enabled (warnings before executing risky commands)?", default=True)
+    guard_enabled = Confirm.ask(
+        "Would you like to enable safety guardrails?", default=True
+    )
+    careful_mode = Confirm.ask(
+        "Would you like careful mode enabled (warnings before executing risky commands)?",
+        default=True,
+    )
 
     config = load_niyam_config(repo_root)
     config.guard.enabled = guard_enabled
@@ -108,7 +130,7 @@ def run_setup(console: Console) -> None:
         Panel(
             "[bold green]✓ Niyam Setup Completed Successfully![/]\n\n"
             "Try planning and executing your first mission:\n"
-            "  [bold cyan]niyam run \"implement a simple hello world test case\"[/]",
+            '  [bold cyan]niyam run "implement a simple hello world test case"[/]',
             title="[bold green]Success[/]",
             border_style="green",
         )
diff --git a/niyam/core/sync.py b/niyam/core/sync.py
index 7f44ef4..4921cae 100644
--- a/niyam/core/sync.py
+++ b/niyam/core/sync.py
@@ -6,7 +6,6 @@ from pathlib import Path
 
 import yaml
 from rich.console import Console
-from rich.panel import Panel
 
 from niyam.core.config import (
     find_niyam_root,
@@ -37,7 +36,9 @@ def run_sync(
     runtimes_to_sync = [runtime] if runtime else config.runtimes
 
     if not runtimes_to_sync:
-        console.print("[yellow]No runtimes configured. Use [bold]niyam runtime add <runtime>[/] first.[/]")
+        console.print(
+            "[yellow]No runtimes configured. Use [bold]niyam runtime add <runtime>[/] first.[/]"
+        )
         return
 
     for rt in runtimes_to_sync:
diff --git a/niyam/evidence/reporter.py b/niyam/evidence/reporter.py
index cd33169..6ffd0c8 100644
--- a/niyam/evidence/reporter.py
+++ b/niyam/evidence/reporter.py
@@ -58,7 +58,9 @@ def _get_diff_summary(repo_root: Path) -> str:
         if staged.stdout.strip():
             sections.append(f"## Staged Changes\n\n```\n{staged.stdout.strip()}\n```")
         if unstaged.stdout.strip():
-            sections.append(f"## Unstaged Changes\n\n```\n{unstaged.stdout.strip()}\n```")
+            sections.append(
+                f"## Unstaged Changes\n\n```\n{unstaged.stdout.strip()}\n```"
+            )
         if log.stdout.strip():
             sections.append(f"## Recent Commits\n\n```\n{log.stdout.strip()}\n```")
 
@@ -156,7 +158,7 @@ def _generate_evidence_markdown(
         "",
         f"**Branch:** `{branch}`",
         f"**Generated:** {now}",
-        f"**Generator:** Niyam v0.1.0",
+        "**Generator:** Niyam v0.1.0",
         "",
         "---",
         "",
@@ -197,7 +199,9 @@ def run_report(format: str, console: Console) -> None:
     """Generate evidence report for the current branch."""
     root = find_niyam_root()
     if root is None:
-        console.print("[bold red]Error:[/] Not a Niyam workspace. Run [bold]niyam init[/] first.")
+        console.print(
+            "[bold red]Error:[/] Not a Niyam workspace. Run [bold]niyam init[/] first."
+        )
         raise SystemExit(1)
 
     config = load_niyam_config(root)
@@ -228,9 +232,13 @@ def run_report(format: str, console: Console) -> None:
         json_path = evidence_dir / "evidence.json"
         json_path.write_text(json.dumps(evidence_data, indent=2), encoding="utf-8")
         if has_failures:
-            console.print(f"[yellow]⚠[/] Evidence exported with validation failures: [cyan]{json_path.relative_to(root)}[/]")
+            console.print(
+                f"[yellow]⚠[/] Evidence exported with validation failures: [cyan]{json_path.relative_to(root)}[/]"
+            )
         else:
-            console.print(f"[green]✓[/] Evidence exported: [cyan]{json_path.relative_to(root)}[/]")
+            console.print(
+                f"[green]✓[/] Evidence exported: [cyan]{json_path.relative_to(root)}[/]"
+            )
 
     else:
         # Markdown report
diff --git a/niyam/mission/dashboard.py b/niyam/mission/dashboard.py
index 11003ae..9d69956 100644
--- a/niyam/mission/dashboard.py
+++ b/niyam/mission/dashboard.py
@@ -3,7 +3,6 @@
 from __future__ import annotations
 
 import json
-import os
 import time
 from pathlib import Path
 from datetime import datetime, timezone
@@ -20,6 +19,7 @@ from niyam.mission.planner import get_latest_mission_id
 def load_plan(run_dir: Path) -> dict:
     """Load mission plan YAML."""
     import yaml
+
     plan_path = run_dir / "mission-plan.yaml"
     with open(plan_path, encoding="utf-8") as f:
         return yaml.safe_load(f) or {}
@@ -69,12 +69,17 @@ def get_task_durations(run_dir: Path) -> dict[str, float]:
     return durations
 
 
-def generate_dashboard_renderable(run_dir: Path, niyam_dir: Path, mission_id: str) -> Panel:
+def generate_dashboard_renderable(
+    run_dir: Path, niyam_dir: Path, mission_id: str
+) -> Panel:
     """Construct a beautiful dashboard layout."""
     try:
         plan_data = load_plan(run_dir)
     except Exception as e:
-        return Panel(f"[bold yellow]Refreshing dashboard...[/]\n[dim]({e})[/]", title="[bold cyan]Niyam Dashboard[/]")
+        return Panel(
+            f"[bold yellow]Refreshing dashboard...[/]\n[dim]({e})[/]",
+            title="[bold cyan]Niyam Dashboard[/]",
+        )
 
     mission_meta = plan_data.get("mission", {})
     status = mission_meta.get("status", "planned")
@@ -111,7 +116,9 @@ def generate_dashboard_renderable(run_dir: Path, niyam_dir: Path, mission_id: st
 
     # Build tasks table
     tasks = plan_data.get("tasks", [])
-    tasks_table = Table(title="[bold cyan]Mission Tasks[/]", show_header=True, expand=True)
+    tasks_table = Table(
+        title="[bold cyan]Mission Tasks[/]", show_header=True, expand=True
+    )
     tasks_table.add_column("ID", width=6, style="bold magenta", justify="center")
     tasks_table.add_column("Title", style="white")
     tasks_table.add_column("Agent", style="yellow")
@@ -153,7 +160,9 @@ def generate_dashboard_renderable(run_dir: Path, niyam_dir: Path, mission_id: st
 
     summary = ledger.get("summary", {})
 
-    ledger_table = Table(title="[bold green]Token & Cost Ledger[/]", show_header=False, expand=True)
+    ledger_table = Table(
+        title="[bold green]Token & Cost Ledger[/]", show_header=False, expand=True
+    )
     ledger_table.add_column(style="bold yellow")
     ledger_table.add_column(justify="right")
 
@@ -175,7 +184,9 @@ def generate_dashboard_renderable(run_dir: Path, niyam_dir: Path, mission_id: st
 
     # Layout assembly
     meta_panel = Panel(meta_table, title="[bold]Mission Config[/]", border_style="cyan")
-    ledger_panel = Panel(ledger_table, title="[bold]Resource Metrics[/]", border_style="green")
+    ledger_panel = Panel(
+        ledger_table, title="[bold]Resource Metrics[/]", border_style="green"
+    )
 
     header_cols = Columns([meta_panel, ledger_panel], expand=True)
 
@@ -191,7 +202,10 @@ def generate_dashboard_renderable(run_dir: Path, niyam_dir: Path, mission_id: st
                 with open(log_path, encoding="utf-8") as lf:
                     lines = lf.readlines()
                     last_lines = [line.rstrip() for line in lines[-12:]]
-                    log_contents.append(f"[bold cyan]Task {r_id} Log Output:[/]\n" + "\n".join(last_lines))
+                    log_contents.append(
+                        f"[bold cyan]Task {r_id} Log Output:[/]\n"
+                        + "\n".join(last_lines)
+                    )
             except Exception:
                 pass
 
@@ -199,8 +213,10 @@ def generate_dashboard_renderable(run_dir: Path, niyam_dir: Path, mission_id: st
         log_disp = "[dim]No active task logs. Execution is either paused, completed, or waiting...[/]"
     else:
         log_disp = "\n\n".join(log_contents)
-        
-    log_panel = Panel(log_disp, title="[bold]Active Task Logs[/]", border_style="magenta", expand=True)
+
+    log_panel = Panel(
+        log_disp, title="[bold]Active Task Logs[/]", border_style="magenta", expand=True
+    )
 
     # Validation results tail
     val_path = run_dir / "validation-results.md"
@@ -213,22 +229,27 @@ def generate_dashboard_renderable(run_dir: Path, niyam_dir: Path, mission_id: st
                 val_disp = "\n".join(last_val_lines)
         except Exception:
             pass
-            
-    val_panel = Panel(val_disp, title="[bold]Validation Suite Output[/]", border_style="blue", expand=True)
+
+    val_panel = Panel(
+        val_disp,
+        title="[bold]Validation Suite Output[/]",
+        border_style="blue",
+        expand=True,
+    )
 
     main_group = Table.grid(expand=True)
     main_group.add_row(header_cols)
     main_group.add_row("")
     main_group.add_row(tasks_table)
     main_group.add_row("")
-    
+
     lower_cols = Columns([log_panel, val_panel], expand=True)
     main_group.add_row(lower_cols)
 
     return Panel(
         main_group,
         title="[bold magenta]NIYAM[/] [bold cyan]MISSION DASHBOARD[/]",
-        border_style="cyan"
+        border_style="cyan",
     )
 
 
@@ -252,12 +273,21 @@ def run_mission_dashboard(watch: bool, console: Console) -> None:
         raise SystemExit(1)
 
     if watch:
-        console.print("[dim]Starting dashboard in live-monitoring mode. Press Ctrl+C to exit.[/]")
-        with Live(generate_dashboard_renderable(run_dir, niyam_dir, mission_id), console=console, auto_refresh=True, refresh_per_second=2) as live:
+        console.print(
+            "[dim]Starting dashboard in live-monitoring mode. Press Ctrl+C to exit.[/]"
+        )
+        with Live(
+            generate_dashboard_renderable(run_dir, niyam_dir, mission_id),
+            console=console,
+            auto_refresh=True,
+            refresh_per_second=2,
+        ) as live:
             try:
                 while True:
                     time.sleep(0.5)
-                    live.update(generate_dashboard_renderable(run_dir, niyam_dir, mission_id))
+                    live.update(
+                        generate_dashboard_renderable(run_dir, niyam_dir, mission_id)
+                    )
             except KeyboardInterrupt:
                 pass
     else:
diff --git a/niyam/mission/executor.py b/niyam/mission/executor.py
index 616b077..caf8f56 100644
--- a/niyam/mission/executor.py
+++ b/niyam/mission/executor.py
@@ -44,8 +44,9 @@ def save_plan(run_dir: Path, plan_data: dict) -> None:
 
         tasks_path = run_dir / "task-list.yaml"
         with open(tasks_path, "w", encoding="utf-8") as f:
-            yaml.dump(plan_data.get("tasks", []), f, default_flow_style=False, sort_keys=False)
-
+            yaml.dump(
+                plan_data.get("tasks", []), f, default_flow_style=False, sort_keys=False
+            )
 
 
 def _lock_and_write_events(log_path: Path, new_event: dict) -> None:
@@ -79,7 +80,9 @@ def _lock_and_write_events(log_path: Path, new_event: dict) -> None:
                 pass
 
 
-def log_execution_event(run_dir: Path, event_type: str, task_id: str, details: str) -> None:
+def log_execution_event(
+    run_dir: Path, event_type: str, task_id: str, details: str
+) -> None:
     """Log execution events to execution-log.json."""
     log_path = run_dir / "execution-log.json"
     event = {
@@ -91,14 +94,19 @@ def log_execution_event(run_dir: Path, event_type: str, task_id: str, details: s
     _lock_and_write_events(log_path, event)
 
 
-def log_policy_event(run_dir: Path, niyam_dir: Path, event_type: str, details: str) -> None:
+def log_policy_event(
+    run_dir: Path, niyam_dir: Path, event_type: str, details: str
+) -> None:
     """Log policy guardrail violation to policy-events.json (both run-level and global)."""
     event = {
         "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
         "type": event_type,
         "details": details,
     }
-    for log_path in (run_dir / "policy-events.json", niyam_dir / "evidence" / "policy-events.json"):
+    for log_path in (
+        run_dir / "policy-events.json",
+        niyam_dir / "evidence" / "policy-events.json",
+    ):
         _lock_and_write_events(log_path, event)
 
 
@@ -128,16 +136,18 @@ def update_token_ledger(
         "default": {"input": 3.0, "output": 15.0},
     }
     r = rates.get(runtime.lower(), rates["default"])
-    
+
     cost = (input_tokens * r["input"] + output_tokens * r["output"]) / 1_000_000.0
-    
+
     baseline_input = int(input_tokens * baseline_multiplier)
     baseline_output = int(output_tokens * baseline_multiplier)
     baseline_total = baseline_input + baseline_output
-    baseline_cost = (baseline_input * r["input"] + baseline_output * r["output"]) / 1_000_000.0
-    
+    baseline_cost = (
+        baseline_input * r["input"] + baseline_output * r["output"]
+    ) / 1_000_000.0
+
     savings_usd = baseline_cost - cost
-    
+
     event = {
         "task_id": task_id,
         "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
@@ -151,25 +161,29 @@ def update_token_ledger(
         "baseline_cost_usd": baseline_cost,
         "savings_usd": savings_usd,
     }
-    
+
     events = ledger.setdefault("events", [])
     # Remove existing event for this task if we are re-running/resuming
     events = [e for e in events if e.get("task_id") != task_id]
     events.append(event)
     ledger["events"] = events
-    
+
     # Calculate summary
     total_input = sum(e.get("input_tokens", 0) for e in events)
     total_output = sum(e.get("output_tokens", 0) for e in events)
     total_tokens = total_input + total_output
     total_cost = sum(e.get("cost_usd", 0.0) for e in events)
-    
+
     total_baseline_tokens = sum(e.get("baseline_tokens", 0) for e in events)
     total_baseline_cost = sum(e.get("baseline_cost_usd", 0.0) for e in events)
     total_savings = total_baseline_cost - total_cost
-    
-    savings_pct = (total_savings / total_baseline_cost * 100.0) if total_baseline_cost > 0 else 0.0
-    
+
+    savings_pct = (
+        (total_savings / total_baseline_cost * 100.0)
+        if total_baseline_cost > 0
+        else 0.0
+    )
+
     ledger["summary"] = {
         "total_input_tokens": total_input,
         "total_output_tokens": total_output,
@@ -180,12 +194,14 @@ def update_token_ledger(
         "total_savings_usd": total_savings,
         "savings_percent": savings_pct,
     }
-    
+
     with open(ledger_path, "w", encoding="utf-8") as f:
         json.dump(ledger, f, indent=2)
 
 
-def run_validation_command(cmd: str, run_dir: Path, cwd: Path, console: Console) -> bool:
+def run_validation_command(
+    cmd: str, run_dir: Path, cwd: Path, console: Console
+) -> bool:
     """Run a validation command safely and log the results."""
     from niyam.core.security import CommandSecurityError, safe_run_command
 
@@ -196,7 +212,9 @@ def run_validation_command(cmd: str, run_dir: Path, cwd: Path, console: Console)
         res = safe_run_command(cmd, cwd=cwd, timeout=120)
     except CommandSecurityError as e:
         with _print_lock:
-            console.print(f"[bold red]🛑 Validation command blocked by security policy:[/] {e}")
+            console.print(
+                f"[bold red]🛑 Validation command blocked by security policy:[/] {e}"
+            )
         # Log the blocked command
         val_path = run_dir / "validation-results.md"
         timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
@@ -207,11 +225,11 @@ def run_validation_command(cmd: str, run_dir: Path, cwd: Path, console: Console)
                 f.write(f"**Command:** `{cmd}`\n")
                 f.write(f"**Status:** 🛑 BLOCKED — {e}\n\n")
         return False
-    
+
     # Save output to validation-results.md
     val_path = run_dir / "validation-results.md"
     timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
-    
+
     with _validation_lock:
         mode = "a" if val_path.exists() else "w"
         with open(val_path, mode, encoding="utf-8") as f:
@@ -221,13 +239,14 @@ def run_validation_command(cmd: str, run_dir: Path, cwd: Path, console: Console)
             f.write("### stdout\n```\n" + res.stdout + "\n```\n")
             if res.stderr:
                 f.write("### stderr\n```\n" + res.stderr + "\n```\n")
-            
+
     return res.returncode == 0
 
 
 def compute_sha256(file_path: Path) -> str:
     """Compute the SHA-256 hash of a file."""
     import hashlib
+
     if not file_path.exists() or not file_path.is_file():
         return "DELETED"
     h = hashlib.sha256()
@@ -243,7 +262,9 @@ def compute_sha256(file_path: Path) -> str:
 def get_snapshot(cwd: Path, is_git: bool) -> dict[str, str]:
     """Get a dictionary mapping relative file paths to their hashes or status."""
     if is_git:
-        res = subprocess.run(["git", "status", "--porcelain"], cwd=cwd, capture_output=True, text=True)
+        res = subprocess.run(
+            ["git", "status", "--porcelain"], cwd=cwd, capture_output=True, text=True
+        )
         snapshot = {}
         for line in res.stdout.splitlines():
             if line.strip():
@@ -255,7 +276,14 @@ def get_snapshot(cwd: Path, is_git: bool) -> dict[str, str]:
         return snapshot
     else:
         snapshot = {}
-        ignore_dirs = {".git", ".niyam", "__pycache__", ".venv", "node_modules", ".antigravitycli"}
+        ignore_dirs = {
+            ".git",
+            ".niyam",
+            "__pycache__",
+            ".venv",
+            "node_modules",
+            ".antigravitycli",
+        }
         for root, dirs, files in os.walk(cwd):
             dirs[:] = [d for d in dirs if d not in ignore_dirs]
             for f in files:
@@ -276,7 +304,14 @@ def backup_non_git_workspace(cwd: Path, backup_dir: Path) -> None:
         except Exception:
             pass
     backup_dir.mkdir(parents=True, exist_ok=True)
-    ignore_dirs = {".git", ".niyam", "__pycache__", ".venv", "node_modules", ".antigravitycli"}
+    ignore_dirs = {
+        ".git",
+        ".niyam",
+        "__pycache__",
+        ".venv",
+        "node_modules",
+        ".antigravitycli",
+    }
     for root, dirs, files in os.walk(cwd):
         dirs[:] = [d for d in dirs if d not in ignore_dirs]
         for f in files:
@@ -310,6 +345,7 @@ def restore_non_git_file(rel_path: str, backup_dir: Path, cwd: Path) -> None:
 
 # ── Git Worktree & Branching Utilities ─────────────────────────────────
 
+
 def is_git_repo(repo_root: Path) -> bool:
     """Check if the project root is a Git repository."""
     return (repo_root / ".git").exists()
@@ -325,7 +361,7 @@ def get_current_head(repo_root: Path) -> str:
     )
     if res.returncode == 0 and res.stdout.strip() != "HEAD":
         return res.stdout.strip()
-    
+
     res = subprocess.run(
         ["git", "rev-parse", "HEAD"],
         cwd=repo_root,
@@ -357,7 +393,9 @@ def branch_exists(repo_root: Path, branch_name: str) -> bool:
     return res.returncode == 0
 
 
-def cleanup_worktree(repo_root: Path, worktree_path: Path, branch_name: str, console: Console) -> None:
+def cleanup_worktree(
+    repo_root: Path, worktree_path: Path, branch_name: str, console: Console
+) -> None:
     """Force-remove a git worktree and cleanup directories."""
     if worktree_path.exists():
         subprocess.run(
@@ -383,13 +421,13 @@ def copy_niyam_to_worktree(repo_root: Path, worktree_path: Path) -> None:
     dst_niyam = worktree_path / ".niyam"
     if not src_niyam.is_dir():
         return
-    
+
     if dst_niyam.exists():
         try:
             shutil.rmtree(dst_niyam)
         except Exception:
             pass
-            
+
     dst_niyam.mkdir(parents=True, exist_ok=True)
     for item in src_niyam.iterdir():
         if item.name in ("runs", "worktrees"):
@@ -403,18 +441,22 @@ def copy_niyam_to_worktree(repo_root: Path, worktree_path: Path) -> None:
             pass
 
 
-def create_worktree(repo_root: Path, run_dir: Path, mission_id: str, task: dict, console: Console) -> Path:
+def create_worktree(
+    repo_root: Path, run_dir: Path, mission_id: str, task: dict, console: Console
+) -> Path:
     """Create a git worktree for a task, branching and merging dependencies."""
     task_id = task["id"]
     worktree_path = run_dir / "worktrees" / task_id
     branch_name = f"niyam-{mission_id}-{task_id}"
-    
+
     cleanup_worktree(repo_root, worktree_path, branch_name, console)
     worktree_path.parent.mkdir(parents=True, exist_ok=True)
-    
+
     if branch_exists(repo_root, branch_name):
         with _print_lock:
-            console.print(f"[{task_id}] [dim]Worktree branch {branch_name} already exists. Reusing branch...[/]")
+            console.print(
+                f"[{task_id}] [dim]Worktree branch {branch_name} already exists. Reusing branch...[/]"
+            )
         subprocess.run(
             ["git", "worktree", "add", str(worktree_path), branch_name],
             cwd=repo_root,
@@ -427,39 +469,63 @@ def create_worktree(repo_root: Path, run_dir: Path, mission_id: str, task: dict,
             parent_commit = get_current_head(repo_root)
         else:
             parent_commit = f"niyam-{mission_id}-{deps[0]}"
-            
+
         with _print_lock:
-            console.print(f"[{task_id}] [dim]Creating branch {branch_name} from parent {parent_commit}...[/]")
-            
+            console.print(
+                f"[{task_id}] [dim]Creating branch {branch_name} from parent {parent_commit}...[/]"
+            )
+
         subprocess.run(
-            ["git", "worktree", "add", "-b", branch_name, str(worktree_path), parent_commit],
+            [
+                "git",
+                "worktree",
+                "add",
+                "-b",
+                branch_name,
+                str(worktree_path),
+                parent_commit,
+            ],
             cwd=repo_root,
             check=True,
             capture_output=True,
         )
-        
+
         # Merge other dependencies if any
         if len(deps) > 1:
             for other_dep in deps[1:]:
                 other_branch = f"niyam-{mission_id}-{other_dep}"
                 with _print_lock:
-                    console.print(f"[{task_id}] [dim]Merging dependency branch {other_branch} into {branch_name}...[/]")
+                    console.print(
+                        f"[{task_id}] [dim]Merging dependency branch {other_branch} into {branch_name}...[/]"
+                    )
                 res = subprocess.run(
-                    ["git", "merge", other_branch, "-m", f"Merge dependency {other_dep}"],
+                    [
+                        "git",
+                        "merge",
+                        other_branch,
+                        "-m",
+                        f"Merge dependency {other_dep}",
+                    ],
                     cwd=worktree_path,
                     capture_output=True,
                     text=True,
                 )
                 if res.returncode != 0:
                     with _print_lock:
-                        console.print(f"[{task_id}] [bold red]Merge conflict:[/] Failed to merge {other_branch} into {branch_name}.\n{res.stderr or res.stdout}")
-                    raise RuntimeError(f"Merge conflict: failed to merge {other_branch} into {branch_name}")
-                    
+                        console.print(
+                            f"[{task_id}] [bold red]Merge conflict:[/] Failed to merge {other_branch} into {branch_name}.\n{res.stderr or res.stdout}"
+                        )
+                    raise RuntimeError(
+                        f"Merge conflict: failed to merge {other_branch} into {branch_name}"
+                    )
+
     copy_niyam_to_worktree(repo_root, worktree_path)
     return worktree_path
 
 
-def commit_worktree_changes(worktree_path: Path, task_id: str, console: Console) -> None:
+def commit_worktree_changes(
+    worktree_path: Path, task_id: str, console: Console
+) -> None:
     """Commit all changes made inside the worktree branch."""
     res_status = subprocess.run(
         ["git", "status", "--porcelain", "--", ":!.niyam"],
@@ -470,9 +536,11 @@ def commit_worktree_changes(worktree_path: Path, task_id: str, console: Console)
     )
     if not res_status.stdout.strip():
         with _print_lock:
-            console.print(f"[{task_id}] [dim]No changes to commit for task {task_id}.[/]")
+            console.print(
+                f"[{task_id}] [dim]No changes to commit for task {task_id}.[/]"
+            )
         return
-        
+
     subprocess.run(
         ["git", "add", "-A", "--", ":!.niyam"],
         cwd=worktree_path,
@@ -499,31 +567,47 @@ def find_leaf_tasks(tasks: list[dict]) -> list[str]:
     return list(all_ids - dependent_ids)
 
 
-def merge_final_changes(repo_root: Path, mission_id: str, tasks: list[dict], console: Console) -> None:
+def merge_final_changes(
+    repo_root: Path, mission_id: str, tasks: list[dict], console: Console
+) -> None:
     """Merge leaf task branches of the completed mission back into main workspace."""
     leaf_ids = find_leaf_tasks(tasks)
     if not leaf_ids:
         console.print("[yellow]No completed leaf tasks to merge.[/]")
         return
-        
+
     for leaf_id in leaf_ids:
         branch_name = f"niyam-{mission_id}-{leaf_id}"
         console.print(f"[cyan]Merging final branch {branch_name} into workspace...[/]")
-        
+
         res = subprocess.run(
-            ["git", "merge", branch_name, "-m", f"Merge completed mission task {leaf_id}"],
+            [
+                "git",
+                "merge",
+                branch_name,
+                "-m",
+                f"Merge completed mission task {leaf_id}",
+            ],
             cwd=repo_root,
             capture_output=True,
             text=True,
         )
         if res.returncode != 0:
-            console.print(f"[bold red]Merge conflict during final integration:[/] Failed to merge {branch_name} back to main workspace.\n{res.stderr or res.stdout}")
-            raise RuntimeError(f"Merge conflict during final integration of {branch_name}")
-            
-        console.print(f"[bold green]✓[/] Successfully integrated changes from branch [cyan]{branch_name}[/].")
+            console.print(
+                f"[bold red]Merge conflict during final integration:[/] Failed to merge {branch_name} back to main workspace.\n{res.stderr or res.stdout}"
+            )
+            raise RuntimeError(
+                f"Merge conflict during final integration of {branch_name}"
+            )
 
+        console.print(
+            f"[bold green]✓[/] Successfully integrated changes from branch [cyan]{branch_name}[/]."
+        )
 
-def delete_mission_branches(repo_root: Path, mission_id: str, tasks: list[dict], console: Console) -> None:
+
+def delete_mission_branches(
+    repo_root: Path, mission_id: str, tasks: list[dict], console: Console
+) -> None:
     """Clean up temporary task branches and prune worktrees."""
     for t in tasks:
         branch_name = f"niyam-{mission_id}-{t['id']}"
@@ -557,6 +641,7 @@ def get_mock_change_path(allowed_files: list[str], task_id: str) -> str:
 
 # ── Task Execution Thread Runner ───────────────────────────────────────
 
+
 def run_hooks(stage: str, context: dict, niyam_dir: Path, console: Console) -> None:
     """Run lifecycle hooks for a given stage."""
     hooks_file = niyam_dir / "hooks.yaml"
@@ -610,12 +695,14 @@ def run_hooks(stage: str, context: dict, niyam_dir: Path, console: Console) -> N
 
         with _print_lock:
             console.print(f"[dim]Executing hook: {cmd}[/]")
-        
+
         try:
             res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
             if res.returncode != 0:
                 with _print_lock:
-                    console.print(f"[yellow]Warning: hook execution returned exit code {res.returncode}[/]\n{res.stderr or res.stdout}")
+                    console.print(
+                        f"[yellow]Warning: hook execution returned exit code {res.returncode}[/]\n{res.stderr or res.stdout}"
+                    )
         except Exception as e:
             with _print_lock:
                 console.print(f"[yellow]Warning: hook execution failed: {e}[/]")
@@ -638,30 +725,36 @@ def execute_single_task(
     worktree_path = None
     branch_name = f"niyam-{mission_id}-{task_id}"
     run_hooks("pre_task", {"mission_id": mission_id, "task": task}, niyam_dir, console)
-    
+
     if use_worktree:
         try:
-            worktree_path = create_worktree(repo_root, run_dir, mission_id, task, console)
+            worktree_path = create_worktree(
+                repo_root, run_dir, mission_id, task, console
+            )
             task_cwd = worktree_path
         except Exception as e:
             with _print_lock:
                 console.print(f"[{task_id}] [bold red]Failed to setup worktree:[/] {e}")
             return False
-            
+
     # Formulate prompt
-    agent_file = (worktree_path / ".niyam" if use_worktree else niyam_dir) / "agents" / f"{task['agent']}.md"
+    agent_file = (
+        (worktree_path / ".niyam" if use_worktree else niyam_dir)
+        / "agents"
+        / f"{task['agent']}.md"
+    )
     agent_instruction = ""
     if agent_file.exists():
         agent_instruction = agent_file.read_text(encoding="utf-8")
-        
+
     requirement_file = run_dir / "requirement.md"
     requirement_content = ""
     if requirement_file.exists():
         requirement_content = requirement_file.read_text(encoding="utf-8")
-        
-    prompt_text = f"""TASK {task_id}: {task['title']}
-Type: {task.get('type', 'generic')}
-Assigned Agent: {task['agent']}
+
+    prompt_text = f"""TASK {task_id}: {task["title"]}
+Type: {task.get("type", "generic")}
+Assigned Agent: {task["agent"]}
 
 --- AGENT SYSTEM PROMPT ---
 {agent_instruction}
@@ -671,42 +764,47 @@ Assigned Agent: {task['agent']}
 
 --- INSTRUCTIONS ---
 Please execute the changes required for this task.
-Only modify files allowed under: {task.get('allowed_files') or task.get('files_allowed', ['Any'])}
+Only modify files allowed under: {task.get("allowed_files") or task.get("files_allowed", ["Any"])}
 Do not perform destructive operations.
 """
     # Write prompt
-    prompt_path = (worktree_path if use_worktree else run_dir) / f"task-{task_id}-prompt.md"
+    prompt_path = (
+        worktree_path if use_worktree else run_dir
+    ) / f"task-{task_id}-prompt.md"
     prompt_path.write_text(prompt_text, encoding="utf-8")
-    
+
     is_test = os.environ.get("NIYAM_TEST") == "1"
     success = True
-    
+
     is_git = is_git_repo(repo_root)
     backup_dir = run_dir / "backups" / task_id
     if not is_git:
         backup_non_git_workspace(task_cwd, backup_dir)
-        
+
     # Take before snapshot
     before_snapshot = get_snapshot(task_cwd, is_git)
 
     if is_test:
         with _print_lock:
             console.print(f"[{task_id}] [dim]Mocking execution of {task_id}...[/]")
-        log_execution_event(run_dir, "TASK_EXECUTION_MOCK", task_id, "Mocked execution successfully.")
-        
+        log_execution_event(
+            run_dir, "TASK_EXECUTION_MOCK", task_id, "Mocked execution successfully."
+        )
+
         # Write dummy file to record change in worktree git diff only if writes_files is True
         if use_worktree and worktree_path and task.get("writes_files", True):
             allowed = task.get("allowed_files") or task.get("files_allowed") or ["*"]
             mock_rel_path = get_mock_change_path(allowed, task_id)
             dummy_file = worktree_path / mock_rel_path
             dummy_file.parent.mkdir(parents=True, exist_ok=True)
-            dummy_file.write_text(f"Changes by task {task_id}", encoding="utf-8")
+            content = f"# Changes by task {task_id}\n" if mock_rel_path.endswith(".py") else f"Changes by task {task_id}"
+            dummy_file.write_text(content, encoding="utf-8")
     else:
         plan_data = load_plan(run_dir)
         mission_meta = plan_data.get("mission", {})
         orchestrator = task.get("runtime") or mission_meta.get("orchestrator", "claude")
         parallel_limit = mission_meta.get("parallel", 1)
-        
+
         if shutil.which(orchestrator):
             with _print_lock:
                 console.print(f"[{task_id}] [cyan]Invoking {orchestrator} CLI...[/]")
@@ -714,10 +812,17 @@ Do not perform destructive operations.
             try:
                 if parallel_limit == 1 and not non_interactive:
                     # Sequential: full interactive pass-through
-                    subprocess.run([orchestrator, str(prompt_path)], cwd=task_cwd, check=True, timeout=timeout)
+                    subprocess.run(
+                        [orchestrator, str(prompt_path)],
+                        cwd=task_cwd,
+                        check=True,
+                        timeout=timeout,
+                    )
                 else:
                     # Parallel or non-interactive: headless execution
-                    task_log_path = (worktree_path if use_worktree else run_dir) / f"task-{task_id}-output.log"
+                    task_log_path = (
+                        worktree_path if use_worktree else run_dir
+                    ) / f"task-{task_id}-output.log"
                     with open(task_log_path, "w", encoding="utf-8") as log_f:
                         subprocess.run(
                             [orchestrator, str(prompt_path)],
@@ -730,48 +835,71 @@ Do not perform destructive operations.
                         )
             except subprocess.TimeoutExpired as e:
                 with _print_lock:
-                    console.print(f"[{task_id}] [bold red]Orchestrator timed out after {timeout} seconds: {e}[/]")
+                    console.print(
+                        f"[{task_id}] [bold red]Orchestrator timed out after {timeout} seconds: {e}[/]"
+                    )
                     if parallel_limit > 1 or non_interactive:
-                        console.print(f"[{task_id}] To complete this task manually, run:")
+                        console.print(
+                            f"[{task_id}] To complete this task manually, run:"
+                        )
                         console.print(f"  [bold]cat {prompt_path}[/]")
-                log_execution_event(run_dir, "TASK_TIMEOUT", task_id, f"Execution timed out after {timeout} seconds.")
+                log_execution_event(
+                    run_dir,
+                    "TASK_TIMEOUT",
+                    task_id,
+                    f"Execution timed out after {timeout} seconds.",
+                )
                 success = False
             except subprocess.CalledProcessError as e:
                 if parallel_limit > 1 or non_interactive:
                     with _print_lock:
-                        console.print(f"[{task_id}] [red]Orchestrator failed in headless execution: {e}[/]")
-                        console.print(f"[{task_id}] To complete this task manually, run:")
+                        console.print(
+                            f"[{task_id}] [red]Orchestrator failed in headless execution: {e}[/]"
+                        )
+                        console.print(
+                            f"[{task_id}] To complete this task manually, run:"
+                        )
                         console.print(f"  [bold]cat {prompt_path}[/]")
                     success = False
                 else:
                     with _print_lock:
-                        console.print(f"[yellow]Warning: {orchestrator} command failed. Asking for manual confirmation.[/]")
+                        console.print(
+                            f"[yellow]Warning: {orchestrator} command failed. Asking for manual confirmation.[/]"
+                        )
                     try:
-                        input("Press Enter once you have completed the task manually in Claude/Codex...")
+                        input(
+                            "Press Enter once you have completed the task manually in Claude/Codex..."
+                        )
                     except (KeyboardInterrupt, EOFError):
                         success = False
         else:
             if parallel_limit > 1 or non_interactive:
                 with _print_lock:
-                    console.print(f"[{task_id}] [red]Orchestrator '{orchestrator}' CLI not found in PATH.[/]")
+                    console.print(
+                        f"[{task_id}] [red]Orchestrator '{orchestrator}' CLI not found in PATH.[/]"
+                    )
                     console.print(f"[{task_id}] To complete this task manually, run:")
                     console.print(f"  [bold]cat {prompt_path}[/]")
                 success = False
             else:
                 with _print_lock:
-                    console.print(f"[yellow]Orchestrator '{orchestrator}' CLI not found in PATH.[/]")
-                    console.print(f"Please run the task using the prompt at:")
+                    console.print(
+                        f"[yellow]Orchestrator '{orchestrator}' CLI not found in PATH.[/]"
+                    )
+                    console.print("Please run the task using the prompt at:")
                     console.print(f"  [bold]cat {prompt_path}[/]")
-                    console.print("\nPress Enter once you have executed the prompt and completed the work...")
+                    console.print(
+                        "\nPress Enter once you have executed the prompt and completed the work..."
+                    )
                 try:
                     input()
                 except (KeyboardInterrupt, EOFError):
                     success = False
-                    
+
     # Mechanical Task Boundary Check
     if success:
         after_snapshot = get_snapshot(task_cwd, is_git)
-        
+
         # Compare before and after to find all changed files
         changed_files = []
         if is_git:
@@ -795,6 +923,7 @@ Do not perform destructive operations.
 
         # Load global security policies
         from niyam.policies.guard import load_security_policy
+
         sec_data = load_security_policy(repo_root)
         deny_patterns = sec_data.get("deny_write_patterns", [])
         allow_patterns = sec_data.get("allow_write_patterns", [])
@@ -806,39 +935,67 @@ Do not perform destructive operations.
             else:
                 for f in changed_files:
                     # Check blocked_files patterns
-                    if blocked_files and any(fnmatch.fnmatch(f, pat) for pat in blocked_files):
+                    if blocked_files and any(
+                        fnmatch.fnmatch(f, pat) for pat in blocked_files
+                    ):
                         violated_files.append(f)
                         continue
                     # Check allowed_files patterns
-                    if allowed_files and "*" not in allowed_files and "Any" not in allowed_files:
+                    if (
+                        allowed_files
+                        and "*" not in allowed_files
+                        and "Any" not in allowed_files
+                    ):
                         if not any(fnmatch.fnmatch(f, pat) for pat in allowed_files):
                             violated_files.append(f)
                             continue
                     # Check global policies
-                    if deny_patterns and any(fnmatch.fnmatch(f, pat) for pat in deny_patterns):
+                    if deny_patterns and any(
+                        fnmatch.fnmatch(f, pat) for pat in deny_patterns
+                    ):
                         violated_files.append(f)
                         continue
-                    if allow_patterns and not any(fnmatch.fnmatch(f, pat) for pat in allow_patterns):
+                    if allow_patterns and not any(
+                        fnmatch.fnmatch(f, pat) for pat in allow_patterns
+                    ):
                         violated_files.append(f)
                         continue
 
         if violated_files:
             with _print_lock:
-                console.print(f"[{task_id}] [bold red]❌ Write restriction/boundary violation detected![/]")
+                console.print(
+                    f"[{task_id}] [bold red]❌ Write restriction/boundary violation detected![/]"
+                )
                 for f in violated_files:
                     console.print(f"  - Reverting unauthorized change to: [red]{f}[/]")
 
             if is_git:
                 for f in violated_files:
                     # Check if file existed in HEAD
-                    res_cat = subprocess.run(["git", "cat-file", "-e", f"HEAD:{f}"], cwd=task_cwd, capture_output=True)
+                    res_cat = subprocess.run(
+                        ["git", "cat-file", "-e", f"HEAD:{f}"],
+                        cwd=task_cwd,
+                        capture_output=True,
+                    )
                     if res_cat.returncode == 0:
                         # Existed in HEAD: reset and checkout to restore original
-                        subprocess.run(["git", "reset", "HEAD", f], cwd=task_cwd, capture_output=True)
-                        subprocess.run(["git", "checkout", "--", f], cwd=task_cwd, capture_output=True)
+                        subprocess.run(
+                            ["git", "reset", "HEAD", f],
+                            cwd=task_cwd,
+                            capture_output=True,
+                        )
+                        subprocess.run(
+                            ["git", "checkout", "--", f],
+                            cwd=task_cwd,
+                            capture_output=True,
+                        )
                     else:
                         # Newly created: remove from index if staged, and delete from disk
-                        subprocess.run(["git", "rm", "--cached", "-f", f], cwd=task_cwd, capture_output=True)
+                        subprocess.run(
+                            ["git", "rm", "--cached", "-f", f],
+                            cwd=task_cwd,
+                            capture_output=True,
+                        )
                         full_p = task_cwd / f
                         if full_p.exists() and not full_p.is_dir():
                             try:
@@ -853,7 +1010,7 @@ Do not perform destructive operations.
                 run_dir=run_dir,
                 niyam_dir=niyam_dir,
                 event_type="WRITE_VIOLATION",
-                details=f"Task {task_id} attempted unauthorized modifications to: {', '.join(violated_files)}"
+                details=f"Task {task_id} attempted unauthorized modifications to: {', '.join(violated_files)}",
             )
             success = False
 
@@ -875,7 +1032,7 @@ Do not perform destructive operations.
             ("build", v_cmds.build),
             ("test", v_cmds.test),
         ]
-        
+
         # Load validation commands from task
         task_validation = task.get("validation", {})
         task_cmds = []
@@ -883,7 +1040,7 @@ Do not perform destructive operations.
             task_cmds = task_validation.get("commands", [])
         elif hasattr(task_validation, "commands"):
             task_cmds = task_validation.commands
-        
+
         # Run standard checks
         for name, cmd in checks:
             if cmd:
@@ -891,16 +1048,20 @@ Do not perform destructive operations.
                 if not cmd_success:
                     success = False
                     with _print_lock:
-                        console.print(f"[{task_id}] [bold red]❌ Validation check '{name}' failed![/]")
+                        console.print(
+                            f"[{task_id}] [bold red]❌ Validation check '{name}' failed![/]"
+                        )
             else:
                 # Log explicitly skipped
                 val_path = run_dir / "validation-results.md"
-                timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
+                timestamp = (
+                    datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
+                )
                 with _validation_lock:
                     mode = "a" if val_path.exists() else "w"
                     with open(val_path, mode, encoding="utf-8") as f:
                         f.write(f"\n## Validation Check - {name} - {timestamp}\n")
-                        f.write(f"**Status:** ℹ SKIPPED — Not configured\n\n")
+                        f.write("**Status:** ℹ SKIPPED — Not configured\n\n")
 
         # Run task-specific checks
         if task_cmds:
@@ -909,7 +1070,9 @@ Do not perform destructive operations.
                 if not cmd_success:
                     success = False
                     with _print_lock:
-                        console.print(f"[{task_id}] [bold red]❌ Task validation command {i} failed![/]")
+                        console.print(
+                            f"[{task_id}] [bold red]❌ Task validation command {i} failed![/]"
+                        )
 
     # Record token usage in the ledger
     try:
@@ -924,19 +1087,25 @@ Do not perform destructive operations.
 
         # Estimate output tokens
         output_tokens = 0
-        task_log_path = (worktree_path if use_worktree else run_dir) / f"task-{task_id}-output.log"
+        task_log_path = (
+            worktree_path if use_worktree else run_dir
+        ) / f"task-{task_id}-output.log"
         if task_log_path.exists():
             try:
                 output_content = task_log_path.read_text(encoding="utf-8")
                 output_tokens = len(output_content) // 4
             except Exception:
                 pass
-        
+
         # If output_tokens is 0 (e.g. sequential mode, or log is empty), try git diff
         if output_tokens == 0 and is_git_repo(repo_root):
             try:
                 if use_worktree and worktree_path:
-                    diff_cmd = ["git", "diff", "HEAD~1", "HEAD"] if success else ["git", "diff"]
+                    diff_cmd = (
+                        ["git", "diff", "HEAD~1", "HEAD"]
+                        if success
+                        else ["git", "diff"]
+                    )
                     diff_res = subprocess.run(
                         diff_cmd,
                         cwd=worktree_path,
@@ -984,7 +1153,7 @@ Do not perform destructive operations.
             output_tokens=output_tokens,
             baseline_multiplier=baseline_multiplier,
         )
-        
+
         # Add 'estimated: true' label to ledger event for token governance
         ledger_path = run_dir / "token-ledger.json"
         if ledger_path.exists():
@@ -1001,14 +1170,21 @@ Do not perform destructive operations.
 
     except Exception as e:
         with _print_lock:
-            console.print(f"[{task_id}] [yellow]Warning: Failed to update token ledger:[/] {e}")
+            console.print(
+                f"[{task_id}] [yellow]Warning: Failed to update token ledger:[/] {e}"
+            )
 
     # Commit changes if worktree is active and task succeeded
     if success and use_worktree and worktree_path:
         try:
             commit_worktree_changes(worktree_path, task_id, console)
             # Retrieve and record commit SHA of this task
-            res = subprocess.run(["git", "rev-parse", "HEAD"], cwd=worktree_path, capture_output=True, text=True)
+            res = subprocess.run(
+                ["git", "rev-parse", "HEAD"],
+                cwd=worktree_path,
+                capture_output=True,
+                text=True,
+            )
             if res.returncode == 0:
                 task_commit_sha = res.stdout.strip()
                 # Update task-list.yaml and mission-plan.yaml in execution flow
@@ -1022,22 +1198,24 @@ Do not perform destructive operations.
             with _print_lock:
                 console.print(f"[{task_id}] [bold red]Failed to commit changes:[/] {e}")
             success = False
-            
+
     # Cleanup worktree
     if use_worktree and worktree_path:
         cleanup_worktree(repo_root, worktree_path, branch_name, console)
-        
+
     # Run post_task hook
     task_copy = dict(task)
     task_copy["status"] = "completed" if success else "failed"
-    run_hooks("post_task", {"mission_id": mission_id, "task": task_copy}, niyam_dir, console)
-        
-    return success
+    run_hooks(
+        "post_task", {"mission_id": mission_id, "task": task_copy}, niyam_dir, console
+    )
 
+    return success
 
 
 # ── Public Entry Points ───────────────────────────────────────────────
 
+
 def run_mission_start(
     console: Console,
     parallel: int | None = None,
@@ -1078,7 +1256,7 @@ def run_mission_start(
             auto_approve_allowed = True
             try:
                 config = load_niyam_config(repo_root)
-                if hasattr(config.guard, 'allow_ci_auto_approve'):
+                if hasattr(config.guard, "allow_ci_auto_approve"):
                     auto_approve_allowed = config.guard.allow_ci_auto_approve
             except Exception:
                 pass  # If config can't be loaded, allow (backward compat)
@@ -1090,16 +1268,29 @@ def run_mission_start(
                 )
                 raise SystemExit(1)
 
-            console.print("[cyan]Non-interactive mode & NIYAM_CI_AUTO_APPROVE=1: Auto-approving mission...[/]")
-            console.print("[yellow]⚠ Warning: Mission approval gate was bypassed via environment variable.[/]")
+            console.print(
+                "[cyan]Non-interactive mode & NIYAM_CI_AUTO_APPROVE=1: Auto-approving mission...[/]"
+            )
+            console.print(
+                "[yellow]⚠ Warning: Mission approval gate was bypassed via environment variable.[/]"
+            )
             approval_data = {
                 "approved": True,
                 "auto_approved": True,
-                "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
+                "timestamp": datetime.now(timezone.utc)
+                .isoformat()
+                .replace("+00:00", "Z"),
             }
-            approval_path.write_text(json.dumps(approval_data, indent=2), encoding="utf-8")
+            approval_path.write_text(
+                json.dumps(approval_data, indent=2), encoding="utf-8"
+            )
             # Log the auto-approve as a policy event for audit trail
-            log_execution_event(run_dir, "POLICY_WARNING", "", "Mission auto-approved via NIYAM_CI_AUTO_APPROVE=1 (approval gate bypassed).")
+            log_execution_event(
+                run_dir,
+                "POLICY_WARNING",
+                "",
+                "Mission auto-approved via NIYAM_CI_AUTO_APPROVE=1 (approval gate bypassed).",
+            )
         else:
             console.print("[bold red]Error:[/] Mission has not been approved.")
             raise SystemExit(1)
@@ -1119,27 +1310,35 @@ def run_mission_start(
 
     parallel_limit = parallel if parallel is not None else plan_parallel
     use_worktree = worktree if worktree is not None else plan_worktree
-    
+
     # Check Git repository requirement
     is_git = is_git_repo(repo_root)
     if use_worktree:
         if not is_git:
             if worktree is True:
-                console.print("[bold red]Error:[/] Git worktree isolation was requested, but this is not a Git repository.")
+                console.print(
+                    "[bold red]Error:[/] Git worktree isolation was requested, but this is not a Git repository."
+                )
                 raise SystemExit(1)
             else:
                 if parallel_limit > 1:
-                    console.print("[bold red]Error:[/] Parallel execution (concurrency > 1) requires a Git repository for worktree isolation.")
+                    console.print(
+                        "[bold red]Error:[/] Parallel execution (concurrency > 1) requires a Git repository for worktree isolation."
+                    )
                     raise SystemExit(1)
                 else:
                     use_worktree = False
         elif not git_has_commits(repo_root):
             if worktree is True:
-                console.print("[bold red]Error:[/] Git worktree isolation requires the repository to have at least one commit.")
+                console.print(
+                    "[bold red]Error:[/] Git worktree isolation requires the repository to have at least one commit."
+                )
                 raise SystemExit(1)
             else:
                 if parallel_limit > 1:
-                    console.print("[bold red]Error:[/] Parallel execution (concurrency > 1) requires a Git repository with at least one commit for worktree isolation.")
+                    console.print(
+                        "[bold red]Error:[/] Parallel execution (concurrency > 1) requires a Git repository with at least one commit for worktree isolation."
+                    )
                     raise SystemExit(1)
                 else:
                     use_worktree = False
@@ -1148,15 +1347,25 @@ def run_mission_start(
     plan_data["mission"]["parallel"] = parallel_limit
     plan_data["mission"]["worktree"] = use_worktree
     plan_data["mission"]["status"] = "running"
-    if is_git and git_has_commits(repo_root) and not plan_data["mission"].get("base_sha"):
-        res = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo_root, capture_output=True, text=True)
+    if (
+        is_git
+        and git_has_commits(repo_root)
+        and not plan_data["mission"].get("base_sha")
+    ):
+        res = subprocess.run(
+            ["git", "rev-parse", "HEAD"], cwd=repo_root, capture_output=True, text=True
+        )
         if res.returncode == 0:
             plan_data["mission"]["base_sha"] = res.stdout.strip()
     save_plan(run_dir, plan_data)
-    log_execution_event(run_dir, "MISSION_STARTED", "", f"Mission execution started (parallel={parallel_limit}, worktree={use_worktree}).")
+    log_execution_event(
+        run_dir,
+        "MISSION_STARTED",
+        "",
+        f"Mission execution started (parallel={parallel_limit}, worktree={use_worktree}).",
+    )
     run_hooks("pre_mission", {"mission_id": mission_id}, niyam_dir, console)
 
-
     # Read project.yaml validation commands
     project_config = None
     try:
@@ -1169,21 +1378,28 @@ def run_mission_start(
     failed_tasks = {t["id"] for t in tasks if t["status"] == "failed"}
     running_tasks = set()
     futures_map = {}
-    
+
     import concurrent.futures
-    
+
     with concurrent.futures.ThreadPoolExecutor(max_workers=parallel_limit) as executor:
         while True:
             # Check if mission has been paused from outside
             current_plan = load_plan(run_dir)
             if current_plan["mission"]["status"] == "paused":
                 with _print_lock:
-                    console.print("[yellow]Mission execution paused. Waiting for active tasks to finish...[/]")
+                    console.print(
+                        "[yellow]Mission execution paused. Waiting for active tasks to finish...[/]"
+                    )
                 if futures_map:
                     concurrent.futures.wait(futures_map.keys())
-                run_hooks("post_mission", {"mission_id": mission_id, "mission_status": "paused"}, niyam_dir, console)
+                run_hooks(
+                    "post_mission",
+                    {"mission_id": mission_id, "mission_status": "paused"},
+                    niyam_dir,
+                    console,
+                )
                 return
-                
+
             # Find ready tasks
             ready_tasks = []
             task_by_id = {task["id"]: task for task in tasks}
@@ -1193,16 +1409,21 @@ def run_mission_start(
                     deps = t.get("depends_on", [])
                     finished_statuses = {"completed", "failed", "skipped"}
                     dep_tasks = [task_by_id[dep] for dep in deps if dep in task_by_id]
-                    
+
                     if all(dt["status"] in finished_statuses for dt in dep_tasks):
                         # If any dependency failed, this task must be skipped
                         if any(dt["status"] == "failed" for dt in dep_tasks):
                             t["status"] = "skipped"
                             save_plan(run_dir, plan_data)
-                            log_execution_event(run_dir, "TASK_SKIPPED", t_id, f"Dependency failed, skipping task.")
+                            log_execution_event(
+                                run_dir,
+                                "TASK_SKIPPED",
+                                t_id,
+                                "Dependency failed, skipping task.",
+                            )
                             continue
                         ready_tasks.append(t)
-                        
+
             # Submit ready tasks up to concurrency capacity
             for t in ready_tasks:
                 if len(running_tasks) < parallel_limit:
@@ -1210,15 +1431,19 @@ def run_mission_start(
                     running_tasks.add(t_id)
                     t["status"] = "running"
                     save_plan(run_dir, plan_data)
-                    log_execution_event(run_dir, "TASK_STARTED", t_id, f"Running task: {t['title']}")
-                    
+                    log_execution_event(
+                        run_dir, "TASK_STARTED", t_id, f"Running task: {t['title']}"
+                    )
+
                     with _print_lock:
-                        console.print(Panel(
-                            f"Running Task [cyan]{t_id}[/]: {t['title']}\nAgent: [bold]{t['agent']}[/]",
-                            title=f"[bold]Task {t_id}[/]",
-                            border_style="cyan"
-                        ))
-                    
+                        console.print(
+                            Panel(
+                                f"Running Task [cyan]{t_id}[/]: {t['title']}\nAgent: [bold]{t['agent']}[/]",
+                                title=f"[bold]Task {t_id}[/]",
+                                border_style="cyan",
+                            )
+                        )
+
                     # Submit task execution
                     future = executor.submit(
                         execute_single_task,
@@ -1233,57 +1458,91 @@ def run_mission_start(
                         non_interactive=non_interactive,
                     )
                     futures_map[future] = t
-                    
+
             # If nothing is running and no more tasks are ready, we are done
             if not futures_map:
                 break
-                
+
             # Wait for at least one future to complete
-            done, _ = concurrent.futures.wait(futures_map.keys(), return_when=concurrent.futures.FIRST_COMPLETED)
-            
+            done, _ = concurrent.futures.wait(
+                futures_map.keys(), return_when=concurrent.futures.FIRST_COMPLETED
+            )
+
             for future in done:
                 t = futures_map.pop(future)
                 t_id = t["id"]
                 running_tasks.remove(t_id)
-                
+
                 try:
                     success = future.result()
                     if success:
                         t["status"] = "completed"
                         completed_tasks.add(t_id)
                         save_plan(run_dir, plan_data)
-                        log_execution_event(run_dir, "TASK_COMPLETED", t_id, f"Completed task: {t['title']}")
+                        log_execution_event(
+                            run_dir,
+                            "TASK_COMPLETED",
+                            t_id,
+                            f"Completed task: {t['title']}",
+                        )
                         with _print_lock:
-                            console.print(f"[bold green]✓[/] Task {t_id} completed successfully.\n")
+                            console.print(
+                                f"[bold green]✓[/] Task {t_id} completed successfully.\n"
+                            )
                     else:
                         t["status"] = "failed"
                         failed_tasks.add(t_id)
                         save_plan(run_dir, plan_data)
-                        log_execution_event(run_dir, "TASK_FAILED", t_id, f"Task execution failed.")
+                        log_execution_event(
+                            run_dir, "TASK_FAILED", t_id, "Task execution failed."
+                        )
                         with _print_lock:
                             console.print(f"[bold red]❌[/] Task {t_id} failed.\n")
                 except Exception as e:
                     t["status"] = "failed"
                     failed_tasks.add(t_id)
                     save_plan(run_dir, plan_data)
-                    log_execution_event(run_dir, "TASK_FAILED", t_id, f"Exception during task execution: {e}")
+                    log_execution_event(
+                        run_dir,
+                        "TASK_FAILED",
+                        t_id,
+                        f"Exception during task execution: {e}",
+                    )
                     with _print_lock:
-                        console.print(f"[bold red]❌[/] Task {t_id} failed with exception: {e}\n")
+                        console.print(
+                            f"[bold red]❌[/] Task {t_id} failed with exception: {e}\n"
+                        )
 
     # Determine final mission status
     final_plan = load_plan(run_dir)
     tasks_list = final_plan.get("tasks", [])
     any_failed = any(t["status"] == "failed" for t in tasks_list)
     any_skipped_due_to_failure = any(t["status"] == "skipped" for t in tasks_list)
-    
+
     if any_failed or any_skipped_due_to_failure:
         final_plan["mission"]["status"] = "failed"
         save_plan(run_dir, final_plan)
-        log_execution_event(run_dir, "MISSION_FAILED", "", "Mission execution failed due to task failures.")
-        run_hooks("post_mission", {"mission_id": mission_id, "mission_status": "failed"}, niyam_dir, console)
-        console.print(Panel("[bold red]❌ Mission execution failed.[/]", title="[bold red]Mission Failed[/]", border_style="red"))
+        log_execution_event(
+            run_dir,
+            "MISSION_FAILED",
+            "",
+            "Mission execution failed due to task failures.",
+        )
+        run_hooks(
+            "post_mission",
+            {"mission_id": mission_id, "mission_status": "failed"},
+            niyam_dir,
+            console,
+        )
+        console.print(
+            Panel(
+                "[bold red]❌ Mission execution failed.[/]",
+                title="[bold red]Mission Failed[/]",
+                border_style="red",
+            )
+        )
         raise SystemExit(1)
-        
+
     # Success integration (merge back if worktree was used)
     if use_worktree and is_git:
         try:
@@ -1298,9 +1557,22 @@ def run_mission_start(
     # Complete mission
     final_plan["mission"]["status"] = "completed"
     save_plan(run_dir, final_plan)
-    log_execution_event(run_dir, "MISSION_COMPLETED", "", "All tasks completed successfully.")
-    run_hooks("post_mission", {"mission_id": mission_id, "mission_status": "completed"}, niyam_dir, console)
-    console.print(Panel("[bold green]✓ Mission execution completed successfully![/]\nRun `niyam mission report` to generate evidence.", title="[bold green]Mission Success[/]", border_style="green"))
+    log_execution_event(
+        run_dir, "MISSION_COMPLETED", "", "All tasks completed successfully."
+    )
+    run_hooks(
+        "post_mission",
+        {"mission_id": mission_id, "mission_status": "completed"},
+        niyam_dir,
+        console,
+    )
+    console.print(
+        Panel(
+            "[bold green]✓ Mission execution completed successfully![/]\nRun `niyam mission report` to generate evidence.",
+            title="[bold green]Mission Success[/]",
+            border_style="green",
+        )
+    )
 
 
 def run_mission_pause(console: Console) -> None:
@@ -1361,7 +1633,9 @@ def run_mission_resume(
         return
 
     # Start the execution
-    run_mission_start(console, parallel=parallel, worktree=worktree, non_interactive=non_interactive)
+    run_mission_start(
+        console, parallel=parallel, worktree=worktree, non_interactive=non_interactive
+    )
 
 
 def run_mission_retry(
@@ -1389,7 +1663,7 @@ def run_mission_retry(
 
     tasks = plan_data.get("tasks", [])
     failed_any = False
-    
+
     # Helper to recursively reset skipped tasks depending on failed ones
     def reset_downstream(task_id: str):
         for t in tasks:
@@ -1409,9 +1683,15 @@ def run_mission_retry(
 
     plan_data["mission"]["status"] = "approved"
     save_plan(run_dir, plan_data)
-    log_execution_event(run_dir, "MISSION_RETRIED", "", "Retrying failed/skipped tasks.")
-    console.print(f"[bold green]✓[/] Re-queued tasks. Resuming mission [cyan]{mission_id}[/]...")
-    run_mission_start(console, parallel=parallel, worktree=worktree, non_interactive=non_interactive)
+    log_execution_event(
+        run_dir, "MISSION_RETRIED", "", "Retrying failed/skipped tasks."
+    )
+    console.print(
+        f"[bold green]✓[/] Re-queued tasks. Resuming mission [cyan]{mission_id}[/]..."
+    )
+    run_mission_start(
+        console, parallel=parallel, worktree=worktree, non_interactive=non_interactive
+    )
 
 
 def run_mission_skip(
@@ -1446,15 +1726,23 @@ def run_mission_skip(
             break
 
     if not target_task:
-        console.print(f"[bold red]Error:[/] Task '{task_id}' not found in mission plan.")
+        console.print(
+            f"[bold red]Error:[/] Task '{task_id}' not found in mission plan."
+        )
         raise SystemExit(1)
 
     target_task["status"] = "skipped"
     plan_data["mission"]["status"] = "approved"
     save_plan(run_dir, plan_data)
-    log_execution_event(run_dir, "TASK_SKIPPED_BY_USER", task_id, "Task skipped by user intervention.")
-    console.print(f"[bold green]✓[/] Marked task [cyan]{task_id}[/] as skipped. Resuming mission...")
-    run_mission_start(console, parallel=parallel, worktree=worktree, non_interactive=non_interactive)
+    log_execution_event(
+        run_dir, "TASK_SKIPPED_BY_USER", task_id, "Task skipped by user intervention."
+    )
+    console.print(
+        f"[bold green]✓[/] Marked task [cyan]{task_id}[/] as skipped. Resuming mission..."
+    )
+    run_mission_start(
+        console, parallel=parallel, worktree=worktree, non_interactive=non_interactive
+    )
 
 
 def run_mission_rollback(console: Console) -> None:
@@ -1477,14 +1765,25 @@ def run_mission_rollback(console: Console) -> None:
     base_sha = plan_data["mission"].get("base_sha")
 
     if not base_sha:
-        console.print("[yellow]No base commit SHA recorded for this mission. Cannot rollback automatically.[/]")
+        console.print(
+            "[yellow]No base commit SHA recorded for this mission. Cannot rollback automatically.[/]"
+        )
         return
 
-    console.print(f"[cyan]Rolling back changes to base commit [bold]{base_sha}[/]...[/]")
-    res = subprocess.run(["git", "checkout", base_sha, "--", "."], cwd=repo_root, capture_output=True, text=True)
+    console.print(
+        f"[cyan]Rolling back changes to base commit [bold]{base_sha}[/]...[/]"
+    )
+    res = subprocess.run(
+        ["git", "checkout", base_sha, "--", "."],
+        cwd=repo_root,
+        capture_output=True,
+        text=True,
+    )
     if res.returncode == 0:
         plan_data["mission"]["status"] = "failed"
         save_plan(run_dir, plan_data)
         console.print("[bold green]✓[/] Workspace rolled back successfully.")
     else:
-        console.print(f"[bold red]Failed to rollback changes:[/] {res.stderr or res.stdout}")
+        console.print(
+            f"[bold red]Failed to rollback changes:[/] {res.stderr or res.stdout}"
+        )
diff --git a/niyam/mission/planner.py b/niyam/mission/planner.py
index fc3f6cd..4a8b2f2 100644
--- a/niyam/mission/planner.py
+++ b/niyam/mission/planner.py
@@ -29,7 +29,17 @@ def get_repo_map(repo_root: Path) -> str:
             return res.stdout.strip()
 
     files = []
-    ignore_dirs = {".git", ".niyam", "__pycache__", ".venv", ".pytest_cache", "node_modules", "build", "dist", ".antigravitycli"}
+    ignore_dirs = {
+        ".git",
+        ".niyam",
+        "__pycache__",
+        ".venv",
+        ".pytest_cache",
+        "node_modules",
+        "build",
+        "dist",
+        ".antigravitycli",
+    }
     for root, dirs, filenames in os.walk(repo_root):
         dirs[:] = [d for d in dirs if d not in ignore_dirs]
         for f in filenames:
@@ -45,7 +55,9 @@ def get_repo_map(repo_root: Path) -> str:
 def extract_yaml_or_json(text: str) -> dict | None:
     """Extract and parse YAML or JSON block from text."""
     # Try looking for ```yaml ... ```
-    yaml_block = re.search(r"```(?:yaml|yml)?\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
+    yaml_block = re.search(
+        r"```(?:yaml|yml)?\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE
+    )
     if yaml_block:
         try:
             parsed = yaml.safe_load(yaml_block.group(1))
@@ -75,7 +87,9 @@ def extract_yaml_or_json(text: str) -> dict | None:
     return None
 
 
-def build_planner_prompt(requirement: str, repo_map: str, available_agents: list[str]) -> str:
+def build_planner_prompt(
+    requirement: str, repo_map: str, available_agents: list[str]
+) -> str:
     agents_str = ", ".join(available_agents)
     return f"""You are the Niyam planning engine.
 Convert the following requirement into a bounded, dependency-resolved task plan.
@@ -141,8 +155,16 @@ DEFAULT_TEMPLATES = {
         "name": "api-endpoint",
         "description": "Add a new API endpoint",
         "variables": [
-            {"name": "endpoint_path", "prompt": "Enter the API route path (e.g. /api/v1/users)", "default": "/api/v1/resource"},
-            {"name": "method", "prompt": "HTTP Method (GET/POST/PUT/DELETE)", "default": "GET"},
+            {
+                "name": "endpoint_path",
+                "prompt": "Enter the API route path (e.g. /api/v1/users)",
+                "default": "/api/v1/resource",
+            },
+            {
+                "name": "method",
+                "prompt": "HTTP Method (GET/POST/PUT/DELETE)",
+                "default": "GET",
+            },
         ],
         "tasks": [
             {
@@ -184,14 +206,18 @@ DEFAULT_TEMPLATES = {
                 "type": "validation",
                 "agent": "qa-reviewer",
                 "depends_on": ["T4"],
-            }
-        ]
+            },
+        ],
     },
     "bugfix": {
         "name": "bugfix",
         "description": "Fix a bug with TDD",
         "variables": [
-            {"name": "bug_description", "prompt": "Brief description of the bug", "default": "Fix unexpected error"},
+            {
+                "name": "bug_description",
+                "prompt": "Brief description of the bug",
+                "default": "Fix unexpected error",
+            },
         ],
         "tasks": [
             {
@@ -225,14 +251,18 @@ DEFAULT_TEMPLATES = {
                 "type": "validation",
                 "agent": "qa-reviewer",
                 "depends_on": ["T3"],
-            }
-        ]
+            },
+        ],
     },
     "refactor": {
         "name": "refactor",
         "description": "Refactor code without changing behavior",
         "variables": [
-            {"name": "target_file", "prompt": "Path to file/module to refactor", "default": ""},
+            {
+                "name": "target_file",
+                "prompt": "Path to file/module to refactor",
+                "default": "",
+            },
         ],
         "tasks": [
             {
@@ -257,9 +287,9 @@ DEFAULT_TEMPLATES = {
                 "type": "validation",
                 "agent": "qa-reviewer",
                 "depends_on": ["T2"],
-            }
-        ]
-    }
+            },
+        ],
+    },
 }
 
 
@@ -282,20 +312,28 @@ def run_mission_plan(
     niyam_dir = get_niyam_dir(repo_root)
 
     if not niyam_dir.exists():
-        console.print("[bold red]Error:[/] Not a Niyam workspace. Run `niyam init` first.")
+        console.print(
+            "[bold red]Error:[/] Not a Niyam workspace. Run `niyam init` first."
+        )
         raise SystemExit(1)
 
     req_file = Path(requirements_path)
     if req_file.exists() and req_file.is_file():
         requirement_content = req_file.read_text(encoding="utf-8")
-        clean_name = "".join(c if c.isalnum() else "-" for c in req_file.stem).strip("-").lower()
+        clean_name = (
+            "".join(c if c.isalnum() else "-" for c in req_file.stem).strip("-").lower()
+        )
         if not clean_name:
             clean_name = "requirement"
         is_inline = False
     else:
         requirement_content = requirements_path
         # Limit clean_name to 30 chars
-        clean_name = "".join(c if c.isalnum() else "-" for c in requirements_path[:30]).strip("-").lower()
+        clean_name = (
+            "".join(c if c.isalnum() else "-" for c in requirements_path[:30])
+            .strip("-")
+            .lower()
+        )
         if not clean_name:
             clean_name = "inline"
         is_inline = True
@@ -323,9 +361,19 @@ def run_mission_plan(
     if not available_agents:
         available_agents = ["default-agent"]
 
-    backend_agent = "backend-specialist" if "backend-specialist" in available_agents else available_agents[0]
-    security_agent = "security-reviewer" if "security-reviewer" in available_agents else available_agents[0]
-    qa_agent = "qa-reviewer" if "qa-reviewer" in available_agents else available_agents[0]
+    backend_agent = (
+        "backend-specialist"
+        if "backend-specialist" in available_agents
+        else available_agents[0]
+    )
+    security_agent = (
+        "security-reviewer"
+        if "security-reviewer" in available_agents
+        else available_agents[0]
+    )
+    qa_agent = (
+        "qa-reviewer" if "qa-reviewer" in available_agents else available_agents[0]
+    )
 
     plan_data = None
 
@@ -346,16 +394,20 @@ def run_mission_plan(
                 with open(template_file, encoding="utf-8") as f:
                     template_data = yaml.safe_load(f)
             except Exception as e:
-                console.print(f"[yellow]Warning: failed to load template file '{template_file}': {e}[/]")
-        
+                console.print(
+                    f"[yellow]Warning: failed to load template file '{template_file}': {e}[/]"
+                )
+
         if not template_data:
             if template in DEFAULT_TEMPLATES:
                 template_data = DEFAULT_TEMPLATES[template]
                 console.print(f"[dim]Using built-in template '{template}'...[/]")
             else:
-                console.print(f"[bold red]Error:[/] Mission template '{template}' not found.")
+                console.print(
+                    f"[bold red]Error:[/] Mission template '{template}' not found."
+                )
                 raise SystemExit(1)
-        
+
         # Resolve variables
         variables = template_data.get("variables", [])
         var_values = {}
@@ -363,19 +415,22 @@ def run_mission_plan(
             var_name = var.get("name")
             prompt_text = var.get("prompt", f"Value for {var_name}")
             default_val = var.get("default", "")
-            
+
             # If running in non-interactive/test, use default
-            is_non_interactive = os.environ.get("NIYAM_TEST") == "1" or "pytest" in sys.modules
+            is_non_interactive = (
+                os.environ.get("NIYAM_TEST") == "1" or "pytest" in sys.modules
+            )
             if is_non_interactive:
                 var_values[var_name] = default_val
             else:
                 from rich.prompt import Prompt
+
                 try:
                     var_values[var_name] = Prompt.ask(prompt_text, default=default_val)
                 except (KeyboardInterrupt, EOFError):
                     console.print("\n[red]Mission planning aborted.[/]")
                     raise SystemExit(1)
-                
+
         # Render tasks
         raw_tasks = template_data.get("tasks", [])
         rendered_tasks = []
@@ -398,39 +453,48 @@ def run_mission_plan(
             if t_writes is None:
                 t_writes = t_type == "implementation"
             t_files = t.get("files_allowed") or ["*"]
-            
+
             # String replacement for variables
             for var_name, var_val in var_values.items():
                 pattern = "{{" + var_name + "}}"
                 t_title = t_title.replace(pattern, var_val)
-                
-            rendered_tasks.append({
-                "id": t_id,
-                "title": t_title,
-                "type": t_type,
-                "status": "pending",
-                "agent": t_agent,
-                "runtime": t_rt,
-                "depends_on": t_deps,
-                "writes_files": t_writes,
-                "files_allowed": t_files,
-            })
-            
+
+            rendered_tasks.append(
+                {
+                    "id": t_id,
+                    "title": t_title,
+                    "type": t_type,
+                    "status": "pending",
+                    "agent": t_agent,
+                    "runtime": t_rt,
+                    "depends_on": t_deps,
+                    "writes_files": t_writes,
+                    "files_allowed": t_files,
+                }
+            )
+
         plan_data = {
             "mission": {
                 "id": mission_id,
                 "requirement": str(requirements_path),
-                "created": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
+                "created": datetime.now(timezone.utc)
+                .isoformat()
+                .replace("+00:00", "Z"),
                 "status": "planned",
-                "orchestrator": runtime_override or (config.runtimes[0] if config and config.runtimes else "claude"),
+                "orchestrator": runtime_override
+                or (config.runtimes[0] if config and config.runtimes else "claude"),
                 "parallel": 1,
             },
-            "tasks": rendered_tasks
+            "tasks": rendered_tasks,
         }
-        console.print(f"[bold green]✓[/] Generated mission plan from template '[cyan]{template}[/]' with {len(rendered_tasks)} tasks.")
-    
+        console.print(
+            f"[bold green]✓[/] Generated mission plan from template '[cyan]{template}[/]' with {len(rendered_tasks)} tasks."
+        )
+
     # 5. Try AI planning if not in basic unit tests
-    is_test = (os.environ.get("NIYAM_TEST") == "1" or "pytest" in sys.modules) and os.environ.get("NIYAM_TEST_PLANNER") != "1"
+    is_test = (
+        os.environ.get("NIYAM_TEST") == "1" or "pytest" in sys.modules
+    ) and os.environ.get("NIYAM_TEST_PLANNER") != "1"
     config = None
     try:
         config = load_niyam_config(repo_root)
@@ -440,23 +504,26 @@ def run_mission_plan(
     if config and not is_test:
         orchestrator = config.runtimes[0] if config.runtimes else "claude"
         if shutil.which(orchestrator):
-
             repo_map = get_repo_map(repo_root)
-            prompt = build_planner_prompt(requirement_content, repo_map, available_agents)
-            
+            prompt = build_planner_prompt(
+                requirement_content, repo_map, available_agents
+            )
+
             # Write prompt for trace
             (run_dir / "planner-prompt.md").write_text(prompt, encoding="utf-8")
-            
+
             console.print(f"[dim]Invoking AI planning engine '{orchestrator}'...[/]")
             cmd = [orchestrator, "-p", prompt]
             if orchestrator == "gemini":
                 cmd.append("--skip-trust")
-                
+
             try:
                 res = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
                 raw_output = (res.stdout or "") + "\n" + (res.stderr or "")
-                (run_dir / "planner-output.raw.txt").write_text(raw_output, encoding="utf-8")
-                
+                (run_dir / "planner-output.raw.txt").write_text(
+                    raw_output, encoding="utf-8"
+                )
+
                 if res.returncode == 0:
                     parsed = extract_yaml_or_json(raw_output)
                     if parsed and isinstance(parsed, dict) and "tasks" in parsed:
@@ -483,43 +550,57 @@ def run_mission_plan(
                             t_files = t.get("files_allowed") or ["*"]
                             if isinstance(t_files, str):
                                 t_files = [t_files]
-                            normalized_tasks.append({
-                                "id": t_id,
-                                "title": t_title,
-                                "type": t_type,
-                                "status": "pending",
-                                "agent": t_agent,
-                                "runtime": t_runtime,
-                                "depends_on": t_deps,
-                                "writes_files": t_writes,
-                                "files_allowed": t_files,
-                            })
+                            normalized_tasks.append(
+                                {
+                                    "id": t_id,
+                                    "title": t_title,
+                                    "type": t_type,
+                                    "status": "pending",
+                                    "agent": t_agent,
+                                    "runtime": t_runtime,
+                                    "depends_on": t_deps,
+                                    "writes_files": t_writes,
+                                    "files_allowed": t_files,
+                                }
+                            )
                         plan_data = {
                             "mission": {
                                 "id": mission_id,
                                 "requirement": str(requirements_path),
-                                "created": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
+                                "created": datetime.now(timezone.utc)
+                                .isoformat()
+                                .replace("+00:00", "Z"),
                                 "status": "planned",
                                 "orchestrator": runtime_override or orchestrator,
                                 "parallel": 1,
                             },
-                            "tasks": normalized_tasks
+                            "tasks": normalized_tasks,
                         }
-                        console.print(f"[bold green]✓[/] AI generated a custom task plan with {len(normalized_tasks)} tasks.")
+                        console.print(
+                            f"[bold green]✓[/] AI generated a custom task plan with {len(normalized_tasks)} tasks."
+                        )
             except Exception as e:
-                console.print(f"[yellow]Warning:[/] AI planner execution encountered an error: {e}")
+                console.print(
+                    f"[yellow]Warning:[/] AI planner execution encountered an error: {e}"
+                )
 
     # Fallback to static template plan
     if not plan_data:
         if strict:
-            console.print("[bold red]Error:[/] AI-powered planning failed and strict planning was requested.")
+            console.print(
+                "[bold red]Error:[/] AI-powered planning failed and strict planning was requested."
+            )
             raise SystemExit(1)
-        console.print("[yellow]AI planner fallback: generating standard static template plan.[/]")
+        console.print(
+            "[yellow]AI planner fallback: generating standard static template plan.[/]"
+        )
         plan_data = {
             "mission": {
                 "id": mission_id,
                 "requirement": str(requirements_path),
-                "created": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
+                "created": datetime.now(timezone.utc)
+                .isoformat()
+                .replace("+00:00", "Z"),
                 "status": "planned",
                 "orchestrator": runtime_override or "claude",
                 "parallel": 1,
@@ -568,8 +649,8 @@ def run_mission_plan(
                     "status": "pending",
                     "agent": qa_agent,
                     "depends_on": ["T4"],
-                }
-            ]
+                },
+            ],
         }
 
     # Write mission-plan.yaml
@@ -590,7 +671,9 @@ def run_mission_plan(
     (run_dir / "execution-log.json").write_text("[]", encoding="utf-8")
     (run_dir / "policy-events.json").write_text("[]", encoding="utf-8")
 
-    console.print(f"[bold green]✓[/] Created mission plan '[cyan]{mission_id}[/]' in .niyam/runs/{mission_id}/")
+    console.print(
+        f"[bold green]✓[/] Created mission plan '[cyan]{mission_id}[/]' in .niyam/runs/{mission_id}/"
+    )
     return mission_id
 
 
@@ -631,10 +714,13 @@ def run_mission_approve(console: Console, interactive: bool = False) -> None:
 
     # Automatically validate plan before approval
     from niyam.mission.validator import validate_mission_plan, PlanValidationError
+
     try:
         validate_mission_plan(plan_path, repo_root)
     except PlanValidationError as e:
-        console.print(f"[bold red]❌ Mission approval rejected due to validation failures:[/]")
+        console.print(
+            "[bold red]❌ Mission approval rejected due to validation failures:[/]"
+        )
         for err in e.errors:
             console.print(f"  • [red]{err}[/]")
         raise SystemExit(1)
@@ -664,7 +750,9 @@ def run_mission_approve(console: Console, interactive: bool = False) -> None:
             tasks = plan_data.get("tasks", [])
             mission_meta = plan_data.get("mission", {})
 
-            table = Table(title=f"Mission Plan preview: [cyan]{mission_id}[/]", expand=True)
+            table = Table(
+                title=f"Mission Plan preview: [cyan]{mission_id}[/]", expand=True
+            )
             table.add_column("ID", style="bold magenta", justify="center", width=4)
             table.add_column("Title")
             table.add_column("Agent", style="yellow")
@@ -697,10 +785,13 @@ def run_mission_approve(console: Console, interactive: bool = False) -> None:
             elif answer == "edit":
                 editor = os.environ.get("EDITOR", "nano")
                 import subprocess
+
                 try:
                     subprocess.run([editor, str(plan_path)], check=True)
                 except Exception as e:
-                    console.print(f"[bold red]Failed to launch editor '{editor}':[/] {e}")
+                    console.print(
+                        f"[bold red]Failed to launch editor '{editor}':[/] {e}"
+                    )
                     try:
                         subprocess.run(["vi", str(plan_path)], check=True)
                     except Exception:
@@ -711,7 +802,9 @@ def run_mission_approve(console: Console, interactive: bool = False) -> None:
                     validate_mission_plan(plan_path, repo_root)
                     console.print("[bold green]✓ Edited plan is valid.[/]")
                 except PlanValidationError as e:
-                    console.print(f"[bold red]❌ Mission plan validation failed after editing:[/]")
+                    console.print(
+                        "[bold red]❌ Mission plan validation failed after editing:[/]"
+                    )
                     for err in e.errors:
                         console.print(f"  • [red]{err}[/]")
                 except Exception as e:
@@ -735,6 +828,9 @@ def run_mission_approve(console: Console, interactive: bool = False) -> None:
         "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
     }
     import json
+
     approval_path.write_text(json.dumps(approval_data, indent=2), encoding="utf-8")
 
-    console.print(f"[bold green]✓[/] Mission '[cyan]{mission_id}[/]' has been approved and is ready to start.")
+    console.print(
+        f"[bold green]✓[/] Mission '[cyan]{mission_id}[/]' has been approved and is ready to start."
+    )
diff --git a/niyam/mission/reporter.py b/niyam/mission/reporter.py
index f774829..3872c89 100644
--- a/niyam/mission/reporter.py
+++ b/niyam/mission/reporter.py
@@ -6,7 +6,6 @@ import json
 from pathlib import Path
 import subprocess
 from datetime import datetime
-import yaml
 from rich.console import Console
 from rich.panel import Panel
 
@@ -46,9 +45,7 @@ def compute_manifest_hmac(manifest_files: dict[str, str], signing_key: bytes) ->
     Creates a deterministic string from sorted file paths and their hashes,
     then signs it with the provided key.
     """
-    canonical = "\n".join(
-        f"{k}:{v}" for k, v in sorted(manifest_files.items())
-    )
+    canonical = "\n".join(f"{k}:{v}" for k, v in sorted(manifest_files.items()))
     return hmac.new(signing_key, canonical.encode("utf-8"), hashlib.sha256).hexdigest()
 
 
@@ -68,7 +65,9 @@ def get_changed_files(repo_root: Path) -> list[str]:
                 parts = line.strip().split(maxsplit=1)
                 if len(parts) == 2:
                     rel_path = parts[1]
-                    if not rel_path.startswith(".niyam") and not rel_path.startswith("evidence.md"):
+                    if not rel_path.startswith(".niyam") and not rel_path.startswith(
+                        "evidence.md"
+                    ):
                         files.append(rel_path)
         return files
     except Exception:
@@ -103,7 +102,9 @@ def run_mission_report(console: Console) -> None:
     base_sha = mission_meta.get("base_sha")
     try:
         if base_sha:
-            res = subprocess.run(["git", "diff", base_sha], capture_output=True, text=True)
+            res = subprocess.run(
+                ["git", "diff", base_sha], capture_output=True, text=True
+            )
         else:
             res = subprocess.run(["git", "diff"], capture_output=True, text=True)
         if res.returncode == 0:
@@ -114,7 +115,9 @@ def run_mission_report(console: Console) -> None:
     # Write diff to run directory
     diff_path = run_dir / "diff-summary.md"
     if git_diff:
-        diff_path.write_text(f"### Git Diff Summary\n\n```diff\n{git_diff}\n```\n", encoding="utf-8")
+        diff_path.write_text(
+            f"### Git Diff Summary\n\n```diff\n{git_diff}\n```\n", encoding="utf-8"
+        )
     else:
         diff_path.write_text("No changes detected in Git.\n", encoding="utf-8")
 
@@ -129,10 +132,10 @@ def run_mission_report(console: Console) -> None:
     # 3. Collect Policy Events
     policy_events_path = run_dir / "policy-events.json"
     policy_events: list[dict] = []
-    
+
     # Also check the global policy events and filter by time if possible
     global_policy_path = niyam_dir / "evidence" / "policy-events.json"
-    
+
     # Combine events
     for path in (policy_events_path, global_policy_path):
         if path.exists():
@@ -163,7 +166,9 @@ def run_mission_report(console: Console) -> None:
     report_sections = []
     report_sections.append(f"# Niyam Mission Evidence Package - {mission_id}")
     report_sections.append("")
-    report_sections.append(f"- **Requirement Source:** `{mission_meta.get('requirement', '')}`")
+    report_sections.append(
+        f"- **Requirement Source:** `{mission_meta.get('requirement', '')}`"
+    )
     report_sections.append(f"- **Generated:** `{datetime.utcnow().isoformat()}Z`")
     report_sections.append(f"- **Status:** `{status.upper()}`")
     report_sections.append(f"- **Orchestrator:** `{orchestrator}`")
@@ -172,8 +177,12 @@ def run_mission_report(console: Console) -> None:
     report_sections.append("")
     for task in plan_data.get("tasks", []):
         icon = "✓" if task.get("status") == "completed" else "✗"
-        sha_str = f" (commit: `{task['commit_sha'][:7]}`)" if task.get("commit_sha") else ""
-        report_sections.append(f"- [{icon}] **{task.get('id', '')}**: {task.get('title', '')} ({task.get('agent', '')}){sha_str}")
+        sha_str = (
+            f" (commit: `{task['commit_sha'][:7]}`)" if task.get("commit_sha") else ""
+        )
+        report_sections.append(
+            f"- [{icon}] **{task.get('id', '')}**: {task.get('title', '')} ({task.get('agent', '')}){sha_str}"
+        )
     report_sections.append("")
 
     report_sections.append("## Execution Log")
@@ -181,7 +190,9 @@ def run_mission_report(console: Console) -> None:
     if exec_log:
         for event in exec_log:
             task_str = f" [{event.get('task_id')}]" if event.get("task_id") else ""
-            report_sections.append(f"- `{event.get('timestamp')}` **{event.get('event')}**{task_str}: {event.get('details')}")
+            report_sections.append(
+                f"- `{event.get('timestamp')}` **{event.get('event')}**{task_str}: {event.get('details')}"
+            )
     else:
         report_sections.append("*No execution logs recorded.*")
     report_sections.append("")
@@ -192,7 +203,9 @@ def run_mission_report(console: Console) -> None:
         report_sections.append("| Timestamp | Type | Event Details |")
         report_sections.append("|-----------|------|---------------|")
         for event in policy_events:
-            report_sections.append(f"| `{event.get('timestamp')}` | `{event.get('type')}` | {event.get('details')} |")
+            report_sections.append(
+                f"| `{event.get('timestamp')}` | `{event.get('type')}` | {event.get('details')} |"
+            )
     else:
         report_sections.append("*No policy events triggered.*")
     report_sections.append("")
@@ -212,15 +225,20 @@ def run_mission_report(console: Console) -> None:
 
     # Generate cryptographic manifest signature block
     manifest_files = {}
-    for run_file in ("mission-plan.yaml", "execution-log.json", "validation-results.md", "policy-events.json"):
+    for run_file in (
+        "mission-plan.yaml",
+        "execution-log.json",
+        "validation-results.md",
+        "policy-events.json",
+    ):
         full_path = run_dir / run_file
         if full_path.exists():
             manifest_files[run_file] = compute_sha256(full_path)
-            
+
     changed_files = get_changed_files(repo_root)
     for f in changed_files:
         manifest_files[f] = compute_sha256(repo_root / f)
-        
+
     manifest = {
         "mission_id": mission_id,
         "timestamp": datetime.utcnow().isoformat() + "Z",
@@ -234,7 +252,7 @@ def run_mission_report(console: Console) -> None:
         manifest["signed"] = True
     else:
         manifest["signed"] = False
-    
+
     report_sections.append("## Cryptographic Integrity Manifest")
     report_sections.append("")
     report_sections.append("<!-- NIYAM_SIGNATURE_START")
@@ -262,13 +280,15 @@ def run_mission_report(console: Console) -> None:
     with open(evidence_json, "w", encoding="utf-8") as f:
         json.dump(json_data, f, indent=2)
 
-    console.print(Panel(
-        f"Evidence Markdown: [bold cyan]evidence.md[/]\n"
-        f"Evidence JSON: [bold cyan]evidence.json[/]\n"
-        f"Location: [bold].niyam/runs/{mission_id}/[/]",
-        title="[bold green]✓ Evidence Report Generated[/]",
-        border_style="green"
-    ))
+    console.print(
+        Panel(
+            f"Evidence Markdown: [bold cyan]evidence.md[/]\n"
+            f"Evidence JSON: [bold cyan]evidence.json[/]\n"
+            f"Location: [bold].niyam/runs/{mission_id}/[/]",
+            title="[bold green]✓ Evidence Report Generated[/]",
+            border_style="green",
+        )
+    )
 
 
 def run_verify_report(evidence_path: str, console: Console) -> None:
@@ -279,30 +299,40 @@ def run_verify_report(evidence_path: str, console: Console) -> None:
         raise SystemExit(1)
 
     content = path.read_text(encoding="utf-8")
-    
+
     start_tag = "<!-- NIYAM_SIGNATURE_START"
     end_tag = "NIYAM_SIGNATURE_END -->"
-    
+
     if start_tag not in content or end_tag not in content:
-        console.print("[bold red]❌ Integrity check failed:[/] No cryptographic signature manifest found in evidence report.")
+        console.print(
+            "[bold red]❌ Integrity check failed:[/] No cryptographic signature manifest found in evidence report."
+        )
         raise SystemExit(1)
 
     try:
         sig_part = content.split(start_tag)[1].split(end_tag)[0].strip()
         manifest = json.loads(sig_part)
     except Exception as e:
-        console.print(f"[bold red]❌ Integrity check failed:[/] Signature manifest block is corrupt: {e}")
+        console.print(
+            f"[bold red]❌ Integrity check failed:[/] Signature manifest block is corrupt: {e}"
+        )
         raise SystemExit(1)
 
     run_dir = path.parent
     from niyam.core.config import find_niyam_root
+
     repo_root = find_niyam_root(start=run_dir) or find_niyam_root() or Path.cwd()
 
     failures = []
     verified_count = 0
 
     for rel_file, expected_hash in manifest.get("files", {}).items():
-        if rel_file in ("mission-plan.yaml", "execution-log.json", "validation-results.md", "policy-events.json"):
+        if rel_file in (
+            "mission-plan.yaml",
+            "execution-log.json",
+            "validation-results.md",
+            "policy-events.json",
+        ):
             file_path = run_dir / rel_file
         else:
             file_path = repo_root / rel_file
@@ -314,9 +344,13 @@ def run_verify_report(evidence_path: str, console: Console) -> None:
             verified_count += 1
 
     if failures:
-        console.print(f"[bold red]❌ Integrity check failed:[/] {len(failures)} file(s) tampered or modified since the report was generated.")
+        console.print(
+            f"[bold red]❌ Integrity check failed:[/] {len(failures)} file(s) tampered or modified since the report was generated."
+        )
         for rel_file, exp, act in failures:
-            console.print(f"  - [red]{rel_file}[/]: expected `{exp[:10]}...`, got `{act[:10]}...`")
+            console.print(
+                f"  - [red]{rel_file}[/]: expected `{exp[:10]}...`, got `{act[:10]}...`"
+            )
         raise SystemExit(1)
 
     # Verify HMAC signature if the manifest was signed
@@ -327,17 +361,23 @@ def run_verify_report(evidence_path: str, console: Console) -> None:
             expected_hmac = manifest.get("hmac_sha256", "")
             actual_hmac = compute_manifest_hmac(manifest.get("files", {}), signing_key)
             if not hmac.compare_digest(expected_hmac, actual_hmac):
-                console.print("[bold red]❌ HMAC signature verification FAILED.[/] The manifest may have been tampered with.")
+                console.print(
+                    "[bold red]❌ HMAC signature verification FAILED.[/] The manifest may have been tampered with."
+                )
                 raise SystemExit(1)
             hmac_status = "[bold green]VERIFIED[/]"
         else:
-            hmac_status = "[yellow]signed but NIYAM_SIGNING_KEY not set — cannot verify[/]"
-
-    console.print(Panel(
-        f"Mission ID: [bold cyan]{manifest.get('mission_id')}[/]\n"
-        f"Signed On: [bold cyan]{manifest.get('timestamp')}[/]\n"
-        f"Verified Files: [bold green]{verified_count}[/]\n"
-        f"HMAC Signature: {hmac_status}",
-        title="[bold green]✓ Evidence Report Verified Successfully[/]",
-        border_style="green"
-    ))
+            hmac_status = (
+                "[yellow]signed but NIYAM_SIGNING_KEY not set — cannot verify[/]"
+            )
+
+    console.print(
+        Panel(
+            f"Mission ID: [bold cyan]{manifest.get('mission_id')}[/]\n"
+            f"Signed On: [bold cyan]{manifest.get('timestamp')}[/]\n"
+            f"Verified Files: [bold green]{verified_count}[/]\n"
+            f"HMAC Signature: {hmac_status}",
+            title="[bold green]✓ Evidence Report Verified Successfully[/]",
+            border_style="green",
+        )
+    )
diff --git a/niyam/mission/status.py b/niyam/mission/status.py
index b4074a2..881315f 100644
--- a/niyam/mission/status.py
+++ b/niyam/mission/status.py
@@ -2,7 +2,6 @@
 
 from __future__ import annotations
 
-from pathlib import Path
 from rich.console import Console
 from rich.table import Table
 from rich.panel import Panel
@@ -44,14 +43,16 @@ def run_mission_status(console: Console) -> None:
     }
     color = status_colors.get(status, "white")
 
-    console.print(Panel(
-        f"Mission ID: [bold cyan]{mission_id}[/]\n"
-        f"Status: [{color}]{status.upper()}[/]\n"
-        f"Created: [dim]{created}[/]\n"
-        f"Orchestrator: [bold]{mission_meta.get('orchestrator', 'claude')}[/]",
-        title="[bold]Mission Status Overview[/]",
-        border_style=status_colors.get(status, "cyan")
-    ))
+    console.print(
+        Panel(
+            f"Mission ID: [bold cyan]{mission_id}[/]\n"
+            f"Status: [{color}]{status.upper()}[/]\n"
+            f"Created: [dim]{created}[/]\n"
+            f"Orchestrator: [bold]{mission_meta.get('orchestrator', 'claude')}[/]",
+            title="[bold]Mission Status Overview[/]",
+            border_style=status_colors.get(status, "cyan"),
+        )
+    )
 
     table = Table(title="Mission Task Checklist")
     table.add_column("ID", style="dim", width=4)
@@ -71,10 +72,7 @@ def run_mission_status(console: Console) -> None:
         t_status = task.get("status", "pending")
         icon = status_icons.get(t_status, t_status)
         table.add_row(
-            task.get("id", ""),
-            task.get("title", ""),
-            task.get("agent", ""),
-            icon
+            task.get("id", ""), task.get("title", ""), task.get("agent", ""), icon
         )
 
     console.print(table)
diff --git a/niyam/mission/validator.py b/niyam/mission/validator.py
index 2da3b3d..4d4efc6 100644
--- a/niyam/mission/validator.py
+++ b/niyam/mission/validator.py
@@ -2,10 +2,8 @@
 
 from __future__ import annotations
 
-import os
 import shutil
 from pathlib import Path
-import yaml
 from pydantic import ValidationError
 
 from niyam.core.config import MissionPlan, get_niyam_dir, load_project_config
@@ -14,6 +12,7 @@ from niyam.core.security import validate_command, CommandSecurityError, safe_loa
 
 class PlanValidationError(Exception):
     """Raised when mission plan validation fails."""
+
     def __init__(self, errors: list[str]):
         super().__init__("\n".join(errors))
         self.errors = errors
@@ -47,7 +46,7 @@ def validate_mission_plan(plan_path: Path, repo_root: Path) -> None:
     # 3. DAG Validation (Cycle and Unknown Dependency checks)
     tasks = plan.tasks
     task_ids = {t.id for t in tasks}
-    
+
     # Check for duplicate task IDs
     seen_ids = set()
     for t in tasks:
@@ -91,22 +90,34 @@ def validate_mission_plan(plan_path: Path, repo_root: Path) -> None:
         # Check Agent existence
         agent_file = agents_dir / f"{t.agent}.md"
         if not agent_file.exists():
-            errors.append(f"Task '{t.id}' assigns unknown agent '{t.agent}' (missing {agent_file.relative_to(repo_root) if repo_root in agent_file.parents else agent_file})")
+            errors.append(
+                f"Task '{t.id}' assigns unknown agent '{t.agent}' (missing {agent_file.relative_to(repo_root) if repo_root in agent_file.parents else agent_file})"
+            )
 
         # Check Runtime existence
         if t.runtime:
-            if not shutil.which(t.runtime) and t.runtime not in ("claude", "gemini", "codex"):
-                errors.append(f"Task '{t.id}' specifies runtime '{t.runtime}' which is not executable or found in PATH")
+            if not shutil.which(t.runtime) and t.runtime not in (
+                "claude",
+                "gemini",
+                "codex",
+            ):
+                errors.append(
+                    f"Task '{t.id}' specifies runtime '{t.runtime}' which is not executable or found in PATH"
+                )
 
     # 5. Path Policy Validation (allowed_files, blocked_files)
     for t in tasks:
         # Prevent absolute or directory traversal in allowed/blocked files
         for pat in t.allowed_files:
             if pat.startswith("/") or ".." in pat:
-                errors.append(f"Task '{t.id}' allowed_files pattern '{pat}' is invalid. Path traversal or absolute paths are forbidden.")
+                errors.append(
+                    f"Task '{t.id}' allowed_files pattern '{pat}' is invalid. Path traversal or absolute paths are forbidden."
+                )
         for pat in t.blocked_files:
             if pat.startswith("/") or ".." in pat:
-                errors.append(f"Task '{t.id}' blocked_files pattern '{pat}' is invalid. Path traversal or absolute paths are forbidden.")
+                errors.append(
+                    f"Task '{t.id}' blocked_files pattern '{pat}' is invalid. Path traversal or absolute paths are forbidden."
+                )
 
     # 6. Validation Command Security Checks
     # Check task-specific validation commands
@@ -116,19 +127,29 @@ def validate_mission_plan(plan_path: Path, repo_root: Path) -> None:
                 try:
                     validate_command(cmd)
                 except CommandSecurityError as e:
-                    errors.append(f"Task '{t.id}' validation command '{cmd}' blocked by security: {e}")
+                    errors.append(
+                        f"Task '{t.id}' validation command '{cmd}' blocked by security: {e}"
+                    )
 
     # Check project-level validation commands
     try:
         proj_config = load_project_config(repo_root)
         if proj_config and proj_config.validation:
             v_cmds = proj_config.validation
-            for name, cmd in [("build", v_cmds.build), ("test", v_cmds.test), ("lint", v_cmds.lint), ("format", v_cmds.format), ("typecheck", v_cmds.typecheck)]:
+            for name, cmd in [
+                ("build", v_cmds.build),
+                ("test", v_cmds.test),
+                ("lint", v_cmds.lint),
+                ("format", v_cmds.format),
+                ("typecheck", v_cmds.typecheck),
+            ]:
                 if cmd:
                     try:
                         validate_command(cmd)
                     except CommandSecurityError as e:
-                        errors.append(f"Project configuration validation '{name}' command '{cmd}' blocked by security: {e}")
+                        errors.append(
+                            f"Project configuration validation '{name}' command '{cmd}' blocked by security: {e}"
+                        )
     except Exception:
         pass  # project.yaml might not exist yet during init/planning, which is fine
 
diff --git a/niyam/policies/guard.py b/niyam/policies/guard.py
index 3436d99..74c9810 100644
--- a/niyam/policies/guard.py
+++ b/niyam/policies/guard.py
@@ -19,7 +19,9 @@ def _ensure_root(console: Console) -> Path:
     """Find niyam root or exit."""
     root = find_niyam_root()
     if root is None:
-        console.print("[bold red]Error:[/] Not a Niyam workspace. Run [bold]niyam init[/] first.")
+        console.print(
+            "[bold red]Error:[/] Not a Niyam workspace. Run [bold]niyam init[/] first."
+        )
         raise SystemExit(1)
     return root
 
@@ -74,7 +76,9 @@ def run_guard_disable(console: Console) -> None:
 
     _resync_hooks(root, console)
 
-    console.print("[yellow]⚠ Guard mode [bold]disabled[/]. AI agents can execute freely.[/]")
+    console.print(
+        "[yellow]⚠ Guard mode [bold]disabled[/]. AI agents can execute freely.[/]"
+    )
 
 
 def run_guard_careful(console: Console) -> None:
@@ -194,10 +198,7 @@ def _fetch_remote_policy_raw(url: str, filename: str) -> dict:
         # Strict SSL context — verifies certificates
         ssl_ctx = ssl.create_default_context()
 
-        req = urllib.request.Request(
-            target_url,
-            headers={"User-Agent": "Niyam-CLI"}
-        )
+        req = urllib.request.Request(target_url, headers={"User-Agent": "Niyam-CLI"})
         with urllib.request.urlopen(req, timeout=5, context=ssl_ctx) as response:
             content = response.read(MAX_RESPONSE_SIZE + 1)
             if len(content) > MAX_RESPONSE_SIZE:
@@ -210,6 +211,7 @@ def _fetch_remote_policy_raw(url: str, filename: str) -> dict:
 
             # Validate against schema
             from niyam.policies.validator import KNOWN_POLICY_FILES
+
             if filename in KNOWN_POLICY_FILES:
                 schema = KNOWN_POLICY_FILES[filename]
                 all_known = set(schema["required_keys"]) | set(schema["optional_keys"])
@@ -278,6 +280,7 @@ def _fetch_remote_policy(url: str, filename: str) -> dict | None:
             if isinstance(cached_val, list) and len(cached_val) == 2:
                 _, data = cached_val
                 import logging
+
                 logging.getLogger("niyam.guard").warning(
                     "Remote policy fetch failed (%s). Using cached version.", e
                 )
@@ -305,13 +308,16 @@ def load_security_policy(root: Path) -> dict:
             if remote_data is not None:
                 return remote_data
         except Exception as e:
-            logger.warning("Failed to fetch remote security policy: %s. Falling back to local.", e)
+            logger.warning(
+                "Failed to fetch remote security policy: %s. Falling back to local.", e
+            )
 
     # Fallback to local
     local_path = root / ".niyam" / "policies" / "security.yaml"
     if local_path.exists():
         try:
             from niyam.core.security import safe_load_yaml
+
             return safe_load_yaml(local_path)
         except Exception:
             pass
@@ -336,13 +342,16 @@ def load_commands_policy(root: Path) -> dict:
             if remote_data is not None:
                 return remote_data
         except Exception as e:
-            logger.warning("Failed to fetch remote commands policy: %s. Falling back to local.", e)
+            logger.warning(
+                "Failed to fetch remote commands policy: %s. Falling back to local.", e
+            )
 
     # Fallback to local
     local_path = root / ".niyam" / "policies" / "commands.yaml"
     if local_path.exists():
         try:
             from niyam.core.security import safe_load_yaml
+
             return safe_load_yaml(local_path)
         except Exception:
             pass
diff --git a/niyam/policies/validator.py b/niyam/policies/validator.py
index 5374be3..45da834 100644
--- a/niyam/policies/validator.py
+++ b/niyam/policies/validator.py
@@ -2,9 +2,7 @@
 
 from __future__ import annotations
 
-from pathlib import Path
 
-import yaml
 from rich.console import Console
 from rich.table import Table
 
@@ -39,7 +37,9 @@ def run_policy_validate(console: Console) -> None:
     """Validate all policy YAML files."""
     root = find_niyam_root()
     if root is None:
-        console.print("[bold red]Error:[/] Not a Niyam workspace. Run [bold]niyam init[/] first.")
+        console.print(
+            "[bold red]Error:[/] Not a Niyam workspace. Run [bold]niyam init[/] first."
+        )
         raise SystemExit(1)
 
     policies_dir = root / ".niyam" / "policies"
@@ -56,6 +56,7 @@ def run_policy_validate(console: Console) -> None:
 
     # Validate remote policies if remote_policy_url is set
     from niyam.core.config import load_niyam_config
+
     try:
         config = load_niyam_config(root)
         remote_url = config.guard.remote_policy_url
@@ -64,17 +65,24 @@ def run_policy_validate(console: Console) -> None:
 
     if remote_url:
         from niyam.policies.guard import _fetch_remote_policy
+
         for filename, schema in KNOWN_POLICY_FILES.items():
             if filename not in ("security.yaml", "commands.yaml"):
                 continue
             remote_data = _fetch_remote_policy(remote_url, filename)
             if remote_data is None:
-                table.add_row(f"[Remote] {filename}", "[bold red]✗[/]", f"Failed to fetch from {remote_url}")
+                table.add_row(
+                    f"[Remote] {filename}",
+                    "[bold red]✗[/]",
+                    f"Failed to fetch from {remote_url}",
+                )
                 errors += 1
                 continue
 
             if not isinstance(remote_data, dict):
-                table.add_row(f"[Remote] {filename}", "[bold red]✗[/]", "Expected a YAML mapping")
+                table.add_row(
+                    f"[Remote] {filename}", "[bold red]✗[/]", "Expected a YAML mapping"
+                )
                 errors += 1
                 continue
 
@@ -99,6 +107,7 @@ def run_policy_validate(console: Console) -> None:
 
         try:
             from niyam.core.security import safe_load_yaml
+
             data = safe_load_yaml(fpath)
 
             if not isinstance(data, dict):
@@ -127,8 +136,11 @@ def run_policy_validate(console: Console) -> None:
         if fpath.name not in KNOWN_POLICY_FILES:
             try:
                 from niyam.core.security import safe_load_yaml
+
                 safe_load_yaml(fpath)
-                table.add_row(fpath.name, "[bold cyan]ℹ[/]", "Custom policy (valid YAML)")
+                table.add_row(
+                    fpath.name, "[bold cyan]ℹ[/]", "Custom policy (valid YAML)"
+                )
             except Exception as e:
                 table.add_row(fpath.name, "[bold red]✗[/]", f"Load error: {e}")
                 errors += 1
diff --git a/niyam/runtimes/claude.py b/niyam/runtimes/claude.py
index 11671ef..3b9a2c1 100644
--- a/niyam/runtimes/claude.py
+++ b/niyam/runtimes/claude.py
@@ -27,7 +27,7 @@ class ClaudeAdapter(RuntimeAdapter):
         self._project_skills(console)
         self._generate_hooks(console)
         self._generate_settings(console)
-        console.print(f"[green]✓[/] Claude Code runtime synced")
+        console.print("[green]✓[/] Claude Code runtime synced")
 
     def clean(self, console: Console) -> None:
         """Remove all Claude-generated files."""
@@ -47,7 +47,9 @@ class ClaudeAdapter(RuntimeAdapter):
 
         sections.append("# Project Instructions")
         sections.append("")
-        sections.append("<!-- Generated by Niyam — do not edit directly. Run `niyam sync` to update. -->")
+        sections.append(
+            "<!-- Generated by Niyam — do not edit directly. Run `niyam sync` to update. -->"
+        )
         sections.append("")
 
         # Include project memory
@@ -123,7 +125,9 @@ class ClaudeAdapter(RuntimeAdapter):
             approvals = data.get("approval_required_for", [])
             if approvals:
                 lines.append("### Approval Required")
-                lines.append("The following changes require **human approval** before proceeding:")
+                lines.append(
+                    "The following changes require **human approval** before proceeding:"
+                )
                 for item in approvals:
                     lines.append(f"- {item.replace('_', ' ').title()}")
                 lines.append("")
@@ -443,31 +447,34 @@ if __name__ == "__main__":
     print(json.dumps(result))
 '''
 
-
     def _generate_settings(self, console: Console) -> None:
         """Generate .claude/settings.json."""
         settings_dir = self.repo_root / ".claude"
         settings_dir.mkdir(parents=True, exist_ok=True)
 
         tool_names = [
-            "bash", "shell", "terminal", "run_command",
-            "write_file", "edit_file", "replace_file_content", "multi_replace_file_content"
+            "bash",
+            "shell",
+            "terminal",
+            "run_command",
+            "write_file",
+            "edit_file",
+            "replace_file_content",
+            "multi_replace_file_content",
         ]
         pre_tool_use_hooks = []
         for tool in tool_names:
-            pre_tool_use_hooks.append({
-                "matcher": {"tool_name": tool},
-                "hook": {
-                    "type": "command",
-                    "command": "python .claude/hooks/pre_tool_guard.py",
-                },
-            })
-
-        settings = {
-            "hooks": {
-                "pre_tool_use": pre_tool_use_hooks
-            }
-        }
+            pre_tool_use_hooks.append(
+                {
+                    "matcher": {"tool_name": tool},
+                    "hook": {
+                        "type": "command",
+                        "command": "python .claude/hooks/pre_tool_guard.py",
+                    },
+                }
+            )
+
+        settings = {"hooks": {"pre_tool_use": pre_tool_use_hooks}}
 
         settings_path = settings_dir / "settings.json"
         settings_path.write_text(
diff --git a/niyam/runtimes/codex.py b/niyam/runtimes/codex.py
index 0bbb82e..86d174f 100644
--- a/niyam/runtimes/codex.py
+++ b/niyam/runtimes/codex.py
@@ -2,8 +2,6 @@
 
 from __future__ import annotations
 
-import shutil
-from pathlib import Path
 
 import yaml
 from rich.console import Console
@@ -21,7 +19,7 @@ class CodexAdapter(RuntimeAdapter):
     def sync(self, console: Console) -> None:
         """Generate Codex CLI files from .niyam/ source of truth."""
         self._generate_agents_md(console)
-        console.print(f"[green]✓[/] Codex CLI runtime synced")
+        console.print("[green]✓[/] Codex CLI runtime synced")
 
     def clean(self, console: Console) -> None:
         """Remove all Codex-generated files."""
@@ -38,7 +36,9 @@ class CodexAdapter(RuntimeAdapter):
 
         sections.append("# Agent Instructions")
         sections.append("")
-        sections.append("<!-- Generated by Niyam — do not edit directly. Run `niyam sync` to update. -->")
+        sections.append(
+            "<!-- Generated by Niyam — do not edit directly. Run `niyam sync` to update. -->"
+        )
         sections.append("")
 
         # Project context
@@ -161,7 +161,9 @@ class CodexAdapter(RuntimeAdapter):
             approvals = data.get("approval_required_for", [])
             if approvals:
                 lines.append("### Approval Required")
-                lines.append("Ask for human approval before making changes in these areas:")
+                lines.append(
+                    "Ask for human approval before making changes in these areas:"
+                )
                 for item in approvals:
                     lines.append(f"- {item.replace('_', ' ').title()}")
                 lines.append("")
diff --git a/niyam/runtimes/gemini.py b/niyam/runtimes/gemini.py
index 1884c97..216dd30 100644
--- a/niyam/runtimes/gemini.py
+++ b/niyam/runtimes/gemini.py
@@ -4,7 +4,6 @@ from __future__ import annotations
 
 import json
 import shutil
-from pathlib import Path
 
 import yaml
 from rich.console import Console
@@ -24,7 +23,7 @@ class GeminiAdapter(RuntimeAdapter):
         self._generate_gemini_md(console)
         self._generate_style_md(console)
         self._generate_settings(console)
-        console.print(f"[green]✓[/] Gemini CLI runtime synced")
+        console.print("[green]✓[/] Gemini CLI runtime synced")
 
     def clean(self, console: Console) -> None:
         """Remove all Gemini-generated files."""
@@ -44,7 +43,9 @@ class GeminiAdapter(RuntimeAdapter):
 
         sections.append("# Gemini Project Instructions")
         sections.append("")
-        sections.append("<!-- Generated by Niyam — do not edit directly. Run `niyam sync` to update. -->")
+        sections.append(
+            "<!-- Generated by Niyam — do not edit directly. Run `niyam sync` to update. -->"
+        )
         sections.append("")
 
         # Include project memory
@@ -112,11 +113,7 @@ Generated by Niyam. Follow these rules when developing in this project:
         settings_dir = self.repo_root / ".gemini"
         settings_dir.mkdir(parents=True, exist_ok=True)
 
-        settings = {
-            "project": self.repo_root.name,
-            "runtime": "gemini",
-            "sync": True
-        }
+        settings = {"project": self.repo_root.name, "runtime": "gemini", "sync": True}
 
         settings_path = settings_dir / "settings.json"
         settings_path.write_text(
@@ -145,7 +142,9 @@ Generated by Niyam. Follow these rules when developing in this project:
             approvals = data.get("approval_required_for", [])
             if approvals:
                 lines.append("### Approval Required")
-                lines.append("Ask for human approval before making changes in these areas:")
+                lines.append(
+                    "Ask for human approval before making changes in these areas:"
+                )
                 for item in approvals:
                     lines.append(f"- {item.replace('_', ' ').title()}")
                 lines.append("")
diff --git a/tests/conftest.py b/tests/conftest.py
index d5e2c95..b454214 100644
--- a/tests/conftest.py
+++ b/tests/conftest.py
@@ -12,7 +12,9 @@ import pytest
 def tmp_repo(tmp_path: Path) -> Path:
     """Create a temporary directory simulating a git repo."""
     # Initialize a minimal git repo
-    os.system(f"cd {tmp_path} && git init -q && git config user.email 'test@test.com' && git config user.name 'Test'")
+    os.system(
+        f"cd {tmp_path} && git init -q && git config user.email 'test@test.com' && git config user.name 'Test'"
+    )
     return tmp_path
 
 
@@ -26,7 +28,13 @@ def niyam_repo(tmp_repo: Path) -> Path:
     original_dir = os.getcwd()
     os.chdir(tmp_repo)
     try:
-        run_init(profile="fullstack", runtime=None, dry_run=False, force=False, console=console)
+        run_init(
+            profile="fullstack",
+            runtime=None,
+            dry_run=False,
+            force=False,
+            console=console,
+        )
     finally:
         os.chdir(original_dir)
     return tmp_repo
diff --git a/tests/test_ci.py b/tests/test_ci.py
index ef53479..6832efd 100644
--- a/tests/test_ci.py
+++ b/tests/test_ci.py
@@ -10,7 +10,7 @@ from rich.console import Console
 
 from niyam.core.config import get_niyam_dir
 from niyam.mission.planner import run_mission_plan
-from niyam.mission.executor import run_mission_start, run_mission_resume, load_plan
+from niyam.mission.executor import run_mission_start, load_plan
 
 
 def test_non_interactive_fails_unapproved(niyam_repo: Path) -> None:
@@ -74,26 +74,29 @@ def test_remote_policy_fetching(niyam_repo: Path) -> None:
         "guard:\n"
         "  enabled: true\n"
         "  remote_policy_url: 'https://mock-server.com/policies/'\n",
-        encoding="utf-8"
+        encoding="utf-8",
     )
 
     mock_yaml_content = b"deny_write_patterns:\n  - 'src/restricted/*'\nallow_write_patterns:\n  - 'src/*'\n"
-    
+
     from unittest.mock import patch, MagicMock
-    import urllib.request
-    
+
     mock_response = MagicMock()
     mock_response.__enter__.return_value = mock_response
     mock_response.read.return_value = mock_yaml_content
-    
+
     with patch("urllib.request.urlopen", return_value=mock_response) as mock_urlopen:
         from niyam.policies.guard import load_security_policy
+
         policy = load_security_policy(niyam_repo)
-        
+
         # Verify URL called
         mock_urlopen.assert_called_once()
-        assert "https://mock-server.com/policies/security.yaml" in mock_urlopen.call_args[0][0].full_url
-        
+        assert (
+            "https://mock-server.com/policies/security.yaml"
+            in mock_urlopen.call_args[0][0].full_url
+        )
+
         # Verify content parsed correctly
         assert policy.get("deny_write_patterns") == ["src/restricted/*"]
 
@@ -111,23 +114,22 @@ def test_remote_policy_fallback(niyam_repo: Path) -> None:
         "guard:\n"
         "  enabled: true\n"
         "  remote_policy_url: 'https://mock-server.com/policies/'\n",
-        encoding="utf-8"
+        encoding="utf-8",
     )
 
     # Write local security.yaml file
     local_security_path = niyam_dir / "policies" / "security.yaml"
     local_security_path.write_text(
-        "deny_write_patterns:\n  - 'local/restricted/*'\n",
-        encoding="utf-8"
+        "deny_write_patterns:\n  - 'local/restricted/*'\n", encoding="utf-8"
     )
 
     from unittest.mock import patch
-    import urllib.error
 
     with patch("urllib.request.urlopen", side_effect=Exception("Connection refused")):
         from niyam.policies.guard import load_security_policy
+
         policy = load_security_policy(niyam_repo)
-        
+
         # Verify fallback content loaded
         assert policy.get("deny_write_patterns") == ["local/restricted/*"]
 
@@ -138,6 +140,7 @@ def test_ci_verify_strict_missing_evidence(niyam_repo: Path) -> None:
     console = Console(quiet=True)
 
     from niyam.core.ci import run_ci_verify
+
     with pytest.raises(SystemExit) as excinfo:
         run_ci_verify(target_branch="main", strict=True, console=console)
     assert excinfo.value.code == 1
@@ -149,9 +152,10 @@ def test_ci_verify_non_strict_missing_evidence(niyam_repo: Path) -> None:
     console = Console(quiet=True)
 
     from niyam.core.ci import run_ci_verify
+
     # Mocks to bypass other checks
     from unittest.mock import patch, MagicMock
-    
+
     mock_run = MagicMock()
     mock_run.returncode = 0
     mock_run.stdout = ""
@@ -171,12 +175,12 @@ def test_ci_verify_write_violation(niyam_repo: Path) -> None:
     mission_id = "test-mission-123"
     run_dir = niyam_dir / "runs" / mission_id
     run_dir.mkdir(parents=True, exist_ok=True)
-    
+
     # Save a plan
     plan_path = run_dir / "mission-plan.yaml"
     plan_path.write_text(
         "mission:\n  id: test-mission-123\n  status: completed\n  orchestrator: claude\ntasks: []\n",
-        encoding="utf-8"
+        encoding="utf-8",
     )
 
     evidence_md = run_dir / "evidence.md"
@@ -189,18 +193,17 @@ def test_ci_verify_write_violation(niyam_repo: Path) -> None:
         '  "files": {}\n'
         "}\n"
         "NIYAM_SIGNATURE_END -->\n",
-        encoding="utf-8"
+        encoding="utf-8",
     )
 
     # Write write restriction policy locally
     local_security_path = niyam_dir / "policies" / "security.yaml"
     local_security_path.write_text(
-        "deny_write_patterns:\n  - 'protected/*'\n",
-        encoding="utf-8"
+        "deny_write_patterns:\n  - 'protected/*'\n", encoding="utf-8"
     )
 
     from unittest.mock import patch, MagicMock
-    
+
     # Mock git status to return the mission ID
     def mock_git(cmd, **kwargs):
         res = MagicMock()
@@ -214,9 +217,11 @@ def test_ci_verify_write_violation(niyam_repo: Path) -> None:
         return res
 
     from niyam.core.ci import run_ci_verify
-    with patch("subprocess.run", side_effect=mock_git), \
-         patch("niyam.mission.reporter.run_verify_report"): # Bypass integrity check details
-        
+
+    with (
+        patch("subprocess.run", side_effect=mock_git),
+        patch("niyam.mission.reporter.run_verify_report"),
+    ):  # Bypass integrity check details
         with pytest.raises(SystemExit) as excinfo:
             run_ci_verify(target_branch="main", strict=True, console=console)
         assert excinfo.value.code == 1
@@ -227,5 +232,6 @@ def test_ci_verify_write_violation(niyam_repo: Path) -> None:
         with open(report_path, encoding="utf-8") as f:
             report = json.load(f)
         assert report["policy_status"] == "failed"
-        assert any("protected/secrets.json" in failure for failure in report["failures"])
-
+        assert any(
+            "protected/secrets.json" in failure for failure in report["failures"]
+        )
diff --git a/tests/test_dashboard.py b/tests/test_dashboard.py
index 26955d4..5569481 100644
--- a/tests/test_dashboard.py
+++ b/tests/test_dashboard.py
@@ -5,13 +5,12 @@ from __future__ import annotations
 import json
 import os
 from pathlib import Path
-import pytest
 from rich.console import Console
-from unittest.mock import patch, MagicMock
+from unittest.mock import patch
 
 from niyam.core.config import get_niyam_dir
 from niyam.mission.planner import run_mission_plan, run_mission_approve
-from niyam.mission.executor import run_mission_start, load_plan
+from niyam.mission.executor import run_mission_start
 from niyam.mission.dashboard import run_mission_dashboard, generate_dashboard_renderable
 
 
@@ -29,7 +28,9 @@ def test_dashboard_rendering(niyam_repo: Path) -> None:
     run_dir = get_niyam_dir(niyam_repo) / "runs" / mission_id
 
     # 2. Render dashboard when no token ledger exists (should not raise error)
-    renderable = generate_dashboard_renderable(run_dir, get_niyam_dir(niyam_repo), mission_id)
+    renderable = generate_dashboard_renderable(
+        run_dir, get_niyam_dir(niyam_repo), mission_id
+    )
     assert renderable is not None
 
     # Run start in test mode (this will populate the token ledger)
@@ -44,7 +45,7 @@ def test_dashboard_rendering(niyam_repo: Path) -> None:
     assert ledger_path.exists()
     with open(ledger_path, encoding="utf-8") as f:
         ledger = json.load(f)
-    
+
     assert "summary" in ledger
     assert "events" in ledger
     assert ledger["summary"]["total_tokens"] > 0
@@ -52,7 +53,9 @@ def test_dashboard_rendering(niyam_repo: Path) -> None:
     assert ledger["summary"]["total_savings_usd"] > 0.0
 
     # 4. Render dashboard with token ledger (should contain token and cost details)
-    renderable_with_ledger = generate_dashboard_renderable(run_dir, get_niyam_dir(niyam_repo), mission_id)
+    renderable_with_ledger = generate_dashboard_renderable(
+        run_dir, get_niyam_dir(niyam_repo), mission_id
+    )
     assert renderable_with_ledger is not None
 
     # Call run_mission_dashboard (non-watch mode)
@@ -73,7 +76,9 @@ def test_dashboard_watch_mode(niyam_repo: Path) -> None:
     run_mission_approve(console=console)
 
     # Mock time.sleep to raise KeyboardInterrupt to exit loop immediately
-    with patch("time.sleep", side_effect=KeyboardInterrupt), \
-         patch("rich.live.Live.update") as mock_update:
+    with (
+        patch("time.sleep", side_effect=KeyboardInterrupt),
+        patch("rich.live.Live.update") as mock_update,
+    ):
         run_mission_dashboard(watch=True, console=console)
         # Should not raise exception (handled KeyboardInterrupt gracefully)
diff --git a/tests/test_doctor.py b/tests/test_doctor.py
index 6b8eeb7..c3b36e0 100644
--- a/tests/test_doctor.py
+++ b/tests/test_doctor.py
@@ -6,7 +6,6 @@ import os
 from pathlib import Path
 
 import pytest
-import yaml
 from rich.console import Console
 
 
diff --git a/tests/test_doctor_enhanced.py b/tests/test_doctor_enhanced.py
index b309861..7b817a2 100644
--- a/tests/test_doctor_enhanced.py
+++ b/tests/test_doctor_enhanced.py
@@ -4,12 +4,9 @@ from __future__ import annotations
 
 import os
 from pathlib import Path
-from unittest.mock import patch, MagicMock
-import pytest
-from rich.console import Console
+from unittest.mock import patch
 
 from niyam.core.doctor import (
-    run_doctor,
     _check_runtimes_in_path,
     _check_agents_validity,
     _check_validation_commands_in_path,
@@ -30,13 +27,13 @@ def test_doctor_runtimes_in_path(niyam_repo: Path) -> None:
 
     with patch("shutil.which", side_effect=mock_which):
         results = _check_runtimes_in_path(niyam_repo, config)
-        
+
     assert len(results) == 2
-    
+
     # claude is present
     assert results[0].name == "Runtime in PATH: claude"
     assert results[0].passed is True
-    
+
     # gemini is missing
     assert results[1].name == "Runtime in PATH: gemini"
     assert results[1].passed is False
@@ -50,7 +47,7 @@ def test_doctor_agents_validity(niyam_repo: Path) -> None:
     empty_agent.write_text("   \n  ", encoding="utf-8")
 
     results = _check_agents_validity(niyam_repo)
-    
+
     # Verify warning generated for empty-agent
     empty_agent_results = [r for r in results if "empty-agent" in r.name]
     assert len(empty_agent_results) == 1
@@ -64,12 +61,10 @@ def test_doctor_validation_commands(niyam_repo: Path) -> None:
     project_yaml = niyam_repo / ".niyam" / "project.yaml"
     project_data = {
         "name": "test-project",
-        "validation": {
-            "test": "pytest",
-            "lint": "nonexistent-linter --verbose"
-        }
+        "validation": {"test": "pytest", "lint": "nonexistent-linter --verbose"},
     }
     import yaml
+
     with open(project_yaml, "w", encoding="utf-8") as f:
         yaml.safe_dump(project_data, f)
 
@@ -104,7 +99,7 @@ def test_doctor_git_status_dirty(niyam_repo: Path) -> None:
     dirty_file.write_text("dirty content", encoding="utf-8")
 
     results = _check_git_status(niyam_repo)
-    
+
     # Verify Git Status check fails or warns
     git_status_results = [r for r in results if "Git Status" in r.name]
     assert len(git_status_results) == 1
diff --git a/tests/test_fleet.py b/tests/test_fleet.py
index 66bfd2b..a6bd48d 100644
--- a/tests/test_fleet.py
+++ b/tests/test_fleet.py
@@ -3,11 +3,9 @@
 from __future__ import annotations
 
 import os
-import json
 from pathlib import Path
 import subprocess
 import pytest
-import yaml
 from rich.console import Console
 
 from niyam.core.config import get_niyam_dir
@@ -21,20 +19,34 @@ def git_repo_with_commit(tmp_repo: Path) -> Path:
     # Write a dummy file and commit it so HEAD exists
     dummy_file = tmp_repo / "dummy.txt"
     dummy_file.write_text("initial content", encoding="utf-8")
-    
-    subprocess.run(["git", "add", "dummy.txt"], cwd=tmp_repo, check=True, capture_output=True)
-    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=tmp_repo, check=True, capture_output=True)
-    
+
+    subprocess.run(
+        ["git", "add", "dummy.txt"], cwd=tmp_repo, check=True, capture_output=True
+    )
+    subprocess.run(
+        ["git", "commit", "-m", "Initial commit"],
+        cwd=tmp_repo,
+        check=True,
+        capture_output=True,
+    )
+
     from niyam.core.init import run_init
+
     console = Console(quiet=True)
-    
+
     original_dir = os.getcwd()
     os.chdir(tmp_repo)
     try:
-        run_init(profile="fullstack", runtime=None, dry_run=False, force=False, console=console)
+        run_init(
+            profile="fullstack",
+            runtime=None,
+            dry_run=False,
+            force=False,
+            console=console,
+        )
     finally:
         os.chdir(original_dir)
-        
+
     return tmp_repo
 
 
@@ -91,7 +103,7 @@ def test_fleet_parallel_execution(git_repo_with_commit: Path) -> None:
             "status": "pending",
             "agent": "qa-reviewer",
             "depends_on": ["T2", "T3"],
-        }
+        },
     ]
     save_plan(run_dir, plan_data)
 
@@ -105,7 +117,7 @@ def test_fleet_parallel_execution(git_repo_with_commit: Path) -> None:
     # 4. Verify completion
     updated_plan = load_plan(run_dir)
     assert updated_plan["mission"]["status"] == "completed"
-    
+
     # Check all tasks ran and completed
     for task in updated_plan["tasks"]:
         assert task["status"] == "completed"
@@ -116,7 +128,9 @@ def test_fleet_parallel_execution(git_repo_with_commit: Path) -> None:
     assert (git_repo_with_commit / "change-T3.txt").exists()
 
     # Check branches were cleaned up
-    res = subprocess.run(["git", "branch"], cwd=git_repo_with_commit, capture_output=True, text=True)
+    res = subprocess.run(
+        ["git", "branch"], cwd=git_repo_with_commit, capture_output=True, text=True
+    )
     assert f"niyam-{mission_id}-T1" not in res.stdout
     assert f"niyam-{mission_id}-T4" not in res.stdout
 
@@ -148,7 +162,7 @@ def test_fleet_dependency_failure(git_repo_with_commit: Path) -> None:
             "id": "T2",
             "title": "Failing Task",
             "type": "implementation",
-            "status": "failed", # Pre-failed to trigger scheduler logic
+            "status": "failed",  # Pre-failed to trigger scheduler logic
             "agent": "backend-specialist",
             "depends_on": ["T1"],
         },
@@ -159,7 +173,7 @@ def test_fleet_dependency_failure(git_repo_with_commit: Path) -> None:
             "status": "pending",
             "agent": "backend-specialist",
             "depends_on": ["T2"],
-        }
+        },
     ]
     save_plan(run_dir, plan_data)
 
@@ -182,16 +196,23 @@ def test_fleet_worktree_fallback_when_no_git(tmp_path: Path) -> None:
     """Should execute sequentially without worktrees if directory is not a Git repo."""
     # Note: tmp_path is a plain directory (NOT a git repo)
     from niyam.core.init import run_init
+
     console = Console(quiet=True)
 
     original_dir = os.getcwd()
     os.chdir(tmp_path)
     try:
-        run_init(profile="fullstack", runtime=None, dry_run=False, force=False, console=console)
-        
+        run_init(
+            profile="fullstack",
+            runtime=None,
+            dry_run=False,
+            force=False,
+            console=console,
+        )
+
         req_file = tmp_path / "requirements.md"
         req_file.write_text("# Test No Git\n", encoding="utf-8")
-        
+
         mission_id = run_mission_plan(str(req_file), console=console)
         run_mission_approve(console=console)
 
diff --git a/tests/test_guardrails.py b/tests/test_guardrails.py
index 5b62195..86d00d6 100644
--- a/tests/test_guardrails.py
+++ b/tests/test_guardrails.py
@@ -27,7 +27,7 @@ def test_path_write_denial_and_revert(niyam_repo: Path) -> None:
         "block_secrets_in_code": True,
         "require_auth_review": True,
         "require_input_validation": True,
-        "deny_write_patterns": ["src/secure/*.py"]
+        "deny_write_patterns": ["src/secure/*.py"],
     }
     with open(security_yaml, "w", encoding="utf-8") as f:
         yaml.dump(policy_data, f)
@@ -47,19 +47,20 @@ def test_path_write_denial_and_revert(niyam_repo: Path) -> None:
     # 3. Patch shutil.which to find 'claude' CLI, and patch subprocess.run
     # When claude CLI is executed, we write a denied file and return success.
     import subprocess as sp
+
     real_run = sp.run
 
     def mock_subprocess_run(args, **kwargs):
         if args and args[0] == "git":
             return real_run(args, **kwargs)
-            
+
         cwd = kwargs.get("cwd", niyam_repo)
-        
+
         # Write the unauthorized file to the correct cwd
         unauthorized_file = Path(cwd) / "src" / "secure" / "secret.py"
         unauthorized_file.parent.mkdir(parents=True, exist_ok=True)
         unauthorized_file.write_text("unauthorized changes", encoding="utf-8")
-        
+
         # Also add it to git so status --porcelain sees it
         real_run(["git", "add", "src/secure/secret.py"], cwd=cwd)
 
@@ -67,9 +68,10 @@ def test_path_write_denial_and_revert(niyam_repo: Path) -> None:
         res.returncode = 0
         return res
 
-    with patch("shutil.which", return_value="/usr/local/bin/claude"), \
-         patch("subprocess.run", side_effect=mock_subprocess_run):
-
+    with (
+        patch("shutil.which", return_value="/usr/local/bin/claude"),
+        patch("subprocess.run", side_effect=mock_subprocess_run),
+    ):
         # We do NOT run in test mode (NIYAM_TEST) because we want orchestrator execution path
         # But wait, run_mission_start will run.
         # Let's make sure it doesn't fail on validation test commands (no validation set in fullstack by default)
@@ -79,14 +81,14 @@ def test_path_write_denial_and_revert(niyam_repo: Path) -> None:
             with pytest.raises(SystemExit) as excinfo:
                 run_mission_start(console=console, worktree=False)
             assert excinfo.value.code == 1
-        except Exception as e:
+        except Exception:
             # Let it fail with SystemExit as expected
             pass
 
     # 4. Assert task T1 failed due to violation, and unauthorized file was deleted/reverted
     run_dir = niyam_dir / "runs" / mission_id
     plan = load_plan(run_dir)
-    
+
     # The first task executed (T1) should be failed
     assert plan["tasks"][0]["status"] == "failed"
     assert plan["mission"]["status"] == "failed"
diff --git a/tests/test_hooks.py b/tests/test_hooks.py
index 33f9262..2be3e0c 100644
--- a/tests/test_hooks.py
+++ b/tests/test_hooks.py
@@ -4,8 +4,6 @@ from __future__ import annotations
 
 import os
 from pathlib import Path
-from unittest.mock import patch, MagicMock
-import pytest
 import yaml
 from rich.console import Console
 
@@ -30,19 +28,19 @@ def test_hooks_lifecycle_triggers(niyam_repo: Path) -> None:
             "pre_task": [
                 {
                     "run": "echo 'Pre-task {{task.id}} with agent {{task.agent}}' > pre_task_{{task.id}}.txt",
-                    "when": "task.type == 'implementation'"
+                    "when": "task.type == 'implementation'",
                 },
                 {
                     "run": "echo 'This should not run' > should_not_run.txt",
-                    "when": "task.type == 'nonexistent'"
-                }
+                    "when": "task.type == 'nonexistent'",
+                },
             ],
             "post_task": [
                 "echo 'Post-task {{task.id}} status: {{task.status}}' > post_task_{{task.id}}.txt"
             ],
             "post_mission": [
                 "echo 'Post-mission {{mission_id}} status: {{mission_status}}' > post_mission.txt"
-            ]
+            ],
         }
     }
 
@@ -60,19 +58,21 @@ def test_hooks_lifecycle_triggers(niyam_repo: Path) -> None:
         "id": "T2",
         "type": "implementation",
         "agent": "coder-agent",
-        "title": "Impl task"
+        "title": "Impl task",
     }
     run_hooks("pre_task", {"mission_id": "m1", "task": impl_task}, niyam_dir, console)
     impl_hook_file = niyam_repo / "pre_task_T2.txt"
     assert impl_hook_file.exists()
-    assert "Pre-task T2 with agent coder-agent" in impl_hook_file.read_text(encoding="utf-8")
+    assert "Pre-task T2 with agent coder-agent" in impl_hook_file.read_text(
+        encoding="utf-8"
+    )
 
     # 3. Run pre_task hook for discovery task (should NOT run because of when conditional)
     disc_task = {
         "id": "T1",
         "type": "discovery",
         "agent": "scanner-agent",
-        "title": "Disc task"
+        "title": "Disc task",
     }
     run_hooks("pre_task", {"mission_id": "m1", "task": disc_task}, niyam_dir, console)
     should_not_run_file = niyam_repo / "should_not_run.txt"
@@ -83,10 +83,19 @@ def test_hooks_lifecycle_triggers(niyam_repo: Path) -> None:
     run_hooks("post_task", {"mission_id": "m1", "task": impl_task}, niyam_dir, console)
     post_task_file = niyam_repo / "post_task_T2.txt"
     assert post_task_file.exists()
-    assert "Post-task T2 status: completed" in post_task_file.read_text(encoding="utf-8")
+    assert "Post-task T2 status: completed" in post_task_file.read_text(
+        encoding="utf-8"
+    )
 
     # 5. Run post_mission hook
-    run_hooks("post_mission", {"mission_id": "m1", "mission_status": "success"}, niyam_dir, console)
+    run_hooks(
+        "post_mission",
+        {"mission_id": "m1", "mission_status": "success"},
+        niyam_dir,
+        console,
+    )
     post_mission_file = niyam_repo / "post_mission.txt"
     assert post_mission_file.exists()
-    assert "Post-mission m1 status: success" in post_mission_file.read_text(encoding="utf-8")
+    assert "Post-mission m1 status: success" in post_mission_file.read_text(
+        encoding="utf-8"
+    )
diff --git a/tests/test_init.py b/tests/test_init.py
index 87ef4c6..c23af36 100644
--- a/tests/test_init.py
+++ b/tests/test_init.py
@@ -19,7 +19,13 @@ class TestInit:
 
         console = Console(quiet=True)
         os.chdir(tmp_repo)
-        run_init(profile="fullstack", runtime=None, dry_run=False, force=False, console=console)
+        run_init(
+            profile="fullstack",
+            runtime=None,
+            dry_run=False,
+            force=False,
+            console=console,
+        )
 
         assert (tmp_repo / ".niyam").is_dir()
 
@@ -29,7 +35,13 @@ class TestInit:
 
         console = Console(quiet=True)
         os.chdir(tmp_repo)
-        run_init(profile="fullstack", runtime=None, dry_run=False, force=False, console=console)
+        run_init(
+            profile="fullstack",
+            runtime=None,
+            dry_run=False,
+            force=False,
+            console=console,
+        )
 
         for subdir in ["tasks", "runs", "templates", "worktrees", "evidence"]:
             assert (tmp_repo / ".niyam" / subdir).is_dir()
@@ -40,7 +52,13 @@ class TestInit:
 
         console = Console(quiet=True)
         os.chdir(tmp_repo)
-        run_init(profile="fullstack", runtime=None, dry_run=False, force=False, console=console)
+        run_init(
+            profile="fullstack",
+            runtime=None,
+            dry_run=False,
+            force=False,
+            console=console,
+        )
 
         niyam_yaml = tmp_repo / ".niyam" / "niyam.yaml"
         assert niyam_yaml.exists()
@@ -58,7 +76,13 @@ class TestInit:
 
         console = Console(quiet=True)
         os.chdir(tmp_repo)
-        run_init(profile="fullstack", runtime=None, dry_run=False, force=False, console=console)
+        run_init(
+            profile="fullstack",
+            runtime=None,
+            dry_run=False,
+            force=False,
+            console=console,
+        )
 
         agents_dir = tmp_repo / ".niyam" / "agents"
         assert agents_dir.is_dir()
@@ -71,7 +95,13 @@ class TestInit:
 
         console = Console(quiet=True)
         os.chdir(tmp_repo)
-        run_init(profile="fullstack", runtime=None, dry_run=False, force=False, console=console)
+        run_init(
+            profile="fullstack",
+            runtime=None,
+            dry_run=False,
+            force=False,
+            console=console,
+        )
 
         skills_dir = tmp_repo / ".niyam" / "skills"
         assert skills_dir.is_dir()
@@ -84,7 +114,13 @@ class TestInit:
 
         console = Console(quiet=True)
         os.chdir(tmp_repo)
-        run_init(profile="fullstack", runtime=None, dry_run=False, force=False, console=console)
+        run_init(
+            profile="fullstack",
+            runtime=None,
+            dry_run=False,
+            force=False,
+            console=console,
+        )
 
         commands_dir = tmp_repo / ".niyam" / "commands"
         assert commands_dir.is_dir()
@@ -97,7 +133,13 @@ class TestInit:
 
         console = Console(quiet=True)
         os.chdir(tmp_repo)
-        run_init(profile="fullstack", runtime=None, dry_run=False, force=False, console=console)
+        run_init(
+            profile="fullstack",
+            runtime=None,
+            dry_run=False,
+            force=False,
+            console=console,
+        )
 
         policies_dir = tmp_repo / ".niyam" / "policies"
         assert policies_dir.is_dir()
@@ -112,7 +154,13 @@ class TestInit:
         os.chdir(niyam_repo)
 
         with pytest.raises(SystemExit):
-            run_init(profile="fullstack", runtime=None, dry_run=False, force=False, console=console)
+            run_init(
+                profile="fullstack",
+                runtime=None,
+                dry_run=False,
+                force=False,
+                console=console,
+            )
 
     def test_init_force_overwrites(self, niyam_repo: Path) -> None:
         """niyam init --force should overwrite existing .niyam/."""
@@ -122,7 +170,13 @@ class TestInit:
         os.chdir(niyam_repo)
 
         # Should not raise
-        run_init(profile="fullstack", runtime=None, dry_run=False, force=True, console=console)
+        run_init(
+            profile="fullstack",
+            runtime=None,
+            dry_run=False,
+            force=True,
+            console=console,
+        )
 
         assert (niyam_repo / ".niyam" / "niyam.yaml").exists()
 
@@ -132,7 +186,13 @@ class TestInit:
 
         console = Console(quiet=True)
         os.chdir(tmp_repo)
-        run_init(profile="fullstack", runtime=None, dry_run=True, force=False, console=console)
+        run_init(
+            profile="fullstack",
+            runtime=None,
+            dry_run=True,
+            force=False,
+            console=console,
+        )
 
         assert not (tmp_repo / ".niyam").exists()
 
@@ -142,7 +202,13 @@ class TestInit:
 
         console = Console(quiet=True)
         os.chdir(tmp_repo)
-        run_init(profile="fullstack", runtime="claude", dry_run=False, force=False, console=console)
+        run_init(
+            profile="fullstack",
+            runtime="claude",
+            dry_run=False,
+            force=False,
+            console=console,
+        )
 
         assert (tmp_repo / ".niyam").is_dir()
         assert (tmp_repo / "CLAUDE.md").exists()
@@ -156,7 +222,13 @@ class TestInit:
         os.chdir(tmp_repo)
 
         with pytest.raises(SystemExit):
-            run_init(profile="nonexistent", runtime=None, dry_run=False, force=False, console=console)
+            run_init(
+                profile="nonexistent",
+                runtime=None,
+                dry_run=False,
+                force=False,
+                console=console,
+            )
 
     def test_init_backend_profile(self, tmp_repo: Path) -> None:
         """niyam init --profile backend should create only backend-related agents."""
@@ -164,12 +236,18 @@ class TestInit:
 
         console = Console(quiet=True)
         os.chdir(tmp_repo)
-        run_init(profile="backend", runtime=None, dry_run=False, force=False, console=console)
+        run_init(
+            profile="backend", runtime=None, dry_run=False, force=False, console=console
+        )
 
         agents_dir = tmp_repo / ".niyam" / "agents"
         assert agents_dir.is_dir()
         agent_names = {f.name for f in agents_dir.glob("*.md")}
-        assert agent_names == {"backend-specialist.md", "security-reviewer.md", "qa-reviewer.md"}
+        assert agent_names == {
+            "backend-specialist.md",
+            "security-reviewer.md",
+            "qa-reviewer.md",
+        }
 
     def test_init_frontend_profile(self, tmp_repo: Path) -> None:
         """niyam init --profile frontend should create only frontend-related agents."""
@@ -177,10 +255,15 @@ class TestInit:
 
         console = Console(quiet=True)
         os.chdir(tmp_repo)
-        run_init(profile="frontend", runtime=None, dry_run=False, force=False, console=console)
+        run_init(
+            profile="frontend",
+            runtime=None,
+            dry_run=False,
+            force=False,
+            console=console,
+        )
 
         agents_dir = tmp_repo / ".niyam" / "agents"
         assert agents_dir.is_dir()
         agent_names = {f.name for f in agents_dir.glob("*.md")}
         assert agent_names == {"frontend-specialist.md", "qa-reviewer.md"}
-
diff --git a/tests/test_memory.py b/tests/test_memory.py
index ae70188..182df67 100644
--- a/tests/test_memory.py
+++ b/tests/test_memory.py
@@ -4,7 +4,6 @@ from __future__ import annotations
 
 import os
 from pathlib import Path
-import pytest
 from rich.console import Console
 
 from niyam.core.memory import (
@@ -60,6 +59,7 @@ class TestMemory:
 
         # Configure runtimes
         from niyam.core.config import load_niyam_config, save_niyam_config
+
         config = load_niyam_config(niyam_repo)
         config.runtimes = ["claude", "codex"]
         save_niyam_config(config, niyam_repo)
diff --git a/tests/test_mission.py b/tests/test_mission.py
index c3dcc0d..ea283b6 100644
--- a/tests/test_mission.py
+++ b/tests/test_mission.py
@@ -10,8 +10,16 @@ import yaml
 from rich.console import Console
 
 from niyam.core.config import get_niyam_dir
-from niyam.mission.planner import run_mission_plan, run_mission_approve, get_latest_mission_id
-from niyam.mission.executor import run_mission_start, run_mission_pause, run_mission_resume, load_plan
+from niyam.mission.planner import (
+    run_mission_plan,
+    run_mission_approve,
+)
+from niyam.mission.executor import (
+    run_mission_start,
+    run_mission_pause,
+    run_mission_resume,
+    load_plan,
+)
 from niyam.mission.status import run_mission_status
 from niyam.mission.reporter import run_mission_report
 
@@ -26,7 +34,9 @@ class TestMission:
 
         # Create requirements file
         req_file = niyam_repo / "requirements.md"
-        req_file.write_text("# Implement Authentication\n\nRequire login validation.", encoding="utf-8")
+        req_file.write_text(
+            "# Implement Authentication\n\nRequire login validation.", encoding="utf-8"
+        )
 
         mission_id = run_mission_plan(str(req_file), console=console)
         assert mission_id is not None
@@ -37,7 +47,9 @@ class TestMission:
 
         # Check copied requirement
         assert (run_dir / "requirement.md").exists()
-        assert (run_dir / "requirement.md").read_text(encoding="utf-8") == req_file.read_text(encoding="utf-8")
+        assert (run_dir / "requirement.md").read_text(
+            encoding="utf-8"
+        ) == req_file.read_text(encoding="utf-8")
 
         # Check plan
         plan_path = run_dir / "mission-plan.yaml"
@@ -137,6 +149,7 @@ class TestMission:
         plan = load_plan(run_dir)
         plan["mission"]["status"] = "running"
         from niyam.mission.executor import save_plan
+
         save_plan(run_dir, plan)
 
         # Pause
diff --git a/tests/test_multi_runtime.py b/tests/test_multi_runtime.py
index bbfa42e..0cf305d 100644
--- a/tests/test_multi_runtime.py
+++ b/tests/test_multi_runtime.py
@@ -4,13 +4,9 @@ from __future__ import annotations
 
 import json
 import os
-import shutil
-import subprocess
 from pathlib import Path
 from unittest.mock import patch, MagicMock
 
-import pytest
-import yaml
 from rich.console import Console
 
 from niyam.core.config import get_niyam_dir
@@ -23,7 +19,7 @@ def test_planner_prompt_contains_runtime() -> None:
     prompt = build_planner_prompt(
         requirement="Build a feature",
         repo_map="file.py",
-        available_agents=["backend-specialist", "qa-reviewer"]
+        available_agents=["backend-specialist", "qa-reviewer"],
     )
     assert "runtime" in prompt
     assert "gemini" in prompt
@@ -98,8 +94,10 @@ def test_executor_resolves_task_runtime(niyam_repo: Path) -> None:
 
     # Approve it
     approval_path = get_niyam_dir(niyam_repo) / "runs" / mission_id / "approval.json"
-    approval_path.write_text('{"approved": true, "timestamp": "2026-05-28T22:00:00Z"}', encoding="utf-8")
-    
+    approval_path.write_text(
+        '{"approved": true, "timestamp": "2026-05-28T22:00:00Z"}', encoding="utf-8"
+    )
+
     run_dir = get_niyam_dir(niyam_repo) / "runs" / mission_id
     plan_data = load_plan(run_dir)
     plan_data["mission"]["status"] = "approved"
@@ -130,7 +128,7 @@ def test_executor_resolves_task_runtime(niyam_repo: Path) -> None:
             "status": "pending",
             "agent": "qa-reviewer",
             "depends_on": ["T2"],
-        }
+        },
     ]
     save_plan(run_dir, plan_data)
 
@@ -141,9 +139,10 @@ def test_executor_resolves_task_runtime(niyam_repo: Path) -> None:
         return None
 
     # Patch subprocess.run to track invocations
-    with patch("shutil.which", side_effect=mock_which), \
-         patch("subprocess.run") as mock_run:
-        
+    with (
+        patch("shutil.which", side_effect=mock_which),
+        patch("subprocess.run") as mock_run,
+    ):
         # NIYAM_TEST=0 allows running subprocess block.
         # NIYAM_CI_AUTO_APPROVE=1 satisfies the approval check.
         os.environ["NIYAM_CI_AUTO_APPROVE"] = "1"
@@ -169,11 +168,13 @@ def test_executor_resolves_task_runtime(niyam_repo: Path) -> None:
         assert ledger_path.exists()
         with open(ledger_path, encoding="utf-8") as f:
             ledger = json.load(f)
-        
+
         events = ledger.get("events", [])
         assert len(events) >= 3
         # Map task ID to runtime used from ledger
-        task_runtimes = {entry["task_id"]: entry["runtime"] for entry in events if "task_id" in entry}
+        task_runtimes = {
+            entry["task_id"]: entry["runtime"] for entry in events if "task_id" in entry
+        }
         assert task_runtimes["T1"] == "gemini"
         assert task_runtimes["T2"] == "codex"
         assert task_runtimes["T3"] == "claude"
diff --git a/tests/test_packs.py b/tests/test_packs.py
index d7634bf..abb99a4 100644
--- a/tests/test_packs.py
+++ b/tests/test_packs.py
@@ -5,7 +5,6 @@ from __future__ import annotations
 import os
 from pathlib import Path
 import pytest
-import yaml
 from rich.console import Console
 
 from niyam.core.config import load_niyam_config
@@ -59,11 +58,15 @@ class TestPacks:
         conflict_file.write_text("User custom command content", encoding="utf-8")
 
         with pytest.raises(ValueError, match="Conflict detected"):
-            add_pack(niyam_repo, "superpowers-methodology", force=False, console=console)
+            add_pack(
+                niyam_repo, "superpowers-methodology", force=False, console=console
+            )
 
         # Overwrite with --force should succeed
         add_pack(niyam_repo, "superpowers-methodology", force=True, console=console)
-        assert conflict_file.read_text(encoding="utf-8").startswith("<!-- pack: superpowers-methodology -->")
+        assert conflict_file.read_text(encoding="utf-8").startswith(
+            "<!-- pack: superpowers-methodology -->"
+        )
 
     def test_remove_pack(self, niyam_repo: Path) -> None:
         """remove_pack should delete pack files and update config."""
@@ -92,6 +95,7 @@ class TestPacks:
         config = load_niyam_config(niyam_repo)
         config.packs.append("superpowers-methodology")
         from niyam.core.config import save_niyam_config
+
         save_niyam_config(config, niyam_repo)
 
         # Skill file should not exist yet
diff --git a/tests/test_pr.py b/tests/test_pr.py
index a38e249..c4590a8 100644
--- a/tests/test_pr.py
+++ b/tests/test_pr.py
@@ -4,7 +4,6 @@ from __future__ import annotations
 
 import os
 from pathlib import Path
-import pytest
 from rich.console import Console
 from unittest.mock import patch, MagicMock
 
@@ -17,10 +16,15 @@ def test_pr_review_mocked(niyam_repo: Path) -> None:
     console = Console(quiet=True)
 
     # Mock get_pr_diff and post_pr_comment
-    with patch("niyam.core.pr.get_pr_diff", return_value="+++ added line") as mock_get_diff, \
-         patch("niyam.core.pr.post_pr_comment") as mock_post_comment, \
-         patch("niyam.core.pr.get_github_repo_owner_name", return_value=("owner", "repo")):
-        
+    with (
+        patch(
+            "niyam.core.pr.get_pr_diff", return_value="+++ added line"
+        ) as mock_get_diff,
+        patch("niyam.core.pr.post_pr_comment") as mock_post_comment,
+        patch(
+            "niyam.core.pr.get_github_repo_owner_name", return_value=("owner", "repo")
+        ),
+    ):
         os.environ["NIYAM_TEST"] = "1"
         try:
             run_pr_review(
@@ -35,7 +39,12 @@ def test_pr_review_mocked(niyam_repo: Path) -> None:
             del os.environ["NIYAM_TEST"]
 
         mock_get_diff.assert_called_once_with("42", "dummy_token", niyam_repo)
-        mock_post_comment.assert_called_once_with("42", "Mocked structured code review for PR #42 using engineering lens.", "dummy_token", niyam_repo)
+        mock_post_comment.assert_called_once_with(
+            "42",
+            "Mocked structured code review for PR #42 using engineering lens.",
+            "dummy_token",
+            niyam_repo,
+        )
 
 
 def test_pr_create_mocked(niyam_repo: Path) -> None:
@@ -44,10 +53,16 @@ def test_pr_create_mocked(niyam_repo: Path) -> None:
     console = Console(quiet=True)
 
     # Mock git commands and PR creation api call
-    with patch("subprocess.run") as mock_run, \
-         patch("niyam.core.pr.create_pr_api", return_value="https://github.com/owner/repo/pull/42") as mock_create_pr, \
-         patch("niyam.core.pr.get_github_repo_owner_name", return_value=("owner", "repo")):
-        
+    with (
+        patch("subprocess.run") as mock_run,
+        patch(
+            "niyam.core.pr.create_pr_api",
+            return_value="https://github.com/owner/repo/pull/42",
+        ) as mock_create_pr,
+        patch(
+            "niyam.core.pr.get_github_repo_owner_name", return_value=("owner", "repo")
+        ),
+    ):
         # Setup git branch name mock response and git push success
         def mock_subprocess_run(args, **kwargs):
             res = MagicMock()
@@ -57,6 +72,7 @@ def test_pr_create_mocked(niyam_repo: Path) -> None:
             else:
                 res.stdout = ""
             return res
+
         mock_run.side_effect = mock_subprocess_run
 
         # Write dummy mission run and evidence report
diff --git a/tests/test_recovery.py b/tests/test_recovery.py
index c4b74a7..5c1b96f 100644
--- a/tests/test_recovery.py
+++ b/tests/test_recovery.py
@@ -3,17 +3,13 @@
 from __future__ import annotations
 
 import os
-import json
 from pathlib import Path
 from unittest.mock import patch, MagicMock
-import pytest
-import yaml
 from rich.console import Console
 
 from niyam.core.config import get_niyam_dir
 from niyam.mission.planner import run_mission_plan, run_mission_approve
 from niyam.mission.executor import (
-    run_mission_start,
     run_mission_retry,
     run_mission_skip,
     run_mission_rollback,
@@ -61,7 +57,9 @@ def test_mission_skip_unblocks_downstream(niyam_repo: Path) -> None:
     assert plan["tasks"][2]["status"] == "completed"
     assert plan["tasks"][3]["status"] == "completed"
     assert plan["tasks"][4]["status"] == "completed"
-    assert plan["mission"]["status"] == "failed"  # Failed is expected because a task was skipped
+    assert (
+        plan["mission"]["status"] == "failed"
+    )  # Failed is expected because a task was skipped
 
 
 def test_mission_retry_requeues_tasks(niyam_repo: Path) -> None:
@@ -121,9 +119,14 @@ def test_mission_rollback_git_checkout(niyam_repo: Path) -> None:
     with patch("subprocess.run") as mock_run:
         mock_run.return_value = MagicMock(returncode=0)
         run_mission_rollback(console=console)
-        
+
         # Verify git checkout base_sha command is executed
-        mock_run.assert_any_call(["git", "checkout", base_sha, "--", "."], cwd=niyam_repo, capture_output=True, text=True)
+        mock_run.assert_any_call(
+            ["git", "checkout", base_sha, "--", "."],
+            cwd=niyam_repo,
+            capture_output=True,
+            text=True,
+        )
 
     plan = load_plan(run_dir)
     assert plan["mission"]["status"] == "failed"
diff --git a/tests/test_remediation.py b/tests/test_remediation.py
index b056046..5d152ba 100644
--- a/tests/test_remediation.py
+++ b/tests/test_remediation.py
@@ -53,7 +53,9 @@ def test_report_fails_on_validation_failure(niyam_repo: Path) -> None:
     assert excinfo.value.code == 1
 
 
-def test_context_diff_ignores_manual_sections(niyam_repo: Path, capsys: pytest.CaptureFixture) -> None:
+def test_context_diff_ignores_manual_sections(
+    niyam_repo: Path, capsys: pytest.CaptureFixture
+) -> None:
     """context diff should ignore changes in manual sections of architecture.md."""
     os.chdir(niyam_repo)
     console = Console()
@@ -70,7 +72,9 @@ def test_context_diff_ignores_manual_sections(niyam_repo: Path, capsys: pytest.C
     newline_idx = content[idx:].index("\n")
     marker_line_end = idx + newline_idx + 1
 
-    modified_content = content[:marker_line_end] + "\nThis is a manual architecture note.\n"
+    modified_content = (
+        content[:marker_line_end] + "\nThis is a manual architecture note.\n"
+    )
     arch_path.write_text(modified_content, encoding="utf-8")
 
     # Clear prior output
@@ -96,7 +100,7 @@ def test_claude_hook_script_formatting_and_imports(tmp_path: Path) -> None:
         allow_write_patterns=[],
         frozen_paths=[],
         guard_enabled=False,
-        remote_policy_url=None
+        remote_policy_url=None,
     )
     assert "import os" not in script
 
@@ -104,8 +108,12 @@ def test_claude_hook_script_formatting_and_imports(tmp_path: Path) -> None:
     hook_file = tmp_path / "pre_tool_guard.py"
     hook_file.write_text(script, encoding="utf-8")
 
-    res = subprocess.run(["ruff", "format", "--check", str(hook_file)], capture_output=True, text=True)
-    assert res.returncode == 0, f"Ruff format check failed on generated hook: {res.stdout}\n{res.stderr}"
+    res = subprocess.run(
+        ["ruff", "format", "--check", str(hook_file)], capture_output=True, text=True
+    )
+    assert res.returncode == 0, (
+        f"Ruff format check failed on generated hook: {res.stdout}\n{res.stderr}"
+    )
 
 
 def test_validate_mission_plan_cycle(tmp_path: Path) -> None:
@@ -128,7 +136,7 @@ def test_validate_mission_plan_cycle(tmp_path: Path) -> None:
             "orchestrator": "claude",
             "parallel": 1,
             "worktree": True,
-            "created": "2026-05-29T12:00:00Z"
+            "created": "2026-05-29T12:00:00Z",
         },
         "tasks": [
             {
@@ -138,7 +146,7 @@ def test_validate_mission_plan_cycle(tmp_path: Path) -> None:
                 "status": "pending",
                 "agent": "mock-agent",
                 "writes_files": False,
-                "depends_on": ["T2"]
+                "depends_on": ["T2"],
             },
             {
                 "id": "T2",
@@ -147,9 +155,9 @@ def test_validate_mission_plan_cycle(tmp_path: Path) -> None:
                 "status": "pending",
                 "agent": "mock-agent",
                 "writes_files": True,
-                "depends_on": ["T1"]
-            }
-        ]
+                "depends_on": ["T1"],
+            },
+        ],
     }
     with open(plan_path, "w", encoding="utf-8") as f:
         yaml.dump(plan_data, f)
@@ -178,7 +186,7 @@ def test_validate_mission_plan_unknown_dependency(tmp_path: Path) -> None:
             "orchestrator": "claude",
             "parallel": 1,
             "worktree": True,
-            "created": "2026-05-29T12:00:00Z"
+            "created": "2026-05-29T12:00:00Z",
         },
         "tasks": [
             {
@@ -188,9 +196,9 @@ def test_validate_mission_plan_unknown_dependency(tmp_path: Path) -> None:
                 "status": "pending",
                 "agent": "mock-agent",
                 "writes_files": False,
-                "depends_on": ["T99"]
+                "depends_on": ["T99"],
             }
-        ]
+        ],
     }
     with open(plan_path, "w", encoding="utf-8") as f:
         yaml.dump(plan_data, f)
@@ -235,13 +243,14 @@ def test_writes_files_false_violation_and_revert(niyam_repo: Path) -> None:
 
     # Patch execution to write a file during execution
     import subprocess as sp
+
     real_run = sp.run
 
     def mock_subprocess_run(args, **kwargs):
         if args and args[0] == "git":
             return real_run(args, **kwargs)
         cwd = kwargs.get("cwd", niyam_repo)
-        
+
         # Modify an existing file or write an unauthorized file
         modified_file = Path(cwd) / "src" / "changed.py"
         modified_file.parent.mkdir(parents=True, exist_ok=True)
@@ -252,8 +261,10 @@ def test_writes_files_false_violation_and_revert(niyam_repo: Path) -> None:
         res.returncode = 0
         return res
 
-    with patch("shutil.which", return_value="/usr/local/bin/claude"), \
-         patch("subprocess.run", side_effect=mock_subprocess_run):
+    with (
+        patch("shutil.which", return_value="/usr/local/bin/claude"),
+        patch("subprocess.run", side_effect=mock_subprocess_run),
+    ):
         try:
             with pytest.raises(SystemExit) as excinfo:
                 run_mission_start(console=console, worktree=False)
diff --git a/tests/test_review.py b/tests/test_review.py
index 790f058..9c0e955 100644
--- a/tests/test_review.py
+++ b/tests/test_review.py
@@ -4,7 +4,6 @@ from __future__ import annotations
 
 import os
 from pathlib import Path
-import pytest
 from rich.console import Console
 
 from niyam.core.review import run_review, get_git_diff
@@ -37,10 +36,19 @@ class TestReview:
         os.environ["NIYAM_TEST"] = "1"
         try:
             # Run engineering collaborative review
-            run_review(lens="engineering", runtime="claude", mode="collaborative", console=console)
-            
+            run_review(
+                lens="engineering",
+                runtime="claude",
+                mode="collaborative",
+                console=console,
+            )
+
             # Check prompt was saved to runs directory
-            prompt_files = list((niyam_repo / ".niyam" / "runs").glob("review-engineering-collaborative-prompt.md"))
+            prompt_files = list(
+                (niyam_repo / ".niyam" / "runs").glob(
+                    "review-engineering-collaborative-prompt.md"
+                )
+            )
             assert len(prompt_files) == 1
             content = prompt_files[0].read_text(encoding="utf-8")
             assert "# Engineering Quality & Architecture Review" in content
@@ -58,9 +66,15 @@ class TestReview:
 
         os.environ["NIYAM_TEST"] = "1"
         try:
-            run_review(lens="security", runtime="claude", mode="adversarial", console=console)
-            
-            prompt_files = list((niyam_repo / ".niyam" / "runs").glob("review-security-adversarial-prompt.md"))
+            run_review(
+                lens="security", runtime="claude", mode="adversarial", console=console
+            )
+
+            prompt_files = list(
+                (niyam_repo / ".niyam" / "runs").glob(
+                    "review-security-adversarial-prompt.md"
+                )
+            )
             assert len(prompt_files) == 1
             content = prompt_files[0].read_text(encoding="utf-8")
             assert "ADVERSARIAL MODE ENABLED" in content
@@ -109,9 +123,8 @@ class TestReview:
 
         secret_file = niyam_repo / "secret.py"
         secret_file.write_text(
-            "aws_key = 'AKIA1234567890123456'\n"
-            "token = 'my-super-secret-token'\n",
-            encoding="utf-8"
+            "aws_key = 'AKIA1234567890123456'\ntoken = 'my-super-secret-token'\n",
+            encoding="utf-8",
         )
 
         diff = get_git_diff(niyam_repo)
diff --git a/tests/test_run_composite.py b/tests/test_run_composite.py
index 9e73085..9a12e05 100644
--- a/tests/test_run_composite.py
+++ b/tests/test_run_composite.py
@@ -5,8 +5,6 @@ from __future__ import annotations
 import os
 from pathlib import Path
 from typer.testing import CliRunner
-import pytest
-import yaml
 
 from niyam.cli import app
 from niyam.core.config import get_niyam_dir
@@ -43,7 +41,7 @@ def test_run_composite_command_file(niyam_repo: Path) -> None:
     assert runs_dir.is_dir()
     runs = list(runs_dir.iterdir())
     assert len(runs) == 1
-    
+
     plan = load_plan(runs[0])
     assert plan["mission"]["status"] == "completed"
     assert plan["mission"]["requirement"] == str(req_file)
@@ -54,10 +52,12 @@ def test_run_composite_command_inline_string(niyam_repo: Path) -> None:
     os.chdir(niyam_repo)
 
     inline_req = "implement a simple helper function"
-    
+
     os.environ["NIYAM_TEST"] = "1"
     try:
-        result = runner.invoke(app, ["run", inline_req, "--auto-approve", "--runtime", "claude"])
+        result = runner.invoke(
+            app, ["run", inline_req, "--auto-approve", "--runtime", "claude"]
+        )
         assert result.exit_code == 0
     finally:
         del os.environ["NIYAM_TEST"]
@@ -66,16 +66,16 @@ def test_run_composite_command_inline_string(niyam_repo: Path) -> None:
     runs_dir = niyam_dir / "runs"
     runs = [d for d in runs_dir.iterdir() if d.is_dir()]
     assert len(runs) > 0
-    
+
     # Sort runs by name/creation to get the latest
     runs.sort(key=lambda d: d.name)
     latest_run = runs[-1]
-    
+
     plan = load_plan(latest_run)
     assert plan["mission"]["status"] == "completed"
     assert plan["mission"]["requirement"] == inline_req
     assert plan["mission"]["orchestrator"] == "claude"
-    
+
     # Requirement file should contain the inline requirements
     req_file_on_disk = latest_run / "requirement.md"
     assert req_file_on_disk.exists()
diff --git a/tests/test_setup.py b/tests/test_setup.py
index dee4a4e..b28ab42 100644
--- a/tests/test_setup.py
+++ b/tests/test_setup.py
@@ -4,8 +4,7 @@ from __future__ import annotations
 
 import os
 from pathlib import Path
-from unittest.mock import patch, MagicMock
-import pytest
+from unittest.mock import patch
 from rich.console import Console
 
 from niyam.core.config import load_niyam_config, get_niyam_dir
@@ -50,10 +49,11 @@ def test_setup_wizard_fresh_initialization(tmp_repo: Path) -> None:
             return f"/usr/local/bin/{cmd}"
         return None
 
-    with patch("rich.prompt.Prompt.ask", side_effect=mock_ask), \
-         patch("rich.prompt.Confirm.ask", side_effect=mock_confirm), \
-         patch("shutil.which", side_effect=mock_which):
-        
+    with (
+        patch("rich.prompt.Prompt.ask", side_effect=mock_ask),
+        patch("rich.prompt.Confirm.ask", side_effect=mock_confirm),
+        patch("shutil.which", side_effect=mock_which),
+    ):
         run_setup(console=console)
 
     # 3. Verify .niyam/ is initialized
@@ -65,7 +65,7 @@ def test_setup_wizard_fresh_initialization(tmp_repo: Path) -> None:
     # Runtimes list should have claude, but not gemini or codex
     assert "claude" in config.runtimes
     assert "gemini" not in config.runtimes
-    
+
     # Verify guards
     assert config.guard.enabled is True
     assert config.guard.careful is True
diff --git a/tests/test_sync.py b/tests/test_sync.py
index 47fc3eb..251bc55 100644
--- a/tests/test_sync.py
+++ b/tests/test_sync.py
@@ -147,7 +147,6 @@ class TestGeminiSync:
         assert "Policies" in content or "Denied" in content
 
 
-
 class TestRuntimeAdd:
     """Tests for runtime add command."""
 
diff --git a/tests/test_templates.py b/tests/test_templates.py
index 1bbf88f..35f2af5 100644
--- a/tests/test_templates.py
+++ b/tests/test_templates.py
@@ -3,9 +3,7 @@
 from __future__ import annotations
 
 import os
-import json
 from pathlib import Path
-import pytest
 import yaml
 from rich.console import Console
 
@@ -24,7 +22,7 @@ def test_builtin_template_planning(niyam_repo: Path) -> None:
         requirements_path="api-endpoint-test",
         console=console,
         template="api-endpoint",
-        runtime_override="claude"
+        runtime_override="claude",
     )
     assert mission_id is not None
 
@@ -37,13 +35,19 @@ def test_builtin_template_planning(niyam_repo: Path) -> None:
     assert plan["mission"]["id"] == mission_id
     assert plan["mission"]["status"] == "planned"
     assert plan["mission"]["orchestrator"] == "claude"
-    
+
     # Verify variable interpolation (using defaults in non-interactive NIYAM_TEST mode)
     # T2 should be: "TDD: Write endpoint contract test case for GET /api/v1/resource"
     tasks = plan["tasks"]
     assert len(tasks) == 5
-    assert tasks[1]["title"] == "TDD: Write endpoint contract test case for GET /api/v1/resource"
-    assert tasks[2]["title"] == "Implementation: implement the GET /api/v1/resource controller and router"
+    assert (
+        tasks[1]["title"]
+        == "TDD: Write endpoint contract test case for GET /api/v1/resource"
+    )
+    assert (
+        tasks[2]["title"]
+        == "Implementation: implement the GET /api/v1/resource controller and router"
+    )
 
 
 def test_custom_template_planning(niyam_repo: Path) -> None:
@@ -60,7 +64,11 @@ def test_custom_template_planning(niyam_repo: Path) -> None:
         "name": "custom-tmpl",
         "description": "My custom development flow",
         "variables": [
-            {"name": "feature_name", "prompt": "Name of the feature", "default": "AwesomeFeature"},
+            {
+                "name": "feature_name",
+                "prompt": "Name of the feature",
+                "default": "AwesomeFeature",
+            },
         ],
         "tasks": [
             {
@@ -76,8 +84,8 @@ def test_custom_template_planning(niyam_repo: Path) -> None:
                 "type": "implementation",
                 "agent": "qa-reviewer",
                 "depends_on": ["T1"],
-            }
-        ]
+            },
+        ],
     }
 
     custom_tmpl_file = custom_tmpl_dir / "my-custom.yaml"
@@ -89,7 +97,7 @@ def test_custom_template_planning(niyam_repo: Path) -> None:
         requirements_path="custom-test",
         console=console,
         template="my-custom",
-        runtime_override="codex"
+        runtime_override="codex",
     )
 
     run_dir = niyam_dir / "runs" / mission_id
diff --git a/tests/test_verification.py b/tests/test_verification.py
index 7191dde..9990305 100644
--- a/tests/test_verification.py
+++ b/tests/test_verification.py
@@ -3,7 +3,6 @@
 from __future__ import annotations
 
 import os
-import json
 from pathlib import Path
 import pytest
 from rich.console import Console
@@ -25,7 +24,7 @@ def test_verification_lifecycle(niyam_repo: Path) -> None:
 
     req_file = niyam_repo / "requirements.md"
     req_file.write_text("# Test requirement\n", encoding="utf-8")
-    
+
     # 2. Plan, Approve, Run, Report
     mission_id = run_mission_plan(str(req_file), console=console)
     run_mission_approve(console=console)

```

## Cryptographic Integrity Manifest

<!-- NIYAM_SIGNATURE_START
{
  "mission_id": "requirements-utils-20260530-115131",
  "timestamp": "2026-05-30T06:26:05.997679Z",
  "files": {
    "mission-plan.yaml": "93aee873a06e5b76e232e9440ec7d1a59b29b1c6c9a1361ce48455c86d7a4417",
    "execution-log.json": "e51dc4db716bc34c2fab9520986664457e7c9d2d59c3709224f909107b8a73d9",
    "validation-results.md": "118bfeb5fdea99a2aef94545acbfa29eddb1535e1bfe7ec9baec3bddce24d5b0",
    "policy-events.json": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945",
    "CLAUDE.md": "49af27bc91979af68b70c685bbb9efa3f8fd8d2eb867fb36a5ed00b151d9cfea",
    "niyam/cli.py": "6f702aef1cd0abf338f1bf11b23821d15a9931232b10dbd6fa9a8c546083cb20",
    "niyam/core/ci.py": "fc848e0b009c58fc1532d10d34d2eab55547454c88920d4ee671c28c045c9f46",
    "niyam/core/config.py": "bd65aba9cafd382277c0a82be5e0152132379b3d3c1540914aafc6366b5c733a",
    "niyam/core/context.py": "ffd571c3d4f9f34172f99aa0702cc6e9486d9822d073def8a626381e5bd22d9a",
    "niyam/core/doctor.py": "078e5f9cec7df340e1664268913bf93c69107ebd52855ea165a0b9a16572c96e",
    "niyam/core/init.py": "1c84224f2ddca08e7f3bc0703f64c01718b8eafa45772ef298660acc81129c3a",
    "niyam/core/memory.py": "c88259db5ac24451cd14eb6b3fc20eee22d5884cfacdf3800ecd4b1e4f232b48",
    "niyam/core/packs.py": "8fb5b2fa3bf99ebbd252635c0bca2e8611e46d0f12d4695bd53eaa3c873d27f4",
    "niyam/core/pr.py": "4ed870adf8921a1f15123fb80a4acf2e077397aced57d95d882ef67edbce43bc",
    "niyam/core/review.py": "0ed917bd8a26d9e5341193e69eac542fd17d982da8d9f823d0264f77d6ee7439",
    "niyam/core/security.py": "53519b91e1db22e7b84b42fcb77488caaa2c0fc7227465a2e31edec3d6eec9a8",
    "niyam/core/setup.py": "d4bd76e739b6f530ab9c461d794087e8d6ec40ed8a75f92d258336f1efcdbf2d",
    "niyam/core/sync.py": "3ae94082487f484564f72e90d316e797bc140a3f376461691d76e9972732c697",
    "niyam/evidence/reporter.py": "2f923f743b75e3a9d836c7c50b73954a8d0229a4258661daaaa92429f97f0959",
    "niyam/mission/dashboard.py": "680977d0ddd48e5cde8d292eb46add3fae8e8ed4dd83a5c5797ad37fecb215a8",
    "niyam/mission/executor.py": "8a7114c78066f6fa2caf53553803797d089586fbeb699b388748e63b5d6fc460",
    "niyam/mission/planner.py": "de57147ec69c3bb8def65644a03a64dde47b23c6620c85f40b933c37c7f0146d",
    "niyam/mission/reporter.py": "dd642c38e34bbefa1f2763e6fc85cc8c9d2227dc151e03b2d131008ea30dbc05",
    "niyam/mission/status.py": "00b282a188c08bd99a485c37655da0c4a9163500532f4a74f5cbcf366a238d11",
    "niyam/mission/validator.py": "b496de10e5d420bf713b524d86639d34cbad41b6e3c5c026471108c6f791dc43",
    "niyam/policies/guard.py": "58c9567e24db87a7e32e3c30021674bb4a3ff89aa6cd20fb0eebc36c6b0be9f3",
    "niyam/policies/validator.py": "3a8437e28b8dc3d2f7783a8d5a1e904417747005b9a56b42fc39fc038895d216",
    "niyam/runtimes/claude.py": "d5b106c900e68a0bf06df418acd9e602c4524a6816aa10793fb8df9a0f519c94",
    "niyam/runtimes/codex.py": "f1c8ad8aabd0c069bc8a1a678b4b62cb847fc788018bc1c0a5ac13a98a0810cf",
    "niyam/runtimes/gemini.py": "db1bd675d112f206f60d17e5e69c3c68025ac78d99eb800b34b1668c45d17201",
    "tests/conftest.py": "24a3ffee9af980745b94509359c6421f4139445e4ea89632d7c6739cb6628caf",
    "tests/test_ci.py": "c5807af57284d124d20bf89bf7020ef76818362ae170171268ef34bddcb31228",
    "tests/test_dashboard.py": "d51821040fc37adf3a04232d5eb8d0d2f1576e20a3abab5b6b88cb4cd90695e4",
    "tests/test_doctor.py": "cf0afb8e061237e2ea45ae0705d046be4335cab3c0a6afaf6339f747b4ec9f37",
    "tests/test_doctor_enhanced.py": "e94dd8b809002b14c3d6dad5597c6adce967c23b3486da1db4039b468e1e1b68",
    "tests/test_fleet.py": "17dcd4929b17d146b6c39716ba3e3c58d939bc8499423e52b855b8dd0e591cde",
    "tests/test_guardrails.py": "89a67d7d54f5b33c28079694d9b2c30137540fc0d6faf5b81e8101b9cd5f683b",
    "tests/test_hooks.py": "c559772d02a7ab2fca1bbf375df3254c2b30fc52eabee996ee53bdd0f2f1bada",
    "tests/test_init.py": "05dcff89f0c33f52830a0ce771e838e2b40ecd94adc4dad4cdaa417adf1c4fd0",
    "tests/test_memory.py": "139f30d9e5da72a8afd6414f6cefecf275f5efc75aa8e801019fbc11f0e1ec8d",
    "tests/test_mission.py": "acbf35440c51a9e98a6740f1860652f98bb3487e5996f307a0d8bc10d9957030",
    "tests/test_multi_runtime.py": "c9b3c814d778bf7a4da2ae8fe06ddd025799f500f46b016e5813dcc809a55441",
    "tests/test_packs.py": "97642049b1968d4fd5302056c8b594c9ca0781660233907c46b90918a440bf44",
    "tests/test_pr.py": "1a76ef5b19e5182ec4b22b43bd9ffe47ab41987155d6c8e188335efb512ba3d0",
    "tests/test_recovery.py": "00fa70ad627a871f45926fde6392d21998a2507e2a1a6f7331e41965c7702955",
    "tests/test_remediation.py": "496467d8f2d11c43fc94372bba6759b170023716840c2631ca34b53707a67fd3",
    "tests/test_review.py": "40280556be4b3757cb9490b159c0094224d0c1c203e2805c166bb44ebb4668bb",
    "tests/test_run_composite.py": "e50972410c3c36a1bf0770caedb304ffb073979642c039147f64dfa11b07d573",
    "tests/test_setup.py": "14b0697b9ab236f7ea5f34f396719ff6c26f04030f5f4738ac99dcac1682ec7f",
    "tests/test_sync.py": "232aa60b69eda8e555a194816230bbc696c0338c294193d455b7fcb3735a773e",
    "tests/test_templates.py": "9c3b7e9ff08a05bd2f2755db3bc71f0b65fbfe4c41c3f78fedb2f15249c7481e",
    "tests/test_verification.py": "7ff6d96ba9377f6562fbba528dcd92476a5da1e623ae7b74a27c3d2a6a08ccbb",
    "scratch/": "DELETED",
    "niyam/core/utils.py": "ccb29a32ffaea95fea75d259e84ad9c4c65e7ea093547f26a9998cceb5b77d3f",
    "tests/test_utils.py": "241bfdcf24b1a01de4cea92df73b9c92d603900fb74c6f3df0fd3a3f6ff0750f"
  },
  "signed": false
}
NIYAM_SIGNATURE_END -->
