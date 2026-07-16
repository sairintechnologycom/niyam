"""Local inventory of first-class AI Applications."""

from __future__ import annotations

import json
import os
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from filelock import FileLock
from pydantic import BaseModel, Field

from niyam.core.config import find_niyam_root


class AIApplication(BaseModel):
    """Stable identity and ownership metadata for an AI application."""

    application_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]*$")
    name: str
    owner: str | None = None
    repository: str | None = None
    description: str | None = None
    status: Literal["prototype", "production", "retired"] = "prototype"
    tags: list[str] = Field(default_factory=list)
    created_at: str
    updated_at: str


class ApplicationRegistry(BaseModel):
    """Versioned local AI Application registry."""

    schema_version: str = "1.0.0"
    applications: dict[str, AIApplication] = Field(default_factory=dict)


def get_application_registry_path(root: Path | None = None) -> Path:
    root = root or find_niyam_root() or Path.cwd()
    return root / ".niyam" / "applications.json"


@contextmanager
def application_registry_lock(root: Path | None = None):
    path = get_application_registry_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with FileLock(str(path.with_suffix(".json.lock"))):
        yield


def load_application_registry(root: Path | None = None) -> ApplicationRegistry:
    path = get_application_registry_path(root)
    if not path.exists():
        return ApplicationRegistry()
    try:
        return ApplicationRegistry.model_validate_json(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(
            f"Failed to load AI Application registry at {path}: {exc}"
        ) from exc


def save_application_registry(
    registry: ApplicationRegistry, root: Path | None = None, *, locked: bool = False
) -> None:
    path = get_application_registry_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)

    def write() -> None:
        temporary = path.with_name(f"{path.name}.tmp.{os.getpid()}")
        temporary.write_text(
            json.dumps(registry.model_dump(), indent=2) + "\n", encoding="utf-8"
        )
        os.replace(temporary, path)

    if locked:
        write()
    else:
        with application_registry_lock(root):
            write()


def register_application(
    application_id: str,
    *,
    name: str | None = None,
    owner: str | None = None,
    repository: str | None = None,
    description: str | None = None,
    status: Literal["prototype", "production", "retired"] | None = None,
    tags: list[str] | None = None,
    update: bool = False,
    root: Path | None = None,
) -> AIApplication:
    """Register an application, or explicitly update an existing record."""
    with application_registry_lock(root):
        registry = load_application_registry(root)
        existing = registry.applications.get(application_id)
        if existing and not update:
            raise ValueError(
                f"AI Application '{application_id}' is already registered."
            )
        if not existing and not name:
            raise ValueError("Name is required for a new AI Application.")

        now = datetime.now(timezone.utc).isoformat()
        values = (
            existing.model_dump()
            if existing
            else {
                "application_id": application_id,
                "name": name,
                "created_at": now,
            }
        )
        updates = {
            "name": name,
            "owner": owner,
            "repository": repository,
            "description": description,
            "status": status,
            "tags": tags,
        }
        values.update(
            {key: value for key, value in updates.items() if value is not None}
        )
        values["updated_at"] = now

        application = AIApplication.model_validate(values)
        registry.applications[application_id] = application
        save_application_registry(registry, root, locked=True)
        return application


def require_application(
    application_id: str | None, root: Path | None = None
) -> str | None:
    """Validate an optional application reference at a write boundary."""
    if application_id is None:
        return None
    if application_id not in load_application_registry(root).applications:
        raise ValueError(f"AI Application '{application_id}' is not registered.")
    return application_id
