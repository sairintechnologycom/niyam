"""Tests for Niyam guard observe mode."""

from __future__ import annotations

import json
from pathlib import Path
import pytest
from typer.testing import CliRunner

from niyam.cli import app


@pytest.fixture(autouse=True)
def setup_workspace(tmp_path: Path, monkeypatch) -> None:
    """Fixture to ensure tests run in a workspace relative to tmp_path."""
    monkeypatch.chdir(tmp_path)
    # Create mock .niyam directory to mock find_niyam_root
    niyam_dir = tmp_path / ".niyam"
    niyam_dir.mkdir(exist_ok=True)
    # Write empty config
    with open(niyam_dir / "niyam.yaml", "w") as f:
        f.write("version: 0.1.0\n")


def test_guard_run_harmless_command(tmp_path: Path) -> None:
    """Should run a harmless command, preserve exit code, and log execution details."""
    runner = CliRunner()

    # Run a harmless command (echo 'hello') with capture output
    result = runner.invoke(
        app, ["guard", "run", "--capture-output", "--", "echo", "hello-observe"]
    )
    assert result.exit_code == 0
    assert "hello-observe" in result.stdout

    # Confirm log is created in the expected location
    log_file = tmp_path / ".niyam" / "logs" / "guard-actions.jsonl"
    assert log_file.exists()

    # Read the log entry
    lines = log_file.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 1

    entry = json.loads(lines[0])
    assert entry["exit_code"] == 0
    assert entry["mode"] == "observe"
    assert "echo" in entry["command"]
    assert entry["actor_type"] == "agent"


def test_guard_run_failed_command(tmp_path: Path) -> None:
    """Should log failed commands and preserve their exit codes."""
    import sys

    runner = CliRunner()

    # Run a command that returns non-zero exit code using the exact python interpreter
    result = runner.invoke(
        app, ["guard", "run", "--", sys.executable, "-c", "import sys; sys.exit(42)"]
    )
    assert result.exit_code == 42

    log_file = tmp_path / ".niyam" / "logs" / "guard-actions.jsonl"
    assert log_file.exists()

    lines = log_file.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 1

    entry = json.loads(lines[0])
    assert entry["exit_code"] == 42
    assert entry["mode"] == "observe"


def test_guard_status_command(tmp_path: Path) -> None:
    """Should display status including count of observed logs."""
    runner = CliRunner()

    # Run one harmless command
    runner.invoke(app, ["guard", "run", "--", "echo", "test"])

    # Check guard status
    result = runner.invoke(app, ["guard", "status"])
    assert result.exit_code == 0
    assert "Total Actions Logged: 1" in result.stdout


def test_guard_logs_command(tmp_path: Path) -> None:
    """Should display recent observed logs in a table format."""
    runner = CliRunner()

    # Run harmless commands
    runner.invoke(app, ["guard", "run", "--", "echo", "cmd1"])
    runner.invoke(app, ["guard", "run", "--", "echo", "cmd2"])

    # Check guard logs
    result = runner.invoke(app, ["guard", "logs"])
    assert result.exit_code == 0
    assert "cmd1" in result.stdout
    assert "cmd2" in result.stdout


def test_guard_observe_log_schema_and_secrets(tmp_path: Path, monkeypatch) -> None:
    """Verify log schema, session ID generation, actor type, and secret redaction."""
    runner = CliRunner()

    # Set up some fake environment variables/secrets that should NOT be in the logs
    monkeypatch.setenv("MY_SUPER_SECRET", "sk-ant-1234567890abcdef12345678")
    monkeypatch.setenv(
        "NIYAM_SESSION_ID", ""
    )  # Clear session ID to trigger auto generation

    # Run command containing a secret
    result = runner.invoke(
        app,
        [
            "guard",
            "run",
            "--capture-output",
            "--",
            "echo",
            "key",
            "sk-proj-24charsandmore1234567890abcdef",
        ],
    )
    assert result.exit_code == 0

    log_file = tmp_path / ".niyam" / "logs" / "guard-actions.jsonl"
    assert log_file.exists()

    lines = log_file.read_text(encoding="utf-8").strip().split("\n")
    entry = json.loads(lines[-1])

    # 1. Validate Log Schema
    required_fields = [
        "schema_version",
        "timestamp",
        "session_id",
        "actor_type",
        "tool",
        "action",
        "command",
        "cwd",
        "exit_code",
        "duration_ms",
        "mode",
        "policy_decision",
    ]
    for field in required_fields:
        assert field in entry, f"Missing field: {field}"

    assert entry["schema_version"] == "1.0.0"
    assert entry["tool"] == "shell"
    assert entry["action"] == "command_execute"
    assert entry["mode"] == "observe"
    assert entry["policy_decision"] == "allow"

    # 2. Verify session_id is generated and contains a UUID (or is a valid UUID/string)
    assert len(entry["session_id"]) > 0

    # 3. Verify actor type defaults to agent in test context
    assert entry["actor_type"] == "agent"

    # 4. Verify secret is redacted in both command and output log (and not present in raw)
    secret_val = "sk-proj-24charsandmore1234567890abcdef"
    assert secret_val not in entry["command"]
    assert "[REDACTED_SECRET" in entry["command"]
    assert secret_val not in entry["output"]
    assert "[REDACTED_SECRET" in entry["output"]

    # 5. Verify environment variables are NOT captured
    for key, val in entry.items():
        if isinstance(val, str):
            assert "MY_SUPER_SECRET" not in val
            assert "sk-ant-1234567890abcdef12345678" not in val
    assert "env" not in entry
    assert "environment" not in entry


def test_guard_observe_actor_type_human(tmp_path: Path, monkeypatch) -> None:
    """Verify actor_type resolves to human when running in a tty."""
    import sys
    from niyam.policies.guard import run_guard_run
    from rich.console import Console

    # Mock sys.stdin.isatty to return True to simulate human/tty run
    class MockStdin:
        def isatty(self):
            return True

    monkeypatch.setattr(sys, "stdin", MockStdin())
    monkeypatch.delenv("NIYAM_ACTOR_TYPE", raising=False)

    # Run direct function call and catch SystemExit
    with pytest.raises(SystemExit) as excinfo:
        run_guard_run(["echo", "human-run"], False, Console(quiet=True))
    assert excinfo.value.code == 0

    log_file = tmp_path / ".niyam" / "logs" / "guard-actions.jsonl"
    lines = log_file.read_text(encoding="utf-8").strip().split("\n")
    entry = json.loads(lines[-1])

    assert entry["actor_type"] == "human"


def test_guard_policy_modes_observe_warn_block_approval(
    tmp_path: Path, monkeypatch
) -> None:
    """Verify warn, block, and approval behaviors and JSONL schema fields."""
    runner = CliRunner()

    # 1. Write niyam.yaml with guard rules
    niyam_dir = tmp_path / ".niyam"
    niyam_dir.mkdir(exist_ok=True)
    import yaml

    config_data = {
        "version": "0.1.0",
        "governance": {
            "guard": {
                "mode": "observe",
                "blocked_commands": ["nonexistent_cmd destroy", "rm -rf"],
                "protected_files": [".env"],
                "approval_required": ["nonexistent_cmd apply"],
            }
        },
    }
    with open(niyam_dir / "niyam.yaml", "w", encoding="utf-8") as f:
        yaml.dump(config_data, f)

    log_file = tmp_path / ".niyam" / "logs" / "guard-actions.jsonl"

    # -- Mode Warn --
    # Risky command warned and allowed in warn mode (will return 127 because nonexistent_cmd doesn't exist)
    result_warn = runner.invoke(
        app, ["guard", "run", "--mode", "warn", "--", "nonexistent_cmd", "destroy"]
    )
    assert result_warn.exit_code == 127
    assert "Warning:" in result_warn.stdout

    # Check JSONL log entry for warn
    lines = log_file.read_text(encoding="utf-8").strip().split("\n")
    entry_warn = json.loads(lines[-1])
    assert entry_warn["policy_decision"] == "warn"
    assert entry_warn["decision"] == "warned"
    assert entry_warn["matched_rule"] == "blocked_command:nonexistent_cmd destroy"
    assert "Command matches blocked command pattern" in entry_warn["reason"]

    # -- Mode Block --
    # Risky command blocked in block mode
    result_block = runner.invoke(
        app, ["guard", "run", "--mode", "block", "--", "nonexistent_cmd", "destroy"]
    )
    assert result_block.exit_code == 1
    assert "Blocked:" in result_block.stdout

    # Check JSONL log entry for block
    lines = log_file.read_text(encoding="utf-8").strip().split("\n")
    entry_block = json.loads(lines[-1])
    assert entry_block["policy_decision"] == "block"
    assert entry_block["decision"] == "blocked"
    assert entry_block["matched_rule"] == "blocked_command:nonexistent_cmd destroy"

    # -- Mode Approval (Approve) --
    # Approval command denied
    result_appr_deny = runner.invoke(
        app,
        ["guard", "run", "--mode", "approval", "--", "nonexistent_cmd", "apply"],
        input="n\n",
    )
    assert result_appr_deny.exit_code == 1
    assert "Denied:" in result_appr_deny.stdout

    lines = log_file.read_text(encoding="utf-8").strip().split("\n")
    entry_deny = json.loads(lines[-1])
    assert entry_deny["policy_decision"] == "approval_required"
    assert entry_deny["decision"] == "denied"
    assert entry_deny["matched_rule"] == "approval_required:nonexistent_cmd apply"

    # Approval command approved (will proceed and fail with exit code 127)
    result_appr_allow = runner.invoke(
        app,
        ["guard", "run", "--mode", "approval", "--", "nonexistent_cmd", "apply"],
        input="y\n",
    )
    assert result_appr_allow.exit_code == 127

    lines = log_file.read_text(encoding="utf-8").strip().split("\n")
    entry_allow = json.loads(lines[-1])
    assert entry_allow["policy_decision"] == "approval_required"
    assert entry_allow["decision"] == "approved"
