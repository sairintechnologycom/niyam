"""Niyam mission state machine — manage task and mission lifecycles."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from niyam.mission.utils import update_plan


# ── State Definitions ──────────────────────────────────────────────────

TaskStatus = Literal[
    "planned",
    "approved",
    "queued",
    "preparing",
    "awaiting_approval",
    "running",
    "validating",
    "reviewing",
    "merging",
    "blocked",
    "needs_human",
    "retry_ready",
    "completed",
    "failed",
    "skipped",
    "cancelled",
    "rolled_back",
]

MissionStatus = Literal[
    "planned",
    "approved",
    "running",
    "paused",
    "completed",
    "failed",
    "cancelled",
    "rolled_back",
]


class IllegalStateTransitionError(ValueError):
    """Raised when a mission or task attempts an invalid state transition."""


VALID_TASK_TRANSITIONS: dict[str, set[str]] = {
    "planned": {
        "approved",
        "queued",
        "preparing",
        "awaiting_approval",
        "running",
        "retry_ready",
        "completed",
        "failed",
        "skipped",
        "cancelled",
    },
    "approved": {"queued", "preparing", "running", "failed", "skipped", "cancelled"},
    "queued": {
        "preparing",
        "running",
        "retry_ready",
        "completed",
        "failed",
        "skipped",
        "cancelled",
    },
    "preparing": {"running", "completed", "failed", "cancelled"},
    "awaiting_approval": {"approved", "failed", "skipped", "cancelled"},
    "running": {"validating", "reviewing", "blocked", "needs_human", "completed", "failed", "cancelled"},
    "validating": {"reviewing", "merging", "completed", "failed", "retry_ready", "cancelled"},
    "reviewing": {"merging", "completed", "failed", "retry_ready", "cancelled"},
    "merging": {"completed", "failed", "rolled_back"},
    "blocked": {"retry_ready", "needs_human", "failed", "skipped", "cancelled"},
    "needs_human": {"approved", "retry_ready", "failed", "skipped", "cancelled"},
    "retry_ready": {"planned", "approved", "queued", "preparing", "running", "failed", "skipped", "cancelled"},
    "failed": {"retry_ready", "planned", "skipped", "rolled_back"},
    "skipped": {"retry_ready", "planned"},
    "completed": {"rolled_back"},
    "cancelled": {"retry_ready", "rolled_back"},
    "rolled_back": {"retry_ready", "planned"},
}


VALID_MISSION_TRANSITIONS: dict[str, set[str]] = {
    "planned": {"approved", "running", "failed", "cancelled"},
    "approved": {"running", "paused", "failed", "cancelled", "rolled_back"},
    "running": {"paused", "completed", "failed", "cancelled", "rolled_back"},
    "paused": {"approved", "running", "failed", "cancelled", "rolled_back"},
    "completed": {"rolled_back"},
    "failed": {"approved", "running", "rolled_back"},
    "cancelled": {"approved", "rolled_back"},
    "rolled_back": {"approved", "running"},
}


def _validate_transition(
    entity_type: str,
    entity_id: str,
    from_status: str,
    to_status: str,
    valid_transitions: dict[str, set[str]],
) -> None:
    allowed = valid_transitions.get(from_status, set())
    if to_status not in allowed:
        allowed_text = ", ".join(sorted(allowed)) or "none"
        raise IllegalStateTransitionError(
            f"Illegal {entity_type} state transition for {entity_id}: "
            f"'{from_status}' -> '{to_status}'. Allowed next states: {allowed_text}."
        )


def log_mission_event(
    run_dir: Path,
    event_type: str,
    task_id: str | None = None,
    details: str | None = None,
    **kwargs: Any,
) -> None:
    """Append a structured event to events.jsonl."""
    events_path = run_dir / "events.jsonl"
    events_path.parent.mkdir(parents=True, exist_ok=True)

    event = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "mission_id": run_dir.name,
        "event": event_type,
    }
    if task_id:
        event["task_id"] = task_id
    if details:
        event["details"] = details
    
    event.update(kwargs)

    with open(events_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")


def _notify_saas_event(run_dir: Path, event_type: str, payload: dict) -> None:
    """Helper to fire an asynchronous webhook notification to SaaS Dashboard."""
    try:
        from niyam.core.config import find_niyam_root, load_niyam_config
        from niyam.core.saas import SaaSClient

        repo_root = find_niyam_root(run_dir)
        config = load_niyam_config(repo_root)
        if config.saas.enabled:
            client = SaaSClient(repo_root)
            client.trigger_webhook(event_type, payload)
    except Exception:
        pass


def transition_task(
    run_dir: Path,
    task_id: str,
    to_status: TaskStatus,
    reason: str | None = None,
    actor: str | None = None,
) -> None:
    """Transition a task to a new status, log the event, and update the plan."""
    transition_data: dict[str, str | bool] = {"changed": False}

    def mutate(plan_data: dict) -> dict:
        tasks = plan_data.get("tasks", [])
        target_task = None
        for t in tasks:
            if t["id"] == task_id:
                target_task = t
                break

        if not target_task:
            raise ValueError(f"Task {task_id} not found in mission plan.")

        from_status = target_task.get("status", "planned")
        transition_data["from_status"] = from_status
        if from_status == to_status:
            return plan_data
        _validate_transition(
            "task",
            task_id,
            from_status,
            to_status,
            VALID_TASK_TRANSITIONS,
        )
        target_task["status"] = to_status
        transition_data["changed"] = True
        return plan_data

    update_plan(run_dir, mutate)
    if not transition_data["changed"]:
        return
    from_status = str(transition_data["from_status"])
    
    # Update task-specific status snapshot
    task_dir = run_dir / "tasks" / task_id
    task_dir.mkdir(parents=True, exist_ok=True)
    status_snapshot = {
        "task_id": task_id,
        "status": to_status,
        "updated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "actor": actor,
        "reason": reason,
    }
    (task_dir / "status.json").write_text(json.dumps(status_snapshot, indent=2), encoding="utf-8")

    # Log event
    log_mission_event(
        run_dir,
        "TASK_STATE_TRANSITION",
        task_id=task_id,
        from_status=from_status,
        to_status=to_status,
        reason=reason,
        actor=actor,
    )

    # Notify SaaS
    _notify_saas_event(
        run_dir,
        "TASK_STATE_TRANSITION",
        {
            "mission_id": run_dir.name,
            "task_id": task_id,
            "from_status": from_status,
            "to_status": to_status,
            "reason": reason,
            "actor": actor,
        }
    )


def transition_mission(
    run_dir: Path,
    to_status: MissionStatus,
    reason: str | None = None,
    actor: str | None = None,
) -> None:
    """Transition a mission to a new status, log the event, and update the plan."""
    transition_data: dict[str, str | bool] = {"changed": False}

    def mutate(plan_data: dict) -> dict:
        mission_meta = plan_data.get("mission", {})
        from_status = mission_meta.get("status", "planned")
        transition_data["from_status"] = from_status
        if from_status == to_status:
            return plan_data
        _validate_transition(
            "mission",
            run_dir.name,
            from_status,
            to_status,
            VALID_MISSION_TRANSITIONS,
        )
        mission_meta["status"] = to_status
        transition_data["changed"] = True
        return plan_data

    update_plan(run_dir, mutate)
    if not transition_data["changed"]:
        return
    from_status = str(transition_data["from_status"])
    
    # Log event
    log_mission_event(
        run_dir,
        "MISSION_STATE_TRANSITION",
        from_status=from_status,
        to_status=to_status,
        reason=reason,
        actor=actor,
    )

    # Notify SaaS
    _notify_saas_event(
        run_dir,
        "MISSION_STATE_TRANSITION",
        {
            "mission_id": run_dir.name,
            "from_status": from_status,
            "to_status": to_status,
            "reason": reason,
            "actor": actor,
        }
    )
