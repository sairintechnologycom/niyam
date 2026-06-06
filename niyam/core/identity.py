"""Niyam identity management — cryptographic signing and verification."""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
from pathlib import Path
from typing import Optional

from niyam.core.config import find_niyam_root, get_niyam_dir


def get_identity_key_path(repo_root: Path | None = None) -> Path:
    """Get path to the local identity key file."""
    if repo_root is None:
        repo_root = find_niyam_root()
    if repo_root is None:
        repo_root = Path.cwd()
    return get_niyam_dir(repo_root) / "identity.key"


def ensure_identity(repo_root: Path | None = None) -> str:
    """Ensure a local identity key exists, generating one if missing."""
    key_path = get_identity_key_path(repo_root)
    if key_path.exists():
        return key_path.read_text(encoding="utf-8").strip()

    # Generate a new strong key
    key = secrets.token_hex(32)
    key_path.parent.mkdir(parents=True, exist_ok=True)
    key_path.write_text(key, encoding="utf-8")
    
    # Restrict permissions (Unix-only)
    try:
        key_path.chmod(0o600)
    except Exception:
        pass
        
    return key


def sign_data(data: str, key: str) -> str:
    """Compute HMAC-SHA256 signature for data string."""
    return hmac.new(
        key.encode("utf-8"), data.encode("utf-8"), hashlib.sha256
    ).hexdigest()


def verify_signature(data: str, signature: str, key: str) -> bool:
    """Verify that a signature matches the data and key."""
    expected = sign_data(data, key)
    return hmac.compare_digest(expected, signature)
