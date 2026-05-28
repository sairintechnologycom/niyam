"""Sutra mission planner — generate mission plans from requirements."""

from __future__ import annotations

from datetime import datetime
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
import yaml
from rich.console import Console

from sutra.core.config import get_sutra_dir, load_sutra_config


def get_repo_map(repo_root: Path) -> str:
    """List project files up to 1000 files for AI context."""
    if (repo_root / ".git").exists():
        res = subprocess.run(
            ["git", "ls-files"],
            cwd=repo_root,
            capture_output=True,
            text=True,
        )
        if res.returncode == 0:
            return res.stdout.strip()

    files = []
    ignore_dirs = {".git", ".sutra", "__pycache__", ".venv", ".pytest_cache", "node_modules", "build", "dist", ".antigravitycli"}
    for root, dirs, filenames in os.walk(repo_root):
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        for f in filenames:
            rel = os.path.relpath(Path(root) / f, repo_root)
            files.append(rel)
            if len(files) >= 1000:
                break
        if len(files) >= 1000:
            break
    return "\n".join(files)


def extract_yaml_or_json(text: str) -> dict | None:
    """Extract and parse YAML or JSON block from text."""
    # Try looking for ```yaml ... ```
    yaml_block = re.search(r"```(?:yaml|yml)?\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
    if yaml_block:
        try:
            parsed = yaml.safe_load(yaml_block.group(1))
            if isinstance(parsed, dict) and "tasks" in parsed:
                return parsed
        except Exception:
            pass

    # Try looking for ```json ... ```
    json_block = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
    if json_block:
        try:
            parsed = json.loads(json_block.group(1))
            if isinstance(parsed, dict) and "tasks" in parsed:
                return parsed
        except Exception:
            pass

    # Try parsing the whole text as YAML
    try:
        data = yaml.safe_load(text)
        if isinstance(data, dict) and "tasks" in data:
            return data
    except Exception:
        pass

    return None


def build_planner_prompt(requirement: str, repo_map: str, available_agents: list[str]) -> str:
    agents_str = ", ".join(available_agents)
    return f"""You are the Sutra planning engine.
Convert the following requirement into a bounded, dependency-resolved task plan.
Each task must be small, bounded, and assigned to a specific agent from the available agents in the workspace.

Available Agents in this workspace:
{agents_str}

Repository Structure (File Map):
{repo_map}

Requirement to implement:
{requirement}

Instructions:
1. Break down the requirement into a list of tasks.
2. The tasks must be ordered logically. Any task depending on another task must list it in `depends_on`.
3. Assign each task to the most appropriate agent from the list of Available Agents. For example, assign development to 'backend-specialist' or 'frontend-specialist', code review to 'security-reviewer', and verification/testing to 'qa-reviewer'.
4. Ensure the first task is a discovery/analysis task, and the last task is a validation task.
5. Return ONLY a valid YAML block matching the schema below. Do not output any markdown prose, chat, warnings, or explanation. Only output the YAML inside ```yaml code fences.

YAML Schema:
```yaml
tasks:
  - id: T1
    title: "Discovery: analyze requirements and code structure"
    type: "discovery"
    agent: "{available_agents[0]}"
    writes_files: false
  - id: T2
    title: "Implementation: write failing tests"
    type: "implementation"
    agent: "{available_agents[0]}"
    depends_on: ["T1"]
    files_allowed: ["tests/**"]
  - id: T3
    title: "Implementation: implement the feature changes"
    type: "implementation"
    agent: "{available_agents[0]}"
    depends_on: ["T2"]
    files_allowed: ["*"]
  - id: T4
    title: "Review: security check"
    type: "review"
    agent: "{available_agents[0]}"
    depends_on: ["T3"]
    writes_files: false
  - id: T5
    title: "Validation: verify all tests pass"
    type: "validation"
    agent: "{available_agents[0]}"
    depends_on: ["T4"]
```
"""


def run_mission_plan(requirements_path: str, strict: bool = False, console: Console = None) -> str:
    """Generate a mission plan from a requirements file."""
    if console is None:
        console = Console()
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

    backend_agent = "backend-specialist" if "backend-specialist" in available_agents else available_agents[0]
    security_agent = "security-reviewer" if "security-reviewer" in available_agents else available_agents[0]
    qa_agent = "qa-reviewer" if "qa-reviewer" in available_agents else available_agents[0]

    plan_data = None
    
    # 5. Try AI planning if not in basic unit tests
    is_test = (os.environ.get("SUTRA_TEST") == "1" or "pytest" in sys.modules) and os.environ.get("SUTRA_TEST_PLANNER") != "1"
    config = None
    try:
        config = load_sutra_config(repo_root)
    except Exception:
        pass

    if config and not is_test:
        orchestrator = config.runtimes[0] if config.runtimes else "claude"
        if shutil.which(orchestrator):
            requirement_content = req_file.read_text(encoding="utf-8")
            repo_map = get_repo_map(repo_root)
            prompt = build_planner_prompt(requirement_content, repo_map, available_agents)
            
            # Write prompt for trace
            (run_dir / "planner-prompt.md").write_text(prompt, encoding="utf-8")
            
            console.print(f"[dim]Invoking AI planning engine '{orchestrator}'...[/]")
            cmd = [orchestrator, "-p", prompt]
            if orchestrator == "gemini":
                cmd.append("--skip-trust")
                
            try:
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
                raw_output = (res.stdout or "") + "\n" + (res.stderr or "")
                (run_dir / "planner-output.raw.txt").write_text(raw_output, encoding="utf-8")
                
                if res.returncode == 0:
                    parsed = extract_yaml_or_json(raw_output)
                    if parsed and isinstance(parsed, dict) and "tasks" in parsed:
                        tasks = parsed["tasks"]
                        normalized_tasks = []
                        for i, t in enumerate(tasks, start=1):
                            t_id = t.get("id") or f"T{i}"
                            t_title = t.get("title") or f"Task {t_id}"
                            t_type = t.get("type") or "implementation"
                            t_agent = t.get("agent")
                            if t_agent not in available_agents:
                                t_agent = available_agents[0]
                            t_deps = t.get("depends_on", [])
                            if isinstance(t_deps, str):
                                t_deps = [t_deps]
                            elif not isinstance(t_deps, list):
                                t_deps = []
                            t_writes = t.get("writes_files")
                            if t_writes is None:
                                t_writes = t_type == "implementation"
                            t_files = t.get("files_allowed") or ["*"]
                            if isinstance(t_files, str):
                                t_files = [t_files]
                            normalized_tasks.append({
                                "id": t_id,
                                "title": t_title,
                                "type": t_type,
                                "status": "pending",
                                "agent": t_agent,
                                "depends_on": t_deps,
                                "writes_files": t_writes,
                                "files_allowed": t_files,
                            })
                        plan_data = {
                            "mission": {
                                "id": mission_id,
                                "requirement": str(requirements_path),
                                "created": datetime.utcnow().isoformat() + "Z",
                                "status": "planned",
                                "orchestrator": orchestrator,
                                "parallel": 1,
                            },
                            "tasks": normalized_tasks
                        }
                        console.print(f"[bold green]✓[/] AI generated a custom task plan with {len(normalized_tasks)} tasks.")
            except Exception as e:
                console.print(f"[yellow]Warning:[/] AI planner execution encountered an error: {e}")

    # Fallback to static template plan
    if not plan_data:
        if strict:
            console.print("[bold red]Error:[/] AI-powered planning failed and strict planning was requested.")
            raise SystemExit(1)
        console.print("[yellow]AI planner fallback: generating standard static template plan.[/]")
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
                    "title": "Discovery: Analyze requirement in requirement.md",
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
