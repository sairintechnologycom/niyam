"""Tests for Phase D MCP-compatible Memory Ledger server."""

from __future__ import annotations

import json
from io import StringIO
from datetime import datetime, timezone
from pathlib import Path

from typer.testing import CliRunner

from niyam.cli import app
from niyam.core.memory import get_memory_dir
from niyam.core.memory_ledger.lineage import LocalMemoryLineageStore
from niyam.core.memory_ledger.local_store import LocalMemoryLedgerStore
from niyam.core.memory_ledger.models import MemoryRecord
from niyam.core.mcp import load_mcp_registry
from niyam.mcp.memory_server import MemoryMCPServer, run_stdio_server

runner = CliRunner()


def _workspace(tmp_path: Path, monkeypatch) -> Path:
    monkeypatch.chdir(tmp_path)
    niyam_dir = tmp_path / ".niyam"
    niyam_dir.mkdir()
    (niyam_dir / "niyam.yaml").write_text("version: 1.0.0-rc1\n", encoding="utf-8")
    return tmp_path


def _tool_text(response: dict) -> dict:
    return json.loads(response["result"]["content"][0]["text"])


def test_memory_mcp_initialize_and_tool_list(tmp_path: Path, monkeypatch) -> None:
    root = _workspace(tmp_path, monkeypatch)
    server = MemoryMCPServer(root)

    init_response = server.handle_request(
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
    )
    assert init_response is not None
    assert init_response["result"]["serverInfo"]["name"] == "niyam-memory-ledger"

    tools_response = server.handle_request(
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
    )
    assert tools_response is not None
    tool_names = {tool["name"] for tool in tools_response["result"]["tools"]}
    assert {
        "memory.create",
        "memory.search",
        "memory.recall",
        "memory.update",
        "memory.delete",
        "memory.export",
        "memory.trace",
        "memory.policy_check",
    }.issubset(tool_names)


def test_memory_mcp_create_recall_trace_and_export(
    tmp_path: Path, monkeypatch
) -> None:
    root = _workspace(tmp_path, monkeypatch)
    server = MemoryMCPServer(root)

    create_response = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "memory.create",
                "arguments": {
                    "id": "mem-mcp-1",
                    "content": "Terraform deploy preference",
                    "type": "preference",
                    "tags": ["terraform"],
                },
            },
        }
    )
    assert create_response is not None
    created = _tool_text(create_response)
    assert created["record"]["id"] == "mem-mcp-1"

    store = LocalMemoryLedgerStore(get_memory_dir(root) / "index.jsonl")
    assert store.list_records()[0].content == "Terraform deploy preference"

    recall_response = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "memory.recall",
                "arguments": {"query": "terraform"},
            },
        }
    )
    assert recall_response is not None
    recalled = _tool_text(recall_response)
    assert recalled["records"][0]["id"] == "mem-mcp-1"

    trace_response = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "memory.trace", "arguments": {"id": "mem-mcp-1"}},
        }
    )
    assert trace_response is not None
    events = _tool_text(trace_response)["events"]
    assert {event["event_type"] for event in events} == {"created", "recalled"}

    export_response = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {"name": "memory.export", "arguments": {}},
        }
    )
    assert export_response is not None
    assert _tool_text(export_response)["records"][0]["id"] == "mem-mcp-1"


def test_memory_mcp_update_delete_and_policy_check(
    tmp_path: Path, monkeypatch
) -> None:
    root = _workspace(tmp_path, monkeypatch)
    store = LocalMemoryLedgerStore(get_memory_dir(root) / "index.jsonl")
    store.append(
        MemoryRecord(
            id="mem-mcp-2",
            type="note",
            content="User-scoped memory",
            scope="user",
            created_at=datetime.now(timezone.utc),
        )
    )
    server = MemoryMCPServer(root)

    policy_response = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": "memory.policy_check", "arguments": {}},
        }
    )
    assert policy_response is not None
    findings = _tool_text(policy_response)["findings"]
    assert findings[0]["code"] == "MEM001"

    update_response = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "memory.update",
                "arguments": {
                    "id": "mem-mcp-2",
                    "fields": {"content": "Project memory", "scope": "project"},
                },
            },
        }
    )
    assert update_response is not None
    assert _tool_text(update_response)["record"]["content"] == "Project memory"

    delete_response = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "memory.delete", "arguments": {"id": "mem-mcp-2"}},
        }
    )
    assert delete_response is not None
    assert _tool_text(delete_response)["deleted"] is True
    assert store.list_records() == []

    lineage = LocalMemoryLineageStore(
        get_memory_dir(root) / "lineage" / "recall-events.jsonl"
    )
    event_types = [
        event.event_type for event in lineage.get_events_for_record("mem-mcp-2")
    ]
    assert event_types == ["updated", "deleted"]


def test_mcp_register_memory_server_command(tmp_path: Path, monkeypatch) -> None:
    root = _workspace(tmp_path, monkeypatch)

    result = runner.invoke(app, ["mcp", "register-memory-server"])
    assert result.exit_code == 0
    assert "Memory MCP server" in result.stdout

    registry = load_mcp_registry(root)
    tool = registry.tools["niyam-memory-ledger"]
    assert tool.type == "mcp_server"
    assert tool.command_or_url == "niyam memory serve-mcp"
    assert "memory.recall" in tool.capabilities
    assert tool.approved is True

    duplicate = runner.invoke(app, ["mcp", "register-memory-server"])
    assert duplicate.exit_code == 1
    assert "already registered" in duplicate.stdout

    update = runner.invoke(app, ["mcp", "register-memory-server", "--update"])
    assert update.exit_code == 0


def test_memory_mcp_stdio_server_round_trip(tmp_path: Path, monkeypatch) -> None:
    root = _workspace(tmp_path, monkeypatch)
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "params": {},
    }
    stdout = StringIO()

    run_stdio_server(root, stdin=StringIO(json.dumps(request) + "\n"), stdout=stdout)

    response = json.loads(stdout.getvalue())
    assert response["id"] == 1
    assert response["result"]["tools"][0]["name"] == "memory.create"
