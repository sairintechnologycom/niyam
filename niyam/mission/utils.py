"""Niyam mission shared utilities and locks."""

from __future__ import annotations

import os
import platform
import sys
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

import yaml
from filelock import FileLock

# Shared locks for thread-safe operations
print_lock = threading.Lock()
validation_lock = threading.Lock()
plan_lock = threading.RLock()
git_lock = threading.RLock()



@contextmanager
def mission_plan_file_lock(run_dir: Path):
    """Process-safe lock for mission plan reads/writes."""
    run_dir.mkdir(parents=True, exist_ok=True)
    lock = FileLock(run_dir / "mission-plan.lock", timeout=30)
    with lock:
        yield


def save_plan(run_dir: Path, plan_data: dict) -> None:
    """Save mission plan YAML and update task-list.yaml."""
    with plan_lock:
        with mission_plan_file_lock(run_dir):
            import tempfile

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


def load_plan(run_dir: Path) -> dict:
    """Load mission plan YAML and validate schema."""
    from niyam.core.config import MissionPlan
    from niyam.core.security import safe_load_yaml

    with plan_lock:
        with mission_plan_file_lock(run_dir):
            plan_path = run_dir / "mission-plan.yaml"
            if not plan_path.exists():
                return {}
            data = safe_load_yaml(plan_path)
            validated = MissionPlan(**data)
            return validated.model_dump()


def update_plan(run_dir: Path, mutator) -> dict:
    """Atomically load, mutate, validate, and save a mission plan."""
    with plan_lock:
        with mission_plan_file_lock(run_dir):
            plan_path = run_dir / "mission-plan.yaml"
            if not plan_path.exists():
                plan_data = {}
            else:
                from niyam.core.config import MissionPlan
                from niyam.core.security import safe_load_yaml

                plan_data = MissionPlan(**safe_load_yaml(plan_path)).model_dump()
            result = mutator(plan_data)
            if result is not None:
                plan_data = result

            import tempfile

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
            return plan_data


def get_failure_diagnostics(run_dir: Path, failed_task_id: str | None = None) -> str:
    """Gather diagnostic information after a task/mission failure."""
    from niyam.governance.common.redaction import redact_text

    diagnostics = []
    diagnostics.append("=== Niyam Failure Diagnostics ===")
    diagnostics.append(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    diagnostics.append(
        f"OS: {platform.system()} {platform.release()} ({platform.machine()})"
    )
    diagnostics.append(f"Python: {sys.version.split()[0]} ({sys.executable})")

    # 1. Failed Task Log
    if failed_task_id:
        log_path = run_dir / f"task-{failed_task_id}-output.log"
        if log_path.exists():
            diagnostics.append(f"\n--- Log Tail: Task {failed_task_id} ---")
            try:
                content = log_path.read_text(encoding="utf-8").splitlines()
                tail = content[-50:]
                diagnostics.append("\n".join(tail))
            except Exception as e:
                diagnostics.append(f"(Error reading log: {e})")

    # 2. Environment Variables (Redacted)
    diagnostics.append("\n--- Environment Variables (Redacted) ---")
    env_lines = []
    # Filter for interesting env vars
    interesting_prefixes = ("PYTHON", "NODE", "PIP", "UV", "NIYAM", "SHELL")
    for k, v in sorted(os.environ.items()):
        is_interesting = any(k.startswith(p) for p in interesting_prefixes) or "PATH" in k
        if is_interesting:
            redacted_v = redact_text(v)
            env_lines.append(f"{k}={redacted_v}")

    if env_lines:
        diagnostics.append("\n".join(env_lines))
    else:
        diagnostics.append("(No relevant environment variables found)")

    return "\n".join(diagnostics)
