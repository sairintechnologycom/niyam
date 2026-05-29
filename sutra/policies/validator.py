"""Sutra policy validator — check policy YAML files."""

from __future__ import annotations

from pathlib import Path

import yaml
from rich.console import Console
from rich.table import Table

from sutra.core.config import find_sutra_root


KNOWN_POLICY_FILES = {
    "commands.yaml": {"required_keys": [], "optional_keys": ["deny", "warn"]},
    "approvals.yaml": {"required_keys": [], "optional_keys": ["approval_required_for"]},
    "security.yaml": {
        "required_keys": [],
        "optional_keys": [
            "block_secrets_in_code",
            "require_auth_review",
            "require_input_validation",
            "deny_write_patterns",
            "allow_write_patterns",
        ],
    },
    "evidence.yaml": {
        "required_keys": [],
        "optional_keys": [
            "require_diff_summary",
            "require_validation_results",
            "require_policy_events",
        ],
    },
}


def run_policy_validate(console: Console) -> None:
    """Validate all policy YAML files."""
    root = find_sutra_root()
    if root is None:
        console.print("[bold red]Error:[/] Not a Sutra workspace. Run [bold]sutra init[/] first.")
        raise SystemExit(1)

    policies_dir = root / ".sutra" / "policies"
    if not policies_dir.is_dir():
        console.print("[bold red]Error:[/] No policies directory found.")
        raise SystemExit(1)

    table = Table(title="Policy Validation", show_lines=False)
    table.add_column("Policy File", style="bold")
    table.add_column("Status", justify="center")
    table.add_column("Details")

    errors = 0

    # Validate remote policies if remote_policy_url is set
    from sutra.core.config import load_sutra_config
    try:
        config = load_sutra_config(root)
        remote_url = config.guard.remote_policy_url
    except Exception:
        remote_url = None

    if remote_url:
        from sutra.policies.guard import _fetch_remote_policy
        for filename, schema in KNOWN_POLICY_FILES.items():
            if filename not in ("security.yaml", "commands.yaml"):
                continue
            remote_data = _fetch_remote_policy(remote_url, filename)
            if remote_data is None:
                table.add_row(f"[Remote] {filename}", "[bold red]✗[/]", f"Failed to fetch from {remote_url}")
                errors += 1
                continue

            if not isinstance(remote_data, dict):
                table.add_row(f"[Remote] {filename}", "[bold red]✗[/]", "Expected a YAML mapping")
                errors += 1
                continue

            all_known = set(schema["required_keys"]) | set(schema["optional_keys"])
            unknown = set(remote_data.keys()) - all_known
            if unknown:
                table.add_row(
                    f"[Remote] {filename}",
                    "[bold yellow]⚠[/]",
                    f"Unknown keys: {', '.join(unknown)}",
                )
            else:
                table.add_row(f"[Remote] {filename}", "[bold green]✓[/]", "Valid")

    # Check known policy files
    for filename, schema in KNOWN_POLICY_FILES.items():
        fpath = policies_dir / filename

        if not fpath.exists():
            table.add_row(filename, "[bold yellow]⚠[/]", "Not found (optional)")
            continue

        try:
            with open(fpath) as f:
                data = yaml.safe_load(f) or {}

            if not isinstance(data, dict):
                table.add_row(filename, "[bold red]✗[/]", "Expected a YAML mapping")
                errors += 1
                continue

            # Check for unknown keys
            all_known = set(schema["required_keys"]) | set(schema["optional_keys"])
            unknown = set(data.keys()) - all_known
            if unknown:
                table.add_row(
                    filename,
                    "[bold yellow]⚠[/]",
                    f"Unknown keys: {', '.join(unknown)}",
                )
            else:
                table.add_row(filename, "[bold green]✓[/]", "Valid")

        except yaml.YAMLError as e:
            table.add_row(filename, "[bold red]✗[/]", f"YAML error: {e}")
            errors += 1

    # Check for extra policy files
    for fpath in policies_dir.glob("*.yaml"):
        if fpath.name not in KNOWN_POLICY_FILES:
            try:
                with open(fpath) as f:
                    yaml.safe_load(f)
                table.add_row(fpath.name, "[bold cyan]ℹ[/]", "Custom policy (valid YAML)")
            except yaml.YAMLError as e:
                table.add_row(fpath.name, "[bold red]✗[/]", f"YAML error: {e}")
                errors += 1

    console.print(table)
    console.print()

    if errors == 0:
        console.print("[bold green]All policies valid.[/]")
    else:
        console.print(f"[bold red]{errors} policy error(s) found.[/]")
        raise SystemExit(1)
