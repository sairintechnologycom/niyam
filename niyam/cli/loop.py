"""CLI commands for Niyam LoopOps."""

from __future__ import annotations

import sys
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
        Path,
        typer.Argument(
            help="Path to the LoopSpec YAML file.",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
        ),
    ],
    scenario: Annotated[
        str,
        typer.Option(
            "--scenario",
            "-s",
            help="Simulation scenario to execute.",
        ),
    ] = "success",
) -> None:
    """Simulate running a loop specification with mock execution steps."""
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
    if scenario not in valid_scenarios:
        console.print(f"[bold red]Error:[/] Invalid scenario '{scenario}'. Choose from: {', '.join(valid_scenarios)}")
        raise typer.Exit(1)

    # Generate steps_data based on scenario
    steps_data: list[dict[str, Any]] = []
    if scenario == "success":
        steps_data = [
            {"status": "success", "cost_usd": 0.45},
            {"status": "passed", "cost_usd": 0.40},
        ]
    elif scenario == "budget-iterations":
        steps_data = [{"status": "success", "cost_usd": 0.20} for _ in range(spec.budgets.max_iterations + 1)]
    elif scenario == "budget-cost":
        steps_data = [
            {"status": "success", "cost_usd": 2.50},
            {"status": "success", "cost_usd": 1.20},
        ]
    elif scenario == "stop-failures":
        steps_data = [
            {"status": "failure", "error": "Error A", "cost_usd": 0.15},
            {"status": "failure", "error": "Error B", "cost_usd": 0.15},
            {"status": "failure", "error": "Error C", "cost_usd": 0.15},
        ]
    elif scenario == "stop-errors":
        steps_data = [
            {"status": "failure", "error": "ConnectionRefusedError", "cost_usd": 0.15},
            {"status": "failure", "error": "ConnectionRefusedError", "cost_usd": 0.15},
        ]
    elif scenario == "approval":
        steps_data = [
            {"status": "success", "cost_usd": 0.50},
            {"status": "success", "human_approval_required": True, "cost_usd": 0.50},
        ]

    # Initialize LoopRun
    run = LoopRunner.initialize_run(spec)

    # Run the simulation loop
    reason = None
    idx = 0
    while run.status in ("pending", "running") and idx < len(steps_data):
        step_result = steps_data[idx]
        reason = LoopRunner.process_step_result(run, spec, step_result)
        idx += 1

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
    if scenario == "approval":
        reason_str = "Modified authentication middleware"

    console.print("Niyam LoopOps\n")
    console.print(f"Loop: {spec.metadata.name}")
    console.print(f"Status: {status_upper}")
    console.print(f"Iterations: {run.iteration_count}/{spec.budgets.max_iterations}")
    console.print(f"Cost: ${run.cost_usd:.2f} / {max_cost_str}")
    console.print(f"Risk: {risk_str}")
    console.print(f"Reason: {reason_str}\n")
    console.print("Evidence Pack:")
    console.print(run.evidence_path)


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
