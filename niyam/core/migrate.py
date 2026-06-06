import shutil
from pathlib import Path
from rich.console import Console


def run_sutra_migration(
    force: bool = False, move: bool = False, console: Console = None
) -> None:
    """Migrate legacy .sutra/ workspace configuration to .niyam/."""
    con = console or Console()
    cwd = Path.cwd()

    # 1. Find .sutra/ directory
    # Walk up to find a directory containing .sutra/
    sutra_dir = None
    for parent in [cwd, *cwd.parents]:
        if (parent / ".sutra").is_dir():
            sutra_dir = parent / ".sutra"
            break

    if not sutra_dir:
        con.print(
            "[bold red]Error:[/] No legacy .sutra/ directory found in this repository or its parent directories."
        )
        raise SystemExit(1)

    repo_root = sutra_dir.parent
    niyam_dir = repo_root / ".niyam"

    # 2. Check if .niyam/ already exists
    if niyam_dir.exists():
        if not force:
            con.print(
                f"[bold red]Error:[/] Destination directory {niyam_dir} already exists."
            )
            con.print("Use [bold]--force[/] to overwrite it.")
            raise SystemExit(1)
        else:
            con.print(f"[yellow]Overwriting existing {niyam_dir}...[/]")
            if niyam_dir.is_dir():
                shutil.rmtree(niyam_dir)
            else:
                niyam_dir.unlink()

    # 3. Perform copy or move
    action_str = "Moving" if move else "Copying"
    con.print(f"[cyan]{action_str} {sutra_dir} to {niyam_dir}...[/]")

    try:
        shutil.copytree(sutra_dir, niyam_dir, dirs_exist_ok=True)
    except Exception as e:
        con.print(f"[bold red]Migration failed during file copy:[/] {e}")
        raise SystemExit(1)

    # 4. Rename sutra.yaml to niyam.yaml
    old_config = niyam_dir / "sutra.yaml"
    new_config = niyam_dir / "niyam.yaml"
    if old_config.exists():
        old_config.rename(new_config)
        con.print("[green]Renamed sutra.yaml to niyam.yaml[/]")

    # 5. Recursively rename nested files containing "sutra" and update internal references
    con.print("[cyan]Updating file contents and names inside .niyam/...[/]")

    replacements = [
        ("sutra-cli", "niyam"),
        ("sutra_cli", "niyam"),
        ("SutraForge", "NiyamForge"),
        ("sutraforge", "niyamforge"),
        (".sutra", ".niyam"),
        ("sutra.yaml", "niyam.yaml"),
        ("SUTRA", "NIYAM"),
        ("Sutra", "Niyam"),
        ("sutra", "niyam"),
    ]

    def replace_text(text: str) -> str:
        for old, new in replacements:
            text = text.replace(old, new)
        return text

    # Process all files in the new .niyam/ directory
    all_files = list(niyam_dir.rglob("*"))
    # We sort by depth descending so that we rename files before renaming their parent directories
    all_files.sort(key=lambda p: len(p.parts), reverse=True)

    for path in all_files:
        if path.is_file():
            # Update file contents
            try:
                content = path.read_text(encoding="utf-8", errors="ignore")
                updated = replace_text(content)
                if updated != content:
                    path.write_text(updated, encoding="utf-8")
            except Exception as e:
                con.print(
                    f"[yellow]Warning:[/] Could not update contents of {path.name}: {e}"
                )

            # Rename file itself if it has "sutra" in name
            if "sutra" in path.name.lower():
                new_name = replace_text(path.name)
                new_path = path.parent / new_name
                path.rename(new_path)

        elif path.is_dir():
            # Rename directory itself if it has "sutra" in name
            if "sutra" in path.name.lower():
                new_name = replace_text(path.name)
                new_path = path.parent / new_name
                path.rename(new_path)

    # 6. If move was requested, remove the old .sutra directory
    if move:
        try:
            shutil.rmtree(sutra_dir)
            con.print("[green]Removed legacy .sutra/ directory.[/]")
        except Exception as e:
            con.print(
                f"[yellow]Warning:[/] Could not remove old .sutra/ directory: {e}"
            )

    # 7. Print completion message
    if move:
        con.print("\n[bold green]✓ Migration complete successfully![/]")
    else:
        con.print(
            "\n[bold green]✓ Migration complete. Review .niyam/, then remove .sutra/ manually when ready.[/]"
        )
