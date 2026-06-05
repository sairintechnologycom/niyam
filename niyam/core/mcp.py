"""MCP and Tool Registry core module."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional, Literal
from pydantic import BaseModel, Field

from niyam.core.config import find_niyam_root


class MCPTool(BaseModel):
    """Pydantic model representing a registered tool or MCP server."""

    schema_version: str = "1.0.0"
    name: str
    type: Literal["mcp_server", "api", "cli", "local_tool", "browser", "other"]
    command_or_url: Optional[str] = None
    owner: Optional[str] = None
    risk_level: Literal["low", "medium", "high", "critical"]
    approved: bool = False
    capabilities: list[str] = Field(default_factory=list)
    data_access: Optional[str] = None
    network_access: Optional[str] = None
    requires_approval: bool = True
    notes: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None



class MCPRegistry(BaseModel):
    """Pydantic model representing the local MCP/Tool registry file."""

    schema_version: str = "1.0.0"
    tools: dict[str, MCPTool] = Field(default_factory=dict)


def get_mcp_registry_path(root: Path | None = None) -> Path:
    """Get the path to the local MCP registry file."""
    if root is None:
        root = find_niyam_root()
    if root is None:
        root = Path.cwd()
    return root / ".niyam" / "mcp-registry.json"


def load_mcp_registry(root: Path | None = None) -> MCPRegistry:
    """Load the local MCP/tool registry from JSON file, returning empty registry on error/missing."""
    path = get_mcp_registry_path(root)
    if not path.exists():
        return MCPRegistry()
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return MCPRegistry.model_validate(data)
    except Exception:
        return MCPRegistry()


def save_mcp_registry(registry: MCPRegistry, root: Path | None = None) -> None:
    """Save the MCP/tool registry locally to the JSON file."""
    path = get_mcp_registry_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(registry.model_dump(), f, indent=2)


def classify_risk(
    name: str,
    type: str,
    command_or_url: str | None = None,
    capabilities: list[str] | None = None,
    data_access: str | None = None,
    notes: str | None = None,
) -> Literal["low", "medium", "high", "critical"]:
    """Classify the risk level of a tool based on heuristics.

    Heuristics:
    - file system access = high
    - shell access = critical
    - cloud API access = critical
    - read-only docs = medium
    - public search = low/medium
    """
    import re

    text = f"{name} {command_or_url or ''} {data_access or ''} {notes or ''}".lower()
    caps = [c.lower() for c in (capabilities or [])]

    # Helper function to check for exact word matching
    def has_word(words: list[str], target: str) -> bool:
        for w in words:
            if re.search(r"\b" + re.escape(w) + r"\b", target):
                return True
        return False

    # Heuristic 1: Shell access (critical)
    shell_keywords = [
        "shell",
        "bash",
        "zsh",
        "sh",
        "terminal",
        "run_command",
        "execute",
        "exec",
        "cmd.exe",
        "powershell",
    ]
    if has_word(shell_keywords, text) or any(
        k in caps for k in ["run_command", "execute", "exec"]
    ):
        return "critical"

    # Heuristic 2: Cloud API access (critical)
    cloud_keywords = ["aws", "gcp", "azure", "cloud", "kubernetes", "k8s"]
    if has_word(cloud_keywords, text) or "cloud api" in text:
        return "critical"

    # Heuristic 3: File system access (high)
    fs_keywords = ["file", "fs", "directory", "folder", "filesystem", "path"]
    if has_word(fs_keywords, text) or any(
        k in caps for k in ["read_file", "write_file", "file", "filesystem"]
    ):
        return "high"

    # Heuristic 4: Read-only docs (medium)
    docs_keywords = ["docs", "doc", "documentation", "wiki", "read-only", "readme"]
    if has_word(docs_keywords, text) or any(
        k in caps for k in ["read_docs", "view_docs"]
    ):
        return "medium"

    # Heuristic 5: Public search (low/medium)
    search_keywords = ["search", "google", "query", "web", "duckduckgo", "bing"]
    if has_word(search_keywords, text) or any(
        k in caps for k in ["search_web", "web_search"]
    ):
        return "low"

    # Default fallback
    return "medium"
