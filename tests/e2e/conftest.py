"""E2E pytest configuration and helpers."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

# Base paths
E2E_DIR = Path(__file__).parent
FIXTURES_DIR = E2E_DIR / "fixtures"
PROJECT_ROOT = E2E_DIR.parent.parent


@pytest.fixture(scope="session")
def mock_bin_dir() -> Path:
    """Create a temporary directory with mocked binaries."""
    temp_dir = Path(tempfile.mkdtemp(prefix="niyam_mock_bin_"))

    # Write mock checkov script
    checkov_path = temp_dir / "checkov"
    checkov_script = """#!/usr/bin/env python3
import sys
import json
import os

if "--output" in sys.argv and "json" in sys.argv:
    if os.path.exists("main.tf"):
        report = {
            "results": {
                "failed_checks": [
                    {
                        "check_id": "CKV_AWS_20",
                        "check_name": "Ensure S3 bucket is not publicly accessible",
                        "file_path": "main.tf",
                        "severity": "HIGH",
                        "file_line_range": [2, 3]
                    }
                ]
            }
        }
        print(json.dumps(report))
    else:
        print(json.dumps({"results": {"failed_checks": []}}))
else:
    print(json.dumps({"results": {"failed_checks": []}}))
"""
    checkov_path.write_text(checkov_script, encoding="utf-8")
    checkov_path.chmod(0o755)

    # Write mock gitleaks script (return empty leaks)
    gitleaks_path = temp_dir / "gitleaks"
    gitleaks_script = """#!/usr/bin/env python3
import sys
import json
print(json.dumps([]))
"""
    gitleaks_path.write_text(gitleaks_script, encoding="utf-8")
    gitleaks_path.chmod(0o755)

    # Write mock semgrep script (return empty results)
    semgrep_path = temp_dir / "semgrep"
    semgrep_script = """#!/usr/bin/env python3
import sys
import json
print(json.dumps({"results": []}))
"""
    semgrep_path.write_text(semgrep_script, encoding="utf-8")
    semgrep_path.chmod(0o755)

    # Write mock trivy script (return empty Results)
    trivy_path = temp_dir / "trivy"
    trivy_script = """#!/usr/bin/env python3
import sys
import json
print(json.dumps({"Results": []}))
"""
    trivy_path.write_text(trivy_script, encoding="utf-8")
    trivy_path.chmod(0o755)

    yield temp_dir

    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def run_cli(mock_bin_dir: Path):
    """Fixture returning the run_cli function."""

    def _run_cli(
        command: list[str], cwd: Path | str, timeout: int = 30
    ) -> subprocess.CompletedProcess:
        # Prepend the mock bin directory to PATH so mock checkov/gitleaks run
        env = os.environ.copy()
        env["PATH"] = os.path.pathsep.join([str(mock_bin_dir), env.get("PATH", "")])
        # Force offline/test flags
        env["NIYAM_TEST"] = "1"
        env["NIYAM_TEST_NON_INTERACTIVE"] = "1"
        # Avoid picking up global/local user configs outside the test workspace
        env["NIYAM_SESSION_ID"] = "e2e-session"

        # Build command: use python interpreter to run niyam main module
        if command and command[0] == "niyam":
            full_command = [sys.executable, "-m", "niyam"] + command[1:]
        else:
            full_command = [sys.executable, "-m", "niyam"] + command

        return subprocess.run(
            full_command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )

    return _run_cli


@pytest.fixture
def clean_workspace(tmp_path: Path) -> Path:
    """Fixture that copies clean_app files to a temp workspace and initializes git."""
    fixture_dir = FIXTURES_DIR / "clean_app"
    shutil.copytree(fixture_dir, tmp_path, dirs_exist_ok=True)

    # Initialize a git repo to satisfy git log/metadata functions
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "config", "user.email", "e2e@niyam.com"], cwd=tmp_path, check=True
    )
    subprocess.run(
        ["git", "config", "user.name", "Niyam E2E"], cwd=tmp_path, check=True
    )
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit", "-q"], cwd=tmp_path, check=True
    )

    return tmp_path


@pytest.fixture
def risky_workspace(tmp_path: Path) -> Path:
    """Fixture that copies risky_app files to a temp workspace and initializes git."""
    fixture_dir = FIXTURES_DIR / "risky_app"
    shutil.copytree(fixture_dir, tmp_path, dirs_exist_ok=True)

    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "config", "user.email", "e2e@niyam.com"], cwd=tmp_path, check=True
    )
    subprocess.run(
        ["git", "config", "user.name", "Niyam E2E"], cwd=tmp_path, check=True
    )
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    # Commit files (Note: some checks warn if files are untracked)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit", "-q"], cwd=tmp_path, check=True
    )

    return tmp_path


@pytest.fixture
def ai_workspace(tmp_path: Path) -> Path:
    """Fixture that copies ai_app files to a temp workspace and initializes git."""
    fixture_dir = FIXTURES_DIR / "ai_app"
    shutil.copytree(fixture_dir, tmp_path, dirs_exist_ok=True)

    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "config", "user.email", "e2e@niyam.com"], cwd=tmp_path, check=True
    )
    subprocess.run(
        ["git", "config", "user.name", "Niyam E2E"], cwd=tmp_path, check=True
    )
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit", "-q"], cwd=tmp_path, check=True
    )

    return tmp_path


@pytest.fixture
def iac_workspace(tmp_path: Path) -> Path:
    """Fixture that copies iac_app files to a temp workspace and initializes git."""
    fixture_dir = FIXTURES_DIR / "iac_app"
    shutil.copytree(fixture_dir, tmp_path, dirs_exist_ok=True)

    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "config", "user.email", "e2e@niyam.com"], cwd=tmp_path, check=True
    )
    subprocess.run(
        ["git", "config", "user.name", "Niyam E2E"], cwd=tmp_path, check=True
    )
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit", "-q"], cwd=tmp_path, check=True
    )

    return tmp_path
