# Niyam Tool & MCP Server Registry (`niyam mcp`)

> [!WARNING]
> The Tool & MCP Registry capability is currently **experimental**. Database structures and risk classification heuristics are subject to change in upcoming releases.

AI coding agents use external CLI tools, web APIs, browser utilities, and Model Context Protocol (MCP) servers to interact with your codebase and system. Niyam MCP provides a local registry to declare, audit, and verify the risk posture of these tools.

---

## 1. Registry Commands

Manage your tool catalog using the `niyam mcp` commands:

| Command | Description |
| --- | --- |
| `niyam mcp register <name>` | Adds/updates a tool or MCP server in the registry. |
| `niyam mcp list` | Displays all registered tools in a summary table. |
| `niyam mcp show <name>` | Displays detailed parameters, capabilities, and notes for a tool. |
| `niyam mcp approve <name>` | Approves a registered tool or MCP server for usage. |
| `niyam mcp risk-report` | Performs a security assessment of all tools, highlighting high/critical unapproved tools. |

---

## 2. Registering a Tool

To register a tool, specify its name and type. You can also specify owner, capabilities, risk, approval requirements, and notes:

```bash
# Register a filesystem MCP server with high risk
niyam mcp register filesystem \
  --type mcp_server \
  --command-or-url "npx -y @modelcontextprotocol/server-filesystem /path/to/project" \
  --risk high \
  --approved false \
  --capability file_read \
  --capability file_write \
  --network-access "localhost only" \
  --requires-approval true \
  --data-access "Local project files" \
  --notes "Enables file operations for the agent."

# Register a shell utility (which defaults to critical risk)
niyam mcp register shell \
  --type local_tool \
  --approved false \
  --capability shell_execute

# Update an existing registration
niyam mcp register filesystem \
  --type mcp_server \
  --notes "Updated filesystem access description" \
  --update
```

### Options for `niyam mcp register`
- `--type`: Type of tool (e.g. `mcp_server`, `api`, `cli`, `local_tool`, `browser`, `other`). Required for new registrations.
- `--command-or-url`: Command or URL for the tool.
- `--owner`: Owner of the tool.
- `--risk`: Risk level: `low`/`medium`/`high`/`critical`. If omitted, the heuristic is used.
- `--approved`: Sets whether the tool is approved (`true`/`false`). Can also be passed as `--no-approved`.
- `--capabilities`: Comma-separated list of capabilities.
- `--capability`: Individual capability of the tool. Can be specified multiple times.
- `--data-access`: Data access details.
- `--network-access`: Network access details.
- `--requires-approval`: Sets whether the tool requires approval (`true`/`false`). Can also be passed as `--no-requires-approval`.
- `--notes`: Notes/description of the tool.
- `--update`: Updates the tool if it is already registered. If not set, registering a duplicate name will fail.

---

## 3. Risk Classification v1

When registering a tool, Niyam maps the tool's explicit capabilities directly to risk levels. If explicit capabilities are not provided, Niyam evaluates the tool's description, commands, and type to heuristically assign a risk level.

### Direct Capability Mapping

| Capability | Risk Level | Description |
| --- | --- | --- |
| `production_deploy` | **Critical** | Commands that perform live production deployments. |
| `secrets_access` | **Critical** | Access to environment variables, API keys, or keystores. |
| `cloud_api` | **Critical** | Direct cloud API access (AWS, GCP, Azure, Kubernetes). |
| `shell_execute` | **Critical** | Ability to execute arbitrary shell/bash commands. |
| `file_write` | **High** | Writes, modifies, or deletes files on the filesystem. |
| `docs_read` | **Medium** | Reads local documentation files, wikis, or readmes. |
| `repo_read` | **Medium** | Reads repository files (source code, commits, configuration). |
| `public_search` | **Low** | Performs web search or fetches from public indexes. |

*For tools with multiple capabilities, the final risk level is the highest of the individual capability risk levels.*

---

## 4. Local Storage Structure & Secret Redaction

The registry database is written locally in JSON format at:
```
.niyam/mcp-registry.json
```

### Secret Redaction
To ensure credential hygiene, Niyam passes the entire registry dataset through its secret redaction engine before writing to disk. Any strings resembling API keys (e.g. `sk-ant-...`), passwords, database connection strings, or JWTs are automatically replaced with `[REDACTED_SECRET]`.

### Sample Registry JSON
```json
{
  "schema_version": "1.0.0",
  "tools": {
    "filesystem": {
      "schema_version": "1.0.0",
      "name": "filesystem",
      "type": "mcp_server",
      "command_or_url": "npx -y @modelcontextprotocol/server-filesystem /path/to/project",
      "owner": "Niyam Team",
      "risk_level": "high",
      "approved": false,
      "capabilities": [
        "file_read",
        "file_write"
      ],
      "data_access": "Local project files",
      "network_access": "localhost only",
      "requires_approval": true,
      "notes": "Enables file operations for the agent.",
      "created_at": "2026-06-05T10:00:00Z",
      "updated_at": "2026-06-05T10:00:00Z"
    },
    "external-api": {
      "schema_version": "1.0.0",
      "name": "external-api",
      "type": "api",
      "command_or_url": "https://api.example.com?key=[REDACTED_SECRET]",
      "owner": "Dev Team",
      "risk_level": "medium",
      "approved": true,
      "capabilities": [
        "public_search"
      ],
      "data_access": "API lookup",
      "network_access": "internet",
      "requires_approval": true,
      "notes": "Queries external index.",
      "created_at": "2026-06-05T10:05:00Z",
      "updated_at": "2026-06-05T10:06:00Z"
    }
  }
}
```

---

## 5. Enterprise Approval Pattern

In a governed enterprise setting, developers or agents register the tools they plan to use. By default, tools with `requires_approval: true` (especially those with **High** or **Critical** risk levels) are registered as `approved: false`.

An administrator or automated CI/CD pipeline reviews the unapproved tools using the `niyam mcp risk-report` command:

```bash
# Output lists all unapproved High/Critical tools
niyam mcp risk-report
```

After verifying the command/URL, owner, and capabilities of the tool, the administrator approves it:

```bash
niyam mcp approve filesystem
```

This updates `approved` to `true` and updates `updated_at`, authorizing the agent runtime to execute the tool under policy constraints.

