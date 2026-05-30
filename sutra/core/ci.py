"""Sutra CI/CD verification module."""

from __future__ import annotations

import json
import fnmatch
import subprocess
from datetime import datetime, timezone

from rich.console import Console
from rich.panel import Panel

from sutra.core.config import (
    find_sutra_root,
    get_sutra_dir,
    load_project_config,
)
from sutra.mission.planner import resolve_mission_id
from sutra.mission.reporter import run_verify_report
from sutra.policies.guard import load_security_policy


def run_ci_verify(
    target_branch: str = "main", strict: bool = True, console: Console = None
) -> None:
    """Verify cryptographic integrity, guardrails, and validation status for CI/CD."""
    if console is None:
        console = Console()

    root = find_sutra_root()
    if root is None:
        console.print(
            "[bold red]❌ CI Validation Failed:[/] Not a Sutra workspace. Run [bold]sutra init[/] first."
        )
        raise SystemExit(1)

    sutra_dir = get_sutra_dir(root)
    mission_id = resolve_mission_id(sutra_dir)
    run_dir = sutra_dir / "runs" / mission_id if mission_id else None
    evidence_path = run_dir / "evidence.md" if run_dir else None

    integrity_status = "skipped"
    policy_status = "passed"
    validation_status = "passed"
    failures = []

    console.print("[cyan]Sutra CI/CD Verification[/]")
    console.print(f"Target Branch: [bold cyan]{target_branch}[/]")
    console.print(f"Strict Mode: [bold]{'Enabled' if strict else 'Disabled'}[/]")
    console.print(f"Latest Mission: [bold cyan]{mission_id or 'None'}[/]\n")

    # 1. Cryptographic Evidence Integrity Check
    if not evidence_path or not evidence_path.exists():
        if strict:
            failures.append("Evidence report (evidence.md) not found.")
            integrity_status = "failed"
            console.print(
                "[bold red]❌ Integrity check failed:[/] evidence.md not found in run directory."
            )
        else:
            console.print(
                "[bold yellow]⚠ Warning:[/] evidence.md not found. Skipping integrity checks (non-strict mode)."
            )
    else:
        console.print("[cyan]Verifying evidence report integrity...[/]")
        try:
            # We call run_verify_report which handles printing and exits on failure
            run_verify_report(str(evidence_path), console)
            integrity_status = "passed"
        except SystemExit as e:
            if e.code != 0:
                failures.append("Evidence integrity check failed.")
                integrity_status = "failed"
            else:
                integrity_status = "passed"
        except Exception as e:
            failures.append(f"Evidence integrity check encountered error: {e}")
            integrity_status = "failed"
            console.print(f"[bold red]❌ Integrity check error:[/] {e}")

    # 2. Write Guard Restrictions check against Target Branch
    console.print("\n[cyan]Checking write restriction policies against Git diff...[/]")
    try:
        # Check if it is a Git repository
        if not (root / ".git").exists():
            console.print(
                "[bold yellow]⚠ Warning:[/] Not a Git repository. Skipping diff policy checks."
            )
        else:
            # Get changes between HEAD and target branch
            res = subprocess.run(
                ["git", "diff", "--name-only", target_branch],
                cwd=root,
                capture_output=True,
                text=True,
            )
            if res.returncode != 0:
                # Fall back to comparing against origin/target_branch
                res = subprocess.run(
                    ["git", "diff", "--name-only", f"origin/{target_branch}"],
                    cwd=root,
                    capture_output=True,
                    text=True,
                )

            if res.returncode == 0:
                changed_files = []
                for line in res.stdout.splitlines():
                    f = line.strip()
                    if (
                        f
                        and not f.startswith(".sutra")
                        and f not in ("evidence.md", "evidence.json")
                    ):
                        changed_files.append(f)

                # Load security policy
                sec_data = load_security_policy(root)
                deny_patterns = sec_data.get("deny_write_patterns", [])
                allow_patterns = sec_data.get("allow_write_patterns", [])

                if deny_patterns or allow_patterns:
                    violated_files = []
                    for f in changed_files:
                        if deny_patterns and any(
                            fnmatch.fnmatch(f, pat) for pat in deny_patterns
                        ):
                            violated_files.append((f, "Denied pattern matched"))
                        elif allow_patterns and not any(
                            fnmatch.fnmatch(f, pat) for pat in allow_patterns
                        ):
                            violated_files.append((f, "Not in allow list"))

                    if violated_files:
                        policy_status = "failed"
                        for f, reason in violated_files:
                            err_msg = f"Write violation on {f} ({reason})"
                            failures.append(err_msg)
                            console.print(
                                f"[bold red]❌ Write Restriction Violation:[/] {f} - {reason}"
                            )
                    else:
                        console.print(
                            "[bold green]✓[/] Git diff conforms to write restriction policies."
                        )
                else:
                    console.print(
                        "[dim]No write restriction policies (deny/allow lists) defined.[/]"
                    )
            else:
                console.print(
                    "[bold yellow]⚠ Warning:[/] git diff execution failed. Skipping diff checks."
                )
    except Exception as e:
        failures.append(f"Write restriction check encountered error: {e}")
        policy_status = "failed"
        console.print(f"[bold red]❌ Write restriction check error:[/] {e}")

    # 3. Workspace Validation Commands
    project_config = None
    try:
        project_config = load_project_config(root)
    except Exception:
        pass

    if project_config and project_config.validation:
        from sutra.core.security import CommandSecurityError, safe_run_command

        console.print("\n[cyan]Executing workspace validation checks...[/]")
        val_cmds = project_config.validation
        # We run test, lint, and build if configured
        cmds_to_run = {
            "lint": val_cmds.lint,
            "typecheck": val_cmds.typecheck,
            "test": val_cmds.test,
            "build": val_cmds.build,
        }

        for name, cmd in cmds_to_run.items():
            if cmd:
                console.print(f"Running validation [cyan]{name}[/]: `{cmd}`...")
                try:
                    res = safe_run_command(cmd, cwd=root, timeout=120)
                except CommandSecurityError as e:
                    failures.append(
                        f"Validation command '{name}' blocked by security policy: {e}"
                    )
                    validation_status = "failed"
                    console.print(f"[bold red]🛑 Validation '{name}' blocked:[/] {e}")
                    continue

                if res.returncode != 0:
                    failures.append(
                        f"Validation command '{name}' failed with code {res.returncode}."
                    )
                    validation_status = "failed"
                    console.print(f"[bold red]❌ Validation failed for {name}[/]")
                    if res.stderr or res.stdout:
                        console.print(
                            f"[dim]Output snippet:\n{res.stderr or res.stdout}[/]"
                        )
                else:
                    console.print(
                        f"[bold green]✓[/] Validation [green]{name}[/] passed."
                    )

    # 4. Save JSON Report
    report_data = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "mission_id": mission_id or "",
        "integrity_status": integrity_status,
        "policy_status": policy_status,
        "validation_status": validation_status,
        "failures": failures,
    }

    report_path = sutra_dir / "ci-report.json"
    try:
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2)
    except Exception as e:
        console.print(f"[bold yellow]Warning: Failed to save CI report:[/] {e}")

    # Summary Panel
    success = len(failures) == 0
    summary_text = (
        f"Integrity check: [bold {'green]PASSED' if integrity_status == 'passed' else 'red]FAILED' if integrity_status == 'failed' else 'yellow]SKIPPED'}\n"
        f"Policy checks: [bold {'green]PASSED' if policy_status == 'passed' else 'red]FAILED'}\n"
        f"Validation checks: [bold {'green]PASSED' if validation_status == 'passed' else 'red]FAILED'}\n"
    )

    if success:
        console.print(
            Panel(
                summary_text
                + "\n[bold green]✓ CI/CD Verification Successful. All gates passed![/]",
                title="[bold green]CI/CD Verification Passed[/]",
                border_style="green",
            )
        )
    else:
        console.print(
            Panel(
                summary_text
                + f"\n[bold red]❌ CI/CD Verification Failed with {len(failures)} error(s):[/]\n"
                + "\n".join(f"  • {f}" for f in failures),
                title="[bold red]CI/CD Verification Failed[/]",
                border_style="red",
            )
        )
        raise SystemExit(1)
