"""Sutra guard — safety guardrails for AI-assisted development."""

from __future__ import annotations

from pathlib import Path

import yaml
from rich.console import Console
from rich.panel import Panel

from sutra.core.config import (
    find_sutra_root,
    load_sutra_config,
    save_sutra_config,
)


def _ensure_root(console: Console) -> Path:
    """Find sutra root or exit."""
    root = find_sutra_root()
    if root is None:
        console.print("[bold red]Error:[/] Not a Sutra workspace. Run [bold]sutra init[/] first.")
        raise SystemExit(1)
    return root


def _resync_hooks(root: Path, console: Console) -> None:
    """Re-sync Claude hooks after guard state change."""
    config = load_sutra_config(root)
    if "claude" in config.runtimes:
        from sutra.runtimes.claude import ClaudeAdapter

        adapter = ClaudeAdapter(root)
        adapter._generate_hooks(console)
        console.print("[dim]  ↳ Claude hooks regenerated[/]")


def run_guard_enable(console: Console) -> None:
    """Enable all configured guardrails."""
    root = _ensure_root(console)
    config = load_sutra_config(root)

    config.guard.enabled = True
    config.guard.careful = True
    save_sutra_config(config, root)

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


def run_guard_disable(console: Console) -> None:
    """Disable all guardrails."""
    root = _ensure_root(console)
    config = load_sutra_config(root)

    config.guard.enabled = False
    config.guard.careful = False
    config.guard.frozen_paths = []
    save_sutra_config(config, root)

    _resync_hooks(root, console)

    console.print("[yellow]⚠ Guard mode [bold]disabled[/]. AI agents can execute freely.[/]")


def run_guard_careful(console: Console) -> None:
    """Enable destructive-command warnings."""
    root = _ensure_root(console)
    config = load_sutra_config(root)

    config.guard.enabled = True
    config.guard.careful = True
    save_sutra_config(config, root)

    # Add warn entries to commands.yaml if not present
    cmd_policy_path = root / ".sutra" / "policies" / "commands.yaml"
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


def run_guard_freeze(path: str, console: Console) -> None:
    """Restrict AI edits to a specific directory."""
    root = _ensure_root(console)
    config = load_sutra_config(root)

    from sutra.core.security import validate_path_within_repo

    try:
        resolved_path = validate_path_within_repo(path, root)
        # Store as a relative path to repo root, keeping it portable
        clean_path = str(resolved_path.relative_to(root.resolve()))
    except ValueError as e:
        console.print(f"[bold red]Error:[/] {e}")
        raise SystemExit(1)

    if clean_path not in config.guard.frozen_paths:
        config.guard.frozen_paths.append(clean_path)

    config.guard.enabled = True
    save_sutra_config(config, root)

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

        req = urllib.request.Request(
            target_url,
            headers={"User-Agent": "Sutra-CLI"}
        )
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
            from sutra.policies.validator import KNOWN_POLICY_FILES
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
    from sutra.core.config import find_sutra_root

    root = find_sutra_root()
    if not root:
        # No sutra workspace, fall back to raw fetch
        return _fetch_remote_policy_raw(url, filename)

    cache_dir = root / ".sutra" / "cache"
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
                logging.getLogger("sutra.guard").warning(
                    "Remote policy fetch failed (%s). Using cached version.", e
                )
                return data
        raise e

    return None


def load_security_policy(root: Path) -> dict:
    """Load security policy from remote URL if configured, falling back to local file."""
    import logging

    logger = logging.getLogger("sutra.guard")

    try:
        config = load_sutra_config(root)
        remote_url = config.guard.remote_policy_url
    except Exception:
        remote_url = None

    if remote_url:
        try:
            remote_data = _fetch_remote_policy(remote_url, "security.yaml")
            if remote_data is not None:
                return remote_data
        except Exception as e:
            logger.warning("Failed to fetch remote security policy: %s. Falling back to local.", e)

    # Fallback to local
    local_path = root / ".sutra" / "policies" / "security.yaml"
    if local_path.exists():
        try:
            from sutra.core.security import safe_load_yaml
            return safe_load_yaml(local_path)
        except Exception:
            pass
    return {}


def load_commands_policy(root: Path) -> dict:
    """Load commands policy from remote URL if configured, falling back to local file."""
    import logging

    logger = logging.getLogger("sutra.guard")

    try:
        config = load_sutra_config(root)
        remote_url = config.guard.remote_policy_url
    except Exception:
        remote_url = None

    if remote_url:
        try:
            remote_data = _fetch_remote_policy(remote_url, "commands.yaml")
            if remote_data is not None:
                return remote_data
        except Exception as e:
            logger.warning("Failed to fetch remote commands policy: %s. Falling back to local.", e)

    # Fallback to local
    local_path = root / ".sutra" / "policies" / "commands.yaml"
    if local_path.exists():
        try:
            from sutra.core.security import safe_load_yaml
            return safe_load_yaml(local_path)
        except Exception:
            pass
    return {}
