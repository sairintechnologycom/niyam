"""Niyam mission Git worktree management utilities."""

from __future__ import annotations

import shutil
import subprocess
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


def merge_final_changes(
    repo_root: Path, mission_id: str, tasks: list[dict], console: Console
) -> None:
    """Merge leaf task branches of the completed mission back into main workspace."""
    with git_lock:
        leaf_ids = find_leaf_tasks(tasks)
        if not leaf_ids:
            console.print("[yellow]No completed leaf tasks to merge.[/]")
            return

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
                    console.print(
                        f"[bold red]Merge conflict during final integration:[/] Failed to merge {branch_name} back to main workspace.\n{res.stderr or res.stdout}"
                    )
                    raise RuntimeError(
                        f"Merge conflict during final integration of {branch_name}"
                    )

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
