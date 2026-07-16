"""Source-linked local architecture inventory."""

from __future__ import annotations

import ast
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel, Field

from niyam.core.config import find_niyam_root
from niyam.core.scanner.stack_detector import detect_stack


IGNORED_DIRS = {
    ".git",
    ".niyam",
    ".sutra",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    "__pycache__",
}


class ArchitectureItem(BaseModel):
    """One architecture signal with its source location."""

    name: str
    file_path: str
    line: int
    details: dict[str, str] = Field(default_factory=dict)


class DataFlow(BaseModel):
    """A function-level source-to-sink flow."""

    function: str
    file_path: str
    line: int
    sources: list[str]
    sinks: list[str]


class ArchitectureInventory(BaseModel):
    """Portable local architecture inventory."""

    schema_version: str = "1.0.0"
    generated_at: str
    frameworks: list[str] = Field(default_factory=list)
    files_scanned: int = 0
    services: list[ArchitectureItem] = Field(default_factory=list)
    external_calls: list[ArchitectureItem] = Field(default_factory=list)
    identity_boundaries: list[ArchitectureItem] = Field(default_factory=list)
    storage: list[ArchitectureItem] = Field(default_factory=list)
    data_flows: list[DataFlow] = Field(default_factory=list)
    parse_errors: list[str] = Field(default_factory=list)


def _dotted_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _dotted_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    return ""


def _literal(node: ast.AST) -> str | None:
    return (
        node.value
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
        else None
    )


def _imports(tree: ast.AST) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for item in node.names:
                aliases[item.asname or item.name.split(".")[0]] = item.name
        elif isinstance(node, ast.ImportFrom) and node.module:
            for item in node.names:
                aliases[item.asname or item.name] = f"{node.module}.{item.name}"
    return aliases


def _resolved_name(raw: str, aliases: dict[str, str]) -> str:
    root, separator, remainder = raw.partition(".")
    resolved = aliases.get(root, root)
    return f"{resolved}.{remainder}" if separator else resolved


def _call_kind(name: str) -> str | None:
    lower = name.lower()
    if lower.endswith(("fastapi", "flask")):
        return "service"
    if lower.startswith(("requests.", "httpx.", "urllib.request.", "aiohttp.")):
        return "external_call"
    if any(
        marker in lower
        for marker in (
            "jwt.decode",
            "oauth",
            "authenticate",
            "verify_token",
            "get_current_user",
        )
    ):
        return "identity_boundary"
    if lower.startswith(
        ("sqlite3.", "sqlalchemy.", "psycopg.", "psycopg2.", "redis.", "pymongo.")
    ):
        return "storage"
    return None


def _item(name: str, path: str, line: int, **details: str) -> ArchitectureItem:
    return ArchitectureItem(name=name, file_path=path, line=line, details=details)


def _analyze_python(path: Path, root: Path) -> tuple[dict[str, list], list[DataFlow]]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    relative = path.relative_to(root).as_posix()
    aliases = _imports(tree)
    found: dict[str, list[ArchitectureItem]] = {
        "services": [],
        "external_calls": [],
        "identity_boundaries": [],
        "storage": [],
    }

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        raw = _dotted_name(node.func)
        kind = _call_kind(_resolved_name(raw, aliases))
        if kind:
            section = {
                "service": "services",
                "external_call": "external_calls",
                "identity_boundary": "identity_boundaries",
                "storage": "storage",
            }[kind]
            target = _literal(node.args[0]) if node.args else None
            details = {"target": target} if target else {}
            found[section].append(_item(raw, relative, node.lineno, **details))

    route_methods = {"get", "post", "put", "patch", "delete", "websocket"}
    functions = [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    flows = []
    for function in functions:
        for decorator in function.decorator_list:
            if isinstance(decorator, ast.Call):
                decorator_name = _dotted_name(decorator.func)
                method = decorator_name.rsplit(".", 1)[-1].lower()
                route = _literal(decorator.args[0]) if decorator.args else None
                if method in route_methods and route:
                    found["services"].append(
                        _item(
                            f"{method.upper()} {route}",
                            relative,
                            decorator.lineno,
                            function=function.name,
                        )
                    )

        kinds = {
            kind
            for call in ast.walk(function)
            if isinstance(call, ast.Call)
            if (kind := _call_kind(_resolved_name(_dotted_name(call.func), aliases)))
        }
        sources = sorted(kinds & {"external_call", "identity_boundary"})
        sinks = sorted(kinds & {"storage"})
        if sources and sinks:
            flows.append(
                DataFlow(
                    function=function.name,
                    file_path=relative,
                    line=function.lineno,
                    sources=sources,
                    sinks=sinks,
                )
            )
    return found, flows


def build_architecture_inventory(root: Path) -> ArchitectureInventory:
    """Analyze local Python source without executing project code."""
    root = root.resolve()
    inventory = ArchitectureInventory(
        generated_at=datetime.now(timezone.utc).isoformat(),
        frameworks=detect_stack(root)["frameworks"],
    )
    paths = sorted(
        path
        for path in root.rglob("*.py")
        if not any(part in IGNORED_DIRS for part in path.relative_to(root).parts)
    )
    for path in paths:
        inventory.files_scanned += 1
        try:
            found, flows = _analyze_python(path, root)
        except (OSError, UnicodeError, SyntaxError):
            inventory.parse_errors.append(path.relative_to(root).as_posix())
            continue
        inventory.services.extend(found["services"])
        inventory.external_calls.extend(found["external_calls"])
        inventory.identity_boundaries.extend(found["identity_boundaries"])
        inventory.storage.extend(found["storage"])
        inventory.data_flows.extend(flows)

    def source_key(item: ArchitectureItem | DataFlow) -> tuple[str, int, str]:
        return item.file_path, item.line, getattr(item, "name", "")

    inventory.services.sort(key=source_key)
    inventory.external_calls.sort(key=source_key)
    inventory.identity_boundaries.sort(key=source_key)
    inventory.storage.sort(key=source_key)
    inventory.data_flows.sort(key=source_key)
    inventory.parse_errors.sort()
    return inventory


def get_architecture_path(root: Path | None = None) -> Path:
    root = root or find_niyam_root() or Path.cwd()
    return root / ".niyam" / "architecture.json"


def save_architecture_inventory(
    inventory: ArchitectureInventory, root: Path | None = None
) -> Path:
    path = get_architecture_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.tmp.{os.getpid()}")
    temporary.write_text(
        json.dumps(inventory.model_dump(), indent=2) + "\n", encoding="utf-8"
    )
    os.replace(temporary, path)
    return path


def load_architecture_inventory(root: Path | None = None) -> ArchitectureInventory:
    path = get_architecture_path(root)
    if not path.exists():
        raise FileNotFoundError(
            "No architecture inventory found. Run 'niyam architecture scan'."
        )
    return ArchitectureInventory.model_validate_json(path.read_text(encoding="utf-8"))
