"""Abstract base class for runtime adapters."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path

from rich.console import Console


class RuntimeAdapter(ABC):
    """Base class for all runtime adapters.

    A runtime adapter projects the canonical .niyam/ source of truth
    into runtime-specific files (e.g., CLAUDE.md, .claude/, AGENTS.md).
    """

    def __init__(
        self, repo_root: Path, verbose: bool = False, dry_run: bool = False
    ) -> None:
        self.repo_root = repo_root
        self.niyam_dir = repo_root / ".niyam"
        self.verbose = verbose
        self.dry_run = dry_run

    @property
    @abstractmethod
    def name(self) -> str:
        """Runtime name (e.g., 'claude', 'codex')."""
        ...

    @abstractmethod
    def sync(self, console: Console) -> None:
        """Generate/update runtime-specific files from .niyam/."""
        ...

    @abstractmethod
    def clean(self, console: Console) -> None:
        """Remove all generated runtime files."""
        ...

    def _read_niyam_file(self, rel_path: str) -> str | None:
        """Read a file from .niyam/ if it exists."""
        fpath = self.niyam_dir / rel_path
        if fpath.exists():
            return fpath.read_text(encoding="utf-8")
        return None

    def _list_niyam_dir(self, rel_path: str) -> list[Path]:
        """List files in a .niyam/ subdirectory."""
        dpath = self.niyam_dir / rel_path
        if dpath.is_dir():
            return sorted(dpath.iterdir())
        return []

    def _write_file(self, target_path: Path, content: str, console: Console) -> None:
        """Write content to a file, respecting verbose/dry_run settings."""
        existed = target_path.exists()
        changed = True
        if existed:
            try:
                if target_path.read_text(encoding="utf-8") == content:
                    changed = False
            except Exception:
                pass

        try:
            rel = target_path.relative_to(self.repo_root)
        except ValueError:
            rel = target_path

        if self.dry_run:
            if self.verbose:
                if changed:
                    console.print(
                        f"[yellow]Dry Run: Would {'update' if existed else 'create'} {rel}[/]"
                    )
                else:
                    console.print(f"[dim]Dry Run: {rel} would remain unchanged[/]")
            return

        if changed:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(content, encoding="utf-8")
            if self.verbose:
                action = "Updated" if existed else "Created"
                console.print(f"[dim]{action} {rel}[/]")
        elif self.verbose:
            console.print(f"[dim]Unchanged {rel}[/]")

    def _mirror_directory(self, source: Path, target: Path, console: Console) -> None:
        """Mirror source directory to target, respecting verbose/dry-run settings."""
        import shutil

        if not source.is_dir():
            return
        if not self.dry_run:
            target.mkdir(parents=True, exist_ok=True)

        for src_file in source.iterdir():
            if src_file.is_file():
                dst_file = target / src_file.name
                try:
                    rel_dst = dst_file.relative_to(self.repo_root)
                except ValueError:
                    rel_dst = dst_file

                changed = True
                existed = dst_file.exists()
                if existed:
                    try:
                        if src_file.read_bytes() == dst_file.read_bytes():
                            changed = False
                    except Exception:
                        pass

                if self.dry_run:
                    if self.verbose:
                        if changed:
                            console.print(
                                f"[yellow]Dry Run: Would {'update' if existed else 'create'} {rel_dst}[/]"
                            )
                        else:
                            console.print(
                                f"[dim]Dry Run: {rel_dst} would remain unchanged[/]"
                            )
                else:
                    if changed:
                        shutil.copy2(src_file, dst_file)
                        if self.verbose:
                            action = "Updated" if existed else "Created"
                            console.print(f"[dim]{action} {rel_dst}[/]")
                    elif self.verbose:
                        console.print(f"[dim]Unchanged {rel_dst}[/]")

    def _generate_hooks(self, console: Console) -> None:
        """Generate runtime-specific hooks (pre_tool_guard.py) from policies."""
        import yaml

        hooks_dir = self.repo_root / f".{self.name}" / "hooks"

        # Load command policy
        cmd_policy_content = self._read_niyam_file("policies/commands.yaml")
        deny_list: list[str] = []
        warn_list: list[str] = []

        if cmd_policy_content:
            data = yaml.safe_load(cmd_policy_content) or {}
            deny_list = data.get("deny", [])
            warn_list = data.get("warn", [])

        # Load security policy
        security_policy_content = self._read_niyam_file("policies/security.yaml")
        deny_write_patterns: list[str] = []
        allow_write_patterns: list[str] = []

        if security_policy_content:
            sec_data = yaml.safe_load(security_policy_content) or {}
            deny_write_patterns = sec_data.get("deny_write_patterns", [])
            allow_write_patterns = sec_data.get("allow_write_patterns", [])

        # Load guard state
        niyam_config_content = self._read_niyam_file("niyam.yaml")
        frozen_paths: list[str] = []
        guard_enabled = False
        remote_policy_url: str | None = None

        if niyam_config_content:
            config_data = yaml.safe_load(niyam_config_content) or {}
            guard = config_data.get("guard", {})
            guard_enabled = guard.get("enabled", False)
            frozen_paths = guard.get("frozen_paths", [])
            remote_policy_url = guard.get("remote_policy_url")

        # Write a local policy cache that the hook reads at runtime.
        niyam_dir = self.repo_root / ".niyam"
        hook_config_dir = niyam_dir / "hook-cache"
        if not self.dry_run:
            hook_config_dir.mkdir(parents=True, exist_ok=True)

        hook_config = {
            "guard_enabled": guard_enabled,
            "deny_patterns": deny_list,
            "warn_patterns": warn_list,
            "deny_write_patterns": deny_write_patterns,
            "allow_write_patterns": allow_write_patterns,
            "frozen_paths": frozen_paths,
        }
        hook_config_path = hook_config_dir / "guard-config.json"
        self._write_file(hook_config_path, json.dumps(hook_config, indent=2), console)

        hook_content = self._render_hook_script(
            deny_list,
            warn_list,
            deny_write_patterns,
            allow_write_patterns,
            frozen_paths,
            guard_enabled,
            remote_policy_url,
        )
        hook_path = hooks_dir / "pre_tool_guard.py"
        self._write_file(hook_path, hook_content, console)

    def _render_hook_script(
        self,
        deny_list: list[str],
        warn_list: list[str],
        deny_write_patterns: list[str],
        allow_write_patterns: list[str],
        frozen_paths: list[str],
        guard_enabled: bool,
        remote_policy_url: str | None,
    ) -> str:
        """Render the pre-tool guard hook script."""
        return f'''#!/usr/bin/env python3
"""Niyam pre-tool guard hook for {self.name.capitalize()} Code.

Generated by Niyam — do not edit directly. Run `niyam sync` to update.
Configuration is loaded from .niyam/hook-cache/guard-config.json at runtime.
"""

import json
import sys
import fnmatch
from datetime import datetime, timezone
from pathlib import Path


# ── Load configuration from .niyam/ at runtime ─────────────────────────


def _find_niyam_root():
    """Walk up from the hook file to find the .niyam directory."""
    hook_dir = Path(__file__).resolve().parent
    current = hook_dir.parent.parent  # .{self.name}/hooks/ -> repo root
    for _ in range(5):
        if (current / ".niyam").is_dir():
            return current
        current = current.parent
    return hook_dir.parent.parent


_REPO_ROOT = _find_niyam_root()
_CONFIG_PATH = _REPO_ROOT / ".niyam" / "hook-cache" / "guard-config.json"

GUARD_ENABLED = False
DENY_PATTERNS = []
WARN_PATTERNS = []
DENY_WRITE_PATTERNS = []
ALLOW_WRITE_PATTERNS = []
FROZEN_PATHS = []

if _CONFIG_PATH.exists():
    try:
        with open(_CONFIG_PATH) as _f:
            _cfg = json.load(_f)
        GUARD_ENABLED = _cfg.get("guard_enabled", False)
        DENY_PATTERNS = _cfg.get("deny_patterns", [])
        WARN_PATTERNS = _cfg.get("warn_patterns", [])
        DENY_WRITE_PATTERNS = _cfg.get("deny_write_patterns", [])
        ALLOW_WRITE_PATTERNS = _cfg.get("allow_write_patterns", [])
        FROZEN_PATHS = _cfg.get("frozen_paths", [])
    except Exception:
        pass


def log_policy_event(event_type, details):
    """Log a policy event for evidence."""
    import fcntl

    evidence_dir = _REPO_ROOT / ".niyam" / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    log_file = evidence_dir / "policy-events.json"

    event = {{
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "type": event_type,
        "details": details,
    }}

    with open(log_file, "a+", encoding="utf-8") as f:
        try:
            fcntl.flock(f, fcntl.LOCK_EX)
            f.seek(0)
            content = f.read().strip()
            if content:
                try:
                    events = json.loads(content)
                    if not isinstance(events, list):
                        events = []
                except Exception:
                    events = []
            else:
                events = []

            events.append(event)
            f.seek(0)
            f.truncate()
            json.dump(events, f, indent=2)
        finally:
            try:
                fcntl.flock(f, fcntl.LOCK_UN)
            except Exception:
                pass


# ── Hook logic ─────────────────────────────────────────────────────────


def _matches_pattern(command_lower, pattern):
    """Token-prefix + glob matching for command patterns."""
    cmd_tokens = command_lower.split()
    pat_tokens = pattern.lower().split()
    if cmd_tokens[: len(pat_tokens)] == pat_tokens:
        return True
    return fnmatch.fnmatch(command_lower, pattern.lower())


def check_command(command):
    """Check a command against policies."""
    if not GUARD_ENABLED:
        return {{"allowed": True}}

    command_lower = command.lower().strip()

    for pattern in DENY_PATTERNS:
        if _matches_pattern(command_lower, pattern):
            log_policy_event("BLOCKED", "Denied command: " + command)
            return {{
                "allowed": False,
                "reason": "Blocked by Niyam policy: '"
                + pattern
                + "' is in the deny list.",
            }}

    for pattern in WARN_PATTERNS:
        if _matches_pattern(command_lower, pattern):
            log_policy_event("WARNING", "Cautioned command: " + command)
            return {{
                "allowed": True,
                "warning": "Niyam caution: '" + pattern + "' - proceed carefully.",
            }}

    return {{"allowed": True}}


def check_file_path(file_path):
    """Check if a file path violates write restriction or frozen scope policies."""
    if not GUARD_ENABLED:
        return {{"allowed": True}}

    if DENY_WRITE_PATTERNS and any(
        fnmatch.fnmatch(file_path, pat) for pat in DENY_WRITE_PATTERNS
    ):
        log_policy_event(
            "BLOCKED", "Write restriction violation (deny list): " + file_path
        )
        return {{
            "allowed": False,
            "reason": "Blocked by Niyam security policy: file '"
            + file_path
            + "' matches deny_write_patterns.",
        }}
    if ALLOW_WRITE_PATTERNS and not any(
        fnmatch.fnmatch(file_path, pat) for pat in ALLOW_WRITE_PATTERNS
    ):
        log_policy_event(
            "BLOCKED", "Write restriction violation (not in allow list): " + file_path
        )
        return {{
            "allowed": False,
            "reason": "Blocked by Niyam security policy: file '"
            + file_path
            + "' does not match allow_write_patterns.",
        }}

    if FROZEN_PATHS:
        for allowed_path in FROZEN_PATHS:
            if file_path.startswith(allowed_path):
                return {{"allowed": True}}
        log_policy_event("BLOCKED", "File outside frozen scope: " + file_path)
        return {{
            "allowed": False,
            "reason": "Blocked by Niyam guard: file '"
            + file_path
            + "' is outside the allowed scope: "
            + str(FROZEN_PATHS),
        }}

    return {{"allowed": True}}


if __name__ == "__main__":
    input_data = json.loads(sys.stdin.read())
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {{}})

    result = {{"allowed": True}}

    if tool_name in ("bash", "shell", "terminal", "run_command"):
        command = tool_input.get("command", "") or tool_input.get("CommandLine", "")
        result = check_command(command)
    elif tool_name in (
        "write_file",
        "edit_file",
        "replace_file_content",
        "multi_replace_file_content",
    ):
        file_path = tool_input.get("file_path", "") or tool_input.get("TargetFile", "")
        result = check_file_path(file_path)

    print(json.dumps(result))
'''
