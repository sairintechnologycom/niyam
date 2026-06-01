
## Validation Run - 2026-05-31T10:15:37.172913Z
**Command:** `ruff format --check .`
**Exit Code:** `1`

### stdout
```
Would reformat: build_binary.py
Would reformat: niyam/cli/__init__.py
Would reformat: niyam/cli/context.py
Would reformat: niyam/cli/main_cmds.py
Would reformat: niyam/cli/mission.py
Would reformat: niyam/core/context.py
Would reformat: niyam/core/doctor.py
Would reformat: niyam/core/sync.py
Would reformat: niyam/mission/planner.py
Would reformat: niyam/policies/guard.py
Would reformat: niyam/runtimes/base.py
Would reformat: tests/test_cli_refinement.py
Would reformat: tests/test_doctor_check.py
Would reformat: tests/test_doctor_enhanced.py
Would reformat: tests/test_planner_robust.py
15 files would be reformatted, 69 files already formatted

```

## Validation Run - 2026-05-31T10:15:37.203503Z
**Command:** `ruff check .`
**Exit Code:** `1`

### stdout
```
F401 [*] `os` imported but unused
 --> build_binary.py:1:8
  |
1 | import os
  |        ^^
2 | import subprocess
3 | import sys
  |
help: Remove unused import: `os`

F401 `PyInstaller` imported but unused; consider using `importlib.util.find_spec` to test for availability
  --> build_binary.py:10:16
   |
 8 |     # Check if pyinstaller is installed
 9 |     try:
10 |         import PyInstaller
   |                ^^^^^^^^^^^
11 |     except ImportError:
12 |         print("Error: PyInstaller is not installed. Run: pip install pyinstaller")
   |
help: Remove unused import: `PyInstaller`

F821 Undefined name `Annotated`
  --> niyam/cli/context.py:10:14
   |
 8 | @context_app.command("refresh")
 9 | def context_refresh(
10 |     dry_run: Annotated[
   |              ^^^^^^^^^
11 |         bool,
12 |         typer.Option("--dry-run", help="Preview changes without writing."),
   |

F821 Undefined name `typer`
  --> niyam/cli/context.py:12:9
   |
10 |     dry_run: Annotated[
11 |         bool,
12 |         typer.Option("--dry-run", help="Preview changes without writing."),
   |         ^^^^^
13 |     ] = False,
14 | ) -> None:
   |

F401 [*] `sys` imported but unused
   --> niyam/cli/main_cmds.py:541:12
    |
539 | ) -> None:
540 |     """Automatically execute the next step in the current run."""
541 |     import sys
    |            ^^^
542 |     from pathlib import Path
543 |     import yaml
    |
help: Remove unused import: `sys`

F401 [*] `pathlib.Path` imported but unused
   --> niyam/cli/main_cmds.py:542:25
    |
540 |     """Automatically execute the next step in the current run."""
541 |     import sys
542 |     from pathlib import Path
    |                         ^^^^
543 |     import yaml
544 |     from niyam.core.config import find_niyam_root, get_niyam_dir
    |
help: Remove unused import: `pathlib.Path`

F401 [*] `pathlib.Path` imported but unused
 --> niyam/runtimes/claude.py:7:21
  |
5 | import json
6 | import shutil
7 | from pathlib import Path
  |                     ^^^^
8 |
9 | import yaml
  |
help: Remove unused import: `pathlib.Path`

F841 Local variable `mock_run` is assigned to but never used
  --> tests/test_doctor_check.py:72:82
   |
70 |     mock_res.stderr = "Linter syntax error on line 4"
71 |
72 |     with patch("niyam.core.security.safe_run_command", return_value=mock_res) as mock_run:
   |                                                                                  ^^^^^^^^
73 |         results = _check_lint_format(niyam_repo)
   |
help: Remove assignment to unused variable `mock_run`

Found 8 errors.
[*] 4 fixable with the `--fix` option (1 hidden fix can be enabled with the `--unsafe-fixes` option).

```

## Validation Check - typecheck - 2026-05-31T10:15:37.204195Z
**Status:** ℹ SKIPPED — Not configured


## Validation Check - build - 2026-05-31T10:15:37.204282Z
**Status:** ℹ SKIPPED — Not configured


## Validation Run - 2026-05-31T10:15:54.301367Z
**Command:** `pytest`
**Exit Code:** `0`

### stdout
```
============================= test session starts ==============================
platform darwin -- Python 3.14.3, pytest-9.0.3, pluggy-1.6.0 -- /opt/homebrew/opt/python@3.14/bin/python3.14
cachedir: .pytest_cache
rootdir: /Users/bhushan/Documents/Projects/niyam/.niyam/runs/add-info-cmd-20260531-143733/worktrees/T1
configfile: pyproject.toml
testpaths: tests
plugins: cov-7.1.0, pytest_tmp_files-0.0.2, anyio-4.13.0
collecting ... collected 136 items

tests/test_ci.py::test_non_interactive_fails_unapproved PASSED           [  0%]
tests/test_ci.py::test_non_interactive_auto_approve PASSED               [  1%]
tests/test_ci.py::test_remote_policy_fetching PASSED                     [  2%]
tests/test_ci.py::test_remote_policy_fallback PASSED                     [  2%]
tests/test_ci.py::test_ci_verify_strict_missing_evidence PASSED          [  3%]
tests/test_ci.py::test_ci_verify_non_strict_missing_evidence PASSED      [  4%]
tests/test_ci.py::test_ci_verify_write_violation PASSED                  [  5%]
tests/test_cli.py::TestCLI::test_version PASSED                          [  5%]
tests/test_cli.py::TestCLI::test_help PASSED                             [  6%]
tests/test_cli.py::TestCLI::test_update_help PASSED                      [  7%]
tests/test_cli.py::TestCLI::test_start_help PASSED                       [  8%]
tests/test_cli.py::TestCLI::test_next_help PASSED                        [  8%]
tests/test_cli.py::TestCLI::test_context_help PASSED                     [  9%]
tests/test_cli.py::TestCLI::test_guard_help PASSED                       [ 10%]
tests/test_cli.py::TestCLI::test_runtime_help PASSED                     [ 11%]
tests/test_cli.py::TestCLI::test_policy_help PASSED                      [ 11%]
tests/test_cli_refinement.py::test_interactive_refiner_loop PASSED       [ 12%]
tests/test_compare.py::test_comparison_runs_multiple_executors PASSED    [ 13%]
tests/test_compare.py::test_compare_cli_command PASSED                   [ 13%]
tests/test_context.py::TestContextRefresh::test_context_refresh_creates_architecture PASSED [ 14%]
tests/test_context.py::TestContextRefresh::test_context_refresh_creates_validation PASSED [ 15%]
tests/test_context.py::TestContextRefresh::test_context_refresh_detects_python PASSED [ 16%]
tests/test_context.py::TestContextRefresh::test_context_refresh_detects_node PASSED [ 16%]
tests/test_context.py::TestContextRefresh::test_context_refresh_preserves_manual_section PASSED [ 17%]
tests/test_contract_enforcement.py::test_any_bypass_removed_and_contract_prompt_enrichment PASSED [ 18%]
tests/test_dashboard.py::test_dashboard_rendering PASSED                 [ 19%]
tests/test_dashboard.py::test_dashboard_watch_mode PASSED                [ 19%]
tests/test_doctor.py::TestDoctor::test_doctor_passes_on_fresh_init PASSED [ 20%]
tests/test_doctor.py::TestDoctor::test_doctor_fails_without_niyam PASSED [ 21%]
tests/test_doctor.py::TestDoctor::test_doctor_detects_missing_files PASSED [ 22%]
tests/test_doctor.py::TestDoctor::test_doctor_detects_invalid_yaml PASSED [ 22%]
tests/test_doctor_check.py::test_doctor_check_lint_format_success PASSED [ 23%]
tests/test_doctor_check.py::test_doctor_check_lint_format_failure PASSED [ 24%]
tests/test_doctor_enhanced.py::test_doctor_runtimes_in_path PASSED       [ 25%]
tests/test_doctor_enhanced.py::test_doctor_agents_validity PASSED        [ 25%]
tests/test_doctor_enhanced.py::test_doctor_validation_commands PASSED    [ 26%]
tests/test_doctor_enhanced.py::test_doctor_git_status_dirty PASSED       [ 27%]
tests/test_doctor_enhanced.py::test_doctor_smoke_tests PASSED            [ 27%]
tests/test_fleet.py::test_fleet_parallel_execution PASSED                [ 28%]
tests/test_fleet.py::test_fleet_dependency_failure PASSED                [ 29%]
tests/test_fleet.py::test_fleet_worktree_fallback_when_no_git PASSED     [ 30%]
tests/test_guard.py::TestGuard::test_guard_enable PASSED                 [ 30%]
tests/test_guard.py::TestGuard::test_guard_disable PASSED                [ 31%]
tests/test_guard.py::TestGuard::test_guard_careful_adds_warn_list PASSED [ 32%]
tests/test_guard.py::TestGuard::test_guard_freeze_adds_path PASSED       [ 33%]
tests/test_guard.py::TestGuard::test_guard_freeze_enables_guard PASSED   [ 33%]
tests/test_guardrails.py::test_path_write_denial_and_revert PASSED       [ 34%]
tests/test_hello.py::test_hello_no_args PASSED                           [ 35%]
tests/test_hello.py::test_hello_with_name PASSED                         [ 36%]
tests/test_hooks.py::test_hooks_lifecycle_triggers PASSED                [ 36%]
tests/test_init.py::TestInit::test_init_creates_niyam_directory PASSED   [ 37%]
tests/test_init.py::TestInit::test_init_creates_mvp_directories PASSED   [ 38%]
tests/test_init.py::TestInit::test_init_creates_niyam_yaml PASSED        [ 38%]
tests/test_init.py::TestInit::test_init_creates_agents PASSED            [ 39%]
tests/test_init.py::TestInit::test_init_creates_skills PASSED            [ 40%]
tests/test_init.py::TestInit::test_init_creates_commands PASSED          [ 41%]
tests/test_init.py::TestInit::test_init_creates_policies PASSED          [ 41%]
tests/test_init.py::TestInit::test_init_fails_if_already_exists PASSED   [ 42%]
tests/test_init.py::TestInit::test_init_force_overwrites PASSED          [ 43%]
tests/test_init.py::TestInit::test_init_dry_run_creates_nothing PASSED   [ 44%]
tests/test_init.py::TestInit::test_init_with_claude_runtime PASSED       [ 44%]
tests/test_init.py::TestInit::test_init_invalid_profile_fails PASSED     [ 45%]
tests/test_init.py::TestInit::test_init_backend_profile PASSED           [ 46%]
tests/test_init.py::TestInit::test_init_frontend_profile PASSED          [ 47%]
tests/test_memory.py::TestMemory::test_memory_show PASSED                [ 47%]
tests/test_memory.py::TestMemory::test_memory_add PASSED                 [ 48%]
tests/test_memory.py::TestMemory::test_memory_clear PASSED               [ 49%]
tests/test_memory.py::TestMemory::test_memory_sync_propagates_to_runtimes PASSED [ 50%]
tests/test_mission.py::TestMission::test_mission_plan_creates_files PASSED [ 50%]
tests/test_mission.py::TestMission::test_mission_approve PASSED          [ 51%]
tests/test_mission.py::TestMission::test_mission_execution_lifecycle PASSED [ 52%]
tests/test_mission.py::TestMission::test_mission_pause_resume PASSED     [ 52%]
tests/test_mission.py::TestMission::test_mission_plan_strict PASSED      [ 53%]
tests/test_mission.py::TestMission::test_resolve_mission_prefers_active_over_completed PASSED [ 54%]
tests/test_multi_runtime.py::test_planner_prompt_contains_runtime PASSED [ 55%]
tests/test_multi_runtime.py::test_planner_parses_runtime_field PASSED    [ 55%]
tests/test_multi_runtime.py::test_executor_resolves_task_runtime PASSED  [ 56%]
tests/test_packs.py::TestPacks::test_list_packs PASSED                   [ 57%]
tests/test_packs.py::TestPacks::test_add_pack_copies_files PASSED        [ 58%]
tests/test_packs.py::TestPacks::test_add_pack_conflict PASSED            [ 58%]
tests/test_packs.py::TestPacks::test_remove_pack PASSED                  [ 59%]
tests/test_packs.py::TestPacks::test_sync_packs PASSED                   [ 60%]
tests/test_planner_robust.py::test_extract_yaml_or_json_malformed PASSED [ 61%]
tests/test_planner_robust.py::test_fallback_matches_requirement_keywords PASSED [ 61%]
tests/test_planner_robust.py::test_validation_commands_injected_from_project_yaml PASSED [ 62%]
tests/test_planner_robust.py::test_planner_retry_on_bad_output PASSED    [ 63%]
tests/test_pr.py::test_pr_review_mocked PASSED                           [ 63%]
tests/test_pr.py::test_pr_create_mocked PASSED                           [ 64%]
tests/test_recovery.py::test_mission_skip_unblocks_downstream PASSED     [ 65%]
tests/test_recovery.py::test_mission_retry_requeues_tasks PASSED         [ 66%]
tests/test_recovery.py::test_mission_rollback_git_checkout PASSED        [ 66%]
tests/test_remediation.py::test_bash_sh_blocked PASSED                   [ 67%]
tests/test_remediation.py::test_report_fails_on_validation_failure PASSED [ 68%]
tests/test_remediation.py::test_context_diff_ignores_manual_sections PASSED [ 69%]
tests/test_remediation.py::test_claude_hook_script_formatting_and_imports PASSED [ 69%]
tests/test_remediation.py::test_validate_mission_plan_cycle PASSED       [ 70%]
tests/test_remediation.py::test_validate_mission_plan_unknown_dependency PASSED [ 71%]
tests/test_remediation.py::test_writes_files_false_violation_and_revert PASSED [ 72%]
tests/test_review.py::TestReview::test_get_git_diff_untracked_file PASSED [ 72%]
tests/test_review.py::TestReview::test_run_review_engineering_lens PASSED [ 73%]
tests/test_review.py::TestReview::test_run_review_adversarial_mode PASSED [ 74%]
tests/test_review.py::TestReview::test_get_git_diff_file_size_limit PASSED [ 75%]
tests/test_review.py::TestReview::test_get_git_diff_budget_limit PASSED  [ 75%]
tests/test_review.py::TestReview::test_get_git_diff_skip_binary_files PASSED [ 76%]
tests/test_review.py::TestReview::test_get_git_diff_redact_secrets PASSED [ 77%]
tests/test_run_composite.py::test_run_composite_command_file PASSED      [ 77%]
tests/test_run_composite.py::test_run_composite_command_inline_string PASSED [ 78%]
tests/test_setup.py::test_setup_wizard_fresh_initialization PASSED       [ 79%]
tests/test_sync.py::TestClaudeSync::test_claude_sync_creates_claude_md PASSED [ 80%]
tests/test_sync.py::TestClaudeSync::test_claude_sync_creates_claude_dir PASSED [ 80%]
tests/test_sync.py::TestClaudeSync::test_claude_sync_creates_agents PASSED [ 81%]
tests/test_sync.py::TestClaudeSync::test_claude_sync_creates_hooks PASSED [ 82%]
tests/test_sync.py::TestClaudeSync::test_claude_sync_creates_settings PASSED [ 83%]
tests/test_sync.py::TestClaudeSync::test_claude_md_contains_policies PASSED [ 83%]
tests/test_sync.py::TestCodexSync::test_codex_sync_creates_agents_md PASSED [ 84%]
tests/test_sync.py::TestCodexSync::test_agents_md_contains_policies PASSED [ 85%]
tests/test_sync.py::TestCodexSync::test_codex_sync_creates_hooks_and_settings PASSED [ 86%]
tests/test_sync.py::TestGeminiSync::test_gemini_sync_creates_gemini_md PASSED [ 86%]
tests/test_sync.py::TestGeminiSync::test_gemini_sync_creates_gemini_dir PASSED [ 87%]
tests/test_sync.py::TestGeminiSync::test_gemini_md_contains_policies PASSED [ 88%]
tests/test_sync.py::TestGeminiSync::test_gemini_sync_creates_hooks_and_settings PASSED [ 88%]
tests/test_sync.py::TestRuntimeAdd::test_runtime_add_updates_config PASSED [ 89%]
tests/test_sync.py::TestRuntimeAdd::test_runtime_add_duplicate_is_safe PASSED [ 90%]
tests/test_template_boilerplating.py::test_template_boilerplating_on_refresh PASSED [ 91%]
tests/test_templates.py::test_builtin_template_planning PASSED           [ 91%]
tests/test_templates.py::test_custom_template_planning PASSED            [ 92%]
tests/test_token_parsing.py::test_parse_claude_cli_output PASSED         [ 93%]
tests/test_token_parsing.py::test_parse_gemini_cli_output PASSED         [ 94%]
tests/test_token_parsing.py::test_parse_codex_cli_output PASSED          [ 94%]
tests/test_token_parsing.py::test_parse_unknown_format_returns_none PASSED [ 95%]
tests/test_token_parsing.py::test_ledger_labels_estimates_honestly PASSED [ 96%]
tests/test_token_parsing.py::test_ledger_uses_real_values_when_available PASSED [ 97%]
tests/test_token_parsing.py::test_baseline_multiplier_opt_in PASSED      [ 97%]
tests/test_utils.py::test_format_date_iso_utc PASSED                     [ 98%]
tests/test_utils.py::test_format_date_iso_naive PASSED                   [ 99%]
tests/test_verification.py::test_verification_lifecycle PASSED           [100%]

============================= 136 passed in 15.20s =============================

```

## Validation Run - 2026-05-31T10:27:09.681176Z
**Command:** `ruff format --check .`
**Exit Code:** `1`

### stdout
```
Would reformat: build_binary.py
Would reformat: niyam/cli/__init__.py
Would reformat: niyam/cli/context.py
Would reformat: niyam/cli/main_cmds.py
Would reformat: niyam/cli/mission.py
Would reformat: niyam/core/context.py
Would reformat: niyam/core/doctor.py
Would reformat: niyam/core/sync.py
Would reformat: niyam/mission/planner.py
Would reformat: niyam/policies/guard.py
Would reformat: niyam/runtimes/base.py
Would reformat: tests/test_cli_refinement.py
Would reformat: tests/test_doctor_check.py
Would reformat: tests/test_doctor_enhanced.py
Would reformat: tests/test_planner_robust.py
15 files would be reformatted, 69 files already formatted

```

## Validation Run - 2026-05-31T10:27:09.710409Z
**Command:** `ruff check .`
**Exit Code:** `1`

### stdout
```
F401 [*] `os` imported but unused
 --> build_binary.py:1:8
  |
1 | import os
  |        ^^
2 | import subprocess
3 | import sys
  |
help: Remove unused import: `os`

F401 `PyInstaller` imported but unused; consider using `importlib.util.find_spec` to test for availability
  --> build_binary.py:10:16
   |
 8 |     # Check if pyinstaller is installed
 9 |     try:
10 |         import PyInstaller
   |                ^^^^^^^^^^^
11 |     except ImportError:
12 |         print("Error: PyInstaller is not installed. Run: pip install pyinstaller")
   |
help: Remove unused import: `PyInstaller`

F821 Undefined name `Annotated`
  --> niyam/cli/context.py:10:14
   |
 8 | @context_app.command("refresh")
 9 | def context_refresh(
10 |     dry_run: Annotated[
   |              ^^^^^^^^^
11 |         bool,
12 |         typer.Option("--dry-run", help="Preview changes without writing."),
   |

F821 Undefined name `typer`
  --> niyam/cli/context.py:12:9
   |
10 |     dry_run: Annotated[
11 |         bool,
12 |         typer.Option("--dry-run", help="Preview changes without writing."),
   |         ^^^^^
13 |     ] = False,
14 | ) -> None:
   |

F401 [*] `sys` imported but unused
   --> niyam/cli/main_cmds.py:541:12
    |
539 | ) -> None:
540 |     """Automatically execute the next step in the current run."""
541 |     import sys
    |            ^^^
542 |     from pathlib import Path
543 |     import yaml
    |
help: Remove unused import: `sys`

F401 [*] `pathlib.Path` imported but unused
   --> niyam/cli/main_cmds.py:542:25
    |
540 |     """Automatically execute the next step in the current run."""
541 |     import sys
542 |     from pathlib import Path
    |                         ^^^^
543 |     import yaml
544 |     from niyam.core.config import find_niyam_root, get_niyam_dir
    |
help: Remove unused import: `pathlib.Path`

F401 [*] `pathlib.Path` imported but unused
 --> niyam/runtimes/claude.py:7:21
  |
5 | import json
6 | import shutil
7 | from pathlib import Path
  |                     ^^^^
8 |
9 | import yaml
  |
help: Remove unused import: `pathlib.Path`

F841 Local variable `mock_run` is assigned to but never used
  --> tests/test_doctor_check.py:72:82
   |
70 |     mock_res.stderr = "Linter syntax error on line 4"
71 |
72 |     with patch("niyam.core.security.safe_run_command", return_value=mock_res) as mock_run:
   |                                                                                  ^^^^^^^^
73 |         results = _check_lint_format(niyam_repo)
   |
help: Remove assignment to unused variable `mock_run`

Found 8 errors.
[*] 4 fixable with the `--fix` option (1 hidden fix can be enabled with the `--unsafe-fixes` option).

```

## Validation Check - typecheck - 2026-05-31T10:27:09.711049Z
**Status:** ℹ SKIPPED — Not configured


## Validation Check - build - 2026-05-31T10:27:09.711121Z
**Status:** ℹ SKIPPED — Not configured


## Validation Run - 2026-05-31T10:27:25.030803Z
**Command:** `pytest`
**Exit Code:** `1`

### stdout
```
============================= test session starts ==============================
platform darwin -- Python 3.14.3, pytest-9.0.3, pluggy-1.6.0 -- /opt/homebrew/opt/python@3.14/bin/python3.14
cachedir: .pytest_cache
rootdir: /Users/bhushan/Documents/Projects/niyam/.niyam/runs/add-info-cmd-20260531-143733/worktrees/T1
configfile: pyproject.toml
testpaths: tests
plugins: cov-7.1.0, pytest_tmp_files-0.0.2, anyio-4.13.0
collecting ... collected 136 items

tests/test_ci.py::test_non_interactive_fails_unapproved PASSED           [  0%]
tests/test_ci.py::test_non_interactive_auto_approve PASSED               [  1%]
tests/test_ci.py::test_remote_policy_fetching PASSED                     [  2%]
tests/test_ci.py::test_remote_policy_fallback PASSED                     [  2%]
tests/test_ci.py::test_ci_verify_strict_missing_evidence PASSED          [  3%]
tests/test_ci.py::test_ci_verify_non_strict_missing_evidence PASSED      [  4%]
tests/test_ci.py::test_ci_verify_write_violation PASSED                  [  5%]
tests/test_cli.py::TestCLI::test_version PASSED                          [  5%]
tests/test_cli.py::TestCLI::test_help PASSED                             [  6%]
tests/test_cli.py::TestCLI::test_update_help PASSED                      [  7%]
tests/test_cli.py::TestCLI::test_start_help PASSED                       [  8%]
tests/test_cli.py::TestCLI::test_next_help PASSED                        [  8%]
tests/test_cli.py::TestCLI::test_context_help PASSED                     [  9%]
tests/test_cli.py::TestCLI::test_guard_help PASSED                       [ 10%]
tests/test_cli.py::TestCLI::test_runtime_help PASSED                     [ 11%]
tests/test_cli.py::TestCLI::test_policy_help PASSED                      [ 11%]
tests/test_cli_refinement.py::test_interactive_refiner_loop PASSED       [ 12%]
tests/test_compare.py::test_comparison_runs_multiple_executors PASSED    [ 13%]
tests/test_compare.py::test_compare_cli_command PASSED                   [ 13%]
tests/test_context.py::TestContextRefresh::test_context_refresh_creates_architecture PASSED [ 14%]
tests/test_context.py::TestContextRefresh::test_context_refresh_creates_validation PASSED [ 15%]
tests/test_context.py::TestContextRefresh::test_context_refresh_detects_python PASSED [ 16%]
tests/test_context.py::TestContextRefresh::test_context_refresh_detects_node PASSED [ 16%]
tests/test_context.py::TestContextRefresh::test_context_refresh_preserves_manual_section PASSED [ 17%]
tests/test_contract_enforcement.py::test_any_bypass_removed_and_contract_prompt_enrichment PASSED [ 18%]
tests/test_dashboard.py::test_dashboard_rendering PASSED                 [ 19%]
tests/test_dashboard.py::test_dashboard_watch_mode PASSED                [ 19%]
tests/test_doctor.py::TestDoctor::test_doctor_passes_on_fresh_init PASSED [ 20%]
tests/test_doctor.py::TestDoctor::test_doctor_fails_without_niyam PASSED [ 21%]
tests/test_doctor.py::TestDoctor::test_doctor_detects_missing_files PASSED [ 22%]
tests/test_doctor.py::TestDoctor::test_doctor_detects_invalid_yaml PASSED [ 22%]
tests/test_doctor_check.py::test_doctor_check_lint_format_success PASSED [ 23%]
tests/test_doctor_check.py::test_doctor_check_lint_format_failure PASSED [ 24%]
tests/test_doctor_enhanced.py::test_doctor_runtimes_in_path PASSED       [ 25%]
tests/test_doctor_enhanced.py::test_doctor_agents_validity PASSED        [ 25%]
tests/test_doctor_enhanced.py::test_doctor_validation_commands PASSED    [ 26%]
tests/test_doctor_enhanced.py::test_doctor_git_status_dirty PASSED       [ 27%]
tests/test_doctor_enhanced.py::test_doctor_smoke_tests PASSED            [ 27%]
tests/test_fleet.py::test_fleet_parallel_execution PASSED                [ 28%]
tests/test_fleet.py::test_fleet_dependency_failure PASSED                [ 29%]
tests/test_fleet.py::test_fleet_worktree_fallback_when_no_git PASSED     [ 30%]
tests/test_guard.py::TestGuard::test_guard_enable PASSED                 [ 30%]
tests/test_guard.py::TestGuard::test_guard_disable PASSED                [ 31%]
tests/test_guard.py::TestGuard::test_guard_careful_adds_warn_list PASSED [ 32%]
tests/test_guard.py::TestGuard::test_guard_freeze_adds_path PASSED       [ 33%]
tests/test_guard.py::TestGuard::test_guard_freeze_enables_guard PASSED   [ 33%]
tests/test_guardrails.py::test_path_write_denial_and_revert PASSED       [ 34%]
tests/test_hello.py::test_hello_no_args PASSED                           [ 35%]
tests/test_hello.py::test_hello_with_name PASSED                         [ 36%]
tests/test_hooks.py::test_hooks_lifecycle_triggers PASSED                [ 36%]
tests/test_init.py::TestInit::test_init_creates_niyam_directory PASSED   [ 37%]
tests/test_init.py::TestInit::test_init_creates_mvp_directories PASSED   [ 38%]
tests/test_init.py::TestInit::test_init_creates_niyam_yaml PASSED        [ 38%]
tests/test_init.py::TestInit::test_init_creates_agents PASSED            [ 39%]
tests/test_init.py::TestInit::test_init_creates_skills PASSED            [ 40%]
tests/test_init.py::TestInit::test_init_creates_commands PASSED          [ 41%]
tests/test_init.py::TestInit::test_init_creates_policies PASSED          [ 41%]
tests/test_init.py::TestInit::test_init_fails_if_already_exists PASSED   [ 42%]
tests/test_init.py::TestInit::test_init_force_overwrites PASSED          [ 43%]
tests/test_init.py::TestInit::test_init_dry_run_creates_nothing PASSED   [ 44%]
tests/test_init.py::TestInit::test_init_with_claude_runtime PASSED       [ 44%]
tests/test_init.py::TestInit::test_init_invalid_profile_fails PASSED     [ 45%]
tests/test_init.py::TestInit::test_init_backend_profile PASSED           [ 46%]
tests/test_init.py::TestInit::test_init_frontend_profile PASSED          [ 47%]
tests/test_memory.py::TestMemory::test_memory_show PASSED                [ 47%]
tests/test_memory.py::TestMemory::test_memory_add PASSED                 [ 48%]
tests/test_memory.py::TestMemory::test_memory_clear PASSED               [ 49%]
tests/test_memory.py::TestMemory::test_memory_sync_propagates_to_runtimes PASSED [ 50%]
tests/test_mission.py::TestMission::test_mission_plan_creates_files PASSED [ 50%]
tests/test_mission.py::TestMission::test_mission_approve PASSED          [ 51%]
tests/test_mission.py::TestMission::test_mission_execution_lifecycle PASSED [ 52%]
tests/test_mission.py::TestMission::test_mission_pause_resume PASSED     [ 52%]
tests/test_mission.py::TestMission::test_mission_plan_strict PASSED      [ 53%]
tests/test_mission.py::TestMission::test_resolve_mission_prefers_active_over_completed PASSED [ 54%]
tests/test_multi_runtime.py::test_planner_prompt_contains_runtime PASSED [ 55%]
tests/test_multi_runtime.py::test_planner_parses_runtime_field PASSED    [ 55%]
tests/test_multi_runtime.py::test_executor_resolves_task_runtime PASSED  [ 56%]
tests/test_packs.py::TestPacks::test_list_packs PASSED                   [ 57%]
tests/test_packs.py::TestPacks::test_add_pack_copies_files PASSED        [ 58%]
tests/test_packs.py::TestPacks::test_add_pack_conflict PASSED            [ 58%]
tests/test_packs.py::TestPacks::test_remove_pack PASSED                  [ 59%]
tests/test_packs.py::TestPacks::test_sync_packs PASSED                   [ 60%]
tests/test_planner_robust.py::test_extract_yaml_or_json_malformed PASSED [ 61%]
tests/test_planner_robust.py::test_fallback_matches_requirement_keywords PASSED [ 61%]
tests/test_planner_robust.py::test_validation_commands_injected_from_project_yaml PASSED [ 62%]
tests/test_planner_robust.py::test_planner_retry_on_bad_output PASSED    [ 63%]
tests/test_pr.py::test_pr_review_mocked PASSED                           [ 63%]
tests/test_pr.py::test_pr_create_mocked PASSED                           [ 64%]
tests/test_recovery.py::test_mission_skip_unblocks_downstream FAILED     [ 65%]
tests/test_recovery.py::test_mission_retry_requeues_tasks PASSED         [ 66%]
tests/test_recovery.py::test_mission_rollback_git_checkout PASSED        [ 66%]
tests/test_remediation.py::test_bash_sh_blocked PASSED                   [ 67%]
tests/test_remediation.py::test_report_fails_on_validation_failure PASSED [ 68%]
tests/test_remediation.py::test_context_diff_ignores_manual_sections PASSED [ 69%]
tests/test_remediation.py::test_claude_hook_script_formatting_and_imports PASSED [ 69%]
tests/test_remediation.py::test_validate_mission_plan_cycle PASSED       [ 70%]
tests/test_remediation.py::test_validate_mission_plan_unknown_dependency PASSED [ 71%]
tests/test_remediation.py::test_writes_files_false_violation_and_revert PASSED [ 72%]
tests/test_review.py::TestReview::test_get_git_diff_untracked_file PASSED [ 72%]
tests/test_review.py::TestReview::test_run_review_engineering_lens PASSED [ 73%]
tests/test_review.py::TestReview::test_run_review_adversarial_mode PASSED [ 74%]
tests/test_review.py::TestReview::test_get_git_diff_file_size_limit PASSED [ 75%]
tests/test_review.py::TestReview::test_get_git_diff_budget_limit PASSED  [ 75%]
tests/test_review.py::TestReview::test_get_git_diff_skip_binary_files PASSED [ 76%]
tests/test_review.py::TestReview::test_get_git_diff_redact_secrets PASSED [ 77%]
tests/test_run_composite.py::test_run_composite_command_file PASSED      [ 77%]
tests/test_run_composite.py::test_run_composite_command_inline_string PASSED [ 78%]
tests/test_setup.py::test_setup_wizard_fresh_initialization PASSED       [ 79%]
tests/test_sync.py::TestClaudeSync::test_claude_sync_creates_claude_md PASSED [ 80%]
tests/test_sync.py::TestClaudeSync::test_claude_sync_creates_claude_dir PASSED [ 80%]
tests/test_sync.py::TestClaudeSync::test_claude_sync_creates_agents PASSED [ 81%]
tests/test_sync.py::TestClaudeSync::test_claude_sync_creates_hooks PASSED [ 82%]
tests/test_sync.py::TestClaudeSync::test_claude_sync_creates_settings PASSED [ 83%]
tests/test_sync.py::TestClaudeSync::test_claude_md_contains_policies PASSED [ 83%]
tests/test_sync.py::TestCodexSync::test_codex_sync_creates_agents_md PASSED [ 84%]
tests/test_sync.py::TestCodexSync::test_agents_md_contains_policies PASSED [ 85%]
tests/test_sync.py::TestCodexSync::test_codex_sync_creates_hooks_and_settings PASSED [ 86%]
tests/test_sync.py::TestGeminiSync::test_gemini_sync_creates_gemini_md PASSED [ 86%]
tests/test_sync.py::TestGeminiSync::test_gemini_sync_creates_gemini_dir PASSED [ 87%]
tests/test_sync.py::TestGeminiSync::test_gemini_md_contains_policies PASSED [ 88%]
tests/test_sync.py::TestGeminiSync::test_gemini_sync_creates_hooks_and_settings PASSED [ 88%]
tests/test_sync.py::TestRuntimeAdd::test_runtime_add_updates_config PASSED [ 89%]
tests/test_sync.py::TestRuntimeAdd::test_runtime_add_duplicate_is_safe PASSED [ 90%]
tests/test_template_boilerplating.py::test_template_boilerplating_on_refresh PASSED [ 91%]
tests/test_templates.py::test_builtin_template_planning PASSED           [ 91%]
tests/test_templates.py::test_custom_template_planning PASSED            [ 92%]
tests/test_token_parsing.py::test_parse_claude_cli_output PASSED         [ 93%]
tests/test_token_parsing.py::test_parse_gemini_cli_output PASSED         [ 94%]
tests/test_token_parsing.py::test_parse_codex_cli_output PASSED          [ 94%]
tests/test_token_parsing.py::test_parse_unknown_format_returns_none PASSED [ 95%]
tests/test_token_parsing.py::test_ledger_labels_estimates_honestly PASSED [ 96%]
tests/test_token_parsing.py::test_ledger_uses_real_values_when_available PASSED [ 97%]
tests/test_token_parsing.py::test_baseline_multiplier_opt_in PASSED      [ 97%]
tests/test_utils.py::test_format_date_iso_utc PASSED                     [ 98%]
tests/test_utils.py::test_format_date_iso_naive PASSED                   [ 99%]
tests/test_verification.py::test_verification_lifecycle PASSED           [100%]

=================================== FAILURES ===================================
____________________ test_mission_skip_unblocks_downstream _____________________
/Users/bhushan/Documents/Projects/niyam/.niyam/runs/add-info-cmd-20260531-143733/worktrees/T1/tests/test_recovery.py:56: in test_mission_skip_unblocks_downstream
    assert plan["tasks"][1]["status"] == "completed"
E   AssertionError: assert 'skipped' == 'completed'
E     
E     - completed
E     + skipped
----------------------------- Captured stdout call -----------------------------
[main (root-commit) 9aae69e] Initial commit
 30 files changed, 635 insertions(+)
 create mode 100644 .niyam/agents/backend-specialist.md
 create mode 100644 .niyam/agents/frontend-specialist.md
 create mode 100644 .niyam/agents/qa-reviewer.md
 create mode 100644 .niyam/agents/security-reviewer.md
 create mode 100644 .niyam/commands/context-refresh.md
 create mode 100644 .niyam/commands/implement.md
 create mode 100644 .niyam/commands/review.md
 create mode 100644 .niyam/commands/ship.md
 create mode 100644 .niyam/context/architecture.md
 create mode 100644 .niyam/context/commands.md
 create mode 100644 .niyam/context/project-memory.md
 create mode 100644 .niyam/context/validation.md
 create mode 100644 .niyam/memory/architecture-decisions.md
 create mode 100644 .niyam/memory/design-taste.md
 create mode 100644 .niyam/memory/project-lessons.md
 create mode 100644 .niyam/memory/recurring-pitfalls.md
 create mode 100644 .niyam/policies/approvals.yaml
 create mode 100644 .niyam/policies/commands.yaml
 create mode 100644 .niyam/policies/evidence.yaml
 create mode 100644 .niyam/policies/security.yaml
 create mode 100644 .niyam/project.yaml
 create mode 100644 .niyam/runtimes.yaml
 create mode 100644 .niyam/skills/implementation-planning/SKILL.md
 create mode 100644 .niyam/skills/repo-context/SKILL.md
 create mode 100644 .niyam/skills/secure-code-review/SKILL.md
 create mode 100644 .niyam/skills/test-driven-development/SKILL.md
 create mode 100644 .niyam/niyam.yaml
 create mode 100644 .niyam/templates/missions/api-endpoint.yaml
 create mode 100644 .niyam/templates/missions/bugfix.yaml
 create mode 100644 .niyam/templates/missions/refactor.yaml
=========================== short test summary info ============================
FAILED tests/test_recovery.py::test_mission_skip_unblocks_downstream - Assert...
======================== 1 failed, 135 passed in 14.09s ========================

```

## Validation Run - 2026-05-31T10:37:37.413001Z
**Command:** `ruff format --check .`
**Exit Code:** `1`

### stdout
```
Would reformat: niyam/mission/executor.py
Would reformat: tests/test_doctor_check.py
2 files would be reformatted, 82 files already formatted

```

## Validation Run - 2026-05-31T10:37:37.439003Z
**Command:** `ruff check .`
**Exit Code:** `0`

### stdout
```
All checks passed!

```

## Validation Check - typecheck - 2026-05-31T10:37:37.439192Z
**Status:** ℹ SKIPPED — Not configured


## Validation Check - build - 2026-05-31T10:37:37.439255Z
**Status:** ℹ SKIPPED — Not configured


## Validation Run - 2026-05-31T10:37:52.514196Z
**Command:** `pytest`
**Exit Code:** `1`

### stdout
```
============================= test session starts ==============================
platform darwin -- Python 3.14.3, pytest-9.0.3, pluggy-1.6.0 -- /opt/homebrew/opt/python@3.14/bin/python3.14
cachedir: .pytest_cache
rootdir: /Users/bhushan/Documents/Projects/niyam/.niyam/runs/add-info-cmd-20260531-143733/worktrees/T1
configfile: pyproject.toml
testpaths: tests
plugins: cov-7.1.0, pytest_tmp_files-0.0.2, anyio-4.13.0
collecting ... collected 136 items

tests/test_ci.py::test_non_interactive_fails_unapproved PASSED           [  0%]
tests/test_ci.py::test_non_interactive_auto_approve PASSED               [  1%]
tests/test_ci.py::test_remote_policy_fetching PASSED                     [  2%]
tests/test_ci.py::test_remote_policy_fallback PASSED                     [  2%]
tests/test_ci.py::test_ci_verify_strict_missing_evidence PASSED          [  3%]
tests/test_ci.py::test_ci_verify_non_strict_missing_evidence PASSED      [  4%]
tests/test_ci.py::test_ci_verify_write_violation PASSED                  [  5%]
tests/test_cli.py::TestCLI::test_version PASSED                          [  5%]
tests/test_cli.py::TestCLI::test_help PASSED                             [  6%]
tests/test_cli.py::TestCLI::test_update_help PASSED                      [  7%]
tests/test_cli.py::TestCLI::test_start_help PASSED                       [  8%]
tests/test_cli.py::TestCLI::test_next_help PASSED                        [  8%]
tests/test_cli.py::TestCLI::test_context_help PASSED                     [  9%]
tests/test_cli.py::TestCLI::test_guard_help PASSED                       [ 10%]
tests/test_cli.py::TestCLI::test_runtime_help PASSED                     [ 11%]
tests/test_cli.py::TestCLI::test_policy_help PASSED                      [ 11%]
tests/test_cli_refinement.py::test_interactive_refiner_loop PASSED       [ 12%]
tests/test_compare.py::test_comparison_runs_multiple_executors PASSED    [ 13%]
tests/test_compare.py::test_compare_cli_command PASSED                   [ 13%]
tests/test_context.py::TestContextRefresh::test_context_refresh_creates_architecture PASSED [ 14%]
tests/test_context.py::TestContextRefresh::test_context_refresh_creates_validation PASSED [ 15%]
tests/test_context.py::TestContextRefresh::test_context_refresh_detects_python PASSED [ 16%]
tests/test_context.py::TestContextRefresh::test_context_refresh_detects_node PASSED [ 16%]
tests/test_context.py::TestContextRefresh::test_context_refresh_preserves_manual_section PASSED [ 17%]
tests/test_contract_enforcement.py::test_any_bypass_removed_and_contract_prompt_enrichment PASSED [ 18%]
tests/test_dashboard.py::test_dashboard_rendering PASSED                 [ 19%]
tests/test_dashboard.py::test_dashboard_watch_mode PASSED                [ 19%]
tests/test_doctor.py::TestDoctor::test_doctor_passes_on_fresh_init PASSED [ 20%]
tests/test_doctor.py::TestDoctor::test_doctor_fails_without_niyam PASSED [ 21%]
tests/test_doctor.py::TestDoctor::test_doctor_detects_missing_files PASSED [ 22%]
tests/test_doctor.py::TestDoctor::test_doctor_detects_invalid_yaml PASSED [ 22%]
tests/test_doctor_check.py::test_doctor_check_lint_format_success PASSED [ 23%]
tests/test_doctor_check.py::test_doctor_check_lint_format_failure PASSED [ 24%]
tests/test_doctor_enhanced.py::test_doctor_runtimes_in_path PASSED       [ 25%]
tests/test_doctor_enhanced.py::test_doctor_agents_validity PASSED        [ 25%]
tests/test_doctor_enhanced.py::test_doctor_validation_commands PASSED    [ 26%]
tests/test_doctor_enhanced.py::test_doctor_git_status_dirty PASSED       [ 27%]
tests/test_doctor_enhanced.py::test_doctor_smoke_tests PASSED            [ 27%]
tests/test_fleet.py::test_fleet_parallel_execution PASSED                [ 28%]
tests/test_fleet.py::test_fleet_dependency_failure PASSED                [ 29%]
tests/test_fleet.py::test_fleet_worktree_fallback_when_no_git PASSED     [ 30%]
tests/test_guard.py::TestGuard::test_guard_enable PASSED                 [ 30%]
tests/test_guard.py::TestGuard::test_guard_disable PASSED                [ 31%]
tests/test_guard.py::TestGuard::test_guard_careful_adds_warn_list PASSED [ 32%]
tests/test_guard.py::TestGuard::test_guard_freeze_adds_path PASSED       [ 33%]
tests/test_guard.py::TestGuard::test_guard_freeze_enables_guard PASSED   [ 33%]
tests/test_guardrails.py::test_path_write_denial_and_revert PASSED       [ 34%]
tests/test_hello.py::test_hello_no_args PASSED                           [ 35%]
tests/test_hello.py::test_hello_with_name PASSED                         [ 36%]
tests/test_hooks.py::test_hooks_lifecycle_triggers PASSED                [ 36%]
tests/test_init.py::TestInit::test_init_creates_niyam_directory PASSED   [ 37%]
tests/test_init.py::TestInit::test_init_creates_mvp_directories PASSED   [ 38%]
tests/test_init.py::TestInit::test_init_creates_niyam_yaml PASSED        [ 38%]
tests/test_init.py::TestInit::test_init_creates_agents PASSED            [ 39%]
tests/test_init.py::TestInit::test_init_creates_skills PASSED            [ 40%]
tests/test_init.py::TestInit::test_init_creates_commands PASSED          [ 41%]
tests/test_init.py::TestInit::test_init_creates_policies PASSED          [ 41%]
tests/test_init.py::TestInit::test_init_fails_if_already_exists PASSED   [ 42%]
tests/test_init.py::TestInit::test_init_force_overwrites PASSED          [ 43%]
tests/test_init.py::TestInit::test_init_dry_run_creates_nothing PASSED   [ 44%]
tests/test_init.py::TestInit::test_init_with_claude_runtime PASSED       [ 44%]
tests/test_init.py::TestInit::test_init_invalid_profile_fails PASSED     [ 45%]
tests/test_init.py::TestInit::test_init_backend_profile PASSED           [ 46%]
tests/test_init.py::TestInit::test_init_frontend_profile PASSED          [ 47%]
tests/test_memory.py::TestMemory::test_memory_show PASSED                [ 47%]
tests/test_memory.py::TestMemory::test_memory_add PASSED                 [ 48%]
tests/test_memory.py::TestMemory::test_memory_clear PASSED               [ 49%]
tests/test_memory.py::TestMemory::test_memory_sync_propagates_to_runtimes PASSED [ 50%]
tests/test_mission.py::TestMission::test_mission_plan_creates_files PASSED [ 50%]
tests/test_mission.py::TestMission::test_mission_approve PASSED          [ 51%]
tests/test_mission.py::TestMission::test_mission_execution_lifecycle PASSED [ 52%]
tests/test_mission.py::TestMission::test_mission_pause_resume PASSED     [ 52%]
tests/test_mission.py::TestMission::test_mission_plan_strict PASSED      [ 53%]
tests/test_mission.py::TestMission::test_resolve_mission_prefers_active_over_completed PASSED [ 54%]
tests/test_multi_runtime.py::test_planner_prompt_contains_runtime PASSED [ 55%]
tests/test_multi_runtime.py::test_planner_parses_runtime_field PASSED    [ 55%]
tests/test_multi_runtime.py::test_executor_resolves_task_runtime PASSED  [ 56%]
tests/test_packs.py::TestPacks::test_list_packs PASSED                   [ 57%]
tests/test_packs.py::TestPacks::test_add_pack_copies_files PASSED        [ 58%]
tests/test_packs.py::TestPacks::test_add_pack_conflict PASSED            [ 58%]
tests/test_packs.py::TestPacks::test_remove_pack PASSED                  [ 59%]
tests/test_packs.py::TestPacks::test_sync_packs PASSED                   [ 60%]
tests/test_planner_robust.py::test_extract_yaml_or_json_malformed PASSED [ 61%]
tests/test_planner_robust.py::test_fallback_matches_requirement_keywords PASSED [ 61%]
tests/test_planner_robust.py::test_validation_commands_injected_from_project_yaml PASSED [ 62%]
tests/test_planner_robust.py::test_planner_retry_on_bad_output PASSED    [ 63%]
tests/test_pr.py::test_pr_review_mocked PASSED                           [ 63%]
tests/test_pr.py::test_pr_create_mocked PASSED                           [ 64%]
tests/test_recovery.py::test_mission_skip_unblocks_downstream FAILED     [ 65%]
tests/test_recovery.py::test_mission_retry_requeues_tasks PASSED         [ 66%]
tests/test_recovery.py::test_mission_rollback_git_checkout PASSED        [ 66%]
tests/test_remediation.py::test_bash_sh_blocked PASSED                   [ 67%]
tests/test_remediation.py::test_report_fails_on_validation_failure PASSED [ 68%]
tests/test_remediation.py::test_context_diff_ignores_manual_sections PASSED [ 69%]
tests/test_remediation.py::test_claude_hook_script_formatting_and_imports PASSED [ 69%]
tests/test_remediation.py::test_validate_mission_plan_cycle PASSED       [ 70%]
tests/test_remediation.py::test_validate_mission_plan_unknown_dependency PASSED [ 71%]
tests/test_remediation.py::test_writes_files_false_violation_and_revert PASSED [ 72%]
tests/test_review.py::TestReview::test_get_git_diff_untracked_file PASSED [ 72%]
tests/test_review.py::TestReview::test_run_review_engineering_lens PASSED [ 73%]
tests/test_review.py::TestReview::test_run_review_adversarial_mode PASSED [ 74%]
tests/test_review.py::TestReview::test_get_git_diff_file_size_limit PASSED [ 75%]
tests/test_review.py::TestReview::test_get_git_diff_budget_limit PASSED  [ 75%]
tests/test_review.py::TestReview::test_get_git_diff_skip_binary_files PASSED [ 76%]
tests/test_review.py::TestReview::test_get_git_diff_redact_secrets PASSED [ 77%]
tests/test_run_composite.py::test_run_composite_command_file PASSED      [ 77%]
tests/test_run_composite.py::test_run_composite_command_inline_string PASSED [ 78%]
tests/test_setup.py::test_setup_wizard_fresh_initialization PASSED       [ 79%]
tests/test_sync.py::TestClaudeSync::test_claude_sync_creates_claude_md PASSED [ 80%]
tests/test_sync.py::TestClaudeSync::test_claude_sync_creates_claude_dir PASSED [ 80%]
tests/test_sync.py::TestClaudeSync::test_claude_sync_creates_agents PASSED [ 81%]
tests/test_sync.py::TestClaudeSync::test_claude_sync_creates_hooks PASSED [ 82%]
tests/test_sync.py::TestClaudeSync::test_claude_sync_creates_settings PASSED [ 83%]
tests/test_sync.py::TestClaudeSync::test_claude_md_contains_policies PASSED [ 83%]
tests/test_sync.py::TestCodexSync::test_codex_sync_creates_agents_md PASSED [ 84%]
tests/test_sync.py::TestCodexSync::test_agents_md_contains_policies PASSED [ 85%]
tests/test_sync.py::TestCodexSync::test_codex_sync_creates_hooks_and_settings PASSED [ 86%]
tests/test_sync.py::TestGeminiSync::test_gemini_sync_creates_gemini_md PASSED [ 86%]
tests/test_sync.py::TestGeminiSync::test_gemini_sync_creates_gemini_dir PASSED [ 87%]
tests/test_sync.py::TestGeminiSync::test_gemini_md_contains_policies PASSED [ 88%]
tests/test_sync.py::TestGeminiSync::test_gemini_sync_creates_hooks_and_settings PASSED [ 88%]
tests/test_sync.py::TestRuntimeAdd::test_runtime_add_updates_config PASSED [ 89%]
tests/test_sync.py::TestRuntimeAdd::test_runtime_add_duplicate_is_safe PASSED [ 90%]
tests/test_template_boilerplating.py::test_template_boilerplating_on_refresh PASSED [ 91%]
tests/test_templates.py::test_builtin_template_planning PASSED           [ 91%]
tests/test_templates.py::test_custom_template_planning PASSED            [ 92%]
tests/test_token_parsing.py::test_parse_claude_cli_output PASSED         [ 93%]
tests/test_token_parsing.py::test_parse_gemini_cli_output PASSED         [ 94%]
tests/test_token_parsing.py::test_parse_codex_cli_output PASSED          [ 94%]
tests/test_token_parsing.py::test_parse_unknown_format_returns_none PASSED [ 95%]
tests/test_token_parsing.py::test_ledger_labels_estimates_honestly PASSED [ 96%]
tests/test_token_parsing.py::test_ledger_uses_real_values_when_available PASSED [ 97%]
tests/test_token_parsing.py::test_baseline_multiplier_opt_in PASSED      [ 97%]
tests/test_utils.py::test_format_date_iso_utc PASSED                     [ 98%]
tests/test_utils.py::test_format_date_iso_naive PASSED                   [ 99%]
tests/test_verification.py::test_verification_lifecycle PASSED           [100%]

=================================== FAILURES ===================================
____________________ test_mission_skip_unblocks_downstream _____________________
/Users/bhushan/Documents/Projects/niyam/.niyam/runs/add-info-cmd-20260531-143733/worktrees/T1/tests/test_recovery.py:56: in test_mission_skip_unblocks_downstream
    assert plan["tasks"][1]["status"] == "completed"
E   AssertionError: assert 'skipped' == 'completed'
E     
E     - completed
E     + skipped
----------------------------- Captured stdout call -----------------------------
[main (root-commit) 5cbb407] Initial commit
 30 files changed, 635 insertions(+)
 create mode 100644 .niyam/agents/backend-specialist.md
 create mode 100644 .niyam/agents/frontend-specialist.md
 create mode 100644 .niyam/agents/qa-reviewer.md
 create mode 100644 .niyam/agents/security-reviewer.md
 create mode 100644 .niyam/commands/context-refresh.md
 create mode 100644 .niyam/commands/implement.md
 create mode 100644 .niyam/commands/review.md
 create mode 100644 .niyam/commands/ship.md
 create mode 100644 .niyam/context/architecture.md
 create mode 100644 .niyam/context/commands.md
 create mode 100644 .niyam/context/project-memory.md
 create mode 100644 .niyam/context/validation.md
 create mode 100644 .niyam/memory/architecture-decisions.md
 create mode 100644 .niyam/memory/design-taste.md
 create mode 100644 .niyam/memory/project-lessons.md
 create mode 100644 .niyam/memory/recurring-pitfalls.md
 create mode 100644 .niyam/policies/approvals.yaml
 create mode 100644 .niyam/policies/commands.yaml
 create mode 100644 .niyam/policies/evidence.yaml
 create mode 100644 .niyam/policies/security.yaml
 create mode 100644 .niyam/project.yaml
 create mode 100644 .niyam/runtimes.yaml
 create mode 100644 .niyam/skills/implementation-planning/SKILL.md
 create mode 100644 .niyam/skills/repo-context/SKILL.md
 create mode 100644 .niyam/skills/secure-code-review/SKILL.md
 create mode 100644 .niyam/skills/test-driven-development/SKILL.md
 create mode 100644 .niyam/niyam.yaml
 create mode 100644 .niyam/templates/missions/api-endpoint.yaml
 create mode 100644 .niyam/templates/missions/bugfix.yaml
 create mode 100644 .niyam/templates/missions/refactor.yaml
=========================== short test summary info ============================
FAILED tests/test_recovery.py::test_mission_skip_unblocks_downstream - Assert...
======================== 1 failed, 135 passed in 13.93s ========================

```
