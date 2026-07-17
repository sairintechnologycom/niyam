"""Phase 3 routing + Phase 4 evidence review tests."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
import yaml

from niyam.core.config import (
    BudgetConfig,
    GovernanceConfig,
    NiyamConfig,
    RoutingConfig,
)
from niyam.mission.routing import (
    apply_budget_tier_degradation,
    apply_routing_policy,
    default_tier_for_task,
    degrade_tier,
    resolve_model_for_task,
    should_degrade_tier,
)
from niyam.mission.reviewer import review_task_evidence, _parse_verdict


def test_default_tier_by_task_type() -> None:
    assert default_tier_for_task({"type": "discovery"}) == "premium"
    assert default_tier_for_task({"type": "implementation"}) == "standard"
    assert default_tier_for_task({"type": "validation"}) == "economy"
    assert default_tier_for_task({"type": "review"}) == "premium"


def test_degrade_tier_steps() -> None:
    assert degrade_tier("premium") == "standard"
    assert degrade_tier("standard") == "economy"
    assert degrade_tier("economy") == "economy"


def test_apply_routing_policy_sets_tier_and_model() -> None:
    cfg = NiyamConfig(runtimes=["claude"])
    tasks = [
        {"id": "T1", "type": "discovery", "agent": "backend-specialist", "runtime": "claude"},
        {"id": "T2", "type": "implementation", "agent": "backend-specialist", "runtime": "claude"},
        {"id": "T3", "type": "validation", "agent": "qa-reviewer", "runtime": "claude"},
    ]
    apply_routing_policy(tasks, cfg)
    assert tasks[0]["tier"] == "premium"
    assert tasks[1]["tier"] == "standard"
    assert tasks[2]["tier"] == "economy"
    # Models resolved via RuntimeSpec
    assert tasks[0].get("model") == "opus"
    assert tasks[1].get("model") == "sonnet"
    assert tasks[2].get("model") == "haiku"


def test_resolve_model_preserves_tier_across_runtime_hop() -> None:
    task = {"type": "implementation", "tier": "economy", "runtime": "claude"}
    m1 = resolve_model_for_task(task, runtime="claude")
    m2 = resolve_model_for_task(task, runtime="gemini")
    assert m1 == "haiku"
    assert m2 == "gemini-2.0-flash"


def test_codex_uses_its_account_default_model() -> None:
    assert resolve_model_for_task({"tier": "standard"}, runtime="codex") is None


def test_budget_degrade_at_80_percent(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "token-ledger.json").write_text(
        json.dumps({"summary": {"total_cost_usd": 8.5, "total_tokens": 0}}),
        encoding="utf-8",
    )
    cfg = NiyamConfig(
        governance=GovernanceConfig(
            budget=BudgetConfig(max_mission_cost_usd=10.0, degrade_tier_at=0.8)
        )
    )
    assert should_degrade_tier(run_dir, cfg) is True
    task = {"type": "implementation", "tier": "premium", "runtime": "claude"}
    apply_budget_tier_degradation(task, run_dir, cfg)
    assert task["tier"] == "standard"
    assert task.get("_tier_degraded") is True


def test_budget_no_degrade_under_threshold(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "token-ledger.json").write_text(
        json.dumps({"summary": {"total_cost_usd": 1.0, "total_tokens": 0}}),
        encoding="utf-8",
    )
    cfg = NiyamConfig(
        governance=GovernanceConfig(
            budget=BudgetConfig(max_mission_cost_usd=10.0, degrade_tier_at=0.8)
        )
    )
    assert should_degrade_tier(run_dir, cfg) is False


def test_parse_verdict_yaml_block() -> None:
    text = """
Here is my review:
```yaml
verdict: REWORK_REQUIRED
confidence: high
required_changes:
  - Add missing healthcheck tests
issues:
  - validation failed
```
"""
    result = _parse_verdict(text)
    assert result["verdict"] == "REWORK_REQUIRED"
    assert "Add missing healthcheck tests" in result["required_changes"]


def test_review_task_evidence_test_default_pass(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("NIYAM_TEST", "1")
    task_dir = tmp_path / "tasks" / "T1"
    task_dir.mkdir(parents=True)
    (task_dir / "validation.log").write_text("PASS: lint\n", encoding="utf-8")
    run_dir = tmp_path
    task = {"id": "T1", "type": "implementation", "title": "impl", "agent": "backend"}
    result = review_task_evidence(
        task=task,
        task_dir=task_dir,
        run_dir=run_dir,
        repo_root=tmp_path,
    )
    assert result["verdict"] == "PASS"
    assert (task_dir / "review-verdict.yaml").exists()


def test_review_task_evidence_rework_on_validation_fail(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("NIYAM_TEST", "1")
    task_dir = tmp_path / "tasks" / "T1"
    task_dir.mkdir(parents=True)
    (task_dir / "validation.log").write_text("FAIL: test :: pytest\n", encoding="utf-8")
    task = {"id": "T1", "type": "implementation", "title": "impl", "agent": "backend"}
    result = review_task_evidence(
        task=task,
        task_dir=task_dir,
        run_dir=tmp_path,
        repo_root=tmp_path,
    )
    assert result["verdict"] == "REWORK_REQUIRED"


def test_review_env_verdict_override(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("NIYAM_TEST", "1")
    monkeypatch.setenv("NIYAM_REVIEW_VERDICT", "REJECT")
    task_dir = tmp_path / "T1"
    task_dir.mkdir()
    task = {"id": "T1", "type": "implementation", "title": "x", "agent": "a"}
    result = review_task_evidence(
        task=task, task_dir=task_dir, run_dir=tmp_path, repo_root=tmp_path
    )
    assert result["verdict"] == "REJECT"


def test_planner_applies_routing_on_fallback(niyam_repo: Path, monkeypatch) -> None:
    from rich.console import Console
    from niyam.core.config import get_niyam_dir
    from niyam.mission.planner import run_mission_plan

    monkeypatch.setenv("NIYAM_TEST", "1")
    os.chdir(niyam_repo)
    req = niyam_repo / "req.md"
    req.write_text(
        "# Healthcheck\n\nAdd GET /health endpoint that returns 200.\n",
        encoding="utf-8",
    )
    mid = run_mission_plan(str(req), console=Console(quiet=True))
    plan_path = get_niyam_dir(niyam_repo) / "runs" / mid / "mission-plan.yaml"
    plan = yaml.safe_load(plan_path.read_text(encoding="utf-8"))
    tasks = {t["id"]: t for t in plan["tasks"]}
    # At least one discovery/premium and implementation/standard when types present
    types = {t["type"] for t in plan["tasks"]}
    for t in plan["tasks"]:
        assert t.get("tier") in {"premium", "standard", "economy"}
    if "discovery" in types:
        disc = next(t for t in plan["tasks"] if t["type"] == "discovery")
        assert disc["tier"] == "premium"
    if "implementation" in types:
        impl = next(t for t in plan["tasks"] if t["type"] == "implementation")
        assert impl["tier"] == "standard"
