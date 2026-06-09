"""Niyam CLI memory commands."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.markup import escape

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
        record_id = escape(f"[{r.id}]")
        console.print(
            f"{record_id} {escape(r.type)} "
            f"(scope: {escape(r.scope)}, source: {escape(r.source_kind)}) "
            f"- {r.created_at}"
        )


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
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="Output file path."),
    ],
    fmt: Annotated[
        str,
        typer.Option("--format", "-f", help="Output format (json|yaml)."),
    ] = "json",
) -> None:
    """Export the memory ledger to a manifest file."""
    from niyam.core.config import find_niyam_root
    from niyam.core.errors import NiyamConfigError
    from niyam.core.memory import get_memory_dir
    from niyam.core.memory_ledger.local_store import LocalMemoryLedgerStore
    from niyam.core.memory_ledger.manifest import export_manifest

    repo_root = find_niyam_root()
    if not repo_root:
        raise NiyamConfigError("Not a Niyam workspace. Run 'niyam init' first.")

    if fmt not in ("json", "yaml"):
        console.print("[bold red]Invalid format. Use 'json' or 'yaml'.[/]")
        raise typer.Exit(1)

    index_path = get_memory_dir(repo_root) / "index.jsonl"
    store = LocalMemoryLedgerStore(index_path)
    records = store.list_records()

    try:
        export_manifest(records, output, fmt=fmt)  # type: ignore[arg-type]
        console.print(f"[bold green]✓[/] Exported {len(records)} records to {output}")
    except Exception as e:
        console.print(f"[bold red]Export failed:[/] {e}")
        raise typer.Exit(1)


@memory_app.command("import")
def memory_import(
    file: Annotated[Path, typer.Argument(help="Manifest file to import.")],
) -> None:
    """Import a memory ledger manifest file."""
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

    if not file.exists():
        console.print(f"[bold red]File not found:[/] {file}")
        raise typer.Exit(1)

    try:
        records = import_manifest(file)
        for r in records:
            store.append(r)
        console.print(f"[bold green]✓[/] Imported {len(records)} records from {file}")
    except Exception as e:
        console.print(f"[bold red]Import failed:[/] {e}")
        raise typer.Exit(1)


@memory_app.command("diff")
def memory_diff(
    before: Annotated[Path, typer.Argument(help="Before manifest file.")],
    after: Annotated[Path, typer.Argument(help="After manifest file.")],
) -> None:
    """Show differences between two memory manifest files."""
    from niyam.core.memory_ledger.manifest import import_manifest
    from niyam.core.memory_ledger.diff import diff_manifests

    if not before.exists() or not after.exists():
        console.print("[bold red]One or both files not found.[/]")
        raise typer.Exit(1)

    try:
        before_records = import_manifest(before)
        after_records = import_manifest(after)

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
            for r_before, _r_after in diff.changed:
                console.print(f"  ~ [{r_before.id}]")

    except Exception as e:
        console.print(f"[bold red]Diff failed:[/] {e}")
        raise typer.Exit(1)


@memory_app.command("redact")
def memory_redact() -> None:
    """Redact sensitive values from memory records."""
    from niyam.core.config import find_niyam_root
    from niyam.core.errors import NiyamConfigError
    from niyam.core.memory import get_memory_dir
    from niyam.core.memory_ledger.local_store import LocalMemoryLedgerStore
    from niyam.core.memory_ledger.redaction import redact_memory_records
    from niyam.core.memory_ledger.lineage import LocalMemoryLineageStore, create_lineage_event

    repo_root = find_niyam_root()
    if not repo_root:
        raise NiyamConfigError("Not a Niyam workspace. Run 'niyam init' first.")

    index_path = get_memory_dir(repo_root) / "index.jsonl"
    store = LocalMemoryLedgerStore(index_path)
    records = store.list_records()

    if not records:
        console.print("[yellow]No memory records to redact.[/]")
        return

    redacted_records, modified_count = redact_memory_records(records)

    if modified_count > 0:
        store.replace_all(redacted_records)

        lineage_path = get_memory_dir(repo_root) / "lineage" / "recall-events.jsonl"
        lineage_store = LocalMemoryLineageStore(lineage_path)
        for original, redacted in zip(records, redacted_records):
            if original.model_dump() != redacted.model_dump():
                event = create_lineage_event(
                    event_type="redacted",
                    record_id=redacted.id,
                    reason="Redaction command executed",
                )
                lineage_store.append(event)

        console.print(
            f"[bold green]✓[/] Redacted secrets from {modified_count} "
            "memory record(s)."
        )
    else:
        console.print("[bold green]✓[/] No secrets found to redact.")


@memory_app.command("policy-check")
def memory_policy_check(
    policy: Annotated[
        Path | None,
        typer.Option("--policy", help="Path to policy YAML file."),
    ] = None,
    output: Annotated[
        str,
        typer.Option("--output", help="Output format (text|json)."),
    ] = "text",
    fail_on: Annotated[
        str,
        typer.Option(
            "--fail-on",
            help="Severity level to fail on (info|low|medium|high|critical).",
        ),
    ] = "high",
) -> None:
    """Evaluate memory records against memory policies."""
    from niyam.core.config import find_niyam_root
    from niyam.core.errors import NiyamConfigError
    from niyam.core.memory import get_memory_dir
    from niyam.core.memory_ledger.local_store import LocalMemoryLedgerStore
    from niyam.core.memory_ledger.policy import load_policy, run_policy_check
    import json

    repo_root = find_niyam_root()
    if not repo_root:
        raise NiyamConfigError("Not a Niyam workspace. Run 'niyam init' first.")

    severity_levels = {"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}
    if fail_on.lower() not in severity_levels:
        console.print("[bold red]Invalid --fail-on severity.[/]")
        raise typer.Exit(1)

    if output not in {"text", "json"}:
        console.print("[bold red]Invalid --output format. Use 'text' or 'json'.[/]")
        raise typer.Exit(1)

    if policy is None:
        policy = get_memory_dir(repo_root) / "policies" / "memory-policy.yaml"

    try:
        mem_policy = load_policy(policy)
    except Exception as e:
        console.print(f"[bold red]Failed to load policy:[/] {e}")
        raise typer.Exit(1)

    index_path = get_memory_dir(repo_root) / "index.jsonl"
    store = LocalMemoryLedgerStore(index_path)
    records = store.list_records()

    findings = run_policy_check(records, mem_policy)

    if output == "json":
        data = [f.model_dump() for f in findings]
        console.print(json.dumps(data, indent=2))
    else:
        if not findings:
            console.print("[bold green]✓[/] No policy findings.")
        else:
            for f in findings:
                record_id = escape(f"[{f.record_id}]")
                console.print(
                    f"[[bold red]{escape(f.severity.upper())}[/]] "
                    f"{record_id} {escape(f.code)}: {escape(f.message)}"
                )

    threshold = severity_levels[fail_on.lower()]

    max_severity = -1
    for f in findings:
        max_severity = max(max_severity, severity_levels.get(f.severity, 0))

    if max_severity >= threshold:
        raise typer.Exit(2)


@memory_app.command("trace")
def memory_trace(
    record_id: Annotated[str, typer.Argument(help="ID of the memory record to trace.")],
) -> None:
    """Inspect source and recall lineage for a memory record."""
    from niyam.core.config import find_niyam_root
    from niyam.core.errors import NiyamConfigError
    from niyam.core.memory import get_memory_dir
    from niyam.core.memory_ledger.lineage import LocalMemoryLineageStore

    repo_root = find_niyam_root()
    if not repo_root:
        raise NiyamConfigError("Not a Niyam workspace. Run 'niyam init' first.")

    lineage_path = get_memory_dir(repo_root) / "lineage" / "recall-events.jsonl"
    store = LocalMemoryLineageStore(lineage_path)
    events = store.get_events_for_record(record_id)

    if not events:
        console.print("[yellow]No lineage found for this record.[/]")
        return

    for evt in events:
        timestamp = escape(f"[{evt.timestamp.isoformat()}]")
        reason = escape(evt.reason or "No reason provided")
        console.print(f"{timestamp} {escape(evt.event_type)} - {reason}")


@memory_app.command("recall")
def memory_recall(
    query: Annotated[
        str,
        typer.Argument(help="Keyword query to match against memory records."),
    ],
    limit: Annotated[
        int | None,
        typer.Option("--limit", help="Max number of records to return."),
    ] = None,
    scope: Annotated[
        str | None,
        typer.Option("--scope", help="Filter by scope (e.g., project)."),
    ] = None,
) -> None:
    """Recall relevant memory records for a task or query."""
    from niyam.core.config import find_niyam_root
    from niyam.core.errors import NiyamConfigError
    from niyam.core.memory import get_memory_dir
    from niyam.core.memory_ledger.local_store import LocalMemoryLedgerStore
    from niyam.core.memory_ledger.recall import recall_records
    from niyam.core.memory_ledger.lineage import LocalMemoryLineageStore, create_lineage_event

    repo_root = find_niyam_root()
    if not repo_root:
        raise NiyamConfigError("Not a Niyam workspace. Run 'niyam init' first.")

    index_path = get_memory_dir(repo_root) / "index.jsonl"
    store = LocalMemoryLedgerStore(index_path)
    records = store.list_records()

    results = recall_records(records, query, limit, scope)

    if not results:
        console.print("[yellow]No matching records found.[/]")
        return

    lineage_path = get_memory_dir(repo_root) / "lineage" / "recall-events.jsonl"
    lineage_store = LocalMemoryLineageStore(lineage_path)

    for r in results:
        event = create_lineage_event(
            event_type="recalled",
            record_id=r.id,
            reason=f"Recalled by query: {query}",
        )
        lineage_store.append(event)
        
        console.print(f"--- {escape(f'[{r.id}]')} {escape(r.type)} ---")
        console.print(escape(r.content))


@memory_app.command("serve-mcp")
def memory_serve_mcp(
    root: Annotated[
        Path | None,
        typer.Option(
            "--root",
            help="Niyam workspace root. Defaults to current workspace.",
        ),
    ] = None,
) -> None:
    """Start the Memory Ledger MCP server over stdio."""
    from niyam.core.config import find_niyam_root
    from niyam.core.errors import NiyamConfigError
    from niyam.mcp.memory_server import run_stdio_server

    repo_root = root or find_niyam_root()
    if not repo_root:
        raise NiyamConfigError("Not a Niyam workspace. Run 'niyam init' first.")

    run_stdio_server(repo_root)
