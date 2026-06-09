"""Niyam CLI memory commands."""

from __future__ import annotations

from typing import Annotated

import typer

from niyam.cli import console, memory_app


@memory_app.command("show")
def memory_show() -> None:
    """Display all memory files and their content."""
    from niyam.core.memory import run_memory_show

    run_memory_show(console=console)


@memory_app.command("add")
def memory_add(
    file: Annotated[
        str,
        typer.Argument(help="Memory file to append to (e.g. project-lessons)."),
    ],
    note: Annotated[str, typer.Argument(help="Note to append.")],
) -> None:
    """Append a note to a memory file."""
    from niyam.core.memory import run_memory_add
    from niyam.core.sync import run_sync

    run_memory_add(file=file, note=note, console=console)
    run_sync(runtime=None, console=console)


@memory_app.command("clear")
def memory_clear(
    file: Annotated[str, typer.Argument(help="Memory file to clear.")],
) -> None:
    """Clear a memory file, resetting it to its title/headers."""
    from niyam.core.memory import run_memory_clear
    from niyam.core.sync import run_sync

    run_memory_clear(file=file, console=console)
    run_sync(runtime=None, console=console)


@memory_app.command("init")
def memory_init() -> None:
    """Initialize the structured memory ledger store."""
    from niyam.core.config import find_niyam_root
    from niyam.core.errors import NiyamConfigError
    from niyam.core.memory import get_memory_dir
    from niyam.core.memory_ledger.local_store import LocalMemoryLedgerStore

    repo_root = find_niyam_root()
    if not repo_root:
        raise NiyamConfigError("Not a Niyam workspace. Run 'niyam init' first.")
    
    index_path = get_memory_dir(repo_root) / "index.jsonl"
    store = LocalMemoryLedgerStore(index_path)
    store.init_store()
    console.print("[bold green]✓[/] Memory ledger store initialized.")


@memory_app.command("list")
def memory_list() -> None:
    """List all records in the structured memory ledger."""
    from niyam.core.config import find_niyam_root
    from niyam.core.errors import NiyamConfigError
    from niyam.core.memory import get_memory_dir
    from niyam.core.memory_ledger.local_store import LocalMemoryLedgerStore

    repo_root = find_niyam_root()
    if not repo_root:
        raise NiyamConfigError("Not a Niyam workspace. Run 'niyam init' first.")
    
    index_path = get_memory_dir(repo_root) / "index.jsonl"
    store = LocalMemoryLedgerStore(index_path)
    records = store.list_records()
    
    if not records:
        console.print("[yellow]No memory records found in ledger.[/yellow]")
        return
        
    for r in records:
        console.print(f"[{r.id}] {r.type} (scope: {r.scope}, source: {r.source_kind}) - {r.created_at}")


@memory_app.command("validate")
def memory_validate() -> None:
    """Validate all records in the structured memory ledger."""
    from niyam.core.config import find_niyam_root
    from niyam.core.errors import NiyamConfigError
    from niyam.core.memory import get_memory_dir
    from niyam.core.memory_ledger.local_store import LocalMemoryLedgerStore

    repo_root = find_niyam_root()
    if not repo_root:
        raise NiyamConfigError("Not a Niyam workspace. Run 'niyam init' first.")
    
    index_path = get_memory_dir(repo_root) / "index.jsonl"
    store = LocalMemoryLedgerStore(index_path)
    
    try:
        store.validate_store()
        console.print("[bold green]✓[/] Memory ledger store is valid.")
    except Exception as e:
        console.print(f"[bold red]Validation failed:[/] {e}")
        raise typer.Exit(1)


@memory_app.command("export")
def memory_export(
    output: Annotated[str, typer.Option("--output", "-o", help="Output file path.")],
    format: Annotated[str, typer.Option("--format", "-f", help="Output format (json|yaml).")] = "json",
) -> None:
    """Export the memory ledger to a manifest file."""
    from pathlib import Path
    from niyam.core.config import find_niyam_root
    from niyam.core.errors import NiyamConfigError
    from niyam.core.memory import get_memory_dir
    from niyam.core.memory_ledger.local_store import LocalMemoryLedgerStore
    from niyam.core.memory_ledger.manifest import export_manifest

    repo_root = find_niyam_root()
    if not repo_root:
        raise NiyamConfigError("Not a Niyam workspace. Run 'niyam init' first.")
    
    if format not in ("json", "yaml"):
        console.print("[bold red]Invalid format. Use 'json' or 'yaml'.[/]")
        raise typer.Exit(1)
        
    index_path = get_memory_dir(repo_root) / "index.jsonl"
    store = LocalMemoryLedgerStore(index_path)
    records = store.list_records()
    
    out_path = Path(output)
    try:
        export_manifest(records, out_path, fmt=format)  # type: ignore
        console.print(f"[bold green]✓[/] Exported {len(records)} records to {output}")
    except Exception as e:
        console.print(f"[bold red]Export failed:[/] {e}")
        raise typer.Exit(1)


@memory_app.command("import")
def memory_import(
    file: Annotated[str, typer.Argument(help="Manifest file to import.")],
) -> None:
    """Import a memory ledger manifest file."""
    from pathlib import Path
    from niyam.core.config import find_niyam_root
    from niyam.core.errors import NiyamConfigError
    from niyam.core.memory import get_memory_dir
    from niyam.core.memory_ledger.local_store import LocalMemoryLedgerStore
    from niyam.core.memory_ledger.manifest import import_manifest

    repo_root = find_niyam_root()
    if not repo_root:
        raise NiyamConfigError("Not a Niyam workspace. Run 'niyam init' first.")
        
    index_path = get_memory_dir(repo_root) / "index.jsonl"
    store = LocalMemoryLedgerStore(index_path)
    
    in_path = Path(file)
    if not in_path.exists():
        console.print(f"[bold red]File not found:[/] {file}")
        raise typer.Exit(1)
        
    try:
        records = import_manifest(in_path)
        # For phase B, import can just append the records. We assume naive import for now.
        for r in records:
            store.append(r)
        console.print(f"[bold green]✓[/] Imported {len(records)} records from {file}")
    except Exception as e:
        console.print(f"[bold red]Import failed:[/] {e}")
        raise typer.Exit(1)


@memory_app.command("diff")
def memory_diff(
    before: Annotated[str, typer.Argument(help="Before manifest file.")],
    after: Annotated[str, typer.Argument(help="After manifest file.")],
) -> None:
    """Show differences between two memory manifest files."""
    from pathlib import Path
    from niyam.core.memory_ledger.manifest import import_manifest
    from niyam.core.memory_ledger.diff import diff_manifests

    before_path = Path(before)
    after_path = Path(after)
    
    if not before_path.exists() or not after_path.exists():
        console.print("[bold red]One or both files not found.[/]")
        raise typer.Exit(1)
        
    try:
        before_records = import_manifest(before_path)
        after_records = import_manifest(after_path)
        
        diff = diff_manifests(before_records, after_records)
        
        if diff.is_empty():
            console.print("No differences found.")
            return
            
        if diff.added:
            console.print("[bold green]Added:[/]")
            for r in diff.added:
                console.print(f"  + [{r.id}] {r.content[:50]}...")
                
        if diff.removed:
            console.print("[bold red]Removed:[/]")
            for r in diff.removed:
                console.print(f"  - [{r.id}] {r.content[:50]}...")
                
        if diff.changed:
            console.print("[bold yellow]Changed:[/]")
            for r_before, r_after in diff.changed:
                console.print(f"  ~ [{r_before.id}]")
                
    except Exception as e:
        console.print(f"[bold red]Diff failed:[/] {e}")
        raise typer.Exit(1)
