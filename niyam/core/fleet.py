"""Multi-repo fleet management core logic."""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional
import yaml
from pydantic import BaseModel, Field


class FleetRepo(BaseModel):
    """A repository managed within the fleet."""
    path: str
    alias: str
    tags: List[str] = Field(default_factory=list)


class FleetConfig(BaseModel):
    """Central registry of all repositories in the Niyam fleet."""
    repos: List[FleetRepo] = Field(default_factory=list)


def get_default_fleet_config_path() -> Path:
    """Get the default path for the fleet configuration file."""
    # Priority:
    # 1. NIYAM_FLEET_CONFIG env var
    # 2. Local niyam-fleet.yaml in current dir
    # 3. Global ~/.niyam/fleet.yaml
    
    env_path = os.environ.get("NIYAM_FLEET_CONFIG")
    if env_path:
        return Path(env_path)
    
    local_path = Path.cwd() / "niyam-fleet.yaml"
    if local_path.exists():
        return local_path
        
    global_dir = Path.home() / ".niyam"
    global_dir.mkdir(parents=True, exist_ok=True)
    return global_dir / "fleet.yaml"


def load_fleet_config(config_path: Optional[Path] = None) -> FleetConfig:
    """Load the fleet configuration from disk."""
    path = config_path or get_default_fleet_config_path()
    
    if not path.exists():
        return FleetConfig()
        
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            return FleetConfig(**data)
    except Exception:
        # Fallback to empty config on error to avoid blocking CLI
        return FleetConfig()


def save_fleet_config(config: FleetConfig, config_path: Optional[Path] = None) -> None:
    """Save the fleet configuration to disk."""
    path = config_path or get_default_fleet_config_path()
    
    # Ensure parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(
            config.model_dump(exclude_none=True),
            f,
            default_flow_style=False,
            sort_keys=False,
        )


def register_repo(path: Path, alias: Optional[str] = None, tags: Optional[List[str]] = None) -> FleetRepo:
    """Register a repository in the fleet."""
    config = load_fleet_config()
    
    abs_path = str(path.absolute())
    # Check if already registered
    for repo in config.repos:
        if repo.path == abs_path:
            # Update alias and tags if provided
            if alias:
                repo.alias = alias
            if tags is not None:
                repo.tags = tags
            save_fleet_config(config)
            return repo
            
    # New registration
    new_repo = FleetRepo(
        path=abs_path,
        alias=alias or path.name,
        tags=tags or []
    )
    config.repos.append(new_repo)
    save_fleet_config(config)
    return new_repo


def discover_repos(root_path: Path, max_depth: int = 3) -> List[FleetRepo]:
    """Discover Niyam workspaces in subdirectories and register them."""
    discovered = []
    
    # We use a manual walk to control depth for scalability
    root_str = str(root_path.absolute())
    base_depth = root_str.count(os.sep)
    
    for root, dirs, files in os.walk(root_path):
        current_depth = root.count(os.sep) - base_depth
        if current_depth >= max_depth:
            dirs[:] = []  # Stop recursion
            continue
            
        if ".niyam" in dirs or ".sutra" in dirs:
            repo = register_repo(Path(root))
            discovered.append(repo)
            # Once we find a Niyam root, we don't need to look deeper in this branch
            dirs[:] = []
            
    return discovered


def sync_fleet_policies(source_repo: FleetRepo, target_repos: List[FleetRepo]) -> List[str]:
    """Sync governance policies from source to target repositories."""
    import shutil
    from niyam.core.config import get_niyam_dir
    
    synced = []
    source_niyam = get_niyam_dir(Path(source_repo.path))
    
    # Files/Dirs to sync
    sync_items = [
        "policies",
        "governance",
        "pricing.json"
    ]
    
    for target in target_repos:
        if target.path == source_repo.path:
            continue
            
        target_niyam = get_niyam_dir(Path(target.path))
        if not target_niyam.exists():
            continue
            
        for item in sync_items:
            src_path = source_niyam / item
            dst_path = target_niyam / item
            
            if src_path.exists():
                if src_path.is_dir():
                    if dst_path.exists():
                        shutil.rmtree(dst_path)
                    shutil.copytree(src_path, dst_path)
                else:
                    shutil.copy2(src_path, dst_path)
        
        synced.append(target.alias)
        
    return synced


def dispatch_fleet_mission(
    requirement: str,
    target_repos: List[FleetRepo],
    runtime: Optional[str] = None,
    auto_approve: bool = False
) -> List[str]:
    """Dispatch a mission to multiple repositories."""
    import subprocess
    import sys
    
    dispatched = []
    
    for target in target_repos:
        # Run 'niyam run' in each repo
        cmd = [sys.executable, "-m", "niyam.cli", "run", requirement]
        if runtime:
            cmd.extend(["--runtime", runtime])
        if auto_approve:
            cmd.append("--auto-approve")
            
        try:
            # We run it in a subprocess to keep the fleet command running
            # In a real scenario, we might want to run these in parallel
            subprocess.run(cmd, cwd=target.path, check=True)
            dispatched.append(target.alias)
        except subprocess.CalledProcessError:
            pass # Continue to next repo even if one fails
            
    return dispatched
