"""CLI commands for Niyam LoopOps."""

from __future__ import annotations

import sys
import subprocess
from pathlib import Path
from typing import Annotated, Optional

import typer
from datetime import datetime, timezone
import json
import yaml
from rich.console import Console

from niyam.cli import console, loop_app
from niyam.core.security import safe_load_yaml
from niyam.core.config import find_niyam_root
from niyam.core.loopops import (
    validate_loop_spec,
    generate_starter_spec,
    LoopSpec,
    LoopRunner,
    LoopRun,
)


@loop_app.command(name="init")
def loop_init(
    name: Annotated[
        str,
        typer.Option(
            "--name",
            "-n",
            help="Name of the loop specification.",
        ),
    ] = "my-loop",
    type: Annotated[
        str,
        typer.Option(
            "--type",
            "-t",
            help="Type of the loop goal (e.g. code-change).",
        ),
    ] = "code-change",
) -> None:
    """Generate a starter LoopSpec YAML file."""
    yaml_content = generate_starter_spec(name=name, goal_type=type)
    # Output to stdout directly for piping or verification
    sys.stdout.write(yaml_content)


@loop_app.command(name="validate")
def loop_validate(
    file: Annotated[
        Path,
        typer.Argument(
            help="Path to the LoopSpec YAML file.",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
        ),
    ],
) -> None:
    """Validate a LoopSpec YAML file against schema and semantic rules."""
    try:
        data = safe_load_yaml(file)
    except Exception as e:
        console.print(f"[bold red]FAIL:[/] LoopSpec YAML parsing failed: {e}")
        raise typer.Exit(1)

    errors = validate_loop_spec(data)

    if errors:
        console.print("[bold red]FAIL:[/] LoopSpec validation failed.")
        console.print("[bold red]Errors:[/]")
        for err in errors:
            console.print(f"  • {err}")
        raise typer.Exit(1)

    # Check for configuration drift
    from niyam.core.loopops.validate import check_runtime_drift
    drift_warnings = check_runtime_drift(find_niyam_root() or Path.cwd())
    for warning in drift_warnings:
        console.print(f"[bold yellow]WARNING:[/] {warning}")

    # Valid specification print summary
    spec_name = data.get("metadata", {}).get("name", "Unknown")
    owner = data.get("metadata", {}).get("owner", "Unknown")
    goal = data.get("goal", {})
    goal_type = goal.get("type", "Unknown")
    goal_desc = goal.get("description", "Unknown")
    actors = ", ".join(f"{k}:{v}" for k, v in data.get("actors", {}).items())
    steps = ", ".join(s.get("name", "Unnamed") for s in data.get("steps", []))
    max_iter = data.get("budgets", {}).get("maxIterations", "Unknown")

    console.print(f"[bold green]PASS:[/] LoopSpec '{spec_name}' is valid.")
    console.print("[bold cyan]Summary:[/]")
    console.print(f"  Name: {spec_name}")
    console.print(f"  Owner: {owner}")
    console.print(f"  Goal: {goal_type} - {goal_desc}")
    if actors:
        console.print(f"  Actors: {actors}")
    if steps:
        console.print(f"  Steps: {steps}")
    console.print(f"  Max Iterations: {max_iter}")


@loop_app.command(name="run")
def loop_run(
    file: Annotated[
        Optional[Path],
        typer.Argument(
            help="Path to the LoopSpec YAML file.",
            file_okay=True,
            dir_okay=False,
            readable=True,
        ),
    ] = None,
    scenario: Annotated[
        Optional[str],
        typer.Option(
            "--scenario",
            "-s",
            help="Simulation scenario to execute.",
        ),
    ] = None,
    planner: Annotated[
        Optional[str],
        typer.Option(
            "--planner",
            help="Override planner tool (claude, codex, gemini, etc.)",
        ),
    ] = None,
    implementer: Annotated[
        Optional[str],
        typer.Option(
            "--implementer",
            help="Override implementer tool (claude, codex, gemini, etc.)",
        ),
    ] = None,
    reviewer: Annotated[
        Optional[str],
        typer.Option(
            "--reviewer",
            help="Override reviewer tool (claude, codex, gemini, etc.)",
        ),
    ] = None,
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            help="Simulate planning/actions without making changes.",
        ),
    ] = False,
    mode: Annotated[
        str,
        typer.Option(
            "--mode",
            help="Execution mode (governed, autonomous).",
        ),
    ] = "governed",
    require_approval_on: Annotated[
        str,
        typer.Option(
            "--require-approval-on",
            help="When to require human approval (high-risk, any, none).",
        ),
    ] = "high-risk",
    max_iterations: Annotated[
        Optional[int],
        typer.Option(
            "--max-iterations",
            help="Override maximum execution iterations.",
        ),
    ] = None,
    max_cost_usd: Annotated[
        Optional[float],
        typer.Option(
            "--max-cost-usd",
            help="Override maximum token cost budget (USD).",
        ),
    ] = None,
    replay: Annotated[
        Optional[str],
        typer.Option(
            "--replay",
            help="Replay a loop run from signed evidence.",
        ),
    ] = None,
    fleet: Annotated[
        bool,
        typer.Option(
            "--fleet",
            help="Run loop across all registered repositories in fleet.",
        ),
    ] = False,
) -> None:
    """Run a loop specification governed by Niyam LoopOps."""
    if replay:
        # Replay mode
        replay_path = Path(replay)
        if replay_path.exists():
            if replay_path.is_file() and replay_path.name == "run.json":
                run_dir = replay_path.parent
            elif replay_path.is_dir():
                run_dir = replay_path
            else:
                run_dir = None
        else:
            run_dir = _find_loop_run_evidence_dir(replay)

        if not run_dir or not (run_dir / "run.json").exists():
            console.print(f"[bold red]FAIL:[/] Could not locate evidence run.json for replay: {replay}")
            raise typer.Exit(1)

        try:
            run, reason = LoopRunner.replay_loop(run_dir)
        except Exception as e:
            console.print(f"[bold red]FAIL:[/] Replay failed: {e}")
            raise typer.Exit(1)

        status_map = {
            "pending": "PENDING",
            "running": "RUNNING",
            "evaluating": "EVALUATING",
            "passed": "PASSED",
            "failed": "FAILED",
            "stopped": "STOPPED",
            "requires_approval": "STOPPED_FOR_APPROVAL",
        }
        status_upper = status_map.get(run.status, run.status.upper())
        max_cost_str = f"${run.max_cost_usd:.2f}" if run.max_cost_usd is not None else "N/A"

        console.print("Niyam LoopOps (Replay)\n")
        console.print(f"Loop: {run.spec_name}")
        console.print(f"Status: {status_upper}")
        console.print(f"Iterations: {run.iteration_count}/{run.max_iterations}")
        console.print(f"Cost: ${run.cost_usd:.2f} / {max_cost_str}")
        console.print(f"Risk: {run.risk_level.capitalize()}")
        console.print(f"Reason: {reason or 'Completed.'}\n")
        console.print("Evidence Pack:")
        console.print(str(run_dir))

        iterations_dir = run_dir / "iterations"
        if iterations_dir.is_dir():
            console.print("\nPlayed back iterations:")
            for iter_file in sorted(iterations_dir.glob("*.json")):
                try:
                    with open(iter_file, encoding="utf-8") as f:
                        iter_data = json.load(f)
                    idx = iter_data.get("index", 0)
                    actor = iter_data.get("actor", "unknown")
                    step_name = iter_data.get("stepName", "unknown")
                    result = iter_data.get("result", "unknown")
                    console.print(f"  Iteration {idx}: {step_name} ({actor}) -> {result.upper()}")
                except Exception:
                    pass
        return

    if not file:
        console.print("[bold red]FAIL:[/] LoopSpec YAML file is required when not in replay mode.")
        raise typer.Exit(1)

    if not file.exists() or not file.is_file():
        console.print(f"[bold red]FAIL:[/] LoopSpec file does not exist: {file}")
        raise typer.Exit(1)

    try:
        data = safe_load_yaml(file)
    except Exception as e:
        console.print(f"[bold red]FAIL:[/] LoopSpec YAML parsing failed: {e}")
        raise typer.Exit(1)

    errors = validate_loop_spec(data)
    if errors:
        console.print("[bold red]FAIL:[/] LoopSpec validation failed.")
        console.print("[bold red]Errors:[/]")
        for err in errors:
            console.print(f"  • {err}")
        raise typer.Exit(1)

    # Convert to Pydantic object
    spec = LoopSpec.model_validate(data)

    # Scenarios list validation
    valid_scenarios = [
        "success",
        "budget-iterations",
        "budget-cost",
        "stop-failures",
        "stop-errors",
        "approval",
    ]
    if scenario is not None and scenario not in valid_scenarios:
        console.print(f"[bold red]Error:[/] Invalid scenario '{scenario}'. Choose from: {', '.join(valid_scenarios)}")
        raise typer.Exit(1)

    # Override actors if specified
    if planner:
        spec.actors["planner"] = planner
    if implementer:
        spec.actors["implementer"] = implementer
    if reviewer:
        spec.actors["reviewer"] = reviewer

    # Override budgets if specified
    if max_iterations is not None:
        spec.budgets.max_iterations = max_iterations
    if max_cost_usd is not None:
        spec.budgets.max_cost_usd = max_cost_usd

    # Fleet Wave Execution
    if fleet:
        from niyam.core.fleet import load_fleet_config, resolve_fleet_dependencies
        from concurrent.futures import ThreadPoolExecutor
        from copy import deepcopy

        root = find_niyam_root() or Path.cwd()

        # Check configuration drift first
        from niyam.core.loopops.validate import check_runtime_drift
        drift_warnings = check_runtime_drift(root)
        for warning in drift_warnings:
            console.print(f"[bold yellow]WARNING:[/] {warning}")

        fleet_config = load_fleet_config()
        repos = fleet_config.repos
        if not repos:
            from niyam.core.fleet import discover_repos
            discover_repos(root)
            fleet_config = load_fleet_config()
            repos = fleet_config.repos

        if not repos:
            console.print("[bold red]Error:[/] No repositories registered in fleet. Run `niyam fleet register` first.")
            raise typer.Exit(1)

        # Resolve dependencies
        waves = resolve_fleet_dependencies(repos)

        # Parallel waves execution
        for wave_idx, wave in enumerate(waves):
            console.print(f"\n[bold cyan]Executing Fleet Wave {wave_idx + 1}/{len(waves)}...[/]")
            with ThreadPoolExecutor(max_workers=len(wave)) as executor:
                def run_for_repo(repo):
                    repo_path = Path(repo.path)
                    repo_spec = deepcopy(spec)
                    run_obj, reason_msg = LoopRunner.run_loop(
                        spec=repo_spec,
                        scenario=scenario,
                        dry_run=dry_run,
                        mode=mode,
                        require_approval_on=require_approval_on,
                        repo_root=repo_path,
                    )
                    return repo.alias, run_obj, reason_msg

                futures = [executor.submit(run_for_repo, repo) for repo in wave]
                for fut in futures:
                    alias, run, reason = fut.result()

                    status_map = {
                        "pending": "PENDING",
                        "running": "RUNNING",
                        "evaluating": "EVALUATING",
                        "passed": "PASSED",
                        "failed": "FAILED",
                        "stopped": "STOPPED",
                        "requires_approval": "STOPPED_FOR_APPROVAL",
                    }
                    status_upper = status_map.get(run.status, run.status.upper())
                    max_cost_str = f"${spec.budgets.max_cost_usd:.2f}" if spec.budgets.max_cost_usd is not None else "N/A"
                    risk_str = run.risk_level.capitalize()
                    if run.status == "requires_approval" and run.risk_level != "high":
                        risk_str = f"{risk_str} → High"
                    reason_str = reason or "No reason provided."

                    console.print(f"\n[bold green]Repo: {alias}[/]")
                    console.print(f"Loop: {spec.metadata.name}")
                    console.print(f"Status: {status_upper}")
                    console.print(f"Iterations: {run.iteration_count}/{spec.budgets.max_iterations}")
                    console.print(f"Cost: ${run.cost_usd:.2f} / {max_cost_str}")
                    console.print(f"Risk: {risk_str}")
                    console.print(f"Reason: {reason_str}")
                    console.print("Evidence Pack:")
                    console.print(run.evidence_path)
        return

    # Normal execution path: Check configuration drift first
    from niyam.core.loopops.validate import check_runtime_drift
    drift_warnings = check_runtime_drift(find_niyam_root() or Path.cwd())
    for warning in drift_warnings:
        console.print(f"[bold yellow]WARNING:[/] {warning}")

    # Execute Loop
    run, reason = LoopRunner.run_loop(
        spec=spec,
        scenario=scenario,
        dry_run=dry_run,
        mode=mode,
        require_approval_on=require_approval_on,
    )


    # Format output
    status_map = {
        "pending": "PENDING",
        "running": "RUNNING",
        "evaluating": "EVALUATING",
        "passed": "PASSED",
        "failed": "FAILED",
        "stopped": "STOPPED",
        "requires_approval": "STOPPED_FOR_APPROVAL",
    }
    status_upper = status_map.get(run.status, run.status.upper())

    max_cost_str = f"${spec.budgets.max_cost_usd:.2f}" if spec.budgets.max_cost_usd is not None else "N/A"

    risk_str = run.risk_level.capitalize()
    if run.status == "requires_approval" and run.risk_level != "high":
        risk_str = f"{risk_str} → High"

    reason_str = reason or "No reason provided."

    console.print("Niyam LoopOps\n")
    console.print(f"Loop: {spec.metadata.name}")
    console.print(f"Status: {status_upper}")
    console.print(f"Iterations: {run.iteration_count}/{spec.budgets.max_iterations}")
    console.print(f"Cost: ${run.cost_usd:.2f} / {max_cost_str}")
    console.print(f"Risk: {risk_str}")
    console.print(f"Reason: {reason_str}\n")
    console.print("Evidence Pack:")
    console.print(run.evidence_path)


@loop_app.command(name="review")
def loop_review(
    diff: Annotated[
        str,
        typer.Option(
            "--diff",
            help="Diff to review (e.g. current or a patch path).",
        ),
    ] = "current",
    reviewer: Annotated[
        str,
        typer.Option(
            "--reviewer",
            help="Reviewer tool to use (gemini, claude, etc.).",
        ),
    ] = "gemini",
    policy: Annotated[
        Optional[Path],
        typer.Option(
            "--policy",
            help="Path to the policy YAML file.",
            file_okay=True,
            dir_okay=False,
            readable=True,
        ),
    ] = None,
) -> None:
    """Review a diff using a chosen reviewer and policy rules."""
    from niyam.core.loopops.adapters import get_adapter, AgentTaskRequest
    from niyam.core.config import find_niyam_root

    root = find_niyam_root() or Path.cwd()
    diff_content = ""
    if diff == "current":
        # Get git diff
        try:
            res = subprocess.run(
                ["git", "diff"],
                cwd=root,
                capture_output=True,
                text=True,
            )
            diff_content = res.stdout
        except Exception:
            pass
    else:
        diff_path = Path(diff)
        if diff_path.exists():
            diff_content = diff_path.read_text(encoding="utf-8")

    console.print(f"Niyam LoopOps: Reviewing diff via {reviewer} with policy {policy}...\n")
    
    # Resolve reviewer adapter
    adapter = get_adapter(reviewer)
    req = AgentTaskRequest(
        goal=f"Review the following diff for missing edge cases, design compliance, and vulnerabilities:\n\n{diff_content}",
        workspace_path=root,
        action="review_diff",
        step_name="review",
    )
    result = adapter.review(req)
    
    console.print(f"Status: {result.status.upper()}")
    console.print(f"Summary: {result.summary}")
    if result.risk_flags:
        console.print(f"Risk Flags: {', '.join(result.risk_flags)}")
    if result.cost_usd:
        console.print(f"Estimated Cost: ${result.cost_usd:.4f}")


def _find_loop_run_evidence_dir(loop_id: str) -> Optional[Path]:
    """Search for the evidence directory for a given LoopRun ID."""
    root = find_niyam_root() or Path.cwd()
    loops_dir = root / ".niyam" / "evidence" / "loops"
    if not loops_dir.is_dir():
        # Fallback to .sutra
        loops_dir = root / ".sutra" / "evidence" / "loops"
        if not loops_dir.is_dir():
            return None

    # Walk through all directories under loops_dir
    for p in loops_dir.glob("**/run.json"):
        try:
            with open(p, encoding="utf-8") as f:
                run_data = json.load(f)
            if run_data.get("id") == loop_id:
                return p.parent
        except Exception:
            pass
    return None


@loop_app.command(name="report")
def loop_report(
    loop_id: Annotated[
        str,
        typer.Argument(help="The Unique ID of the LoopRun (e.g. LR-XXXXXX)."),
    ],
    format: Annotated[
        str,
        typer.Option(
            "--format",
            "-f",
            help="Output format (markdown, html).",
        ),
    ] = "markdown",
    output: Annotated[
        Optional[Path],
        typer.Option(
            "--output",
            "-o",
            help="Path to write the report file.",
            dir_okay=False,
            writable=True,
        ),
    ] = None,
) -> None:
    """Generate or retrieve a report for a specific LoopRun from evidence."""
    # Find the run directory
    run_dir = _find_loop_run_evidence_dir(loop_id)
    if not run_dir:
        console.print(f"[bold red]Error:[/] LoopRun with ID '{loop_id}' not found in evidence.")
        raise typer.Exit(1)

    if format not in ("markdown", "html"):
        console.print(f"[bold red]Error:[/] Invalid format '{format}'. Use 'markdown' or 'html'.")
        raise typer.Exit(1)

    run_path = run_dir / "run.json"
    spec_path = run_dir / "loop-spec.yaml"
    if not run_path.exists() or not spec_path.exists():
        console.print(f"[bold red]Error:[/] Run data or spec file is missing in {run_dir}.")
        raise typer.Exit(1)

    try:
        with open(run_path, encoding="utf-8") as f:
            run_data = json.load(f)
        with open(spec_path, encoding="utf-8") as f:
            spec_data = safe_load_yaml(spec_path)

        spec = LoopSpec.model_validate(spec_data)
        run = LoopRun.model_validate(run_data)
    except Exception as e:
        console.print(f"[bold red]Error:[/] Failed to parse run or spec data: {e}")
        raise typer.Exit(1)

    report_md = ""
    report_md_path = run_dir / "report.md"
    if report_md_path.exists():
        report_md = report_md_path.read_text(encoding="utf-8")
    else:
        # Generate on the fly
        reason_msg = "Completed."
        report_md = LoopRunner.generate_report_markdown(run, spec, reason_msg)

    if format == "markdown":
        report_content = report_md
    else:
        report_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Niyam LoopOps Report: {run.spec_name}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 40px auto;
            padding: 0 20px;
            color: #333;
        }}
        h1, h2, h3 {{ color: #111; }}
        code {{
            background: #f4f4f4;
            padding: 2px 5px;
            border-radius: 3px;
            font-family: monospace;
        }}
        pre {{
            background: #f4f4f4;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
        }}
        ul {{ padding-left: 20px; }}
    </style>
</head>
<body>
    <h1>Niyam LoopOps Report: {run.spec_name}</h1>
    <pre>{report_md}</pre>
</body>
</html>
"""

    if output:
        try:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(report_content, encoding="utf-8")
            console.print(f"[bold green]PASS:[/] Report written to {output}")
        except Exception as e:
            console.print(f"[bold red]Error:[/] Failed to write output: {e}")
            raise typer.Exit(1)
    else:
        sys.stdout.write(report_content)


@loop_app.command(name="evidence")
def loop_evidence(
    loop_id: Annotated[
        str,
        typer.Argument(help="The Unique ID of the LoopRun (e.g. LR-XXXXXX)."),
    ],
    bundle: Annotated[
        Path,
        typer.Option(
            "--bundle",
            "-b",
            help="Path to save the zipped evidence bundle (e.g. my_bundle.zip).",
            dir_okay=False,
            writable=True,
        ),
    ],
) -> None:
    """Package the evidence directory of a LoopRun into a zip archive."""
    run_dir = _find_loop_run_evidence_dir(loop_id)
    if not run_dir:
        console.print(f"[bold red]Error:[/] LoopRun with ID '{loop_id}' not found in evidence.")
        raise typer.Exit(1)

    bundle_str = str(bundle)
    if bundle_str.lower().endswith(".zip"):
        base_name = bundle_str[:-4]
    else:
        base_name = bundle_str

    try:
        import shutil
        bundle.parent.mkdir(parents=True, exist_ok=True)
        shutil.make_archive(base_name, "zip", root_dir=str(run_dir))
        console.print(f"[bold green]PASS:[/] Evidence bundle created at {base_name}.zip")
    except Exception as e:
        console.print(f"[bold red]Error:[/] Failed to create bundle: {e}")
        raise typer.Exit(1)
