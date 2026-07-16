"""Tests for source-linked local architecture inventory."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from niyam.cli import app
from niyam.core.architecture import build_architecture_inventory


SOURCE = """\
from fastapi import FastAPI
import jwt
import requests
import sqlite3

app = FastAPI()

@app.get("/users")
def users(token: str):
    claims = jwt.decode(token, "key")
    response = requests.get("https://directory.example/users")
    database = sqlite3.connect("users.db")
    database.execute("insert into audit values (?)", (response.status_code,))
    return claims
"""


def test_build_architecture_inventory_with_source_locations(tmp_path: Path) -> None:
    (tmp_path / "service.py").write_text(SOURCE, encoding="utf-8")
    (tmp_path / "broken.py").write_text("def nope(:\n", encoding="utf-8")

    inventory = build_architecture_inventory(tmp_path)

    assert inventory.schema_version == "1.0.0"
    assert any(item.name == "FastAPI" for item in inventory.services)
    assert any(item.name == "requests.get" for item in inventory.external_calls)
    assert any(item.name == "jwt.decode" for item in inventory.identity_boundaries)
    assert any(item.name == "sqlite3.connect" for item in inventory.storage)
    assert any(
        flow.function == "users"
        and "external_call" in flow.sources
        and "storage" in flow.sinks
        for flow in inventory.data_flows
    )
    assert all(item.file_path == "service.py" for item in inventory.external_calls)
    assert all(item.line > 0 for item in inventory.external_calls)
    assert inventory.parse_errors == ["broken.py"]


def test_architecture_cli_scan_and_show(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".niyam").mkdir()
    (tmp_path / "service.py").write_text(SOURCE, encoding="utf-8")
    runner = CliRunner()

    scanned = runner.invoke(app, ["architecture", "scan", "."])
    assert scanned.exit_code == 0, scanned.stdout
    assert "Architecture inventory saved" in scanned.stdout

    output = tmp_path / ".niyam" / "architecture.json"
    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["services"][0]["file_path"] == "service.py"

    shown = runner.invoke(app, ["architecture", "show"])
    assert shown.exit_code == 0
    assert "FastAPI" in shown.stdout
    assert "requests.get" in shown.stdout
