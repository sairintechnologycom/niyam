"""Niyam mission task runner — execute task contracts and enforce boundaries."""

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
import yaml
import fnmatch
import re
import atexit
import signal
import sys
from rich.console import Console
from rich.panel import Panel

from niyam.core.config import load_niyam_config, find_niyam_root
from niyam.core.saas import SaaSClient
from niyam.core.utils import compute_sha256
from niyam.mission.utils import (
    print_lock,
    validation_lock,
    plan_lock,
    load_plan,
    save_plan,
)
from niyam.mission.worktree import (
    create_worktree,
    cleanup_worktree,
    is_git_repo,
    commit_worktree_changes,
)
from niyam.mission.state_machine import transition_task, log_mission_event

logger = logging.getLogger(__name__)


def log_execution_event(
    run_dir: Path, event_type: str, task_id: str, details: str
) -> None:
    """Append execution event to execution-log.json (JSON array format)."""
    log_path = run_dir / "execution-log.json"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    event = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "event": event_type,
        "task_id": task_id,
        "details": details,
    }

    import fcntl

    with open(log_path, "a+", encoding="utf-8") as f:
        try:
            fcntl.flock(f, fcntl.LOCK_EX)
            f.seek(0)
            content = f.read().strip()
            events = []
            if content:
                try:
                    events = json.loads(content)
                    if not isinstance(events, list):
                        events = []
                except Exception:
                    events = []

            events.append(event)
            f.seek(0)
            f.truncate()
            # No indent to match potential test expectations for compact format
            json.dump(events, f)
        finally:
            try:
                fcntl.flock(f, fcntl.LOCK_UN)
            except Exception:
                pass


def log_policy_event(
    run_dir: Path, niyam_dir: Path, event_type: str, details: str
) -> None:
    """Log policy guardrail violation to policy-events.json (JSON array format)."""
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "type": event_type,
        "details": details,
    }

    import fcntl

    for log_path in (
        run_dir / "policy-events.json",
        niyam_dir / "evidence" / "policy-events.json",
    ):
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "a+", encoding="utf-8") as f:
            try:
                fcntl.flock(f, fcntl.LOCK_EX)
                f.seek(0)
                content = f.read().strip()
                events = []
                if content:
                    try:
                        events = json.loads(content)
                        if not isinstance(events, list):
                            events = []
                    except Exception:
                        events = []

                events.append(event)
                f.seek(0)
                f.truncate()
                json.dump(events, f)
            finally:
                try:
                    fcntl.flock(f, fcntl.LOCK_UN)
                except Exception:
                    pass


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
    """Parse token usage from coding-agent CLI output via RuntimeSpec parsers."""
    from niyam.runtimes.executor import parse_usage_from_output
    from niyam.runtimes.registry import get_runtime_spec

    parser = "text_regex"
    if runtime:
        spec = get_runtime_spec(runtime)
        if spec is not None:
            parser = spec.usage_parser
    return parse_usage_from_output(output_text, parser=parser, runtime=runtime)


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
    is_waste: bool = False,
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

    rates = {
        "claude": {"input": 3.0, "output": 15.0},
        "gemini": {"input": 1.25, "output": 5.0},
        "codex": {"input": 2.5, "output": 10.0},
        "default": {"input": 3.0, "output": 15.0},
    }

    show_marketing = False
    baseline_multiplier = 5.0

    try:
        repo_root = find_niyam_root(run_dir)
        if repo_root:
            config = load_niyam_config(repo_root)
            # Use direct attribute access for Pydantic model
            show_marketing = config.show_marketing_metrics
            baseline_multiplier = config.baseline_multiplier

            runtimes_yaml_path = repo_root / ".niyam" / "runtimes.yaml"
            if runtimes_yaml_path.exists():
                with open(runtimes_yaml_path) as f:
                    r_data = yaml.safe_load(f) or {}
                    if "pricing" in r_data:
                        for k, v in r_data["pricing"].items():
                            rates[k.lower()] = v
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
        "is_waste": is_waste,
    }

    if estimation_method and estimated:
        event["estimation_method"] = estimation_method

    if show_marketing:
        baseline_input = int(input_tokens * baseline_multiplier)
        baseline_output = int(output_tokens * baseline_multiplier)
        baseline_total = baseline_input + baseline_output
        baseline_cost = (
            baseline_input * r["input"] + baseline_output * r["output"]
        ) / 1_000_000.0
        # Ensure at least some savings if cost > 0
        savings_usd = max(0.0, baseline_cost - cost)
        if cost > 0 and savings_usd == 0:
            savings_usd = cost * (baseline_multiplier - 1.0)

        event["baseline_tokens"] = baseline_total
        event["baseline_cost_usd"] = baseline_cost
        event["savings_usd"] = savings_usd
        event["projected_estimate_labeled"] = (
            f"projected estimate based on configurable multiplier {baseline_multiplier}"
        )

    events = ledger.setdefault("events", [])
    events = [e for e in events if e.get("task_id") != task_id]
    events.append(event)
    ledger["events"] = events

    total_input = sum(e.get("input_tokens", 0) for e in events)
    total_output = sum(e.get("output_tokens", 0) for e in events)
    total_tokens = total_input + total_output
    total_cost = sum(e.get("cost_usd", 0.0) for e in events)
    total_wasted = sum(e.get("cost_usd", 0.0) for e in events if e.get("is_waste"))

    ledger["summary"] = {
        "total_input_tokens": total_input,
        "total_output_tokens": total_output,
        "total_tokens": total_tokens,
        "total_cost_usd": total_cost,
        "total_wasted_cost_usd": total_wasted,
    }

    if show_marketing:
        total_baseline_tokens = sum(e.get("baseline_tokens", 0) for e in events)
        total_baseline_cost = sum(e.get("baseline_cost_usd", 0.0) for e in events)
        total_savings = sum(e.get("savings_usd", 0.0) for e in events)
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

    try:
        from niyam.core.cost import (
            get_branch_name,
            get_repo_name,
            CostEvent,
        )

        repo_root_for_global = run_dir.parent.parent.parent
        CostEvent(
            timestamp=event["timestamp"],
            session_id=run_dir.name,
            task_id=task_id,
            tool_name=runtime,
            model=runtime,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost=cost,
            repo=get_repo_name(repo_root_for_global),
            branch=get_branch_name(repo_root_for_global),
            status="success",
            notes=f"Logged automatically during execution by agent {agent}.",
        )
    except Exception:
        pass

    return cost


def run_validation_command(
    cmd: str, run_dir: Path, cwd: Path, console: Console
) -> bool:
    """Run a validation command safely and log the results."""
    from niyam.core.security import CommandSecurityError, safe_run_command

    with print_lock:
        console.print(f"[dim]Running validation command: {cmd} inside {cwd}[/]")

    try:
        res = safe_run_command(cmd, cwd=cwd, timeout=120)
    except CommandSecurityError as e:
        with print_lock:
            console.print(
                f"[bold red]🛑 Validation command blocked by security policy:[/] {e}"
            )
        val_path = run_dir / "validation-results.md"
        timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        with validation_lock:
            mode = "a" if val_path.exists() else "w"
            with open(val_path, mode, encoding="utf-8") as f:
                f.write(f"\n## Validation Run - {timestamp}\n")
                f.write(f"**Command:** `{cmd}`\n")
                f.write(f"**Status:** 🛑 BLOCKED — {e}\n\n")
        return False

    val_path = run_dir / "validation-results.md"
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    with validation_lock:
        mode = "a" if val_path.exists() else "w"
        with open(val_path, mode, encoding="utf-8") as f:
            f.write(f"\n## Validation Run - {timestamp}\n")
            f.write(f"**Command:** `{cmd}`\n")
            f.write(f"**Exit Code:** `{res.returncode}`\n\n")
            f.write("### stdout\n```\n" + res.stdout + "\n```\n")
            if res.stderr:
                f.write("### stderr\n```\n" + res.stderr + "\n```\n")

    return res.returncode == 0


def get_snapshot(cwd: Path, is_git: bool) -> dict[str, str]:
    """Get a dictionary mapping relative file paths to their hashes or status."""
    ignore_dirs = {
        ".git",
        ".niyam",
        "__pycache__",
        ".venv",
        ".pytest_cache",
        ".ruff_cache",
        ".mypy_cache",
        "node_modules",
        ".antigravitycli",
    }

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
                    path_parts = Path(rel_path).parts
                    if not any(p in ignore_dirs for p in path_parts):
                        snapshot[rel_path] = status
        return snapshot
    else:
        snapshot = {}
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


def check_overlap(files1: list[str], files2: list[str]) -> bool:
    """Check if two sets of allowed files/globs overlap.

    Robustly handles nested globs like 'src/**' and 'src/components/*'.
    """
    if not files1 or not files2:
        return False

    def normalize(p: str) -> str:
        p = p.strip()
        if p.startswith("./"):
            p = p[2:]
        return p

    f1 = [normalize(f) for f in files1]
    f2 = [normalize(f) for f in files2]

    # Quick exit for universal access
    universal = {"*", "all", "**", "./*", "Any"}
    if any(p in universal for p in f1) or any(p in universal for p in f2):
        return True

    for p1 in f1:
        for p2 in f2:
            # 1. Exact match
            if p1 == p2:
                return True

            # 2. Directory prefix check (e.g. 'src/**' vs 'src/app.py')
            # Strip glob characters to get base path
            b1 = p1.split("*")[0].rstrip("/")
            b2 = p2.split("*")[0].rstrip("/")

            if not b1 or not b2:  # Root overlap
                return True

            # If one base path is a parent of another, they MIGHT overlap
            # We check if b1 is a prefix of b2 or vice-versa
            if b1 == b2:
                return True

            if b1.startswith(b2 + "/") or b2.startswith(b1 + "/"):
                # They are in the same directory branch.
                # If the parent one is a glob, they definitely overlap.
                # E.g. 'src/**' (b1='src') vs 'src/components/x.py' (b2='src/components/x.py')
                if "*" in p1 or "*" in p2:
                    return True

            # 3. Fnmatch fallback for simple cases (e.g. *.py)
            try:
                if fnmatch.fnmatch(p1, p2) or fnmatch.fnmatch(p2, p1):
                    return True
            except Exception:
                pass

    return False


_active_frozen_modes: dict[Path, int] = {}


def apply_path_freeze(frozen_paths: list[str], repo_root: Path) -> dict[Path, int]:
    """Change permissions of frozen files/directories to read-only."""
    import stat

    original_modes = {}

    for path_str in frozen_paths:
        try:
            path = (repo_root / path_str).resolve()
            if not path.exists():
                continue

            def make_read_only(p: Path):
                if p in original_modes:
                    return
                try:
                    mode = p.stat().st_mode
                    original_modes[p] = mode
                    p.chmod(mode & ~stat.S_IWRITE & ~stat.S_IWGRP & ~stat.S_IWOTH)
                    _active_frozen_modes[p] = mode
                except Exception:
                    pass

            if path.is_dir():
                make_read_only(path)
                for item in path.rglob("*"):
                    make_read_only(item)
            else:
                make_read_only(path)
        except Exception:
            pass

    return original_modes


def restore_path_freeze(original_modes: dict[Path, int]) -> None:
    """Restore original permissions to frozen paths."""
    for path, mode in original_modes.items():
        try:
            if path.exists():
                path.chmod(mode)
            if path in _active_frozen_modes:
                del _active_frozen_modes[path]
        except Exception:
            pass


def _emergency_cleanup_permissions():
    """Emergency helper to restore permissions if process crashes while frozen."""
    if _active_frozen_modes:
        for path, mode in list(_active_frozen_modes.items()):
            try:
                if path.exists():
                    path.chmod(mode)
            except Exception:
                pass
        _active_frozen_modes.clear()


atexit.register(_emergency_cleanup_permissions)


def _signal_handler(signum, frame):
    _emergency_cleanup_permissions()
    sys.exit(128 + signum)


for sig in (signal.SIGTERM, signal.SIGINT, getattr(signal, "SIGHUP", None)):
    if sig is not None:
        try:
            signal.signal(sig, _signal_handler)
        except ValueError:
            pass


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
        with print_lock:
            console.print(f"[yellow]Warning: failed to load hooks.yaml: {e}[/]")
        return

    hooks = hooks_config.get("hooks", {}).get(stage, [])
    if not hooks:
        return

    with print_lock:
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

        for k, v in context.items():
            if k == "task":
                for tk, tv in v.items():
                    cmd = cmd.replace("{{" + f"task.{tk}" + "}}", str(tv))
            else:
                cmd = cmd.replace("{{" + k + "}}", str(v))

        try:
            from niyam.core.security import CommandSecurityError, safe_run_command

            repo_root = niyam_dir.parent
            res = safe_run_command(cmd, cwd=repo_root, capture_output=True, text=True)
            if res.returncode != 0:
                with print_lock:
                    console.print(
                        f"[yellow]Warning: hook execution returned exit code {res.returncode}[/]\n{res.stderr or res.stdout}"
                    )
        except CommandSecurityError as e:
            with print_lock:
                console.print(
                    f"[bold red]🛑 Hook command blocked by security policy:[/] {e}"
                )
        except Exception as e:
            with print_lock:
                console.print(f"[yellow]Warning: hook execution failed: {e}[/]")


def _notify_saas_event(run_dir: Path, event_type: str, payload: dict) -> None:
    """Helper to fire an asynchronous-ish (non-blocking) webhook notification."""
    try:
        config = load_niyam_config(run_dir.parent.parent)
        if config.saas.enabled:
            client = SaaSClient(run_dir.parent.parent)
            client.trigger_webhook(event_type, payload)
    except Exception:
        # Silently fail for webhooks to avoid breaking the core execution loop
        pass


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
    task_dir = run_dir / "tasks" / task_id
    task_dir.mkdir(parents=True, exist_ok=True)

    task_cwd = repo_root
    worktree_path = None
    if branch_name is None:
        branch_name = f"niyam-{mission_id}-{task_id}"
    run_hooks("pre_task", {"mission_id": mission_id, "task": task}, niyam_dir, console)

    if task.get("approval_required") and not non_interactive:
        transition_task(
            run_dir,
            task_id,
            "awaiting_approval",
            reason="Manual approval required by contract.",
        )
        with print_lock:
            console.print(
                Panel(
                    f"Task [bold cyan]{task_id}[/] requires approval before execution.\n"
                    f"Evidence dir: [bold]{task_dir}[/]\n"
                    "Waiting for approval...",
                    title="[bold yellow]Awaiting Approval[/]",
                    border_style="yellow",
                )
            )

        _notify_saas_event(
            run_dir,
            "TASK_APPROVAL_REQUESTED",
            {"task_id": task_id, "title": task["title"]},
        )

        # Simple polling logic or wait for local approval.json
        approval_file = task_dir / "approval.json"
        while not approval_file.exists():
            # For now, we wait for a local file to be created in the task dir
            time.sleep(5)

        try:
            with open(approval_file, encoding="utf-8") as f:
                approval_data = json.load(f)
            if not approval_data.get("approved"):
                transition_task(
                    run_dir,
                    task_id,
                    "failed",
                    reason="Task denied by reviewer.",
                    actor="human",
                )
                with print_lock:
                    console.print(f"[{task_id}] [bold red]Task denied by reviewer.[/]")
                return False

            transition_task(
                run_dir,
                task_id,
                "approved",
                reason="Task approved by human.",
                actor="human",
            )
            with print_lock:
                console.print(
                    f"[{task_id}] [bold green]Task approved. Proceeding...[/]"
                )
        except Exception:
            return False

    if use_worktree:
        transition_task(
            run_dir, task_id, "preparing", reason="Setting up worktree isolation."
        )
        try:
            worktree_path = create_worktree(
                repo_root, run_dir, mission_id, task, console, branch_name=branch_name
            )
            task_cwd = worktree_path

            # Inject task-specific active guardrails (Task Isolation)
            try:
                allowed_list = (
                    task.get("allowed_files") or task.get("files_allowed") or ["*"]
                )
                blocked_list = (
                    task.get("blocked_list") or task.get("blocked_files") or []
                )

                hook_cache_dir = worktree_path / ".niyam" / "hook-cache"
                hook_cache_dir.mkdir(parents=True, exist_ok=True)
                hook_config_path = hook_cache_dir / "guard-config.json"

                # Load existing base config to preserve global deny lists
                base_config = {}
                if hook_config_path.exists():
                    try:
                        base_config = json.loads(
                            hook_config_path.read_text(encoding="utf-8")
                        )
                    except Exception:
                        pass

                task_hook_config = {
                    "guard_enabled": True,
                    "deny_patterns": base_config.get("deny_patterns", []),
                    "warn_patterns": base_config.get("warn_patterns", []),
                    "deny_write_patterns": blocked_list
                    + base_config.get("deny_write_patterns", []),
                    "allow_write_patterns": base_config.get("allow_write_patterns", []),
                    "frozen_paths": allowed_list,  # Restrict active writes to this task's scope
                }
                hook_config_path.write_text(
                    json.dumps(task_hook_config, indent=2), encoding="utf-8"
                )
            except Exception as e:
                with print_lock:
                    console.print(
                        f"[{task_id}] [dim yellow]Warning: Failed to inject task-specific guardrails: {e}[/]"
                    )

        except Exception as e:
            transition_task(
                run_dir, task_id, "failed", reason=f"Failed to setup worktree: {e}"
            )
            with print_lock:
                console.print(f"[{task_id}] [bold red]Failed to setup worktree:[/] {e}")
            return False

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

    # Generate Task-Specific Context (Context Router)
    repo_map_str = ""
    related_list = []
    try:
        from niyam.mission.planner import get_repo_map
        from niyam.core.context import ContextRouter

        full_map = get_repo_map(repo_root)
        router = ContextRouter(repo_root)
        allowed_list = task.get("allowed_files") or task.get("files_allowed") or ["*"]

        related_list = router.get_related_paths(allowed_list)
        repo_map_str = router.prune_repo_map(
            full_map, allowed_list, related_files=related_list
        )
    except Exception as e:
        logger.debug("Failed to generate pruned repo map: %s", e)

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
    healing_prompt = task.get("healing_prompt")
    healing_section = ""
    if healing_prompt:
        healing_section = f"""
--- AUTO-HEAL CONTEXT ---
The previous attempt failed. Use this failure context to make a targeted fix:
{healing_prompt}
"""

    prompt_text = f"""TASK {task_id}: {task["title"]}
Type: {task.get("type", "generic")}
Assigned Agent: {task["agent"]}

--- AGENT SYSTEM PROMPT ---
{agent_instruction}

--- MISSION REQUIREMENT ---
{requirement_content}

--- REPOSITORY CONTEXT (Pruned) ---
{repo_map_str}

--- TASK CONTRACT ---
Allowed files: {allowed_list}
Related files: {related_list}
Blocked files: {blocked_list}
TDD required: {tdd_req}
Acceptance criteria:
{criteria_str}

Validation commands that will run after your changes:
{val_cmds_str}
{healing_section}

--- INSTRUCTIONS ---
Execute the changes required for this task.
Only modify files matching the allowed patterns above.
Do not modify files matching blocked patterns.
Do not perform destructive operations.
"""
    prompt_path = task_dir / "prompt.md"
    prompt_path.write_text(prompt_text, encoding="utf-8")

    transition_task(run_dir, task_id, "running", actor=task["agent"])

    is_test = os.environ.get("NIYAM_TEST") == "1"
    success = True

    is_git = is_git_repo(repo_root)
    backup_dir = task_dir / "backup"
    if not is_git:
        backup_non_git_workspace(task_cwd, backup_dir)

    before_snapshot = get_snapshot(task_cwd, is_git)

    if is_test:
        with print_lock:
            console.print(f"[{task_id}] [dim]Mocking execution of {task_id}...[/]")
        log_mission_event(
            run_dir,
            "TASK_EXECUTION_MOCK",
            task_id=task_id,
            details="Mocked execution successfully.",
        )

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
        original_modes = {}
        frozen_paths = []
        try:
            config = load_niyam_config(repo_root)
            frozen_paths = config.guard.frozen_paths
        except Exception:
            pass
        if frozen_paths:
            original_modes = apply_path_freeze(frozen_paths, task_cwd)

        try:
            plan_data = load_plan(run_dir)
            mission_meta = plan_data.get("mission", {})
            orchestrator = task.get("runtime") or mission_meta.get(
                "orchestrator", "claude"
            )
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
                    with print_lock:
                        console.print(
                            f"[{task_id}] [yellow]Orchestrator '{current_orchestrator}' CLI not found in PATH.[/]"
                        )
                    if len(tried_runtimes) < len(orchestrators_to_try):
                        continue
                    else:
                        if parallel_limit > 1 or non_interactive:
                            pass
                        else:
                            with print_lock:
                                console.print(
                                    "Please run the task using the prompt at:"
                                )
                                console.print(f"  [bold]cat {prompt_path}[/]")
                                console.print(
                                    "\nPress Enter once you have executed the prompt and completed the work..."
                                )
                            try:
                                input()
                            except (KeyboardInterrupt, EOFError):
                                pass
                        break

                timeout = task.get("timeout_seconds") or task.get("timeout") or 600
                run_failed = False
                exhaustion_detected = False
                task_log_path = task_dir / "output.log"

                try:
                    from niyam.runtimes.executor import run_runtime

                    # Keep swarm lock ownership alive for long-running tasks
                    hb_stop = None
                    try:
                        from niyam.core.swarm import start_heartbeat_thread

                        agent_id = f"{Path(run_dir).name}:{task_id}"
                        # Prefer mission-scoped agent id if locks used that form
                        try:
                            from niyam.mission.executor import _task_agent_id

                            agent_id = _task_agent_id(Path(run_dir).name, task_id)
                        except Exception:
                            pass
                        hb_stop = start_heartbeat_thread(
                            agent_id=agent_id,
                            role=task.get("agent", "agent"),
                            task_id=task_id,
                            repo_root=repo_root,
                            interval_seconds=30,
                        )
                    except Exception:
                        hb_stop = None

                    try:
                        result = run_runtime(
                            current_orchestrator,
                            prompt_file=prompt_path,
                            cwd=task_cwd,
                            model=task.get("model"),
                            tier=task.get("tier"),
                            mode="exec",
                            timeout=int(timeout),
                            repo_root=repo_root,
                            log_path=task_log_path,
                            include_sandbox=True,
                        )
                    finally:
                        if hb_stop is not None:
                            try:
                                hb_stop()
                            except Exception:
                                pass

                    if result.usage:
                        try:
                            update_token_ledger(
                                run_dir=run_dir,
                                task_id=task_id,
                                agent=task.get("agent", "agent"),
                                runtime=current_orchestrator,
                                input_tokens=int(result.usage.get("input_tokens") or 0),
                                output_tokens=int(
                                    result.usage.get("output_tokens") or 0
                                ),
                                estimated=bool(result.usage.get("estimated", False)),
                                cost_override=result.usage.get("cost_usd"),
                            )
                        except Exception:
                            pass

                    if result.success:
                        success = True
                    else:
                        run_failed = True
                        exhaustion_detected = bool(result.exhaustion_detected)
                        # Also inspect log for quota/rate-limit messages when the
                        # process failed (covers mocks and non-zero exits).
                        if not exhaustion_detected and task_log_path.exists():
                            try:
                                log_content = task_log_path.read_text(
                                    encoding="utf-8"
                                ).lower()
                                exhaustion_keywords = [
                                    "rate limit",
                                    "limit exceeded",
                                    "quota exceeded",
                                    "insufficient funds",
                                    "insufficient credit",
                                    "exhausted",
                                    "out of tokens",
                                    "token limit",
                                    "overloaded",
                                ]
                                if any(
                                    kw in log_content for kw in exhaustion_keywords
                                ):
                                    exhaustion_detected = True
                            except Exception:
                                pass
                except Exception:
                    run_failed = True
                    if task_log_path.exists():
                        try:
                            log_content = task_log_path.read_text(
                                encoding="utf-8"
                            ).lower()
                            exhaustion_keywords = [
                                "rate limit",
                                "limit exceeded",
                                "quota exceeded",
                                "insufficient funds",
                                "insufficient credit",
                                "exhausted",
                                "out of tokens",
                                "token limit",
                                "overloaded",
                            ]
                            if any(kw in log_content for kw in exhaustion_keywords):
                                exhaustion_detected = True
                        except Exception:
                            pass

                if success:
                    task["runtime"] = current_orchestrator
                    break

                if run_failed:
                    if exhaustion_detected and len(tried_runtimes) < len(
                        orchestrators_to_try
                    ):
                        continue
                    else:
                        if parallel_limit > 1 or non_interactive:
                            pass
                        else:
                            try:
                                input(
                                    "Press Enter once you have completed the task manually in Claude/Codex..."
                                )
                                success = True
                            except (KeyboardInterrupt, EOFError):
                                pass
                        break
        finally:
            if original_modes:
                restore_path_freeze(original_modes)

    if success:
        transition_task(run_dir, task_id, "validating")
        after_snapshot = get_snapshot(task_cwd, is_git)

        changed_files = []
        if is_git:
            for f in after_snapshot:
                if f not in before_snapshot or after_snapshot[f] != before_snapshot[f]:
                    changed_files.append(f)
            for f in before_snapshot:
                if f not in after_snapshot:
                    changed_files.append(f)
        else:
            all_keys = set(before_snapshot.keys()) | set(after_snapshot.keys())
            for f in all_keys:
                if before_snapshot.get(f) != after_snapshot.get(f):
                    changed_files.append(f)

        # Capture task-specific diff
        if changed_files and is_git:
            try:
                # If using worktree, diff HEAD~1..HEAD (since we haven't committed yet, wait,
                # we commit at the end of the function. So right now it's just dirty changes in worktree)
                diff_cmd = ["git", "diff"]
                res_diff = subprocess.run(
                    diff_cmd, cwd=task_cwd, capture_output=True, text=True
                )
                if res_diff.returncode == 0:
                    (task_dir / "diff.patch").write_text(
                        res_diff.stdout, encoding="utf-8"
                    )
            except Exception:
                pass

        violated_files = []
        writes_files = task.get("writes_files", True)
        allowed_files = task.get("allowed_files") or task.get("files_allowed") or ["*"]
        blocked_files = task.get("blocked_files", [])

        from niyam.policies.guard import load_security_policy

        sec_data = load_security_policy(repo_root)
        deny_patterns = sec_data.get("deny_write_patterns", [])
        allow_patterns = sec_data.get("allow_write_patterns", [])

        if changed_files:
            if not writes_files:
                violated_files = changed_files
            else:
                for f in changed_files:
                    if blocked_files and any(
                        fnmatch.fnmatch(f, pat) for pat in blocked_files
                    ):
                        violated_files.append(f)
                        continue
                    if allowed_files and "*" not in allowed_files:
                        if not any(fnmatch.fnmatch(f, pat) for pat in allowed_files):
                            violated_files.append(f)
                            continue
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
            if is_git:
                for f in violated_files:
                    res_cat = subprocess.run(
                        ["git", "cat-file", "-e", f"HEAD:{f}"],
                        cwd=task_cwd,
                        capture_output=True,
                    )
                    if res_cat.returncode == 0:
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

            log_mission_event(
                run_dir,
                "POLICY_VIOLATION",
                task_id=task_id,
                details=f"Task attempted unauthorized modifications to: {', '.join(violated_files)}",
                type="WRITE_VIOLATION",
            )
            log_policy_event(
                run_dir,
                niyam_dir,
                "WRITE_VIOLATION",
                f"Unauthorized write attempt by {task_id} to: {', '.join(violated_files)}",
            )
            success = False

    if not is_git and backup_dir.exists():
        try:
            shutil.rmtree(backup_dir)
        except Exception:
            pass

    if success and task.get("acceptance_criteria"):
        criteria = task["acceptance_criteria"]
        record_acceptance_criteria(run_dir, task_id, criteria)
        for i, criterion in enumerate(criteria, 1):
            log_mission_event(
                run_dir,
                "CRITERIA_CHECK",
                task_id=task_id,
                details=f"Criterion {i}: {criterion}",
            )

    validation_results = []
    if success and project_config and project_config.validation:
        v_cmds = project_config.validation
        checks = [
            ("format", v_cmds.format),
            ("lint", v_cmds.lint),
            ("typecheck", v_cmds.typecheck),
            ("build", v_cmds.build),
            ("test", v_cmds.test),
        ]

        task_validation = task.get("validation", {})
        task_cmds = []
        if isinstance(task_validation, dict):
            task_cmds = task_validation.get("commands", [])
        elif hasattr(task_validation, "commands"):
            task_cmds = task_validation.commands

        # Only run project-wide validation for implementation/validation tasks
        # or if files were actually changed.
        should_run_project_val = task.get("type") in (
            "implementation",
            "validation",
        ) or bool(changed_files)

        executed_cmds = set()

        if should_run_project_val:
            for name, cmd in checks:
                if cmd:
                    cmd_success = run_validation_command(
                        cmd, run_dir, task_cwd, console
                    )
                    validation_results.append(
                        {"name": name, "command": cmd, "success": cmd_success}
                    )
                    executed_cmds.add(cmd.strip())
                    if not cmd_success:
                        success = False

        if task_cmds:
            for i, cmd in enumerate(task_cmds, start=1):
                # Skip if already run in project validation
                if cmd.strip() in executed_cmds:
                    continue

                cmd_success = run_validation_command(cmd, run_dir, task_cwd, console)
                validation_results.append(
                    {"name": f"task_val_{i}", "command": cmd, "success": cmd_success}
                )
                if not cmd_success:
                    success = False

        # Evaluate minimum test coverage if configured
        try:
            niyam_config = load_niyam_config(repo_root)
            if (
                niyam_config
                and niyam_config.governance
                and niyam_config.governance.scan
            ):
                min_coverage = niyam_config.governance.scan.min_test_coverage
                if min_coverage is not None:
                    from niyam.core.coverage import find_and_parse_coverage

                    cov_result = find_and_parse_coverage(repo_root)
                    if cov_result:
                        actual_coverage = cov_result["percentage"]
                        if actual_coverage < min_coverage:
                            success = False
                            validation_results.append(
                                {
                                    "name": "coverage",
                                    "command": "internal_coverage_check",
                                    "success": False,
                                    "error": f"Coverage {actual_coverage}% < {min_coverage}%",
                                }
                            )
                        else:
                            validation_results.append(
                                {
                                    "name": "coverage",
                                    "command": "internal_coverage_check",
                                    "success": True,
                                    "details": f"Coverage: {actual_coverage}%",
                                }
                            )
                    else:
                        success = False
                        validation_results.append(
                            {
                                "name": "coverage",
                                "command": "internal_coverage_check",
                                "success": False,
                                "error": "Coverage report not found",
                            }
                        )
        except Exception:
            pass

    if validation_results:
        (task_dir / "validation.json").write_text(
            json.dumps(validation_results, indent=2), encoding="utf-8"
        )

    try:
        parsed_usage = None
        task_log_path = task_dir / "output.log"
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
            estimated = True
            estimation_method = "char_count_heuristic"
            cost_usd = None
            input_tokens = 0
            if prompt_path.exists():
                try:
                    prompt_content = prompt_path.read_text(encoding="utf-8")
                    input_tokens = max(1, len(prompt_content) // 4)
                except Exception:
                    pass
            output_tokens = 0
            if task_log_path.exists():
                try:
                    output_content = task_log_path.read_text(encoding="utf-8")
                    output_tokens = len(output_content) // 4
                except Exception:
                    pass
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
                output_tokens = 250

        plan_data = load_plan(run_dir)
        mission_meta = plan_data.get("mission", {})
        orchestrator = task.get("runtime") or mission_meta.get("orchestrator", "claude")

        actual_cost = update_token_ledger(
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

        # Also save to task dir
        token_usage = {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "cost_usd": actual_cost,
            "estimated": estimated,
            "runtime": orchestrator,
        }
        (task_dir / "token-usage.json").write_text(
            json.dumps(token_usage, indent=2), encoding="utf-8"
        )

        # Task-Level Budget Check
        try:
            config = load_niyam_config(repo_root)
            if config and config.governance and config.governance.budget:
                budget = config.governance.budget
                total_task_tokens = input_tokens + output_tokens

                # 1. Cost check
                if budget.max_task_cost_usd is not None:
                    if actual_cost > budget.max_task_cost_usd:
                        success = False
                        with print_lock:
                            console.print(
                                Panel(
                                    f"[bold red]🛑 Task Cost Budget Breached![/]\n"
                                    f"Task: {task_id} / Cost: ${actual_cost:.4f} / Limit: ${budget.max_task_cost_usd:.4f}\n"
                                    f"Task has been automatically failed.",
                                    title="[bold red]Task Budget Enforcer[/]",
                                    border_style="red",
                                )
                            )
                        log_mission_event(
                            run_dir,
                            "BUDGET_VIOLATION",
                            task_id=task_id,
                            details=f"Task cost breached limit: ${actual_cost:.4f} > ${budget.max_task_cost_usd:.4f}",
                            type="TASK_COST_BREACH",
                        )
                    elif actual_cost >= 0.8 * budget.max_task_cost_usd:
                        with print_lock:
                            console.print(
                                f"[bold yellow]⚠️ Task Budget Alert:[/] Task {task_id} cost reached 80% of limit (${actual_cost:.4f} / ${budget.max_task_cost_usd:.4f})"
                            )

                # 2. Token check
                if budget.max_task_tokens is not None:
                    if total_task_tokens > budget.max_task_tokens:
                        success = False
                        with print_lock:
                            console.print(
                                Panel(
                                    f"[bold red]🛑 Task Token Budget Breached![/]\n"
                                    f"Task: {task_id} / Tokens: {total_task_tokens} / Limit: {budget.max_task_tokens}\n"
                                    f"Task has been automatically failed.",
                                    title="[bold red]Task Budget Enforcer[/]",
                                    border_style="red",
                                )
                            )
                        log_mission_event(
                            run_dir,
                            "BUDGET_VIOLATION",
                            task_id=task_id,
                            details=f"Task tokens breached limit: {total_task_tokens} > {budget.max_task_tokens}",
                            type="TASK_TOKEN_BREACH",
                        )
                    elif total_task_tokens >= 0.8 * budget.max_task_tokens:
                        with print_lock:
                            console.print(
                                f"[bold yellow]⚠️ Task Budget Alert:[/] Task {task_id} tokens reached 80% of limit ({total_task_tokens} / {budget.max_task_tokens})"
                            )
        except Exception:
            pass

    except Exception:
        pass

    if success and use_worktree and worktree_path:
        transition_task(
            run_dir,
            task_id,
            "merging",
            reason="Committing and merging changes from worktree.",
        )
        try:
            commit_worktree_changes(worktree_path, task_id, console)
            res = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=worktree_path,
                capture_output=True,
                text=True,
            )
            if res.returncode == 0:
                task_commit_sha = res.stdout.strip()
                with plan_lock:
                    plan_data = load_plan(run_dir)
                    for t in plan_data.get("tasks", []):
                        if t["id"] == task_id:
                            t["commit_sha"] = task_commit_sha
                    save_plan(run_dir, plan_data)
        except Exception:
            success = False

    if use_worktree and worktree_path:
        cleanup_worktree(repo_root, worktree_path, branch_name, console)

    task_copy = dict(task)
    task_copy["status"] = "completed" if success else "failed"
    run_hooks(
        "post_task", {"mission_id": mission_id, "task": task_copy}, niyam_dir, console
    )

    return success
