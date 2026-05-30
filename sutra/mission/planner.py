"""Sutra mission planner — generate mission plans from requirements."""

from __future__ import annotations

from datetime import datetime, timezone
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
4. Optionally, you can assign a custom execution `runtime` (such as `claude`, `gemini`, or `codex`) to a task if a specific runtime is better suited for it (e.g. `gemini` for coding, `codex` for scripting). If omitted, the task will use the default global runtime.
5. Ensure the first task is a discovery/analysis task, and the last task is a validation task.
6. Return ONLY a valid YAML block matching the schema below. Do not output any markdown prose, chat, warnings, or explanation. Only output the YAML inside ```yaml code fences.

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
    runtime: "claude"
    depends_on: ["T1"]
    files_allowed: ["tests/**"]
  - id: T3
    title: "Implementation: implement the feature changes"
    type: "implementation"
    agent: "{available_agents[0]}"
    runtime: "gemini"
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
    runtime: "codex"
    depends_on: ["T4"]
```
"""


DEFAULT_TEMPLATES = {
    "api-endpoint": {
        "name": "api-endpoint",
        "description": "Add a new API endpoint",
        "variables": [
            {"name": "endpoint_path", "prompt": "Enter the API route path (e.g. /api/v1/users)", "default": "/api/v1/resource"},
            {"name": "method", "prompt": "HTTP Method (GET/POST/PUT/DELETE)", "default": "GET"},
        ],
        "tasks": [
            {
                "id": "T1",
                "title": "Discovery: analyze current API patterns in the codebase",
                "type": "discovery",
                "agent": "backend-specialist",
                "writes_files": False,
            },
            {
                "id": "T2",
                "title": "TDD: Write endpoint contract test case for {{method}} {{endpoint_path}}",
                "type": "implementation",
                "agent": "backend-specialist",
                "depends_on": ["T1"],
                "writes_files": True,
                "files_allowed": ["tests/**"],
            },
            {
                "id": "T3",
                "title": "Implementation: implement the {{method}} {{endpoint_path}} controller and router",
                "type": "implementation",
                "agent": "backend-specialist",
                "depends_on": ["T2"],
                "writes_files": True,
                "files_allowed": ["*"],
            },
            {
                "id": "T4",
                "title": "Review: review the endpoint security",
                "type": "review",
                "agent": "security-reviewer",
                "depends_on": ["T3"],
                "writes_files": False,
            },
            {
                "id": "T5",
                "title": "Validation: run all verification tests to confirm success",
                "type": "validation",
                "agent": "qa-reviewer",
                "depends_on": ["T4"],
            }
        ]
    },
    "bugfix": {
        "name": "bugfix",
        "description": "Fix a bug with TDD",
        "variables": [
            {"name": "bug_description", "prompt": "Brief description of the bug", "default": "Fix unexpected error"},
        ],
        "tasks": [
            {
                "id": "T1",
                "title": "Discovery: locate the source of: {{bug_description}}",
                "type": "discovery",
                "agent": "backend-specialist",
                "writes_files": False,
            },
            {
                "id": "T2",
                "title": "TDD: write a test case reproducing the bug",
                "type": "implementation",
                "agent": "backend-specialist",
                "depends_on": ["T1"],
                "writes_files": True,
                "files_allowed": ["tests/**"],
            },
            {
                "id": "T3",
                "title": "Implementation: apply fix for: {{bug_description}}",
                "type": "implementation",
                "agent": "backend-specialist",
                "depends_on": ["T2"],
                "writes_files": True,
                "files_allowed": ["*"],
            },
            {
                "id": "T4",
                "title": "Validation: run verify check to ensure bug is fixed",
                "type": "validation",
                "agent": "qa-reviewer",
                "depends_on": ["T3"],
            }
        ]
    },
    "refactor": {
        "name": "refactor",
        "description": "Refactor code without changing behavior",
        "variables": [
            {"name": "target_file", "prompt": "Path to file/module to refactor", "default": ""},
        ],
        "tasks": [
            {
                "id": "T1",
                "title": "Discovery: analyze structure of {{target_file}}",
                "type": "discovery",
                "agent": "backend-specialist",
                "writes_files": False,
            },
            {
                "id": "T2",
                "title": "Implementation: refactor code in {{target_file}}",
                "type": "implementation",
                "agent": "backend-specialist",
                "depends_on": ["T1"],
                "writes_files": True,
                "files_allowed": ["*"],
            },
            {
                "id": "T3",
                "title": "Validation: verify all existing tests still pass",
                "type": "validation",
                "agent": "qa-reviewer",
                "depends_on": ["T2"],
            }
        ]
    }
}


def run_mission_plan(
    requirements_path: str,
    strict: bool = False,
    console: Console = None,
    template: str | None = None,
    runtime_override: str | None = None,
) -> str:
    """Generate a mission plan from a requirements file."""
    if console is None:
        console = Console()
    from sutra.core.config import find_sutra_root
    from sutra.core.errors import SutraConfigError

    repo_root = find_sutra_root()
    if not repo_root:
        raise SutraConfigError("Not a Sutra workspace. Run 'sutra init' first.")
    sutra_dir = get_sutra_dir(repo_root)

    if not sutra_dir.exists():
        console.print("[bold red]Error:[/] Not a Sutra workspace. Run `sutra init` first.")
        raise SystemExit(1)

    req_file = Path(requirements_path)
    if req_file.exists() and req_file.is_file():
        requirement_content = req_file.read_text(encoding="utf-8")
        clean_name = "".join(c if c.isalnum() else "-" for c in req_file.stem).strip("-").lower()
        if not clean_name:
            clean_name = "requirement"
        is_inline = False
    else:
        requirement_content = requirements_path
        # Limit clean_name to 30 chars
        clean_name = "".join(c if c.isalnum() else "-" for c in requirements_path[:30]).strip("-").lower()
        if not clean_name:
            clean_name = "inline"
        is_inline = True

    # 1. Generate unique mission ID
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    mission_id = f"{clean_name}-{timestamp}"

    # 2. Create runs directory
    run_dir = sutra_dir / "runs" / mission_id
    run_dir.mkdir(parents=True, exist_ok=True)

    # 3. Copy or write requirements file
    if is_inline:
        (run_dir / "requirement.md").write_text(requirement_content, encoding="utf-8")
    else:
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

    # Load config if exists
    config = None
    try:
        config = load_sutra_config(repo_root)
    except Exception:
        pass

    # Template planning
    if template:
        # Load template
        template_file = sutra_dir / "templates" / "missions" / f"{template}.yaml"
        template_data = None
        if template_file.exists():
            try:
                with open(template_file, encoding="utf-8") as f:
                    template_data = yaml.safe_load(f)
            except Exception as e:
                console.print(f"[yellow]Warning: failed to load template file '{template_file}': {e}[/]")
        
        if not template_data:
            if template in DEFAULT_TEMPLATES:
                template_data = DEFAULT_TEMPLATES[template]
                console.print(f"[dim]Using built-in template '{template}'...[/]")
            else:
                console.print(f"[bold red]Error:[/] Mission template '{template}' not found.")
                raise SystemExit(1)
        
        # Resolve variables
        variables = template_data.get("variables", [])
        var_values = {}
        for var in variables:
            var_name = var.get("name")
            prompt_text = var.get("prompt", f"Value for {var_name}")
            default_val = var.get("default", "")
            
            # If running in non-interactive/test, use default
            is_non_interactive = os.environ.get("SUTRA_TEST") == "1" or "pytest" in sys.modules
            if is_non_interactive:
                var_values[var_name] = default_val
            else:
                from rich.prompt import Prompt
                try:
                    var_values[var_name] = Prompt.ask(prompt_text, default=default_val)
                except (KeyboardInterrupt, EOFError):
                    console.print("\n[red]Mission planning aborted.[/]")
                    raise SystemExit(1)
                
        # Render tasks
        raw_tasks = template_data.get("tasks", [])
        rendered_tasks = []
        for i, t in enumerate(raw_tasks, start=1):
            t_id = t.get("id") or f"T{i}"
            t_title = t.get("title", "")
            t_type = t.get("type", "implementation")
            t_agent = t.get("agent")
            if t_agent == "backend-specialist":
                t_agent = backend_agent
            elif t_agent == "security-reviewer":
                t_agent = security_agent
            elif t_agent == "qa-reviewer":
                t_agent = qa_agent
            elif t_agent not in available_agents:
                t_agent = available_agents[0]
            t_deps = t.get("depends_on", [])
            t_rt = t.get("runtime") or runtime_override
            t_writes = t.get("writes_files")
            if t_writes is None:
                t_writes = t_type == "implementation"
            t_files = t.get("files_allowed") or ["*"]
            
            # String replacement for variables
            for var_name, var_val in var_values.items():
                pattern = "{{" + var_name + "}}"
                t_title = t_title.replace(pattern, var_val)
                
            rendered_tasks.append({
                "id": t_id,
                "title": t_title,
                "type": t_type,
                "status": "pending",
                "agent": t_agent,
                "runtime": t_rt,
                "depends_on": t_deps,
                "writes_files": t_writes,
                "files_allowed": t_files,
            })
            
        plan_data = {
            "mission": {
                "id": mission_id,
                "requirement": str(requirements_path),
                "created": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "status": "planned",
                "orchestrator": runtime_override or (config.runtimes[0] if config and config.runtimes else "claude"),
                "parallel": 1,
            },
            "tasks": rendered_tasks
        }
        console.print(f"[bold green]✓[/] Generated mission plan from template '[cyan]{template}[/]' with {len(rendered_tasks)} tasks.")
    
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

            repo_map = get_repo_map(repo_root)
            prompt = build_planner_prompt(requirement_content, repo_map, available_agents)
            
            # Write prompt for trace
            (run_dir / "planner-prompt.md").write_text(prompt, encoding="utf-8")
            
            console.print(f"[dim]Invoking AI planning engine '{orchestrator}'...[/]")
            cmd = [orchestrator, "-p", prompt]
            if orchestrator == "gemini":
                cmd.append("--skip-trust")
                
            try:
                res = subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=180)
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
                            t_runtime = t.get("runtime")
                            if t_runtime is not None:
                                t_runtime = str(t_runtime).strip()
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
                                "runtime": t_runtime,
                                "depends_on": t_deps,
                                "writes_files": t_writes,
                                "files_allowed": t_files,
                            })
                        plan_data = {
                            "mission": {
                                "id": mission_id,
                                "requirement": str(requirements_path),
                                "created": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                                "status": "planned",
                                "orchestrator": runtime_override or orchestrator,
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
                "created": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "status": "planned",
                "orchestrator": runtime_override or "claude",
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


def run_mission_approve(console: Console, interactive: bool = False) -> None:
    """Approve the latest planned mission."""
    from sutra.core.config import find_sutra_root
    from sutra.core.errors import SutraConfigError

    repo_root = find_sutra_root()
    if not repo_root:
        raise SutraConfigError("Not a Sutra workspace. Run 'sutra init' first.")
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

    # Automatically validate plan before approval
    from sutra.mission.validator import validate_mission_plan, PlanValidationError
    try:
        validate_mission_plan(plan_path, repo_root)
    except PlanValidationError as e:
        console.print(f"[bold red]❌ Mission approval rejected due to validation failures:[/]")
        for err in e.errors:
            console.print(f"  • [red]{err}[/]")
        raise SystemExit(1)
    except Exception as e:
        console.print(f"[bold red]Error during validation:[/] {e}")
        raise SystemExit(1)

    with open(plan_path, encoding="utf-8") as f:
        plan_data = yaml.safe_load(f) or {}

    mission_meta = plan_data.get("mission", {})
    status = mission_meta.get("status", "planned")

    if status != "planned":
        console.print(f"[yellow]Mission '{mission_id}' is already {status}.[/]")
        return

    if interactive:
        from rich.table import Table
        from rich.panel import Panel

        while True:
            # Re-load plan data
            with open(plan_path, encoding="utf-8") as f:
                plan_data = yaml.safe_load(f) or {}

            tasks = plan_data.get("tasks", [])
            mission_meta = plan_data.get("mission", {})

            table = Table(title=f"Mission Plan preview: [cyan]{mission_id}[/]", expand=True)
            table.add_column("ID", style="bold magenta", justify="center", width=4)
            table.add_column("Title")
            table.add_column("Agent", style="yellow")
            table.add_column("Runtime", style="cyan")
            table.add_column("Depends On", style="dim white")
            table.add_column("Writes", style="green")

            for t in tasks:
                t_id = t.get("id")
                t_title = t.get("title")
                t_agent = t.get("agent")
                t_rt = t.get("runtime") or mission_meta.get("orchestrator", "claude")
                t_deps = ", ".join(t.get("depends_on", [])) or "-"
                t_writes = "Yes" if t.get("writes_files", True) else "No"
                table.add_row(t_id, t_title, t_agent, t_rt, t_deps, t_writes)

            console.print(Panel(table, border_style="magenta"))

            try:
                answer = input("Approve all tasks? [Y/n/edit]: ").strip().lower()
            except (KeyboardInterrupt, EOFError):
                console.print("\n[red]Mission approval cancelled.[/]")
                raise SystemExit(1)

            if not answer or answer in ("y", "yes"):
                break
            elif answer in ("n", "no"):
                console.print("[red]Mission approval cancelled.[/]")
                raise SystemExit(1)
            elif answer == "edit":
                editor = os.environ.get("EDITOR", "nano")
                import subprocess
                try:
                    subprocess.run([editor, str(plan_path)], check=True)
                except Exception as e:
                    console.print(f"[bold red]Failed to launch editor '{editor}':[/] {e}")
                    try:
                        subprocess.run(["vi", str(plan_path)], check=True)
                    except Exception:
                        pass

                # Re-validate
                try:
                    validate_mission_plan(plan_path, repo_root)
                    console.print("[bold green]✓ Edited plan is valid.[/]")
                except PlanValidationError as e:
                    console.print(f"[bold red]❌ Mission plan validation failed after editing:[/]")
                    for err in e.errors:
                        console.print(f"  • [red]{err}[/]")
                except Exception as e:
                    console.print(f"[bold red]Error during validation:[/] {e}")
            else:
                console.print("[yellow]Invalid option. Please choose y, n, or edit.[/]")

    # Re-load plan data final time to make sure we write approved status
    with open(plan_path, encoding="utf-8") as f:
        plan_data = yaml.safe_load(f) or {}

    # Update status to approved
    plan_data["mission"]["status"] = "approved"
    with open(plan_path, "w", encoding="utf-8") as f:
        yaml.dump(plan_data, f, default_flow_style=False, sort_keys=False)

    # Write approval.json
    approval_path = run_dir / "approval.json"
    approval_data = {
        "approved": True,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    import json
    approval_path.write_text(json.dumps(approval_data, indent=2), encoding="utf-8")

    console.print(f"[bold green]✓[/] Mission '[cyan]{mission_id}[/]' has been approved and is ready to start.")
