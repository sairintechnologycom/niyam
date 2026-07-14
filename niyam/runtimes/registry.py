"""Open runtime registry: built-ins + user specs from .niyam/runtimes.yaml."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from niyam.core.config import find_niyam_root, get_niyam_dir
from niyam.runtimes.specs import (
    BUILTIN_RUNTIME_SPECS,
    RuntimeSpec,
    runtime_spec_from_dict,
)


def _load_user_specs(repo_root: Path | None = None) -> dict[str, RuntimeSpec]:
    root = repo_root or find_niyam_root()
    if root is None:
        return {}
    path = get_niyam_dir(root) / "runtimes.yaml"
    if not path.exists():
        return {}
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}
    if not isinstance(data, dict):
        return {}

    specs: dict[str, RuntimeSpec] = {}
    # New style: execution_specs: { name: { binary, exec_args, ... } }
    exec_block = data.get("execution_specs") or data.get("execution") or {}
    if isinstance(exec_block, dict):
        for name, raw in exec_block.items():
            if not isinstance(raw, dict):
                continue
            payload = {"name": name, **raw}
            try:
                specs[name] = runtime_spec_from_dict(payload)
            except Exception:
                continue

    # Lightweight custom runtime: runtimes.custom.myruntime: { binary: ... }
    custom = data.get("custom") or {}
    if isinstance(custom, dict):
        for name, raw in custom.items():
            if not isinstance(raw, dict):
                continue
            payload = {
                "name": name,
                "binary": raw.get("binary", name),
                "prompt_delivery": raw.get("prompt_delivery", "stdin"),
                "exec_args": raw.get("exec_args") or ["exec", "-"],
                "plan_args": raw.get("plan_args") or raw.get("exec_args") or ["exec", "-"],
                "usage_parser": raw.get("usage_parser", "text_regex"),
                "output_format": raw.get("output_format", "text"),
                "capabilities": raw.get("capabilities") or ["implementation"],
            }
            try:
                specs[name] = runtime_spec_from_dict(payload)
            except Exception:
                continue

    return specs


def list_runtime_names(repo_root: Path | None = None) -> list[str]:
    """Return registered runtime names (built-in + user)."""
    return sorted(get_runtime_registry(repo_root).keys())


def get_runtime_registry(repo_root: Path | None = None) -> dict[str, RuntimeSpec]:
    """Merge built-in specs with workspace overrides."""
    registry = {name: spec.model_copy(deep=True) for name, spec in BUILTIN_RUNTIME_SPECS.items()}
    user = _load_user_specs(repo_root)
    registry.update(user)
    return registry


def get_runtime_spec(
    name: str, repo_root: Path | None = None, *, strict: bool = False
) -> RuntimeSpec | None:
    """Resolve a runtime by name. Falls back to a generic exec-style spec when unknown."""
    key = (name or "").strip().lower()
    if not key:
        return None
    registry = get_runtime_registry(repo_root)
    if key in registry:
        return registry[key]
    if strict:
        return None
    # Generic: treat name as binary, prompt via stdin like codex exec
    return RuntimeSpec(
        name=key,
        binary=key,
        prompt_delivery="stdin",
        exec_args=["exec", "-"],
        plan_args=["exec", "-"],
        usage_parser="text_regex",
        capabilities=["implementation"],
    )


def register_runtime_spec(
    spec: RuntimeSpec, repo_root: Path | None = None
) -> Path:
    """Persist a custom execution spec under .niyam/runtimes.yaml."""
    root = repo_root or find_niyam_root()
    if root is None:
        root = Path.cwd()
    path = get_niyam_dir(root) / "runtimes.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    data: dict[str, Any] = {}
    if path.exists():
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except Exception:
            data = {}
    if not isinstance(data, dict):
        data = {}
    exec_block = data.setdefault("execution_specs", {})
    if not isinstance(exec_block, dict):
        exec_block = {}
        data["execution_specs"] = exec_block
    payload = spec.model_dump(exclude_none=True)
    payload.pop("name", None)
    exec_block[spec.name] = payload
    path.write_text(
        yaml.safe_dump(data, default_flow_style=False, sort_keys=False),
        encoding="utf-8",
    )
    return path
