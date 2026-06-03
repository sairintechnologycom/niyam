"""Niyam mission executor — run tasks in an approved plan."""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import threading
from datetime import datetime, timezone
import yaml
import fnmatch
import re
from rich.console import Console
from rich.panel import Panel

from niyam.core.config import get_niyam_dir, load_niyam_config, load_project_config
from niyam.mission.planner import resolve_mission_id

# Locks for thread-safe operations
_print_lock = threading.Lock()
_validation_lock = threading.Lock()
_plan_lock = threading.RLock()


def load_plan(run_dir: Path) -> dict:
    """Load mission plan YAML and validate schema."""
    from niyam.core.config import MissionPlan
    from niyam.core.security import safe_load_yaml

    with _plan_lock:
        import fcntl

        lock_path = run_dir / ".mission-plan.lock"
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        with open(lock_path, "a+", encoding="utf-8") as lock_f:
            fcntl.flock(lock_f, fcntl.LOCK_SH)
            try:
                plan_path = run_dir / "mission-plan.yaml"
                data = safe_load_yaml(plan_path)
                validated = MissionPlan(**data)
                return validated.model_dump()
            finally:
                fcntl.flock(lock_f, fcntl.LOCK_UN)


def save_plan(run_dir: Path, plan_data: dict) -> None:
    """Save mission plan YAML and update task-list.yaml."""
    with _plan_lock:
        import fcntl
        import tempfile

        lock_path = run_dir / ".mission-plan.lock"
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        with open(lock_path, "a+", encoding="utf-8") as lock_f:
            fcntl.flock(lock_f, fcntl.LOCK_EX)
            try:
                plan_path = run_dir / "mission-plan.yaml"
                tasks_path = run_dir / "task-list.yaml"

                with tempfile.NamedTemporaryFile(
                    "w",
                    encoding="utf-8",
                    dir=run_dir,
                    prefix=".mission-plan.",
                    suffix=".tmp",
                    delete=False,
                ) as f:
                    yaml.dump(plan_data, f, default_flow_style=False, sort_keys=False)
                    plan_tmp = Path(f.name)
                plan_tmp.replace(plan_path)

                with tempfile.NamedTemporaryFile(
                    "w",
                    encoding="utf-8",
                    dir=run_dir,
                    prefix=".task-list.",
                    suffix=".tmp",
                    delete=False,
                ) as f:
                    yaml.dump(
                        plan_data.get("tasks", []),
                        f,
                        default_flow_style=False,
                        sort_keys=False,
                    )
                    tasks_tmp = Path(f.name)
                tasks_tmp.replace(tasks_path)
            finally:
                fcntl.flock(lock_f, fcntl.LOCK_UN)


def _lock_and_write_events(log_path: Path, new_event: dict) -> None:
    """Read, modify, and write a JSON array in a thread-safe / process-safe way using file locking."""
    import fcntl

    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a+", encoding="utf-8") as f:
        try:
            fcntl.flock(f, fcntl.LOCK_EX)
            f.seek(0)
            content = f.read().strip()
            if content:
                try:
                    events = json.loads(content)
                    if not isinstance(events, list):
                        events = []
                except Exception:
                    events = []
            else:
                events = []

            events.append(new_event)
            f.seek(0)
            f.truncate()
            json.dump(events, f, indent=2)
        finally:
            try:
                fcntl.flock(f, fcntl.LOCK_UN)
            except Exception:
                pass


def log_execution_event(
    run_dir: Path, event_type: str, task_id: str, details: str
) -> None:
    """Log execution events to execution-log.json."""
    log_path = run_dir / "execution-log.json"
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "event": event_type,
        "task_id": task_id,
        "details": details,
    }
    _lock_and_write_events(log_path, event)


def log_policy_event(
    run_dir: Path, niyam_dir: Path, event_type: str, details: str
) -> None:
    """Log policy guardrail violation to policy-events.json (both run-level and global)."""
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "type": event_type,
        "details": details,
    }
    for log_path in (
        run_dir / "policy-events.json",
        niyam_dir / "evidence" / "policy-events.json",
    ):
        _lock_and_write_events(log_path, event)


def record_acceptance_criteria(
    run_dir: Path, task_id: str, criteria: list[str]
) -> None:
    """Record acceptance criteria as explicit review evidence for a task."""
    if not criteria:
        return

    import fcntl

    checks_path = run_dir / "acceptance-checks.json"
    checks_path.parent.mkdir(parents=True, exist_ok=True)
    with open(checks_path, "a+", encoding="utf-8") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            f.seek(0)
            content = f.read().strip()
            existing: list[dict] = []
            if content:
                try:
                    data = json.loads(content)
                    if isinstance(data, list):
                        existing = data
                except Exception:
                    existing = []

            existing = [e for e in existing if e.get("task_id") != task_id]
            timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            for i, criterion in enumerate(criteria, 1):
                existing.append(
                    {
                        "task_id": task_id,
                        "criterion_id": f"{task_id}-AC{i}",
                        "criterion": criterion,
                        "status": "requires_review",
                        "timestamp": timestamp,
                        "verification": (
                            "Recorded by Niyam. Attach a validation command or reviewer "
                            "verdict to mark this criterion as deterministically verified."
                        ),
                    }
                )

            f.seek(0)
            f.truncate()
            json.dump(existing, f, indent=2)
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


def parse_cli_token_usage(output_text: str, runtime: str | None = None) -> dict | None:
    """Parse token usage from Claude/Gemini/Codex CLI output."""
    patterns = {
        "claude": {
            "tokens": r"Total tokens:\s*([\d,]+)",
            "input": r"(?:input|prompt):\s*([\d,]+)",
            "output": r"(?:output|completion):\s*([\d,]+)",
            "cost": r"Total cost:\s*\$([\d.]+)",
        },
        "gemini": {
            "tokens": r"(?:Gemini tokens|Total tokens):\s*([\d,]+)",
            "input": r"(?:input|prompt):\s*([\d,]+)",
            "output": r"(?:output|candidates):\s*([\d,]+)",
            "cost": r"(?:Total cost|Cost):\s*\$([\d.]+)",
        },
        "codex": {
            "tokens": r"(?:Codex tokens|Total tokens):\s*([\d,]+)",
            "input": r"(?:input|prompt):\s*([\d,]+)",
            "output": r"(?:output|completion):\s*([\d,]+)",
            "cost": r"(?:Total cost|Cost):\s*\$([\d.]+)",
        },
    }

    # Filter patterns by runtime if specified
    runtimes_to_try = (
        [runtime.lower()]
        if runtime and runtime.lower() in patterns
        else list(patterns.keys())
    )

    # Try each pattern set...
    for rt in runtimes_to_try:
        pats = patterns[rt]
        total_match = re.search(pats["tokens"], output_text)
        if total_match:
            try:
                # Find input and output tokens
                input_match = re.search(pats["input"], output_text)
                output_match = re.search(pats["output"], output_text)
                cost_match = re.search(pats["cost"], output_text)

                input_tokens = (
                    int(input_match.group(1).replace(",", "")) if input_match else 0
                )
                output_tokens = (
                    int(output_match.group(1).replace(",", "")) if output_match else 0
                )
                total_tokens = int(total_match.group(1).replace(",", ""))
                cost_usd = float(cost_match.group(1)) if cost_match else None

                # Verify total matches sum or use parsed total
                if input_tokens == 0 and output_tokens == 0:
                    input_tokens = total_tokens

                return {
                    "runtime": rt,
                    "total_tokens": total_tokens,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "cost_usd": cost_usd,
                    "estimated": False,
                }
            except Exception:
                pass
    return None


def update_token_ledger(
    run_dir: Path,
    task_id: str,
    agent: str,
    runtime: str,
    input_tokens: int,
    output_tokens: int,
    estimated: bool = True,
    estimation_method: str | None = None,
    cost_override: float | None = None,
) -> None:
    """Update token & cost ledger with task metrics."""
    ledger_path = run_dir / "token-ledger.json"
    ledger = {"mission_id": run_dir.name, "events": [], "summary": {}}
    if ledger_path.exists():
        try:
            with open(ledger_path, encoding="utf-8") as f:
                ledger = json.load(f) or ledger
        except Exception:
            pass

    # Rates per million tokens
    rates = {
        "claude": {"input": 3.0, "output": 15.0},
        "gemini": {"input": 1.25, "output": 5.0},
        "codex": {"input": 2.5, "output": 10.0},
        "default": {"input": 3.0, "output": 15.0},
    }

    show_marketing = False
    baseline_multiplier = 5.0
    try:
        from niyam.core.config import find_niyam_root
        from niyam.core.security import safe_load_yaml

        repo_root = find_niyam_root(run_dir)
        if repo_root:
            runtimes_yaml_path = repo_root / ".niyam" / "runtimes.yaml"
            if runtimes_yaml_path.exists():
                data = safe_load_yaml(runtimes_yaml_path)
                if isinstance(data, dict):
                    # Check global pricing block
                    if "pricing" in data and isinstance(data["pricing"], dict):
                        for k, v in data["pricing"].items():
                            if isinstance(v, dict) and "input" in v and "output" in v:
                                rates[k.lower()] = {
                                    "input": float(v["input"]),
                                    "output": float(v["output"]),
                                }
                    # Check per-runtime pricing block
                    for k, v in data.items():
                        if isinstance(v, dict) and "pricing" in v:
                            p = v["pricing"]
                            if isinstance(p, dict) and "input" in p and "output" in p:
                                rates[k.lower()] = {
                                    "input": float(p["input"]),
                                    "output": float(p["output"]),
                                }

            # Load marketing config and multiplier from niyam.yaml
            niyam_yaml_path = repo_root / ".niyam" / "niyam.yaml"
            if niyam_yaml_path.exists():
                with open(niyam_yaml_path, encoding="utf-8") as f:
                    s_conf = yaml.safe_load(f) or {}
                    show_marketing = s_conf.get("show_marketing_metrics", False)
                    baseline_multiplier = float(s_conf.get("baseline_multiplier", 5.0))
    except Exception:
        pass

    r = rates.get(runtime.lower(), rates["default"])

    if cost_override is not None:
        cost = cost_override
    else:
        cost = (input_tokens * r["input"] + output_tokens * r["output"]) / 1_000_000.0

    event = {
        "task_id": task_id,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "agent": agent,
        "runtime": runtime,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "cost_usd": cost,
        "estimated": estimated,
    }

    if estimation_method:
        event["estimation_method"] = estimation_method

    if show_marketing:
        baseline_input = int(input_tokens * baseline_multiplier)
        baseline_output = int(output_tokens * baseline_multiplier)
        baseline_total = baseline_input + baseline_output
        baseline_cost = (
            baseline_input * r["input"] + baseline_output * r["output"]
        ) / 1_000_000.0
        savings_usd = baseline_cost - cost

        event["baseline_tokens"] = baseline_total
        event["baseline_cost_usd"] = baseline_cost
        event["savings_usd"] = savings_usd
        event["projected_estimate_labeled"] = (
            f"projected estimate based on configurable multiplier {baseline_multiplier}"
        )

    events = ledger.setdefault("events", [])
    # Remove existing event for this task if we are re-running/resuming
    events = [e for e in events if e.get("task_id") != task_id]
    events.append(event)
    ledger["events"] = events

    # Calculate summary
    total_input = sum(e.get("input_tokens", 0) for e in events)
    total_output = sum(e.get("output_tokens", 0) for e in events)
    total_tokens = total_input + total_output
    total_cost = sum(e.get("cost_usd", 0.0) for e in events)

    ledger["summary"] = {
        "total_input_tokens": total_input,
        "total_output_tokens": total_output,
        "total_tokens": total_tokens,
        "total_cost_usd": total_cost,
    }

    if show_marketing:
        total_baseline_tokens = sum(e.get("baseline_tokens", 0) for e in events)
        total_baseline_cost = sum(e.get("baseline_cost_usd", 0.0) for e in events)
        total_savings = total_baseline_cost - total_cost
        savings_pct = (
            (total_savings / total_baseline_cost * 100.0)
            if total_baseline_cost > 0
            else 0.0
        )

        ledger["summary"]["total_baseline_tokens"] = total_baseline_tokens
        ledger["summary"]["total_baseline_cost_usd"] = total_baseline_cost
        ledger["summary"]["total_savings_usd"] = total_savings
        ledger["summary"]["savings_percent"] = savings_pct

    with open(ledger_path, "w", encoding="utf-8") as f:
        json.dump(ledger, f, indent=2)


def run_validation_command(
    cmd: str, run_dir: Path, cwd: Path, console: Console
) -> bool:
    """Run a validation command safely and log the results."""
    from niyam.core.security import CommandSecurityError, safe_run_command

    with _print_lock:
        console.print(f"[dim]Running validation command: {cmd} inside {cwd}[/]")

    try:
        res = safe_run_command(cmd, cwd=cwd, timeout=120)
    except CommandSecurityError as e:
        with _print_lock:
            console.print(
                f"[bold red]🛑 Validation command blocked by security policy:[/] {e}"
            )
        # Log the blocked command
        val_path = run_dir / "validation-results.md"
        timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        with _validation_lock:
            mode = "a" if val_path.exists() else "w"
            with open(val_path, mode, encoding="utf-8") as f:
                f.write(f"\n## Validation Run - {timestamp}\n")
                f.write(f"**Command:** `{cmd}`\n")
                f.write(f"**Status:** 🛑 BLOCKED — {e}\n\n")
        return False

    # Save output to validation-results.md
    val_path = run_dir / "validation-results.md"
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    with _validation_lock:
        mode = "a" if val_path.exists() else "w"
        with open(val_path, mode, encoding="utf-8") as f:
            f.write(f"\n## Validation Run - {timestamp}\n")
            f.write(f"**Command:** `{cmd}`\n")
            f.write(f"**Exit Code:** `{res.returncode}`\n\n")
            f.write("### stdout\n```\n" + res.stdout + "\n```\n")
            if res.stderr:
                f.write("### stderr\n```\n" + res.stderr + "\n```\n")

    return res.returncode == 0


def compute_sha256(file_path: Path) -> str:
    """Compute the SHA-256 hash of a file."""
    import hashlib

    if not file_path.exists() or not file_path.is_file():
        return "DELETED"
    h = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                h.update(chunk)
        return h.hexdigest()
    except Exception as e:
        return f"ERROR: {e}"


def get_snapshot(cwd: Path, is_git: bool) -> dict[str, str]:
    """Get a dictionary mapping relative file paths to their hashes or status."""
    if is_git:
        res = subprocess.run(
            ["git", "status", "--porcelain"], cwd=cwd, capture_output=True, text=True
        )
        snapshot = {}
        for line in res.stdout.splitlines():
            if line.strip():
                parts = line.strip().split(maxsplit=1)
                if len(parts) == 2:
                    status, rel_path = parts[0], parts[1]
                    if not rel_path.startswith(".niyam"):
                        snapshot[rel_path] = status
        return snapshot
    else:
        snapshot = {}
        ignore_dirs = {
            ".git",
            ".niyam",
            "__pycache__",
            ".venv",
            "node_modules",
            ".antigravitycli",
        }
        for root, dirs, files in os.walk(cwd):
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            for f in files:
                full_path = Path(root) / f
                try:
                    rel_path = str(full_path.relative_to(cwd))
                    snapshot[rel_path] = compute_sha256(full_path)
                except Exception:
                    pass
        return snapshot


def backup_non_git_workspace(cwd: Path, backup_dir: Path) -> None:
    """Create a backup of all non-git workspace files."""
    if backup_dir.exists():
        try:
            shutil.rmtree(backup_dir)
        except Exception:
            pass
    backup_dir.mkdir(parents=True, exist_ok=True)
    ignore_dirs = {
        ".git",
        ".niyam",
        "__pycache__",
        ".venv",
        "node_modules",
        ".antigravitycli",
    }
    for root, dirs, files in os.walk(cwd):
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        for f in files:
            full_path = Path(root) / f
            try:
                rel_path = full_path.relative_to(cwd)
                dest_path = backup_dir / rel_path
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(full_path, dest_path)
            except Exception:
                pass


def restore_non_git_file(rel_path: str, backup_dir: Path, cwd: Path) -> None:
    """Restore a single file from the backup directory, or delete if it wasn't in backup."""
    backup_file = backup_dir / rel_path
    target_file = cwd / rel_path
    if backup_file.exists():
        try:
            target_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(backup_file, target_file)
        except Exception:
            pass
    else:
        if target_file.exists():
            try:
                target_file.unlink()
            except Exception:
                pass


# ── Git Worktree & Branching Utilities ─────────────────────────────────


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
    """Force-remove a git worktree and cleanup directories."""
    if worktree_path.exists():
        subprocess.run(
            ["git", "worktree", "remove", "--force", str(worktree_path)],
            cwd=repo_root,
            capture_output=True,
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
    worktree_path = run_dir / "worktrees" / task_id
    if branch_name is None:
        branch_name = f"niyam-{mission_id}-{task_id}"

    cleanup_worktree(repo_root, worktree_path, branch_name, console)
    worktree_path.parent.mkdir(parents=True, exist_ok=True)

    if branch_exists(repo_root, branch_name):
        with _print_lock:
            console.print(
                f"[{task_id}] [dim]Worktree branch {branch_name} already exists. Reusing branch...[/]"
            )
        subprocess.run(
            ["git", "worktree", "add", str(worktree_path), branch_name],
            cwd=repo_root,
            check=True,
            capture_output=True,
        )
    else:
        deps = task.get("depends_on", [])
        if not deps:
            parent_commit = get_current_head(repo_root)
        else:
            parent_commit = f"niyam-{mission_id}-{deps[0]}"

        with _print_lock:
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
        )

        # Merge other dependencies if any
        if len(deps) > 1:
            for other_dep in deps[1:]:
                other_branch = f"niyam-{mission_id}-{other_dep}"
                with _print_lock:
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
                )
                if res.returncode != 0:
                    with _print_lock:
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
        with _print_lock:
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
    with _print_lock:
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


def get_mock_change_path(allowed_files: list[str], task_id: str) -> str:
    """Resolve a relative path matching allowed patterns for mock writing."""
    for pattern in allowed_files:
        if pattern in ("*", "Any"):
            return f"change-{task_id}.txt"
        if pattern.endswith("/**"):
            return os.path.join(pattern[:-3], f"change-{task_id}.txt")
        if pattern.endswith("/*"):
            return os.path.join(pattern[:-2], f"change-{task_id}.txt")
        if "*" in pattern:
            return pattern.replace("**/", "").replace("*", f"change-{task_id}")
        return pattern
    return f"change-{task_id}.txt"


# ── Task Execution Thread Runner ───────────────────────────────────────


def run_hooks(stage: str, context: dict, niyam_dir: Path, console: Console) -> None:
    """Run lifecycle hooks for a given stage."""
    hooks_file = niyam_dir / "hooks.yaml"
    if not hooks_file.exists():
        hooks_file = niyam_dir / "hooks.yml"
        if not hooks_file.exists():
            return

    try:
        with open(hooks_file, encoding="utf-8") as f:
            hooks_config = yaml.safe_load(f) or {}
    except Exception as e:
        with _print_lock:
            console.print(f"[yellow]Warning: failed to load hooks.yaml: {e}[/]")
        return

    hooks = hooks_config.get("hooks", {}).get(stage, [])
    if not hooks:
        return

    with _print_lock:
        console.print(f"[dim]Running lifecycle hooks for {stage}...[/]")

    for hook in hooks:
        cmd = ""
        if isinstance(hook, str):
            cmd = hook
        elif isinstance(hook, dict):
            cmd = hook.get("run") or hook.get("cmd") or hook.get("script") or ""
            when = hook.get("when")
            if when:
                if "task.type" in when and "task" in context:
                    t_type = context["task"].get("type")
                    if f"'{t_type}'" not in when and f'"{t_type}"' not in when:
                        continue
                if "task.status" in when and "task" in context:
                    t_status = context["task"].get("status")
                    if f"'{t_status}'" not in when and f'"{t_status}"' not in when:
                        continue

        if not cmd:
            continue

        # Format placeholders
        for k, v in context.items():
            if k == "task":
                for tk, tv in v.items():
                    cmd = cmd.replace("{{" + f"task.{tk}" + "}}", str(tv))
            else:
                cmd = cmd.replace("{{" + k + "}}", str(v))

        with _print_lock:
            console.print(f"[dim]Executing hook: {cmd}[/]")

        try:
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if res.returncode != 0:
                with _print_lock:
                    console.print(
                        f"[yellow]Warning: hook execution returned exit code {res.returncode}[/]\n{res.stderr or res.stdout}"
                    )
        except Exception as e:
            with _print_lock:
                console.print(f"[yellow]Warning: hook execution failed: {e}[/]")


def execute_single_task(
    task: dict,
    run_dir: Path,
    niyam_dir: Path,
    repo_root: Path,
    mission_id: str,
    use_worktree: bool,
    project_config: any,
    console: Console,
    non_interactive: bool = False,
    branch_name: str | None = None,
) -> bool:
    """Execute a single task, isolating in worktree if enabled."""
    task_id = task["id"]
    task_cwd = repo_root
    worktree_path = None
    if branch_name is None:
        branch_name = f"niyam-{mission_id}-{task_id}"
    run_hooks("pre_task", {"mission_id": mission_id, "task": task}, niyam_dir, console)

    if use_worktree:
        try:
            worktree_path = create_worktree(
                repo_root, run_dir, mission_id, task, console, branch_name=branch_name
            )
            task_cwd = worktree_path
        except Exception as e:
            with _print_lock:
                console.print(f"[{task_id}] [bold red]Failed to setup worktree:[/] {e}")
            return False

    # Formulate prompt
    agent_file = (
        (worktree_path / ".niyam" if use_worktree else niyam_dir)
        / "agents"
        / f"{task['agent']}.md"
    )
    agent_instruction = ""
    if agent_file.exists():
        agent_instruction = agent_file.read_text(encoding="utf-8")

    requirement_file = run_dir / "requirement.md"
    requirement_content = ""
    if requirement_file.exists():
        requirement_content = requirement_file.read_text(encoding="utf-8")

    allowed_list = task.get("allowed_files") or task.get("files_allowed") or ["*"]
    blocked_list = task.get("blocked_list") or task.get("blocked_files") or []
    tdd_req = task.get("tdd_required") or False

    criteria_list = task.get("acceptance_criteria") or []
    criteria_str = (
        "\n".join(f"  - {c}" for c in criteria_list)
        if criteria_list
        else "  - None specified"
    )

    val_cmds = []
    task_validation = task.get("validation", {})
    if isinstance(task_validation, dict):
        val_cmds = task_validation.get("commands") or []
    elif hasattr(task_validation, "commands"):
        val_cmds = task_validation.commands or []
    val_cmds_str = (
        "\n".join(f"  - {c}" for c in val_cmds) if val_cmds else "  - None configured"
    )

    prompt_text = f"""TASK {task_id}: {task["title"]}
Type: {task.get("type", "generic")}
Assigned Agent: {task["agent"]}

--- AGENT SYSTEM PROMPT ---
{agent_instruction}

--- MISSION REQUIREMENT ---
{requirement_content}

--- TASK CONTRACT ---
Allowed files: {allowed_list}
Blocked files: {blocked_list}
TDD required: {tdd_req}
Acceptance criteria:
{criteria_str}

Validation commands that will run after your changes:
{val_cmds_str}

--- INSTRUCTIONS ---
Execute the changes required for this task.
Only modify files matching the allowed patterns above.
Do not modify files matching blocked patterns.
Do not perform destructive operations.
"""
    # Write prompt
    prompt_path = (
        worktree_path if use_worktree else run_dir
    ) / f"task-{task_id}-prompt.md"
    prompt_path.write_text(prompt_text, encoding="utf-8")

    is_test = os.environ.get("NIYAM_TEST") == "1"
    success = True

    is_git = is_git_repo(repo_root)
    backup_dir = run_dir / "backups" / task_id
    if not is_git:
        backup_non_git_workspace(task_cwd, backup_dir)

    # Take before snapshot
    before_snapshot = get_snapshot(task_cwd, is_git)

    if is_test:
        with _print_lock:
            console.print(f"[{task_id}] [dim]Mocking execution of {task_id}...[/]")
        log_execution_event(
            run_dir, "TASK_EXECUTION_MOCK", task_id, "Mocked execution successfully."
        )

        # Write dummy file to record change in worktree git diff only if writes_files is True
        if use_worktree and worktree_path and task.get("writes_files", True):
            allowed = task.get("allowed_files") or task.get("files_allowed") or ["*"]
            mock_rel_path = get_mock_change_path(allowed, task_id)
            dummy_file = worktree_path / mock_rel_path
            dummy_file.parent.mkdir(parents=True, exist_ok=True)

            ext = dummy_file.suffix.lower()
            if ext == ".py":
                content = f"# Changes by task {task_id}\n"
            elif ext == ".json":
                content = f'{{"mock_change": "Changes by task {task_id}"}}'
            elif ext in (".html", ".xml"):
                content = f"<!-- Changes by task {task_id} -->"
            elif ext in (".js", ".ts"):
                content = f"// Changes by task {task_id}\n"
            elif ext in (".yaml", ".yml"):
                content = f"# Changes by task {task_id}\n"
            else:
                content = f"Changes by task {task_id}"

            dummy_file.write_text(content, encoding="utf-8")
    else:
        plan_data = load_plan(run_dir)
        mission_meta = plan_data.get("mission", {})
        orchestrator = task.get("runtime") or mission_meta.get("orchestrator", "claude")
        parallel_limit = mission_meta.get("parallel", 1)

        configured_runtimes = []
        try:
            config = load_niyam_config(repo_root)
            configured_runtimes = [r.lower() for r in config.runtimes]
        except Exception:
            pass

        orchestrators_to_try = [orchestrator.lower()]
        for r in configured_runtimes:
            if r not in orchestrators_to_try:
                orchestrators_to_try.append(r)

        success = False
        tried_runtimes = []

        for current_orchestrator in orchestrators_to_try:
            tried_runtimes.append(current_orchestrator)
            
            if not shutil.which(current_orchestrator):
                with _print_lock:
                    console.print(
                        f"[{task_id}] [yellow]Orchestrator '{current_orchestrator}' CLI not found in PATH.[/]"
                    )
                if len(tried_runtimes) < len(orchestrators_to_try):
                    with _print_lock:
                        console.print(f"[{task_id}] [cyan]Attempting fallback runtime...[/]")
                    continue
                else:
                    if parallel_limit > 1 or non_interactive:
                        with _print_lock:
                            console.print(f"[{task_id}] To complete this task manually, run:")
                            console.print(f"  [bold]cat {prompt_path}[/]")
                    else:
                        with _print_lock:
                            console.print(
                                f"[yellow]Orchestrator '{current_orchestrator}' CLI not found in PATH.[/]"
                            )
                            console.print("Please run the task using the prompt at:")
                            console.print(f"  [bold]cat {prompt_path}[/]")
                            console.print(
                                "\nPress Enter once you have executed the prompt and completed the work..."
                            )
                        try:
                            input()
                        except (KeyboardInterrupt, EOFError):
                            pass
                    break

            with _print_lock:
                console.print(f"[{task_id}] [cyan]Invoking {current_orchestrator} CLI...[/]")
            timeout = task.get("timeout_seconds") or task.get("timeout") or 600
            run_failed = False
            exhaustion_detected = False
            task_log_path = (
                worktree_path if use_worktree else run_dir
            ) / f"task-{task_id}-output.log"

            try:
                if parallel_limit == 1 and not non_interactive:
                    subprocess.run(
                        [current_orchestrator, str(prompt_path)],
                        cwd=task_cwd,
                        check=True,
                        timeout=timeout,
                    )
                    success = True
                else:
                    with open(task_log_path, "w", encoding="utf-8") as log_f:
                        subprocess.run(
                            [current_orchestrator, str(prompt_path)],
                            cwd=task_cwd,
                            stdin=subprocess.DEVNULL,
                            stdout=log_f,
                            stderr=log_f,
                            check=True,
                            timeout=timeout,
                        )
                    success = True
            except subprocess.TimeoutExpired as e:
                run_failed = True
                with _print_lock:
                    console.print(
                        f"[{task_id}] [bold red]Orchestrator '{current_orchestrator}' timed out after {timeout} seconds: {e}[/]"
                    )
                log_execution_event(
                    run_dir,
                    "TASK_TIMEOUT",
                    task_id,
                    f"Execution on '{current_orchestrator}' timed out after {timeout} seconds.",
                )
            except subprocess.CalledProcessError as e:
                run_failed = True
                if task_log_path.exists():
                    try:
                        log_content = task_log_path.read_text(encoding="utf-8").lower()
                        exhaustion_keywords = [
                            "rate limit", "limit exceeded", "quota exceeded", 
                            "insufficient funds", "insufficient credit", "exhausted", 
                            "out of tokens", "token limit", "overloaded"
                        ]
                        if any(kw in log_content for kw in exhaustion_keywords):
                            exhaustion_detected = True
                    except Exception:
                        pass
                
                if not exhaustion_detected:
                    err_str = f"{e.stderr or ''} {e.stdout or ''}".lower()
                    if any(kw in err_str for kw in [
                        "rate limit", "limit exceeded", "quota exceeded", 
                        "insufficient funds", "insufficient credit", "exhausted", 
                        "out of tokens", "token limit", "overloaded"
                    ]):
                        exhaustion_detected = True

            if success:
                task["runtime"] = current_orchestrator
                break

            if run_failed:
                if exhaustion_detected and len(tried_runtimes) < len(orchestrators_to_try):
                    next_rt = orchestrators_to_try[len(tried_runtimes)]
                    with _print_lock:
                        console.print(
                            f"[{task_id}] [yellow]Token/rate limit reached on '{current_orchestrator}'. Trying fallback runtime '{next_rt}'...[/]"
                        )
                    log_execution_event(
                        run_dir,
                        "TASK_RUNTIME_FALLBACK",
                        task_id,
                        f"Rate limit/token exhaustion on '{current_orchestrator}'. Trying fallback '{next_rt}'.",
                    )
                    continue
                else:
                    if parallel_limit > 1 or non_interactive:
                        with _print_lock:
                            console.print(
                                f"[{task_id}] [red]Orchestrator failed in headless execution: {current_orchestrator}[/]"
                            )
                            console.print(
                                f"[{task_id}] To complete this task manually, run:"
                            )
                            console.print(f"  [bold]cat {prompt_path}[/]")
                    else:
                        with _print_lock:
                            console.print(
                                f"[yellow]Warning: {current_orchestrator} command failed. Asking for manual confirmation.[/]"
                            )
                        try:
                            input(
                                "Press Enter once you have completed the task manually in Claude/Codex..."
                            )
                            success = True
                        except (KeyboardInterrupt, EOFError):
                            pass
                    break

    # Mechanical Task Boundary Check
    if success:
        after_snapshot = get_snapshot(task_cwd, is_git)

        # Compare before and after to find all changed files
        changed_files = []
        if is_git:
            for f in after_snapshot:
                if f not in before_snapshot or after_snapshot[f] != before_snapshot[f]:
                    changed_files.append(f)
            # Find deleted files that were tracked but deleted (git status shows D)
            for f in before_snapshot:
                if f not in after_snapshot:
                    changed_files.append(f)
        else:
            all_keys = set(before_snapshot.keys()) | set(after_snapshot.keys())
            for f in all_keys:
                if before_snapshot.get(f) != after_snapshot.get(f):
                    changed_files.append(f)

        violated_files = []
        writes_files = task.get("writes_files", True)
        allowed_files = task.get("allowed_files") or task.get("files_allowed") or ["*"]
        blocked_files = task.get("blocked_files", [])

        # Load global security policies
        from niyam.policies.guard import load_security_policy

        sec_data = load_security_policy(repo_root)
        deny_patterns = sec_data.get("deny_write_patterns", [])
        allow_patterns = sec_data.get("allow_write_patterns", [])

        if changed_files:
            if not writes_files:
                # Task is writes_files: false, but changes were detected!
                violated_files = changed_files
            else:
                for f in changed_files:
                    # Check blocked_files patterns
                    if blocked_files and any(
                        fnmatch.fnmatch(f, pat) for pat in blocked_files
                    ):
                        violated_files.append(f)
                        continue
                    # Check allowed_files patterns
                    if allowed_files and "*" not in allowed_files:
                        if not any(fnmatch.fnmatch(f, pat) for pat in allowed_files):
                            violated_files.append(f)
                            continue
                    # Check global policies
                    if deny_patterns and any(
                        fnmatch.fnmatch(f, pat) for pat in deny_patterns
                    ):
                        violated_files.append(f)
                        continue
                    if (
                        allow_patterns
                        and len(allow_patterns) > 0
                        and not any(fnmatch.fnmatch(f, pat) for pat in allow_patterns)
                    ):
                        violated_files.append(f)
                        continue

        if violated_files:
            with _print_lock:
                console.print(
                    f"[{task_id}] [bold red]❌ Write restriction/boundary violation detected![/]"
                )
                for f in violated_files:
                    console.print(f"  - Reverting unauthorized change to: [red]{f}[/]")

            if is_git:
                for f in violated_files:
                    # Check if file existed in HEAD
                    res_cat = subprocess.run(
                        ["git", "cat-file", "-e", f"HEAD:{f}"],
                        cwd=task_cwd,
                        capture_output=True,
                    )
                    if res_cat.returncode == 0:
                        # Existed in HEAD: reset and checkout to restore original
                        subprocess.run(
                            ["git", "reset", "HEAD", f],
                            cwd=task_cwd,
                            capture_output=True,
                        )
                        subprocess.run(
                            ["git", "checkout", "--", f],
                            cwd=task_cwd,
                            capture_output=True,
                        )
                    else:
                        # Newly created: remove from index if staged, and delete from disk
                        subprocess.run(
                            ["git", "rm", "--cached", "-f", f],
                            cwd=task_cwd,
                            capture_output=True,
                        )
                        full_p = task_cwd / f
                        if full_p.exists() and not full_p.is_dir():
                            try:
                                full_p.unlink()
                            except Exception:
                                pass
            else:
                for f in violated_files:
                    restore_non_git_file(f, backup_dir, task_cwd)

            log_policy_event(
                run_dir=run_dir,
                niyam_dir=niyam_dir,
                event_type="WRITE_VIOLATION",
                details=f"Task {task_id} attempted unauthorized modifications to: {', '.join(violated_files)}",
            )
            success = False

    # Clean up non-git backup if it was created
    if not is_git and backup_dir.exists():
        try:
            shutil.rmtree(backup_dir)
        except Exception:
            pass

    # Acceptance Criteria Post-Check (Phase 2b)
    if success and task.get("acceptance_criteria"):
        criteria = task["acceptance_criteria"]
        with _print_lock:
            console.print(
                f"[{task_id}] Checking {len(criteria)} acceptance criteria..."
            )
        record_acceptance_criteria(run_dir, task_id, criteria)
        for i, criterion in enumerate(criteria, 1):
            log_execution_event(
                run_dir=run_dir,
                event_type="CRITERIA_CHECK",
                task_id=task_id,
                details=f"Criterion {i}: {criterion}",
            )

    # Validation Matrix Execution
    if success and project_config and project_config.validation:
        v_cmds = project_config.validation
        # stable order of validation
        checks = [
            ("format", v_cmds.format),
            ("lint", v_cmds.lint),
            ("typecheck", v_cmds.typecheck),
            ("build", v_cmds.build),
            ("test", v_cmds.test),
        ]

        # Load validation commands from task
        task_validation = task.get("validation", {})
        task_cmds = []
        if isinstance(task_validation, dict):
            task_cmds = task_validation.get("commands", [])
        elif hasattr(task_validation, "commands"):
            task_cmds = task_validation.commands

        # Run standard checks
        for name, cmd in checks:
            if cmd:
                cmd_success = run_validation_command(cmd, run_dir, task_cwd, console)
                if not cmd_success:
                    success = False
                    with _print_lock:
                        console.print(
                            f"[{task_id}] [bold red]❌ Validation check '{name}' failed![/]"
                        )
            else:
                # Log explicitly skipped
                val_path = run_dir / "validation-results.md"
                timestamp = (
                    datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                )
                with _validation_lock:
                    mode = "a" if val_path.exists() else "w"
                    with open(val_path, mode, encoding="utf-8") as f:
                        f.write(f"\n## Validation Check - {name} - {timestamp}\n")
                        f.write("**Status:** ℹ SKIPPED — Not configured\n\n")

        # Run task-specific checks
        if task_cmds:
            for i, cmd in enumerate(task_cmds, start=1):
                cmd_success = run_validation_command(cmd, run_dir, task_cwd, console)
                if not cmd_success:
                    success = False
                    with _print_lock:
                        console.print(
                            f"[{task_id}] [bold red]❌ Task validation command {i} failed![/]"
                        )

    # Record token usage in the ledger
    try:
        parsed_usage = None
        task_log_path = (
            worktree_path if use_worktree else run_dir
        ) / f"task-{task_id}-output.log"
        if task_log_path.exists():
            try:
                log_content = task_log_path.read_text(encoding="utf-8")
                task_runtime = task.get("runtime")
                if not task_runtime:
                    try:
                        plan_data = load_plan(run_dir)
                        task_runtime = plan_data.get("mission", {}).get(
                            "orchestrator", "claude"
                        )
                    except Exception:
                        task_runtime = "claude"
                parsed_usage = parse_cli_token_usage(log_content, runtime=task_runtime)
            except Exception:
                pass

        if parsed_usage:
            input_tokens = parsed_usage["input_tokens"]
            output_tokens = parsed_usage["output_tokens"]
            estimated = False
            estimation_method = None
            cost_usd = parsed_usage["cost_usd"]
        else:
            # Fall back to estimates
            estimated = True
            estimation_method = "char_count_heuristic"
            cost_usd = None

            # Estimate input tokens
            input_tokens = 0
            if prompt_path.exists():
                try:
                    prompt_content = prompt_path.read_text(encoding="utf-8")
                    input_tokens = max(1, len(prompt_content) // 4)
                except Exception:
                    pass

            # Estimate output tokens
            output_tokens = 0
            if task_log_path.exists():
                try:
                    output_content = task_log_path.read_text(encoding="utf-8")
                    output_tokens = len(output_content) // 4
                except Exception:
                    pass

            # If output_tokens is 0 (e.g. sequential mode, or log is empty), try git diff
            if output_tokens == 0 and is_git_repo(repo_root):
                try:
                    if use_worktree and worktree_path:
                        diff_cmd = (
                            ["git", "diff", "HEAD~1", "HEAD"]
                            if success
                            else ["git", "diff"]
                        )
                        diff_res = subprocess.run(
                            diff_cmd,
                            cwd=worktree_path,
                            capture_output=True,
                            text=True,
                        )
                    else:
                        diff_res = subprocess.run(
                            ["git", "diff"],
                            cwd=repo_root,
                            capture_output=True,
                            text=True,
                        )
                    if diff_res.returncode == 0 and diff_res.stdout:
                        output_tokens = max(1, len(diff_res.stdout) // 4)
                except Exception:
                    pass

            if output_tokens == 0 and success:
                output_tokens = 250  # fallback for a successful task

        # Get active runtime
        plan_data = load_plan(run_dir)
        mission_meta = plan_data.get("mission", {})
        orchestrator = task.get("runtime") or mission_meta.get("orchestrator", "claude")

        # Label token ledger entry with parsing or estimation details
        update_token_ledger(
            run_dir=run_dir,
            task_id=task_id,
            agent=task["agent"],
            runtime=orchestrator,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated=estimated,
            estimation_method=estimation_method,
            cost_override=cost_usd,
        )

    except Exception as e:
        with _print_lock:
            console.print(
                f"[{task_id}] [yellow]Warning: Failed to update token ledger:[/] {e}"
            )

    # Commit changes if worktree is active and task succeeded
    if success and use_worktree and worktree_path:
        try:
            commit_worktree_changes(worktree_path, task_id, console)
            # Retrieve and record commit SHA of this task
            res = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=worktree_path,
                capture_output=True,
                text=True,
            )
            if res.returncode == 0:
                task_commit_sha = res.stdout.strip()
                # Update task-list.yaml and mission-plan.yaml in execution flow
                with _plan_lock:
                    plan_data = load_plan(run_dir)
                    for t in plan_data.get("tasks", []):
                        if t["id"] == task_id:
                            t["commit_sha"] = task_commit_sha
                    save_plan(run_dir, plan_data)
        except Exception as e:
            with _print_lock:
                console.print(f"[{task_id}] [bold red]Failed to commit changes:[/] {e}")
            success = False

    # Cleanup worktree
    if use_worktree and worktree_path:
        cleanup_worktree(repo_root, worktree_path, branch_name, console)

    # Run post_task hook
    task_copy = dict(task)
    task_copy["status"] = "completed" if success else "failed"
    run_hooks(
        "post_task", {"mission_id": mission_id, "task": task_copy}, niyam_dir, console
    )

    return success


# ── Public Entry Points ───────────────────────────────────────────────


def run_mission_start(
    console: Console,
    parallel: int | None = None,
    worktree: bool | None = None,
    non_interactive: bool = False,
    mission_id: str | None = None,
) -> None:
    """Start or resume the latest approved mission."""
    from niyam.core.config import find_niyam_root
    from niyam.core.errors import NiyamConfigError

    repo_root = find_niyam_root()
    if not repo_root:
        raise NiyamConfigError("Not a Niyam workspace. Run 'niyam init' first.")
    niyam_dir = get_niyam_dir(repo_root)

    mission_id = resolve_mission_id(niyam_dir, mission_id)
    if not mission_id:
        console.print("[bold red]Error:[/] No missions found.")
        raise SystemExit(1)

    run_dir = niyam_dir / "runs" / mission_id
    approval_path = run_dir / "approval.json"

    # Check approval
    approved = False
    if approval_path.exists():
        try:
            with open(approval_path, encoding="utf-8") as f:
                app_data = json.load(f)
            if app_data.get("approved", False):
                approved = True
        except Exception:
            pass

    if not approved:
        if non_interactive and os.environ.get("NIYAM_CI_AUTO_APPROVE") == "1":
            # Check if auto-approve is allowed by guard config
            auto_approve_allowed = True
            try:
                config = load_niyam_config(repo_root)
                if hasattr(config.guard, "allow_ci_auto_approve"):
                    auto_approve_allowed = config.guard.allow_ci_auto_approve
            except Exception:
                pass  # If config can't be loaded, allow (backward compat)

            if not auto_approve_allowed:
                console.print(
                    "[bold red]Error:[/] NIYAM_CI_AUTO_APPROVE=1 is set but "
                    "guard.allow_ci_auto_approve is disabled in niyam.yaml."
                )
                raise SystemExit(1)

            console.print(
                "[cyan]Non-interactive mode & NIYAM_CI_AUTO_APPROVE=1: Auto-approving mission...[/]"
            )
            console.print(
                "[yellow]⚠ Warning: Mission approval gate was bypassed via environment variable.[/]"
            )
            approval_data = {
                "approved": True,
                "auto_approved": True,
                "timestamp": datetime.now(timezone.utc)
                .isoformat()
                .replace("+00:00", "Z"),
            }
            approval_path.write_text(
                json.dumps(approval_data, indent=2), encoding="utf-8"
            )
            # Log the auto-approve as a policy event for audit trail
            log_execution_event(
                run_dir,
                "POLICY_WARNING",
                "",
                "Mission auto-approved via NIYAM_CI_AUTO_APPROVE=1 (approval gate bypassed).",
            )
        else:
            console.print("[bold red]Error:[/] Mission has not been approved.")
            raise SystemExit(1)

    # Load plan
    plan_data = load_plan(run_dir)
    mission_meta = plan_data.get("mission", {})
    status = mission_meta.get("status", "planned")

    if status in ("completed", "failed"):
        console.print(f"[yellow]Mission '{mission_id}' is already {status}.[/]")
        return

    # Determine execution options
    plan_parallel = mission_meta.get("parallel", 1)
    plan_worktree = mission_meta.get("worktree", True)

    parallel_limit = parallel if parallel is not None else plan_parallel
    use_worktree = worktree if worktree is not None else plan_worktree

    # Check Git repository requirement
    is_git = is_git_repo(repo_root)
    if use_worktree:
        if not is_git:
            if worktree is True:
                console.print(
                    "[bold red]Error:[/] Git worktree isolation was requested, but this is not a Git repository."
                )
                raise SystemExit(1)
            else:
                if parallel_limit > 1:
                    console.print(
                        "[bold red]Error:[/] Parallel execution (concurrency > 1) requires a Git repository for worktree isolation."
                    )
                    raise SystemExit(1)
                else:
                    use_worktree = False
        elif not git_has_commits(repo_root):
            if worktree is True:
                console.print(
                    "[bold red]Error:[/] Git worktree isolation requires the repository to have at least one commit."
                )
                raise SystemExit(1)
            else:
                if parallel_limit > 1:
                    console.print(
                        "[bold red]Error:[/] Parallel execution (concurrency > 1) requires a Git repository with at least one commit for worktree isolation."
                    )
                    raise SystemExit(1)
                else:
                    use_worktree = False

    # Save the resolved settings and update status to running
    plan_data["mission"]["parallel"] = parallel_limit
    plan_data["mission"]["worktree"] = use_worktree
    plan_data["mission"]["status"] = "running"
    if (
        is_git
        and git_has_commits(repo_root)
        and not plan_data["mission"].get("base_sha")
    ):
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=repo_root, capture_output=True, text=True
        )
        if res.returncode == 0:
            plan_data["mission"]["base_sha"] = res.stdout.strip()
    save_plan(run_dir, plan_data)
    log_execution_event(
        run_dir,
        "MISSION_STARTED",
        "",
        f"Mission execution started (parallel={parallel_limit}, worktree={use_worktree}).",
    )
    run_hooks("pre_mission", {"mission_id": mission_id}, niyam_dir, console)

    # Read project.yaml validation commands
    project_config = None
    try:
        project_config = load_project_config(repo_root)
    except Exception:
        pass

    tasks = plan_data.get("tasks", [])
    completed_tasks = {t["id"] for t in tasks if t["status"] == "completed"}
    failed_tasks = {t["id"] for t in tasks if t["status"] == "failed"}
    running_tasks = set()
    futures_map = {}

    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor(max_workers=parallel_limit) as executor:
        while True:
            # Check if mission has been paused from outside
            current_plan = load_plan(run_dir)
            if current_plan["mission"]["status"] == "paused":
                with _print_lock:
                    console.print(
                        "[yellow]Mission execution paused. Waiting for active tasks to finish...[/]"
                    )
                if futures_map:
                    concurrent.futures.wait(futures_map.keys())
                run_hooks(
                    "post_mission",
                    {"mission_id": mission_id, "mission_status": "paused"},
                    niyam_dir,
                    console,
                )
                return

            # Find ready tasks
            ready_tasks = []
            task_by_id = {task["id"]: task for task in tasks}
            for t in tasks:
                t_id = t["id"]
                if t["status"] == "pending" and t_id not in running_tasks:
                    deps = t.get("depends_on", [])
                    finished_statuses = {"completed", "failed", "skipped"}
                    dep_tasks = [task_by_id[dep] for dep in deps if dep in task_by_id]

                    if all(dt["status"] in finished_statuses for dt in dep_tasks):
                        # If any dependency failed, this task must be skipped
                        if any(dt["status"] == "failed" for dt in dep_tasks):
                            t["status"] = "skipped"
                            save_plan(run_dir, plan_data)
                            log_execution_event(
                                run_dir,
                                "TASK_SKIPPED",
                                t_id,
                                "Dependency failed, skipping task.",
                            )
                            continue
                        ready_tasks.append(t)

            # Submit ready tasks up to concurrency capacity
            for t in ready_tasks:
                if len(running_tasks) < parallel_limit:
                    t_id = t["id"]
                    running_tasks.add(t_id)
                    t["status"] = "running"
                    save_plan(run_dir, plan_data)
                    log_execution_event(
                        run_dir, "TASK_STARTED", t_id, f"Running task: {t['title']}"
                    )

                    with _print_lock:
                        console.print(
                            Panel(
                                f"Running Task [cyan]{t_id}[/]: {t['title']}\nAgent: [bold]{t['agent']}[/]",
                                title=f"[bold]Task {t_id}[/]",
                                border_style="cyan",
                            )
                        )

                    # Submit task execution
                    future = executor.submit(
                        execute_single_task,
                        task=t,
                        run_dir=run_dir,
                        niyam_dir=niyam_dir,
                        repo_root=repo_root,
                        mission_id=mission_id,
                        use_worktree=use_worktree,
                        project_config=project_config,
                        console=console,
                        non_interactive=non_interactive,
                    )
                    futures_map[future] = t

            # If nothing is running and no more tasks are ready, we are done
            if not futures_map:
                break

            # Wait for at least one future to complete
            done, _ = concurrent.futures.wait(
                futures_map.keys(), return_when=concurrent.futures.FIRST_COMPLETED
            )

            for future in done:
                t = futures_map.pop(future)
                t_id = t["id"]
                running_tasks.remove(t_id)

                try:
                    success = future.result()
                    if success:
                        t["status"] = "completed"
                        completed_tasks.add(t_id)
                        save_plan(run_dir, plan_data)
                        log_execution_event(
                            run_dir,
                            "TASK_COMPLETED",
                            t_id,
                            f"Completed task: {t['title']}",
                        )
                        with _print_lock:
                            console.print(
                                f"[bold green]✓[/] Task {t_id} completed successfully.\n"
                            )
                    else:
                        t["status"] = "failed"
                        failed_tasks.add(t_id)
                        save_plan(run_dir, plan_data)
                        log_execution_event(
                            run_dir, "TASK_FAILED", t_id, "Task execution failed."
                        )
                        with _print_lock:
                            console.print(f"[bold red]❌[/] Task {t_id} failed.\n")
                except Exception as e:
                    t["status"] = "failed"
                    failed_tasks.add(t_id)
                    save_plan(run_dir, plan_data)
                    log_execution_event(
                        run_dir,
                        "TASK_FAILED",
                        t_id,
                        f"Exception during task execution: {e}",
                    )
                    with _print_lock:
                        console.print(
                            f"[bold red]❌[/] Task {t_id} failed with exception: {e}\n"
                        )

    # Determine final mission status
    final_plan = load_plan(run_dir)
    tasks_list = final_plan.get("tasks", [])
    any_failed = any(t["status"] == "failed" for t in tasks_list)
    any_skipped_due_to_failure = any(t["status"] == "skipped" for t in tasks_list)

    if any_failed or any_skipped_due_to_failure:
        final_plan["mission"]["status"] = "failed"
        save_plan(run_dir, final_plan)
        log_execution_event(
            run_dir,
            "MISSION_FAILED",
            "",
            "Mission execution failed due to task failures.",
        )
        run_hooks(
            "post_mission",
            {"mission_id": mission_id, "mission_status": "failed"},
            niyam_dir,
            console,
        )
        console.print(
            Panel(
                "[bold red]❌ Mission execution failed.[/]",
                title="[bold red]Mission Failed[/]",
                border_style="red",
            )
        )
        raise SystemExit(1)

    # Success integration (merge back if worktree was used)
    if use_worktree and is_git:
        try:
            merge_final_changes(repo_root, mission_id, tasks_list, console)
            delete_mission_branches(repo_root, mission_id, tasks_list, console)
        except Exception as e:
            console.print(f"[bold red]Error integrating final changes:[/] {e}")
            final_plan["mission"]["status"] = "failed"
            save_plan(run_dir, final_plan)
            raise SystemExit(1)

    # Complete mission
    final_plan["mission"]["status"] = "completed"
    save_plan(run_dir, final_plan)
    log_execution_event(
        run_dir, "MISSION_COMPLETED", "", "All tasks completed successfully."
    )
    run_hooks(
        "post_mission",
        {"mission_id": mission_id, "mission_status": "completed"},
        niyam_dir,
        console,
    )
    console.print(
        Panel(
            "[bold green]✓ Mission execution completed successfully![/]\nRun `niyam mission report` to generate evidence.",
            title="[bold green]Mission Success[/]",
            border_style="green",
        )
    )


def run_mission_pause(console: Console, mission_id: str | None = None) -> None:
    """Pause the currently running mission."""
    from niyam.core.config import find_niyam_root
    from niyam.core.errors import NiyamConfigError

    repo_root = find_niyam_root()
    if not repo_root:
        raise NiyamConfigError("Not a Niyam workspace. Run 'niyam init' first.")
    niyam_dir = get_niyam_dir(repo_root)

    mission_id = resolve_mission_id(niyam_dir, mission_id)
    if not mission_id:
        console.print("[bold red]Error:[/] No missions found.")
        raise SystemExit(1)

    run_dir = niyam_dir / "runs" / mission_id
    plan_data = load_plan(run_dir)
    status = plan_data["mission"]["status"]

    if status != "running":
        console.print(f"[yellow]Mission is not running (current status: {status}).[/]")
        return

    plan_data["mission"]["status"] = "paused"
    save_plan(run_dir, plan_data)
    log_execution_event(run_dir, "MISSION_PAUSED", "", "Mission paused by user.")
    console.print(f"[bold green]✓[/] Mission '[cyan]{mission_id}[/]' has been paused.")


def run_mission_resume(
    console: Console,
    parallel: int | None = None,
    worktree: bool | None = None,
    non_interactive: bool = False,
    mission_id: str | None = None,
) -> None:
    """Resume a paused mission."""
    from niyam.core.config import find_niyam_root
    from niyam.core.errors import NiyamConfigError

    repo_root = find_niyam_root()
    if not repo_root:
        raise NiyamConfigError("Not a Niyam workspace. Run 'niyam init' first.")
    niyam_dir = get_niyam_dir(repo_root)

    mission_id = resolve_mission_id(niyam_dir, mission_id)
    if not mission_id:
        console.print("[bold red]Error:[/] No missions found.")
        raise SystemExit(1)

    run_dir = niyam_dir / "runs" / mission_id
    plan_data = load_plan(run_dir)
    status = plan_data["mission"]["status"]

    if status != "paused":
        console.print(f"[yellow]Mission is not paused (current status: {status}).[/]")
        return

    # Start the execution
    run_mission_start(
        console,
        parallel=parallel,
        worktree=worktree,
        non_interactive=non_interactive,
        mission_id=mission_id,
    )


def run_mission_retry(
    console: Console,
    parallel: int | None = None,
    worktree: bool | None = None,
    non_interactive: bool = False,
    mission_id: str | None = None,
) -> None:
    """Retry failed tasks of the latest mission."""
    from niyam.core.config import find_niyam_root
    from niyam.core.errors import NiyamConfigError

    repo_root = find_niyam_root()
    if not repo_root:
        raise NiyamConfigError("Not a Niyam workspace. Run 'niyam init' first.")
    niyam_dir = get_niyam_dir(repo_root)

    mission_id = resolve_mission_id(niyam_dir, mission_id)
    if not mission_id:
        console.print("[bold red]Error:[/] No missions found.")
        raise SystemExit(1)

    run_dir = niyam_dir / "runs" / mission_id
    plan_data = load_plan(run_dir)

    tasks = plan_data.get("tasks", [])
    failed_any = False

    # Helper to recursively reset skipped tasks depending on failed ones
    def reset_downstream(task_id: str):
        for t in tasks:
            if task_id in t.get("depends_on", []) and t["status"] == "skipped":
                t["status"] = "pending"
                reset_downstream(t["id"])

    for t in tasks:
        if t["status"] in ("failed", "skipped"):
            t["status"] = "pending"
            failed_any = True
            reset_downstream(t["id"])

    if not failed_any:
        console.print("[yellow]No failed or skipped tasks found to retry.[/]")
        return

    plan_data["mission"]["status"] = "approved"
    save_plan(run_dir, plan_data)
    log_execution_event(
        run_dir, "MISSION_RETRIED", "", "Retrying failed/skipped tasks."
    )
    console.print(
        f"[bold green]✓[/] Re-queued tasks. Resuming mission [cyan]{mission_id}[/]..."
    )
    run_mission_start(
        console,
        parallel=parallel,
        worktree=worktree,
        non_interactive=non_interactive,
        mission_id=mission_id,
    )


def run_mission_skip(
    task_id: str,
    console: Console,
    parallel: int | None = None,
    worktree: bool | None = None,
    non_interactive: bool = False,
    mission_id: str | None = None,
) -> None:
    """Skip a specific task and resume execution."""
    from niyam.core.config import find_niyam_root
    from niyam.core.errors import NiyamConfigError

    repo_root = find_niyam_root()
    if not repo_root:
        raise NiyamConfigError("Not a Niyam workspace. Run 'niyam init' first.")
    niyam_dir = get_niyam_dir(repo_root)

    mission_id = resolve_mission_id(niyam_dir, mission_id)
    if not mission_id:
        console.print("[bold red]Error:[/] No missions found.")
        raise SystemExit(1)

    run_dir = niyam_dir / "runs" / mission_id
    plan_data = load_plan(run_dir)

    tasks = plan_data.get("tasks", [])
    target_task = None
    for t in tasks:
        if t["id"] == task_id:
            target_task = t
            break

    if not target_task:
        console.print(
            f"[bold red]Error:[/] Task '{task_id}' not found in mission plan."
        )
        raise SystemExit(1)

    target_task["status"] = "skipped"
    plan_data["mission"]["status"] = "approved"
    save_plan(run_dir, plan_data)
    log_execution_event(
        run_dir, "TASK_SKIPPED_BY_USER", task_id, "Task skipped by user intervention."
    )
    console.print(
        f"[bold green]✓[/] Marked task [cyan]{task_id}[/] as skipped. Resuming mission..."
    )
    run_mission_start(
        console,
        parallel=parallel,
        worktree=worktree,
        non_interactive=non_interactive,
        mission_id=mission_id,
    )


def run_mission_rollback(console: Console, mission_id: str | None = None) -> None:
    """Rollback all workspace changes back to the start of the latest mission."""
    from niyam.core.config import find_niyam_root
    from niyam.core.errors import NiyamConfigError

    repo_root = find_niyam_root()
    if not repo_root:
        raise NiyamConfigError("Not a Niyam workspace. Run 'niyam init' first.")
    niyam_dir = get_niyam_dir(repo_root)

    mission_id = resolve_mission_id(niyam_dir, mission_id)
    if not mission_id:
        console.print("[bold red]Error:[/] No missions found.")
        raise SystemExit(1)

    run_dir = niyam_dir / "runs" / mission_id
    plan_data = load_plan(run_dir)
    base_sha = plan_data["mission"].get("base_sha")

    if not base_sha:
        console.print(
            "[yellow]No base commit SHA recorded for this mission. Cannot rollback automatically.[/]"
        )
        return

    console.print(
        f"[cyan]Rolling back changes to base commit [bold]{base_sha}[/]...[/]"
    )
    res = subprocess.run(
        ["git", "checkout", base_sha, "--", "."],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    if res.returncode == 0:
        plan_data["mission"]["status"] = "failed"
        save_plan(run_dir, plan_data)
        console.print("[bold green]✓[/] Workspace rolled back successfully.")
    else:
        console.print(
            f"[bold red]Failed to rollback changes:[/] {res.stderr or res.stdout}"
        )
