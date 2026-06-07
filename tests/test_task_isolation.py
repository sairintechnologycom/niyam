import json
import pytest
import os
from pathlib import Path
from unittest.mock import MagicMock, patch
from niyam.mission.task_runner import execute_single_task
from niyam.core.config import ProjectConfig

def test_task_isolation_hook_injection(tmp_path):
    """Should inject task-specific guard config into the worktree."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    niyam_dir = repo_root / ".niyam"
    niyam_dir.mkdir()
    
    # Setup a dummy mission and task
    mission_id = "test-mission"
    run_dir = niyam_dir / "runs" / mission_id
    run_dir.mkdir(parents=True)
    
    task = {
        "id": "T1",
        "title": "Isolated Task",
        "agent": "test-agent",
        "allowed_files": ["src/backend/*"],
        "blocked_files": ["config/*"],
    }
    
    # Mocking create_worktree to just return a directory
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()
    (worktree_path / ".niyam" / "hook-cache").mkdir(parents=True)
    
    # Mock existing base config
    base_config = {
        "guard_enabled": False,
        "deny_patterns": ["rm -rf /"],
    }
    (worktree_path / ".niyam" / "hook-cache" / "guard-config.json").write_text(json.dumps(base_config))

    with patch("niyam.mission.task_runner.create_worktree", return_value=worktree_path):
        with patch("niyam.mission.task_runner.cleanup_worktree"):
            with patch("niyam.mission.task_runner.transition_task"):
                with patch("niyam.mission.task_runner.load_plan", return_value={"mission": {"orchestrator": "claude"}}):
                    with patch("niyam.mission.task_runner.run_validation_command", return_value=True):
                        with patch("niyam.mission.task_runner.update_token_ledger"):
                            with patch("subprocess.run") as mock_run:
                                # Mock subprocess.run to avoid actual execution
                                mock_run.return_value = MagicMock(returncode=0)
                                
                                # We need to set NIYAM_TEST=1 to avoid real path freeze logic and other things
                                with patch.dict(os.environ, {"NIYAM_TEST": "1"}):
                                    execute_single_task(
                                        task, 
                                        run_dir, 
                                        niyam_dir, 
                                        repo_root, 
                                        mission_id, 
                                        True, # use_worktree
                                        ProjectConfig(), # real config
                                        MagicMock() # console
                                    )
    
    # Verify injected config
    injected_path = worktree_path / ".niyam" / "hook-cache" / "guard-config.json"
    assert injected_path.exists()
    injected_config = json.loads(injected_path.read_text())
    
    assert injected_config["guard_enabled"] is True
    assert injected_config["frozen_paths"] == ["src/backend/*"]
    assert "rm -rf /" in injected_config["deny_patterns"]
    assert "config/*" in injected_config["deny_write_patterns"]
