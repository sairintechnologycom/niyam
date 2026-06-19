from __future__ import annotations

import json
import os
import sys
import yaml
import pytest
import hashlib
from pathlib import Path
from datetime import datetime, timezone, timedelta
from unittest import mock

from niyam.core.loopops import LoopRunner, LoopSpec
from niyam.core.loopops.state_machine import LoopRun, LoopStateMachine
from niyam.core.loopops.evaluator import _run_command_evaluator, run_evaluators
from niyam.core.evidence import redact_secrets_recursive
from niyam.core.security import safe_run_command, CommandSecurityError

def test_secret_redaction() -> None:
    # Authorization Bearer token
    assert "[REDACTED]" in redact_secrets_recursive("Bearer eJxyz123456789")
    assert "[REDACTED]" in redact_secrets_recursive("authorization: bearer abcdef123456")
    
    # JWT token
    jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    assert "[REDACTED_JWT]" in redact_secrets_recursive(jwt)

    # JSON secret keys
    json_secrets = '{"api_key": "some-secret-token", "password": "securepassword"}'
    redacted_json = redact_secrets_recursive(json_secrets)
    assert "[REDACTED]" in redacted_json
    assert "api_key" in redacted_json

    # key=value secrets
    kv = "secret = 'password123'"
    assert "[REDACTED]" in redact_secrets_recursive(kv)
    
    # High-entropy base64 strings (>=32 chars)
    high_entropy = "U3VwZXJTZWNyZXRLZXlXaXRoSGlnaEVudHJvcHlGb3JUZXN0aW5n"
    assert "[REDACTED_HIGH_ENTROPY]" in redact_secrets_recursive(high_entropy)


def test_hook_integrity_verification_success(tmp_path: Path) -> None:
    # Create mock hook
    hook_dir = tmp_path / ".niyam" / "hook-cache"
    hook_dir.mkdir(parents=True, exist_ok=True)
    hook_file = hook_dir / "test_hook.py"
    hook_file.write_text("print('test')", encoding="utf-8")

    # Write hook_checksums.json
    expected_hash = hashlib.sha256(hook_file.read_bytes()).hexdigest()
    checksums = {
        ".niyam/hook-cache/test_hook.py": expected_hash
    }
    (hook_dir / "hook_checksums.json").write_text(json.dumps(checksums), encoding="utf-8")

    # Run Loop Spec setup
    spec_data = {
        "apiVersion": "niyam.dev/v1",
        "kind": "LoopSpec",
        "metadata": {"name": "hook-ok", "owner": "platform"},
        "goal": {"type": "testing", "description": "Verification ok"},
        "actors": {"planner": "claude"},
        "steps": [{"name": "plan", "action": "plan"}],
        "budgets": {"maxIterations": 1}
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
        run, reason = LoopRunner.run_loop(spec, repo_root=tmp_path, mode="governed")
    
    # Verification should succeed, and it should run to completion
    assert run.status == "passed"


def test_hook_integrity_verification_failure_block(tmp_path: Path) -> None:
    hook_dir = tmp_path / ".niyam" / "hook-cache"
    hook_dir.mkdir(parents=True, exist_ok=True)
    hook_file = hook_dir / "test_hook.py"
    hook_file.write_text("print('original')", encoding="utf-8")

    # Expected hash matches original
    expected_hash = hashlib.sha256(hook_file.read_bytes()).hexdigest()
    checksums = {
        ".niyam/hook-cache/test_hook.py": expected_hash
    }
    (hook_dir / "hook_checksums.json").write_text(json.dumps(checksums), encoding="utf-8")

    # Tamper the hook file
    hook_file.write_text("print('tampered')", encoding="utf-8")

    # Configure block mode
    niyam_yaml = tmp_path / ".niyam" / "niyam.yaml"
    niyam_yaml.parent.mkdir(parents=True, exist_ok=True)
    niyam_yaml.write_text(yaml.dump({
        "version": "0.1.0",
        "governance": {
            "guard": {
                "mode": "block"
            }
        }
    }), encoding="utf-8")

    spec_data = {
        "apiVersion": "niyam.dev/v1",
        "kind": "LoopSpec",
        "metadata": {"name": "hook-fail", "owner": "platform"},
        "goal": {"type": "testing", "description": "Verification fail"},
        "actors": {"planner": "claude"},
        "steps": [{"name": "plan", "action": "plan"}],
        "budgets": {"maxIterations": 1}
    }
    spec = LoopSpec.model_validate(spec_data)
    
    mock_adapter = mock.MagicMock()
    with mock.patch("niyam.core.loopops.adapters.get_adapter", return_value=mock_adapter):
        run, reason = LoopRunner.run_loop(spec, repo_root=tmp_path, mode="governed")
        
    assert run.status == "failed"
    assert "Hook file integrity verification failed" in reason


def test_hook_integrity_verification_failure_warn(tmp_path: Path) -> None:
    hook_dir = tmp_path / ".niyam" / "hook-cache"
    hook_dir.mkdir(parents=True, exist_ok=True)
    hook_file = hook_dir / "test_hook.py"
    hook_file.write_text("print('original')", encoding="utf-8")

    expected_hash = hashlib.sha256(hook_file.read_bytes()).hexdigest()
    checksums = {
        ".niyam/hook-cache/test_hook.py": expected_hash
    }
    (hook_dir / "hook_checksums.json").write_text(json.dumps(checksums), encoding="utf-8")

    hook_file.write_text("print('tampered')", encoding="utf-8")

    # Configure observe mode
    niyam_yaml = tmp_path / ".niyam" / "niyam.yaml"
    niyam_yaml.parent.mkdir(parents=True, exist_ok=True)
    niyam_yaml.write_text(yaml.dump({
        "version": "0.1.0",
        "governance": {
            "guard": {
                "mode": "observe"
            }
        }
    }), encoding="utf-8")

    spec_data = {
        "apiVersion": "niyam.dev/v1",
        "kind": "LoopSpec",
        "metadata": {"name": "hook-warn", "owner": "platform"},
        "goal": {"type": "testing", "description": "Verification warn"},
        "actors": {"planner": "claude"},
        "steps": [{"name": "plan", "action": "plan"}],
        "budgets": {"maxIterations": 1}
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
    with mock.patch("niyam.core.loopops.adapters.get_adapter", return_value=mock_adapter), \
         mock.patch("niyam.mission.task_runner.log_policy_event") as mock_log:
        run, reason = LoopRunner.run_loop(spec, repo_root=tmp_path, mode="governed")
        
    assert run.status == "passed"
    mock_log.assert_called_once()
    assert "Hook integrity check warning" in mock_log.call_args[0][3]


def test_command_evaluator_real_execution(tmp_path: Path) -> None:
    # 1. Success execution
    res = _run_command_evaluator(
        name="test-echo",
        command="echo hello",
        required=True,
        workspace_path=tmp_path,
        timestamp="2026-06-19T00:00:00Z"
    )
    assert res.result == "pass"
    assert res.exit_code == 0
    assert res.stdout.strip() == "hello"
    assert res.stderr == ""
    assert res.duration is not None and res.duration >= 0.0
    assert res.policy_result == "allow"

    # 2. Failing execution
    res_fail = _run_command_evaluator(
        name="test-fail",
        command="test 1 -eq 2",
        required=True,
        workspace_path=tmp_path,
        timestamp="2026-06-19T00:00:00Z"
    )
    assert res_fail.result == "fail"
    assert res_fail.exit_code == 1
    assert res_fail.policy_result == "allow"

    # 3. Blocked execution
    res_block = _run_command_evaluator(
        name="test-block",
        command="invalidcommand12345",
        required=True,
        workspace_path=tmp_path,
        timestamp="2026-06-19T00:00:00Z"
    )
    assert res_block.result == "fail"
    assert res_block.exit_code == -1
    assert res_block.policy_result == "blocked"
    assert "Command executable" in res_block.details


def test_early_budget_enforcement_runtime(tmp_path: Path) -> None:
    spec_data = {
        "apiVersion": "niyam.dev/v1",
        "kind": "LoopSpec",
        "metadata": {"name": "runtime-budget-test", "owner": "platform"},
        "goal": {"type": "testing", "description": "Runtime budget test"},
        "actors": {"planner": "claude"},
        "steps": [{"name": "plan", "action": "plan"}],
        "budgets": {
            "maxIterations": 5,
            "maxRuntimeMinutes": 5
        }
    }
    spec = LoopSpec.model_validate(spec_data)
    run = LoopRunner.initialize_run(spec, repo_root=tmp_path)
    
    # Simulate run started 10 minutes ago
    ten_mins_ago = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
    run.started_at = ten_mins_ago
    
    # Run the loop. Since it evaluates budget at the start of each iteration in the while loop,
    # it should terminate immediately.
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
    with mock.patch("niyam.core.loopops.adapters.get_adapter", return_value=mock_adapter), \
         mock.patch("niyam.core.loopops.runner.LoopRunner.initialize_run", return_value=run):
        run, reason = LoopRunner.run_loop(spec, repo_root=tmp_path)
        
    assert run.status == "stopped"
    assert "Max runtime (5m) exceeded" in reason
    # Verify iteration count didn't advance
    assert run.iteration_count == 0


def test_step_max_attempts_transition(tmp_path: Path) -> None:
    spec_data = {
        "apiVersion": "niyam.dev/v1",
        "kind": "LoopSpec",
        "metadata": {"name": "max-attempts-test", "owner": "platform"},
        "goal": {"type": "testing", "description": "Max attempts test"},
        "actors": {"planner": "claude"},
        "steps": [{"name": "plan", "action": "plan", "maxAttempts": 2}],
        "budgets": {"maxIterations": 5}
    }
    spec = LoopSpec.model_validate(spec_data)
    
    mock_adapter = mock.MagicMock()
    # Mock plan to return failing results
    mock_adapter.plan.return_value = mock.MagicMock(
        status="failure",
        cost_usd=0.0,
        tokens_in=0,
        tokens_out=0,
        files_changed=[],
        commands_run=[],
        evidence_artifacts=[]
    )
    with mock.patch("niyam.core.loopops.adapters.get_adapter", return_value=mock_adapter):
        run, reason = LoopRunner.run_loop(spec, repo_root=tmp_path)
        
    assert run.status == "failed"
    assert "exceeded maxAttempts" in reason
    assert run.iteration_count == 2


def test_cryptographic_manifest_and_replay_integrity(tmp_path: Path) -> None:
    spec_data = {
        "apiVersion": "niyam.dev/v1",
        "kind": "LoopSpec",
        "metadata": {"name": "crypto-replay", "owner": "platform"},
        "goal": {"type": "testing", "description": "Crypto replay verification"},
        "actors": {"planner": "claude"},
        "steps": [{"name": "plan", "action": "plan"}],
        "budgets": {"maxIterations": 1}
    }
    spec = LoopSpec.model_validate(spec_data)
    
    mock_adapter = mock.MagicMock()
    mock_adapter.plan.return_value = mock.MagicMock(
        status="passed",
        cost_usd=0.1,
        tokens_in=10,
        tokens_out=20,
        files_changed=[],
        commands_run=[],
        evidence_artifacts=[]
    )
    with mock.patch("niyam.core.loopops.adapters.get_adapter", return_value=mock_adapter):
        run, reason = LoopRunner.run_loop(spec, repo_root=tmp_path)
        
    assert run.status == "passed"
    evidence_dir = tmp_path / run.evidence_path
    
    # Verify manifest.json exists
    manifest_path = evidence_dir / "manifest.json"
    assert manifest_path.exists()
    
    # Replay should succeed
    with mock.patch("niyam.core.loopops.adapters.get_adapter") as mock_get_adapter:
        replayed_run, replayed_reason = LoopRunner.replay_loop(evidence_dir)
        mock_get_adapter.assert_not_called()
    assert replayed_run.id == run.id
    assert replayed_run.status == "passed"
    
    # Tamper with an iteration file (001.json)
    iter_file = evidence_dir / "iterations" / "001.json"
    iter_data = json.loads(iter_file.read_text(encoding="utf-8"))
    iter_data["tokensIn"] = 99999
    iter_file.write_text(json.dumps(iter_data), encoding="utf-8")
    
    with pytest.raises(ValueError) as exc:
        LoopRunner.replay_loop(evidence_dir)
    assert "has been modified" in str(exc.value)

    # Restore iteration file, but tamper with manifest.json signature
    iter_data["tokensIn"] = 10
    iter_file.write_text(json.dumps(iter_data), encoding="utf-8")
    
    manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest_data["signature"] = "invalidsignature123"
    manifest_path.write_text(json.dumps(manifest_data), encoding="utf-8")

    with pytest.raises(ValueError) as exc:
        LoopRunner.replay_loop(evidence_dir)
    assert "manifest signature verification failed" in str(exc.value)
