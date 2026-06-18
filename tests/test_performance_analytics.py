import pytest
import json
import yaml
from pathlib import Path
from niyam.core.analytics import PerformanceMetrics

def test_performance_analytics_aggregation(tmp_path: Path):
    """Test that PerformanceMetrics correctly aggregates retries, val_fails, and success rates."""
    # Setup mission structure
    runs_dir = tmp_path / ".niyam" / "runs"
    runs_dir.mkdir(parents=True)
    
    mission_id = "test-mission"
    mission_dir = runs_dir / mission_id
    mission_dir.mkdir()
    
    # 1. Mock mission plan with retries
    plan_data = {
        "mission": {
            "id": mission_id, 
            "status": "completed",
            "requirement": "Test requirement",
            "created": "2026-06-11T10:00:00Z",
            "orchestrator": "claude"
        },
        "tasks": [
            {
                "id": "T1", 
                "title": "Task 1",
                "type": "implementation",
                "agent": "senior-engineer", 
                "status": "completed", 
                "retry_count": 0
            },
            {
                "id": "T2", 
                "title": "Task 2",
                "type": "implementation",
                "agent": "senior-engineer", 
                "status": "completed", 
                "retry_count": 2
            },
            {
                "id": "T3", 
                "title": "Task 3",
                "type": "implementation",
                "agent": "review-bot", 
                "status": "failed", 
                "retry_count": 1
            },
        ]
    }
    (mission_dir / "mission-plan.yaml").write_text(yaml.dump(plan_data))
    
    # 2. Mock token ledger
    ledger_data = {
        "events": [
            {"task_id": "T1", "agent": "senior-engineer", "cost_usd": 0.5, "total_tokens": 1000},
            {"task_id": "T2", "agent": "senior-engineer", "cost_usd": 1.5, "total_tokens": 3000, "is_waste": True},
            {"task_id": "T3", "agent": "review-bot", "cost_usd": 0.2, "total_tokens": 500},
        ],
        "summary": {
            "total_cost_usd": 2.2,
            "total_wasted_cost_usd": 1.5,
            "total_tokens": 4500
        }
    }
    (mission_dir / "token-ledger.json").write_text(json.dumps(ledger_data))
    
    # 3. Mock validation failures in task directories
    tasks_dir = mission_dir / "tasks"
    tasks_dir.mkdir()
    
    # T1: clean success
    t1_dir = tasks_dir / "T1"
    t1_dir.mkdir()
    (t1_dir / "validation.json").write_text(json.dumps([{"success": True}]))
    
    # T2: has a validation failure record (even if it eventually passed)
    t2_dir = tasks_dir / "T2"
    t2_dir.mkdir()
    (t2_dir / "validation.json").write_text(json.dumps([{"success": False, "error": "flake"}]))
    
    # T3: failed validation
    t3_dir = tasks_dir / "T3"
    t3_dir.mkdir()
    (t3_dir / "validation.json").write_text(json.dumps([{"success": False}]))
    
    # Initialize metrics engine
    metrics_engine = PerformanceMetrics(tmp_path)
    
    # Test mission metrics
    m = metrics_engine.get_mission_metrics(mission_id)
    assert m["task_count"] == 3
    assert m["completed_count"] == 2
    assert m["failed_count"] == 1
    assert m["total_retries"] == 3  # T2(2) + T3(1)
    assert m["validation_failures"] == 2 # T2 and T3 failed validation at some point
    assert m["total_cost_usd"] == 2.2
    
    # Test agent breakdown
    eng_stats = m["by_agent"]["senior-engineer"]
    assert eng_stats["count"] == 2
    assert eng_stats["completed"] == 2
    assert eng_stats["retries"] == 2
    assert eng_stats["val_fails"] == 1
    
    bot_stats = m["by_agent"]["review-bot"]
    assert bot_stats["count"] == 1
    assert bot_stats["completed"] == 0
    assert bot_stats["failed"] == 1
    
    # Test fleet summary
    summary = metrics_engine.get_fleet_summary()
    assert summary["total_missions"] == 1
    assert summary["total_retries"] == 3
    
    eng_perf = summary["agent_performance"]["senior-engineer"]
    assert eng_perf["success_rate"] == 100.0
    assert eng_perf["avg_retries"] == 1.0 # 2 retries / 2 tasks
    assert eng_perf["cost_per_success"] == 1.0 # $2.0 total cost / 2 successes
    
    bot_perf = summary["agent_performance"]["review-bot"]
    assert bot_perf["success_rate"] == 0.0
