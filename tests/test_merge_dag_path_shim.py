"""Tests for merge-conflict recovery, DAGPlanner scheduling, and PATH shims."""

from __future__ import annotations

import json
import os
import stat
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml
from rich.console import Console

from niyam.mission.planner import DAGPlanner
from niyam.mission.worktree import (
    MergeResult,
    build_merge_recovery_task,
    merge_final_changes,
)
from niyam.policies.path_shim import (
    ensure_path_shim,
    inject_path_shim_env,
    runtime_needs_path_shim,
    shim_dir,
)


# ── DAGPlanner.ready_tasks ─────────────────────────────────────────────


def test_ready_tasks_respects_deps_and_statuses() -> None:
    tasks = [
        {"id": "T1", "status": "completed", "depends_on": [], "type": "implementation"},
        {"id": "T2", "status": "planned", "depends_on": ["T1"], "type": "implementation"},
        {"id": "T3", "status": "planned", "depends_on": ["T2"], "type": "validation"},
    ]
    ready, skip = DAGPlanner().ready_tasks(tasks)
    assert [t["id"] for t in ready] == ["T2"]
    assert skip == []


def test_ready_tasks_skips_failed_deps() -> None:
    tasks = [
        {"id": "T1", "status": "failed", "depends_on": [], "type": "implementation"},
        {"id": "T2", "status": "planned", "depends_on": ["T1"], "type": "implementation"},
    ]
    ready, skip = DAGPlanner().ready_tasks(tasks)
    assert ready == []
    assert [t["id"] for t in skip] == ["T2"]


def test_ready_tasks_prioritizes_recovery() -> None:
    tasks = [
        {"id": "T1", "status": "planned", "depends_on": [], "type": "implementation"},
        {"id": "T_REC", "status": "planned", "depends_on": [], "type": "recovery"},
    ]
    ready, _ = DAGPlanner().ready_tasks(tasks)
    assert ready[0]["id"] == "T_REC"
    assert ready[1]["id"] == "T1"


def test_ready_tasks_excludes_running() -> None:
    tasks = [
        {"id": "T1", "status": "planned", "depends_on": []},
        {"id": "T2", "status": "planned", "depends_on": []},
    ]
    ready, _ = DAGPlanner().ready_tasks(tasks, exclude_ids={"T1"})
    assert [t["id"] for t in ready] == ["T2"]


def test_ready_tasks_includes_approved_and_retry_ready() -> None:
    tasks = [
        {"id": "A", "status": "approved", "depends_on": []},
        {"id": "B", "status": "retry_ready", "depends_on": []},
        {"id": "C", "status": "completed", "depends_on": []},
        {"id": "D", "status": "awaiting_approval", "depends_on": []},
    ]
    ready, _ = DAGPlanner().ready_tasks(tasks)
    assert {t["id"] for t in ready} == {"A", "B"}


# ── Merge recovery task builder ────────────────────────────────────────


def test_build_merge_recovery_task_shape() -> None:
    task = build_merge_recovery_task(
        mission_id="m1",
        leaf_id="T3",
        branch_name="niyam-m1-T3",
        conflict_files=["src/a.py", "src/b.py"],
        merge_output="CONFLICT (content): Merge conflict in src/a.py",
        branch_diff=" src/a.py | 10 +++++-----",
    )
    assert task["id"] == "T_MERGE_REC_T3"
    assert task["type"] == "recovery"
    assert task["approval_required"] is True
    assert task["status"] == "planned"
    assert task["depends_on"] == ["T3"]
    assert "src/a.py" in task["files_allowed"]
    assert "CONFLICT" in task["healing_prompt"]
    assert task["context"]["kind"] == "merge_conflict"


def test_build_merge_recovery_task_unique_ids() -> None:
    t1 = build_merge_recovery_task(
        mission_id="m",
        leaf_id="T1",
        branch_name="b",
        conflict_files=[],
        merge_output="",
        branch_diff="",
        existing_task_ids={"T_MERGE_REC_T1"},
    )
    assert t1["id"] == "T_MERGE_REC_T1_2"


def _init_git_repo(path: Path) -> None:
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=path,
        check=True,
        capture_output=True,
    )
    (path / "README.md").write_text("base\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "init"],
        cwd=path,
        check=True,
        capture_output=True,
    )


def test_merge_final_changes_creates_recovery_on_conflict(tmp_path: Path) -> None:
    """Conflicting leaf branch → recovery task, not hard abort."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_git_repo(repo)

    # Create conflicting branch
    leaf = "T1"
    mission_id = "mission-x"
    branch = f"niyam-{mission_id}-{leaf}"
    subprocess.run(
        ["git", "checkout", "-b", branch],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    (repo / "README.md").write_text("branch change\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "branch"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    # Back to main / first branch and diverge
    subprocess.run(
        ["git", "checkout", "-"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    (repo / "README.md").write_text("main change\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "main diverge"],
        cwd=repo,
        check=True,
        capture_output=True,
    )

    tasks = [{"id": leaf, "status": "completed", "depends_on": []}]
    console = Console(quiet=True)
    result = merge_final_changes(repo, mission_id, tasks, console)

    assert isinstance(result, MergeResult)
    assert result.success is False
    assert len(result.recovery_tasks) == 1
    rec = result.recovery_tasks[0]
    assert rec["type"] == "recovery"
    assert rec["approval_required"] is True
    assert leaf in rec["depends_on"] or rec["depends_on"] == [leaf]
    # Workspace should not remain mid-merge
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    # No unmerged paths after abort
    unmerged = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=U"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    assert unmerged.stdout.strip() == ""


def test_merge_final_changes_success_no_recovery(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_git_repo(repo)

    leaf = "T1"
    mission_id = "m2"
    branch = f"niyam-{mission_id}-{leaf}"
    subprocess.run(
        ["git", "checkout", "-b", branch],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    (repo / "extra.txt").write_text("ok\n", encoding="utf-8")
    subprocess.run(["git", "add", "extra.txt"], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "feat"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "checkout", "-"],
        cwd=repo,
        check=True,
        capture_output=True,
    )

    tasks = [{"id": leaf, "status": "completed", "depends_on": []}]
    result = merge_final_changes(repo, mission_id, tasks, Console(quiet=True))
    assert result.success is True
    assert result.recovery_tasks == []
    assert (repo / "extra.txt").exists()


# ── PATH shim ──────────────────────────────────────────────────────────


def test_runtime_needs_path_shim_hookless() -> None:
    assert runtime_needs_path_shim("codex") is True
    assert runtime_needs_path_shim("gemini") is True
    assert runtime_needs_path_shim("claude") is False


def test_ensure_path_shim_creates_wrappers(tmp_path: Path) -> None:
    niyam = tmp_path / ".niyam"
    (niyam / "policies").mkdir(parents=True)
    (niyam / "policies" / "commands.yaml").write_text(
        "deny:\n  - git push --force\n  - rm -rf\n",
        encoding="utf-8",
    )
    bin_dir = ensure_path_shim(tmp_path, force=True)
    assert bin_dir == shim_dir(tmp_path)
    git_shim = bin_dir / "git"
    assert git_shim.exists()
    assert git_shim.stat().st_mode & stat.S_IXUSR


def test_path_shim_blocks_force_push(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Shim wrapper exits 126 and logs when command matches deny pattern."""
    (tmp_path / ".niyam" / "policies").mkdir(parents=True)
    (tmp_path / ".niyam" / "policies" / "commands.yaml").write_text(
        "deny:\n  - git push --force\n",
        encoding="utf-8",
    )
    (tmp_path / ".niyam" / "hook-cache").mkdir(parents=True)
    (tmp_path / ".niyam" / "hook-cache" / "guard-config.json").write_text(
        json.dumps({"guard_enabled": True, "deny_patterns": ["git push --force"]}),
        encoding="utf-8",
    )
    bin_dir = ensure_path_shim(tmp_path, force=True, commands=["git"])
    git_shim = bin_dir / "git"
    # Run shim with force-push args (real git not needed — blocked before exec)
    proc = subprocess.run(
        [str(git_shim), "push", "--force", "origin", "main"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env={**os.environ, "NIYAM_PATH_SHIM": "1"},
    )
    assert proc.returncode == 126
    assert "Blocked by Niyam PATH-shim" in (proc.stderr or "")
    events_path = tmp_path / ".niyam" / "evidence" / "policy-events.json"
    assert events_path.exists()
    events = json.loads(events_path.read_text(encoding="utf-8"))
    assert any(e.get("type") == "BLOCKED" for e in events)


def test_inject_path_shim_env_for_codex(tmp_path: Path) -> None:
    (tmp_path / ".niyam").mkdir()
    env = inject_path_shim_env(dict(os.environ), tmp_path, "codex")
    assert str(shim_dir(tmp_path)) in env["PATH"].split(os.pathsep)[0]


def test_inject_path_shim_skips_claude_by_default(tmp_path: Path) -> None:
    (tmp_path / ".niyam").mkdir()
    env = inject_path_shim_env({"PATH": "/usr/bin"}, tmp_path, "claude")
    # Claude has hooks capability — no shim prefix by default
    assert env["PATH"] == "/usr/bin" or not env["PATH"].startswith(
        str(shim_dir(tmp_path))
    )


def test_build_runtime_invocation_injects_shim_for_codex(tmp_path: Path) -> None:
    from niyam.runtimes.executor import build_runtime_invocation

    (tmp_path / ".niyam").mkdir()
    inv = build_runtime_invocation(
        "codex",
        prompt_text="hi",
        repo_root=tmp_path,
        include_sandbox=False,
    )
    assert "PATH" in inv.env
    assert str(shim_dir(tmp_path)) in inv.env["PATH"]
