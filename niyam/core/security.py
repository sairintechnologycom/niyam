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
    # Development, Packaging and Repo Utils
    "git",
    "pip",
    "uv",
    "poetry",
    "mkdir",
    "rm",
    "cp",
    "mv",
}


class CommandSecurityError(Exception):
    """Raised when a command fails security validation."""


def validate_command(cmd: str, repo_root: Path | None = None) -> list[str]:
    """Validate and split a command string safely.

    Returns the command as a list of arguments (shlex-split).
    Raises CommandSecurityError if the command base is not in the allowlist
    or if command arguments violate path traversal policies.
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

    # Hardening dangerous executables
    if repo_root is not None:
        repo_resolved = repo_root.resolve()

        # 1. Check path arguments for file manipulation utilities
        if executable in {"rm", "cp", "mv", "mkdir"}:
            for arg in parts[1:]:
                # Skip flags/options (e.g., -r, -f, --recursive)
                if arg.startswith("-"):
                    continue

                # BLOCK WILDCARDS (*) to prevent destructive broad matches
                if "*" in arg:
                    raise CommandSecurityError(
                        f"Wildcards ('*') are blocked in '{executable}' arguments for safety. "
                        "Specify individual file paths instead."
                    )

                # Check if this argument resolves outside repo_root
                try:
                    resolved_arg = (repo_resolved / arg).resolve()
                    resolved_arg.relative_to(repo_resolved)
                except ValueError:
                    raise CommandSecurityError(
                        f"Argument '{arg}' in command '{executable}' points outside the repository root. "
                        "File manipulation outside the repository root is blocked."
                    )

                # Special protection for root-level critical files/dirs
                if resolved_arg == repo_resolved:
                    raise CommandSecurityError(
                        f"Command '{executable}' is blocked from targeting the repository root directly."
                    )

        # 2. Check Git commands
        elif executable == "git":
            blocked_git_args = {"--force", "-f", "--mirror", "--delete"}
            # Specifically block destructive operations on protected branches or force updates
            for arg in parts[1:]:
                if arg in blocked_git_args:
                    raise CommandSecurityError(
                        f"Destructive Git flag '{arg}' is blocked for safety. Force updates are not allowed."
                    )
            
            # Block push to main/master directly if detected
            if "push" in parts:
                for arg in parts:
                    if arg in ("main", "master", "prod", "production"):
                        raise CommandSecurityError(
                            f"Direct Git push to protected branch '{arg}' is blocked. Use a pull request instead."
                        )

        # 3. Check Docker volume/mount arguments
        elif executable in {"docker", "docker-compose"}:
            for arg in parts[1:]:
                # Check for volume mapping flags like -v host_path:container_path
                # or --volume host_path:container_path
                if ":" in arg and not arg.startswith("-"):
                    parts_mount = arg.split(":")
                    host_part = parts_mount[0]
                    if host_part == "/var/run/docker.sock":
                        continue
                    try:
                        resolved_host = (repo_resolved / host_part).resolve()
                        resolved_host.relative_to(repo_resolved)
                    except ValueError:
                        raise CommandSecurityError(
                            f"Docker volume host path '{host_part}' resolves outside the repository root. "
                            "Mounting directories outside the repository root is blocked."
                        )
                elif "source=" in arg:
                    for sub in arg.split(","):
                        if sub.startswith("source="):
                            host_part = sub.split("=", 1)[1]
                            if host_part == "/var/run/docker.sock":
                                continue
                            try:
                                resolved_host = (repo_resolved / host_part).resolve()
                                resolved_host.relative_to(repo_resolved)
                            except ValueError:
                                raise CommandSecurityError(
                                    f"Docker mount source path '{host_part}' resolves outside the repository root. "
                                    "Mounting directories outside the repository root is blocked."
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
    redirection_mode = None
    redirection_file = None
    exec_cmd = cmd

    if ">>" in cmd:
        parts_split = cmd.split(">>", 1)
        exec_cmd = parts_split[0].strip()
        redirection_file = parts_split[1].strip()
        redirection_mode = "a"
    elif ">" in cmd:
        parts_split = cmd.split(">", 1)
        exec_cmd = parts_split[0].strip()
        redirection_file = parts_split[1].strip()
        redirection_mode = "w"

    if redirection_file and redirection_mode:
        # Strip quotes if present
        if (redirection_file.startswith("'") and redirection_file.endswith("'")) or (
            redirection_file.startswith('"') and redirection_file.endswith('"')
        ):
            redirection_file = redirection_file[1:-1]

        dest_path = validate_path_within_repo(redirection_file, cwd)
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        parts = validate_command(exec_cmd, repo_root=cwd)

        sub_kwargs = kwargs.copy()
        if capture_output:
            sub_kwargs["stderr"] = subprocess.PIPE

        with open(dest_path, redirection_mode, encoding="utf-8") as f:
            res = subprocess.run(
                parts,
                cwd=cwd,
                stdout=f,
                timeout=timeout,
                text=text,
                **sub_kwargs,
            )
        return res

    parts = validate_command(cmd, repo_root=cwd)
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

    try:
        resolved.relative_to(repo_resolved)
    except ValueError:
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
