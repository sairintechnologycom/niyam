"""MCP-compatible stdio server for the Niyam Memory Ledger."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from niyam.core.memory import get_memory_dir
from niyam.core.memory_ledger.lineage import (
    LocalMemoryLineageStore,
    create_lineage_event,
)
from niyam.core.memory_ledger.local_store import LocalMemoryLedgerStore
from niyam.core.memory_ledger.models import MemoryRecord
from niyam.core.memory_ledger.policy import load_policy, run_policy_check
from niyam.core.memory_ledger.recall import recall_records

SERVER_NAME = "niyam-memory-ledger"
SERVER_VERSION = "1.0.0"


def _json_safe(value: Any) -> Any:
    """Convert Pydantic models and datetimes to JSON-compatible values."""
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json", exclude_none=True)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    return value


class MemoryMCPServer:
    """Local MCP tool adapter backed by the Memory Ledger JSONL store."""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.memory_dir = get_memory_dir(repo_root)
        self.store = LocalMemoryLedgerStore(self.memory_dir / "index.jsonl")
        self.lineage = LocalMemoryLineageStore(
            self.memory_dir / "lineage" / "recall-events.jsonl"
        )

    def tool_names(self) -> list[str]:
        """Return supported MCP tool names."""
        return [tool["name"] for tool in self.list_tools()]

    def list_tools(self) -> list[dict[str, Any]]:
        """Return MCP tool definitions for Memory Ledger operations."""
        return [
            {
                "name": "memory.create",
                "description": "Create a governed Memory Ledger record.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "type": {
                            "type": "string",
                            "enum": [
                                "semantic",
                                "episodic",
                                "procedural",
                                "preference",
                                "note",
                            ],
                        },
                        "content": {"type": "string"},
                        "summary": {"type": "string"},
                        "scope": {
                            "type": "string",
                            "enum": ["user", "project", "workspace", "organization"],
                        },
                        "source_kind": {
                            "type": "string",
                            "enum": [
                                "manual",
                                "conversation",
                                "document",
                                "tool_call",
                                "agent_task",
                                "import",
                            ],
                        },
                        "source_ref": {"type": "string"},
                        "confidence": {"type": "number"},
                        "tags": {"type": "array", "items": {"type": "string"}},
                        "metadata": {"type": "object"},
                    },
                    "required": ["content"],
                    "additionalProperties": False,
                },
            },
            {
                "name": "memory.search",
                "description": "Search Memory Ledger records without recording recall lineage.",
                "inputSchema": self._query_schema(),
            },
            {
                "name": "memory.recall",
                "description": "Recall Memory Ledger records and record recall lineage.",
                "inputSchema": self._query_schema(),
            },
            {
                "name": "memory.update",
                "description": "Update an existing Memory Ledger record.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "fields": {"type": "object"},
                    },
                    "required": ["id", "fields"],
                    "additionalProperties": False,
                },
            },
            {
                "name": "memory.delete",
                "description": "Delete a Memory Ledger record by id.",
                "inputSchema": {
                    "type": "object",
                    "properties": {"id": {"type": "string"}},
                    "required": ["id"],
                    "additionalProperties": False,
                },
            },
            {
                "name": "memory.export",
                "description": "Export Memory Ledger records as JSON-compatible data.",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False,
                },
            },
            {
                "name": "memory.trace",
                "description": "Return lineage events for a Memory Ledger record.",
                "inputSchema": {
                    "type": "object",
                    "properties": {"id": {"type": "string"}},
                    "required": ["id"],
                    "additionalProperties": False,
                },
            },
            {
                "name": "memory.policy_check",
                "description": "Evaluate Memory Ledger records against memory policy.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "policy_path": {"type": "string"},
                    },
                    "additionalProperties": False,
                },
            },
        ]

    def _query_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "limit": {"type": "integer", "minimum": 1},
                "scope": {
                    "type": "string",
                    "enum": ["user", "project", "workspace", "organization"],
                },
            },
            "required": ["query"],
            "additionalProperties": False,
        }

    def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> Any:
        """Dispatch a Memory Ledger MCP tool call."""
        arguments = arguments or {}
        if name == "memory.create":
            return self.create(arguments)
        if name == "memory.search":
            return self.search(arguments, trace=False)
        if name == "memory.recall":
            return self.search(arguments, trace=True)
        if name == "memory.update":
            return self.update(arguments)
        if name == "memory.delete":
            return self.delete(arguments)
        if name == "memory.export":
            return self.export()
        if name == "memory.trace":
            return self.trace(arguments)
        if name == "memory.policy_check":
            return self.policy_check(arguments)
        raise ValueError(f"Unknown memory tool: {name}")

    def create(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """Create a Memory Ledger record."""
        now = datetime.now(timezone.utc)
        record_data = {
            "id": arguments.get("id") or now.strftime("mem-%Y%m%d%H%M%S%f"),
            "type": arguments.get("type", "note"),
            "content": arguments["content"],
            "summary": arguments.get("summary"),
            "scope": arguments.get("scope", "project"),
            "source_kind": arguments.get("source_kind", "tool_call"),
            "source_ref": arguments.get("source_ref"),
            "confidence": arguments.get("confidence"),
            "created_at": now,
            "tags": arguments.get("tags", []),
            "metadata": arguments.get("metadata", {}),
        }
        record = MemoryRecord.model_validate(record_data)
        self.store.append(record)
        self.lineage.append(
            create_lineage_event(
                "created",
                record_id=record.id,
                actor="mcp",
                source_ref=record.source_ref,
                reason="Created through MCP memory server",
            )
        )
        return {"record": _json_safe(record)}

    def search(self, arguments: dict[str, Any], *, trace: bool) -> dict[str, Any]:
        """Search or recall records."""
        records = self.store.list_records()
        results = recall_records(
            records,
            arguments["query"],
            limit=arguments.get("limit"),
            scope=arguments.get("scope"),
        )
        if trace:
            for record in results:
                self.lineage.append(
                    create_lineage_event(
                        "recalled",
                        record_id=record.id,
                        actor="mcp",
                        reason=f"Recalled by query: {arguments['query']}",
                    )
                )
        return {"records": _json_safe(results)}

    def update(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """Update a record by id."""
        record_id = arguments["id"]
        fields = arguments["fields"]
        if not isinstance(fields, dict):
            raise ValueError("fields must be an object")

        allowed_fields = set(MemoryRecord.model_fields) - {
            "id",
            "created_at",
            "schema_version",
        }
        invalid_fields = sorted(set(fields) - allowed_fields)
        if invalid_fields:
            raise ValueError(f"Unsupported update fields: {', '.join(invalid_fields)}")

        records = self.store.list_records()
        updated_record: MemoryRecord | None = None
        new_records: list[MemoryRecord] = []
        for record in records:
            if record.id != record_id:
                new_records.append(record)
                continue
            data = record.model_dump()
            data.update(fields)
            data["updated_at"] = datetime.now(timezone.utc)
            updated_record = MemoryRecord.model_validate(data)
            new_records.append(updated_record)

        if updated_record is None:
            raise ValueError(f"Memory record not found: {record_id}")

        self.store.replace_all(new_records)
        self.lineage.append(
            create_lineage_event(
                "updated",
                record_id=record_id,
                actor="mcp",
                reason="Updated through MCP memory server",
                metadata={"fields": sorted(fields)},
            )
        )
        return {"record": _json_safe(updated_record)}

    def delete(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """Delete a record by id."""
        record_id = arguments["id"]
        records = self.store.list_records()
        remaining = [record for record in records if record.id != record_id]
        if len(remaining) == len(records):
            raise ValueError(f"Memory record not found: {record_id}")

        self.store.replace_all(remaining)
        self.lineage.append(
            create_lineage_event(
                "deleted",
                record_id=record_id,
                actor="mcp",
                reason="Deleted through MCP memory server",
            )
        )
        return {"deleted": True, "id": record_id}

    def export(self) -> dict[str, Any]:
        """Export all records as JSON-compatible data."""
        return {"records": _json_safe(self.store.list_records())}

    def trace(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """Return lineage events for a record."""
        events = self.lineage.get_events_for_record(arguments["id"])
        return {"events": _json_safe(events)}

    def policy_check(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """Run policy checks for all records."""
        policy_path = arguments.get("policy_path")
        if policy_path:
            policy = load_policy(Path(policy_path))
        else:
            policy = load_policy(self.memory_dir / "policies" / "memory-policy.yaml")
        findings = run_policy_check(self.store.list_records(), policy)
        return {"findings": _json_safe(findings)}

    def handle_request(self, request: dict[str, Any]) -> dict[str, Any] | None:
        """Handle a JSON-RPC MCP request."""
        request_id = request.get("id")
        method = request.get("method")
        try:
            if method == "initialize":
                result = {
                    "protocolVersion": "2024-11-05",
                    "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
                    "capabilities": {"tools": {}},
                }
            elif method == "tools/list":
                result = {"tools": self.list_tools()}
            elif method == "tools/call":
                params = request.get("params") or {}
                tool_result = self.call_tool(
                    params["name"],
                    params.get("arguments") or {},
                )
                result = {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(_json_safe(tool_result), indent=2),
                        }
                    ],
                    "isError": False,
                }
            elif method in {"notifications/initialized", "$/cancelRequest"}:
                return None
            else:
                return self._error_response(
                    request_id,
                    -32601,
                    f"Unknown method: {method}",
                )

            return {"jsonrpc": "2.0", "id": request_id, "result": result}
        except (KeyError, TypeError, ValidationError, ValueError) as e:
            return self._error_response(request_id, -32602, str(e))
        except Exception as e:
            return self._error_response(request_id, -32603, str(e))

    def _error_response(
        self, request_id: Any, code: int, message: str
    ) -> dict[str, Any]:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": code, "message": message},
        }


def run_stdio_server(repo_root: Path, stdin: Any = None, stdout: Any = None) -> None:
    """Run the Memory Ledger MCP server over newline-delimited JSON-RPC stdio."""
    stdin = stdin or sys.stdin
    stdout = stdout or sys.stdout
    server = MemoryMCPServer(repo_root)
    server.store.init_store()
    server.lineage.init_store()

    for line in stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
            response = server.handle_request(request)
        except json.JSONDecodeError as e:
            response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": f"Parse error: {e}"},
            }

        if response is not None:
            stdout.write(json.dumps(response, separators=(",", ":")) + "\n")
            stdout.flush()


def main() -> None:
    """CLI entry point for `python -m niyam.mcp.memory_server`."""
    repo_root = Path.cwd()
    run_stdio_server(repo_root)


if __name__ == "__main__":
    main()
