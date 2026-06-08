"""Integration tests for Niyam Multi-Repo Fleet Management."""

import os
import json
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from niyam.cli import app
from niyam.core.fleet import get_default_fleet_config_path

runner = CliRunner()


@pytest.fixture
def fleet_env(tmp_path):
    """Setup a multi-repo environment and isolate fleet config."""
    # Isolate fleet config
    fleet_config = tmp_path / "fleet.yaml"
    
    # Create two mock repos
    repo1 = tmp_path / "repo1"
    repo2 = tmp_path / "repo2"
    repo1.mkdir()
    repo2.mkdir()
    
    # Initialize them as Niyam workspaces
    from niyam.core.init import run_init
    from rich.console import Console
    console = Console(quiet=True)
    
    for repo in [repo1, repo2]:
        os.chdir(repo)
        run_init(profile="fullstack", runtime=None, dry_run=False, force=False, console=console)
        
    os.chdir(tmp_path)
    
    with patch.dict(os.environ, {"NIYAM_FLEET_CONFIG": str(fleet_config)}):
        yield tmp_path, repo1, repo2


def test_fleet_discover_and_list(fleet_env):
    """Verify fleet can discover workspaces and list them."""
    root_dir, repo1, repo2 = fleet_env
    
    # Run discover
    result = runner.invoke(app, ["fleet", "discover", str(root_dir)])
    assert result.exit_code == 0
    assert "repo1" in result.stdout
    assert "repo2" in result.stdout
    
    # Run list
    result = runner.invoke(app, ["fleet", "list"])
    assert result.exit_code == 0
    assert "repo1" in result.stdout
    assert "repo2" in result.stdout


def test_fleet_status_reports_missions(fleet_env):
    """Verify fleet status aggregates mission data across repos."""
    root_dir, repo1, repo2 = fleet_env
    
    # Manually register repos to bypass discovery in this test
    runner.invoke(app, ["fleet", "register", str(repo1)])
    runner.invoke(app, ["fleet", "register", str(repo2)])
    
    # Create a mock mission in repo1
    mission_id = "test-mission-123"
    run_dir = repo1 / ".niyam" / "runs" / mission_id
    run_dir.mkdir(parents=True, exist_ok=True)
    
    plan_data = {
        "mission": {
            "id": mission_id, 
            "status": "running",
            "orchestrator": "claude",
            "requirement": "dummy requirement",
            "created": "2026-06-08T00:00:00Z"
        },
        "tasks": [
            {"id": "T1", "title": "A", "type": "discovery", "status": "completed", "agent": "default-agent"}, 
            {"id": "T2", "title": "B", "type": "implementation", "status": "planned", "agent": "default-agent"}
        ]
    }
    
    import yaml
    with open(run_dir / "mission-plan.yaml", "w") as f:
        yaml.dump(plan_data, f)
        
    result = runner.invoke(app, ["fleet", "status"])
    assert result.exit_code == 0
    assert mission_id in result.stdout
    assert "RUNNING" in result.stdout
    assert "1/2" in result.stdout # Progress


def test_fleet_sync_policies(fleet_env):
    """Verify fleet sync correctly copies policies from source to target."""
    root_dir, repo1, repo2 = fleet_env
    
    # Register repos with specific tags
    runner.invoke(app, ["fleet", "register", str(repo1), "--alias", "source-repo", "--tags", "prod"])
    runner.invoke(app, ["fleet", "register", str(repo2), "--alias", "target-repo", "--tags", "prod"])
    
    # Create a custom policy in the source repo
    source_policy_dir = repo1 / ".niyam" / "policies"
    source_policy_dir.mkdir(parents=True, exist_ok=True)
    (source_policy_dir / "custom-guard.yaml").write_text("rules: strict", encoding="utf-8")
    
    # Ensure target doesn't have it
    target_policy = repo2 / ".niyam" / "policies" / "custom-guard.yaml"
    assert not target_policy.exists()
    
    # Sync policies
    result = runner.invoke(app, ["fleet", "sync", "--source", "source-repo", "--tags", "prod"])
    assert result.exit_code == 0
    assert "target-repo" in result.stdout
    
    # Verify target now has the policy
    assert target_policy.exists()
    assert target_policy.read_text() == "rules: strict"
