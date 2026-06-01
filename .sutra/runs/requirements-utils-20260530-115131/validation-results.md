
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
