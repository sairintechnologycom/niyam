# Niyam Control Room

Niyam Control Room is a governed workspace for supervised agent tasks. It provides the backend primitives for creating task sessions, appending action timeline events, modeling approval gates, and exporting task evidence. 

## Overview

The Control Room serves as an extension of the existing mission, portal, guard, swarm, and evidence foundations. It tracks operations performed by agents and humans in a structured format, enabling auditability and rollback transparency.

### Components

- **Sessions:** Track high-level task status, risk level, objective, and references to memory and evidence.
- **Timelines:** Append-only JSONL files capturing individual actions (e.g., `prompt`, `tool_call`, `command`, `approval_request`, `status_change`).
- **Approvals:** Gated actions that require a human decision (`approved` or `rejected`) before proceeding.
- **Evidence:** Session export containing summaries of actions, pending approvals, and redacted security-sensitive content.

## Commands

### Session Management

- `niyam workspace create "Research competitor pricing"`: Start a new supervised task room.
- `niyam workspace list`: List all known sessions.
- `niyam workspace show TASK-001`: Inspect the state of a specific session.
- `niyam workspace pause TASK-001`: Pause execution for a running session.
- `niyam workspace resume TASK-001`: Resume a paused session.

### Timeline Logging

- `niyam workspace log TASK-001 --type prompt --actor human --input "..."`: Append an action to a session's timeline.

### Approvals

- `niyam workspace request-approval TASK-001 --action submit-form --risk high --reason "External write"`: Flag a required approval for an action.
- `niyam workspace approve TASK-001 --approval APPROVAL-ID --by USER`: Grant the requested approval.
- `niyam workspace reject TASK-001 --approval APPROVAL-ID --by USER`: Deny the requested approval.

### Auditing & Evidence

- `niyam workspace timeline TASK-001`: View the full timeline of actions in a session.
- `niyam workspace evidence TASK-001 --format markdown|json`: Export session metadata and timeline records.

### Browser Sandbox (Phase F)

The Control Room supports sandboxed browser sessions for supervised tasks:

- `niyam workspace browser-start TASK-001 --url https://example.com`: Start a tracked browser session.
- `niyam workspace browser-action TASK-001 --type navigate --target "https://example.com/pricing"`: Log a browser action.
- `niyam workspace browser-pause TASK-001`: Pause the browser session.
- `niyam workspace browser-resume TASK-001`: Resume the browser session.

#### Human Takeover

- `niyam workspace takeover TASK-001 --by USER`: Flag that a human has taken control of the session.
- `niyam workspace release TASK-001 --by USER`: Return the session to agent control.

## Storage
All Control Room data resides in the local `.niyam/workspace/` directory:
- `.niyam/workspace/sessions/`
- `.niyam/workspace/timelines/`
- `.niyam/workspace/approvals/`
- `.niyam/workspace/browser/` (Phase F)
- `.niyam/workspace/artifacts/` (Phase F)

## Next Steps (Phase G)
Control Room data is now available through opt-in evidence reports:

```bash
niyam evidence --include scan,guard,mcp,cost,memory,workspace
```

The workspace section summarizes session status, pending approvals, browser
activity, takeover state, high-risk actions, and recent sessions. Portal/API
work should consume this read-only data shape before adding any write paths.
