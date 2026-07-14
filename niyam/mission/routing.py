"""Cost-aware model tier routing for mission tasks."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from niyam.core.config import NiyamConfig, RoutingConfig, load_niyam_config
from niyam.runtimes.registry import get_runtime_spec

TIER_ORDER = ("premium", "standard", "economy")


def normalize_tier(tier: str | None) -> str | None:
    if not tier:
        return None
    t = str(tier).strip().lower()
    if t in TIER_ORDER:
        return t
    # aliases
    if t in {"high", "opus", "pro"}:
        return "premium"
    if t in {"mid", "medium", "default", "sonnet"}:
        return "standard"
    if t in {"low", "cheap", "haiku", "flash", "mini"}:
        return "economy"
    return None


def default_tier_for_task(
    task: dict[str, Any], routing: RoutingConfig | None = None
) -> str:
    routing = routing or RoutingConfig()
    agent = str(task.get("agent") or "")
    if agent and agent in routing.by_agent:
        return normalize_tier(routing.by_agent[agent]) or routing.default_tier
    ttype = str(task.get("type") or "implementation")
    return (
        normalize_tier(routing.by_type.get(ttype))
        or normalize_tier(routing.default_tier)
        or "standard"
    )


def degrade_tier(tier: str | None, steps: int = 1) -> str:
    """Drop one or more tiers toward economy."""
    current = normalize_tier(tier) or "standard"
    try:
        idx = TIER_ORDER.index(current)
    except ValueError:
        idx = 1
    new_idx = min(len(TIER_ORDER) - 1, idx + max(0, steps))
    return TIER_ORDER[new_idx]


def apply_routing_policy(
    tasks: list[dict[str, Any]],
    config: NiyamConfig | None = None,
    *,
    force: bool = False,
) -> list[dict[str, Any]]:
    """Normalize task tier/model fields from routing policy.

    Does not override an explicit ``model`` unless ``force`` is True.
    Explicit ``tier`` is kept (normalized) unless force replaces from policy.
    """
    routing = (config.routing if config and config.routing else None) or RoutingConfig()
    for task in tasks:
        explicit_model = task.get("model")
        explicit_tier = normalize_tier(task.get("tier"))
        if force or not explicit_tier:
            task["tier"] = default_tier_for_task(task, routing)
        else:
            task["tier"] = explicit_tier
        if force:
            task.pop("model", None)
        elif explicit_model:
            task["model"] = explicit_model
        # Resolve concrete model id when possible
        runtime = task.get("runtime") or (
            config.runtimes[0] if config and config.runtimes else "claude"
        )
        model = resolve_model_for_task(task, runtime=runtime, repo_root=None)
        if model and not task.get("model"):
            task["model"] = model
    return tasks


def resolve_model_for_task(
    task: dict[str, Any],
    *,
    runtime: str | None = None,
    repo_root: Path | None = None,
) -> str | None:
    """Resolve concrete model id from task model/tier + RuntimeSpec."""
    if task.get("model"):
        return str(task["model"])
    rt = runtime or task.get("runtime") or "claude"
    tier = normalize_tier(task.get("tier")) or "standard"
    spec = get_runtime_spec(str(rt), repo_root)
    if spec is None:
        return None
    return spec.resolve_model(tier=tier, model=None)


def mission_budget_usage(run_dir: Path) -> dict[str, float]:
    """Return current mission cost/token totals from token-ledger.json."""
    ledger_path = run_dir / "token-ledger.json"
    if not ledger_path.exists():
        return {"cost_usd": 0.0, "tokens": 0.0}
    try:
        data = json.loads(ledger_path.read_text(encoding="utf-8"))
    except Exception:
        return {"cost_usd": 0.0, "tokens": 0.0}
    summary = data.get("summary") or {}
    return {
        "cost_usd": float(summary.get("total_cost_usd") or 0.0),
        "tokens": float(summary.get("total_tokens") or 0.0),
    }


def should_degrade_tier(
    run_dir: Path,
    config: NiyamConfig | None = None,
) -> bool:
    """True when mission spend has reached the degrade threshold (default 80%)."""
    if config is None:
        return False
    budget = None
    if config.governance and config.governance.budget:
        budget = config.governance.budget
    if budget is None:
        return False
    threshold = float(getattr(budget, "degrade_tier_at", 0.8) or 0.8)
    usage = mission_budget_usage(run_dir)
    if budget.max_mission_cost_usd and budget.max_mission_cost_usd > 0:
        if usage["cost_usd"] >= threshold * float(budget.max_mission_cost_usd):
            return True
    if budget.max_mission_tokens and budget.max_mission_tokens > 0:
        if usage["tokens"] >= threshold * float(budget.max_mission_tokens):
            return True
    return False


def apply_budget_tier_degradation(
    task: dict[str, Any],
    run_dir: Path,
    config: NiyamConfig | None = None,
) -> dict[str, Any]:
    """Possibly drop task tier when mission budget is under pressure."""
    if not should_degrade_tier(run_dir, config):
        return task
    original = normalize_tier(task.get("tier")) or "standard"
    degraded = degrade_tier(original, steps=1)
    if degraded != original:
        task["tier"] = degraded
        # Force re-resolve model for new tier
        task.pop("model", None)
        runtime = task.get("runtime") or "claude"
        model = resolve_model_for_task(task, runtime=runtime)
        if model:
            task["model"] = model
        task["_tier_degraded"] = True
        task["_tier_degraded_from"] = original
    return task


def load_routing_config(repo_root: Path | None = None) -> tuple[NiyamConfig | None, RoutingConfig]:
    try:
        cfg = load_niyam_config(repo_root) if repo_root else load_niyam_config()
        return cfg, (cfg.routing if cfg.routing else RoutingConfig())
    except Exception:
        return None, RoutingConfig()
