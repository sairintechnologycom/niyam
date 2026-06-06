"""Remediation tests for Niyam security and logic bug fixes."""

from __future__ import annotations

import os
import json
import yaml
from pathlib import Path
import pytest
from rich.console import Console

from niyam.core.security import validate_command, CommandSecurityError
from niyam.evidence.reporter import run_report
from niyam.core.context import run_context_refresh, run_context_diff
from niyam.runtimes.claude import ClaudeAdapter


def test_bash_sh_blocked() -> None:
    """bash and sh should be blocked by command validation policy."""
    with pytest.raises(CommandSecurityError) as excinfo:
        validate_command("bash -c 'touch bypass'")
    assert "Command executable 'bash' is not in the allowed" in str(excinfo.value)

    with pytest.raises(CommandSecurityError) as excinfo:
        validate_command("sh -c 'touch bypass'")
    assert "Command executable 'sh' is not in the allowed" in str(excinfo.value)

    # Valid command should pass
    parts = validate_command("pytest")
    assert parts == ["pytest"]


def test_report_fails_on_validation_failure(niyam_repo: Path) -> None:
    """niyam report should fail (raise SystemExit(1)) when a validation command fails."""
    os.chdir(niyam_repo)
    console = Console(quiet=True)

    # Run context refresh first to ensure config exists
    run_context_refresh(console=console)

    project_yaml = niyam_repo / ".niyam" / "project.yaml"
    with open(project_yaml) as f:
        data = yaml.safe_load(f) or {}

    # Set a failing validation command
    data["validation"] = {"failing_test": "python -c 'import sys; sys.exit(1)'"}
    with open(project_yaml, "w") as f:
        yaml.dump(data, f)

    # Run report — it should raise SystemExit(1)
    with pytest.raises(SystemExit) as excinfo:
        run_report("md", console=console)
    assert excinfo.value.code == 1


def test_context_diff_ignores_manual_sections(
    niyam_repo: Path, capsys: pytest.CaptureFixture
) -> None:
    """context diff should ignore changes in manual sections of architecture.md."""
    os.chdir(niyam_repo)
    console = Console()

    # 1. Initialize context
    run_context_refresh(console=console)

    # 2. Add manual section to architecture.md
    arch_path = niyam_repo / ".niyam" / "context" / "architecture.md"
    content = arch_path.read_text(encoding="utf-8")
    assert "<!-- MANUAL SECTION:" in content

    idx = content.index("<!-- MANUAL SECTION:")
    newline_idx = content[idx:].index("\n")
    marker_line_end = idx + newline_idx + 1

    modified_content = (
        content[:marker_line_end] + "\nThis is a manual architecture note.\n"
    )
    arch_path.write_text(modified_content, encoding="utf-8")

    # Clear prior output
    capsys.readouterr()

    # 3. Run context diff
    run_context_diff(console=console)
    captured = capsys.readouterr()

    assert "architecture.md — no changes" in captured.out
    assert "changes detected" not in captured.out


def test_claude_hook_script_formatting_and_imports(tmp_path: Path) -> None:
    """Generated Claude pre-tool hook should be clean of unused imports and format violations."""
    import subprocess

    adapter = ClaudeAdapter(repo_root=tmp_path)
    script = adapter._render_hook_script(
        deny_list=[],
        warn_list=[],
        deny_write_patterns=[],
        allow_write_patterns=[],
        frozen_paths=[],
        guard_enabled=False,
        remote_policy_url=None,
    )
    assert "import os" not in script

    # Write hook script to tmp file and assert ruff format checks pass
    hook_file = tmp_path / "pre_tool_guard.py"
    hook_file.write_text(script, encoding="utf-8")

    res = subprocess.run(
        ["ruff", "format", "--check", str(hook_file)], capture_output=True, text=True
    )
    assert res.returncode == 0, (
        f"Ruff format check failed on generated hook: {res.stdout}\n{res.stderr}"
    )


def test_validate_mission_plan_cycle(tmp_path: Path) -> None:
    """Should raise PlanValidationError when a dependency cycle is detected."""
    from niyam.mission.validator import validate_mission_plan, PlanValidationError

    # Create a mock .niyam directory structure with dummy agents
    niyam_dir = tmp_path / ".niyam"
    niyam_dir.mkdir()
    agents_dir = niyam_dir / "agents"
    agents_dir.mkdir()
    (agents_dir / "mock-agent.md").write_text("# Mock Agent\n", encoding="utf-8")

    plan_path = tmp_path / "mission-plan.yaml"
    plan_data = {
        "mission": {
            "id": "test-mission",
            "requirement": "Test requirement",
            "status": "planned",
            "orchestrator": "claude",
            "parallel": 1,
            "worktree": True,
            "created": "2026-05-29T12:00:00Z",
        },
        "tasks": [
            {
                "id": "T1",
                "title": "Task 1",
                "type": "discovery",
                "status": "planned",
                "agent": "mock-agent",
                "writes_files": False,
                "depends_on": ["T2"],
            },
            {
                "id": "T2",
                "title": "Task 2",
                "type": "implementation",
                "status": "planned",
                "agent": "mock-agent",
                "writes_files": True,
                "depends_on": ["T1"],
            },
        ],
    }
    with open(plan_path, "w", encoding="utf-8") as f:
        yaml.dump(plan_data, f)

    with pytest.raises(PlanValidationError) as excinfo:
        validate_mission_plan(plan_path, tmp_path)
    assert "Dependency cycle detected" in str(excinfo.value)


def test_validate_mission_plan_unknown_dependency(tmp_path: Path) -> None:
    """Should raise PlanValidationError when a task depends on an unknown task ID."""
    from niyam.mission.validator import validate_mission_plan, PlanValidationError

    niyam_dir = tmp_path / ".niyam"
    niyam_dir.mkdir()
    agents_dir = niyam_dir / "agents"
    agents_dir.mkdir()
    (agents_dir / "mock-agent.md").write_text("# Mock Agent\n", encoding="utf-8")

    plan_path = tmp_path / "mission-plan.yaml"
    plan_data = {
        "mission": {
            "id": "test-mission",
            "requirement": "Test requirement",
            "status": "planned",
            "orchestrator": "claude",
            "parallel": 1,
            "worktree": True,
            "created": "2026-05-29T12:00:00Z",
        },
        "tasks": [
            {
                "id": "T1",
                "title": "Task 1",
                "type": "discovery",
                "status": "planned",
                "agent": "mock-agent",
                "writes_files": False,
                "depends_on": ["T99"],
            }
        ],
    }
    with open(plan_path, "w", encoding="utf-8") as f:
        yaml.dump(plan_data, f)

    with pytest.raises(PlanValidationError) as excinfo:
        validate_mission_plan(plan_path, tmp_path)
    assert "depends on unknown task ID 'T99'" in str(excinfo.value)


def test_writes_files_false_violation_and_revert(niyam_repo: Path) -> None:
    """Should revert changes and fail task if a writes_files: false task modifies files."""
    from unittest.mock import patch, MagicMock
    from niyam.mission.executor import run_mission_start, load_plan
    from niyam.mission.planner import run_mission_plan, run_mission_approve
    from niyam.core.config import get_niyam_dir

    os.chdir(niyam_repo)
    console = Console(quiet=True)

    # Initial git commit so checkout works
    os.system("git add .niyam && git commit -m 'Initial commit'")

    # Plan and approve mission
    req_file = niyam_repo / "requirements.md"
    req_file.write_text("# Writes files false test\n", encoding="utf-8")
    mission_id = run_mission_plan(str(req_file), console=console)

    # Let's override the generated plan to set writes_files: false on the task being run
    niyam_dir = get_niyam_dir(niyam_repo)
    run_dir = niyam_dir / "runs" / mission_id
    plan_path = run_dir / "mission-plan.yaml"
    with open(plan_path, encoding="utf-8") as f:
        plan_data = yaml.safe_load(f)

    # Modify all tasks to have writes_files: false
    for t in plan_data["tasks"]:
        t["writes_files"] = False
    with open(plan_path, "w", encoding="utf-8") as f:
        yaml.dump(plan_data, f)

    run_mission_approve(console=console)

    # Patch execution to write a file during execution
    import subprocess as sp

    real_run = sp.run

    def mock_subprocess_run(args, **kwargs):
        if args and args[0] == "git":
            return real_run(args, **kwargs)
        cwd = kwargs.get("cwd", niyam_repo)

        # Modify an existing file or write an unauthorized file
        modified_file = Path(cwd) / "src" / "changed.py"
        modified_file.parent.mkdir(parents=True, exist_ok=True)
        modified_file.write_text("changes made", encoding="utf-8")
        real_run(["git", "add", "src/changed.py"], cwd=cwd)

        res = MagicMock()
        res.returncode = 0
        return res

    with (
        patch("shutil.which", return_value="/usr/local/bin/claude"),
        patch("subprocess.run", side_effect=mock_subprocess_run),
    ):
        try:
            with pytest.raises(SystemExit) as excinfo:
                run_mission_start(console=console, worktree=False)
            assert excinfo.value.code == 1
        except Exception:
            pass

    # Verify task failed and file was reverted/deleted
    plan = load_plan(run_dir)
    assert plan["tasks"][0]["status"] == "failed"
    assert not (niyam_repo / "src" / "changed.py").exists()

    policy_events_path = run_dir / "policy-events.json"
    assert policy_events_path.exists()
    with open(policy_events_path, encoding="utf-8") as f:
        events = json.load(f)
    assert any(e["type"] == "WRITE_VIOLATION" for e in events)


def test_validate_path_within_repo_security(tmp_path: Path) -> None:
    """Should block path traversal and partial match traversal."""
    from niyam.core.security import validate_path_within_repo

    repo_root = tmp_path / "my-repo"
    repo_root.mkdir()

    # Path within repo is allowed
    allowed = validate_path_within_repo("src/file.py", repo_root)
    assert allowed == (repo_root / "src/file.py").resolve()

    # Traversal resolving outside should be blocked
    with pytest.raises(ValueError) as excinfo:
        validate_path_within_repo("../outside.py", repo_root)
    assert "resolves outside the repository root" in str(excinfo.value)

    # Prefix match trick (e.g. repo-backup vs repo) should be blocked
    backup_path = tmp_path / "my-repo-backup"
    backup_path.mkdir()

    # Although my-repo-backup starts with my-repo, it is not inside my-repo
    with pytest.raises(ValueError) as excinfo:
        validate_path_within_repo("../my-repo-backup", repo_root)
    assert "resolves outside the repository root" in str(excinfo.value)


def test_validate_command_hardening(tmp_path: Path) -> None:
    """Should enforce command validation and path restrictions for validation commands."""
    from niyam.core.security import validate_command, CommandSecurityError

    repo_root = tmp_path / "my-repo"
    repo_root.mkdir()

    # 1. Test normal command within repo
    parts = validate_command("rm file.txt", repo_root)
    assert parts == ["rm", "file.txt"]

    # 2. Test command with traversal outside repo
    with pytest.raises(CommandSecurityError) as excinfo:
        validate_command("rm ../outside.txt", repo_root)
    assert "points outside the repository root" in str(excinfo.value)

    # 3. Test command with absolute path outside repo
    with pytest.raises(CommandSecurityError) as excinfo:
        validate_command("rm /etc/passwd", repo_root)
    assert "points outside the repository root" in str(excinfo.value)

    # 4. Test Docker volume mount security
    # Valid relative volume mount
    parts = validate_command("docker run -v .:/workspace alpine", repo_root)
    assert parts == ["docker", "run", "-v", ".:/workspace", "alpine"]

    # Valid absolute mount of docker socket
    parts = validate_command(
        "docker run -v /var/run/docker.sock:/var/run/docker.sock alpine", repo_root
    )
    assert parts == [
        "docker",
        "run",
        "-v",
        "/var/run/docker.sock:/var/run/docker.sock",
        "alpine",
    ]

    # Invalid absolute volume mount
    with pytest.raises(CommandSecurityError) as excinfo:
        validate_command("docker run -v /etc:/workspace alpine", repo_root)
    assert "resolves outside the repository root" in str(excinfo.value)

    # Invalid relative volume mount pointing outside
    with pytest.raises(CommandSecurityError) as excinfo:
        validate_command("docker run -v ../outside:/workspace alpine", repo_root)
    assert "resolves outside the repository root" in str(excinfo.value)

    # Invalid mount using --mount syntax
    with pytest.raises(CommandSecurityError) as excinfo:
        validate_command(
            "docker run --mount type=bind,source=/etc,target=/workspace alpine",
            repo_root,
        )
    assert "resolves outside the repository root" in str(excinfo.value)
