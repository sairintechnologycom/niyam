# Testing Patterns

**Analysis Date:** 2024-05-23

## Test Framework

**Runner:**
- pytest 8.x
- Config: `pyproject.toml` ([tool.pytest.ini_options])

**Assertion Library:**
- Standard `assert` statements.

**Run Commands:**
```bash
pytest                 # Run all tests
pytest -v              # Verbose mode
pytest --cov=niyam     # Coverage (requires pytest-cov)
```

## Test File Organization

**Location:**
- Separate `tests/` directory at the project root.

**Naming:**
- Files: `test_*.py` (e.g., `tests/test_cli.py`).
- Classes: `Test*` (e.g., `class TestCLI`).
- Methods: `test_*` (e.g., `def test_version`).

**Structure:**
```
tests/
├── conftest.py       # Shared fixtures
├── test_cli.py       # CLI command tests
├── test_core.py      # Core logic tests
└── ...
```

## Test Structure

**Suite Organization:**
```python
class TestFeature:
    """Description of the feature being tested."""

    def test_specific_behavior(self) -> None:
        """Explain what this test verifies."""
        # setup (fixtures, state)
        # execute (function call, CLI command)
        # assert (check results)
```

**Patterns:**
- **Setup pattern**: Extensive use of pytest fixtures in `tests/conftest.py`.
- **Teardown pattern**: Pytest handles cleanup of `tmp_path`. Manual cleanup in `finally` blocks for directory changes (`os.chdir`).
- **Assertion pattern**: Checking exit codes, presence of specific strings in `result.output`, and verifying side effects on the filesystem.

## Mocking

**Framework:** `unittest.mock`

**Patterns:**
```python
from unittest.mock import patch, MagicMock

def test_feature(niyam_repo: Path):
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        # Call function that uses subprocess
        mock_run.assert_called()
```

**What to Mock:**
- External CLI calls (`subprocess.run`).
- Network requests (`urllib.request.urlopen`).
- File system side effects in unit tests to avoid polluting the workspace.
- Interaction with `rich.console.Console` to suppress or verify output.

**What NOT to Mock:**
- Core business logic.
- Pydantic models and basic data structures.

## Fixtures and Factories

**Test Data:**
```python
@pytest.fixture
def tmp_repo(tmp_path: Path) -> Path:
    """Create a temporary directory simulating a git repo."""
    os.system(f"cd {tmp_path} && git init -q")
    return tmp_path

@pytest.fixture
def niyam_repo(tmp_repo: Path) -> Path:
    """Create a temporary repo with niyam initialized."""
    # ... calls run_init ...
    return tmp_repo
```

**Location:**
- Shared fixtures: `tests/conftest.py`.
- Local fixtures: Defined within specific test files for specialized setup.

## Coverage

**Requirements:** `pytest-cov` is listed as a dev dependency in `pyproject.toml`.

**View Coverage:**
```bash
pytest --cov=niyam
```

## Test Types

**Unit Tests:**
- Testing individual functions and classes in isolation (e.g., exceptions, config parsing).

**Integration Tests:**
- Testing CLI commands and their interaction with the filesystem (e.g., `tests/test_cli.py`, `tests/test_init.py`).
- Use `niyam_repo` fixture to test against a real initialized workspace on disk.

**E2E Tests:**
- CLI invocation tests using `typer.testing.CliRunner`.

## Common Patterns

**Async Testing:** Not detected; the codebase is synchronous.

**Error Testing:**
```python
import pytest
from niyam.core.errors import NiyamError

def test_failure():
    with pytest.raises(NiyamError):
        do_something_invalid()
```

---

*Testing analysis: 2024-05-23*
