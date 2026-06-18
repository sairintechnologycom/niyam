from __future__ import annotations

from pathlib import Path
from typing import Dict
from niyam.core.config import find_niyam_root
from niyam.core.security import safe_load_yaml


def get_aliases() -> Dict[str, str]:
    """Retrieve alias mappings from .niyam/config.yaml if it exists."""
    root = find_niyam_root() or Path.cwd()
    config_path = root / ".niyam" / "config.yaml"
    
    if not config_path.is_file():
        # Maybe check global config? For now, just project config
        return {}
        
    try:
        data = safe_load_yaml(config_path)
        if isinstance(data, dict) and "aliases" in data:
            return data["aliases"]
    except Exception:
        pass

    return {}


def resolve_alias(command_str: str) -> str:
    """Resolve a full command string if its first token is an alias."""
    aliases = get_aliases()
    if not aliases:
        return command_str
        
    tokens = command_str.strip().split()
    if not tokens:
        return command_str
        
    if tokens[0] in aliases:
        # Replace the first token with its alias resolution
        resolved_prefix = aliases[tokens[0]]
        rest = " ".join(tokens[1:])
        return f"{resolved_prefix} {rest}".strip()
        
    return command_str
