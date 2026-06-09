# MCP Memory Server

Phase D adds a local MCP-compatible stdio server for the Niyam Memory Ledger.
It exposes governed memory operations to MCP clients without adding a hosted
service or external database.

## Start the Server

```bash
niyam memory serve-mcp
```

The server reads and writes the current workspace's local ledger:

```text
.niyam/memory/index.jsonl
.niyam/memory/lineage/recall-events.jsonl
```

Use `--root` when the client launches the server outside the workspace:

```bash
niyam memory serve-mcp --root /path/to/workspace
```

## Register with Niyam

Register the server in the existing MCP/tool registry:

```bash
niyam mcp register-memory-server
```

This creates a registry entry equivalent to:

```bash
niyam mcp register niyam-memory-ledger \
  --type mcp_server \
  --command-or-url "niyam memory serve-mcp" \
  --risk medium \
  --approved true \
  --capability memory.create \
  --capability memory.search \
  --capability memory.recall \
  --capability memory.update \
  --capability memory.delete \
  --capability memory.export \
  --capability memory.trace \
  --capability memory.policy_check
```

## Supported Tools

| Tool | Purpose |
| --- | --- |
| `memory.create` | Create a structured memory record. |
| `memory.search` | Search records without recording recall lineage. |
| `memory.recall` | Search records and append recall lineage events. |
| `memory.update` | Update mutable fields on an existing record. |
| `memory.delete` | Delete a record and append deletion lineage. |
| `memory.export` | Return all records as JSON-compatible data. |
| `memory.trace` | Return lineage events for a record. |
| `memory.policy_check` | Run Memory Ledger policy checks. |

## MCP Shape

The server supports JSON-RPC over stdio:

- `initialize`
- `tools/list`
- `tools/call`
- `notifications/initialized`

Tool call results are returned as MCP text content containing JSON.

## Validation

```bash
pytest tests/test_mcp_memory_server.py tests/test_memory_ledger.py tests/test_memory_policy.py tests/test_memory_recall.py tests/test_mcp.py
```
