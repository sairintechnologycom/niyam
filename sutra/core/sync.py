"""Sutra sync — project runtime files from .sutra/ source of truth."""

from __future__ import annotations

from pathlib import Path

import yaml
from rich.console import Console

from sutra.core.config import (
    find_sutra_root,
    load_sutra_config,
    save_sutra_config,
)


def _ensure_sutra_root(console: Console) -> Path:
    """Find and return the sutra root, or exit."""
    root = find_sutra_root()
    if root is None:
        console.print(
            "[bold red]Error:[/] Not a Sutra workspace. Run [bold]sutra init[/] first."
        )
        raise SystemExit(1)
    return root


def run_sync(
    runtime: str | None,
    console: Console,
    verbose: bool = False,
    dry_run: bool = False,
) -> None:
    """Sync .sutra/ to configured runtimes."""
    repo_root = _ensure_sutra_root(console)
    config = load_sutra_config(repo_root)

    runtimes_to_sync = [runtime] if runtime else config.runtimes

    if not runtimes_to_sync:
        console.print(
            "[yellow]No runtimes configured. Use [bold]sutra runtime add <runtime>[/] first.[/]"
        )
        return

    for rt in runtimes_to_sync:
        if rt == "claude":
            from sutra.runtimes.claude import ClaudeAdapter

            adapter = ClaudeAdapter(repo_root, verbose=verbose, dry_run=dry_run)
            adapter.sync(console)
        elif rt == "codex":
            from sutra.runtimes.codex import CodexAdapter

            adapter = CodexAdapter(repo_root, verbose=verbose, dry_run=dry_run)
            adapter.sync(console)
        elif rt == "gemini":
            from sutra.runtimes.gemini import GeminiAdapter

            adapter = GeminiAdapter(repo_root, verbose=verbose, dry_run=dry_run)
            adapter.sync(console)
        else:
            console.print(f"[yellow]Unknown runtime: {rt}[/]")


def run_runtime_add(
    runtime: str,
    console: Console,
    dry_run: bool = False,
) -> None:
    """Add a runtime to the workspace and sync it."""
    repo_root = _ensure_sutra_root(console)
    config = load_sutra_config(repo_root)

    if runtime in config.runtimes:
        console.print(f"[yellow]Runtime [cyan]{runtime}[/] is already configured.[/]")
        return

    if dry_run:
        console.print(
            f"[yellow]Dry Run: Would add runtime [bold cyan]{runtime}[/] to sutra.yaml and runtimes.yaml[/]"
        )
        # Preview sync
        run_sync(runtime=runtime, console=console, verbose=True, dry_run=True)
        return

    # Add runtime to config
    config.runtimes.append(runtime)
    save_sutra_config(config, repo_root)

    # Update runtimes.yaml
    runtimes_yaml_path = repo_root / ".sutra" / "runtimes.yaml"
    runtimes_data: dict = {}
    if runtimes_yaml_path.exists():
        with open(runtimes_yaml_path) as f:
            runtimes_data = yaml.safe_load(f) or {}

    if runtime == "claude":
        runtimes_data["claude"] = {
            "generate_claude_md": True,
            "generate_hooks": True,
            "generate_settings": True,
        }
    elif runtime == "codex":
        runtimes_data["codex"] = {
            "generate_agents_md": True,
        }
    elif runtime == "gemini":
        runtimes_data["gemini"] = {
            "generate_gemini_md": True,
            "generate_style_md": True,
        }

    with open(runtimes_yaml_path, "w") as f:
        yaml.dump(runtimes_data, f, default_flow_style=False, sort_keys=False)

    console.print(f"[green]✓[/] Added runtime [bold cyan]{runtime}[/]")

    # Sync the new runtime
    run_sync(runtime=runtime, console=console)
