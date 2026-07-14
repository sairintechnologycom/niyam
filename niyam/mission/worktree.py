"""Niyam mission Git worktree management utilities."""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from rich.console import Console
from niyam.mission.utils import print_lock, git_lock


def is_git_repo(repo_root: Path) -> bool:
    """Check if the project root is a Git repository."""
    return (repo_root / ".git").exists()


def get_current_head(repo_root: Path) -> str:
    """Get the current branch name or commit hash of main repo."""
    res = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    if res.returncode == 0 and res.stdout.strip() != "HEAD":
        return res.stdout.strip()

    res = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    if res.returncode == 0:
        return res.stdout.strip()
    return "main"


def git_has_commits(repo_root: Path) -> bool:
    """Check if the Git repository has any commits."""
    res = subprocess.run(
        ["git", "rev-parse", "--verify", "HEAD"],
        cwd=repo_root,
        capture_output=True,
    )
    return res.returncode == 0


def save_checkpoint(task_id: str, repo_root: Path, console: Console | None = None) -> str:
    """Commit current changes, then update a local checkpoint branch."""
    if not is_git_repo(repo_root) or not git_has_commits(repo_root):
        raise RuntimeError("Cannot save checkpoint outside a Git repo with commits.")

    safe_task_id = "".join(c if c.isalnum() or c in ("-", "_") else "-" for c in task_id)
    branch_name = f"niyam/checkpoint-{safe_task_id}"

    status = subprocess.run(
        ["git", "status", "--porcelain", "--", ":!.niyam"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    if status.stdout.strip():
        subprocess.run(
            ["git", "add", "-A", "--", ":!.niyam"],
            cwd=repo_root,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "commit", "-m", f"Niyam checkpoint {task_id}"],
            cwd=repo_root,
            check=True,
            capture_output=True,
        )

    subprocess.run(
        ["git", "branch", "-f", branch_name, "HEAD"],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )
    if console:
        console.print(f"[dim]Saved checkpoint branch {branch_name}[/]")
    return branch_name


def branch_exists(repo_root: Path, branch_name: str) -> bool:
    """Check if a local Git branch exists."""
    res = subprocess.run(
        ["git", "show-ref", "--verify", f"refs/heads/{branch_name}"],
        cwd=repo_root,
        capture_output=True,
    )
    return res.returncode == 0


def cleanup_worktree(
    repo_root: Path, worktree_path: Path, branch_name: str, console: Console
) -> None:
    """Force-remove a git worktree and cleanup directories (Thread-safe)."""
    with git_lock:
        cleanup_worktree_unlocked(repo_root, worktree_path, branch_name, console)


def cleanup_worktree_unlocked(
    repo_root: Path, worktree_path: Path, branch_name: str, console: Console
) -> None:
    """Force-remove a git worktree and cleanup directories (Internal)."""
    if worktree_path.exists():
        subprocess.run(
            ["git", "worktree", "remove", "--force", str(worktree_path)],
            cwd=repo_root,
            capture_output=True,
            timeout=30,
        )
        if worktree_path.exists():
            try:
                shutil.rmtree(worktree_path)
            except Exception:
                pass
    subprocess.run(
        ["git", "worktree", "prune"],
        cwd=repo_root,
        capture_output=True,
        timeout=30,
    )


def copy_niyam_to_worktree(repo_root: Path, worktree_path: Path) -> None:
    """Copy .niyam/ configuration (excluding runs/worktrees) to worktree."""
    src_niyam = repo_root / ".niyam"
    dst_niyam = worktree_path / ".niyam"
    if not src_niyam.is_dir():
        return

    if dst_niyam.exists():
        try:
            shutil.rmtree(dst_niyam)
        except Exception:
            pass

    dst_niyam.mkdir(parents=True, exist_ok=True)
    for item in src_niyam.iterdir():
        if item.name in ("runs", "worktrees"):
            continue
        try:
            if item.is_dir():
                shutil.copytree(item, dst_niyam / item.name)
            else:
                shutil.copy2(item, dst_niyam / item.name)
        except Exception:
            pass


def create_worktree(
    repo_root: Path,
    run_dir: Path,
    mission_id: str,
    task: dict,
    console: Console,
    branch_name: str | None = None,
) -> Path:
    """Create a git worktree for a task, branching and merging dependencies."""
    task_id = task["id"]
    with git_lock:
        worktree_path = run_dir / "worktrees" / task_id
        if branch_name is None:
            branch_name = f"niyam-{mission_id}-{task_id}"

        cleanup_worktree_unlocked(repo_root, worktree_path, branch_name, console)
        worktree_path.parent.mkdir(parents=True, exist_ok=True)

        if branch_exists(repo_root, branch_name):
            with print_lock:
                console.print(
                    f"[{task_id}] [dim]Worktree branch {branch_name} already exists. Reusing branch...[/]"
                )
            subprocess.run(
                ["git", "worktree", "add", str(worktree_path), branch_name],
                cwd=repo_root,
                check=True,
                capture_output=True,
                timeout=60,
            )
        else:
            deps = task.get("depends_on", [])
            if not deps:
                parent_commit = get_current_head(repo_root)
            else:
                parent_commit = f"niyam-{mission_id}-{deps[0]}"

            with print_lock:
                console.print(
                    f"[{task_id}] [dim]Creating branch {branch_name} from parent {parent_commit}...[/]"
                )

            subprocess.run(
                [
                    "git",
                    "worktree",
                    "add",
                    "-b",
                    branch_name,
                    str(worktree_path),
                    parent_commit,
                ],
                cwd=repo_root,
                check=True,
                capture_output=True,
                timeout=60,
            )

            # Merge other dependencies if any
            if len(deps) > 1:
                for other_dep in deps[1:]:
                    other_branch = f"niyam-{mission_id}-{other_dep}"
                    with print_lock:
                        console.print(
                            f"[{task_id}] [dim]Merging dependency branch {other_branch} into {branch_name}...[/]"
                        )
                    res = subprocess.run(
                        [
                            "git",
                            "merge",
                            other_branch,
                            "-m",
                            f"Merge dependency {other_dep}",
                        ],
                        cwd=worktree_path,
                        capture_output=True,
                        text=True,
                        timeout=60,
                    )

                    if res.returncode != 0:
                        with print_lock:
                            console.print(
                                f"[{task_id}] [bold red]Merge conflict:[/] Failed to merge {other_branch} into {branch_name}.\n{res.stderr or res.stdout}"
                            )
                        raise RuntimeError(
                            f"Merge conflict: failed to merge {other_branch} into {branch_name}"
                        )

        copy_niyam_to_worktree(repo_root, worktree_path)
        return worktree_path


def commit_worktree_changes(
    worktree_path: Path, task_id: str, console: Console
) -> None:
    """Commit all changes made inside the worktree branch."""
    res_status = subprocess.run(
        ["git", "status", "--porcelain", "--", ":!.niyam"],
        cwd=worktree_path,
        capture_output=True,
        text=True,
        check=True,
    )
    if not res_status.stdout.strip():
        with print_lock:
            console.print(
                f"[{task_id}] [dim]No changes to commit for task {task_id}.[/]"
            )
        return

    subprocess.run(
        ["git", "add", "-A", "--", ":!.niyam"],
        cwd=worktree_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-m", f"Complete task {task_id}"],
        cwd=worktree_path,
        check=True,
        capture_output=True,
    )
    with print_lock:
        console.print(f"[{task_id}] [dim]Committed changes successfully.[/]")


def find_leaf_tasks(tasks: list[dict]) -> list[str]:
    """Find task IDs that no other task depends on."""
    all_ids = {t["id"] for t in tasks if t["status"] == "completed"}
    dependent_ids = set()
    for t in tasks:
        for dep in t.get("depends_on", []):
            dependent_ids.add(dep)
    return list(all_ids - dependent_ids)


@dataclass
class MergeResult:
    """Outcome of final mission branch integration."""

    success: bool
    recovery_tasks: list[dict] = field(default_factory=list)
    conflicts: list[dict] = field(default_factory=list)
    message: str = ""


def _unmerged_paths(repo_root: Path) -> list[str]:
    """List paths with unresolved merge conflicts."""
    res = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=U"],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    if res.returncode != 0:
        return []
    return [line.strip() for line in res.stdout.splitlines() if line.strip()]


def _branch_diff_summary(
    repo_root: Path, branch_name: str, *, max_chars: int = 8000
) -> str:
    """Short stat + patch summary of branch vs HEAD for recovery prompts."""
    parts: list[str] = []
    for args in (
        ["git", "diff", "--stat", "HEAD", branch_name],
        ["git", "diff", "HEAD", branch_name, "--"],
    ):
        res = subprocess.run(
            args,
            cwd=repo_root,
            capture_output=True,
            text=True,
        )
        if res.returncode == 0 and res.stdout.strip():
            parts.append(res.stdout.strip())
    text = "\n\n".join(parts) if parts else "(no diff available)"
    if len(text) > max_chars:
        return text[:max_chars] + "\n… [truncated]"
    return text


def build_merge_recovery_task(
    *,
    mission_id: str,
    leaf_id: str,
    branch_name: str,
    conflict_files: list[str],
    merge_output: str,
    branch_diff: str,
    existing_task_ids: set[str] | None = None,
) -> dict:
    """Create a recovery TaskContract-shaped dict for a final-merge conflict."""
    base_id = f"T_MERGE_REC_{leaf_id}"
    task_id = base_id
    if existing_task_ids:
        n = 2
        while task_id in existing_task_ids:
            task_id = f"{base_id}_{n}"
            n += 1

    files = conflict_files or ["*"]
    healing = (
        f"Final integration of branch `{branch_name}` into the workspace failed "
        f"with a merge conflict while completing mission `{mission_id}` "
        f"(leaf task `{leaf_id}`).\n\n"
        f"Conflict files:\n"
        + "\n".join(f"- {p}" for p in (conflict_files or ["(unknown)"]))
        + "\n\nMerge output:\n```\n"
        + (merge_output or "")[:4000]
        + "\n```\n\nBranch diff vs workspace HEAD:\n```\n"
        + (branch_diff or "")[:6000]
        + "\n```\n\n"
        "Resolve by: (1) merging the branch cleanly or replaying changes, "
        "(2) fixing every conflict file without leaving conflict markers, "
        "(3) ensuring validation commands pass. Do not force-push or rewrite "
        "shared history."
    )
    return {
        "id": task_id,
        "title": f"Recovery: resolve merge conflict integrating {leaf_id}",
        "type": "recovery",
        "status": "planned",
        "approval_required": True,
        "agent": "backend-specialist",
        "depends_on": [leaf_id],
        "files_allowed": files,
        "allowed_files": files,
        "writes_files": True,
        "acceptance_criteria": [
            f"Branch {branch_name} merges cleanly into the workspace",
            "No conflict markers remain in the tree",
            "Relevant validation commands pass",
        ],
        "description": healing,
        "healing_prompt": healing,
        "context": {
            "kind": "merge_conflict",
            "mission_id": mission_id,
            "leaf_task_id": leaf_id,
            "branch": branch_name,
            "conflict_files": conflict_files,
        },
    }


def merge_final_changes(
    repo_root: Path, mission_id: str, tasks: list[dict], console: Console
) -> MergeResult:
    """Merge leaf task branches back into the main workspace.

    On merge conflict: abort the merge, build a recovery task (conflict files +
    branch diffs), and return ``success=False`` with recovery tasks so the
    executor can pause for approval instead of failing the mission hard.
    """
    with git_lock:
        leaf_ids = find_leaf_tasks(tasks)
        if not leaf_ids:
            console.print("[yellow]No completed leaf tasks to merge.[/]")
            return MergeResult(success=True, message="No completed leaf tasks to merge.")

        existing_ids = {t["id"] for t in tasks}
        recovery_tasks: list[dict] = []
        conflicts: list[dict] = []

        # Check if working directory is dirty (including untracked files)
        status_res = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo_root,
            capture_output=True,
            text=True,
        )
        is_dirty = bool(status_res.stdout.strip())
        stashed = False

        if is_dirty:
            console.print("[cyan]Working directory is dirty. Stashing changes...[/]")
            stash_res = subprocess.run(
                [
                    "git",
                    "stash",
                    "push",
                    "-u",
                    "-m",
                    f"Niyam auto-stash for merge {mission_id}",
                ],
                cwd=repo_root,
                capture_output=True,
                text=True,
            )
            if stash_res.returncode == 0:
                stashed = True
                console.print("[green]✓ Stashed successfully.[/]")
            else:
                console.print(
                    f"[yellow]Warning: Failed to stash changes: {stash_res.stderr or stash_res.stdout}[/]"
                )

        try:
            for leaf_id in leaf_ids:
                branch_name = f"niyam-{mission_id}-{leaf_id}"
                console.print(
                    f"[cyan]Merging final branch {branch_name} into workspace...[/]"
                )

                # Capture branch content before merge attempt for recovery prompts
                branch_diff = _branch_diff_summary(repo_root, branch_name)

                res = subprocess.run(
                    [
                        "git",
                        "merge",
                        branch_name,
                        "-m",
                        f"Merge completed mission task {leaf_id}",
                    ],
                    cwd=repo_root,
                    capture_output=True,
                    text=True,
                )
                if res.returncode != 0:
                    merge_out = (res.stderr or "") + "\n" + (res.stdout or "")
                    conflict_files = _unmerged_paths(repo_root)
                    # Leave workspace clean for the recovery task
                    subprocess.run(
                        ["git", "merge", "--abort"],
                        cwd=repo_root,
                        capture_output=True,
                        text=True,
                    )
                    console.print(
                        f"[bold yellow]Merge conflict during final integration of "
                        f"{branch_name}.[/] Generating recovery task instead of aborting "
                        f"the mission.\nConflict files: {', '.join(conflict_files) or '(see merge output)'}"
                    )
                    rec = build_merge_recovery_task(
                        mission_id=mission_id,
                        leaf_id=leaf_id,
                        branch_name=branch_name,
                        conflict_files=conflict_files,
                        merge_output=merge_out.strip(),
                        branch_diff=branch_diff,
                        existing_task_ids=existing_ids | {t["id"] for t in recovery_tasks},
                    )
                    recovery_tasks.append(rec)
                    conflicts.append(
                        {
                            "leaf_id": leaf_id,
                            "branch": branch_name,
                            "conflict_files": conflict_files,
                        }
                    )
                    continue

                console.print(
                    f"[bold green]✓[/] Successfully integrated changes from branch [cyan]{branch_name}[/]."
                )
        finally:
            if stashed:
                console.print("[cyan]Restoring stashed changes...[/]")
                pop_res = subprocess.run(
                    ["git", "stash", "pop"],
                    cwd=repo_root,
                    capture_output=True,
                    text=True,
                )
                if pop_res.returncode == 0:
                    console.print("[green]✓ Restored stashed changes successfully.[/]")
                else:
                    console.print(
                        f"[bold red]Warning: Failed to restore stashed changes: {pop_res.stderr or pop_res.stdout}[/]"
                    )

        if recovery_tasks:
            return MergeResult(
                success=False,
                recovery_tasks=recovery_tasks,
                conflicts=conflicts,
                message=(
                    f"{len(recovery_tasks)} merge conflict(s) require recovery tasks."
                ),
            )
        return MergeResult(success=True, message="All leaf branches integrated.")


def delete_mission_branches(
    repo_root: Path, mission_id: str, tasks: list[dict], console: Console
) -> None:
    """Clean up temporary task branches and prune worktrees."""
    with git_lock:
        for t in tasks:
            branch_name = f"niyam-{mission_id}-{t['id']}"
            if branch_exists(repo_root, branch_name):
                subprocess.run(
                    ["git", "branch", "-D", branch_name],
                    cwd=repo_root,
                    capture_output=True,
                )
        subprocess.run(
            ["git", "worktree", "prune"],
            cwd=repo_root,
            capture_output=True,
        )
