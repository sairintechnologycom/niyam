"""Niyam init — create a governed AI-development workspace."""

from __future__ import annotations

import shutil
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape
from rich.console import Console
from rich.panel import Panel
from rich.tree import Tree

from niyam.core.config import (
    NIYAM_DIR,
    NiyamConfig,
    get_niyam_dir,
    save_niyam_config,
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
    if "/" in profile or "\\" in profile or ".." in profile:
        raise ValueError("Invalid profile name (path traversal not allowed)")
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
    niyam_dir = repo_root / NIYAM_DIR
    profile_dir = _get_profile_dir(profile)
    files: list[tuple[Path, str | None]] = []

    # Walk the profile directory and collect all files
    for source_path in sorted(profile_dir.rglob("*")):
        if source_path.is_dir():
            rel = source_path.relative_to(profile_dir)
            target = niyam_dir / rel
            files.append((target, None))
        else:
            rel = source_path.relative_to(profile_dir)
            target = niyam_dir / rel
            content = source_path.read_text(encoding="utf-8")
            files.append((target, content))

    # Collect the governance suite planning documents to create in the repo root
    init_docs_dir = TEMPLATES_DIR / "init_docs"
    if init_docs_dir.exists():
        for doc_path in sorted(init_docs_dir.glob("*.md")):
            target = repo_root / doc_path.name
            content = doc_path.read_text(encoding="utf-8")
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
    """Execute the niyam init command."""
    repo_root = Path.cwd()
    niyam_dir = get_niyam_dir(repo_root)

    # Check existing
    if niyam_dir.exists() and not force:
        console.print(
            Panel(
                f"[blue]Info:[/] .niyam/ already exists in {repo_root}\n\n"
                "No files were changed. Use [bold]--force[/] to overwrite.",
                title="[bold blue]Already initialized[/]",
                border_style="blue",
            )
        )
        return

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
        console.print(
            f"\n[dim]{len([f for f in files if f[1] is not None])} files would be created.[/]"
        )
        return

    # Remove existing if --force
    if niyam_dir.exists() and force:
        shutil.rmtree(niyam_dir)
        console.print("[yellow]♻ Removed existing .niyam/[/]")

    # Create directories first
    niyam_dir.mkdir(parents=True, exist_ok=True)
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

    # Write niyam.yaml from config
    project_name = repo_root.name
    runtimes_list = [runtime] if runtime else []

    config = NiyamConfig(
        version="0.1.0",
        project_name=project_name,
        profile=profile,
        runtimes=runtimes_list,
    )
    save_niyam_config(config, repo_root)

    # Create required directories
    for subdir in ["tasks", "runs", "templates", "worktrees", "evidence"]:
        (niyam_dir / subdir).mkdir(exist_ok=True)

    # Write default mission templates
    (niyam_dir / "templates" / "missions").mkdir(parents=True, exist_ok=True)
    from niyam.mission.planner import DEFAULT_TEMPLATES

    for name, template_data in DEFAULT_TEMPLATES.items():
        template_file = niyam_dir / "templates" / "missions" / f"{name}.yaml"
        with open(template_file, "w", encoding="utf-8") as f:
            yaml.dump(template_data, f, default_flow_style=False, sort_keys=False)

    # If runtime specified, trigger sync
    if runtime:
        from niyam.core.sync import run_sync

        run_sync(runtime=runtime, console=console)

    # Done
    console.print(
        Panel(
            f"[bold green]✓[/] Created Niyam workspace with [cyan]{profile}[/] profile\n"
            f"  [dim]•[/] {created_count} files written to .niyam/\n"
            + (
                f"  [dim]•[/] Runtime [cyan]{runtime}[/] configured\n"
                if runtime
                else ""
            )
            + f"  [dim]•[/] Project: [bold]{project_name}[/]\n"
            "\n"
            "[dim]Next steps:[/]\n"
            '  niyam context add -t prd "..."  [dim]# provide your PRD or project description[/]\n'
            "  niyam context refresh           [dim]# detect your stack[/]\n"
            "  niyam policy validate           [dim]# check policies[/]\n"
            "  niyam doctor                    [dim]# verify setup[/]\n"
            "  niyam sync                      [dim]# project rules into your AI runtime[/]\n"
            "\n"
            "[dim]How to use Niyam:[/] "
            "[link=https://github.com/sairintechnologycom/niyam/blob/main/docs/user-guide.md]"
            "User Guide[/link] "
            "(setup, day-to-day commands, missions, scan/guard, evidence).\n"
            "Then open your agent and use [bold]/implement[/], [bold]/review[/], [bold]/ship[/].",
            title="[bold green]Niyam Initialized[/]",
            border_style="green",
        )
    )
