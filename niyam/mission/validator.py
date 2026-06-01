"""Niyam mission plan validator — schema, DAG, agent/runtime, path, and security checks."""

from __future__ import annotations

import shutil
from pathlib import Path
from pydantic import ValidationError

from niyam.core.config import MissionPlan, get_niyam_dir, load_project_config
from niyam.core.security import validate_command, CommandSecurityError, safe_load_yaml


class PlanValidationError(Exception):
    """Raised when mission plan validation fails."""

    def __init__(self, errors: list[str]):
        super().__init__("\n".join(errors))
        self.errors = errors


def validate_mission_plan(plan_path: Path, repo_root: Path) -> None:
    """Validate mission-plan.yaml against schemas, DAG requirements, security, and paths.

    Raises PlanValidationError if any checks fail.
    """
    errors: list[str] = []

    # 1. Load and parse file
    if not plan_path.exists():
        raise FileNotFoundError(f"Mission plan file not found: {plan_path}")

    try:
        data = safe_load_yaml(plan_path)
    except Exception as e:
        raise PlanValidationError([f"Failed to load YAML: {e}"])

    # 2. Schema Validation (Pydantic)
    try:
        plan = MissionPlan(**data)
    except ValidationError as e:
        for err in e.errors():
            loc_str = " -> ".join(str(part) for part in err["loc"])
            errors.append(f"Schema violation at {loc_str}: {err['msg']}")
        raise PlanValidationError(errors)

    # 3. DAG Validation (Cycle and Unknown Dependency checks)
    tasks = plan.tasks
    task_ids = {t.id for t in tasks}

    # Check for duplicate task IDs
    seen_ids = set()
    for t in tasks:
        if t.id in seen_ids:
            errors.append(f"Duplicate task ID detected: '{t.id}'")
        seen_ids.add(t.id)

    # Check for unknown dependency IDs
    for t in tasks:
        for dep in t.depends_on:
            if dep not in task_ids:
                errors.append(f"Task '{t.id}' depends on unknown task ID '{dep}'")

    # Cycle Detection (DFS)
    if not errors:
        visited = {}  # ID -> state (0 = unvisited, 1 = visiting, 2 = visited)
        adj = {t.id: t.depends_on for t in tasks}

        def has_cycle(u: str) -> bool:
            visited[u] = 1
            for v in adj.get(u, []):
                if visited.get(v, 0) == 1:
                    return True
                elif visited.get(v, 0) == 0:
                    if has_cycle(v):
                        return True
            visited[u] = 2
            return False

        for t in tasks:
            if visited.get(t.id, 0) == 0:
                if has_cycle(t.id):
                    errors.append("Dependency cycle detected in the task graph.")
                    break

    # 4. Agent and Runtime Existence
    niyam_dir = get_niyam_dir(repo_root)
    agents_dir = niyam_dir / "agents"

    for t in tasks:
        # Check Agent existence
        agent_file = agents_dir / f"{t.agent}.md"
        if not agent_file.exists():
            errors.append(
                f"Task '{t.id}' assigns unknown agent '{t.agent}' (missing {agent_file.relative_to(repo_root) if repo_root in agent_file.parents else agent_file})"
            )

        # Check Runtime existence
        if t.runtime:
            if not shutil.which(t.runtime) and t.runtime not in (
                "claude",
                "gemini",
                "codex",
            ):
                errors.append(
                    f"Task '{t.id}' specifies runtime '{t.runtime}' which is not executable or found in PATH"
                )

    # 5. Path Policy Validation (allowed_files, blocked_files)
    for t in tasks:
        # Prevent absolute or directory traversal in allowed/blocked files
        for pat in t.allowed_files:
            if pat.startswith("/") or ".." in pat:
                errors.append(
                    f"Task '{t.id}' allowed_files pattern '{pat}' is invalid. Path traversal or absolute paths are forbidden."
                )
        for pat in t.blocked_files:
            if pat.startswith("/") or ".." in pat:
                errors.append(
                    f"Task '{t.id}' blocked_files pattern '{pat}' is invalid. Path traversal or absolute paths are forbidden."
                )

    # 6. Validation Command Security Checks
    # Check task-specific validation commands
    for t in tasks:
        if t.validation and t.validation.commands:
            for cmd in t.validation.commands:
                try:
                    validate_command(cmd)
                except CommandSecurityError as e:
                    errors.append(
                        f"Task '{t.id}' validation command '{cmd}' blocked by security: {e}"
                    )

    # Check project-level validation commands
    try:
        proj_config = load_project_config(repo_root)
        if proj_config and proj_config.validation:
            v_cmds = proj_config.validation
            for name, cmd in [
                ("build", v_cmds.build),
                ("test", v_cmds.test),
                ("lint", v_cmds.lint),
                ("format", v_cmds.format),
                ("typecheck", v_cmds.typecheck),
            ]:
                if cmd:
                    try:
                        validate_command(cmd)
                    except CommandSecurityError as e:
                        errors.append(
                            f"Project configuration validation '{name}' command '{cmd}' blocked by security: {e}"
                        )
    except Exception:
        pass  # project.yaml might not exist yet during init/planning, which is fine

    if errors:
        raise PlanValidationError(errors)
