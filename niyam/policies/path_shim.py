"""PATH-shim command guards for hookless coding-agent runtimes.

Runtimes without in-loop hooks (Codex, Gemini, custom CLIs) cannot load
Claude-style pre_tool_use scripts. For those, Niyam installs thin wrappers
under ``.niyam/shims/bin`` and prepends that directory to the subprocess PATH
so shell commands like ``git push --force`` still hit policy before the real
binary.

Shim scripts consult ``.niyam/hook-cache/guard-config.json`` (and fall back to
``.niyam/policies/commands.yaml`` deny patterns).
"""

from __future__ import annotations

import json
import os
import shutil
import stat
import textwrap
from pathlib import Path
from typing import Iterable

# Commands most often used by coding agents that may match deny patterns.
DEFAULT_SHIM_COMMANDS: tuple[str, ...] = (
    "git",
    "rm",
    "npm",
    "npx",
    "pnpm",
    "yarn",
    "terraform",
    "sudo",
    "curl",
    "chmod",
    "chown",
    "dd",
    "mkfs",
    "kubectl",
    "docker",
    "pip",
    "pip3",
    "uv",
    "poetry",
)


DEFAULT_DENY_PATTERNS: list[str] = [
    "rm -rf",
    "sudo",
    "chmod 777",
    "git push --force",
    "git reset --hard",
    "npm publish",
    "terraform apply",
    "terraform destroy",
    "curl * | sh",
    "DROP TABLE",
    "DROP DATABASE",
]


def shim_dir(repo_root: Path) -> Path:
    return Path(repo_root) / ".niyam" / "shims" / "bin"


def _load_deny_patterns(repo_root: Path) -> list[str]:
    patterns: list[str] = []
    guard_cfg = Path(repo_root) / ".niyam" / "hook-cache" / "guard-config.json"
    if guard_cfg.exists():
        try:
            data = json.loads(guard_cfg.read_text(encoding="utf-8"))
            patterns.extend(data.get("deny_patterns") or [])
        except Exception:
            pass
    commands_yaml = Path(repo_root) / ".niyam" / "policies" / "commands.yaml"
    if commands_yaml.exists():
        try:
            import yaml

            data = yaml.safe_load(commands_yaml.read_text(encoding="utf-8")) or {}
            deny = data.get("deny") or []
            if isinstance(deny, list):
                patterns.extend(str(p) for p in deny)
        except Exception:
            pass
    # Dedupe preserve order
    seen: set[str] = set()
    out: list[str] = []
    for p in patterns or DEFAULT_DENY_PATTERNS:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out or list(DEFAULT_DENY_PATTERNS)


def _shim_script_body(command_name: str) -> str:
    """Generate a self-contained Python wrapper for one command name."""
    # Use a pure-python wrapper so we do not depend on bash features on Windows.
    return textwrap.dedent(
        f'''\
        #!/usr/bin/env python3
        """Niyam PATH shim for `{command_name}`. Auto-generated — do not edit."""
        from __future__ import annotations

        import fnmatch
        import json
        import os
        import shutil
        import sys
        from datetime import datetime, timezone
        from pathlib import Path


        COMMAND = {command_name!r}


        def _find_repo_root() -> Path:
            here = Path(__file__).resolve()
            # .niyam/shims/bin/<cmd> -> repo root is parents[3]
            if len(here.parents) >= 4 and here.parents[2].name == "shims":
                return here.parents[3]
            current = here.parent
            for _ in range(8):
                if (current / ".niyam").is_dir():
                    return current
                current = current.parent
            return here.parents[3] if len(here.parents) >= 4 else Path.cwd()


        def _load_deny(repo: Path) -> tuple[bool, list[str]]:
            enabled = True
            patterns: list[str] = []
            cfg = repo / ".niyam" / "hook-cache" / "guard-config.json"
            if cfg.exists():
                try:
                    data = json.loads(cfg.read_text(encoding="utf-8"))
                    enabled = bool(data.get("guard_enabled", True))
                    patterns.extend(data.get("deny_patterns") or [])
                except Exception:
                    pass
            yml = repo / ".niyam" / "policies" / "commands.yaml"
            if yml.exists():
                try:
                    import yaml  # type: ignore

                    data = yaml.safe_load(yml.read_text(encoding="utf-8")) or {{}}
                    deny = data.get("deny") or []
                    if isinstance(deny, list):
                        patterns.extend(str(p) for p in deny)
                except Exception:
                    # Minimal YAML-free fallback for deny list lines
                    try:
                        in_deny = False
                        for line in yml.read_text(encoding="utf-8").splitlines():
                            s = line.strip()
                            if s.startswith("deny:"):
                                in_deny = True
                                continue
                            if in_deny:
                                if s.startswith("- "):
                                    patterns.append(s[2:].strip().strip('"').strip("'"))
                                elif s and not s.startswith("#") and ":" in s:
                                    break
                    except Exception:
                        pass
            if not patterns:
                patterns = [
                    "rm -rf",
                    "sudo",
                    "chmod 777",
                    "git push --force",
                    "git reset --hard",
                    "npm publish",
                    "terraform apply",
                    "terraform destroy",
                    "curl * | sh",
                    "DROP TABLE",
                    "DROP DATABASE",
                ]
            return enabled, patterns


        def _match(command_lower: str, pattern: str) -> bool:
            cmd_tokens = command_lower.split()
            pat_tokens = pattern.lower().split()
            if pat_tokens and cmd_tokens[: len(pat_tokens)] == pat_tokens:
                return True
            return fnmatch.fnmatch(command_lower, pattern.lower())


        def _log_block(repo: Path, command: str, pattern: str) -> None:
            evidence = repo / ".niyam" / "evidence"
            evidence.mkdir(parents=True, exist_ok=True)
            log_file = evidence / "policy-events.json"
            event = {{
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "type": "BLOCKED",
                "details": f"PATH-shim denied command: {{command}} (pattern: {{pattern}})",
                "source": "path_shim",
                "command": command,
                "pattern": pattern,
            }}
            try:
                events = []
                if log_file.exists():
                    try:
                        events = json.loads(log_file.read_text(encoding="utf-8"))
                        if not isinstance(events, list):
                            events = []
                    except Exception:
                        events = []
                events.append(event)
                log_file.write_text(json.dumps(events, indent=2), encoding="utf-8")
            except Exception:
                pass
            # Also append JSONL for streaming consumers
            try:
                with open(evidence / "policy-events.jsonl", "a", encoding="utf-8") as f:
                    f.write(json.dumps(event) + "\\n")
            except Exception:
                pass


        def _real_binary(name: str) -> str | None:
            shim_bin = str(Path(__file__).resolve().parent)
            path = os.environ.get("PATH", "")
            cleaned = os.pathsep.join(
                p for p in path.split(os.pathsep) if p and os.path.abspath(p) != shim_bin
            )
            return shutil.which(name, path=cleaned)


        def main() -> int:
            if os.environ.get("NIYAM_PATH_SHIM", "1") in ("0", "false", "False", "no"):
                real = _real_binary(COMMAND)
                if not real:
                    sys.stderr.write(f"niyam-shim: real binary for {{COMMAND}} not found\\n")
                    return 127
                os.execv(real, [real, *sys.argv[1:]])

            repo = _find_repo_root()
            enabled, patterns = _load_deny(repo)
            argv_cmd = " ".join([COMMAND, *sys.argv[1:]])
            if enabled:
                lower = argv_cmd.lower().strip()
                for pattern in patterns:
                    if _match(lower, pattern):
                        _log_block(repo, argv_cmd, pattern)
                        sys.stderr.write(
                            f"Blocked by Niyam PATH-shim: '{{pattern}}' is in the deny list.\\n"
                            f"Command: {{argv_cmd}}\\n"
                        )
                        return 126

            real = _real_binary(COMMAND)
            if not real:
                sys.stderr.write(f"niyam-shim: real binary for {{COMMAND}} not found\\n")
                return 127
            os.execv(real, [real, *sys.argv[1:]])
            return 127  # unreachable


        if __name__ == "__main__":
            raise SystemExit(main())
        '''
    )


def ensure_path_shim(
    repo_root: Path,
    *,
    commands: Iterable[str] | None = None,
    force: bool = False,
) -> Path:
    """Write/update shim wrappers under ``.niyam/shims/bin`` and return that path."""
    root = Path(repo_root)
    bin_dir = shim_dir(root)
    bin_dir.mkdir(parents=True, exist_ok=True)

    # Persist effective deny patterns next to shims for debugging
    deny = _load_deny_patterns(root)
    meta = {
        "deny_patterns": deny,
        "commands": list(commands or DEFAULT_SHIM_COMMANDS),
    }
    (bin_dir.parent / "shim-config.json").write_text(
        json.dumps(meta, indent=2), encoding="utf-8"
    )

    for name in commands or DEFAULT_SHIM_COMMANDS:
        target = bin_dir / name
        if target.exists() and not force:
            # Refresh if empty/corrupt
            try:
                if target.stat().st_size > 50:
                    continue
            except OSError:
                pass
        target.write_text(_shim_script_body(name), encoding="utf-8")
        mode = target.stat().st_mode
        target.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    return bin_dir


def runtime_needs_path_shim(runtime_name: str, repo_root: Path | None = None) -> bool:
    """Hookless runtimes need PATH shims; Claude with hooks is optional."""
    if os.environ.get("NIYAM_PATH_SHIM", "1") in ("0", "false", "False", "no"):
        return False
    if os.environ.get("NIYAM_PATH_SHIM_FORCE") in ("1", "true", "True", "yes"):
        return True
    try:
        from niyam.runtimes.registry import get_runtime_spec

        spec = get_runtime_spec(runtime_name, repo_root)
        if spec is None:
            return True
        caps = set(spec.capabilities or [])
        # Only Claude-class runtimes declare "hooks" today
        return "hooks" not in caps
    except Exception:
        return True


def inject_path_shim_env(
    env: dict[str, str],
    repo_root: Path,
    runtime_name: str,
    *,
    force: bool = False,
) -> dict[str, str]:
    """Return a copy of env with shim dir prepended when needed."""
    out = dict(env)
    if not force and not runtime_needs_path_shim(runtime_name, repo_root):
        return out
    bin_dir = ensure_path_shim(repo_root)
    current = out.get("PATH", os.environ.get("PATH", ""))
    prefix = str(bin_dir)
    if current.split(os.pathsep)[0] != prefix:
        out["PATH"] = prefix + os.pathsep + current if current else prefix
    out["NIYAM_PATH_SHIM"] = out.get("NIYAM_PATH_SHIM", "1")
    out["NIYAM_SHIM_DIR"] = prefix
    return out


def which_real(command: str, env: dict[str, str] | None = None) -> str | None:
    """Locate the real binary, skipping Niyam shim directories."""
    path = (env or os.environ).get("PATH", os.environ.get("PATH", ""))
    parts = []
    for p in path.split(os.pathsep):
        if not p:
            continue
        # Skip known shim locations
        if p.endswith(str(Path(".niyam") / "shims" / "bin")) or "/.niyam/shims/bin" in p:
            continue
        parts.append(p)
    return shutil.which(command, path=os.pathsep.join(parts))
