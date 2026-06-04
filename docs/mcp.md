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
| `niyam mcp risk-report` | Performs a security assessment of all tools based on risk heuristics. |

---

## 2. Registering a Tool

To register a tool, specify its name and type. You can also specify owner, capabilities, and approved status:

```bash
# Register a filesystem MCP server with high risk
niyam mcp register filesystem \
  --type mcp_server \
  --command-or-url "npx -y @modelcontextprotocol/server-filesystem /path/to/project" \
  --risk high \
  --approved true \
  --capabilities "read_file,write_file,list_dir" \
  --data-access "Local project files" \
  --notes "Enables file operations for the agent."

# Register a browser-use utility
niyam mcp register browser \
  --type browser \
  --risk critical \
  --notes "Agent browser interaction."
```

### Supported Tool Types
- `mcp_server`: Model Context Protocol server.
- `api`: External web service/API endpoint.
- `cli`: Shell executable command.
- `local_tool`: Custom python/JS helper scripts.
- `browser`: GUI or headless browser driver.
- `other`: Generic tool description.

---

## 3. Heuristic Risk Classification

If `--risk` is omitted during registration, Niyam evaluates the tool's capabilities, description, commands, and type to heuristically assign a risk level:

| Risk Level | Heuristic Indicator / Condition | Typical Tools |
| --- | --- | --- |
| **Critical** | Contains shell execution, bash commands, or raw command line access | `bash`, `cmd`, `execute_command` |
| **High** | Requires filesystem writes, database modifications, or root privileges | `filesystem`, `db-write`, `sqlite` |
| **Medium** | Connects to standard cloud APIs, remote repos, or read-only databases | `github-api`, `jira-server`, `slack` |
| **Low** | Read-only local document databases, search engines, or static APIs | `google-search`, `tavily`, `read-only-docs` |

---

## 4. Local Storage Structure

The registry database is written locally in JSON format at:
```
.niyam/mcp-registry.json
```

### JSON Registry Schema
```json
{
  "version": 1,
  "tools": {
    "filesystem": {
      "name": "filesystem",
      "type": "mcp_server",
      "command_or_url": "npx -y @modelcontextprotocol/server-filesystem /path/to/project",
      "owner": "Niyam Team",
      "risk_level": "high",
      "approved": true,
      "capabilities": ["read_file", "write_file", "list_dir"],
      "data_access": "Local project files",
      "notes": "Enables file operations for the agent."
    }
  }
}
```
No credentials or access tokens are stored in the registry; only configuration descriptors are retained.
