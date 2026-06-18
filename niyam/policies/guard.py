"""Niyam guard — safety guardrails for AI-assisted development."""

import json
import os
import re
import selectors
import ssl
import subprocess
import time
import uuid
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

import yaml
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from niyam.core.config import (
    find_niyam_root,
    load_niyam_config,
    save_niyam_config,
)
from niyam.governance.common.redaction import redact_text


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


def _install_git_hooks(root: Path, console: Console) -> None:
    """Install Niyam git hooks into .git/hooks/."""
    git_dir = root / ".git"
    if not git_dir.exists():
        return

    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)

    pre_commit_path = hooks_dir / "pre_commit"
    hook_content = "#!/bin/sh\nniyam guard verify-commit\n"

    try:
        pre_commit_path.write_text(hook_content, encoding="utf-8")
        pre_commit_path.chmod(0o755)
        console.print("[dim]  ↳ Git pre-commit hook installed[/]")
    except Exception as e:
        console.print(f"[dim yellow]Warning: Failed to install git hook: {e}[/]")


def _uninstall_git_hooks(root: Path, console: Console) -> None:
    """Remove Niyam git hooks from .git/hooks/."""
    git_dir = root / ".git"
    if not git_dir.exists():
        return

    pre_commit_path = git_dir / "hooks" / "pre_commit"
    if pre_commit_path.exists():
        try:
            # Only remove if it's our hook
            if "niyam guard verify-commit" in pre_commit_path.read_text():
                pre_commit_path.unlink()
                console.print("[dim]  ↳ Git pre-commit hook removed[/]")
        except Exception:
            pass


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
    _install_git_hooks(root, console)

    console.print(
        Panel(
            "[bold green]✓[/] Guard mode [bold]enabled[/]\n"
            "  [dim]•[/] Denied commands will be blocked\n"
            "  [dim]•[/] Careful mode active (destructive command warnings)\n"
            "  [dim]•[/] Git pre-commit hooks installed\n"
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
    _uninstall_git_hooks(root, console)

    console.print(
        "[yellow]⚠ Guard mode [bold]disabled[/]. AI agents can execute freely.[/]"
    )


def run_guard_verify_commit(console: Console) -> None:
    """Check staged files against frozen paths before commit."""
    root = find_niyam_root()
    if root is None:
        return

    config = load_niyam_config(root)
    if not config.guard.enabled or not config.guard.frozen_paths:
        return

    # Get staged files
    try:
        res = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
        )
        staged_files = res.stdout.splitlines()
    except Exception as e:
        console.print(f"[bold red]Error:[/] Failed to get staged files: {e}")
        raise SystemExit(1)

    blocked_files = []
    for f in staged_files:
        for frozen in config.guard.frozen_paths:
            if f.startswith(frozen):
                blocked_files.append(f)
                break

    if blocked_files:
        console.print("[bold red]🛑 Commit Blocked by Niyam Guard[/]")
        console.print(
            f"The following staged files are inside [bold]frozen paths[/]:"
        )
        for f in blocked_files:
            console.print(f"  [red]• {f}[/]")
        console.print(
            "\n[dim]To commit these changes, run [bold]niyam guard disable[/] or remove them from frozen_paths.[/]"
        )
        raise SystemExit(1)


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
    """Fetch policy YAML from a remote URL."""
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


def _match_command_pattern(cmd_args: list[str], pattern: str) -> bool:
    """Matches a command pattern against executed command arguments."""
    if not cmd_args:
        return False

    pattern_tokens = pattern.strip().split()
    if not pattern_tokens:
        return False

    # 1. Main executable matching (token-aware)
    exe = cmd_args[0]
    exe_basename = os.path.basename(exe)
    first_token = pattern_tokens[0]

    if exe_basename == first_token or exe == first_token:
        # Check if the remaining pattern tokens are present in command arguments in order
        rem_pattern = pattern_tokens[1:]
        rem_args = cmd_args[1:]

        idx = 0
        for token in rem_pattern:
            try:
                idx = rem_args.index(token, idx)
                idx += 1
            except ValueError:
                return False
        return True

    # 2. SQL / Query substring matching (excluding safe commands)
    safe_executables = {"echo", "printf", "cat", "less", "more", "grep", "git"}
    if exe_basename in safe_executables:
        return False

    command_str_normalized = " ".join(cmd_args)
    pattern_normalized = " ".join(pattern_tokens)

    # Word-boundary check case-insensitively
    pattern_regex = r"\b" + re.escape(pattern_normalized) + r"\b"
    return bool(re.search(pattern_regex, command_str_normalized, re.IGNORECASE))


def _is_protected_file_match(cmd_args: list[str], protected_files: list[str], root: Path | None = None) -> bool:
    """Determines if any file path operand in the command points to a protected file or directory."""
    if not cmd_args or not protected_files:
        return False
        
    root_path = root or Path.cwd()

    for arg in cmd_args[1:]:
        # Skip options/flags
        if arg.startswith("-"):
            continue

        try:
            # Resolve the argument path relative to the root
            arg_resolved = (root_path / arg).resolve()
        except Exception:
            continue

        for f in protected_files:
            try:
                # Resolve the protected file path relative to the root
                f_resolved = (root_path / f).resolve()
                
                # Check if the argument is the protected file itself or inside it
                if arg_resolved == f_resolved or arg_resolved.is_relative_to(f_resolved):
                    return True
            except Exception:
                continue
    return False


def _prompt_confirm(console: Console, prompt: str) -> bool:
    """Prompt user for confirmation."""
    import typer

    # Check if we are running in tests
    if os.environ.get("NIYAM_TEST_NON_INTERACTIVE") == "1":
        is_interactive = False
    elif (
        os.environ.get("NIYAM_TEST") == "1"
        or os.environ.get("PYTEST_CURRENT_TEST") is not None
    ):
        is_interactive = True
    else:
        import sys
        is_interactive = sys.stdin.isatty() and not os.environ.get("CI")

    if not is_interactive:
        console.print(
            "[bold red]Denied:[/] Non-interactive/CI environment detected. Auto-denying approval request."
        )
        return False

    try:
        return typer.confirm(prompt, default=False)
    except Exception:
        return False


def run_guard_run(
    cmd_args: list[str],
    capture_output: bool,
    console: Console,
    dry_run: bool = False,
    mode_override: str | None = None,
) -> None:
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
        git_branch = None
        try:
            res = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=root,
                capture_output=True,
                text=True,
                check=False,
            )
            if res.returncode == 0:
                git_branch = res.stdout.strip()
        except Exception:
            pass
        if git_branch and git_branch != "HEAD":
            session_id = f"{git_branch}-{uuid.uuid4()}"
        else:
            session_id = str(uuid.uuid4())

    actor_type = os.environ.get("NIYAM_ACTOR_TYPE")
    if not actor_type:
        import sys
        if sys.stdin.isatty():
            actor_type = "human"
        elif (
            os.environ.get("NIYAM_TEST") == "1"
            or os.environ.get("PYTEST_CURRENT_TEST") is not None
        ):
            actor_type = "agent"
        else:
            actor_type = "unknown"
    else:
        actor_type = actor_type.strip().lower()
        if actor_type not in ("human", "agent", "unknown"):
            actor_type = "unknown"

    # Load config
    mode = "observe"
    blocked_commands = []
    warn_commands = []
    protected_files = []
    approval_required = []

    try:
        config = load_niyam_config(root)
        if config and config.guard and config.guard.enabled:
            mode = "block"

        if config and config.governance and config.governance.guard:
            mode = config.governance.guard.mode
            blocked_commands = config.governance.guard.blocked_commands
            protected_files = config.governance.guard.protected_files
            approval_required = config.governance.guard.approval_required
        else:
            # Fallback to local files
            from niyam.core.security import safe_load_yaml
            
            cmd_policy_path = root / ".niyam" / "policies" / "commands.yaml"
            if cmd_policy_path.exists():
                cmd_data = safe_load_yaml(cmd_policy_path) or {}
                blocked_commands = cmd_data.get("deny", [])
                warn_commands = cmd_data.get("warn", [])
            
            app_policy_path = root / ".niyam" / "policies" / "approvals.yaml"
            if app_policy_path.exists():
                app_data = safe_load_yaml(app_policy_path) or {}
                approval_required = app_data.get("approval_required_for", [])
            
            sec_policy_path = root / ".niyam" / "policies" / "security.yaml"
            if sec_policy_path.exists():
                sec_data = safe_load_yaml(sec_policy_path) or {}
                protected_files = sec_data.get("deny_write_patterns", [])
        
        # Merge frozen paths from legacy guard config
        if config and config.guard and config.guard.frozen_paths:
            # Avoid duplicates
            for fp in config.guard.frozen_paths:
                if fp not in protected_files:
                    protected_files.append(fp)
    except Exception:
        pass

    if mode_override:
        mode = mode_override

    # Validate mode
    valid_modes = {"observe", "block", "warn", "approve", "approval"}
    if mode not in valid_modes:
        console.print(
            f"[bold red]Error:[/] Invalid guard mode '{mode}'. Choose from: observe, block, warn, approve, approval."
        )
        raise SystemExit(1)

    command_str = " ".join(cmd_args)
    redacted_command = redact_text(command_str)

    # Policy evaluation
    matched_rule = None
    reason = None
    policy_decision = "allow"

    from niyam.core.policy import is_exception_active

    for pattern in blocked_commands:
        if _match_command_pattern(cmd_args, pattern):
            # Check for active exception (Risk Acceptance)
            exception = is_exception_active(pattern, root)
            if exception:
                matched_rule = f"blocked_command:{pattern}"
                reason = f"Command matches blocked pattern '{pattern}' but has active Risk Acceptance: {exception.id} ({exception.reason})"
                policy_decision = "allow"
                break
            
            matched_rule = f"blocked_command:{pattern}"
            reason = f"Command matches blocked command pattern: '{pattern}'"
            policy_decision = "block"
            break

    if not matched_rule:
        for pattern in protected_files:
            if _is_protected_file_match(cmd_args, [pattern], root=root):
                # Check for active exception (Risk Acceptance)
                exception = is_exception_active(pattern, root)
                if exception:
                    matched_rule = f"protected_file:{pattern}"
                    reason = f"Command references protected file '{pattern}' but has active Risk Acceptance: {exception.id} ({exception.reason})"
                    policy_decision = "allow"
                    break

                matched_rule = f"protected_file:{pattern}"
                reason = f"Command references protected file: '{pattern}'"
                policy_decision = "block"
                break

    if not matched_rule:
        for pattern in approval_required:
            if _match_command_pattern(cmd_args, pattern):
                # Check for active exception (Risk Acceptance)
                exception = is_exception_active(pattern, root)
                if exception:
                    matched_rule = f"approval_required:{pattern}"
                    reason = f"Command requires approval pattern '{pattern}' but has active Risk Acceptance: {exception.id} ({exception.reason})"
                    policy_decision = "allow"
                    break

                matched_rule = f"approval_required:{pattern}"
                reason = f"Command requires approval pattern: '{pattern}'"
                policy_decision = "approval_required"
                break

    # MCP/Tool Registry Check
    if not matched_rule:
        try:
            from niyam.core.mcp import load_mcp_registry
            registry = load_mcp_registry(root)
            
            exe = cmd_args[0]
            exe_basename = os.path.basename(exe)
            
            for tool_name, tool in registry.tools.items():
                matches = False
                if tool_name == exe_basename or tool_name == exe:
                    matches = True
                elif tool.command_or_url:
                    if command_str.startswith(tool.command_or_url):
                        matches = True
                
                if matches:
                    if not tool.approved:
                        if tool.risk_level in ("high", "critical"):
                            matched_rule = f"mcp_unapproved:{tool_name}"
                            reason = f"Unapproved {tool.risk_level} risk tool from registry: '{tool_name}'"
                            policy_decision = "block"
                            break
                        elif tool.risk_level == "medium":
                            matched_rule = f"mcp_unapproved:{tool_name}"
                            reason = f"Unapproved medium risk tool from registry: '{tool_name}'"
                            policy_decision = "approval_required"
                            break
        except Exception:
            pass

    if not matched_rule:
        for pattern in warn_commands:
            if _match_command_pattern(cmd_args, pattern):
                matched_rule = f"warn_command:{pattern}"
                reason = f"Command matches warn command pattern: '{pattern}'"
                policy_decision = "warn"
                break

    def write_log(
        exit_code: int,
        duration_ms: int,
        final_decision: str,
        final_policy_decision: str,
        output_data: str | None = None,
    ) -> None:
        log_entry = {
            "schema_version": "1.0.0",
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
            "policy_decision": final_policy_decision,
            "decision": final_decision,
            "matched_rule": matched_rule,
            "reason": reason,
        }
        if output_data is not None:
            log_entry["output"] = redact_text(output_data)
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            console.print(f"[dim yellow]Warning: Failed to write guard log: {e}[/]")

    if dry_run:
        table = Table(
            title="Niyam Guard Dry Run",
            header_style="bold yellow",
            show_lines=False,
        )
        table.add_column("Command", style="cyan")
        table.add_column("Mode")
        table.add_column("Policy Decision")
        table.add_column("Matched Policy")
        table.add_column("Actionable Remediation")

        remediation = "No remediation needed."
        dry_run_decision = "allowed"
        if policy_decision in ("block", "approval_required"):
            dry_run_decision = "would_fail"
            remediation = (
                "Change the command, update the relevant policy, or request human "
                "approval before running without --dry-run."
            )
        elif policy_decision == "warn":
            dry_run_decision = "would_warn"
            remediation = "Review the command risk before running without --dry-run."

        table.add_row(
            redacted_command,
            mode,
            policy_decision,
            matched_rule or "-",
            remediation,
        )
        if dry_run_decision == "allowed":
            console.print("[bold green]✓[/] Guard dry run passed. Command would be allowed.")
        else:
            console.print(table)

        write_log(0, 0, dry_run_decision, policy_decision)
        raise SystemExit(0)

    # Enforcement
    if policy_decision == "block" and mode == "block":
        console.print("[bold red]Blocked:[/] Command violates governance policy.")
        write_log(1, 0, "blocked", "block")
        raise SystemExit(1)

    elif (policy_decision == "block" and mode in ("approve", "approval")) or (
        policy_decision == "approval_required"
        and mode in ("block", "approve", "approval")
    ):
        allowed = _prompt_confirm(
            console, "Approval required for command. Allow execution?"
        )
        if not allowed:
            console.print("[bold red]Denied:[/] User rejected execution.")
            write_log(1, 0, "denied", "approval_required")
            raise SystemExit(1)
        decision_label = "approved"
        policy_decision_label = "approval_required"

    elif (policy_decision in ("block", "approval_required") and mode == "warn") or (
        policy_decision == "warn"
    ):
        console.print(f"[bold yellow]Warning:[/] Command is flagged as dangerous. {reason}")
        decision_label = "warned"
        policy_decision_label = "warn"

    else:
        decision_label = "allowed"
        policy_decision_label = policy_decision

    # Run the command
    start_time = time.perf_counter()
    exit_code = 0
    captured_stdout = []
    captured_stderr = []

    try:
        import sys
        # Use Popen for streaming
        process = subprocess.Popen(
            cmd_args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

        sel = selectors.DefaultSelector()
        sel.register(process.stdout, selectors.EVENT_READ)
        sel.register(process.stderr, selectors.EVENT_READ)

        while process.poll() is None or sel.get_map():
            events = sel.select(timeout=0.1)
            for key, _ in events:
                line = key.fileobj.readline()
                if not line:
                    sel.unregister(key.fileobj)
                    continue

                redacted_line = redact_text(line)
                if key.fileobj is process.stdout:
                    sys.stdout.write(redacted_line)
                    sys.stdout.flush()
                    if capture_output:
                        captured_stdout.append(redacted_line)
                else:
                    sys.stderr.write(redacted_line)
                    sys.stderr.flush()
                    if capture_output:
                        captured_stderr.append(redacted_line)

            if process.poll() is not None and not events:
                break

        exit_code = process.returncode
        output_data = None
        if capture_output:
            output_data = f"STDOUT:\n{''.join(captured_stdout)}\nSTDERR:\n{''.join(captured_stderr)}"

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
    write_log(
        exit_code, duration_ms, decision_label, policy_decision_label, output_data
    )
    raise SystemExit(exit_code)


def run_guard_status_metrics(console: Console) -> None:
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
