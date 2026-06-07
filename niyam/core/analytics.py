"""Niyam analytics — aggregate performance, cost, and agent efficiency metrics."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from niyam.core.config import find_niyam_root, get_niyam_dir

class PerformanceMetrics:
    """Agent and mission performance metrics aggregation."""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.niyam_dir = get_niyam_dir(repo_root)

    def get_mission_metrics(self, mission_id: str) -> Dict[str, Any]:
        """Aggregate metrics for a specific mission run."""
        run_dir = self.niyam_dir / "runs" / mission_id
        if not run_dir.exists():
            return {}

        metrics = {
            "mission_id": mission_id,
            "total_tokens": 0,
            "total_cost_usd": 0.0,
            "total_duration_s": 0.0,
            "task_count": 0,
            "success_rate": 0.0,
            "savings_percent": 0.0,
            "by_agent": {},
        }

        # 1. Load token ledger
        ledger_path = run_dir / "token-ledger.json"
        if ledger_path.exists():
            try:
                with open(ledger_path, encoding="utf-8") as f:
                    ledger = json.load(f)
                    summary = ledger.get("summary", {})
                    metrics["total_tokens"] = summary.get("total_tokens", 0)
                    metrics["total_cost_usd"] = summary.get("total_cost_usd", 0.0)
                    metrics["savings_percent"] = summary.get("savings_percent", 0.0)
            except Exception:
                pass

        # 2. Walk tasks
        tasks_dir = run_dir / "tasks"
        completed = 0
        if tasks_dir.exists():
            for task_dir in tasks_dir.iterdir():
                if not task_dir.is_dir():
                    continue
                metrics["task_count"] += 1
                
                # Check status from plan if possible (but here we just check for completion)
                log_path = task_dir / "execution.log"
                if log_path.exists():
                    # Simplified: if log exists, we count it for now or check final line
                    pass

        # 3. Load mission plan for accurate status
        from niyam.mission.utils import load_plan
        try:
            plan = load_plan(run_dir)
            tasks = plan.get("tasks", [])
            metrics["task_count"] = len(tasks)
            completed = sum(1 for t in tasks if t.get("status") == "completed")
            if metrics["task_count"] > 0:
                metrics["success_rate"] = (completed / metrics["task_count"]) * 100

            # Aggregate by agent
            for t in tasks:
                agent = t.get("agent", "unknown")
                if agent not in metrics["by_agent"]:
                    metrics["by_agent"][agent] = {"count": 0, "completed": 0}
                metrics["by_agent"][agent]["count"] += 1
                if t.get("status") == "completed":
                    metrics["by_agent"][agent]["completed"] += 1
        except Exception:
            pass

        return metrics

    def get_fleet_summary(self) -> Dict[str, Any]:
        """Aggregate performance across all missions in the repo."""
        runs_dir = self.niyam_dir / "runs"
        if not runs_dir.exists():
            return {}

        summary = {
            "total_missions": 0,
            "total_cost_usd": 0.0,
            "avg_success_rate": 0.0,
            "avg_savings_percent": 0.0,
            "agent_performance": {},
        }

        mission_metrics = []
        for run_dir in runs_dir.iterdir():
            if run_dir.is_dir() and (run_dir / "mission-plan.yaml").exists():
                m = self.get_mission_metrics(run_dir.name)
                if m:
                    mission_metrics.append(m)

        if not mission_metrics:
            return summary

        summary["total_missions"] = len(mission_metrics)
        
        total_success = 0.0
        total_savings = 0.0
        for m in mission_metrics:
            summary["total_cost_usd"] += m["total_cost_usd"]
            total_success += m["success_rate"]
            total_savings += m["savings_percent"]

            # Aggregate agent stats
            for agent, stats in m["by_agent"].items():
                if agent not in summary["agent_performance"]:
                    summary["agent_performance"][agent] = {"tasks": 0, "completed": 0}
                summary["agent_performance"][agent]["tasks"] += stats["count"]
                summary["agent_performance"][agent]["completed"] += stats["completed"]

        summary["avg_success_rate"] = total_success / len(mission_metrics)
        summary["avg_savings_percent"] = total_savings / len(mission_metrics)

        # Calculate agent success rates
        for agent in summary["agent_performance"]:
            stats = summary["agent_performance"][agent]
            stats["success_rate"] = (stats["completed"] / stats["tasks"]) * 100 if stats["tasks"] > 0 else 0

        return summary
