"""Niyam governance common redaction engine."""

from __future__ import annotations

import re
import hashlib
from typing import Any

# Compiled Regex patterns for identifying specific secret formats
PATTERNS = {
    "private_key": re.compile(
        r"-----BEGIN\s+([A-Z0-9\s_]+)\s+PRIVATE\s+KEY-----[\s\S]*?-----END\s+\1\s+PRIVATE\s+KEY-----"
    ),
    "openai": re.compile(
        r"\bsk-(?:proj-)?[a-zA-Z0-9_\-]{24,}\b"
    ),
    "anthropic": re.compile(r"\bsk-ant-[a-zA-Z0-9_\-]{24,}\b"),
    "github": re.compile(
        r"\b(?:ghp|ghs)_[a-zA-Z0-9]{36,}\b|\bgithub_pat_[a-zA-Z0-9_\-]{70,}\b"
    ),
    "aws_id": re.compile(r"\b(?:AKIA|AGPA|AIDA|AROA|ASCA|ASIA)[A-Z0-9]{16}\b"),
    "azure_conn": re.compile(r"(?i)(AccountKey=)[a-zA-Z0-9+/=]{40,}"),
    "jwt": re.compile(
        r"\beyJ[a-zA-Z0-9_\-]{10,}\.[a-zA-Z0-9_\-]{10,}\.[a-zA-Z0-9_\-]{10,}\b"
    ),
    "db_url": re.compile(r"([a-zA-Z0-9+.-]+://[^/:]+:)([^/@\s]+)(@[^/\s]+)"),
    "generic_assignment": re.compile(
        r"(?i)(password|passwd|api_key|apikey|secret_key|private_key|token|auth_token|pass)(\s*)([=:]|\bis\b)(\s*)(['\"]?)([a-zA-Z0-9_\-\.\@\#\!\$\%\^\&\*\(\)\+\/\?\:\=\~\[\]\{\}\<\>\\\|]{8,128})(\5)"
    ),
}

SENSITIVE_KEYS = {
    "password", "passwd", "api_key", "apikey", "secret_key", 
    "private_key", "token", "auth_token", "pass", "secret"
}

def get_secret_fingerprint(secret: str) -> str:
    """Calculate SHA-256 of a secret and return the first 8 hex characters."""
    if not secret:
        return ""
    clean_secret = secret.strip("'\"")
    hasher = hashlib.sha256(clean_secret.encode("utf-8", errors="ignore"))
    return hasher.hexdigest()[:8]

def redact_text(value: str, with_fingerprint: bool = False) -> str:
    """Detect and redact common secrets in string values."""
    if not isinstance(value, str):
        return value

    # 1. Private keys
    def sub_private_key(m: re.Match) -> str:
        if with_fingerprint:
            fp = get_secret_fingerprint(m.group(0))
            return f"[REDACTED_PRIVATE_KEY_{fp}]"
        return "[REDACTED_PRIVATE_KEY]"
    value = PATTERNS["private_key"].sub(sub_private_key, value)

    # 2. OpenAI
    def sub_openai(m: re.Match) -> str:
        if with_fingerprint:
            fp = get_secret_fingerprint(m.group(0))
            return f"[REDACTED_SECRET_{fp}]"
        return "[REDACTED_SECRET]"
    value = PATTERNS["openai"].sub(sub_openai, value)

    # 3. Anthropic
    def sub_anthropic(m: re.Match) -> str:
        if with_fingerprint:
            fp = get_secret_fingerprint(m.group(0))
            return f"[REDACTED_SECRET_{fp}]"
        return "[REDACTED_SECRET]"
    value = PATTERNS["anthropic"].sub(sub_anthropic, value)

    # 4. GitHub
    def sub_github(m: re.Match) -> str:
        if with_fingerprint:
            fp = get_secret_fingerprint(m.group(0))
            return f"[REDACTED_SECRET_{fp}]"
        return "[REDACTED_SECRET]"
    value = PATTERNS["github"].sub(sub_github, value)

    # 5. AWS Access Key ID
    def sub_aws_id(m: re.Match) -> str:
        if with_fingerprint:
            fp = get_secret_fingerprint(m.group(0))
            return f"[REDACTED_AWS_KEY_{fp}]"
        return "[REDACTED_AWS_KEY]"
    value = PATTERNS["aws_id"].sub(sub_aws_id, value)

    # 6. Azure connection string containing AccountKey
    def sub_azure(m: re.Match) -> str:
        key_part = m.group(0)[len(m.group(1)):]
        if with_fingerprint:
            fp = get_secret_fingerprint(key_part)
            return f"{m.group(1)}[REDACTED_SECRET_{fp}]"
        return f"{m.group(1)}[REDACTED_SECRET]"
    value = PATTERNS["azure_conn"].sub(sub_azure, value)

    # 7. JWT
    def sub_jwt(m: re.Match) -> str:
        if with_fingerprint:
            fp = get_secret_fingerprint(m.group(0))
            return f"[REDACTED_SECRET_{fp}]"
        return "[REDACTED_SECRET]"
    value = PATTERNS["jwt"].sub(sub_jwt, value)

    # 8. Database URL
    def sub_db_url(m: re.Match) -> str:
        password = m.group(2)
        if with_fingerprint:
            fp = get_secret_fingerprint(password)
            redacted = f"[REDACTED_SECRET_{fp}]"
        else:
            redacted = "[REDACTED_SECRET]"
        return f"{m.group(1)}{redacted}{m.group(3)}"
    value = PATTERNS["db_url"].sub(sub_db_url, value)

    # 9. Generic assignments
    def sub_generic(m: re.Match) -> str:
        secret_val = m.group(6)
        if with_fingerprint:
            fp = get_secret_fingerprint(secret_val)
            redacted = f"[REDACTED_SECRET_{fp}]"
        else:
            redacted = "[REDACTED_SECRET]"
        return f"{m.group(1)}{m.group(2)}{m.group(3)}{m.group(4)}{m.group(5)}{redacted}{m.group(7)}"
    value = PATTERNS["generic_assignment"].sub(sub_generic, value)

    return value

def redact_dict(value: dict[str, Any], with_fingerprint: bool = False, is_sensitive: bool = False) -> dict[str, Any]:
    """Recursively search and redact secrets in dictionaries."""
    redacted = {}
    for k, v in value.items():
        item_is_sensitive = is_sensitive or (k.lower() in SENSITIVE_KEYS)
        redacted[k] = redact_secrets(v, with_fingerprint=with_fingerprint, is_sensitive=item_is_sensitive)
    return redacted

def contains_secret(value: str) -> bool:
    """Return True if the text contains any matching secret pattern."""
    if not isinstance(value, str):
        return False
    return any(p.search(value) is not None for p in PATTERNS.values())

def redact_secrets(data: Any, with_fingerprint: bool = False, is_sensitive: bool = False) -> Any:
    """Redacts secrets recursively from strings, dictionaries, lists or other data types."""
    if isinstance(data, str):
        if is_sensitive:
            if data.strip():
                if with_fingerprint:
                    fp = get_secret_fingerprint(data)
                    return f"[REDACTED_SECRET_{fp}]"
                return "[REDACTED_SECRET]"
            return data
        return redact_text(data, with_fingerprint=with_fingerprint)
    elif isinstance(data, dict):
        return redact_dict(data, with_fingerprint=with_fingerprint, is_sensitive=is_sensitive)
    elif isinstance(data, list):
        return [redact_secrets(item, with_fingerprint=with_fingerprint, is_sensitive=is_sensitive) for item in data]
    return data
