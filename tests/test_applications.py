"""Tests for the local AI Application inventory."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from niyam.cli import app
from niyam.core.applications import load_application_registry, register_application


def test_application_registry_round_trip_and_update(tmp_path: Path) -> None:
    app_record = register_application(
        "support-bot",
        name="Support Bot",
        owner="ai-platform",
        repository="https://example.test/support-bot",
        tags=["customer-facing"],
        root=tmp_path,
    )

    assert app_record.application_id == "support-bot"
    assert load_application_registry(tmp_path).applications["support-bot"] == app_record

    updated = register_application(
        "support-bot",
        status="production",
        update=True,
        root=tmp_path,
    )
    assert updated.name == "Support Bot"
    assert updated.status == "production"

    data = json.loads((tmp_path / ".niyam" / "applications.json").read_text())
    assert data["schema_version"] == "1.0.0"


def test_applications_cli_register_list_show_and_reject_duplicate(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".niyam").mkdir()
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "applications",
            "register",
            "support-bot",
            "--name",
            "Support Bot",
            "--owner",
            "ai-platform",
            "--repository",
            "https://example.test/support-bot",
            "--tags",
            "customer-facing,rag",
        ],
    )
    assert result.exit_code == 0, result.stdout
    assert "support-bot" in result.stdout

    duplicate = runner.invoke(
        app,
        ["applications", "register", "support-bot", "--name", "Duplicate"],
    )
    assert duplicate.exit_code == 1
    assert "already registered" in duplicate.stdout

    listed = runner.invoke(app, ["applications", "list"])
    assert listed.exit_code == 0
    assert "Support Bot" in listed.stdout
    assert "production" not in listed.stdout

    shown = runner.invoke(app, ["applications", "show", "support-bot"])
    assert shown.exit_code == 0
    assert "ai-platform" in shown.stdout
    assert "customer-facing" in shown.stdout
