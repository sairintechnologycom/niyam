"""E2E tests for niyam guard commands."""

from __future__ import annotations

from pathlib import Path
import yaml


def configure_governance(workspace: Path, mode: str, blocked: list[str]) -> None:
    """Helper to update niyam.yaml with guard settings."""
    config_path = workspace / ".niyam" / "niyam.yaml"
    with open(config_path, encoding="utf-8") as f:
        config_data = yaml.safe_load(f) or {}

    config_data["governance"] = {
        "scan": {"profile": "startup", "fail_on": [], "include": []},
        "guard": {
            "mode": mode,
            "blocked_commands": blocked,
            "protected_files": [],
            "approval_required": [],
        },
    }
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(config_data, f)


def test_guard_observe_and_logs(clean_workspace: Path, run_cli) -> None:
    """Guard observe logs command."""
    # 1. Initialize Niyam
    init_res = run_cli(["niyam", "init", "--profile", "fullstack"], cwd=clean_workspace)
    assert init_res.returncode == 0

    # 2. Run a command under guard observation
    observe_res = run_cli(
        ["niyam", "guard", "run", "--", "echo", "test-observe-command"],
        cwd=clean_workspace,
    )
    assert observe_res.returncode == 0
    assert "test-observe-command" in observe_res.stdout

    # 3. Check logs using niyam guard logs
    logs_res = run_cli(["niyam", "guard", "logs"], cwd=clean_workspace)
    assert logs_res.returncode == 0
    assert "echo" in logs_res.stdout
    assert "test-observe" in logs_res.stdout


def test_guard_block_mode(clean_workspace: Path, run_cli) -> None:
    """Guard block mode blocks simulated risky command."""
    # 1. Initialize Niyam
    init_res = run_cli(["niyam", "init", "--profile", "fullstack"], cwd=clean_workspace)
    assert init_res.returncode == 0

    # 2. Configure governance block rules
    configure_governance(clean_workspace, mode="block", blocked=["rm -rf"])

    # 3. Run blocked command
    block_res = run_cli(
        ["niyam", "guard", "run", "--", "rm", "-rf", "nonexistent-dir"],
        cwd=clean_workspace,
    )
    assert block_res.returncode == 1
    assert "Blocked:" in block_res.stdout or "Blocked:" in block_res.stderr

    # 4. Verify guard status lists the blocked metric
    status_res = run_cli(["niyam", "guard", "status"], cwd=clean_workspace)
    assert status_res.returncode == 0
    assert "Total Actions Logged:" in status_res.stdout
    assert "Failed Actions" in status_res.stdout
