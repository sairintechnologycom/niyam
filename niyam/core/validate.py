"""Niyam core validation logic for tasks."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from rich.console import Console

from niyam.core.config import find_niyam_root, get_niyam_dir, load_project_config, load_niyam_config
from niyam.mission.planner import resolve_mission_id
from niyam.mission.utils import load_plan


def run_task_validation(task_id: str, mission_id: str | None, console: Console) -> None:
    """Run validation for a specific task manually."""
    repo_root = find_niyam_root()
    if not repo_root:
        console.print("[bold red]Error:[/] Not a Niyam workspace. Run 'niyam init' first.")
        raise SystemExit(1)

    niyam_dir = get_niyam_dir(repo_root)
    resolved_mission = resolve_mission_id(niyam_dir, mission_id)
    if not resolved_mission:
        console.print("[bold red]Error:[/] No missions found.")
        raise SystemExit(1)

    run_dir = niyam_dir / "runs" / resolved_mission
    plan_data = load_plan(run_dir)

    tasks = plan_data.get("tasks", [])
    target_task = None
    for t in tasks:
        if t["id"] == task_id:
            target_task = t
            break

    if not target_task:
        console.print(f"[bold red]Error:[/] Task '{task_id}' not found in mission '{resolved_mission}'.")
        raise SystemExit(1)

    console.print(f"Running validation for task [bold cyan]{task_id}[/]...")

    # Load project level validation
    project_config = None
    niyam_config = None
    min_coverage = None
    try:
        project_config = load_project_config(repo_root)
        niyam_config = load_niyam_config(repo_root)
        if niyam_config and niyam_config.governance and niyam_config.governance.scan:
            min_coverage = niyam_config.governance.scan.min_test_coverage
    except Exception:
        pass

    validation_results = []
    success = True
    
    # We borrow the logic from task_runner.py to run validation
    from niyam.mission.task_runner import run_validation_command

    if project_config and project_config.validation:
        v_cmds = project_config.validation
        checks = [
            ("format", v_cmds.format),
            ("lint", v_cmds.lint),
            ("typecheck", v_cmds.typecheck),
            ("build", v_cmds.build),
            ("test", v_cmds.test),
        ]

        task_validation = target_task.get("validation", {})
        task_cmds = []
        if isinstance(task_validation, dict):
            task_cmds = task_validation.get("commands", [])
        elif hasattr(task_validation, "commands"):
            task_cmds = task_validation.commands

        executed_cmds = set()

        # Run project level commands
        for name, cmd in checks:
            if cmd:
                console.print(f"Executing [bold]{name}[/] command: {cmd}")
                cmd_success = run_validation_command(cmd, run_dir, repo_root, console)
                validation_results.append({"name": name, "command": cmd, "success": cmd_success})
                executed_cmds.add(cmd.strip())
                if not cmd_success:
                    success = False
                    console.print(f"[bold red]FAILED:[/] {name}")
                else:
                    console.print(f"[bold green]PASS:[/] {name}")

        # Run task specific commands
        if task_cmds:
            for i, cmd in enumerate(task_cmds, start=1):
                if cmd.strip() in executed_cmds:
                    continue
                console.print(f"Executing task-specific validation command: {cmd}")
                cmd_success = run_validation_command(cmd, run_dir, repo_root, console)
                validation_results.append({"name": f"task_val_{i}", "command": cmd, "success": cmd_success})
                if not cmd_success:
                    success = False
                    console.print(f"[bold red]FAILED:[/] {cmd}")
                else:
                    console.print(f"[bold green]PASS:[/] {cmd}")
    
    # Enforce test coverage if configured
    if min_coverage is not None:
        console.print(f"Checking test coverage against minimum threshold: {min_coverage}%")
        try:
            from niyam.core.coverage import find_and_parse_coverage
            cov_result = find_and_parse_coverage(repo_root)
            if cov_result:
                actual_coverage = cov_result["percentage"]
                if actual_coverage < min_coverage:
                    success = False
                    console.print(f"[bold red]FAILED:[/] Test coverage ({actual_coverage}%) is below the configured minimum threshold ({min_coverage}%).")
                    validation_results.append({
                        "name": "coverage", 
                        "command": "internal_coverage_check", 
                        "success": False, 
                        "error": f"Coverage {actual_coverage}% < {min_coverage}%"
                    })
                else:
                    console.print(f"[bold green]PASS:[/] Test coverage ({actual_coverage}%) meets the minimum threshold ({min_coverage}%).")
                    validation_results.append({
                        "name": "coverage", 
                        "command": "internal_coverage_check", 
                        "success": True, 
                        "details": f"Coverage: {actual_coverage}%"
                    })
            else:
                success = False
                console.print(f"[bold red]FAILED:[/] Minimum test coverage is configured ({min_coverage}%), but no coverage report could be found.")
                validation_results.append({
                    "name": "coverage", 
                    "command": "internal_coverage_check", 
                    "success": False, 
                    "error": "Coverage report not found"
                })
        except Exception as e:
            console.print(f"[yellow]Warning: Error checking test coverage:[/] {e}")

    if validation_results:
        task_dir = run_dir / "tasks" / task_id
        task_dir.mkdir(parents=True, exist_ok=True)
        (task_dir / "manual_validation.json").write_text(json.dumps(validation_results, indent=2), encoding="utf-8")

    if success:
        console.print(f"\n[bold green]✓ Task {task_id} validation PASSED.[/]")
    else:
        console.print(f"\n[bold red]❌ Task {task_id} validation FAILED.[/]")
        raise SystemExit(1)
