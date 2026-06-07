# Phase 12: Autonomous Workspace Swarm (Swarm Mode) Design

## 1. Overview
The Autonomous Workspace Swarm (Swarm Mode) enables multiple AI coding agents (Claude, Codex, Gemini, etc.) to collaborate on the same project simultaneously. It provides coordination mechanisms to prevent file edit collisions, track agent statuses, and allow agents to negotiate access to shared resources.

This phase builds upon the existing primitive state management in `niyam/core/swarm.py` and elevates it to a robust, concurrent-safe orchestration layer.

## 2. State Management & Concurrency
The swarm state is tracked in a local JSON file (`.niyam/swarm/state.json`). Because multiple independent agent processes may read and write to this file simultaneously, race conditions must be prevented.

**Design Decision:**
- **Concurrency Control:** We will introduce standard file locking (e.g., using the `filelock` package or a custom robust lockfile implementation) around all reads and writes to `state.json`.
- **Atomic Writes:** State updates will write to a temporary file and use atomic `os.replace` alongside the file lock to ensure the state file is never corrupted if a process crashes mid-write.

## 3. Locking Primitives & Dead Agent Recovery
Agents acquire exclusive locks on files (defined in their task's `allowed_files`) before making modifications.

**Enhancements:**
- **Heartbeat Expiration:** Define a `STALE_HEARTBEAT_TIMEOUT` (e.g., 60 seconds). Agents must call `heartbeat()` periodically.
- **Automatic Recovery:** When an agent calls `acquire_lock(resource)`, the engine will check the heartbeat of the current lock holder. If the holder's `last_seen` timestamp is older than the timeout, the engine will **automatically release all locks** held by the dead agent and grant the lock to the new requester.
- **Lock Expirations (Optional):** Locks themselves can have an explicit timeout, acting as a safeguard against runaway agent tasks.

## 4. Negotiation Protocol (Ledger)
When Agent A needs a file currently locked by Agent B, they must negotiate. Niyam uses an append-only ledger (`.niyam/swarm/ledger.jsonl`) for inter-agent communication.

**Message Types:**
- `request_lock(resource)`: Agent A requests access to a locked resource.
- `yield_lock(resource)`: Agent B grants the request and releases the lock.
- `deny_lock(resource, reason)`: Agent B cannot yield the lock immediately.

**Agent Integration (Polling):**
- Niyam will rely on a **Polling** mechanism for negotiation.
- The `task_runner` will periodically poll the ledger (e.g., between file edit operations or validation steps).
- If the runner detects a `request_lock` message directed at the current agent, it can surface this to the agent's context (e.g., "Another agent needs `api.py`. Can you yield it soon?").
- The agent decides when to safely flush changes and call `niyam swarm unlock` (which implicitly acts as a `yield`).

## 5. CLI Interface Enhancements
The `niyam/cli/swarm.py` will be enhanced to manage the swarm lifecycle and provide visibility:

- `niyam swarm init`: Initialize the `.niyam/swarm` directory and ledger.
- `niyam swarm status`: 
  - Enhance the table to clearly mark dead/stale agents in red.
  - Show negotiation requests pending in the ledger.
- `niyam swarm clean`: Manually prune dead agents and release their locks, compacting the state.
- `niyam swarm lock/unlock`: Add a `--force` flag for administrative overrides.
- `niyam swarm ledger`: (Alias for `logs`) Display the negotiation history.

## 6. Execution Flow Example
1. Agent 1 (Codex) starts TASK-A and locks `models.py` and `views.py`.
2. Agent 2 (Gemini) starts TASK-B and needs `models.py`. `acquire_lock` fails.
3. Agent 2 executes `niyam swarm request-lock models.py --to agent-1`.
4. Agent 1 polls the ledger, sees the request.
5. Agent 1 finishes modifying `models.py`, saves, and runs `niyam swarm unlock models.py`.
6. Agent 1 appends `yield_lock` to the ledger.
7. Agent 2 polls the ledger, sees the yield, retries `acquire_lock`, succeeds, and proceeds.
