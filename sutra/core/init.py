"""Sutra init — create a governed AI-development workspace."""

from __future__ import annotations

import shutil
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape
from rich.console import Console
from rich.panel import Panel
from rich.tree import Tree

from sutra.core.config import (
    SUTRA_DIR,
    SutraConfig,
    get_sutra_dir,
    save_sutra_config,
)

# ── Template directory ─────────────────────────────────────────────────

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


def _get_jinja_env() -> Environment:
    """Create Jinja2 environment for template rendering."""
    return Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape([]),
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )


def _get_profile_dir(profile: str) -> Path:
    """Get the profile template directory."""
    profile_dir = TEMPLATES_DIR / "profiles" / profile
    if not profile_dir.exists():
        raise ValueError(
            f"Unknown profile: '{profile}'. "
            f"Available: {', '.join(p.name for p in (TEMPLATES_DIR / 'profiles').iterdir() if p.is_dir())}"
        )
    return profile_dir


def _collect_files_to_create(
    profile: str,
    runtime: str | None,
    repo_root: Path,
) -> list[tuple[Path, str | None]]:
    """Collect all files that will be created.

    Returns list of (target_path, source_content_or_none).
    None means the file is a directory to create.
    """
    sutra_dir = repo_root / SUTRA_DIR
    profile_dir = _get_profile_dir(profile)
    files: list[tuple[Path, str | None]] = []

    # Walk the profile directory and collect all files
    for source_path in sorted(profile_dir.rglob("*")):
        if source_path.is_dir():
            rel = source_path.relative_to(profile_dir)
            target = sutra_dir / rel
            files.append((target, None))
        else:
            rel = source_path.relative_to(profile_dir)
            target = sutra_dir / rel
            content = source_path.read_text(encoding="utf-8")
            files.append((target, content))

    return files


def _build_file_tree(files: list[tuple[Path, str | None]], repo_root: Path) -> Tree:
    """Build a Rich tree showing files to be created."""
    tree = Tree(f"[bold cyan]{repo_root.name}/[/]")
    seen_dirs: dict[str, Tree] = {}

    for target, content in files:
        rel = target.relative_to(repo_root)
        parts = rel.parts

        # Build path progressively
        current = tree
        for i, part in enumerate(parts):
            path_so_far = "/".join(parts[: i + 1])
            if i < len(parts) - 1:
                # Directory
                if path_so_far not in seen_dirs:
                    current = current.add(f"[bold blue]{part}/[/]")
                    seen_dirs[path_so_far] = current  # type: ignore[assignment]
                else:
                    current = seen_dirs[path_so_far]  # type: ignore[assignment]
            else:
                # File
                if content is None:
                    if path_so_far not in seen_dirs:
                        node = current.add(f"[bold blue]{part}/[/]")
                        seen_dirs[path_so_far] = node  # type: ignore[assignment]
                else:
                    current.add(f"[green]{part}[/]")

    return tree


def run_init(
    profile: str,
    runtime: str | None,
    dry_run: bool,
    force: bool,
    console: Console,
) -> None:
    """Execute the sutra init command."""
    repo_root = Path.cwd()
    sutra_dir = get_sutra_dir(repo_root)

    # Check existing
    if sutra_dir.exists() and not force:
        console.print(
            Panel(
                f"[yellow]⚠ .sutra/ already exists in {repo_root}[/]\n\n"
                "Use [bold]--force[/] to overwrite.",
                title="[bold yellow]Already initialized[/]",
                border_style="yellow",
            )
        )
        raise SystemExit(1)

    # Validate profile
    try:
        _get_profile_dir(profile)
    except ValueError as e:
        console.print(f"[bold red]Error:[/] {e}")
        raise SystemExit(1)

    # Collect files
    files = _collect_files_to_create(profile, runtime, repo_root)

    # Dry run — show what would happen
    if dry_run:
        console.print(
            Panel(
                "[dim]No files will be written.[/]",
                title="[bold cyan]Dry Run[/]",
                border_style="cyan",
            )
        )
        tree = _build_file_tree(files, repo_root)
        console.print(tree)
        console.print(f"\n[dim]{len([f for f in files if f[1] is not None])} files would be created.[/]")
        return

    # Remove existing if --force
    if sutra_dir.exists() and force:
        shutil.rmtree(sutra_dir)
        console.print("[yellow]♻ Removed existing .sutra/[/]")

    # Create directories first
    sutra_dir.mkdir(parents=True, exist_ok=True)
    for target, content in files:
        if content is None:
            target.mkdir(parents=True, exist_ok=True)

    # Write files
    created_count = 0
    for target, content in files:
        if content is not None:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            created_count += 1

    # Write sutra.yaml from config
    project_name = repo_root.name
    runtimes_list = [runtime] if runtime else []

    config = SutraConfig(
        version="0.1.0",
        project_name=project_name,
        profile=profile,
        runtimes=runtimes_list,
    )
    save_sutra_config(config, repo_root)

    # Create required directories
    for subdir in ["tasks", "runs", "templates", "worktrees", "evidence"]:
        (sutra_dir / subdir).mkdir(exist_ok=True)

    # If runtime specified, trigger sync
    if runtime:
        from sutra.core.sync import run_sync

        run_sync(runtime=runtime, console=console)

    # Done
    console.print(
        Panel(
            f"[bold green]✓[/] Created Sutra workspace with [cyan]{profile}[/] profile\n"
            f"  [dim]•[/] {created_count} files written to .sutra/\n"
            + (f"  [dim]•[/] Runtime [cyan]{runtime}[/] configured\n" if runtime else "")
            + f"  [dim]•[/] Project: [bold]{project_name}[/]\n"
            "\n"
            "[dim]Next steps:[/]\n"
            "  sutra context refresh   [dim]# detect your stack[/]\n"
            "  sutra policy validate   [dim]# check policies[/]\n"
            "  sutra doctor            [dim]# verify setup[/]",
            title="[bold green]Sutra Initialized[/]",
            border_style="green",
        )
    )
