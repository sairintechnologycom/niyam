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

Each log entry conforms to the following schema:
- `schema_version`: String version identifier (e.g., `"1.0.0"`).
- `timestamp`: ISO 8601 UTC timestamp.
- `session_id`: Unique session ID generated per session (includes Git branch prefix if available, followed by a unique UUID).
- `actor_type`: Normalized actor type (`human`, `agent`, or `unknown`).
- `tool`: Client tool type, default is `"shell"`.
- `action`: Specific action type (`"command_execute"`).
- `command`: The executed shell command (redacted).
- `cwd`: Absolute path of the working directory.
- `exit_code`: The command exit code (e.g., `0` for success).
- `duration_ms`: Duration of the command run in milliseconds.
- `mode`: The active guard mode (e.g., `"observe"`).
- `policy_decision`: The governance policy classification decision (e.g., `"allowed"`, `"blocked"`, `"denied"`, `"warned"`, `"approved"`).

---

## 3. Secret Redaction & Security

Before writing to local logs, the `guard run` command engine enforces strict security constraints:
- **Environment Variable Protection:** Environment variable values (such as `os.environ` contents) are never captured or recorded in logs.
- **Robust Secret Redaction:** Command strings and captured outputs (if `--capture-output` is enabled) are parsed and redacted using the centralized Niyam redaction library. This matches and redacts OpenAI, Anthropic, GitHub PATs, AWS credentials, JWTs, Database connection URLs, and generic credential patterns.
- **No File Content Storage:** File contents are never stored in the logged output or command context.
- **No stdout Capture by Default:** Command stdout/stderr outputs are entirely skipped unless the `--capture-output` flag is explicitly passed.
- **Local Isolation:** The engine runs completely offline. No external APIs or SaaS endpoints are contacted.

---

## 4. Guard Policy Modes & Configuration

Niyam Guard supports four active policy modes to control risk and secure the development environment:

### Policy Modes
1. **`observe`**: Passive monitoring. Flagged commands are logged, but execution proceeds unrestricted.
2. **`warn`**: Warns the user on the console when a risky command matches policy rules, but allows it to execute.
3. **`block`**: Prevents the execution of risky commands matching blocklist rules, exiting immediately with exit code 1.
4. **`approval`**: Prompts the user on the CLI for manual confirmation before execution.

### Config Example (`.niyam/niyam.yaml`)
To enforce policies, configure the `governance` block in your workspace:
```yaml
governance:
  guard:
    mode: warn
    blocked_commands:
      - "rm -rf"
      - "terraform destroy"
      - "kubectl delete"
    protected_files:
      - ".env"
      - ".env.local"
      - "secrets.json"
    approval_required:
      - "terraform apply"
      - "az ad"
      - "aws iam"
```

### CLI Override
You can override the workspace's configured mode on a per-run basis using the `--mode` flag:
```bash
niyam guard run --mode block -- terraform destroy
```

---

## 5. Safe Enterprise Rollout Strategy

To successfully implement guardrails in enterprise teams without disrupting developer workflows, we recommend a phased rollout strategy:

1. **Phase 1: Observe (Audit Only)**
   - Set `mode: observe` in the shared Niyam configuration.
   - Passive logging runs in the background to collect command metrics and identify typical developer command execution profiles.
2. **Phase 2: Warn (Visibility & Education)**
   - Transition to `mode: warn`.
   - Provide warning banners to developers when high-risk commands are executed, helping build security awareness.
3. **Phase 3: Approval / Block (Active Enforcement)**
   - Transition critical systems or high-risk rules to `mode: approval` or `mode: block`.
   - Block dangerous operations (like `rm -rf`) entirely, while requiring human confirmation for sensitive infrastructure tasks (like `terraform apply`).
