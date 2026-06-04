# Niyam Guardrail & Audit Log System (`niyam guard`)

> [!WARNING]
> The guardrail system and command logging wrapper are currently **experimental**. Interception patterns and configurations may be modified in future releases.

Niyam Guard provides security, safety policies, and local logging to govern AI agent behaviors. It supports active restrictions as well as passive observation modes.

---

## 1. Guard Commands

The `niyam guard` suite provides commands to manage policies and wrap execution:

| Command | Type | Description |
| --- | --- | --- |
| `niyam guard enable` | Configuration | Enables all policy checks and guardrails. |
| `niyam guard disable` | Configuration | Disables policy checks and guardrails. |
| `niyam guard careful` | Configuration | Warns on destructive shell commands. |
| `niyam guard freeze <path>` | Configuration | Restricts edits to a specific folder or file path. |
| `niyam guard run -- <cmd>`| Execution Wrap | Executes a command under passive observation. |
| `niyam guard status` | Audit | Displays active configuration and audit metrics. |
| `niyam guard logs` | Audit | Outputs a list of recently observed commands. |

---

## 2. Guard Observe Mode (`niyam guard run`)

When executing tasks or tests, AI agents or human developers can run commands wrapped by the guard auditor:

```bash
# Passive observation of command runs
niyam guard run -- npm test

# Capture command outputs (stdout/stderr) inside audit logs
niyam guard run --capture-output -- python script.py
```

### Log Storage Schema
Execution logs are stored locally in JSON Lines (JSONL) format at:
```
.niyam/logs/guard-actions.jsonl
```

Each log entry includes:
- `timestamp`: ISO 8601 UTC timestamp.
- `session_id`: Session ID derived from Git branch or the `NIYAM_SESSION_ID` environment variable.
- `actor_type`: Type of actor (`human`, `agent`, or `unknown`).
- `tool`: Client tool type, default is `shell`.
- `action`: Specific action type (`command_execute`).
- `command`: The executed shell command.
- `cwd`: Absolute path of the working directory.
- `exit_code`: The command exit code (e.g. `0` for success).
- `duration_ms`: Duration of the command run in milliseconds.
- `mode`: Constant value `"observe"`.

---

## 3. Secret Redaction & Security

Before writing to local logs, the `guard run` command engine automatically filters out secrets and credentials:
- **Environment and Command Redaction:** Command arguments are matched against credentials regexes (AWS keys, generic tokens, password properties). Matching sub-strings are replaced with `REDACTED`.
- **No stdout Capture by Default:** Command outputs are skipped unless `--capture-output` is explicitly provided.
- **Local Isolation:** Logs are kept entirely local; no remote SaaS queries are made.
