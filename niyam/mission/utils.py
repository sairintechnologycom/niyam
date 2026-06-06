"""Niyam mission shared utilities and locks."""

from __future__ import annotations

import threading
import yaml
from pathlib import Path
from niyam.core.utils import compute_sha256

# Shared locks for thread-safe operations
print_lock = threading.Lock()
validation_lock = threading.Lock()
plan_lock = threading.RLock()


def save_plan(run_dir: Path, plan_data: dict) -> None:
    """Save mission plan YAML and update task-list.yaml."""
    with plan_lock:
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


def load_plan(run_dir: Path) -> dict:
    """Load mission plan YAML and validate schema."""
    from niyam.core.config import MissionPlan
    from niyam.core.security import safe_load_yaml

    with plan_lock:
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
