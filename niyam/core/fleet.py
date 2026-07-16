"""Multi-repo fleet management core logic."""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional, Any
import yaml
from pydantic import BaseModel, Field


class FleetRepo(BaseModel):
    """A repository managed within the fleet."""
    path: str
    alias: str
    tags: List[str] = Field(default_factory=list)
    depends_on: List[str] = Field(default_factory=list)
    application_id: str | None = None


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


def register_repo(
    path: Path,
    alias: Optional[str] = None,
    tags: Optional[List[str]] = None,
    depends_on: Optional[List[str]] = None,
    application_id: str | None = None,
    config_path: Path | None = None,
) -> FleetRepo:
    """Register a repository in the fleet."""
    from niyam.core.applications import require_application

    application_id = require_application(application_id, path)
    config = load_fleet_config(config_path)

    abs_path = str(path.absolute())
    # Check if already registered
    for repo in config.repos:
        if repo.path == abs_path:
            # Update alias, tags, and depends_on if provided
            if alias:
                repo.alias = alias
            if tags is not None:
                repo.tags = tags
            if depends_on is not None:
                repo.depends_on = depends_on
            if application_id is not None:
                repo.application_id = application_id
            save_fleet_config(config, config_path)
            return repo

    # New registration
    new_repo = FleetRepo(
        path=abs_path,
        alias=alias or path.name,
        tags=tags or [],
        depends_on=depends_on or [],
        application_id=application_id,
    )
    config.repos.append(new_repo)
    save_fleet_config(config, config_path)
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


def resolve_fleet_dependencies(repos: List[FleetRepo]) -> List[List[FleetRepo]]:
    """Group repositories into execution waves based on their dependencies (topological sort)."""
    alias_to_repo = {r.alias: r for r in repos}
    all_aliases = set(alias_to_repo.keys())

    # Build adjacency list and in-degree map
    # We only care about dependencies within the provided repos list
    adj = {alias: set() for alias in all_aliases}
    in_degree = {alias: 0 for alias in all_aliases}

    for repo in repos:
        for dep in repo.depends_on:
            if dep in all_aliases:
                adj[dep].add(repo.alias)
                in_degree[repo.alias] += 1

    # Kahn's algorithm for topological sort, but grouping by waves
    waves = []
    current_wave_aliases = [alias for alias in all_aliases if in_degree[alias] == 0]

    while current_wave_aliases:
        waves.append([alias_to_repo[alias] for alias in current_wave_aliases])
        next_wave_aliases = []
        for alias in current_wave_aliases:
            for neighbor in adj[alias]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    next_wave_aliases.append(neighbor)
        current_wave_aliases = next_wave_aliases

    # Detect cycles
    flattened_waves = [r.alias for wave in waves for r in wave]
    if len(flattened_waves) < len(repos):
        remaining = all_aliases - set(flattened_waves)
        raise ValueError(f"Circular dependency detected in fleet among: {', '.join(remaining)}")

    return waves


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
    auto_approve: bool = False,
    max_workers: int = 4
) -> dict[str, Any]:
    """Dispatch a mission to multiple repositories in parallel waves."""
    import subprocess
    import sys
    from concurrent.futures import ThreadPoolExecutor, as_completed

    waves = resolve_fleet_dependencies(target_repos)
    results = {
        "waves": [],
        "success": [],
        "failed": [],
        "summary": {}
    }

    def _run_mission(repo: FleetRepo) -> tuple[str, bool, str]:
        cmd = [sys.executable, "-m", "niyam.cli", "run", requirement]
        if runtime:
            cmd.extend(["--runtime", runtime])
        if auto_approve:
            cmd.append("--auto-approve")

        try:
            # We use subprocess.run with capture_output to keep the UI clean
            res = subprocess.run(cmd, cwd=repo.path, capture_output=True, text=True, check=True)
            return repo.alias, True, res.stdout
        except subprocess.CalledProcessError as e:
            return repo.alias, False, e.stderr + e.stdout
        except Exception as e:
            return repo.alias, False, str(e)

    for i, wave in enumerate(waves):
        wave_results = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_repo = {executor.submit(_run_mission, repo): repo for repo in wave}
            for future in as_completed(future_to_repo):
                alias, success, output = future.result()
                wave_results.append({
                    "alias": alias,
                    "success": success,
                    "output_preview": output[:500] + "..." if len(output) > 500 else output
                })
                if success:
                    results["success"].append(alias)
                else:
                    results["failed"].append(alias)
        
        results["waves"].append({
            "wave_index": i + 1,
            "results": wave_results
        })

        # Stop if any repo in a wave fails? 
        # For now, we continue within the wave, but could stop next waves.
        if any(not r["success"] for r in wave_results):
            # If a dependency fails, we should probably stop subsequent waves
            break

    return results
