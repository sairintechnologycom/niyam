"""Niyam mission planner — generate mission plans from requirements."""

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

from niyam.core.config import (
    get_niyam_dir,
    load_niyam_config,
    load_project_config,
    MissionPlan,
)
from pydantic import ValidationError


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
    ignore_dirs = {
        ".git",
        ".niyam",
        "__pycache__",
        ".venv",
        ".pytest_cache",
        "node_modules",
        "build",
        "dist",
        ".antigravitycli",
    }
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
    text = text.strip()
    if not text:
        return None

    # Helper to extract JSON recursively
    def extract_json_blob(t: str) -> dict | list | None:
        t = t.strip()
        if not t:
            return None

        # helper for cleaning prose around JSON
        def clean_prose(s: str) -> str:
            # Remove markdown blocks
            s = re.sub(r"```(?:json)?\s*(.*?)\s*```", r"\1", s, flags=re.DOTALL)
            # Find first { or [ and last } or ]
            start = s.find("{")
            if start == -1:
                start = s.find("[")
            end = s.rfind("}")
            if end == -1:
                end = s.rfind("]")
            if start != -1 and end != -1 and end > start:
                return s[start : end + 1]
            return s

        # Try direct parse first
        try:
            data = json.loads(t)
            if isinstance(data, dict):
                for key in ["response", "text", "content", "message"]:
                    val = data.get(key)
                    if isinstance(val, str) and ("{" in val or "[" in val):
                        nested = extract_json_blob(val)
                        if nested:
                            return nested
            return data
        except Exception:
            pass

        # Try cleaning prose and parsing again
        cleaned = clean_prose(t)
        try:
            data = json.loads(cleaned)
            # Repeat unwrapping for cleaned data
            if isinstance(data, dict):
                for key in ["response", "text", "content", "message"]:
                    val = data.get(key)
                    if isinstance(val, str) and ("{" in val or "[" in val):
                        nested = extract_json_blob(val)
                        if nested:
                            return nested
            return data
        except Exception:
            pass

        return None

    # 1. Try extracting JSON first
    parsed_json = extract_json_blob(text)
    if isinstance(parsed_json, dict) and "tasks" in parsed_json:
        return parsed_json

    # 2. Try looking for ```yaml ... ```
    yaml_block = re.search(
        r"```(?:yaml|yml)?\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE
    )
    if yaml_block:
        try:
            parsed = yaml.safe_load(yaml_block.group(1))
            if isinstance(parsed, dict) and "tasks" in parsed:
                return parsed
        except Exception:
            pass

    # 3. Try parsing the whole text as YAML
    try:
        data = yaml.safe_load(text)
        if isinstance(data, dict) and "tasks" in data:
            return data
    except Exception:
        pass

    return None


def build_planner_prompt(
    requirement: str, repo_map: str, available_agents: list[str]
) -> str:
    agents_str = ", ".join(available_agents)
    return f"""You are the Niyam planning engine.
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
6. Return ONLY a valid YAML or JSON block matching the schema below. Do not output any markdown prose, chat, warnings, or explanation. Only output the content inside ```yaml or ```json code fences.

Schema (YAML format):
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
    tdd_required: true
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


def build_corrective_prompt(
    original_prompt: str, raw_output: str, error_msg: str
) -> str:
    return f"""{original_prompt}

---
[WARNING] Your previous output failed verification/validation with the following error:
{error_msg}

Here was your previous output:
{raw_output}

Please fix the error. Return ONLY the corrected YAML/JSON block matching the schema inside code fences. Do not output any other text or explanation.
"""


def choose_fallback_template(requirement_text: str) -> str:
    req_lower = requirement_text.lower()
    if "api" in req_lower or "endpoint" in req_lower:
        return "api-endpoint"
    if (
        "bug" in req_lower
        or "fix" in req_lower
        or "issue" in req_lower
        or "error" in req_lower
        or "fail" in req_lower
    ):
        return "bugfix"
    if "refactor" in req_lower or "clean" in req_lower or "optimize" in req_lower:
        return "refactor"
    return "default"


def inject_validation_commands(tasks: list[dict], repo_root: Path) -> None:
    try:
        proj = load_project_config(repo_root)
    except Exception:
        proj = None
    if proj and proj.validation:
        for task in tasks:
            if "validation" not in task:
                task["validation"] = {"commands": []}
            elif not isinstance(task["validation"], dict):
                task["validation"] = {"commands": []}
            elif "commands" not in task["validation"]:
                task["validation"]["commands"] = []

            if task.get("type") == "implementation":
                cmds = []
                if proj.validation.test:
                    cmds.append(proj.validation.test)
                if proj.validation.lint:
                    cmds.append(proj.validation.lint)
                task["validation"]["commands"] = cmds
            elif task.get("type") == "validation":
                cmds = [
                    c
                    for c in [
                        proj.validation.test,
                        proj.validation.lint,
                        proj.validation.typecheck,
                        proj.validation.build,
                    ]
                    if c
                ]
                task["validation"]["commands"] = cmds
            elif task.get("type") in ("discovery", "review"):
                task["validation"]["commands"] = []


DEFAULT_TEMPLATES = {
    "api-endpoint": {
        "name": "api-endpoint",
        "description": "Add a new API endpoint",
        "variables": [
            {
                "name": "endpoint_path",
                "prompt": "Enter the API route path (e.g. /api/v1/users)",
                "default": "/api/v1/resource",
            },
            {
                "name": "method",
                "prompt": "HTTP Method (GET/POST/PUT/DELETE)",
                "default": "GET",
            },
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
            },
        ],
    },
    "bugfix": {
        "name": "bugfix",
        "description": "Fix a bug with TDD",
        "variables": [
            {
                "name": "bug_description",
                "prompt": "Brief description of the bug",
                "default": "Fix unexpected error",
            },
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
            },
        ],
    },
    "refactor": {
        "name": "refactor",
        "description": "Refactor code without changing behavior",
        "variables": [
            {
                "name": "target_file",
                "prompt": "Path to file/module to refactor",
                "default": "",
            },
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
            },
        ],
    },
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
    from niyam.core.config import find_niyam_root
    from niyam.core.errors import NiyamConfigError

    repo_root = find_niyam_root()
    if not repo_root:
        raise NiyamConfigError("Not a Niyam workspace. Run 'niyam init' first.")
    niyam_dir = get_niyam_dir(repo_root)

    if not niyam_dir.exists():
        console.print(
            "[bold red]Error:[/] Not a Niyam workspace. Run `niyam init` first."
        )
        raise SystemExit(1)

    req_file = Path(requirements_path)
    if req_file.exists() and req_file.is_file():
        requirement_content = req_file.read_text(encoding="utf-8")
        clean_name = (
            "".join(c if c.isalnum() else "-" for c in req_file.stem).strip("-").lower()
        )
        if not clean_name:
            clean_name = "requirement"
        is_inline = False
    else:
        requirement_content = requirements_path
        # Limit clean_name to 30 chars
        clean_name = (
            "".join(c if c.isalnum() else "-" for c in requirements_path[:30])
            .strip("-")
            .lower()
        )
        if not clean_name:
            clean_name = "inline"
        is_inline = True

    # 1. Generate unique mission ID
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    mission_id = f"{clean_name}-{timestamp}"

    # 2. Create runs directory
    run_dir = niyam_dir / "runs" / mission_id
    run_dir.mkdir(parents=True, exist_ok=True)

    # 3. Copy or write requirements file
    if is_inline:
        (run_dir / "requirement.md").write_text(requirement_content, encoding="utf-8")
    else:
        shutil.copy2(req_file, run_dir / "requirement.md")

    # 4. Determine available agents
    agents_dir = niyam_dir / "agents"
    available_agents = []
    if agents_dir.is_dir():
        available_agents = [f.stem for f in agents_dir.glob("*.md")]

    if not available_agents:
        available_agents = ["default-agent"]

    backend_agent = (
        "backend-specialist"
        if "backend-specialist" in available_agents
        else available_agents[0]
    )
    security_agent = (
        "security-reviewer"
        if "security-reviewer" in available_agents
        else available_agents[0]
    )
    qa_agent = (
        "qa-reviewer" if "qa-reviewer" in available_agents else available_agents[0]
    )

    plan_data = None

    # Load config if exists
    config = None
    try:
        config = load_niyam_config(repo_root)
    except Exception:
        pass

    # Template planning
    if template:
        # Load template
        template_file = niyam_dir / "templates" / "missions" / f"{template}.yaml"
        template_data = None
        if template_file.exists():
            try:
                with open(template_file, encoding="utf-8") as f:
                    template_data = yaml.safe_load(f)
            except Exception as e:
                console.print(
                    f"[yellow]Warning: failed to load template file '{template_file}': {e}[/]"
                )

        if not template_data:
            if template in DEFAULT_TEMPLATES:
                template_data = DEFAULT_TEMPLATES[template]
                console.print(f"[dim]Using built-in template '{template}'...[/]")
            else:
                console.print(
                    f"[bold red]Error:[/] Mission template '{template}' not found."
                )
                raise SystemExit(1)

        # Resolve variables
        variables = template_data.get("variables", [])
        var_values = {}
        for var in variables:
            var_name = var.get("name")
            prompt_text = var.get("prompt", f"Value for {var_name}")
            default_val = var.get("default", "")

            # If running in non-interactive/test, use default
            is_non_interactive = (
                os.environ.get("NIYAM_TEST") == "1" or "pytest" in sys.modules
            )
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

            rendered_tasks.append(
                {
                    "id": t_id,
                    "title": t_title,
                    "type": t_type,
                    "status": "planned",
                    "agent": t_agent,
                    "runtime": t_rt,
                    "depends_on": t_deps,
                    "writes_files": t_writes,
                    "files_allowed": t_files,
                }
            )

        inject_validation_commands(rendered_tasks, repo_root)

        plan_data = {
            "mission": {
                "id": mission_id,
                "requirement": str(requirements_path),
                "created": datetime.now(timezone.utc)
                .isoformat()
                .replace("+00:00", "Z"),
                "status": "planned",
                "orchestrator": runtime_override
                or (config.runtimes[0] if config and config.runtimes else "claude"),
                "parallel": 1,
            },
            "tasks": rendered_tasks,
        }

        # Pydantic validation for template plan
        try:
            validated = MissionPlan(**plan_data)
            plan_data = validated.model_dump(exclude_none=True)
        except Exception as e:
            console.print(
                f"[yellow]Warning: template plan failed schema validation: {e}[/]"
            )

        console.print(
            f"[bold green]✓[/] Generated mission plan from template '[cyan]{template}[/]' with {len(rendered_tasks)} tasks."
        )

    # 5. Try AI planning if not in basic unit tests
    is_test = (
        os.environ.get("NIYAM_TEST") == "1" or "pytest" in sys.modules
    ) and os.environ.get("NIYAM_TEST_PLANNER") != "1"
    config = None
    try:
        config = load_niyam_config(repo_root)
    except Exception:
        pass

    MAX_PLANNER_RETRIES = 2

    if config and not is_test:
        orchestrator = config.runtimes[0] if config.runtimes else "claude"
        if shutil.which(orchestrator):
            repo_map = get_repo_map(repo_root)
            current_prompt = build_planner_prompt(
                requirement_content, repo_map, available_agents
            )

            # Write prompt for trace
            (run_dir / "planner-prompt.md").write_text(current_prompt, encoding="utf-8")

            for attempt in range(MAX_PLANNER_RETRIES):
                console.print(
                    f"[dim]Invoking AI planning engine '{orchestrator}' (attempt {attempt + 1}/{MAX_PLANNER_RETRIES})...[/]"
                )
                cmd = [orchestrator, "-p", current_prompt]
                if orchestrator == "gemini":
                    cmd.append("--skip-trust")

                try:
                    res = subprocess.run(
                        cmd,
                        stdin=subprocess.DEVNULL,
                        capture_output=True,
                        text=True,
                        timeout=180,
                    )
                    raw_output = (res.stdout or "") + "\n" + (res.stderr or "")

                    # Log raw output for debugging
                    out_file = run_dir / f"planner-output-attempt-{attempt + 1}.raw.txt"
                    out_file.write_text(raw_output, encoding="utf-8")
                    if attempt == 0:
                        (run_dir / "planner-output.raw.txt").write_text(
                            raw_output, encoding="utf-8"
                        )

                    if res.returncode != 0:
                        error_msg = f"Orchestrator returned non-zero exit code: {res.returncode}"
                        if attempt < MAX_PLANNER_RETRIES - 1:
                            current_prompt = build_corrective_prompt(
                                current_prompt, raw_output, error_msg
                            )
                            continue
                        else:
                            console.print(
                                f"[yellow]Warning:[/] AI planner failed: {error_msg}"
                            )
                            break

                    parsed = extract_yaml_or_json(raw_output)
                    if (
                        not parsed
                        or not isinstance(parsed, dict)
                        or "tasks" not in parsed
                    ):
                        error_msg = "Could not parse JSON/YAML or 'tasks' key is missing from output."
                        if attempt < MAX_PLANNER_RETRIES - 1:
                            current_prompt = build_corrective_prompt(
                                current_prompt, raw_output, error_msg
                            )
                            continue
                        else:
                            console.print(
                                f"[yellow]Warning:[/] AI planner failed: {error_msg}"
                            )
                            break

                    tasks = parsed["tasks"]
                    if not isinstance(tasks, list):
                        error_msg = "'tasks' must be a list in the planner output."
                        if attempt < MAX_PLANNER_RETRIES - 1:
                            current_prompt = build_corrective_prompt(
                                current_prompt, raw_output, error_msg
                            )
                            continue
                        else:
                            console.print(
                                f"[yellow]Warning:[/] AI planner failed: {error_msg}"
                            )
                            break

                    normalized_tasks = []
                    for i, t in enumerate(tasks, start=1):
                        if not isinstance(t, dict):
                            continue
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
                        t_files = (
                            t.get("files_allowed") or t.get("allowed_files") or ["*"]
                        )
                        if isinstance(t_files, str):
                            t_files = [t_files]

                        normalized_task = {
                            "id": t_id,
                            "title": t_title,
                            "type": t_type,
                            "status": "planned",
                            "agent": t_agent,
                            "runtime": t_runtime,
                            "depends_on": t_deps,
                            "writes_files": t_writes,
                            "files_allowed": t_files,
                        }

                        # Preserve other fields that are valid in TaskContract
                        for field in [
                            "timeout_seconds",
                            "timeout",
                            "risk",
                            "objective",
                            "acceptance_criteria",
                            "validation",
                            "approval_required",
                            "tdd_required",
                        ]:
                            if field in t:
                                normalized_task[field] = t[field]

                        normalized_tasks.append(normalized_task)

                    # Inject validation commands before validating with Pydantic
                    inject_validation_commands(normalized_tasks, repo_root)

                    candidate_plan = {
                        "mission": {
                            "id": mission_id,
                            "requirement": str(requirements_path),
                            "created": datetime.now(timezone.utc)
                            .isoformat()
                            .replace("+00:00", "Z"),
                            "status": "planned",
                            "orchestrator": runtime_override or orchestrator,
                            "parallel": 1,
                        },
                        "tasks": normalized_tasks,
                    }

                    # Validate using MissionPlan Pydantic model
                    try:
                        validated = MissionPlan(**candidate_plan)
                        plan_data = validated.model_dump(exclude_none=True)
                        console.print(
                            f"[bold green]✓[/] AI generated a custom task plan with {len(normalized_tasks)} tasks."
                        )
                        break  # Success! Break the retry loop
                    except ValidationError as e:
                        error_msg = f"AI plan failed schema validation: {e}"
                        if attempt < MAX_PLANNER_RETRIES - 1:
                            current_prompt = build_corrective_prompt(
                                current_prompt, raw_output, error_msg
                            )
                            continue
                        else:
                            console.print(f"[yellow]Warning:[/] {error_msg}")
                            break

                except Exception as e:
                    error_msg = f"AI planner execution encountered an error: {e}"
                    if attempt < MAX_PLANNER_RETRIES - 1:
                        current_prompt = build_corrective_prompt(
                            current_prompt, "", error_msg
                        )
                        continue
                    else:
                        console.print(f"[yellow]Warning:[/] {error_msg}")
                        break

    # Fallback to templates/static plan
    if not plan_data:
        if strict:
            console.print(
                "[bold red]Error:[/] AI-powered planning failed and strict planning was requested."
            )
            raise SystemExit(1)

        req_name = (
            Path(requirements_path).name
            if Path(requirements_path).exists()
            else "requirement.md"
        )
        fallback_type = choose_fallback_template(requirement_content)
        console.print(
            f"[yellow]AI planner fallback: generating standard '{fallback_type}' template plan.[/]"
        )

        if fallback_type in DEFAULT_TEMPLATES:
            # We will use the default template rendering logic programmatically
            template_data = DEFAULT_TEMPLATES[fallback_type]
            var_values = {}
            for var in template_data.get("variables", []):
                var_name = var.get("name")
                default_val = var.get("default", "")
                if fallback_type == "bugfix" and var_name == "bug_description":
                    var_values[var_name] = f"Fix issue described in {req_name}"
                elif fallback_type == "refactor" and var_name == "target_file":
                    var_values[var_name] = f"files in {req_name}"
                else:
                    var_values[var_name] = default_val

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
                    t_title = t_title.replace("{{" + var_name + "}}", var_val)
                    t_title = t_title.replace("{" + var_name + "}", var_val)

                rendered_tasks.append(
                    {
                        "id": t_id,
                        "title": t_title,
                        "type": t_type,
                        "status": "planned",
                        "agent": t_agent,
                        "runtime": t_rt,
                        "depends_on": t_deps,
                        "writes_files": t_writes,
                        "files_allowed": t_files,
                    }
                )

            # Inject validation commands for templates too!
            inject_validation_commands(rendered_tasks, repo_root)

            plan_data = {
                "mission": {
                    "id": mission_id,
                    "requirement": str(requirements_path),
                    "created": datetime.now(timezone.utc)
                    .isoformat()
                    .replace("+00:00", "Z"),
                    "status": "planned",
                    "orchestrator": runtime_override or "claude",
                    "parallel": 1,
                },
                "tasks": rendered_tasks,
            }
        else:
            # Standard fallback (default)
            plan_data = {
                "mission": {
                    "id": mission_id,
                    "requirement": str(requirements_path),
                    "created": datetime.now(timezone.utc)
                    .isoformat()
                    .replace("+00:00", "Z"),
                    "status": "planned",
                    "orchestrator": runtime_override or "claude",
                    "parallel": 1,
                },
                "tasks": [
                    {
                        "id": "T1",
                        "title": f"Discovery: Analyze requirement in {req_name}",
                        "type": "discovery",
                        "status": "planned",
                        "agent": backend_agent,
                        "writes_files": False,
                    },
                    {
                        "id": "T2",
                        "title": f"TDD: Write failing test cases for {req_name}",
                        "type": "implementation",
                        "status": "planned",
                        "agent": backend_agent,
                        "depends_on": ["T1"],
                        "tdd_required": True,
                        "files_allowed": ["tests/**"],
                    },
                    {
                        "id": "T3",
                        "title": f"Implementation: Code the solution for {req_name}",
                        "type": "implementation",
                        "status": "planned",
                        "agent": backend_agent,
                        "depends_on": ["T2"],
                        "files_allowed": ["*"],
                    },
                    {
                        "id": "T4",
                        "title": f"Security: Review changes for {req_name} for vulnerabilities",
                        "type": "review",
                        "status": "planned",
                        "agent": security_agent,
                        "depends_on": ["T3"],
                        "writes_files": False,
                    },
                    {
                        "id": "T5",
                        "title": f"Validation: Run full verification suite for {req_name}",
                        "type": "validation",
                        "status": "planned",
                        "agent": qa_agent,
                        "depends_on": ["T4"],
                    },
                ],
            }
            # Inject validation commands for fallback tasks
            inject_validation_commands(plan_data["tasks"], repo_root)

        # Validate fallback plan with Pydantic
        try:
            validated = MissionPlan(**plan_data)
            plan_data = validated.model_dump(exclude_none=True)
        except Exception as e:
            console.print(
                f"[yellow]Warning: fallback plan failed schema validation: {e}[/]"
            )

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

    # Maintain current symlink
    current_symlink = niyam_dir / "runs" / "current"
    if current_symlink.exists() or current_symlink.is_symlink():
        try:
            current_symlink.unlink()
        except Exception:
            pass
    try:
        current_symlink.symlink_to(mission_id)
    except Exception as e:
        console.print(
            f"[yellow]Warning: failed to create symlink '.niyam/runs/current': {e}[/]"
        )

    console.print(
        f"[bold green]✓[/] Created mission plan '[cyan]{mission_id}[/]' in .niyam/runs/{mission_id}/"
    )
    return mission_id


def get_latest_mission_id(niyam_dir: Path) -> str | None:
    """Find the latest mission run directory."""
    runs_dir = niyam_dir / "runs"
    if not runs_dir.exists():
        return None
    runs = [d for d in runs_dir.iterdir() if d.is_dir() and d.name != "current"]
    if not runs:
        return None
    # Sort by directory creation/modification time
    runs.sort(key=lambda d: d.stat().st_mtime, reverse=True)
    return runs[0].name


def resolve_mission_id(niyam_dir: Path, mission_id: str | None = None) -> str | None:
    """Resolve a mission ID, preferring active work over completed history."""
    runs_dir = niyam_dir / "runs"
    if not runs_dir.exists():
        return None

    if mission_id:
        run_dir = runs_dir / mission_id
        return mission_id if run_dir.is_dir() else None

    runs = [d for d in runs_dir.iterdir() if d.is_dir() and d.name != "current"]
    if not runs:
        return None

    status_rank = {
        "running": 0,
        "paused": 1,
        "approved": 2,
        "planned": 3,
        "failed": 4,
        "completed": 5,
    }

    def sort_key(run_dir: Path) -> tuple[int, float]:
        status = "completed"
        plan_path = run_dir / "mission-plan.yaml"
        if plan_path.exists():
            try:
                with open(plan_path, encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                status = data.get("mission", {}).get("status", status)
            except Exception:
                pass
        return (status_rank.get(status, 6), -run_dir.stat().st_mtime)

    runs.sort(key=sort_key)
    return runs[0].name


def _print_preview_table(console: Console, mission_id: str, plan_data: dict) -> None:
    from rich.table import Table
    from rich.panel import Panel

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


def _run_refiner_loop(
    console: Console,
    plan_path: Path,
    repo_root: Path,
    niyam_dir: Path,
) -> None:
    from niyam.mission.validator import validate_mission_plan, PlanValidationError
    import yaml
    import re

    agents_dir = niyam_dir / "agents"
    available_agents = []
    if agents_dir.is_dir():
        available_agents = [f.stem for f in agents_dir.glob("*.md")]
    if not available_agents:
        available_agents = ["default-agent"]

    console.print("\n[bold cyan]=== Mission Plan Refinement CLI ===[/]")
    console.print("Commands:")
    console.print("  [bold]merge <t1> <t2>[/]      - Merge task t2 into t1")
    console.print("  [bold]delete <t>[/]          - Delete task t")
    console.print("  [bold]add <title>[/]         - Append a new task to the end")
    console.print(
        "  [bold]insert <after_t> <title>[/] - Insert a new task after after_t"
    )
    console.print(
        "  [bold]edit <t> <f>=<v>[/]     - Edit field f (title, agent, runtime, depends_on, writes_files, files_allowed) of task t"
    )
    console.print("  [bold]show[/]                  - Show the current tasks table")
    console.print(
        "  [bold]done[/]                  - Finish refinement and return to approval menu"
    )
    console.print("")

    while True:
        try:
            with open(plan_path, encoding="utf-8") as f:
                plan_data = yaml.safe_load(f) or {}
        except Exception as e:
            console.print(f"[red]Error loading plan: {e}[/]")
            break

        try:
            cmd_input = input("refine> ").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]Exiting refinement mode.[/]")
            break

        if not cmd_input:
            continue

        parts = cmd_input.split(None, 1)
        cmd = parts[0].lower()
        args_str = parts[1] if len(parts) > 1 else ""

        if cmd == "done":
            break
        elif cmd == "show":
            _print_preview_table(
                console, plan_data.get("mission", {}).get("id", "mission"), plan_data
            )
            continue

        changed = False

        if cmd == "merge":
            subparts = args_str.split(None, 1)
            if len(subparts) < 2:
                console.print("[red]Usage: merge <t1> <t2>[/]")
                continue
            t1, t2 = subparts[0], subparts[1]

            idx1 = next(
                (
                    i
                    for i, t in enumerate(plan_data.get("tasks", []))
                    if t.get("id") == t1
                ),
                -1,
            )
            idx2 = next(
                (
                    i
                    for i, t in enumerate(plan_data.get("tasks", []))
                    if t.get("id") == t2
                ),
                -1,
            )

            if idx1 == -1 or idx2 == -1:
                console.print(f"[red]Error: task '{t1}' or '{t2}' not found.[/]")
                continue

            tasks = plan_data["tasks"]
            task1 = tasks[idx1]
            task2 = tasks[idx2]

            task1["title"] = f"{task1.get('title')} & {task2.get('title')}"
            deps1 = task1.get("depends_on", []) or []
            deps2 = task2.get("depends_on", []) or []
            combined_deps = list(set(deps1 + deps2))
            if t1 in combined_deps:
                combined_deps.remove(t1)
            if t2 in combined_deps:
                combined_deps.remove(t2)
            task1["depends_on"] = combined_deps

            # Update references to t2 to point to t1
            for t in tasks:
                if t.get("id") == t1 or t.get("id") == t2:
                    continue
                deps = t.get("depends_on", []) or []
                if t2 in deps:
                    deps = [t1 if d == t2 else d for d in deps]
                    t["depends_on"] = list(set(deps))

            tasks.pop(idx2)
            changed = True
            console.print(f"[green]Merged '{t2}' into '{t1}'.[/]")

        elif cmd == "delete":
            if not args_str:
                console.print("[red]Usage: delete <t>[/]")
                continue
            target_id = args_str

            tasks = plan_data.get("tasks", [])
            idx_to_del = next(
                (i for i, t in enumerate(tasks) if t.get("id") == target_id), -1
            )
            if idx_to_del == -1:
                console.print(f"[red]Error: task '{target_id}' not found.[/]")
                continue

            tasks.pop(idx_to_del)
            # Remove target_id from depends_on in other tasks
            for t in tasks:
                deps = t.get("depends_on", []) or []
                if target_id in deps:
                    deps.remove(target_id)
                    t["depends_on"] = deps

            changed = True
            console.print(f"[green]Deleted task '{target_id}'.[/]")

        elif cmd == "add":
            if not args_str:
                console.print("[red]Usage: add <title>[/]")
                continue
            title = args_str

            tasks = plan_data.get("tasks", [])
            max_num = 0
            for t in tasks:
                t_id = t.get("id", "")
                m = re.match(r"^T(\d+)$", t_id)
                if m:
                    max_num = max(max_num, int(m.group(1)))
            new_id = f"T{max_num + 1}"

            new_task = {
                "id": new_id,
                "title": title,
                "type": "implementation",
                "status": "planned",
                "agent": available_agents[0],
                "depends_on": [tasks[-1]["id"]] if tasks else [],
                "writes_files": True,
                "files_allowed": ["*"],
            }
            tasks.append(new_task)
            changed = True
            console.print(f"[green]Added task '{new_id}': {title}[/]")

        elif cmd == "insert":
            subparts = args_str.split(None, 1)
            if len(subparts) < 2:
                console.print("[red]Usage: insert <after_t> <title>[/]")
                continue
            after_t, title = subparts[0], subparts[1]

            tasks = plan_data.get("tasks", [])
            idx_after = next(
                (i for i, t in enumerate(tasks) if t.get("id") == after_t), -1
            )
            if idx_after == -1:
                console.print(f"[red]Error: task '{after_t}' not found.[/]")
                continue

            max_num = 0
            for t in tasks:
                t_id = t.get("id", "")
                m = re.match(r"^T(\d+)$", t_id)
                if m:
                    max_num = max(max_num, int(m.group(1)))
            new_id = f"T{max_num + 1}"

            new_task = {
                "id": new_id,
                "title": title,
                "type": "implementation",
                "status": "planned",
                "agent": available_agents[0],
                "depends_on": [after_t],
                "writes_files": True,
                "files_allowed": ["*"],
            }
            tasks.insert(idx_after + 1, new_task)
            changed = True
            console.print(f"[green]Inserted task '{new_id}' after '{after_t}'.[/]")

        elif cmd == "edit":
            subparts = args_str.split(None, 1)
            if len(subparts) < 2:
                console.print("[red]Usage: edit <t> <field>=<value>[/]")
                continue
            target_id, field_val = subparts[0], subparts[1]

            tasks = plan_data.get("tasks", [])
            idx_to_edit = next(
                (i for i, t in enumerate(tasks) if t.get("id") == target_id), -1
            )
            if idx_to_edit == -1:
                console.print(f"[red]Error: task '{target_id}' not found.[/]")
                continue

            if "=" not in field_val:
                console.print("[red]Error: field_val must be field=value[/]")
                continue

            field, val = field_val.split("=", 1)
            field = field.strip()
            val = val.strip()

            task = tasks[idx_to_edit]
            allowed_fields = (
                "title",
                "agent",
                "runtime",
                "type",
                "writes_files",
                "files_allowed",
                "depends_on",
            )
            if field not in allowed_fields:
                console.print(f"[red]Error: field must be one of {allowed_fields}[/]")
                continue

            if field == "title":
                task["title"] = val
            elif field == "agent":
                if val not in available_agents:
                    console.print(
                        f"[yellow]Warning: agent '{val}' is not in available agents: {available_agents}[/]"
                    )
                task["agent"] = val
            elif field == "runtime":
                task["runtime"] = val
            elif field == "type":
                task["type"] = val
            elif field == "writes_files":
                task["writes_files"] = val.lower() in ("true", "yes", "1")
            elif field == "files_allowed":
                task["files_allowed"] = [v.strip() for v in val.split(",") if v.strip()]
            elif field == "depends_on":
                task["depends_on"] = [v.strip() for v in val.split(",") if v.strip()]

            changed = True
            console.print(f"[green]Updated task '{target_id}' field '{field}'.[/]")

        else:
            console.print(f"[red]Unknown refinement command: {cmd}[/]")
            continue

        if changed:
            # Inject validation commands
            inject_validation_commands(plan_data["tasks"], repo_root)

            # Save plan-path
            try:
                with open(plan_path, "w", encoding="utf-8") as f:
                    yaml.dump(plan_data, f, default_flow_style=False, sort_keys=False)

                # Save task-list.yaml
                tasks_path = plan_path.parent / "task-list.yaml"
                with open(tasks_path, "w", encoding="utf-8") as f:
                    yaml.dump(
                        plan_data["tasks"], f, default_flow_style=False, sort_keys=False
                    )
            except Exception as e:
                console.print(f"[red]Error saving plan: {e}[/]")
                continue

            # Validate plan
            try:
                validate_mission_plan(plan_path, repo_root)
                console.print("[green]✓ Current plan is valid.[/]")
            except PlanValidationError as e:
                console.print("[yellow]⚠ Plan has validation errors/warnings:[/]")
                for err in e.errors:
                    console.print(f"  • [red]{err}[/]")
            except Exception as e:
                console.print(f"[red]Validation error: {e}[/]")


def run_mission_approve(
    console: Console, interactive: bool = False, mission_id: str | None = None
) -> None:
    """Approve the latest planned mission."""
    from niyam.core.config import find_niyam_root
    from niyam.core.errors import NiyamConfigError

    repo_root = find_niyam_root()
    if not repo_root:
        raise NiyamConfigError("Not a Niyam workspace. Run 'niyam init' first.")
    niyam_dir = get_niyam_dir(repo_root)

    mission_id = resolve_mission_id(niyam_dir, mission_id)
    if not mission_id:
        console.print("[bold red]Error:[/] No missions found.")
        raise SystemExit(1)

    run_dir = niyam_dir / "runs" / mission_id
    plan_path = run_dir / "mission-plan.yaml"

    if not plan_path.exists():
        console.print(f"[bold red]Error:[/] Mission plan for '{mission_id}' not found.")
        raise SystemExit(1)

    # Automatically validate plan before approval
    from niyam.mission.validator import validate_mission_plan, PlanValidationError

    try:
        validate_mission_plan(plan_path, repo_root)
    except PlanValidationError as e:
        console.print(
            "[bold red]❌ Mission approval rejected due to validation failures:[/]"
        )
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

    if status not in ("planned", "validated"):
        console.print(f"[yellow]Mission '{mission_id}' is already {status}.[/]")
        return

    if interactive:
        while True:
            # Re-load plan data
            with open(plan_path, encoding="utf-8") as f:
                plan_data = yaml.safe_load(f) or {}

            _print_preview_table(console, mission_id, plan_data)

            try:
                answer = input("Approve all tasks? [Y/n/edit/refine]: ").strip().lower()
            except (KeyboardInterrupt, EOFError):
                console.print("\n[red]Mission approval cancelled.[/]")
                raise SystemExit(1)

            if not answer or answer in ("y", "yes"):
                break
            elif answer in ("n", "no"):
                console.print("[red]Mission approval cancelled.[/]")
                raise SystemExit(1)
            elif answer == "refine":
                _run_refiner_loop(console, plan_path, repo_root, niyam_dir)
            elif answer == "edit":
                editor = os.environ.get("EDITOR", "nano")
                import subprocess

                try:
                    subprocess.run([editor, str(plan_path)], check=True)
                except Exception as e:
                    console.print(
                        f"[bold red]Failed to launch editor '{editor}':[/] {e}"
                    )
                    try:
                        subprocess.run(["vi", str(plan_path)], check=True)
                    except Exception:
                        pass

                # Re-validate
                try:
                    validate_mission_plan(plan_path, repo_root)
                    console.print("[bold green]✓ Edited plan is valid.[/]")
                except PlanValidationError as e:
                    console.print(
                        "[bold red]❌ Mission plan validation failed after editing:[/]"
                    )
                    for err in e.errors:
                        console.print(f"  • [red]{err}[/]")
                except Exception as e:
                    console.print(f"[bold red]Error during validation:[/] {e}")
            else:
                console.print(
                    "[yellow]Invalid option. Please choose y, n, edit, or refine.[/]"
                )

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

    console.print(
        f"[bold green]✓[/] Mission '[cyan]{mission_id}[/]' has been approved and is ready to start."
    )
