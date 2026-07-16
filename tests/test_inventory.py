"""Tests for versioned model, prompt, and data inventory."""

from pathlib import Path

from typer.testing import CliRunner

from niyam.cli import app
from niyam.core.applications import register_application
from niyam.core.graph import get_relationships
from niyam.core.inventory import load_inventory, register_inventory_object


def test_inventory_objects_are_versioned_and_graph_linked(tmp_path: Path) -> None:
    register_application("support-bot", name="Support Bot", root=tmp_path)

    for object_type in (
        "model",
        "prompt",
        "dataset",
        "vector-store",
        "knowledge-base",
    ):
        record = register_inventory_object(
            object_type,
            f"support-{object_type}",
            name=f"Support {object_type}",
            version="v1",
            application_id="support-bot",
            root=tmp_path,
        )
        assert record.version == "v1"

    inventory = load_inventory(tmp_path)
    assert inventory.schema_version == "1.0.0"
    assert len(inventory.objects) == 5
    assert {
        edge.target_type
        for edge in get_relationships("application", "support-bot", root=tmp_path)
    } == {"model", "prompt", "dataset", "vector-store", "knowledge-base"}


def test_inventory_cli_register_list_and_show(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".niyam").mkdir()
    register_application("support-bot", name="Support Bot", root=tmp_path)
    runner = CliRunner()

    registered = runner.invoke(
        app,
        [
            "inventory",
            "register",
            "model",
            "support-model",
            "--name",
            "Support Model",
            "--version",
            "2026-07",
            "--owner",
            "ml-platform",
            "--location",
            "vertex://support-model",
            "--application",
            "support-bot",
        ],
    )
    assert registered.exit_code == 0, registered.stdout

    listed = runner.invoke(app, ["inventory", "list", "--type", "model"])
    assert listed.exit_code == 0
    assert "Support Model" in listed.stdout

    shown = runner.invoke(app, ["inventory", "show", "model:support-model"])
    assert shown.exit_code == 0
    assert "2026-07" in shown.stdout
    assert "vertex://support-model" in shown.stdout
