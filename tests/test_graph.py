"""Tests for the local Niyam relationship graph."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from niyam.cli import app
from niyam.core.applications import register_application
from niyam.core.graph import get_relationships, link_objects, load_graph


def test_graph_links_and_queries_application_relationships(tmp_path: Path) -> None:
    register_application("support-bot", name="Support Bot", root=tmp_path)

    edge = link_objects(
        "application",
        "support-bot",
        "uses",
        "model",
        "gpt-5",
        root=tmp_path,
    )
    link_objects(
        "application",
        "support-bot",
        "uses",
        "model",
        "gpt-5",
        root=tmp_path,
    )

    assert edge.target_id == "gpt-5"
    assert get_relationships("application", "support-bot", root=tmp_path) == [edge]
    assert len(load_graph(tmp_path).relationships) == 1

    with pytest.raises(ValueError, match="not registered"):
        link_objects(
            "application",
            "missing-app",
            "uses",
            "model",
            "gpt-5",
            root=tmp_path,
        )


def test_graph_cli_link_and_show(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".niyam").mkdir()
    register_application("support-bot", name="Support Bot", root=tmp_path)
    runner = CliRunner()

    linked = runner.invoke(
        app,
        ["graph", "link", "application:support-bot", "uses", "model:gpt-5"],
    )
    assert linked.exit_code == 0, linked.stdout

    shown = runner.invoke(app, ["graph", "show", "application:support-bot"])
    assert shown.exit_code == 0
    assert "uses" in shown.stdout
    assert "model:gpt-5" in shown.stdout
