"""Niyam runtime adapters and execution registry."""

from niyam.runtimes.registry import (
    get_runtime_registry,
    get_runtime_spec,
    list_runtime_names,
    register_runtime_spec,
)
from niyam.runtimes.specs import RuntimeSpec, BUILTIN_RUNTIME_SPECS

__all__ = [
    "RuntimeSpec",
    "BUILTIN_RUNTIME_SPECS",
    "get_runtime_registry",
    "get_runtime_spec",
    "list_runtime_names",
    "register_runtime_spec",
]
