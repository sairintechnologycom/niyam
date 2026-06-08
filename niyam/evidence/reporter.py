"""Niyam evidence reporter — generate audit trails for AI-assisted work."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

from niyam.core.config import find_niyam_root, load_niyam_config


def _get_current_branch(repo_root: Path) -> str:
    """Get the current git branch name."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except FileNotFoundError:
        pass
    return "unknown"


def _get_diff_summary(repo_root: Path) -> str:
    """Generate a git diff summary."""
    try:
        # Staged changes
        staged = subprocess.run(
            ["git", "diff", "--cached", "--stat"],
            cwd=repo_root,
            capture_output=True,
            text=True,
        )
        # Unstaged changes
        unstaged = subprocess.run(
            ["git", "diff", "--stat"],
            cwd=repo_root,
            capture_output=True,
            text=True,
        )
        # Recent commits on this branch vs main
        log = subprocess.run(
            ["git", "log", "--oneline", "-20", "--no-merges"],
            cwd=repo_root,
            capture_output=True,
            text=True,
        )

        sections = []
        if staged.stdout.strip():
            sections.append(f"## Staged Changes\n\n```\n{staged.stdout.strip()}\n```")
        if unstaged.stdout.strip():
            sections.append(
                f"## Unstaged Changes\n\n```\n{unstaged.stdout.strip()}\n```"
            )
        if log.stdout.strip():
            sections.append(f"## Recent Commits\n\n```\n{log.stdout.strip()}\n```")

        return "\n\n".join(sections) if sections else "No changes detected."

    except FileNotFoundError:
        return "Git not available."


def _get_validation_results(repo_root: Path) -> tuple[str, bool]:
    """Run validation commands and collect results.

    Returns:
        A tuple of (results_markdown, has_failures).
    """
    import yaml

    from niyam.core.security import CommandSecurityError, safe_run_command

    project_yaml = repo_root / ".niyam" / "project.yaml"
    if not project_yaml.exists():
        return "No project.yaml found — run `niyam context refresh` first.", False

    with open(project_yaml) as f:
        project_data = yaml.safe_load(f) or {}

    validation = project_data.get("validation", {})
    if not validation:
        return "No validation commands configured.", False

    results = []
    has_failures = False
    for cmd_type, cmd in validation.items():
        results.append(f"### {cmd_type.title()}")
        results.append(f"Command: `{cmd}`")
        if not cmd:
            results.append("Status: Not Configured")
            results.append("")
            continue
        try:
            result = safe_run_command(
                cmd,
                cwd=repo_root,
                timeout=120,
            )
            status = "✓ Passed" if result.returncode == 0 else "✗ Failed"
            if result.returncode != 0:
                has_failures = True
            results.append(f"Status: {status}")
            if result.stdout.strip():
                output = result.stdout.strip()
                # Truncate long output
                if len(output) > 2000:
                    output = output[:2000] + "\n... (truncated)"
                results.append(f"```\n{output}\n```")
            if result.returncode != 0 and result.stderr.strip():
                stderr = result.stderr.strip()
                if len(stderr) > 1000:
                    stderr = stderr[:1000] + "\n... (truncated)"
                results.append(f"```\n{stderr}\n```")
        except CommandSecurityError as e:
            has_failures = True
            results.append(f"Status: 🛑 Blocked by security policy: {e}")
        except subprocess.TimeoutExpired:
            has_failures = True
            results.append("Status: ⚠ Timed out (120s)")
        except Exception as e:
            has_failures = True
            results.append(f"Status: ⚠ Error: {e}")
        results.append("")

    return "\n".join(results), has_failures


def _get_policy_events(repo_root: Path) -> list[dict]:
    """Load policy events from evidence directory."""
    events_file = repo_root / ".niyam" / "evidence" / "policy-events.json"
    if events_file.exists():
        try:
            with open(events_file) as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            pass
    return []


def _generate_evidence_markdown(
    branch: str,
    diff_summary: str,
    validation_results: str,
    policy_events: list[dict],
    cost_metrics: dict,
    project_name: str,
) -> str:
    """Generate the evidence.md file content."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines = [
        f"# Evidence Report — {project_name}",
        "",
        f"**Branch:** `{branch}`",
        f"**Generated:** {now}",
        "**Generator:** Niyam v0.1.0",
        "",
        "---",
        "",
        "# Cost & Token Usage",
        "",
        f"- **Total Estimated Cost:** `${cost_metrics.get('total_cost', 0.0):.4f}`",
        f"- **Total Tokens:** `{cost_metrics.get('total_input_tokens', 0) + cost_metrics.get('total_output_tokens', 0):,}` ({cost_metrics.get('total_input_tokens', 0):,} In / {cost_metrics.get('total_output_tokens', 0):,} Out)",
        f"- **Wasted Cost (Failures/Repeats):** `${cost_metrics.get('failed_repeated_cost', 0.0):.4f}`",
        "",
        "---",
        "",
        "# Diff Summary",
        "",
        diff_summary,
        "",
        "---",
        "",
        "# Validation Results",
        "",
        validation_results,
        "",
        "---",
        "",
        "# Policy Events",
        "",
    ]

    if policy_events:
        lines.append(f"**{len(policy_events)} event(s) recorded:**")
        lines.append("")
        for event in policy_events:
            ts = event.get("timestamp", "?")
            etype = event.get("type", "?")
            details = event.get("details", "?")
            emoji = "🛑" if etype == "BLOCKED" else "⚠️"
            lines.append(f"- {emoji} **{etype}** at {ts}: {details}")
    else:
        lines.append("No policy events recorded.")

    lines.extend(["", "---", "", "<!-- End of Niyam Evidence Report -->", ""])

    return "\n".join(lines)


def run_report(format: str, console: Console) -> None:
    """Generate evidence report for the current branch."""
    from niyam.core.cost import load_cost_events, generate_cost_metrics

    root = find_niyam_root()
    if root is None:
        console.print(
            "[bold red]Error:[/] Not a Niyam workspace. Run [bold]niyam init[/] first."
        )
        raise SystemExit(1)

    config = load_niyam_config(root)
    branch = _get_current_branch(root)

    console.print(f"[dim]Generating evidence for branch: {branch}[/]")

    # Collect evidence
    diff_summary = _get_diff_summary(root)
    validation_results, has_failures = _get_validation_results(root)
    policy_events = _get_policy_events(root)
    
    # Collect cost metrics for this branch
    all_events = load_cost_events(root)
    branch_events = [e for e in all_events if e.branch == branch]
    cost_metrics = generate_cost_metrics(branch_events)

    # Create evidence directory for this branch
    safe_branch = branch.replace("/", "--")
    evidence_dir = root / ".niyam" / "evidence" / safe_branch
    evidence_dir.mkdir(parents=True, exist_ok=True)

    if format == "json":
        # JSON export
        evidence_data = {
            "project": config.project_name,
            "branch": branch,
            "generated": datetime.now(timezone.utc).isoformat(),
            "diff_summary": diff_summary,
            "validation_results": validation_results,
            "policy_events": policy_events,
            "cost_metrics": cost_metrics,
        }
        json_path = evidence_dir / "evidence.json"
        json_path.write_text(json.dumps(evidence_data, indent=2), encoding="utf-8")
        if has_failures:
            console.print(
                f"[yellow]⚠[/] Evidence exported with validation failures: [cyan]{json_path.relative_to(root)}[/]"
            )
        else:
            console.print(
                f"[green]✓[/] Evidence exported: [cyan]{json_path.relative_to(root)}[/]"
            )

    else:
        # Markdown report
        evidence_md = _generate_evidence_markdown(
            branch=branch,
            diff_summary=diff_summary,
            validation_results=validation_results,
            policy_events=policy_events,
            cost_metrics=cost_metrics,
            project_name=config.project_name,
        )

        # Write individual files
        (evidence_dir / "diff-summary.md").write_text(
            f"# Diff Summary\n\n{diff_summary}\n", encoding="utf-8"
        )
        (evidence_dir / "validation-results.md").write_text(
            f"# Validation Results\n\n{validation_results}\n", encoding="utf-8"
        )
        (evidence_dir / "policy-events.json").write_text(
            json.dumps(policy_events, indent=2), encoding="utf-8"
        )
        (evidence_dir / "cost-metrics.json").write_text(
            json.dumps(cost_metrics, indent=2), encoding="utf-8"
        )
        (evidence_dir / "evidence.md").write_text(evidence_md, encoding="utf-8")

        if has_failures:
            console.print(
                Panel(
                    f"[bold yellow]⚠[/] Evidence generated with validation failures for branch [cyan]{branch}[/]\n\n"
                    f"  [dim]•[/] {evidence_dir.relative_to(root)}/evidence.md\n"
                    f"  [dim]•[/] {evidence_dir.relative_to(root)}/diff-summary.md\n"
                    f"  [dim]•[/] {evidence_dir.relative_to(root)}/validation-results.md\n"
                    f"  [dim]•[/] {evidence_dir.relative_to(root)}/policy-events.json\n"
                    f"  [dim]•[/] {evidence_dir.relative_to(root)}/cost-metrics.json\n"
                    f"\n  Policy events: {len(policy_events)}",
                    title="[bold yellow]Evidence Report (Degraded)[/]",
                    border_style="yellow",
                )
            )
        else:
            console.print(
                Panel(
                    f"[bold green]✓[/] Evidence generated for branch [cyan]{branch}[/]\n\n"
                    f"  [dim]•[/] {evidence_dir.relative_to(root)}/evidence.md\n"
                    f"  [dim]•[/] {evidence_dir.relative_to(root)}/diff-summary.md\n"
                    f"  [dim]•[/] {evidence_dir.relative_to(root)}/validation-results.md\n"
                    f"  [dim]•[/] {evidence_dir.relative_to(root)}/policy-events.json\n"
                    f"  [dim]•[/] {evidence_dir.relative_to(root)}/cost-metrics.json\n"
                    f"\n  Policy events: {len(policy_events)}",
                    title="[bold green]Evidence Report[/]",
                    border_style="green",
                )
            )


    if has_failures:
        raise SystemExit(1)
