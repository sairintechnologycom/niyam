"""Tests for the enhanced diagnostics in sutra doctor."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from rich.console import Console

from sutra.core.doctor import (
    run_doctor,
    _check_runtimes_in_path,
    _check_agents_validity,
    _check_validation_commands_in_path,
    _check_git_status,
)
from sutra.core.config import load_sutra_config


def test_doctor_runtimes_in_path(sutra_repo: Path) -> None:
    """Should correctly report when runtimes are missing or present in PATH."""
    config = load_sutra_config(sutra_repo)
    config.runtimes = ["claude", "gemini"]

    def mock_which(cmd):
        if cmd == "claude":
            return "/usr/local/bin/claude"
        return None

    with patch("shutil.which", side_effect=mock_which):
        results = _check_runtimes_in_path(sutra_repo, config)
        
    assert len(results) == 2
    
    # claude is present
    assert results[0].name == "Runtime in PATH: claude"
    assert results[0].passed is True
    
    # gemini is missing
    assert results[1].name == "Runtime in PATH: gemini"
    assert results[1].passed is False
    assert results[1].severity == "warning"


def test_doctor_agents_validity(sutra_repo: Path) -> None:
    """Should detect empty or invalid agent persona files."""
    # Write an empty agent file
    empty_agent = sutra_repo / ".sutra" / "agents" / "empty-agent.md"
    empty_agent.write_text("   \n  ", encoding="utf-8")

    results = _check_agents_validity(sutra_repo)
    
    # Verify warning generated for empty-agent
    empty_agent_results = [r for r in results if "empty-agent" in r.name]
    assert len(empty_agent_results) == 1
    assert empty_agent_results[0].passed is False
    assert empty_agent_results[0].severity == "warning"


def test_doctor_validation_commands(sutra_repo: Path) -> None:
    """Should check validation commands' binaries existence in PATH."""
    # Write a test project.yaml with a missing validation command
    project_yaml = sutra_repo / ".sutra" / "project.yaml"
    project_data = {
        "name": "test-project",
        "validation": {
            "test": "pytest",
            "lint": "nonexistent-linter --verbose"
        }
    }
    import yaml
    with open(project_yaml, "w", encoding="utf-8") as f:
        yaml.safe_dump(project_data, f)

    def mock_which(cmd):
        if cmd == "pytest":
            return "/usr/local/bin/pytest"
        return None

    with patch("shutil.which", side_effect=mock_which):
        results = _check_validation_commands_in_path(sutra_repo)

    # pytest should pass, nonexistent-linter should fail
    pytest_results = [r for r in results if "test command" in r.name]
    assert len(pytest_results) == 1
    assert pytest_results[0].passed is True

    lint_results = [r for r in results if "lint command" in r.name]
    assert len(lint_results) == 1
    assert lint_results[0].passed is False
    assert lint_results[0].severity == "warning"


def test_doctor_git_status_dirty(sutra_repo: Path) -> None:
    """Should report warning if uncommitted changes are present in the Git repository."""
    os.chdir(sutra_repo)

    # Initial commit so HEAD exists
    os.system("git add . && git commit -m 'Initial commit'")

    # Create uncommitted file to dirty the git repo
    dirty_file = sutra_repo / "dirty.txt"
    dirty_file.write_text("dirty content", encoding="utf-8")

    results = _check_git_status(sutra_repo)
    
    # Verify Git Status check fails or warns
    git_status_results = [r for r in results if "Git Status" in r.name]
    assert len(git_status_results) == 1
    assert git_status_results[0].passed is False
    assert git_status_results[0].severity == "warning"
