"""Core module for Niyam cost tracking and token auditing."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel

from niyam.core.config import find_niyam_root

logger = logging.getLogger(__name__)


class CostEvent(BaseModel):
    """Pydantic model representing logged token usage and cost metadata."""

    timestamp: str
    session_id: str
    task_id: str
    tool_name: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost: float = 0.0
    repo: str
    branch: str
    status: str
    notes: Optional[str] = None


def get_pricing_path(root: Path | None = None) -> Path:
    """Get path to local configurable model pricing JSON file."""
    if root is None:
        root = find_niyam_root()
    if root is None:
        root = Path.cwd()
    return root / ".niyam" / "pricing.json"


DEFAULT_PRICING = {
    "claude-sonnet": {"input_cost_per_million": 3.00, "output_cost_per_million": 15.00},
    "claude-3-5-sonnet": {
        "input_cost_per_million": 3.00,
        "output_cost_per_million": 15.00,
    },
    "claude-opus": {"input_cost_per_million": 15.00, "output_cost_per_million": 75.00},
    "claude-haiku": {"input_cost_per_million": 0.25, "output_cost_per_million": 1.25},
    "gpt-5.5": {"input_cost_per_million": 5.00, "output_cost_per_million": 30.00},
    "gpt-5.4": {"input_cost_per_million": 2.50, "output_cost_per_million": 15.00},
    "gpt-5.4-mini": {"input_cost_per_million": 0.75, "output_cost_per_million": 4.50},
    "gpt-5-codex": {"input_cost_per_million": 2.50, "output_cost_per_million": 15.00},
    "gpt-4o": {"input_cost_per_million": 5.00, "output_cost_per_million": 15.00},
    "gemini-pro": {"input_cost_per_million": 3.50, "output_cost_per_million": 10.50},
    "gemini-flash": {"input_cost_per_million": 0.075, "output_cost_per_million": 0.30},
    "unknown": {"input_cost_per_million": 0.0, "output_cost_per_million": 0.0},
}


def load_pricing(root: Path | None = None) -> dict:
    """Load configurable model pricing rates, creating default configuration if missing.

    If saas.pricing_url is configured in niyam.yaml, attempts to fetch and update
    the local pricing cache.
    """
    from niyam.core.config import load_niyam_config
    import urllib.request
    import urllib.error

    path = get_pricing_path(root)
    pricing = dict(DEFAULT_PRICING)

    # 1. Load local pricing if it exists
    if path.exists():
        try:
            with open(path, encoding="utf-8") as f:
                local_pricing = json.load(f)
                if isinstance(local_pricing, dict):
                    pricing = {**DEFAULT_PRICING, **local_pricing}
        except Exception as e:
            logger.debug("Failed to load local pricing file %s: %s", path, e)

    # 2. Check for remote pricing URL
    remote_url = None
    try:
        config_root = root if root else find_niyam_root()
        if config_root:
            config = load_niyam_config(config_root)
            remote_url = config.saas.pricing_url
    except Exception:
        pass

    # 3. Fetch remote pricing if URL is set
    if remote_url:
        try:
            with urllib.request.urlopen(remote_url, timeout=5) as response:
                remote_data = json.loads(response.read().decode("utf-8"))
                if isinstance(remote_data, dict):
                    pricing = remote_data
                    # Update local cache
                    try:
                        path.parent.mkdir(parents=True, exist_ok=True)
                        with open(path, "w", encoding="utf-8") as f:
                            json.dump(pricing, f, indent=2)
                    except Exception:
                        pass
        except Exception as e:
            logger.debug("Failed to fetch remote pricing from %s: %s", remote_url, e)

    # 4. Initialize default if still empty or missing and local doesn't exist
    if not path.exists() and not remote_url:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_PRICING, f, indent=2)
        except Exception:
            pass

    return pricing


def calculate_cost(
    model: str, input_tokens: int, output_tokens: int, pricing: dict
) -> float:
    """Calculate estimated cost (USD) using the model pricing table rates.
    
    Prioritizes exact case-insensitive match, falls back to substring match,
    and finally to 'unknown' entry.
    """
    model_key = model.lower().strip()
    
    # 1. Exact match
    rates = pricing.get(model_key)
    
    # 2. Loose match search (e.g. 'gpt-4o-2024-05-13' matches 'gpt-4o')
    if not rates:
        for k, v in pricing.items():
            if k != "unknown" and (k in model_key or model_key in k):
                rates = v
                break
                
    # 3. Final fallback
    if not rates:
        rates = pricing.get(
            "unknown", {"input_cost_per_million": 0.0, "output_cost_per_million": 0.0}
        )

    input_rate = rates.get("input_cost_per_million", 0.0)
    output_rate = rates.get("output_cost_per_million", 0.0)

    cost = (input_tokens * input_rate / 1_000_000.0) + (
        output_tokens * output_rate / 1_000_000.0
    )
    return round(cost, 6)


def get_repo_name(root: Path) -> str:
    """Retrieve git repository name or fall back to directory name."""
    import subprocess

    try:
        res = subprocess.run(
            ["git", "config", "--get", "remote.origin.url"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode == 0 and res.stdout.strip():
            url = res.stdout.strip()
            name = url.split("/")[-1]
            if name.endswith(".git"):
                name = name[:-4]
            return name
    except Exception as e:
        logger.debug("Failed to get git repo name: %s", e)
    return root.name


def get_branch_name(root: Path) -> str:
    """Retrieve current Git branch name or fall back to main."""
    import subprocess

    try:
        res = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip()
    except Exception as e:
        logger.debug("Failed to get git branch name: %s", e)
    return "main"


def log_cost_event(event: CostEvent, root: Path | None = None) -> None:
    """Log a cost event locally to JSONL file with cross-platform locking."""
    if root is None:
        root = find_niyam_root()
    if root is None:
        root = Path.cwd()
    log_dir = root / ".niyam" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    path = log_dir / "cost-events.jsonl"

    try:
        import fcntl
        with open(path, "a", encoding="utf-8") as f:
            try:
                fcntl.flock(f, fcntl.LOCK_EX)
                f.write(event.model_dump_json() + "\n")
                f.flush()
                os.fsync(f.fileno())
            finally:
                try:
                    fcntl.flock(f, fcntl.LOCK_UN)
                except Exception:
                    pass
    except ImportError:
        # Windows fallback using msvcrt
        try:
            import msvcrt
            with open(path, "a", encoding="utf-8") as f:
                # Seek to end and lock 1 byte at current position
                # This is a basic way to lock on Windows without external deps
                f.seek(0, os.SEEK_END)
                try:
                    # msrvcrt.locking uses sizes, we lock a small range
                    # This is indicative; better to use a proper file lock if available
                    # but for Niyam core we avoid new heavy dependencies.
                    msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)
                    f.write(event.model_dump_json() + "\n")
                    f.flush()
                    os.fsync(f.fileno())
                finally:
                    try:
                        f.seek(0, os.SEEK_END)
                        msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
                    except Exception:
                        pass
        except ImportError:
            # Fallback to no locking if neither is available
            with open(path, "a", encoding="utf-8") as f:
                f.write(event.model_dump_json() + "\n")
                f.flush()
                os.fsync(f.fileno())


def load_cost_events(root: Path | None = None) -> list[CostEvent]:
    """Load all logged cost events from local JSONL file."""
    if root is None:
        root = find_niyam_root()
    if root is None:
        root = Path.cwd()
    path = root / ".niyam" / "logs" / "cost-events.jsonl"
    if not path.exists():
        return []
    events = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    events.append(CostEvent.model_validate_json(line))
                except Exception as e:
                    logger.debug("Failed to parse cost event line: %s", e)
    return events


def generate_cost_metrics(events: list[CostEvent]) -> dict:
    """Aggregate logged cost events into day, repo, task, and session summaries."""
    metrics = {
        "total_cost": 0.0,
        "total_input_tokens": 0,
        "total_output_tokens": 0,
        "by_day": {},
        "by_repo": {},
        "by_task": {},
        "by_session": {},
        "by_tool": {},
        "failed_repeated_cost": 0.0,
        "failed_repeated_count": 0,
        "wastage_by_tool": {},
        "success_cost": 0.0,
        "success_count": 0,
    }

    for event in events:
        cost = event.estimated_cost
        metrics["total_cost"] += cost
        metrics["total_input_tokens"] += event.input_tokens
        metrics["total_output_tokens"] += event.output_tokens

        # Day grouping (YYYY-MM-DD)
        day = event.timestamp.split("T")[0]
        if day not in metrics["by_day"]:
            metrics["by_day"][day] = 0.0
        metrics["by_day"][day] += cost

        # Repo grouping
        repo = event.repo
        if repo not in metrics["by_repo"]:
            metrics["by_repo"][repo] = 0.0
        metrics["by_repo"][repo] += cost

        # Task grouping
        task = event.task_id
        if task not in metrics["by_task"]:
            metrics["by_task"][task] = 0.0
        metrics["by_task"][task] += cost

        # Session grouping
        session = event.session_id
        if session not in metrics["by_session"]:
            metrics["by_session"][session] = 0.0
        metrics["by_session"][session] += cost

        # Tool grouping
        tool = event.tool_name
        if tool not in metrics["by_tool"]:
            metrics["by_tool"][tool] = 0.0
        metrics["by_tool"][tool] += cost

        # Status checks (failed/repeated)
        status = event.status.lower()
        if "fail" in status or "repeat" in status:
            metrics["failed_repeated_cost"] += cost
            metrics["failed_repeated_count"] += 1
            
            if tool not in metrics["wastage_by_tool"]:
                metrics["wastage_by_tool"][tool] = 0.0
            metrics["wastage_by_tool"][tool] += cost
        else:
            metrics["success_cost"] += cost
            metrics["success_count"] += 1

    return metrics
