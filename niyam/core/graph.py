"""Versioned local relationship graph for governed AI objects."""

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


def parse_object_ref(value: str) -> tuple[str, str]:
    """Parse a TYPE:ID graph reference."""
    object_type, separator, object_id = value.partition(":")
    if not separator or not object_type or not object_id:
        raise ValueError(
            "Object references must use TYPE:ID, for example application:bot."
        )
    return object_type, object_id


class Relationship(BaseModel):
    """A directed relationship between two governed objects."""

    source_type: str = Field(pattern=r"^[a-z][a-z0-9_-]*$")
    source_id: str = Field(min_length=1)
    relationship: str = Field(pattern=r"^[a-z][a-z0-9_-]*$")
    target_type: str = Field(pattern=r"^[a-z][a-z0-9_-]*$")
    target_id: str = Field(min_length=1)
    created_at: str


class NiyamGraph(BaseModel):
    """Portable graph representation stored in the workspace."""

    schema_version: str = "1.0.0"
    relationships: list[Relationship] = Field(default_factory=list)


def get_graph_path(root: Path | None = None) -> Path:
    root = root or find_niyam_root() or Path.cwd()
    return root / ".niyam" / "graph.json"


@contextmanager
def graph_lock(root: Path | None = None):
    path = get_graph_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with FileLock(str(path.with_suffix(".json.lock"))):
        yield


def load_graph(root: Path | None = None) -> NiyamGraph:
    path = get_graph_path(root)
    if not path.exists():
        return NiyamGraph()
    try:
        return NiyamGraph.model_validate_json(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"Failed to load Niyam Graph at {path}: {exc}") from exc


def save_graph(
    graph: NiyamGraph, root: Path | None = None, *, locked: bool = False
) -> None:
    path = get_graph_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)

    def write() -> None:
        temporary = path.with_name(f"{path.name}.tmp.{os.getpid()}")
        temporary.write_text(
            json.dumps(graph.model_dump(), indent=2) + "\n", encoding="utf-8"
        )
        os.replace(temporary, path)

    if locked:
        write()
    else:
        with graph_lock(root):
            write()


def _validate_application_ref(
    object_type: str, object_id: str, root: Path | None
) -> None:
    if object_type != "application":
        return
    from niyam.core.applications import load_application_registry

    if object_id not in load_application_registry(root).applications:
        raise ValueError(f"AI Application '{object_id}' is not registered.")


def link_objects(
    source_type: str,
    source_id: str,
    relationship: str,
    target_type: str,
    target_id: str,
    *,
    root: Path | None = None,
) -> Relationship:
    """Create one idempotent directed relationship."""
    _validate_application_ref(source_type, source_id, root)
    _validate_application_ref(target_type, target_id, root)
    candidate = Relationship(
        source_type=source_type,
        source_id=source_id,
        relationship=relationship,
        target_type=target_type,
        target_id=target_id,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    with graph_lock(root):
        graph = load_graph(root)
        for existing in graph.relationships:
            if (
                existing.source_type,
                existing.source_id,
                existing.relationship,
                existing.target_type,
                existing.target_id,
            ) == (
                source_type,
                source_id,
                relationship,
                target_type,
                target_id,
            ):
                return existing
        graph.relationships.append(candidate)
        save_graph(graph, root, locked=True)
    return candidate


def get_relationships(
    object_type: str,
    object_id: str,
    *,
    direction: Literal["outgoing", "incoming", "both"] = "both",
    root: Path | None = None,
) -> list[Relationship]:
    """Return direct relationships for one governed object."""
    edges = load_graph(root).relationships
    if direction == "outgoing":
        return [
            edge
            for edge in edges
            if (edge.source_type, edge.source_id) == (object_type, object_id)
        ]
    if direction == "incoming":
        return [
            edge
            for edge in edges
            if (edge.target_type, edge.target_id) == (object_type, object_id)
        ]
    return [
        edge
        for edge in edges
        if (edge.source_type, edge.source_id) == (object_type, object_id)
        or (edge.target_type, edge.target_id) == (object_type, object_id)
    ]
