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

    # Normalize path
    clean_path = path.rstrip("/")

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
