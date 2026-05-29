"""Sutra memory manager — cross-session learning and project knowledge accumulation."""

from __future__ import annotations

from pathlib import Path
from rich.console import Console
from rich.panel import Panel

from sutra.core.config import get_sutra_dir

MEMORY_DIR = "memory"


def get_memory_dir(repo_root: Path) -> Path:
    """Get the memory directory path."""
    return get_sutra_dir(repo_root) / MEMORY_DIR


def get_memory_file(repo_root: Path, name: str) -> Path:
    """Get a specific memory file, supporting with or without .md extension."""
    from sutra.core.security import sanitize_filename

    # Strip .md first, sanitize the base, then append .md back
    if name.endswith(".md"):
        base_name = name[:-3]
    else:
        base_name = name

    sanitized_base = sanitize_filename(base_name)
    name = f"{sanitized_base}.md"

    mem_dir = get_memory_dir(repo_root)
    filepath = mem_dir / name
    if not filepath.exists():
        raise FileNotFoundError(
            f"Memory file '{name}' does not exist. "
            f"Available memories: {', '.join(f.stem for f in mem_dir.glob('*.md'))}"
        )
    return filepath


def run_memory_show(console: Console) -> None:
    """Display all memory files and their content."""
    from sutra.core.config import find_sutra_root
    from sutra.core.errors import SutraConfigError

    repo_root = find_sutra_root()
    if not repo_root:
        raise SutraConfigError("Not a Sutra workspace. Run 'sutra init' first.")
    mem_dir = get_memory_dir(repo_root)

    if not mem_dir.exists():
        console.print("[yellow]No memory directory found. Initialize workspace first.[/]")
        return

    files = sorted(mem_dir.glob("*.md"))
    if not files:
        console.print("[yellow]No memory files found.[/]")
        return

    for filepath in files:
        title = filepath.stem.replace("-", " ").title()
        content = filepath.read_text(encoding="utf-8")
        console.print(Panel(content, title=f"[bold cyan]{title}[/]", border_style="cyan"))


def run_memory_add(file: str, note: str, console: Console) -> None:
    """Append a note to a memory file."""
    from sutra.core.config import find_sutra_root
    from sutra.core.errors import SutraConfigError

    repo_root = find_sutra_root()
    if not repo_root:
        raise SutraConfigError("Not a Sutra workspace. Run 'sutra init' first.")
    try:
        filepath = get_memory_file(repo_root, file)
    except FileNotFoundError as e:
        console.print(f"[bold red]Error:[/] {e}")
        return

    # Check if we need a leading newline
    content = filepath.read_text(encoding="utf-8")
    suffix = "\n" if not content.endswith("\n") else ""
    
    # Append the note as a bullet point
    filepath.write_text(content + suffix + f"- {note}\n", encoding="utf-8")
    console.print(f"[bold green]✓[/] Added note to memory '[cyan]{filepath.name}[/]'.")


def run_memory_clear(file: str, console: Console) -> None:
    """Clear a memory file, resetting it to its title/headers."""
    from sutra.core.config import find_sutra_root
    from sutra.core.errors import SutraConfigError

    repo_root = find_sutra_root()
    if not repo_root:
        raise SutraConfigError("Not a Sutra workspace. Run 'sutra init' first.")
    try:
        filepath = get_memory_file(repo_root, file)
    except FileNotFoundError as e:
        console.print(f"[bold red]Error:[/] {e}")
        return

    # Read first line to preserve the title header
    content = filepath.read_text(encoding="utf-8")
    lines = content.split("\n")
    title_line = ""
    for line in lines:
        if line.startswith("#"):
            title_line = line
            break

    if not title_line:
        # Fallback to file name
        title_line = f"# {filepath.stem.replace('-', ' ').title()}"

    initial_content = f"{title_line}\n\n<!-- Cleared memory. Add new entries below. -->\n"
    filepath.write_text(initial_content, encoding="utf-8")
    console.print(f"[bold green]✓[/] Cleared memory '[cyan]{filepath.name}[/]'.")
