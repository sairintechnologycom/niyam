"""Niyam multi-runtime task comparison logic."""

from __future__ import annotations

import json
import shutil
import subprocess
import time
from rich.console import Console
from rich.table import Table

from niyam.core.config import find_niyam_root, get_niyam_dir, load_project_config
from niyam.mission.planner import resolve_mission_id
from niyam.mission.executor import (
    load_plan,
    execute_single_task,
    cleanup_worktree,
)


def run_comparison(task_id: str, executors_str: str, console: Console) -> None:
    """Run comparison of multiple executors on a single task."""
    root = find_niyam_root()
    if root is None:
        console.print(
            "[bold red]Error:[/] Not a Niyam workspace. Run [bold]niyam init[/] first."
        )
        raise SystemExit(1)

    niyam_dir = get_niyam_dir(root)
    mission_id = resolve_mission_id(niyam_dir)
    if not mission_id:
        console.print("[bold red]Error:[/] No active or completed mission found.")
        raise SystemExit(1)

    run_dir = niyam_dir / "runs" / mission_id
    plan_data = load_plan(run_dir)
    tasks = plan_data.get("tasks", [])
    task = None
    for t in tasks:
        if (
            t["id"].lower() == task_id.lower()
            or t.get("title", "").lower() == task_id.lower()
        ):
            task = t
            break

    if not task:
        console.print(
            f"[bold red]Error:[/] Task '{task_id}' not found in mission plan."
        )
        raise SystemExit(1)

    executors = [e.strip().lower() for e in executors_str.split(",") if e.strip()]
    if not executors:
        console.print("[bold red]Error:[/] No executors specified for comparison.")
        raise SystemExit(1)

    project_config = load_project_config(root)
    is_git = (root / ".git").exists()
    use_worktree = plan_data.get("mission", {}).get("worktree", True) and is_git

    results = []

    console.print(
        f"[cyan]Starting Multi-Runtime Comparison for Task: [bold]{task['id']} - {task['title']}[/][/]"
    )
    console.print(f"Executors to compare: [bold]{', '.join(executors)}[/]\n")

    for executor in executors:
        console.print(f"[bold yellow]=== Running task with executor: {executor} ===[/]")

        # Create isolated comparison run directory
        comparison_run_dir = run_dir / "comparison" / task["id"] / executor
        if comparison_run_dir.exists():
            try:
                shutil.rmtree(comparison_run_dir)
            except Exception:
                pass
        comparison_run_dir.mkdir(parents=True, exist_ok=True)

        # Copy requirement and plan
        req_file = run_dir / "requirement.md"
        if req_file.exists():
            shutil.copy2(req_file, comparison_run_dir / "requirement.md")
        plan_file = run_dir / "mission-plan.yaml"
        if plan_file.exists():
            shutil.copy2(plan_file, comparison_run_dir / "mission-plan.yaml")

        # Copy agents folder for context
        agents_src = niyam_dir / "agents"
        if agents_src.is_dir():
            shutil.copytree(
                agents_src, comparison_run_dir / ".niyam" / "agents", dirs_exist_ok=True
            )

        comp_task = task.copy()
        comp_task["runtime"] = executor

        branch_name = f"niyam-compare-{mission_id}-{task['id']}-{executor}"
        start_time = time.time()
        success = False

        try:
            success = execute_single_task(
                task=comp_task,
                run_dir=comparison_run_dir,
                niyam_dir=niyam_dir,
                repo_root=root,
                mission_id=mission_id,
                use_worktree=use_worktree,
                project_config=project_config,
                console=console,
                non_interactive=True,
                branch_name=branch_name,
            )
        except Exception as e:
            console.print(f"[bold red]Execution error with {executor}:[/] {e}")

        duration = time.time() - start_time

        # Read metrics from token ledger
        input_tokens = 0
        output_tokens = 0
        total_tokens = 0
        cost = 0.0
        ledger_path = comparison_run_dir / "token-ledger.json"
        if ledger_path.exists():
            try:
                with open(ledger_path, encoding="utf-8") as f:
                    ledger = json.load(f)
                    summary = ledger.get("summary", {})
                    input_tokens = summary.get("total_input_tokens", 0)
                    output_tokens = summary.get("total_output_tokens", 0)
                    total_tokens = summary.get("total_tokens", 0)
                    cost = summary.get("total_cost_usd", 0.0)
            except Exception:
                pass

        # Cleanup isolated branch / worktree
        if use_worktree:
            try:
                worktree_path = comparison_run_dir / "worktrees" / comp_task["id"]
                cleanup_worktree(root, worktree_path, branch_name, console)
                subprocess.run(
                    ["git", "branch", "-D", branch_name],
                    cwd=root,
                    capture_output=True,
                )
            except Exception:
                pass

        results.append(
            {
                "executor": executor,
                "success": success,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "cost": cost,
                "duration": duration,
            }
        )

    # Render results
    table = Table(title=f"Comparison Results for Task {task['id']}")
    table.add_column("Executor", style="cyan", justify="left")
    table.add_column("Status", justify="center")
    table.add_column("Input Tokens", justify="right")
    table.add_column("Output Tokens", justify="right")
    table.add_column("Total Tokens", justify="right")
    table.add_column("Cost (USD)", justify="right")
    table.add_column("Duration (s)", justify="right")

    for r in results:
        status_str = "[bold green]PASS[/]" if r["success"] else "[bold red]FAIL[/]"
        table.add_row(
            r["executor"],
            status_str,
            f"{r['input_tokens']:,}",
            f"{r['output_tokens']:,}",
            f"{r['total_tokens']:,}",
            f"${r['cost']:.4f}",
            f"{r['duration']:.2f}s",
        )

    console.print("\n")
    console.print(table)
    console.print("\n")

    # Save Markdown report
    report_lines = [
        f"# Comparison Report — Task {task['id']}",
        "",
        f"**Task Title:** {task['title']}",
        f"**Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Summary Metrics",
        "",
        "| Executor | Status | Input Tokens | Output Tokens | Total Tokens | Cost (USD) | Duration |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in results:
        status_md = "PASS" if r["success"] else "FAIL"
        report_lines.append(
            f"| {r['executor']} | {status_md} | {r['input_tokens']:,} | {r['output_tokens']:,} | {r['total_tokens']:,} | ${r['cost']:.4f} | {r['duration']:.2f}s |"
        )
    report_lines.append("")

    report_path = run_dir / "comparison" / task["id"] / "comparison-report.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(report_lines), encoding="utf-8")
    console.print(f"[green]✓[/] Comparison report saved to: {report_path}")
