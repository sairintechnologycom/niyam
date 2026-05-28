"""Sutra mission planner — generate mission plans from requirements."""

from __future__ import annotations

from datetime import datetime
import shutil
from pathlib import Path
import yaml
from rich.console import Console

from sutra.core.config import get_sutra_dir, load_sutra_config


def run_mission_plan(requirements_path: str, console: Console) -> str:
    """Generate a mission plan from a requirements file."""
    repo_root = Path.cwd()
    sutra_dir = get_sutra_dir(repo_root)

    if not sutra_dir.exists():
        console.print("[bold red]Error:[/] Not a Sutra workspace. Run `sutra init` first.")
        raise SystemExit(1)

    req_file = Path(requirements_path)
    if not req_file.exists():
        console.print(f"[bold red]Error:[/] Requirements file '{requirements_path}' not found.")
        raise SystemExit(1)

    # 1. Generate unique mission ID
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    clean_name = "".join(c if c.isalnum() else "-" for c in req_file.stem).strip("-")
    mission_id = f"{clean_name}-{timestamp}"

    # 2. Create runs directory
    run_dir = sutra_dir / "runs" / mission_id
    run_dir.mkdir(parents=True, exist_ok=True)

    # 3. Copy requirements file
    shutil.copy2(req_file, run_dir / "requirement.md")

    # 4. Determine available agents
    agents_dir = sutra_dir / "agents"
    available_agents = []
    if agents_dir.is_dir():
        available_agents = [f.stem for f in agents_dir.glob("*.md")]
    
    if not available_agents:
        available_agents = ["default-agent"]

    # Select best match agents
    backend_agent = "backend-specialist" if "backend-specialist" in available_agents else available_agents[0]
    security_agent = "security-reviewer" if "security-reviewer" in available_agents else available_agents[0]
    qa_agent = "qa-reviewer" if "qa-reviewer" in available_agents else available_agents[0]

    # 5. Build mission plan template
    plan_data = {
        "mission": {
            "id": mission_id,
            "requirement": str(requirements_path),
            "created": datetime.utcnow().isoformat() + "Z",
            "status": "planned",
            "orchestrator": "claude",
            "parallel": 1,
        },
        "tasks": [
            {
                "id": "T1",
                "title": f"Discovery: Analyze requirement in requirement.md",
                "type": "discovery",
                "status": "pending",
                "agent": backend_agent,
                "writes_files": False,
            },
            {
                "id": "T2",
                "title": "TDD: Write failing test cases",
                "type": "implementation",
                "status": "pending",
                "agent": backend_agent,
                "depends_on": ["T1"],
                "tdd_required": True,
                "files_allowed": ["tests/**"],
            },
            {
                "id": "T3",
                "title": "Implementation: Code the solution",
                "type": "implementation",
                "status": "pending",
                "agent": backend_agent,
                "depends_on": ["T2"],
                "files_allowed": ["*"],
            },
            {
                "id": "T4",
                "title": "Security: Review changes for vulnerabilities",
                "type": "review",
                "status": "pending",
                "agent": security_agent,
                "depends_on": ["T3"],
                "writes_files": False,
            },
            {
                "id": "T5",
                "title": "Validation: Run full verification suite",
                "type": "validation",
                "status": "pending",
                "agent": qa_agent,
                "depends_on": ["T4"],
            }
        ]
    }

    # Write mission-plan.yaml
    plan_path = run_dir / "mission-plan.yaml"
    with open(plan_path, "w", encoding="utf-8") as f:
        yaml.dump(plan_data, f, default_flow_style=False, sort_keys=False)

    # Write task-list.yaml
    tasks_path = run_dir / "task-list.yaml"
    with open(tasks_path, "w", encoding="utf-8") as f:
        yaml.dump(plan_data["tasks"], f, default_flow_style=False, sort_keys=False)

    # Initialize approval.json
    approval_path = run_dir / "approval.json"
    approval_path.write_text('{"approved": false}', encoding="utf-8")

    # Initialize execution-log.json and policy-events.json
    (run_dir / "execution-log.json").write_text("[]", encoding="utf-8")
    (run_dir / "policy-events.json").write_text("[]", encoding="utf-8")

    console.print(f"[bold green]✓[/] Created mission plan '[cyan]{mission_id}[/]' in .sutra/runs/{mission_id}/")
    return mission_id


def get_latest_mission_id(sutra_dir: Path) -> str | None:
    """Find the latest mission run directory."""
    runs_dir = sutra_dir / "runs"
    if not runs_dir.exists():
        return None
    runs = [d for d in runs_dir.iterdir() if d.is_dir()]
    if not runs:
        return None
    # Sort by directory creation/modification time
    runs.sort(key=lambda d: d.stat().st_mtime, reverse=True)
    return runs[0].name


def run_mission_approve(console: Console) -> None:
    """Approve the latest planned mission."""
    repo_root = Path.cwd()
    sutra_dir = get_sutra_dir(repo_root)

    mission_id = get_latest_mission_id(sutra_dir)
    if not mission_id:
        console.print("[bold red]Error:[/] No missions found.")
        raise SystemExit(1)

    run_dir = sutra_dir / "runs" / mission_id
    plan_path = run_dir / "mission-plan.yaml"

    if not plan_path.exists():
        console.print(f"[bold red]Error:[/] Mission plan for '{mission_id}' not found.")
        raise SystemExit(1)

    with open(plan_path, encoding="utf-8") as f:
        plan_data = yaml.safe_load(f) or {}

    mission_meta = plan_data.get("mission", {})
    status = mission_meta.get("status", "planned")

    if status != "planned":
        console.print(f"[yellow]Mission '{mission_id}' is already {status}.[/]")
        return

    # Update status to approved
    plan_data["mission"]["status"] = "approved"
    with open(plan_path, "w", encoding="utf-8") as f:
        yaml.dump(plan_data, f, default_flow_style=False, sort_keys=False)

    # Write approval.json
    approval_path = run_dir / "approval.json"
    approval_data = {
        "approved": True,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    import json
    approval_path.write_text(json.dumps(approval_data, indent=2), encoding="utf-8")

    console.print(f"[bold green]✓[/] Mission '[cyan]{mission_id}[/]' has been approved and is ready to start.")
