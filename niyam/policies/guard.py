"""Niyam guard — safety guardrails for AI-assisted development."""

from __future__ import annotations

from pathlib import Path

import yaml
from rich.console import Console
from rich.panel import Panel

from niyam.core.config import (
    find_niyam_root,
    load_niyam_config,
    save_niyam_config,
)


def _ensure_root(console: Console) -> Path:
    """Find niyam root or exit."""
    root = find_niyam_root()
    if root is None:
        console.print(
            "[bold red]Error:[/] Not a Niyam workspace. Run [bold]niyam init[/] first."
        )
        raise SystemExit(1)
    return root


def _resync_hooks(root: Path, console: Console) -> None:
    """Re-sync hooks for all active runtimes after guard state change."""
    config = load_niyam_config(root)
    for rt in config.runtimes:
        if rt == "claude":
            from niyam.runtimes.claude import ClaudeAdapter

            adapter = ClaudeAdapter(root)
            adapter._generate_hooks(console)
            console.print("[dim]  ↳ Claude hooks regenerated[/]")
        elif rt == "gemini":
            from niyam.runtimes.gemini import GeminiAdapter

            adapter = GeminiAdapter(root)
            adapter._generate_hooks(console)
            console.print("[dim]  ↳ Gemini hooks regenerated[/]")
        elif rt == "codex":
            from niyam.runtimes.codex import CodexAdapter

            adapter = CodexAdapter(root)
            adapter._generate_hooks(console)
            console.print("[dim]  ↳ Codex hooks regenerated[/]")


def run_guard_enable(console: Console, dry_run: bool = False) -> None:
    """Enable all configured guardrails."""
    root = _ensure_root(console)
    config = load_niyam_config(root)

    if dry_run:
        console.print(
            "[yellow]Dry Run: Would enable guard mode (denied commands blocked, careful mode active)[/]"
        )
        return

    config.guard.enabled = True
    config.guard.careful = True
    save_niyam_config(config, root)

    _resync_hooks(root, console)

    console.print(
        Panel(
            "[bold green]✓[/] Guard mode [bold]enabled[/]\n"
            "  [dim]•[/] Denied commands will be blocked\n"
            "  [dim]•[/] Careful mode active (destructive command warnings)\n"
            + (
                f"  [dim]•[/] Frozen paths: {', '.join(config.guard.frozen_paths)}\n"
                if config.guard.frozen_paths
                else ""
            ),
            title="[bold green]Guard Enabled[/]",
            border_style="green",
        )
    )


def run_guard_disable(console: Console, dry_run: bool = False) -> None:
    """Disable all guardrails."""
    root = _ensure_root(console)
    config = load_niyam_config(root)

    if dry_run:
        console.print(
            "[yellow]Dry Run: Would disable guard mode (AI agents can execute freely)[/]"
        )
        return

    config.guard.enabled = False
    config.guard.careful = False
    config.guard.frozen_paths = []
    save_niyam_config(config, root)

    _resync_hooks(root, console)

    console.print(
        "[yellow]⚠ Guard mode [bold]disabled[/]. AI agents can execute freely.[/]"
    )


def run_guard_careful(console: Console, dry_run: bool = False) -> None:
    """Enable destructive-command warnings."""
    root = _ensure_root(console)
    config = load_niyam_config(root)

    if dry_run:
        console.print(
            "[yellow]Dry Run: Would enable careful mode (warnings for destructive commands like rm -rf, etc.)[/]"
        )
        return

    config.guard.enabled = True
    config.guard.careful = True
    save_niyam_config(config, root)

    # Add warn entries to commands.yaml if not present
    cmd_policy_path = root / ".niyam" / "policies" / "commands.yaml"
    if cmd_policy_path.exists():
        with open(cmd_policy_path) as f:
            data = yaml.safe_load(f) or {}
    else:
        data = {}

    default_warn = [
        "rm -rf",
        "git reset --hard",
        "git push --force",
        "DROP TABLE",
        "DROP DATABASE",
        "terraform apply",
        "terraform destroy",
        "npm publish",
    ]

    existing_warn = set(data.get("warn", []))
    for w in default_warn:
        existing_warn.add(w)
    data["warn"] = sorted(existing_warn)

    with open(cmd_policy_path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    _resync_hooks(root, console)

    console.print(
        Panel(
            "[bold green]✓[/] Careful mode [bold]enabled[/]\n"
            "  [dim]Destructive commands will trigger warnings before execution.[/]",
            title="[bold yellow]⚠ Careful Mode[/]",
            border_style="yellow",
        )
    )


def run_guard_freeze(path: str, console: Console, dry_run: bool = False) -> None:
    """Restrict AI edits to a specific directory."""
    root = _ensure_root(console)
    config = load_niyam_config(root)

    from niyam.core.security import validate_path_within_repo

    try:
        resolved_path = validate_path_within_repo(path, root)
        # Store as a relative path to repo root, keeping it portable
        clean_path = str(resolved_path.relative_to(root.resolve()))
    except ValueError as e:
        console.print(f"[bold red]Error:[/] {e}")
        raise SystemExit(1)

    if dry_run:
        console.print(
            f"[yellow]Dry Run: Would restrict edits to path '{clean_path}'[/]"
        )
        return

    if clean_path not in config.guard.frozen_paths:
        config.guard.frozen_paths.append(clean_path)

    config.guard.enabled = True
    save_niyam_config(config, root)

    _resync_hooks(root, console)

    console.print(
        Panel(
            f"[bold green]✓[/] Edits restricted to: [cyan]{', '.join(config.guard.frozen_paths)}[/]\n"
            "  [dim]Files outside these paths will be blocked.[/]",
            title="[bold cyan]Guard Freeze[/]",
            border_style="cyan",
        )
    )


def _fetch_remote_policy_raw(url: str, filename: str) -> dict:
    """Fetch policy YAML from a remote URL.

    Security hardening:
    - Enforces HTTPS-only URLs
    - Uses strict SSL certificate verification
    - Validates fetched content against known policy schemas
    - Rejects responses larger than 256 KB
    """
    import ssl
    import urllib.request
    import urllib.error
    import yaml

    MAX_RESPONSE_SIZE = 256 * 1024  # 256 KB

    if url.endswith(".yaml") or url.endswith(".yml"):
        if filename in url:
            target_url = url
        else:
            parts = url.rsplit("/", 1)
            target_url = f"{parts[0]}/{filename}"
    else:
        target_url = f"{url.rstrip('/')}/{filename}"

    # Enforce HTTPS
    if not target_url.startswith("https://"):
        raise ValueError(
            f"Remote policy URL must use HTTPS (got: {target_url}). "
            "Plain HTTP is not allowed for policy files."
        )

    try:
        # Strict SSL context — verifies certificates
        ssl_ctx = ssl.create_default_context()

        req = urllib.request.Request(target_url, headers={"User-Agent": "Niyam-CLI"})
        with urllib.request.urlopen(req, timeout=5, context=ssl_ctx) as response:
            content = response.read(MAX_RESPONSE_SIZE + 1)
            if len(content) > MAX_RESPONSE_SIZE:
                raise ValueError(
                    f"Remote policy response exceeds maximum size ({MAX_RESPONSE_SIZE} bytes)"
                )
            data = yaml.safe_load(content.decode("utf-8"))
            if not isinstance(data, dict):
                raise ValueError("Remote policy must be a YAML mapping (dict)")

            # Validate against schema
            from niyam.policies.validator import KNOWN_POLICY_FILES

            if filename in KNOWN_POLICY_FILES:
                schema = KNOWN_POLICY_FILES[filename]
                all_known = set(schema["required_keys"]) | set(schema["optional_keys"])
                unknown = set(data.keys()) - all_known
                if unknown:
                    raise ValueError(
                        f"Remote policy '{filename}' contains unknown/invalid keys: "
                        f"{', '.join(sorted(unknown))}"
                    )
            return data
    except (urllib.error.HTTPError, urllib.error.URLError) as e:
        raise RuntimeError(f"Failed to fetch remote policy from {target_url}: {e}")
    except yaml.YAMLError as e:
        raise ValueError(f"Remote policy YAML is malformed: {e}")


def _fetch_remote_policy(url: str, filename: str) -> dict | None:
    """Fetch policy YAML from a remote URL, with local caching (TTL = 300s)."""
    import time
    import json
    from niyam.core.config import find_niyam_root

    root = find_niyam_root()
    if not root:
        # No niyam workspace, fall back to raw fetch
        return _fetch_remote_policy_raw(url, filename)

    cache_dir = root / ".niyam" / "cache"
    cache_file = cache_dir / "remote-policies.json"
    cache_key = f"{url}/{filename}"

    # Try loading cache
    cache_data = {}
    if cache_file.exists():
        try:
            with open(cache_file, encoding="utf-8") as f:
                cache_data = json.load(f)
        except Exception:
            pass

    # Check cache TTL (5 minutes)
    if cache_key in cache_data:
        cached_val = cache_data[cache_key]
        if isinstance(cached_val, list) and len(cached_val) == 2:
            cached_at, data = cached_val
            if time.time() - cached_at < 300:
                return data

    # Miss: fetch raw
    try:
        data = _fetch_remote_policy_raw(url, filename)
        if data is not None:
            # Save to cache
            cache_dir.mkdir(parents=True, exist_ok=True)
            cache_data[cache_key] = [time.time(), data]
            try:
                with open(cache_file, "w", encoding="utf-8") as f:
                    json.dump(cache_data, f, indent=2)
            except Exception:
                pass
            return data
    except Exception as e:
        # Fall back to expired cache if available
        if cache_key in cache_data:
            cached_val = cache_data[cache_key]
            if isinstance(cached_val, list) and len(cached_val) == 2:
                _, data = cached_val
                import logging

                logging.getLogger("niyam.guard").warning(
                    "Remote policy fetch failed (%s). Using cached version.", e
                )
                return data
        raise e

    return None


def load_security_policy(root: Path) -> dict:
    """Load security policy from remote URL if configured, falling back to local file."""
    import logging

    logger = logging.getLogger("niyam.guard")

    try:
        config = load_niyam_config(root)
        remote_url = config.guard.remote_policy_url
    except Exception:
        remote_url = None

    if remote_url:
        try:
            remote_data = _fetch_remote_policy(remote_url, "security.yaml")
            if remote_data is not None:
                return remote_data
        except Exception as e:
            logger.warning(
                "Failed to fetch remote security policy: %s. Falling back to local.", e
            )

    # Fallback to local
    local_path = root / ".niyam" / "policies" / "security.yaml"
    if local_path.exists():
        try:
            from niyam.core.security import safe_load_yaml

            return safe_load_yaml(local_path)
        except Exception:
            pass
    return {}


def load_commands_policy(root: Path) -> dict:
    """Load commands policy from remote URL if configured, falling back to local file."""
    import logging

    logger = logging.getLogger("niyam.guard")

    try:
        config = load_niyam_config(root)
        remote_url = config.guard.remote_policy_url
    except Exception:
        remote_url = None

    if remote_url:
        try:
            remote_data = _fetch_remote_policy(remote_url, "commands.yaml")
            if remote_data is not None:
                return remote_data
        except Exception as e:
            logger.warning(
                "Failed to fetch remote commands policy: %s. Falling back to local.", e
            )

    # Fallback to local
    local_path = root / ".niyam" / "policies" / "commands.yaml"
    if local_path.exists():
        try:
            from niyam.core.security import safe_load_yaml

            return safe_load_yaml(local_path)
        except Exception:
            pass
    return {}


def run_guard_run(cmd_args: list[str], capture_output: bool, console: Console, mode_override: str | None = None) -> None:
    import sys
    import os
    import re
    import time
    import json
    from datetime import datetime, timezone
    import subprocess

    if not cmd_args:
        console.print(
            "[bold red]Error:[/] No command specified. Usage: niyam guard run -- <command>"
        )
        raise SystemExit(1)

    root = find_niyam_root()
    if root is None:
        root = Path.cwd()

    logs_dir = root / ".niyam" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_file = logs_dir / "guard-actions.jsonl"

    # Session ID calculation
    session_id = os.environ.get("NIYAM_SESSION_ID")
    if not session_id:
        try:
            res = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=root,
                capture_output=True,
                text=True,
                check=False,
            )
            if res.returncode == 0:
                session_id = res.stdout.strip()
        except Exception:
            pass
    if not session_id:
        session_id = "default-session"

    actor_type = os.environ.get("NIYAM_ACTOR_TYPE", "agent")

    # Load config to get policy mode and lists
    mode = "observe"
    blocked_commands = []
    protected_files = []
    approval_required = []

    try:
        config = load_niyam_config(root)
        if config and config.governance and config.governance.guard:
            mode = config.governance.guard.mode
            blocked_commands = config.governance.guard.blocked_commands
            protected_files = config.governance.guard.protected_files
            approval_required = config.governance.guard.approval_required
    except Exception:
        pass

    if mode_override:
        mode = mode_override

    command_str = " ".join(cmd_args)

    # Redact secret assignments in command
    redacted_command = re.sub(
        r'(?i)(api_key|apikey|secret_key|private_key|token|auth_token|password|pass)\s*[=:]\s*["\']?[a-zA-Z0-9_\-\.]{8,}["\']?',
        r"\1=REDACTED",
        command_str,
    )

    is_blocked = any(blocked in command_str for blocked in blocked_commands)
    is_protected_file = any(f in command_str for f in protected_files)
    is_approval = any(appr in command_str for appr in approval_required)

    decision = "allowed"

    # Check Block Mode
    if mode == "block":
        if is_blocked or is_protected_file:
            console.print("[bold red]Blocked:[/] Command violates governance policy.")
            log_entry = {
                "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "session_id": session_id,
                "actor_type": actor_type,
                "tool": "shell",
                "action": "command_execute",
                "command": redacted_command,
                "cwd": str(Path.cwd().resolve()),
                "exit_code": 1,
                "duration_ms": 0,
                "mode": "block",
                "decision": "blocked",
            }
            try:
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(log_entry) + "\n")
            except Exception:
                pass
            raise SystemExit(1)
        elif is_approval:
            # Requires approval
            import typer
            try:
                allowed = typer.confirm("Approval required for command. Allow execution?", default=False)
            except Exception:
                allowed = False
            if not allowed:
                console.print("[bold red]Denied:[/] User rejected execution.")
                log_entry = {
                    "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    "session_id": session_id,
                    "actor_type": actor_type,
                    "tool": "shell",
                    "action": "command_execute",
                    "command": redacted_command,
                    "cwd": str(Path.cwd().resolve()),
                    "exit_code": 1,
                    "duration_ms": 0,
                    "mode": "block",
                    "decision": "denied",
                }
                try:
                    with open(log_file, "a", encoding="utf-8") as f:
                        f.write(json.dumps(log_entry) + "\n")
                except Exception:
                    pass
                raise SystemExit(1)
            decision = "approved"

    # Check Warn Mode
    elif mode == "warn":
        if is_blocked or is_protected_file or is_approval:
            console.print("[bold yellow]Warning:[/] Command is flagged as dangerous.")
            decision = "warned"

    # Check Approve Mode
    elif mode == "approve":
        if is_blocked or is_protected_file or is_approval:
            import typer
            try:
                allowed = typer.confirm("Approval required for command. Allow execution?", default=False)
            except Exception:
                allowed = False
            if not allowed:
                console.print("[bold red]Denied:[/] User rejected execution.")
                log_entry = {
                    "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    "session_id": session_id,
                    "actor_type": actor_type,
                    "tool": "shell",
                    "action": "command_execute",
                    "command": redacted_command,
                    "cwd": str(Path.cwd().resolve()),
                    "exit_code": 1,
                    "duration_ms": 0,
                    "mode": "approve",
                    "decision": "denied",
                }
                try:
                    with open(log_file, "a", encoding="utf-8") as f:
                        f.write(json.dumps(log_entry) + "\n")
                except Exception:
                    pass
                raise SystemExit(1)
            decision = "approved"

    # Run the command
    start_time = time.perf_counter()
    exit_code = 0
    output_data = None

    try:
        if capture_output:
            res = subprocess.run(cmd_args, capture_output=True, text=True, check=False)
            exit_code = res.returncode
            if res.stdout:
                sys.stdout.write(res.stdout)
                sys.stdout.flush()
            if res.stderr:
                sys.stderr.write(res.stderr)
                sys.stderr.flush()
            output_data = f"STDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}"
        else:
            res = subprocess.run(cmd_args, check=False)
            exit_code = res.returncode
    except FileNotFoundError:
        console.print(
            f"[bold red]Error:[/] Command executable '{cmd_args[0]}' not found."
        )
        exit_code = 127
        output_data = f"Command '{cmd_args[0]}' not found."
    except Exception as e:
        console.print(f"[bold red]Error:[/] Execution failed: {e}")
        exit_code = 1
        output_data = str(e)

    duration_ms = int((time.perf_counter() - start_time) * 1000)

    # Store Log
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "session_id": session_id,
        "actor_type": actor_type,
        "tool": "shell",
        "action": "command_execute",
        "command": redacted_command,
        "cwd": str(Path.cwd().resolve()),
        "exit_code": exit_code,
        "duration_ms": duration_ms,
        "mode": mode,
        "decision": decision,
    }
    if capture_output and output_data is not None:
        # Avoid storing secrets from captured output via standard redact
        redacted_output = re.sub(
            r'(?i)(api_key|apikey|secret_key|private_key|token|auth_token|password|pass)\s*[=:]\s*["\']?[a-zA-Z0-9_\-\.]{8,}["\']?',
            r"\1=REDACTED",
            output_data,
        )
        log_entry["output"] = redacted_output

    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception as e:
        console.print(f"[dim yellow]Warning: Failed to write guard log: {e}[/]")

    raise SystemExit(exit_code)


def run_guard_status_metrics(console: Console) -> None:
    from niyam.core.config import find_niyam_root, load_niyam_config
    import json

    root = find_niyam_root()
    if root is None:
        root = Path.cwd()

    config = None
    try:
        config = load_niyam_config(root)
    except Exception:
        pass

    enabled = config.guard.enabled if config else False
    careful = config.guard.careful if config else False
    frozen = config.guard.frozen_paths if config else []

    log_file = root / ".niyam" / "logs" / "guard-actions.jsonl"
    total_logs = 0
    success_logs = 0
    failed_logs = 0

    if log_file.exists():
        try:
            with open(log_file, encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        try:
                            data = json.loads(line)
                            total_logs += 1
                            if data.get("exit_code") == 0:
                                success_logs += 1
                            else:
                                failed_logs += 1
                        except Exception:
                            pass
        except Exception:
            pass

    from rich.panel import Panel

    status_content = (
        f"Guard Mode: {'[bold green]Enabled[/]' if enabled else '[yellow]Disabled[/]'}\n"
        f"Careful Mode: {'[bold green]Enabled[/]' if careful else '[yellow]Disabled[/]'}\n"
        f"Frozen Paths: {', '.join(frozen) if frozen else 'None'}\n\n"
        f"[bold]Observation Metrics (Observe Mode):[/]\n"
        f"  Total Actions Logged: [bold cyan]{total_logs}[/]\n"
        f"  Successful Actions (Exit Code 0): [bold green]{success_logs}[/]\n"
        f"  Failed Actions (Exit Code != 0): [bold red]{failed_logs}[/]"
    )
    console.print(
        Panel(
            status_content,
            title="[bold]Niyam Guard & Observation Status[/]",
            border_style="cyan" if enabled else "yellow",
        )
    )


def run_guard_show_logs(limit: int, console: Console) -> None:
    from niyam.core.config import find_niyam_root
    from rich.table import Table
    import json

    root = find_niyam_root()
    if root is None:
        root = Path.cwd()

    log_file = root / ".niyam" / "logs" / "guard-actions.jsonl"
    if not log_file.exists():
        console.print("[yellow]No guard logs found.[/]")
        return

    entries = []
    try:
        with open(log_file, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        entries.append(json.loads(line))
                    except Exception:
                        pass
    except Exception as e:
        console.print(f"[bold red]Error reading logs:[/] {e}")
        return

    # Take the last limit elements
    show_entries = entries[-limit:]

    table = Table(title=f"Recent Observed Actions (Showing last {len(show_entries)})")
    table.add_column("Timestamp", style="dim")
    table.add_column("Actor", style="magenta")
    table.add_column("Command", style="cyan")
    table.add_column("Duration (ms)", justify="right")
    table.add_column("Exit Code", justify="center")

    for entry in show_entries:
        ts = entry.get("timestamp", "")
        if len(ts) > 19:
            ts = ts[:19].replace("T", " ")
        actor = entry.get("actor_type", "unknown")
        cmd = entry.get("command", "")
        if len(cmd) > 50:
            cmd = cmd[:47] + "..."
        dur = str(entry.get("duration_ms", 0))
        code = str(entry.get("exit_code", 0))
        code_style = "[bold green]0[/]" if code == "0" else f"[bold red]{code}[/]"

        table.add_row(ts, actor, cmd, dur, code_style)

    console.print(table)
