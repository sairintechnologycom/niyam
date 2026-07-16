"""Versioned local inventory for models, prompts, and data assets."""

from __future__ import annotations

import json
import os
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from filelock import FileLock
from pydantic import BaseModel, Field

from niyam.core.applications import require_application
from niyam.core.config import find_niyam_root
from niyam.core.graph import link_objects


InventoryType = Literal["model", "prompt", "dataset", "vector-store", "knowledge-base"]


class InventoryObject(BaseModel):
    """A versioned governed model, prompt, or data object."""

    object_type: InventoryType
    object_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]*$")
    name: str
    version: str = Field(min_length=1)
    owner: str | None = None
    location: str | None = None
    description: str | None = None
    tags: list[str] = Field(default_factory=list)
    created_at: str
    updated_at: str


class Inventory(BaseModel):
    """Portable, versioned object registry."""

    schema_version: str = "1.0.0"
    objects: dict[str, InventoryObject] = Field(default_factory=dict)


def get_inventory_path(root: Path | None = None) -> Path:
    root = root or find_niyam_root() or Path.cwd()
    return root / ".niyam" / "inventory.json"


@contextmanager
def inventory_lock(root: Path | None = None):
    path = get_inventory_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with FileLock(str(path.with_suffix(".json.lock"))):
        yield


def load_inventory(root: Path | None = None) -> Inventory:
    path = get_inventory_path(root)
    if not path.exists():
        return Inventory()
    try:
        return Inventory.model_validate_json(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"Failed to load inventory at {path}: {exc}") from exc


def _save_inventory(inventory: Inventory, root: Path | None = None) -> None:
    path = get_inventory_path(root)
    temporary = path.with_name(f"{path.name}.tmp.{os.getpid()}")
    temporary.write_text(
        json.dumps(inventory.model_dump(), indent=2) + "\n", encoding="utf-8"
    )
    os.replace(temporary, path)


def register_inventory_object(
    object_type: InventoryType,
    object_id: str,
    *,
    name: str | None = None,
    version: str | None = None,
    owner: str | None = None,
    location: str | None = None,
    description: str | None = None,
    tags: list[str] | None = None,
    application_id: str | None = None,
    update: bool = False,
    root: Path | None = None,
) -> InventoryObject:
    """Register an object and optionally link it to an Application."""
    require_application(application_id, root)
    key = f"{object_type}:{object_id}"
    with inventory_lock(root):
        inventory = load_inventory(root)
        existing = inventory.objects.get(key)
        if existing and not update:
            raise ValueError(f"Inventory object '{key}' is already registered.")
        if not existing and (not name or not version):
            raise ValueError(
                "Name and version are required for a new inventory object."
            )

        now = datetime.now(timezone.utc).isoformat()
        values = (
            existing.model_dump()
            if existing
            else {
                "object_type": object_type,
                "object_id": object_id,
                "name": name,
                "version": version,
                "created_at": now,
            }
        )
        updates = {
            "name": name,
            "version": version,
            "owner": owner,
            "location": location,
            "description": description,
            "tags": tags,
        }
        values.update(
            {field: value for field, value in updates.items() if value is not None}
        )
        values["updated_at"] = now
        record = InventoryObject.model_validate(values)
        inventory.objects[key] = record
        _save_inventory(inventory, root)

    if application_id:
        link_objects(
            "application",
            application_id,
            "uses",
            object_type,
            object_id,
            root=root,
        )
    return record
