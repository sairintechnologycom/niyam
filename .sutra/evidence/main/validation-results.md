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

