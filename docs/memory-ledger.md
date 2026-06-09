# Memory Ledger

Niyam provides a structured memory ledger designed for storing, diffing, and validating persistent AI memory cross-session.

## Core Concepts

The Memory Ledger (Phase B) moves from a pure markdown and loosely-coupled JSONL index to a formalized Pydantic model (`MemoryRecord`).

### MemoryRecord

The schema ensures consistency across all agents.

```json
{
  "id": "mem-20260609...",
  "type": "note",
  "content": "A crucial project lesson",
  "scope": "project",
  "source_kind": "manual",
  "created_at": "2026-06-09T10:00:00Z"
}
```

### Supported Commands

- `niyam memory init`: Initialize the local store at `.niyam/memory/index.jsonl`.
- `niyam memory list`: List all memory records in the ledger.
- `niyam memory validate`: Validate all records against the `MemoryRecord` schema.
- `niyam memory export --format json|yaml -o file`: Export records to a JSON or YAML manifest.
- `niyam memory import file`: Import records from a manifest.
- `niyam memory diff file1 file2`: Show added, removed, and changed records between manifests.
- `niyam memory redact`: Redact sensitive values from structured records.
- `niyam memory policy-check`: Evaluate records against local memory policy.
- `niyam memory recall`: Recall matching records and append recall lineage.
- `niyam memory trace`: Inspect lineage for a record.
- `niyam memory serve-mcp`: Start the local MCP-compatible Memory Ledger server.

The existing markdown files continue to function, and `niyam memory add` automatically writes a valid `MemoryRecord` to the ledger.

## MCP Server

The Phase D MCP server exposes Memory Ledger operations to MCP-compatible
clients over stdio:

```bash
niyam memory serve-mcp
niyam mcp register-memory-server
```

See [mcp-memory-server.md](mcp-memory-server.md) for tool names and client
integration details.
