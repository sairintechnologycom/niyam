"""MCP and Tool Registry core module."""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Literal
from pydantic import BaseModel, Field

from niyam.core.config import find_niyam_root
from niyam.governance.common.redaction import redact_secrets


class MCPTool(BaseModel):
    """Pydantic model representing a registered tool or MCP server."""

    schema_version: str = "1.0.0"
    name: str
    type: Literal["mcp_server", "api", "cli", "local_tool", "browser", "other"]
    command_or_url: str | None = None
    owner: str | None = None
    risk_level: Literal["low", "medium", "high", "critical"]
    approved: bool = False
    capabilities: list[str] = Field(default_factory=list)
    data_access: str | None = None
    network_access: str | None = None
    requires_approval: bool = True
    notes: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


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
    """Save the MCP/tool registry locally to the JSON file with secret redaction."""
    path = get_mcp_registry_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)

    redacted_data = redact_secrets(registry.model_dump())

    with open(path, "w", encoding="utf-8") as f:
        json.dump(redacted_data, f, indent=2)


def _classify_risk_ai(
    name: str,
    type: str,
    command_or_url: str | None = None,
    capabilities: list[str] | None = None,
    data_access: str | None = None,
    notes: str | None = None,
) -> Optional[Literal["low", "medium", "high", "critical"]]:
    """Stub for AI-powered semantic risk classification."""
    # In a real implementation, this would use a local or remote LLM
    # to analyze the tool details and return a risk verdict.
    # For now, it returns None to fall back to heuristics.
    return None


def classify_risk(
    name: str,
    type: str,
    command_or_url: str | None = None,
    capabilities: list[str] | None = None,
    data_access: str | None = None,
    notes: str | None = None,
    use_ai: bool = False,
) -> Literal["low", "medium", "high", "critical"]:
    """Classify the risk level of a tool based on heuristics or AI semantic analysis."""
    
    # 1. Try AI-powered semantic classification if requested
    if use_ai:
        try:
            ai_risk = _classify_risk_ai(name, type, command_or_url, capabilities, data_access, notes)
            if ai_risk:
                return ai_risk
        except Exception:
            # Fall back to heuristics on AI failure
            pass

    # 2. Existing heuristic classification
    caps = [c.lower().strip() for c in (capabilities or [])]
    text = f"{name} {command_or_url or ''} {data_access or ''} {notes or ''}".lower()

    # Priority mapping
    inv_risk_levels = {1: "low", 2: "medium", 3: "high", 4: "critical"}
    max_risk_val = 0

    # Unified capability mapping
    capability_risks = {
        "production_deploy": 4,
        "secrets_access": 4,
        "cloud_api": 4,
        "shell_execute": 4,
        "run_command": 4,
        "execute": 4,
        "exec": 4,
        "file_write": 3,
        "read_file": 3,
        "write_file": 3,
        "file": 3,
        "filesystem": 3,
        "repo_read": 2,
        "docs_read": 2,
        "read_docs": 2,
        "view_docs": 2,
        "public_search": 1,
        "search_web": 1,
        "web_search": 1,
    }

    for cap in caps:
        if cap in capability_risks:
            max_risk_val = max(max_risk_val, capability_risks[cap])

    # Fallback to text heuristics
    def has_word(words: list[str], target: str) -> bool:
        for w in words:
            if re.search(r"\b" + re.escape(w) + r"\b", target):
                return True
        return False

    text_critical = [
        "shell",
        "bash",
        "zsh",
        "terminal",
        "powershell",
        "aws",
        "gcp",
        "azure",
        "kubernetes",
        "k8s",
        "secret",
        "deploy",
        "publish",
    ]
    text_high = ["file", "filesystem", "write", "create", "delete", "modify"]
    text_medium = ["docs", "doc", "wiki", "read-only", "repo", "repository"]
    text_low = ["search", "google", "query", "web"]

    if max_risk_val < 4 and has_word(text_critical, text):
        max_risk_val = 4
    if max_risk_val < 3 and has_word(text_high, text):
        max_risk_val = 3
    if max_risk_val < 2 and has_word(text_medium, text):
        max_risk_val = 2
    if max_risk_val < 1 and has_word(text_low, text):
        max_risk_val = 1

    if max_risk_val == 0:
        return "medium"
    return inv_risk_levels[max_risk_val]
