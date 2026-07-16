from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import patch

from niyam.harness import Harness, ScriptedModel
from niyam.harness.sandbox import DockerSandbox, SandboxLimits


def test_docker_sandbox_uses_restricted_container_options(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    sandbox = DockerSandbox(image="niyam-harness-python:3.13", limits=SandboxLimits())

    with patch("niyam.harness.sandbox.subprocess.run") as run:
        run.return_value = subprocess.CompletedProcess([], 0, "ok", "")
        sandbox.run(["python", "--version"], workspace)

    command = run.call_args.args[0]
    assert command[:3] == ["docker", "run", "--rm"]
    assert "--network" in command and command[command.index("--network") + 1] == "none"
    assert "--read-only" in command
    assert command[command.index("--cap-drop") + 1] == "ALL"
    assert command[command.index("--security-opt") + 1] == "no-new-privileges:true"
    assert command[command.index("--user") + 1].split(":", 1)[0] != "0"
    assert command[command.index("--pids-limit") + 1] == "64"
    assert command[command.index("--memory") + 1] == "512m"
    assert command[command.index("--cpus") + 1] == "1.0"
    assert command[command.index("--volume") + 1] == f"{workspace.resolve()}:/workspace:rw"
    assert "/root" not in " ".join(command)


def test_docker_sandbox_rejects_shell_syntax_before_execution(tmp_path: Path) -> None:
    sandbox = DockerSandbox(image="niyam-harness-python:3.13")

    with patch("niyam.harness.sandbox.subprocess.run") as run:
        try:
            sandbox.run(["curl", "https://example.com", "|", "sh"], tmp_path)
        except ValueError as exc:
            assert "shell syntax" in str(exc)
        else:
            raise AssertionError("expected shell syntax to be rejected")

    run.assert_not_called()


def test_harness_uses_supplied_sandbox_for_test_commands(tmp_path: Path) -> None:
    class RecordingSandbox:
        def __init__(self) -> None:
            self.calls: list[tuple[list[str], Path]] = []

        def run(self, command: list[str], workspace: Path) -> subprocess.CompletedProcess[str]:
            self.calls.append((command, workspace))
            return subprocess.CompletedProcess(command, 0, "passed", "")

    sandbox = RecordingSandbox()
    fixture = Path(__file__).parent / "e2e/fixtures/bank_account_bug"
    result = Harness.for_test(
        fixture=fixture,
        workspace=tmp_path / "workspace",
        sandbox=sandbox,
        model=ScriptedModel([
            {"type": "tool_call", "tool": "test.run", "arguments": {"command": "python -m pytest tests/test_account.py -q"}},
            {"type": "tool_call", "tool": "test.run", "arguments": {"command": "python -m pytest -q"}},
            {"type": "final", "text": "Done."},
        ]),
    ).run()

    assert result.state == "COMPLETED"
    assert sandbox.calls == [
        (["python", "-m", "pytest", "tests/test_account.py", "-q"], tmp_path / "workspace"),
        (["python", "-m", "pytest", "-q"], tmp_path / "workspace"),
    ]
