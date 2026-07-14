"""Comprehensive unit tests for Niyam Autonomous Workspace Swarm (Swarm Mode).

Covers:
- Core lock lifecycle (acquire, release, contention)
- Ledger operations (append, load, multiple messages)
- Heartbeat and staleness detection
- Stale lock automatic recovery
- prune_stale_agents
- release_all_locks
- Edge cases: corrupt state, missing agents, reentrant locks
- Atomic write safety (os.replace path)
- Path normalization
- Multi-agent negotiation scenario
- CLI integration via Typer CliRunner
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from niyam.core.config import NIYAM_DIR
from niyam.core.swarm import (
    STALE_HEARTBEAT_TIMEOUT,
    SwarmAgent,
    SwarmState,
    ResourceLock,
    LedgerMessage,
    acquire_lock,
    release_lock,
    release_all_locks,
    load_swarm_state,
    save_swarm_state,
    append_ledger_message,
    load_ledger_messages,
    heartbeat,
    prune_stale_agents,
    is_agent_stale,
    get_swarm_dir,
    swarm_state_lock,
    _release_all_locks_internal,
)



# ── Concurrency Workers ────────────────────────────────────────────────

def _acquire_lock_worker(repo_root_path: str, resource: str, agent_id: str, success_flag: any) -> None:
    """Worker function for concurrent lock tests. Must be top-level for multiprocessing spawn."""
    root = Path(repo_root_path)
    res = acquire_lock(resource, agent_id, repo_root=root)
    success_flag.value = 1 if res else 0


def _state_lock_worker(repo_root_path: str, duration: float, success_flag: any, acquired_event: any) -> None:
    """Worker function to hold the state lock for a certain duration."""
    import time
    root = Path(repo_root_path)
    try:
        with swarm_state_lock(root, timeout=5):
            success_flag.value = 1
            acquired_event.set()
            time.sleep(duration)
    except Exception:
        success_flag.value = 0


def _short_timeout_worker(repo_root_path: str, success_flag: any, wait_event: any) -> None:
    """Worker function for short timeout state lock attempts."""
    import filelock
    root = Path(repo_root_path)
    # Wait for the lock to be acquired by the other process
    wait_event.wait(timeout=5)
    try:
        with swarm_state_lock(root, timeout=0.1):
            success_flag.value = 1
    except filelock.Timeout:
        success_flag.value = 0


# ── Fixtures ──────────────────────────────────────────────────────────


@pytest.fixture
def repo_root(tmp_path: Path) -> Path:
    """Create a temporary Niyam workspace."""
    (tmp_path / NIYAM_DIR).mkdir()
    return tmp_path


@pytest.fixture
def populated_state(repo_root: Path) -> Path:
    """Create a workspace with pre-registered agents."""
    heartbeat("agent-1", "backend", repo_root=repo_root)
    heartbeat("agent-2", "frontend", repo_root=repo_root)
    heartbeat("agent-3", "qa", repo_root=repo_root)
    return repo_root


# ══════════════════════════════════════════════════════════════════════
#  1. State Management
# ══════════════════════════════════════════════════════════════════════


class TestStateManagement:
    """Tests for SwarmState load/save and the swarm directory."""

    def test_get_swarm_dir_creates_directory(self, repo_root: Path) -> None:
        """get_swarm_dir should create .niyam/swarm/ if missing."""
        swarm_dir = get_swarm_dir(repo_root)
        assert swarm_dir.is_dir()
        assert swarm_dir == repo_root / NIYAM_DIR / "swarm"

    def test_load_empty_state(self, repo_root: Path) -> None:
        """Loading from a fresh workspace yields an empty SwarmState."""
        state = load_swarm_state(repo_root)
        assert state.agents == {}
        assert state.locks == {}

    def test_save_and_reload(self, repo_root: Path) -> None:
        """State should survive a save/load round-trip."""
        state = SwarmState()
        state.agents["a1"] = SwarmAgent(id="a1", role="test")
        state.locks["file.py"] = ResourceLock(
            resource_path="file.py", agent_id="a1"
        )
        save_swarm_state(state, repo_root)

        loaded = load_swarm_state(repo_root)
        assert "a1" in loaded.agents
        assert "file.py" in loaded.locks
        assert loaded.locks["file.py"].agent_id == "a1"

    def test_atomic_write_leaves_no_tmp(self, repo_root: Path) -> None:
        """save_swarm_state should clean up the .tmp file after atomic rename."""
        state = SwarmState()
        save_swarm_state(state, repo_root)
        swarm_dir = get_swarm_dir(repo_root)
        assert not (swarm_dir / "state.json.tmp").exists()
        assert (swarm_dir / "state.json").exists()

    def test_corrupt_state_returns_empty(self, repo_root: Path) -> None:
        """If state.json is corrupt, load_swarm_state returns empty state."""
        state_path = get_swarm_dir(repo_root) / "state.json"
        state_path.write_text("NOT VALID JSON {{{", encoding="utf-8")

        state = load_swarm_state(repo_root)
        assert state.agents == {}
        assert state.locks == {}

    def test_swarm_state_lock_context_manager(self, repo_root: Path) -> None:
        """The file lock context manager should be reentrant-safe."""
        # Just ensure it doesn't deadlock on single-thread usage
        with swarm_state_lock(repo_root):
            state = load_swarm_state(repo_root)
            assert isinstance(state, SwarmState)


# ══════════════════════════════════════════════════════════════════════
#  2. Lock Lifecycle
# ══════════════════════════════════════════════════════════════════════


class TestLockLifecycle:
    """Tests for acquire_lock, release_lock, and contention."""

    def test_acquire_and_release(self, populated_state: Path) -> None:
        """Basic acquire → release → verify cleared."""
        root = populated_state
        assert acquire_lock("api.py", "agent-1", repo_root=root) is True

        state = load_swarm_state(root)
        assert "api.py" in state.locks
        assert state.locks["api.py"].agent_id == "agent-1"

        assert release_lock("api.py", "agent-1", repo_root=root) is True

        state = load_swarm_state(root)
        assert "api.py" not in state.locks

    def test_contention_blocks_second_agent(self, populated_state: Path) -> None:
        """A second agent should be blocked from a held lock."""
        root = populated_state
        assert acquire_lock("api.py", "agent-1", repo_root=root) is True
        assert acquire_lock("api.py", "agent-2", repo_root=root) is False

    def test_reentrant_lock_same_agent(self, populated_state: Path) -> None:
        """Same agent acquiring same lock again should succeed (idempotent)."""
        root = populated_state
        assert acquire_lock("api.py", "agent-1", repo_root=root) is True
        assert acquire_lock("api.py", "agent-1", repo_root=root) is True

    def test_release_wrong_agent_fails(self, populated_state: Path) -> None:
        """An agent that doesn't hold the lock cannot release it."""
        root = populated_state
        acquire_lock("api.py", "agent-1", repo_root=root)
        assert release_lock("api.py", "agent-2", repo_root=root) is False

    def test_release_nonexistent_lock(self, populated_state: Path) -> None:
        """Releasing a lock that doesn't exist should return False."""
        root = populated_state
        assert release_lock("no-such-file.py", "agent-1", repo_root=root) is False

    def test_multiple_independent_locks(self, populated_state: Path) -> None:
        """Different agents can lock different files simultaneously."""
        root = populated_state
        assert acquire_lock("api.py", "agent-1", repo_root=root) is True
        assert acquire_lock("models.py", "agent-2", repo_root=root) is True
        assert acquire_lock("tests.py", "agent-3", repo_root=root) is True

        state = load_swarm_state(root)
        assert len(state.locks) == 3

    def test_lock_includes_reason(self, populated_state: Path) -> None:
        """Lock reason should be preserved in state."""
        root = populated_state
        acquire_lock("api.py", "agent-1", reason="Refactoring endpoints", repo_root=root)

        state = load_swarm_state(root)
        assert state.locks["api.py"].reason == "Refactoring endpoints"

    def test_lock_path_normalization(self, populated_state: Path) -> None:
        """Paths should be normalized to POSIX format for consistency."""
        root = populated_state
        # Use backslash-style path
        assert acquire_lock("src\\models\\user.py", "agent-1", repo_root=root) is True
        state = load_swarm_state(root)
        # Should be stored as posix
        assert "src/models/user.py" in state.locks


# ══════════════════════════════════════════════════════════════════════
#  3. Release All Locks
# ══════════════════════════════════════════════════════════════════════


class TestReleaseAllLocks:
    """Tests for release_all_locks and the internal helper."""

    def test_release_all_for_agent(self, populated_state: Path) -> None:
        """release_all_locks should free all locks held by a specific agent."""
        root = populated_state
        acquire_lock("a.py", "agent-1", repo_root=root)
        acquire_lock("b.py", "agent-1", repo_root=root)
        acquire_lock("c.py", "agent-2", repo_root=root)

        count = release_all_locks("agent-1", repo_root=root)
        assert count == 2

        state = load_swarm_state(root)
        assert len(state.locks) == 1
        assert "c.py" in state.locks

    def test_release_all_no_locks(self, populated_state: Path) -> None:
        """Releasing all locks when agent holds none should return 0."""
        root = populated_state
        count = release_all_locks("agent-1", repo_root=root)
        assert count == 0

    def test_internal_release_helper(self) -> None:
        """_release_all_locks_internal should mutate state in place."""
        state = SwarmState()
        state.locks["a.py"] = ResourceLock(resource_path="a.py", agent_id="x")
        state.locks["b.py"] = ResourceLock(resource_path="b.py", agent_id="x")
        state.locks["c.py"] = ResourceLock(resource_path="c.py", agent_id="y")

        removed = _release_all_locks_internal(state, "x")
        assert removed == 2
        assert len(state.locks) == 1
        assert "c.py" in state.locks


# ══════════════════════════════════════════════════════════════════════
#  4. Heartbeat & Staleness
# ══════════════════════════════════════════════════════════════════════


class TestHeartbeat:
    """Tests for heartbeat registration and staleness detection."""

    def test_heartbeat_registers_agent(self, repo_root: Path) -> None:
        """heartbeat should create or update an agent entry."""
        heartbeat("agent-1", "backend", status="busy", task_id="TASK-001", repo_root=repo_root)

        state = load_swarm_state(repo_root)
        assert "agent-1" in state.agents
        agent = state.agents["agent-1"]
        assert agent.role == "backend"
        assert agent.status == "busy"
        assert agent.current_task == "TASK-001"

    def test_heartbeat_updates_last_seen(self, repo_root: Path) -> None:
        """Subsequent heartbeats should refresh last_seen."""
        heartbeat("agent-1", "backend", repo_root=repo_root)
        state1 = load_swarm_state(repo_root)
        ts1 = state1.agents["agent-1"].last_seen

        heartbeat("agent-1", "backend", status="busy", repo_root=repo_root)
        state2 = load_swarm_state(repo_root)
        ts2 = state2.agents["agent-1"].last_seen

        # Timestamps should be different (or at least not older)
        assert ts2 >= ts1

    def test_fresh_agent_is_not_stale(self) -> None:
        """A just-created agent should not be stale."""
        agent = SwarmAgent(id="a1", role="test")
        assert is_agent_stale(agent) is False

    def test_old_agent_is_stale(self) -> None:
        """An agent with last_seen > STALE_HEARTBEAT_TIMEOUT ago is stale."""
        stale_time = datetime.now(timezone.utc) - timedelta(seconds=STALE_HEARTBEAT_TIMEOUT + 10)
        agent = SwarmAgent(id="a1", role="test", last_seen=stale_time.isoformat())
        assert is_agent_stale(agent) is True

    def test_borderline_not_stale(self) -> None:
        """An agent exactly at the timeout boundary should NOT be stale."""
        # Use timeout - 5 seconds to avoid test flakiness
        recent = datetime.now(timezone.utc) - timedelta(seconds=STALE_HEARTBEAT_TIMEOUT - 5)
        agent = SwarmAgent(id="a1", role="test", last_seen=recent.isoformat())
        assert is_agent_stale(agent) is False

    def test_invalid_timestamp_is_stale(self) -> None:
        """An agent with a malformed timestamp should be considered stale."""
        agent = SwarmAgent(id="a1", role="test", last_seen="NOT-A-TIMESTAMP")
        assert is_agent_stale(agent) is True

    def test_naive_timestamp_handled(self) -> None:
        """A naive (no timezone) timestamp should be handled gracefully."""
        # Old ISO format without tz info
        naive_recent = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
        agent = SwarmAgent(id="a1", role="test", last_seen=naive_recent)
        assert is_agent_stale(agent) is False


# ══════════════════════════════════════════════════════════════════════
#  5. Stale Lock Recovery
# ══════════════════════════════════════════════════════════════════════


class TestStaleLockRecovery:
    """Tests for automatic dead-agent lock recovery."""

    def test_stale_agent_lock_recovered(self, repo_root: Path) -> None:
        """acquire_lock should reclaim a lock from a stale agent."""
        # Agent 1 acquires lock
        heartbeat("agent-1", "backend", repo_root=repo_root)
        assert acquire_lock("api.py", "agent-1", repo_root=repo_root) is True

        # Make agent-1 stale
        state = load_swarm_state(repo_root)
        stale_time = datetime.now(timezone.utc) - timedelta(
            seconds=STALE_HEARTBEAT_TIMEOUT + 30
        )
        state.agents["agent-1"].last_seen = stale_time.isoformat()
        with swarm_state_lock(repo_root):
            save_swarm_state(state, repo_root)

        # Agent 2 should be able to acquire
        heartbeat("agent-2", "frontend", repo_root=repo_root)
        assert acquire_lock("api.py", "agent-2", repo_root=repo_root) is True

        # Verify ownership transferred
        state = load_swarm_state(repo_root)
        assert state.locks["api.py"].agent_id == "agent-2"

    def test_stale_recovery_releases_all_stale_locks(self, repo_root: Path) -> None:
        """When a stale agent's lock is recovered, ALL its locks are released."""
        heartbeat("agent-1", "backend", repo_root=repo_root)
        acquire_lock("a.py", "agent-1", repo_root=repo_root)
        acquire_lock("b.py", "agent-1", repo_root=repo_root)
        acquire_lock("c.py", "agent-1", repo_root=repo_root)

        # Make agent-1 stale
        state = load_swarm_state(repo_root)
        stale_time = datetime.now(timezone.utc) - timedelta(
            seconds=STALE_HEARTBEAT_TIMEOUT + 30
        )
        state.agents["agent-1"].last_seen = stale_time.isoformat()
        with swarm_state_lock(repo_root):
            save_swarm_state(state, repo_root)

        # Agent 2 acquires one of agent-1's locks, triggering recovery of ALL
        heartbeat("agent-2", "frontend", repo_root=repo_root)
        assert acquire_lock("a.py", "agent-2", repo_root=repo_root) is True

        state = load_swarm_state(repo_root)
        # a.py now held by agent-2, b.py and c.py released
        assert state.locks["a.py"].agent_id == "agent-2"
        assert "b.py" not in state.locks
        assert "c.py" not in state.locks

    def test_orphaned_lock_holder_not_in_agents(self, repo_root: Path) -> None:
        """Lock held by an agent not in the agents list should be treated as dead."""
        heartbeat("agent-2", "frontend", repo_root=repo_root)

        # Manually create a lock for an unknown agent
        state = load_swarm_state(repo_root)
        state.locks["file.py"] = ResourceLock(resource_path="file.py", agent_id="ghost-agent")
        with swarm_state_lock(repo_root):
            save_swarm_state(state, repo_root)

        # agent-2 should be able to acquire it
        assert acquire_lock("file.py", "agent-2", repo_root=repo_root) is True

        state = load_swarm_state(repo_root)
        assert state.locks["file.py"].agent_id == "agent-2"


# ══════════════════════════════════════════════════════════════════════
#  6. Prune Stale Agents
# ══════════════════════════════════════════════════════════════════════


class TestPruneStaleAgents:
    """Tests for prune_stale_agents."""

    def test_prune_removes_stale_agents(self, repo_root: Path) -> None:
        """Stale agents should be removed and their locks released."""
        heartbeat("agent-1", "backend", repo_root=repo_root)
        heartbeat("agent-2", "frontend", repo_root=repo_root)
        acquire_lock("api.py", "agent-1", repo_root=repo_root)

        # Make agent-1 stale
        state = load_swarm_state(repo_root)
        stale_time = datetime.now(timezone.utc) - timedelta(
            seconds=STALE_HEARTBEAT_TIMEOUT + 30
        )
        state.agents["agent-1"].last_seen = stale_time.isoformat()
        with swarm_state_lock(repo_root):
            save_swarm_state(state, repo_root)

        pruned = prune_stale_agents(repo_root)
        assert pruned == 1

        state = load_swarm_state(repo_root)
        assert "agent-1" not in state.agents
        assert "agent-2" in state.agents
        assert "api.py" not in state.locks

    def test_prune_no_stale(self, populated_state: Path) -> None:
        """Pruning with no stale agents should return 0."""
        assert prune_stale_agents(populated_state) == 0

    def test_prune_all_stale(self, repo_root: Path) -> None:
        """All stale agents should be pruned in one pass."""
        for i in range(5):
            heartbeat(f"agent-{i}", "worker", repo_root=repo_root)

        # Make all stale
        state = load_swarm_state(repo_root)
        stale_time = datetime.now(timezone.utc) - timedelta(
            seconds=STALE_HEARTBEAT_TIMEOUT + 30
        )
        for agent in state.agents.values():
            agent.last_seen = stale_time.isoformat()
        with swarm_state_lock(repo_root):
            save_swarm_state(state, repo_root)

        pruned = prune_stale_agents(repo_root)
        assert pruned == 5

        state = load_swarm_state(repo_root)
        assert len(state.agents) == 0


# ══════════════════════════════════════════════════════════════════════
#  7. Ledger Operations
# ══════════════════════════════════════════════════════════════════════


class TestLedgerOperations:
    """Tests for the append-only negotiation ledger."""

    def test_append_and_load_single(self, repo_root: Path) -> None:
        """Single message should round-trip through the ledger."""
        append_ledger_message(
            sender="agent-1",
            receiver="agent-2",
            action="request_lock",
            resource="api.py",
            repo_root=repo_root,
        )

        messages = load_ledger_messages(repo_root)
        assert len(messages) == 1
        assert messages[0].sender == "agent-1"
        assert messages[0].receiver == "agent-2"
        assert messages[0].action == "request_lock"
        assert messages[0].resource == "api.py"

    def test_append_multiple_messages(self, repo_root: Path) -> None:
        """Multiple messages should be appended in order."""
        for i in range(5):
            append_ledger_message(
                sender=f"agent-{i}",
                receiver=f"agent-{i+1}",
                action="info",
                payload={"index": i},
                repo_root=repo_root,
            )

        messages = load_ledger_messages(repo_root)
        assert len(messages) == 5
        for i, msg in enumerate(messages):
            assert msg.sender == f"agent-{i}"
            assert msg.payload["index"] == i

    def test_load_empty_ledger(self, repo_root: Path) -> None:
        """Loading from nonexistent ledger returns empty list."""
        assert load_ledger_messages(repo_root) == []

    def test_ledger_survives_corrupt_lines(self, repo_root: Path) -> None:
        """Corrupt lines in ledger should be skipped gracefully."""
        ledger_path = get_swarm_dir(repo_root) / "ledger.jsonl"

        append_ledger_message("a", "b", "info", repo_root=repo_root)

        # Inject a corrupt line
        with open(ledger_path, "a", encoding="utf-8") as f:
            f.write("NOT JSON\n")

        append_ledger_message("c", "d", "info", repo_root=repo_root)

        messages = load_ledger_messages(repo_root)
        assert len(messages) == 2
        assert messages[0].sender == "a"
        assert messages[1].sender == "c"

    def test_ledger_message_with_payload(self, repo_root: Path) -> None:
        """Messages with complex payloads should be preserved."""
        payload = {"priority": "high", "files": ["a.py", "b.py"], "nested": {"key": "val"}}
        append_ledger_message(
            sender="agent-1",
            receiver="agent-2",
            action="handoff",
            payload=payload,
            repo_root=repo_root,
        )

        messages = load_ledger_messages(repo_root)
        assert messages[0].payload == payload


# ══════════════════════════════════════════════════════════════════════
#  8. Pydantic Models
# ══════════════════════════════════════════════════════════════════════


class TestPydanticModels:
    """Validate Pydantic model defaults and serialization."""

    def test_swarm_agent_defaults(self) -> None:
        agent = SwarmAgent(id="a1", role="test")
        assert agent.status == "idle"
        assert agent.current_task is None
        assert agent.last_seen  # Should have a timestamp

    def test_resource_lock_defaults(self) -> None:
        lock = ResourceLock(resource_path="f.py", agent_id="a1")
        assert lock.reason is None
        assert lock.acquired_at  # Should have a timestamp

    def test_ledger_message_defaults(self) -> None:
        msg = LedgerMessage(sender="a", receiver="b", action="info")
        assert msg.resource is None
        assert msg.payload == {}
        assert msg.timestamp

    def test_swarm_state_defaults(self) -> None:
        state = SwarmState()
        assert state.agents == {}
        assert state.locks == {}


# ══════════════════════════════════════════════════════════════════════
#  9. End-to-End Multi-Agent Scenario
# ══════════════════════════════════════════════════════════════════════


class TestMultiAgentScenario:
    """Simulate a realistic multi-agent workflow."""

    def test_full_negotiation_flow(self, repo_root: Path) -> None:
        """Simulate the execution flow from the design doc."""
        # 1. Agent 1 (Codex) starts TASK-A and locks models.py and views.py
        heartbeat("codex-agent", "backend", status="busy", task_id="TASK-A", repo_root=repo_root)
        assert acquire_lock("models.py", "codex-agent", repo_root=repo_root) is True
        assert acquire_lock("views.py", "codex-agent", repo_root=repo_root) is True

        # 2. Agent 2 (Gemini) starts TASK-B and needs models.py → fails
        heartbeat("gemini-agent", "frontend", status="busy", task_id="TASK-B", repo_root=repo_root)
        assert acquire_lock("models.py", "gemini-agent", repo_root=repo_root) is False

        # 3. Agent 2 sends negotiation request
        append_ledger_message(
            sender="gemini-agent",
            receiver="codex-agent",
            action="request_lock",
            resource="models.py",
            repo_root=repo_root,
        )

        # 4. Agent 1 polls the ledger and sees the request
        messages = load_ledger_messages(repo_root)
        pending_for_codex = [m for m in messages if m.receiver == "codex-agent" and m.action == "request_lock"]
        assert len(pending_for_codex) == 1
        assert pending_for_codex[0].resource == "models.py"

        # 5. Agent 1 finishes and unlocks models.py
        assert release_lock("models.py", "codex-agent", repo_root=repo_root) is True

        # 6. Agent 1 appends yield_lock
        append_ledger_message(
            sender="codex-agent",
            receiver="gemini-agent",
            action="yield_lock",
            resource="models.py",
            repo_root=repo_root,
        )

        # 7. Agent 2 polls, sees yield, retries → succeeds
        messages = load_ledger_messages(repo_root)
        yields = [m for m in messages if m.receiver == "gemini-agent" and m.action == "yield_lock"]
        assert len(yields) == 1

        assert acquire_lock("models.py", "gemini-agent", repo_root=repo_root) is True

        # Final state: codex holds views.py, gemini holds models.py
        state = load_swarm_state(repo_root)
        assert state.locks["views.py"].agent_id == "codex-agent"
        assert state.locks["models.py"].agent_id == "gemini-agent"


# ══════════════════════════════════════════════════════════════════════
#  10. CLI Integration Tests
# ══════════════════════════════════════════════════════════════════════


class TestCLIIntegration:
    """Test CLI commands via Typer's CliRunner."""

    @pytest.fixture(autouse=True)
    def _patch_find_root(self, repo_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Patch find_niyam_root to return our temp dir."""
        monkeypatch.setattr(
            "niyam.cli.swarm.find_niyam_root",
            lambda: repo_root,
        )
        self.root = repo_root

    def _runner(self):
        from typer.testing import CliRunner
        from niyam.cli.swarm import swarm_app
        return CliRunner(), swarm_app

    def test_cli_init(self) -> None:
        runner, app = self._runner()
        result = runner.invoke(app, ["init"])
        assert result.exit_code == 0
        assert "initialized" in result.output.lower() or "✓" in result.output

    def test_cli_status_empty(self) -> None:
        runner, app = self._runner()
        result = runner.invoke(app, ["status"])
        assert result.exit_code == 0

    def test_cli_heartbeat(self) -> None:
        runner, app = self._runner()
        result = runner.invoke(app, [
            "heartbeat",
            "--agent", "agent-1",
            "--role", "backend",
            "--status", "idle",
        ])
        assert result.exit_code == 0
        assert "heartbeat" in result.output.lower() or "agent-1" in result.output

        # Verify state
        state = load_swarm_state(self.root)
        assert "agent-1" in state.agents

    def test_cli_lock_and_unlock(self) -> None:
        runner, app = self._runner()

        # Register agent first
        heartbeat("agent-1", "backend", repo_root=self.root)

        # Lock
        result = runner.invoke(app, [
            "lock", "api.py",
            "--agent", "agent-1",
            "--reason", "Refactoring",
        ])
        assert result.exit_code == 0
        assert "✓" in result.output

        state = load_swarm_state(self.root)
        assert "api.py" in state.locks

        # Unlock
        result = runner.invoke(app, [
            "unlock", "api.py",
            "--agent", "agent-1",
        ])
        assert result.exit_code == 0
        assert "✓" in result.output

        state = load_swarm_state(self.root)
        assert "api.py" not in state.locks

    def test_cli_lock_contention(self) -> None:
        runner, app = self._runner()
        heartbeat("agent-1", "backend", repo_root=self.root)
        heartbeat("agent-2", "frontend", repo_root=self.root)

        # Agent 1 locks
        runner.invoke(app, ["lock", "api.py", "--agent", "agent-1"])

        # Agent 2 fails to lock
        result = runner.invoke(app, ["lock", "api.py", "--agent", "agent-2"])
        assert result.exit_code == 1
        assert "✗" in result.output or "failed" in result.output.lower()

    def test_cli_force_lock(self) -> None:
        runner, app = self._runner()
        heartbeat("agent-1", "backend", repo_root=self.root)
        heartbeat("agent-2", "frontend", repo_root=self.root)

        runner.invoke(app, ["lock", "api.py", "--agent", "agent-1"])

        # Force lock by agent-2
        result = runner.invoke(app, ["lock", "api.py", "--agent", "agent-2", "--force"])
        assert result.exit_code == 0

        state = load_swarm_state(self.root)
        assert state.locks["api.py"].agent_id == "agent-2"

    def test_cli_force_unlock(self) -> None:
        runner, app = self._runner()
        heartbeat("agent-1", "backend", repo_root=self.root)

        acquire_lock("api.py", "agent-1", repo_root=self.root)

        # Force unlock by a different agent
        result = runner.invoke(app, ["unlock", "api.py", "--agent", "agent-2", "--force"])
        assert result.exit_code == 0
        assert "✓" in result.output

        state = load_swarm_state(self.root)
        assert "api.py" not in state.locks

    def test_cli_request_lock(self) -> None:
        runner, app = self._runner()
        result = runner.invoke(app, [
            "request-lock", "api.py",
            "--from", "agent-2",
            "--to", "agent-1",
        ])
        assert result.exit_code == 0
        assert "request" in result.output.lower() or "ℹ" in result.output

        messages = load_ledger_messages(self.root)
        assert len(messages) == 1
        assert messages[0].action == "request_lock"

    def test_cli_ledger_empty(self) -> None:
        runner, app = self._runner()
        result = runner.invoke(app, ["ledger"])
        assert result.exit_code == 0
        assert "no" in result.output.lower() or "No" in result.output

    def test_cli_ledger_with_entries(self) -> None:
        runner, app = self._runner()
        append_ledger_message("a", "b", "info", repo_root=self.root)
        result = runner.invoke(app, ["ledger"])
        assert result.exit_code == 0

    def test_cli_logs_alias(self) -> None:
        """'logs' command should behave identically to 'ledger'."""
        runner, app = self._runner()
        result = runner.invoke(app, ["logs"])
        assert result.exit_code == 0

    def test_cli_clean_no_stale(self) -> None:
        runner, app = self._runner()
        heartbeat("agent-1", "backend", repo_root=self.root)
        result = runner.invoke(app, ["clean"])
        assert result.exit_code == 0
        assert "no stale" in result.output.lower() or "No stale" in result.output

    def test_cli_clean_with_stale(self) -> None:
        runner, app = self._runner()
        heartbeat("agent-1", "backend", repo_root=self.root)

        # Make stale
        state = load_swarm_state(self.root)
        stale_time = datetime.now(timezone.utc) - timedelta(
            seconds=STALE_HEARTBEAT_TIMEOUT + 30
        )
        state.agents["agent-1"].last_seen = stale_time.isoformat()
        with swarm_state_lock(self.root):
            save_swarm_state(state, self.root)

        result = runner.invoke(app, ["clean"])
        assert result.exit_code == 0
        assert "1" in result.output
        assert "✓" in result.output

    def test_cli_status_shows_agents_and_locks(self) -> None:
        """Status should show registered agents and locks."""
        runner, app = self._runner()
        heartbeat("agent-1", "backend", status="busy", task_id="TASK-A", repo_root=self.root)
        acquire_lock("api.py", "agent-1", repo_root=self.root)

        result = runner.invoke(app, ["status"])
        assert result.exit_code == 0
        assert "agent-1" in result.output
        assert "api.py" in result.output

    def test_cli_outside_workspace(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """CLI commands should fail gracefully when run outside a workspace."""
        monkeypatch.setattr(
            "niyam.cli.swarm.find_niyam_root",
            lambda: None,
        )
        runner, app = self._runner()
        result = runner.invoke(app, ["status"])
        assert result.exit_code == 1
        assert "not a niyam workspace" in result.output.lower()

    def test_cli_force_lock_windows_path(self) -> None:
        runner, app = self._runner()
        heartbeat("agent-1", "backend", repo_root=self.root)
        heartbeat("agent-2", "frontend", repo_root=self.root)

        runner.invoke(app, ["lock", "src\\models\\user.py", "--agent", "agent-1"])

        # Force lock by agent-2 with Windows-style backslashes
        result = runner.invoke(app, ["lock", "src\\models\\user.py", "--agent", "agent-2", "--force"])
        assert result.exit_code == 0

        state = load_swarm_state(self.root)
        assert "src/models/user.py" in state.locks
        assert state.locks["src/models/user.py"].agent_id == "agent-2"

    def test_cli_force_unlock_windows_path(self) -> None:
        runner, app = self._runner()
        heartbeat("agent-1", "backend", repo_root=self.root)

        acquire_lock("src/models/user.py", "agent-1", repo_root=self.root)

        # Force unlock with Windows-style backslashes by another agent
        result = runner.invoke(app, ["unlock", "src\\models\\user.py", "--agent", "agent-2", "--force"])
        assert result.exit_code == 0
        assert "✓" in result.output

        state = load_swarm_state(self.root)
        assert "src/models/user.py" not in state.locks


# ══════════════════════════════════════════════════════════════════════
#  11. Concurrency and Multi-Process Safety
# ══════════════════════════════════════════════════════════════════════


class TestConcurrency:
    """Tests for multi-process safety and state locking."""

    def test_swarm_state_lock_timeout(self, repo_root: Path) -> None:
        """Locking should raise filelock.Timeout if already held by another context."""
        import filelock
        # Hold lock in one context with a short timeout
        with swarm_state_lock(repo_root, timeout=5):
            # Attempt to acquire again with a very short timeout should raise Timeout
            with pytest.raises(filelock.Timeout):
                with swarm_state_lock(repo_root, timeout=1):
                    pass

    def test_concurrent_lock_acquisition(self, repo_root: Path) -> None:
        """Test that only one process can acquire a contested lock concurrently."""
        from multiprocessing import Process, Value
        import time

        heartbeat("agent-1", "worker", repo_root=repo_root)
        heartbeat("agent-2", "worker", repo_root=repo_root)

        # Spawn two processes trying to lock the same resource
        # Using Value to store result
        success1 = Value("i", -1)
        success2 = Value("i", -1)

        p1 = Process(target=_acquire_lock_worker, args=(str(repo_root), "api.py", "agent-1", success1))
        p2 = Process(target=_acquire_lock_worker, args=(str(repo_root), "api.py", "agent-2", success2))

        p1.start()
        p2.start()
        p1.join()
        p2.join()

        # One should have succeeded (value == 1) and the other failed (value == 0)
        results = {success1.value, success2.value}
        assert results == {0, 1}

    def test_concurrent_state_lock_exclusion(self, repo_root: Path) -> None:
        """Test that the state lock provides mutual exclusion across processes."""
        from multiprocessing import Process, Value, Event
        import time

        flag1 = Value("i", -1)
        flag2 = Value("i", -1)
        acquired_event = Event()

        # Process 1 acquires and holds state lock for 0.5s
        p1 = Process(target=_state_lock_worker, args=(str(repo_root), 0.5, flag1, acquired_event))
        
        # Process 2 will attempt to acquire with a very short timeout of 0.1s
        # (It should fail because Process 1 holds the lock)
        p2 = Process(target=_short_timeout_worker, args=(str(repo_root), flag2, acquired_event))

        p1.start()
        p2.start()
        p1.join()
        p2.join()

        assert flag1.value == 1  # P1 successfully got lock and held it
        assert flag2.value == 0  # P2 failed due to timeout

