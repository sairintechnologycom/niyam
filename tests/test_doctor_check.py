"""Tests for the linter checking functionality in niyam doctor."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import yaml

from niyam.core.doctor import _check_lint_format
from niyam.core.config import get_niyam_dir


def test_doctor_check_lint_format_success(niyam_repo: Path) -> None:
    os.chdir(niyam_repo)

    # 1. Configure lint and format commands in project.yaml
    project_yaml = get_niyam_dir(niyam_repo) / "project.yaml"
    with open(project_yaml, "r", encoding="utf-8") as f:
        proj_data = yaml.safe_load(f) or {}

    proj_data["validation"] = {
        "lint": "mock-linter --check",
        "format": "mock-formatter --check",
    }

    with open(project_yaml, "w", encoding="utf-8") as f:
        yaml.safe_dump(proj_data, f)

    # 2. Mock successful execution
    mock_res = MagicMock()
    mock_res.returncode = 0
    mock_res.stdout = "All clean"
    mock_res.stderr = ""

    with patch(
        "niyam.core.security.safe_run_command", return_value=mock_res
    ) as mock_run:
        results = _check_lint_format(niyam_repo)

    assert len(results) == 2
    assert results[0].passed is True
    assert "Passed" in results[0].message
    assert results[1].passed is True
    assert "Passed" in results[1].message

    # Verify mock commands were run
    assert mock_run.call_count == 2
    mock_run.assert_any_call("mock-linter --check", cwd=niyam_repo, timeout=60)
    mock_run.assert_any_call("mock-formatter --check", cwd=niyam_repo, timeout=60)


def test_doctor_check_lint_format_failure(niyam_repo: Path) -> None:
    os.chdir(niyam_repo)

    # 1. Configure lint and format commands in project.yaml
    project_yaml = get_niyam_dir(niyam_repo) / "project.yaml"
    with open(project_yaml, "r", encoding="utf-8") as f:
        proj_data = yaml.safe_load(f) or {}

    proj_data["validation"] = {
        "lint": "mock-linter --check",
    }

    with open(project_yaml, "w", encoding="utf-8") as f:
        yaml.safe_dump(proj_data, f)

    # 2. Mock failed execution
    mock_res = MagicMock()
    mock_res.returncode = 1
    mock_res.stdout = ""
    mock_res.stderr = "Linter syntax error on line 4"

    with patch(
        "niyam.core.security.safe_run_command", return_value=mock_res
    ):
        results = _check_lint_format(niyam_repo)

    assert len(results) == 1
    assert results[0].passed is False
    assert "Failed" in results[0].message
    assert "Linter syntax error" in results[0].message
