"""Unit tests for Niyam Multi-Repo Fleet Management."""

from __future__ import annotations

import os
from pathlib import Path
import pytest
from unittest.mock import MagicMock, patch

from niyam.core.fleet import FleetConfig, FleetRepo, register_repo, discover_repos, sync_fleet_policies
from niyam.core.config import NIYAM_DIR


@pytest.fixture
def fleet_config_file(tmp_path: Path) -> Path:
    """Create a temporary fleet config file."""
    config_path = tmp_path / "fleet.yaml"
    return config_path


def test_register_repo(fleet_config_file: Path) -> None:
    """Should register a repository in the fleet config."""
    with patch("niyam.core.fleet.get_default_fleet_config_path", return_value=fleet_config_file):
        repo_path = Path("/tmp/mock-repo")
        repo = register_repo(repo_path, alias="mock-alias", tags=["tag1"])
        
        assert repo.alias == "mock-alias"
        assert repo.tags == ["tag1"]
        
        # Verify persistence
        from niyam.core.fleet import load_fleet_config
        config = load_fleet_config(fleet_config_file)
        assert len(config.repos) == 1
        assert config.repos[0].alias == "mock-alias"


def test_discover_repos(tmp_path: Path, fleet_config_file: Path) -> None:
    """Should discover Niyam workspaces in a directory tree."""
    # Create mock workspaces
    repo1 = tmp_path / "repo1"
    repo1.mkdir()
    (repo1 / NIYAM_DIR).mkdir()
    
    repo2 = tmp_path / "subdir" / "repo2"
    repo2.mkdir(parents=True)
    (repo2 / NIYAM_DIR).mkdir()
    
    # Not a Niyam workspace
    (tmp_path / "repo3").mkdir()
    
    with patch("niyam.core.fleet.get_default_fleet_config_path", return_value=fleet_config_file):
        discovered = discover_repos(tmp_path)
        
        assert len(discovered) == 2
        aliases = [r.alias for r in discovered]
        assert "repo1" in aliases
        assert "repo2" in aliases


def test_sync_fleet_policies(tmp_path: Path) -> None:
    """Should sync policies from source to target repos."""
    source = tmp_path / "source"
    source.mkdir()
    (source / NIYAM_DIR).mkdir()
    (source / NIYAM_DIR / "policies").mkdir()
    (source / NIYAM_DIR / "policies" / "test.yaml").write_text("policy data")
    
    target = tmp_path / "target"
    target.mkdir()
    (target / NIYAM_DIR).mkdir()
    
    source_repo = FleetRepo(path=str(source), alias="source")
    target_repo = FleetRepo(path=str(target), alias="target")
    
    synced = sync_fleet_policies(source_repo, [target_repo])
    
    assert "target" in synced
    assert (target / NIYAM_DIR / "policies" / "test.yaml").exists()
    assert (target / NIYAM_DIR / "policies" / "test.yaml").read_text() == "policy data"
