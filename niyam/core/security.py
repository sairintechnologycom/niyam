"""Niyam security utilities — shared hardening primitives."""

from __future__ import annotations

import shlex
import subprocess
from pathlib import Path
from typing import Any

import yaml


# ── Safe Command Execution ─────────────────────────────────────────────

# Commands whose base executable is trusted for validation.
# Only the first token of the command is checked against this set.
ALLOWED_VALIDATION_EXECUTABLES: set[str] = {
    # Python
    "pytest",
    "python",
    "python3",
    "mypy",
    "ruff",
    "black",
    "isort",
    "flake8",
    "pylint",
    "pyright",
    "bandit",
    "safety",
    "pip-audit",
    # Node / JS
    "npm",
    "npx",
    "yarn",
    "pnpm",
    "bun",
    "node",
    "tsc",
    "eslint",
    "prettier",
    # Rust
    "cargo",
    "clippy",
    # Go
    "go",
    # General build
    "make",
    "cmake",
    "gradle",
    "mvn",
    # Docker
    "docker",
    "docker-compose",
    # Security scanners
    "semgrep",
    "gitleaks",
    "detect-secrets",
    "trivy",
    "grype",
    # Shell utilities commonly used in validation
    "echo",
    "cat",
    "grep",
    "wc",
    "diff",
    "test",
}


class CommandSecurityError(Exception):
    """Raised when a command fails security validation."""


def validate_command(cmd: str) -> list[str]:
    """Validate and split a command string safely.

    Returns the command as a list of arguments (shlex-split).
    Raises CommandSecurityError if the command base is not in the allowlist.
    """
    if not cmd or not cmd.strip():
        raise CommandSecurityError("Empty command is not allowed")

    # Split using shlex to handle quoting properly
    try:
        parts = shlex.split(cmd)
    except ValueError as e:
        raise CommandSecurityError(f"Malformed command string: {e}")

    if not parts:
        raise CommandSecurityError("Empty command after parsing")

    executable = Path(
        parts[0]
    ).name  # Strip any path prefix (e.g. /usr/bin/pytest → pytest)

    if executable not in ALLOWED_VALIDATION_EXECUTABLES:
        raise CommandSecurityError(
            f"Command executable '{executable}' is not in the allowed validation "
            f"commands list. Allowed: {', '.join(sorted(ALLOWED_VALIDATION_EXECUTABLES))}"
        )

    # Check for obvious shell injection patterns even within allowed commands
    dangerous_chars = {";", "&&", "||", "|", "`", "$(", "${"}
    for char in dangerous_chars:
        if char in cmd:
            raise CommandSecurityError(
                f"Command contains potentially dangerous shell operator '{char}'. "
                "Use separate validation commands instead of chaining."
            )

    return parts


def safe_run_command(
    cmd: str,
    cwd: Path,
    *,
    timeout: int = 120,
    capture_output: bool = True,
    text: bool = True,
    **kwargs: Any,
) -> subprocess.CompletedProcess:
    """Run a validation command safely without shell=True.

    The command is validated against the allowlist and split using shlex
    before execution. This prevents shell injection attacks from malicious
    project.yaml or mission-plan.yaml files.
    """
    parts = validate_command(cmd)
    return subprocess.run(
        parts,
        cwd=cwd,
        capture_output=capture_output,
        text=text,
        timeout=timeout,
        **kwargs,
    )


# ── Safe YAML Loading ──────────────────────────────────────────────────

MAX_YAML_FILE_SIZE = 1_048_576  # 1 MB


def safe_load_yaml(path: Path) -> dict:
    """Load YAML with size limit to prevent DoS.

    Raises ValueError if file exceeds MAX_YAML_FILE_SIZE.
    Raises FileNotFoundError if file does not exist.
    """
    if not path.exists():
        raise FileNotFoundError(f"YAML file not found: {path}")

    file_size = path.stat().st_size
    if file_size > MAX_YAML_FILE_SIZE:
        raise ValueError(
            f"YAML file '{path.name}' exceeds maximum allowed size "
            f"({file_size:,} bytes > {MAX_YAML_FILE_SIZE:,} bytes)"
        )

    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


# ── Path Validation ────────────────────────────────────────────────────


def validate_path_within_repo(path_str: str, repo_root: Path) -> Path:
    """Validate that a path resolves within the repository root.

    Prevents path traversal attacks (../../etc/passwd).
    """
    resolved = (repo_root / path_str).resolve()
    repo_resolved = repo_root.resolve()

    if not str(resolved).startswith(str(repo_resolved)):
        raise ValueError(
            f"Path '{path_str}' resolves outside the repository root. "
            "Path traversal is not allowed."
        )

    return resolved


def sanitize_filename(name: str) -> str:
    """Sanitize a filename to prevent injection.

    Strips path separators, '..' sequences, and special characters.
    """
    # Remove path separators and parent directory references
    sanitized = name.replace("/", "").replace("\\", "").replace("..", "")

    # Keep only alphanumeric, hyphens, underscores, and dots
    sanitized = "".join(c for c in sanitized if c.isalnum() or c in "-_.")

    if not sanitized:
        raise ValueError(f"Filename '{name}' is empty after sanitization")

    return sanitized
