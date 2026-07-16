"""Acceptance tests for AI Application attribution across Niyam records."""

from __future__ import annotations

import json
from pathlib import Path

import yaml
from rich.console import Console
from typer.testing import CliRunner

from niyam.cli import app
from niyam.core.applications import register_application
from niyam.core.config import MissionMeta
from niyam.core.cost import CostEvent, generate_cost_metrics, load_cost_events
from niyam.core.evidence import UnifiedEvidenceCompiler
from niyam.core.fleet import FleetRepo, register_repo
from niyam.core.mcp import MCPTool
from niyam.core.skills import RegisteredSkill, load_skill_registry, register_skill


def test_attribution_fields_are_optional_for_legacy_records() -> None:
    cost = CostEvent(
        timestamp="2026-07-14T00:00:00Z",
        session_id="S1",
        task_id="T1",
        tool_name="codex",
        model="gpt-5",
        repo="repo",
        branch="main",
        status="success",
    )
    tool = MCPTool(name="docs", type="api", risk_level="low")
    skill = RegisteredSkill(
        manifest={"name": "review"},
        checksum="abc",
        risk_level="low",
        registered_at="2026-07-14T00:00:00Z",
        updated_at="2026-07-14T00:00:00Z",
    )
    mission = MissionMeta(
        id="M1",
        requirement="test",
        created="2026-07-14T00:00:00Z",
        status="planned",
        orchestrator="codex",
    )
    fleet_repo = FleetRepo(path="/tmp/repo", alias="repo")

    assert cost.application_id is None
    assert tool.application_id is None
    assert skill.application_id is None
    assert mission.application_id is None
    assert fleet_repo.application_id is None


def test_cost_and_evidence_attribute_registered_application(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".niyam").mkdir()
    register_application("support-bot", name="Support Bot", root=tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "cost",
            "log",
            "--model",
            "gpt-5-codex",
            "--input-tokens",
            "10",
            "--application",
            "support-bot",
        ],
    )
    assert result.exit_code == 0, result.stdout
    events = load_cost_events(tmp_path)
    assert events[0].application_id == "support-bot"
    assert generate_cost_metrics(events)["by_application"]["support-bot"] > 0

    evidence = UnifiedEvidenceCompiler(tmp_path).compile(["applications", "cost"])
    assert (
        evidence["applications"]["applications"][0]["application_id"] == "support-bot"
    )
    assert evidence["cost"]["by_application"]["support-bot"] > 0

    unknown = runner.invoke(
        app, ["cost", "log", "--application", "missing-application"]
    )
    assert unknown.exit_code == 1
    assert "not registered" in unknown.stdout


def test_tool_skill_mission_and_fleet_accept_application_id(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)
    from niyam.core.init import run_init

    run_init(
        profile="fullstack",
        runtime=None,
        dry_run=False,
        force=False,
        console=Console(quiet=True),
    )
    register_application("support-bot", name="Support Bot", root=tmp_path)
    runner = CliRunner()

    tool = runner.invoke(
        app,
        [
            "mcp",
            "register",
            "search",
            "--type",
            "api",
            "--application",
            "support-bot",
        ],
    )
    assert tool.exit_code == 0, tool.stdout
    registry = json.loads((tmp_path / ".niyam" / "mcp-registry.json").read_text())
    assert registry["tools"]["search"]["application_id"] == "support-bot"

    skill_file = tmp_path / "review" / "SKILL.md"
    skill_file.parent.mkdir()
    skill_file.write_text("---\nname: review\n---\nReview code.\n", encoding="utf-8")
    register_skill(skill_file, application_id="support-bot", root=tmp_path)
    assert (
        load_skill_registry(tmp_path).skills["review"].application_id == "support-bot"
    )

    mission = runner.invoke(
        app,
        ["mission", "plan", "Add a health endpoint", "--application", "support-bot"],
    )
    assert mission.exit_code == 0, mission.stdout
    run_dirs = [
        path
        for path in (tmp_path / ".niyam" / "runs").iterdir()
        if path.is_dir() and path.name != "current"
    ]
    plan = yaml.safe_load(
        (
            max(run_dirs, key=lambda p: p.stat().st_mtime) / "mission-plan.yaml"
        ).read_text()
    )
    assert plan["mission"]["application_id"] == "support-bot"

    fleet_repo = register_repo(
        tmp_path,
        alias="support",
        application_id="support-bot",
        config_path=tmp_path / "fleet.yaml",
    )
    assert fleet_repo.application_id == "support-bot"
