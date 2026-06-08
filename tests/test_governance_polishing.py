"""Tests for polished governance features (streaming redaction, git hooks, MCP refinement)."""

import json
import os
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from rich.console import Console

from niyam.policies.guard import (
    run_guard_run,
    run_guard_enable,
    run_guard_disable,
    run_guard_verify_commit,
    _install_git_hooks,
    _uninstall_git_hooks,
)
from niyam.core.mcp import MCPTool, MCPRegistry, save_mcp_registry


@pytest.fixture
def repo_root(tmp_path):
    """Setup a temporary repo root with .niyam and .git."""
    niyam_dir = tmp_path / ".niyam"
    niyam_dir.mkdir()
    (niyam_dir / "policies").mkdir()
    (niyam_dir / "logs").mkdir()
    
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    (git_dir / "hooks").mkdir()
    
    # Create a basic config
    config_path = tmp_path / "niyam.yaml"
    config_path.write_text("guard:\n  enabled: false\n  frozen_paths: []\n")
    
    return tmp_path


def test_streaming_redaction(repo_root, capsys):
    """Test that secrets are redacted in real-time as they stream."""
    # Mock redact_text to verify it's called
    with patch("niyam.policies.guard.redact_text") as mock_redact:
        mock_redact.side_effect = lambda x: x.replace("SECRET_TOKEN", "[REDACTED]")
        
        # We need a command that prints a secret
        # In a real environment, we'd use echo, but let's mock subprocess.Popen for stability
        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.stdout.readline.side_effect = ["This is a SECRET_TOKEN\n", ""]
            mock_process.stderr.readline.side_effect = [""]
            mock_process.poll.side_effect = [None, 0]
            mock_process.returncode = 0
            mock_popen.return_value = mock_process
            
            # Mock selectors
            with patch("selectors.DefaultSelector") as mock_selector_cls:
                mock_sel = MagicMock()
                # Simulate one read event for stdout
                key = MagicMock()
                key.fileobj = mock_process.stdout
                mock_sel.select.side_effect = [[(key, None)], []]
                mock_selector_cls.return_value = mock_sel
                
                with pytest.raises(SystemExit):
                    run_guard_run(
                        cmd_args=["echo", "secret"],
                        capture_output=True,
                        console=Console(),
                    )
    
    out, err = capsys.readouterr()
    assert "[REDACTED]" in out
    assert "SECRET_TOKEN" not in out


def test_git_hook_lifecycle(repo_root):
    """Test installation and removal of git hooks."""
    console = Console()
    
    # 1. Install
    _install_git_hooks(repo_root, console)
    pre_commit_path = repo_root / ".git" / "hooks" / "pre_commit"
    assert pre_commit_path.exists()
    assert "niyam guard verify-commit" in pre_commit_path.read_text()
    
    # 2. Uninstall
    _uninstall_git_hooks(repo_root, console)
    assert not pre_commit_path.exists()


def test_verify_commit_blocks_frozen_paths(repo_root, capsys):
    """Test that verify-commit blocks commits to frozen paths."""
    console = Console()
    
    # Setup config with frozen path
    niyam_dir = repo_root / ".niyam"
    config_path = niyam_dir / "niyam.yaml"
    config_path.write_text("guard:\n  enabled: true\n  frozen_paths: ['src/critical']\n")
    
    # Mock git diff --cached --name-only
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0, stdout="src/critical/core.py\nREADME.md\n", stderr=""
        )
        
        with patch("niyam.policies.guard.find_niyam_root", return_value=repo_root):
            with pytest.raises(SystemExit) as excinfo:
                run_guard_verify_commit(console)
            assert excinfo.value.code == 1
    
    out, _ = capsys.readouterr()
    assert "Commit Blocked" in out
    assert "src/critical/core.py" in out


def test_refined_mcp_check(repo_root, capsys):
    """Test that refined MCP check accurately matches tools."""
    # Setup registry with a tool
    registry = MCPRegistry()
    registry.tools["dangerous-tool"] = MCPTool(
        name="dangerous-tool",
        type="cli",
        command_or_url="/usr/local/bin/danger",
        risk_level="critical",
        approved=False
    )
    save_mcp_registry(registry, repo_root)
    
    # Mock find_niyam_root
    with patch("niyam.policies.guard.find_niyam_root", return_value=repo_root):
        # 1. Match by name (executable basename)
        with patch("subprocess.Popen") as mock_popen:
            mock_popen.return_value = MagicMock(returncode=0, poll=lambda: 0, stdout=MagicMock(), stderr=MagicMock())
            # Simulate selectors returning nothing to exit quickly
            with patch("selectors.DefaultSelector") as mock_sel:
                mock_sel.return_value.select.return_value = []
                
                with patch("niyam.policies.guard.redact_text", side_effect=lambda x: x):
                    with pytest.raises(SystemExit) as excinfo:
                        run_guard_run(
                            cmd_args=["dangerous-tool", "run"],
                            capture_output=False,
                            console=Console(),
                            mode_override="block"
                        )
                    assert excinfo.value.code == 1
                
        out, _ = capsys.readouterr()
        assert "Blocked" in out
        # The refined check should match 'dangerous-tool'

        # 2. Match by command string prefix
        with patch("subprocess.Popen") as mock_popen:
            mock_popen.return_value = MagicMock(returncode=0, poll=lambda: 0, stdout=MagicMock(), stderr=MagicMock())
            with patch("selectors.DefaultSelector") as mock_sel:
                mock_sel.return_value.select.return_value = []
                
                with patch("niyam.policies.guard.redact_text", side_effect=lambda x: x):
                    with pytest.raises(SystemExit) as excinfo:
                        run_guard_run(
                            cmd_args=["/usr/local/bin/danger", "--force"],
                            capture_output=False,
                            console=Console(),
                            mode_override="block"
                        )
                    assert excinfo.value.code == 1
