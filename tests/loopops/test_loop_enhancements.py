from __future__ import annotations

import json
import os
from pathlib import Path
from unittest import mock
import pytest
import yaml
from typer.testing import CliRunner

from niyam.cli import app
from niyam.core.loopops import LoopRunner, LoopSpec, validate_loop_spec
from niyam.core.loopops.state_machine import LoopRun
from niyam.core.loopops.validate import check_runtime_drift
from niyam.core.memory import CodebaseIndexer
from niyam.core.identity import verify_signature


def test_loop_memory_loading(tmp_path: Path) -> None:
    """Verify that memories are loaded from .niyam/memory and passed to adapters."""
    # Write a test memory file
    memory_dir = tmp_path / ".niyam" / "memory"
    memory_dir.mkdir(parents=True, exist_ok=True)
    (memory_dir / "instructions.md").write_text("Use Python 3.14 features.", encoding="utf-8")

    spec_data = {
        "apiVersion": "niyam.dev/v1",
        "kind": "LoopSpec",
        "metadata": {
            "name": "mem-test-loop",
            "owner": "platform",
            "riskTier": "low"
        },
        "goal": {
            "type": "testing",
            "description": "Orchestration testing for instructions"
        },
        "actors": {
            "planner": "claude"
        },
        "budgets": {
            "maxIterations": 1
        },
        "steps": [
            {
                "name": "plan",
                "actor": "planner",
                "action": "plan_steps"
            }
        ]
    }
    spec = LoopSpec.model_validate(spec_data)

    # Let's mock get_adapter to return a mock adapter that checks context
    mock_adapter = mock.MagicMock()
    mock_adapter.plan.return_value = mock.MagicMock(
        status="passed",
        cost_usd=0.0,
        tokens_in=0,
        tokens_out=0,
        files_changed=[],
        commands_run=[],
        evidence_artifacts=[]
    )

    with mock.patch("niyam.core.loopops.adapters.get_adapter", return_value=mock_adapter):
        run, reason = LoopRunner.run_loop(spec, repo_root=tmp_path)
        
    assert run.status == "passed"
    # Verify that plan was called with req containing loaded memories
    args, kwargs = mock_adapter.plan.call_args
    req = args[0]
    assert "Use Python 3.14 features." in req.context["memories"][0]


def test_fallback_codebase_indexing(tmp_path: Path) -> None:
    """Verify that CodebaseIndexer falls back to JSONL when chroma is disabled."""
    # Setup test file to index
    src_dir = tmp_path / "src"
    src_dir.mkdir(exist_ok=True)
    (src_dir / "app.py").write_text("print('hello world')", encoding="utf-8")

    # Disable chroma
    with mock.patch.dict(os.environ, {"NIYAM_DISABLE_CHROMA": "1"}):
        indexer = CodebaseIndexer(tmp_path)
        count = indexer.build_index()
        assert count > 0

        # Verify codebase-index.jsonl was created
        index_file = tmp_path / ".niyam" / "db" / "codebase-index.jsonl"
        assert index_file.exists()

        # Query indexer and verify fallback search returns match
        matches = indexer.search("hello")
        assert len(matches) > 0
        assert "hello world" in matches[0]["text"]


def test_swarm_lock_enforcement(tmp_path: Path) -> None:
    """Verify that swarm locks prevent concurrent writes and stop the loop run."""
    spec_data = {
        "apiVersion": "niyam.dev/v1",
        "kind": "LoopSpec",
        "metadata": {
            "name": "lock-test-loop",
            "owner": "platform",
            "riskTier": "low"
        },
        "goal": {
            "type": "testing",
            "description": "Locking target file src/app.py"
        },
        "actors": {
            "implementer": "claude"
        },
        "budgets": {
            "maxIterations": 1
        },
        "steps": [
            {
                "name": "implement",
                "actor": "implementer",
                "action": "implement_feature"
            }
        ]
    }
    spec = LoopSpec.model_validate(spec_data)

    # Mock acquire_lock to simulate resource is locked by another process
    with mock.patch("niyam.core.swarm.acquire_lock", return_value=False):
        run, reason = LoopRunner.run_loop(spec, repo_root=tmp_path)

    assert run.status == "failed"
    assert "Blocked by swarm lock" in reason


def test_stale_agent_cleanup(tmp_path: Path) -> None:
    """Verify stale heartbeats/agents are pruned at run start."""
    from niyam.core.swarm import heartbeat, prune_stale_agents, load_swarm_state, save_swarm_state

    # Create stale heartbeat in state file
    heartbeat(
        agent_id="stale-agent",
        role="planner",
        status="idle",
        task_id="LR-STALE",
        repo_root=tmp_path
    )

    # Modify state to set last_seen in the past
    state = load_swarm_state(tmp_path)
    assert "stale-agent" in state.agents
    state.agents["stale-agent"].last_seen = "2026-06-11T12:00:00Z"
    save_swarm_state(state, tmp_path)

    # Run prune_stale_agents and verify the stale agent is removed
    prune_stale_agents(tmp_path)
    state_cleaned = load_swarm_state(tmp_path)
    assert "stale-agent" not in state_cleaned.agents


def test_fleet_wave_execution(tmp_path: Path) -> None:
    """Verify that fleet wave dependencies are resolved and runs parallel waves."""
    # Write a fleet configuration file
    fleet_file = tmp_path / "niyam-fleet.yaml"
    
    # Create sub-repositories
    repo1 = tmp_path / "repo1"
    repo2 = tmp_path / "repo2"
    repo1.mkdir()
    repo2.mkdir()
    
    # Setup .niyam in each repo
    (repo1 / ".niyam").mkdir()
    (repo2 / ".niyam").mkdir()

    fleet_data = {
        "repos": [
            {
                "path": str(repo1.absolute()),
                "alias": "repo1",
                "depends_on": ["repo2"]
            },
            {
                "path": str(repo2.absolute()),
                "alias": "repo2",
                "depends_on": []
            }
        ]
    }
    fleet_file.write_text(yaml.dump(fleet_data), encoding="utf-8")

    # Write a loop spec to test with
    spec_file = tmp_path / "loop-spec.yaml"
    spec_yaml = """
apiVersion: niyam.dev/v1
kind: LoopSpec
metadata:
  name: fleet-test-loop
  owner: platform
actors:
  planner: claude
goal:
  type: testing
  description: Fleet deployment
budgets:
  maxIterations: 1
steps:
  - name: plan
    actor: planner
    action: plan
"""
    spec_file.write_text(spec_yaml, encoding="utf-8")

    # Run the loop CLI using CliRunner with --fleet
    runner = CliRunner()
    with mock.patch.dict(os.environ, {"NIYAM_FLEET_CONFIG": str(fleet_file)}):
        # Mock LoopRunner.run_loop to avoid executing real adapters
        mock_run = LoopRun(
            id="LR-FLEET1",
            specName="fleet-test-loop",
            goal="Fleet deployment",
            status="passed",
            startedAt="2026-06-18T10:00:00Z",
            maxIterations=1,
            costUsd=0.0
        )
        with mock.patch("niyam.core.loopops.runner.LoopRunner.run_loop", return_value=(mock_run, "Success")):
            result = runner.invoke(app, ["loop", "run", str(spec_file), "--fleet"])
            assert result.exit_code == 0
            assert "Executing Fleet Wave" in result.stdout
            assert "Repo: repo1" in result.stdout
            assert "Repo: repo2" in result.stdout


def test_hook_enforcement(tmp_path: Path) -> None:
    """Verify hook configuration file cache is enabled/disabled during loop run."""
    spec_data = {
        "apiVersion": "niyam.dev/v1",
        "kind": "LoopSpec",
        "metadata": {
            "name": "hook-test-loop",
            "owner": "platform",
            "riskTier": "low"
        },
        "goal": {
            "type": "testing",
            "description": "Interception test"
        },
        "actors": {
            "planner": "claude"
        },
        "budgets": {
            "maxIterations": 1
        },
        "steps": [
            {
                "name": "plan",
                "actor": "planner",
                "action": "plan"
            }
        ]
    }
    spec = LoopSpec.model_validate(spec_data)

    mock_adapter = mock.MagicMock()
    mock_adapter.plan.return_value = mock.MagicMock(status="passed")

    # Intercept while running loop to see if guard-config.json was set to guard_enabled=True
    guard_config_file = tmp_path / ".niyam" / "hook-cache" / "guard-config.json"
    
    def check_guard_config(*args, **kwargs):
        assert guard_config_file.exists()
        g_config = json.loads(guard_config_file.read_text(encoding="utf-8"))
        assert g_config["guard_enabled"] is True
        return mock.MagicMock(
            status="passed",
            cost_usd=0.0,
            tokens_in=0,
            tokens_out=0,
            files_changed=[],
            commands_run=[],
            evidence_artifacts=[]
        )

    mock_adapter.plan.side_effect = check_guard_config

    with mock.patch("niyam.core.loopops.adapters.get_adapter", return_value=mock_adapter):
        run, reason = LoopRunner.run_loop(spec, repo_root=tmp_path, mode="governed")

    assert run.status == "passed"
    # Ensure config cache is restored/removed after run
    assert not guard_config_file.exists()


def test_cryptographic_signing(tmp_path: Path) -> None:
    """Verify that LoopRun data is signed and can be verified via its public key."""
    spec_data = {
        "apiVersion": "niyam.dev/v1",
        "kind": "LoopSpec",
        "metadata": {
            "name": "sign-test-loop",
            "owner": "platform",
            "riskTier": "low"
        },
        "goal": {
            "type": "testing",
            "description": "Signing test"
        },
        "actors": {
            "planner": "claude"
        },
        "budgets": {
            "maxIterations": 2
        },
        "steps": [
            {
                "name": "plan",
                "actor": "planner",
                "action": "plan"
            }
        ]
    }
    spec = LoopSpec.model_validate(spec_data)

    mock_adapter = mock.MagicMock()
    mock_adapter.plan.return_value = mock.MagicMock(
        status="passed",
        cost_usd=0.5,
        tokens_in=100,
        tokens_out=200,
        files_changed=["src/main.py"],
        commands_run=["git status"],
        evidence_artifacts=[]
    )

    with mock.patch("niyam.core.loopops.adapters.get_adapter", return_value=mock_adapter):
        run, reason = LoopRunner.run_loop(spec, repo_root=tmp_path)

    # Verification
    assert run.status == "passed"
    assert run.signature is not None
    assert run.public_key_pem is not None

    # Load run.json and verify using niyam.core.identity.verify_signature
    evidence_dir = tmp_path / run.evidence_path
    run_json_path = evidence_dir / "run.json"
    assert run_json_path.exists()

    run_data = json.loads(run_json_path.read_text(encoding="utf-8"))
    sig = run_data.pop("signature")
    pub_pem = run_data.pop("publicKeyPem")
    serialized = json.dumps(run_data, sort_keys=True)

    assert verify_signature(serialized, sig, pub_pem.encode("utf-8")) is True


def test_config_drift_detection(tmp_path: Path) -> None:
    """Verify configuration drift warnings for CLAUDE.md and GEMINI.md."""
    # Write a mocked CLAUDE.md with drifted content
    (tmp_path / "CLAUDE.md").write_text("drifted content here", encoding="utf-8")

    # Run check_runtime_drift and verify it warns
    warnings = check_runtime_drift(tmp_path)
    assert len(warnings) > 0
    assert "CLAUDE.md configuration drift detected" in warnings[0]


def test_loop_replay(tmp_path: Path) -> None:
    """Verify replaying a loop run from signed evidence works without invoking adapters."""
    # First, run a normal loop to write signed evidence
    spec_data = {
        "apiVersion": "niyam.dev/v1",
        "kind": "LoopSpec",
        "metadata": {
            "name": "replay-test-loop",
            "owner": "platform",
            "riskTier": "low"
        },
        "goal": {
            "type": "testing",
            "description": "Replay verification"
        },
        "actors": {
            "planner": "claude"
        },
        "budgets": {
            "maxIterations": 1
        },
        "steps": [
            {
                "name": "plan",
                "actor": "planner",
                "action": "plan"
            }
        ]
    }
    spec = LoopSpec.model_validate(spec_data)

    mock_adapter = mock.MagicMock()
    mock_adapter.plan.return_value = mock.MagicMock(
        status="passed",
        cost_usd=0.0,
        tokens_in=0,
        tokens_out=0,
        files_changed=[],
        commands_run=[],
        evidence_artifacts=[]
    )

    with mock.patch("niyam.core.loopops.adapters.get_adapter", return_value=mock_adapter):
        run, reason = LoopRunner.run_loop(spec, repo_root=tmp_path)

    assert run.status == "passed"
    evidence_dir = tmp_path / run.evidence_path

    # Replay it
    # Mock get_adapter to ensure it is NEVER called during replay
    with mock.patch("niyam.core.loopops.adapters.get_adapter") as mock_get_adapter:
        replayed_run, replayed_reason = LoopRunner.replay_loop(evidence_dir)
        mock_get_adapter.assert_not_called()

    assert replayed_run.id == run.id
    assert replayed_run.status == "passed"


def test_missing_evidence_fails_replay(tmp_path: Path) -> None:
    """Verify that replaying with missing evidence (e.g. no iterations) fails replay."""
    spec_data = {
        "apiVersion": "niyam.dev/v1",
        "kind": "LoopSpec",
        "metadata": {
            "name": "missing-ev-loop",
            "owner": "platform",
            "riskTier": "low"
        },
        "goal": {
            "type": "testing",
            "description": "Missing evidence testing"
        },
        "actors": {
            "planner": "claude"
        },
        "budgets": {
            "maxIterations": 1
        },
        "steps": [
            {
                "name": "plan",
                "actor": "planner",
                "action": "plan"
            }
        ]
    }
    spec = LoopSpec.model_validate(spec_data)

    mock_adapter = mock.MagicMock()
    mock_adapter.plan.return_value = mock.MagicMock(
        status="passed",
        cost_usd=0.0,
        tokens_in=0,
        tokens_out=0,
        files_changed=[],
        commands_run=[],
        evidence_artifacts=[]
    )

    with mock.patch("niyam.core.loopops.adapters.get_adapter", return_value=mock_adapter):
        run, reason = LoopRunner.run_loop(spec, repo_root=tmp_path)

    evidence_dir = tmp_path / run.evidence_path
    
    # Delete iterations folder to trigger missing evidence failure during replay
    import shutil
    shutil.rmtree(evidence_dir / "iterations")

    with pytest.raises(ValueError) as exc:
        LoopRunner.replay_loop(evidence_dir)
    assert "Missing evidence" in str(exc.value)
