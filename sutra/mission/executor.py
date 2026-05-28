"""Sutra mission executor — run tasks in an approved plan."""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import threading
from datetime import datetime, timezone
import yaml
from rich.console import Console
from rich.panel import Panel

from sutra.core.config import get_sutra_dir, load_sutra_config, load_project_config
from sutra.mission.planner import get_latest_mission_id

# Locks for thread-safe operations
_print_lock = threading.Lock()
_validation_lock = threading.Lock()


def load_plan(run_dir: Path) -> dict:
    """Load mission plan YAML."""
    plan_path = run_dir / "mission-plan.yaml"
    with open(plan_path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def save_plan(run_dir: Path, plan_data: dict) -> None:
    """Save mission plan YAML and update task-list.yaml."""
    plan_path = run_dir / "mission-plan.yaml"
    with open(plan_path, "w", encoding="utf-8") as f:
        yaml.dump(plan_data, f, default_flow_style=False, sort_keys=False)

    tasks_path = run_dir / "task-list.yaml"
    with open(tasks_path, "w", encoding="utf-8") as f:
        yaml.dump(plan_data.get("tasks", []), f, default_flow_style=False, sort_keys=False)


def log_execution_event(run_dir: Path, event_type: str, task_id: str, details: str) -> None:
    """Log execution events to execution-log.json."""
    log_path = run_dir / "execution-log.json"
    events = []
    if log_path.exists():
        try:
            with open(log_path, encoding="utf-8") as f:
                events = json.load(f)
        except Exception:
            events = []

    events.append({
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "event": event_type,
        "task_id": task_id,
        "details": details,
    })

    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(events, f, indent=2)


def update_token_ledger(
    run_dir: Path,
    task_id: str,
    agent: str,
    runtime: str,
    input_tokens: int,
    output_tokens: int,
    baseline_multiplier: float = 5.0,
) -> None:
    """Update token & cost ledger with task metrics."""
    ledger_path = run_dir / "token-ledger.json"
    ledger = {"mission_id": run_dir.name, "events": [], "summary": {}}
    if ledger_path.exists():
        try:
            with open(ledger_path, encoding="utf-8") as f:
                ledger = json.load(f) or ledger
        except Exception:
            pass

    # Rates per million tokens
    rates = {
        "claude": {"input": 3.0, "output": 15.0},
        "gemini": {"input": 1.25, "output": 5.0},
        "default": {"input": 3.0, "output": 15.0},
    }
    r = rates.get(runtime.lower(), rates["default"])
    
    cost = (input_tokens * r["input"] + output_tokens * r["output"]) / 1_000_000.0
    
    baseline_input = int(input_tokens * baseline_multiplier)
    baseline_output = int(output_tokens * baseline_multiplier)
    baseline_total = baseline_input + baseline_output
    baseline_cost = (baseline_input * r["input"] + baseline_output * r["output"]) / 1_000_000.0
    
    savings_usd = baseline_cost - cost
    
    event = {
        "task_id": task_id,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "agent": agent,
        "runtime": runtime,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "cost_usd": cost,
        "baseline_tokens": baseline_total,
        "baseline_cost_usd": baseline_cost,
        "savings_usd": savings_usd,
    }
    
    events = ledger.setdefault("events", [])
    # Remove existing event for this task if we are re-running/resuming
    events = [e for e in events if e.get("task_id") != task_id]
    events.append(event)
    ledger["events"] = events
    
    # Calculate summary
    total_input = sum(e.get("input_tokens", 0) for e in events)
    total_output = sum(e.get("output_tokens", 0) for e in events)
    total_tokens = total_input + total_output
    total_cost = sum(e.get("cost_usd", 0.0) for e in events)
    
    total_baseline_tokens = sum(e.get("baseline_tokens", 0) for e in events)
    total_baseline_cost = sum(e.get("baseline_cost_usd", 0.0) for e in events)
    total_savings = total_baseline_cost - total_cost
    
    savings_pct = (total_savings / total_baseline_cost * 100.0) if total_baseline_cost > 0 else 0.0
    
    ledger["summary"] = {
        "total_input_tokens": total_input,
        "total_output_tokens": total_output,
        "total_tokens": total_tokens,
        "total_cost_usd": total_cost,
        "total_baseline_tokens": total_baseline_tokens,
        "total_baseline_cost_usd": total_baseline_cost,
        "total_savings_usd": total_savings,
        "savings_percent": savings_pct,
    }
    
    with open(ledger_path, "w", encoding="utf-8") as f:
        json.dump(ledger, f, indent=2)


def run_validation_command(cmd: str, run_dir: Path, cwd: Path, console: Console) -> bool:
    """Run a validation command and log the results."""
    with _print_lock:
        console.print(f"[dim]Running validation command: {cmd} inside {cwd}[/]")
    res = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    
    # Save output to validation-results.md
    val_path = run_dir / "validation-results.md"
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    with _validation_lock:
        mode = "a" if val_path.exists() else "w"
        with open(val_path, mode, encoding="utf-8") as f:
            f.write(f"\n## Validation Run - {timestamp}\n")
            f.write(f"**Command:** `{cmd}`\n")
            f.write(f"**Exit Code:** `{res.returncode}`\n\n")
            f.write("### stdout\n```\n" + res.stdout + "\n```\n")
            if res.stderr:
                f.write("### stderr\n```\n" + res.stderr + "\n```\n")
            
    return res.returncode == 0


# ── Git Worktree & Branching Utilities ─────────────────────────────────

def is_git_repo(repo_root: Path) -> bool:
    """Check if the project root is a Git repository."""
    return (repo_root / ".git").exists()


def get_current_head(repo_root: Path) -> str:
    """Get the current branch name or commit hash of main repo."""
    res = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    if res.returncode == 0 and res.stdout.strip() != "HEAD":
        return res.stdout.strip()
    
    res = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    if res.returncode == 0:
        return res.stdout.strip()
    return "main"


def git_has_commits(repo_root: Path) -> bool:
    """Check if the Git repository has any commits."""
    res = subprocess.run(
        ["git", "rev-parse", "--verify", "HEAD"],
        cwd=repo_root,
        capture_output=True,
    )
    return res.returncode == 0


def branch_exists(repo_root: Path, branch_name: str) -> bool:
    """Check if a local Git branch exists."""
    res = subprocess.run(
        ["git", "show-ref", "--verify", f"refs/heads/{branch_name}"],
        cwd=repo_root,
        capture_output=True,
    )
    return res.returncode == 0


def cleanup_worktree(repo_root: Path, worktree_path: Path, branch_name: str, console: Console) -> None:
    """Force-remove a git worktree and cleanup directories."""
    if worktree_path.exists():
        subprocess.run(
            ["git", "worktree", "remove", "--force", str(worktree_path)],
            cwd=repo_root,
            capture_output=True,
        )
        if worktree_path.exists():
            try:
                shutil.rmtree(worktree_path)
            except Exception:
                pass
    subprocess.run(
        ["git", "worktree", "prune"],
        cwd=repo_root,
        capture_output=True,
    )


def copy_sutra_to_worktree(repo_root: Path, worktree_path: Path) -> None:
    """Copy .sutra/ configuration (excluding runs/worktrees) to worktree."""
    src_sutra = repo_root / ".sutra"
    dst_sutra = worktree_path / ".sutra"
    if not src_sutra.is_dir():
        return
    
    if dst_sutra.exists():
        try:
            shutil.rmtree(dst_sutra)
        except Exception:
            pass
            
    dst_sutra.mkdir(parents=True, exist_ok=True)
    for item in src_sutra.iterdir():
        if item.name in ("runs", "worktrees"):
            continue
        try:
            if item.is_dir():
                shutil.copytree(item, dst_sutra / item.name)
            else:
                shutil.copy2(item, dst_sutra / item.name)
        except Exception:
            pass


def create_worktree(repo_root: Path, run_dir: Path, mission_id: str, task: dict, console: Console) -> Path:
    """Create a git worktree for a task, branching and merging dependencies."""
    task_id = task["id"]
    worktree_path = run_dir / "worktrees" / task_id
    branch_name = f"sutra-{mission_id}-{task_id}"
    
    cleanup_worktree(repo_root, worktree_path, branch_name, console)
    worktree_path.parent.mkdir(parents=True, exist_ok=True)
    
    if branch_exists(repo_root, branch_name):
        with _print_lock:
            console.print(f"[{task_id}] [dim]Worktree branch {branch_name} already exists. Reusing branch...[/]")
        subprocess.run(
            ["git", "worktree", "add", str(worktree_path), branch_name],
            cwd=repo_root,
            check=True,
            capture_output=True,
        )
    else:
        deps = task.get("depends_on", [])
        if not deps:
            parent_commit = get_current_head(repo_root)
        else:
            parent_commit = f"sutra-{mission_id}-{deps[0]}"
            
        with _print_lock:
            console.print(f"[{task_id}] [dim]Creating branch {branch_name} from parent {parent_commit}...[/]")
            
        subprocess.run(
            ["git", "worktree", "add", "-b", branch_name, str(worktree_path), parent_commit],
            cwd=repo_root,
            check=True,
            capture_output=True,
        )
        
        # Merge other dependencies if any
        if len(deps) > 1:
            for other_dep in deps[1:]:
                other_branch = f"sutra-{mission_id}-{other_dep}"
                with _print_lock:
                    console.print(f"[{task_id}] [dim]Merging dependency branch {other_branch} into {branch_name}...[/]")
                res = subprocess.run(
                    ["git", "merge", other_branch, "-m", f"Merge dependency {other_dep}"],
                    cwd=worktree_path,
                    capture_output=True,
                    text=True,
                )
                if res.returncode != 0:
                    with _print_lock:
                        console.print(f"[{task_id}] [bold red]Merge conflict:[/] Failed to merge {other_branch} into {branch_name}.\n{res.stderr or res.stdout}")
                    raise RuntimeError(f"Merge conflict: failed to merge {other_branch} into {branch_name}")
                    
    copy_sutra_to_worktree(repo_root, worktree_path)
    return worktree_path


def commit_worktree_changes(worktree_path: Path, task_id: str, console: Console) -> None:
    """Commit all changes made inside the worktree branch."""
    res_status = subprocess.run(
        ["git", "status", "--porcelain", "--", ":!.sutra"],
        cwd=worktree_path,
        capture_output=True,
        text=True,
        check=True,
    )
    if not res_status.stdout.strip():
        with _print_lock:
            console.print(f"[{task_id}] [dim]No changes to commit for task {task_id}.[/]")
        return
        
    subprocess.run(
        ["git", "add", "-A", "--", ":!.sutra"],
        cwd=worktree_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-m", f"Complete task {task_id}"],
        cwd=worktree_path,
        check=True,
        capture_output=True,
    )
    with _print_lock:
        console.print(f"[{task_id}] [dim]Committed changes successfully.[/]")


def find_leaf_tasks(tasks: list[dict]) -> list[str]:
    """Find task IDs that no other task depends on."""
    all_ids = {t["id"] for t in tasks if t["status"] == "completed"}
    dependent_ids = set()
    for t in tasks:
        for dep in t.get("depends_on", []):
            dependent_ids.add(dep)
    return list(all_ids - dependent_ids)


def merge_final_changes(repo_root: Path, mission_id: str, tasks: list[dict], console: Console) -> None:
    """Merge leaf task branches of the completed mission back into main workspace."""
    leaf_ids = find_leaf_tasks(tasks)
    if not leaf_ids:
        console.print("[yellow]No completed leaf tasks to merge.[/]")
        return
        
    for leaf_id in leaf_ids:
        branch_name = f"sutra-{mission_id}-{leaf_id}"
        console.print(f"[cyan]Merging final branch {branch_name} into workspace...[/]")
        
        res = subprocess.run(
            ["git", "merge", branch_name, "-m", f"Merge completed mission task {leaf_id}"],
            cwd=repo_root,
            capture_output=True,
            text=True,
        )
        if res.returncode != 0:
            console.print(f"[bold red]Merge conflict during final integration:[/] Failed to merge {branch_name} back to main workspace.\n{res.stderr or res.stdout}")
            raise RuntimeError(f"Merge conflict during final integration of {branch_name}")
            
        console.print(f"[bold green]✓[/] Successfully integrated changes from branch [cyan]{branch_name}[/].")


def delete_mission_branches(repo_root: Path, mission_id: str, tasks: list[dict], console: Console) -> None:
    """Clean up temporary task branches and prune worktrees."""
    for t in tasks:
        branch_name = f"sutra-{mission_id}-{t['id']}"
        if branch_exists(repo_root, branch_name):
            subprocess.run(
                ["git", "branch", "-D", branch_name],
                cwd=repo_root,
                capture_output=True,
            )
    subprocess.run(
        ["git", "worktree", "prune"],
        cwd=repo_root,
        capture_output=True,
    )


# ── Task Execution Thread Runner ───────────────────────────────────────

def execute_single_task(
    task: dict,
    run_dir: Path,
    sutra_dir: Path,
    repo_root: Path,
    mission_id: str,
    use_worktree: bool,
    project_config: any,
    console: Console,
) -> bool:
    """Execute a single task, isolating in worktree if enabled."""
    task_id = task["id"]
    task_cwd = repo_root
    worktree_path = None
    branch_name = f"sutra-{mission_id}-{task_id}"
    
    if use_worktree:
        try:
            worktree_path = create_worktree(repo_root, run_dir, mission_id, task, console)
            task_cwd = worktree_path
        except Exception as e:
            with _print_lock:
                console.print(f"[{task_id}] [bold red]Failed to setup worktree:[/] {e}")
            return False
            
    # Formulate prompt
    agent_file = (worktree_path / ".sutra" if use_worktree else sutra_dir) / "agents" / f"{task['agent']}.md"
    agent_instruction = ""
    if agent_file.exists():
        agent_instruction = agent_file.read_text(encoding="utf-8")
        
    requirement_file = run_dir / "requirement.md"
    requirement_content = ""
    if requirement_file.exists():
        requirement_content = requirement_file.read_text(encoding="utf-8")
        
    prompt_text = f"""TASK {task_id}: {task['title']}
Type: {task.get('type', 'generic')}
Assigned Agent: {task['agent']}

--- AGENT SYSTEM PROMPT ---
{agent_instruction}

--- MISSION REQUIREMENT ---
{requirement_content}

--- INSTRUCTIONS ---
Please execute the changes required for this task.
Only modify files allowed under: {task.get('files_allowed', ['Any'])}
Do not perform destructive operations.
"""
    # Write prompt
    prompt_path = (worktree_path if use_worktree else run_dir) / f"task-{task_id}-prompt.md"
    prompt_path.write_text(prompt_text, encoding="utf-8")
    
    is_test = os.environ.get("SUTRA_TEST") == "1"
    success = True
    
    if is_test:
        with _print_lock:
            console.print(f"[{task_id}] [dim]Mocking execution of {task_id}...[/]")
        log_execution_event(run_dir, "TASK_EXECUTION_MOCK", task_id, "Mocked execution successfully.")
        
        # Write dummy file to record change in worktree git diff
        if use_worktree and worktree_path:
            dummy_file = worktree_path / f"change-{task_id}.txt"
            dummy_file.write_text(f"Changes by task {task_id}", encoding="utf-8")
    else:
        plan_data = load_plan(run_dir)
        mission_meta = plan_data.get("mission", {})
        orchestrator = mission_meta.get("orchestrator", "claude")
        parallel_limit = mission_meta.get("parallel", 1)
        
        if shutil.which(orchestrator):
            with _print_lock:
                console.print(f"[{task_id}] [cyan]Invoking {orchestrator} CLI...[/]")
            try:
                if parallel_limit == 1:
                    # Sequential: full interactive pass-through
                    subprocess.run([orchestrator, str(prompt_path)], cwd=task_cwd, check=True)
                else:
                    # Parallel: headless execution
                    task_log_path = (worktree_path if use_worktree else run_dir) / f"task-{task_id}-output.log"
                    with open(task_log_path, "w", encoding="utf-8") as log_f:
                        subprocess.run(
                            [orchestrator, str(prompt_path)],
                            cwd=task_cwd,
                            stdin=subprocess.DEVNULL,
                            stdout=log_f,
                            stderr=log_f,
                            check=True,
                        )
            except subprocess.CalledProcessError as e:
                if parallel_limit > 1:
                    with _print_lock:
                        console.print(f"[{task_id}] [red]Orchestrator failed in parallel execution: {e}[/]")
                        console.print(f"[{task_id}] To complete this task manually, run:")
                        console.print(f"  [bold]cat {prompt_path}[/]")
                    success = False
                else:
                    with _print_lock:
                        console.print(f"[yellow]Warning: {orchestrator} command failed. Asking for manual confirmation.[/]")
                    try:
                        input("Press Enter once you have completed the task manually in Claude/Codex...")
                    except (KeyboardInterrupt, EOFError):
                        success = False
        else:
            if parallel_limit > 1:
                with _print_lock:
                    console.print(f"[{task_id}] [red]Orchestrator '{orchestrator}' CLI not found in PATH.[/]")
                    console.print(f"[{task_id}] To complete this task manually, run:")
                    console.print(f"  [bold]cat {prompt_path}[/]")
                success = False
            else:
                with _print_lock:
                    console.print(f"[yellow]Orchestrator '{orchestrator}' CLI not found in PATH.[/]")
                    console.print(f"Please run the task using the prompt at:")
                    console.print(f"  [bold]cat {prompt_path}[/]")
                    console.print("\nPress Enter once you have executed the prompt and completed the work...")
                try:
                    input()
                except (KeyboardInterrupt, EOFError):
                    success = False
                    
    # Validation
    if success and project_config and project_config.validation:
        v_cmds = project_config.validation
        test_cmd = v_cmds.test or v_cmds.build
        if test_cmd:
            success = run_validation_command(test_cmd, run_dir, task_cwd, console)
            if not success:
                with _print_lock:
                    console.print(f"[{task_id}] [bold red]❌ Validation failed! Check validation-results.md[/]")
                log_execution_event(run_dir, "TASK_FAILED", task_id, "Task validation failed.")
                
    # Record token usage in the ledger
    try:
        # Estimate input tokens
        input_tokens = 0
        if prompt_path.exists():
            try:
                prompt_content = prompt_path.read_text(encoding="utf-8")
                input_tokens = max(1, len(prompt_content) // 4)
            except Exception:
                pass

        # Estimate output tokens
        output_tokens = 0
        task_log_path = (worktree_path if use_worktree else run_dir) / f"task-{task_id}-output.log"
        if task_log_path.exists():
            try:
                output_content = task_log_path.read_text(encoding="utf-8")
                output_tokens = len(output_content) // 4
            except Exception:
                pass
        
        # If output_tokens is 0 (e.g. sequential mode, or log is empty), try git diff
        if output_tokens == 0 and is_git_repo(repo_root):
            try:
                if use_worktree and worktree_path:
                    diff_cmd = ["git", "diff", "HEAD~1", "HEAD"] if success else ["git", "diff"]
                    diff_res = subprocess.run(
                        diff_cmd,
                        cwd=worktree_path,
                        capture_output=True,
                        text=True,
                    )
                else:
                    diff_res = subprocess.run(
                        ["git", "diff"],
                        cwd=repo_root,
                        capture_output=True,
                        text=True,
                    )
                if diff_res.returncode == 0 and diff_res.stdout:
                    output_tokens = max(1, len(diff_res.stdout) // 4)
            except Exception:
                pass

        if output_tokens == 0 and success:
            output_tokens = 250  # fallback for a successful task

        # Get baseline_multiplier
        baseline_multiplier = 5.0
        try:
            sutra_yaml_path = sutra_dir / "sutra.yaml"
            if sutra_yaml_path.exists():
                with open(sutra_yaml_path, encoding="utf-8") as f:
                    s_conf = yaml.safe_load(f) or {}
                    baseline_multiplier = float(s_conf.get("baseline_multiplier", 5.0))
        except Exception:
            pass

        # Get active runtime
        plan_data = load_plan(run_dir)
        mission_meta = plan_data.get("mission", {})
        orchestrator = mission_meta.get("orchestrator", "claude")

        update_token_ledger(
            run_dir=run_dir,
            task_id=task_id,
            agent=task["agent"],
            runtime=orchestrator,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            baseline_multiplier=baseline_multiplier,
        )
    except Exception as e:
        with _print_lock:
            console.print(f"[{task_id}] [yellow]Warning: Failed to update token ledger:[/] {e}")

    # Commit changes if worktree is active and task succeeded
    if success and use_worktree and worktree_path:
        try:
            commit_worktree_changes(worktree_path, task_id, console)
        except Exception as e:
            with _print_lock:
                console.print(f"[{task_id}] [bold red]Failed to commit changes:[/] {e}")
            success = False
            
    # Cleanup worktree
    if use_worktree and worktree_path:
        cleanup_worktree(repo_root, worktree_path, branch_name, console)
        
    return success


# ── Public Entry Points ───────────────────────────────────────────────

def run_mission_start(console: Console, parallel: int | None = None, worktree: bool | None = None) -> None:
    """Start or resume the latest approved mission."""
    repo_root = Path.cwd()
    sutra_dir = get_sutra_dir(repo_root)

    mission_id = get_latest_mission_id(sutra_dir)
    if not mission_id:
        console.print("[bold red]Error:[/] No missions found.")
        raise SystemExit(1)

    run_dir = sutra_dir / "runs" / mission_id
    approval_path = run_dir / "approval.json"

    # Check approval
    if not approval_path.exists():
        console.print("[bold red]Error:[/] Mission has not been approved.")
        raise SystemExit(1)

    with open(approval_path, encoding="utf-8") as f:
        app_data = json.load(f)
    if not app_data.get("approved", False):
        console.print("[bold red]Error:[/] Mission has not been approved yet.")
        raise SystemExit(1)

    # Load plan
    plan_data = load_plan(run_dir)
    mission_meta = plan_data.get("mission", {})
    status = mission_meta.get("status", "planned")

    if status in ("completed", "failed"):
        console.print(f"[yellow]Mission '{mission_id}' is already {status}.[/]")
        return

    # Determine execution options
    plan_parallel = mission_meta.get("parallel", 1)
    plan_worktree = mission_meta.get("worktree", True)

    parallel_limit = parallel if parallel is not None else plan_parallel
    use_worktree = worktree if worktree is not None else plan_worktree
    
    # Check Git repository requirement
    is_git = is_git_repo(repo_root)
    if use_worktree:
        if not is_git:
            if worktree is True:
                console.print("[bold red]Error:[/] Git worktree isolation was requested, but this is not a Git repository.")
                raise SystemExit(1)
            else:
                if parallel_limit > 1:
                    console.print("[bold red]Error:[/] Parallel execution (concurrency > 1) requires a Git repository for worktree isolation.")
                    raise SystemExit(1)
                else:
                    use_worktree = False
        elif not git_has_commits(repo_root):
            if worktree is True:
                console.print("[bold red]Error:[/] Git worktree isolation requires the repository to have at least one commit.")
                raise SystemExit(1)
            else:
                if parallel_limit > 1:
                    console.print("[bold red]Error:[/] Parallel execution (concurrency > 1) requires a Git repository with at least one commit for worktree isolation.")
                    raise SystemExit(1)
                else:
                    use_worktree = False

    # Save the resolved settings and update status to running
    plan_data["mission"]["parallel"] = parallel_limit
    plan_data["mission"]["worktree"] = use_worktree
    plan_data["mission"]["status"] = "running"
    save_plan(run_dir, plan_data)
    log_execution_event(run_dir, "MISSION_STARTED", "", f"Mission execution started (parallel={parallel_limit}, worktree={use_worktree}).")

    # Read project.yaml validation commands
    project_config = None
    try:
        project_config = load_project_config(repo_root)
    except Exception:
        pass

    tasks = plan_data.get("tasks", [])
    completed_tasks = {t["id"] for t in tasks if t["status"] == "completed"}
    failed_tasks = {t["id"] for t in tasks if t["status"] == "failed"}
    running_tasks = set()
    futures_map = {}
    
    import concurrent.futures
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=parallel_limit) as executor:
        while True:
            # Check if mission has been paused from outside
            current_plan = load_plan(run_dir)
            if current_plan["mission"]["status"] == "paused":
                with _print_lock:
                    console.print("[yellow]Mission execution paused. Waiting for active tasks to finish...[/]")
                if futures_map:
                    concurrent.futures.wait(futures_map.keys())
                return
                
            # Find ready tasks
            ready_tasks = []
            task_by_id = {task["id"]: task for task in tasks}
            for t in tasks:
                t_id = t["id"]
                if t["status"] == "pending" and t_id not in running_tasks:
                    deps = t.get("depends_on", [])
                    finished_statuses = {"completed", "failed", "skipped"}
                    dep_tasks = [task_by_id[dep] for dep in deps if dep in task_by_id]
                    
                    if all(dt["status"] in finished_statuses for dt in dep_tasks):
                        # If any dependency failed or was skipped, this task must be skipped
                        if any(dt["status"] in {"failed", "skipped"} for dt in dep_tasks):
                            t["status"] = "skipped"
                            save_plan(run_dir, plan_data)
                            log_execution_event(run_dir, "TASK_SKIPPED", t_id, f"Dependency failed or was skipped, skipping task.")
                            continue
                        ready_tasks.append(t)
                        
            # Submit ready tasks up to concurrency capacity
            for t in ready_tasks:
                if len(running_tasks) < parallel_limit:
                    t_id = t["id"]
                    running_tasks.add(t_id)
                    t["status"] = "running"
                    save_plan(run_dir, plan_data)
                    log_execution_event(run_dir, "TASK_STARTED", t_id, f"Running task: {t['title']}")
                    
                    with _print_lock:
                        console.print(Panel(
                            f"Running Task [cyan]{t_id}[/]: {t['title']}\nAgent: [bold]{t['agent']}[/]",
                            title=f"[bold]Task {t_id}[/]",
                            border_style="cyan"
                        ))
                    
                    # Submit task execution
                    future = executor.submit(
                        execute_single_task,
                        task=t,
                        run_dir=run_dir,
                        sutra_dir=sutra_dir,
                        repo_root=repo_root,
                        mission_id=mission_id,
                        use_worktree=use_worktree,
                        project_config=project_config,
                        console=console,
                    )
                    futures_map[future] = t
                    
            # If nothing is running and no more tasks are ready, we are done
            if not futures_map:
                break
                
            # Wait for at least one future to complete
            done, _ = concurrent.futures.wait(futures_map.keys(), return_when=concurrent.futures.FIRST_COMPLETED)
            
            for future in done:
                t = futures_map.pop(future)
                t_id = t["id"]
                running_tasks.remove(t_id)
                
                try:
                    success = future.result()
                    if success:
                        t["status"] = "completed"
                        completed_tasks.add(t_id)
                        save_plan(run_dir, plan_data)
                        log_execution_event(run_dir, "TASK_COMPLETED", t_id, f"Completed task: {t['title']}")
                        with _print_lock:
                            console.print(f"[bold green]✓[/] Task {t_id} completed successfully.\n")
                    else:
                        t["status"] = "failed"
                        failed_tasks.add(t_id)
                        save_plan(run_dir, plan_data)
                        log_execution_event(run_dir, "TASK_FAILED", t_id, f"Task execution failed.")
                        with _print_lock:
                            console.print(f"[bold red]❌[/] Task {t_id} failed.\n")
                except Exception as e:
                    t["status"] = "failed"
                    failed_tasks.add(t_id)
                    save_plan(run_dir, plan_data)
                    log_execution_event(run_dir, "TASK_FAILED", t_id, f"Exception during task execution: {e}")
                    with _print_lock:
                        console.print(f"[bold red]❌[/] Task {t_id} failed with exception: {e}\n")

    # Determine final mission status
    final_plan = load_plan(run_dir)
    tasks_list = final_plan.get("tasks", [])
    any_failed = any(t["status"] == "failed" for t in tasks_list)
    any_skipped_due_to_failure = any(t["status"] == "skipped" for t in tasks_list)
    
    if any_failed or any_skipped_due_to_failure:
        final_plan["mission"]["status"] = "failed"
        save_plan(run_dir, final_plan)
        log_execution_event(run_dir, "MISSION_FAILED", "", "Mission execution failed due to task failures.")
        console.print(Panel("[bold red]❌ Mission execution failed.[/]", title="[bold red]Mission Failed[/]", border_style="red"))
        raise SystemExit(1)
        
    # Success integration (merge back if worktree was used)
    if use_worktree and is_git:
        try:
            merge_final_changes(repo_root, mission_id, tasks_list, console)
            delete_mission_branches(repo_root, mission_id, tasks_list, console)
        except Exception as e:
            console.print(f"[bold red]Error integrating final changes:[/] {e}")
            final_plan["mission"]["status"] = "failed"
            save_plan(run_dir, final_plan)
            raise SystemExit(1)

    # Complete mission
    final_plan["mission"]["status"] = "completed"
    save_plan(run_dir, final_plan)
    log_execution_event(run_dir, "MISSION_COMPLETED", "", "All tasks completed successfully.")
    console.print(Panel("[bold green]✓ Mission execution completed successfully![/]\nRun `sutra mission report` to generate evidence.", title="[bold green]Mission Success[/]", border_style="green"))


def run_mission_pause(console: Console) -> None:
    """Pause the currently running mission."""
    repo_root = Path.cwd()
    sutra_dir = get_sutra_dir(repo_root)

    mission_id = get_latest_mission_id(sutra_dir)
    if not mission_id:
        console.print("[bold red]Error:[/] No missions found.")
        raise SystemExit(1)

    run_dir = sutra_dir / "runs" / mission_id
    plan_data = load_plan(run_dir)
    status = plan_data["mission"]["status"]

    if status != "running":
        console.print(f"[yellow]Mission is not running (current status: {status}).[/]")
        return

    plan_data["mission"]["status"] = "paused"
    save_plan(run_dir, plan_data)
    log_execution_event(run_dir, "MISSION_PAUSED", "", "Mission paused by user.")
    console.print(f"[bold green]✓[/] Mission '[cyan]{mission_id}[/]' has been paused.")


def run_mission_resume(console: Console, parallel: int | None = None, worktree: bool | None = None) -> None:
    """Resume a paused mission."""
    repo_root = Path.cwd()
    sutra_dir = get_sutra_dir(repo_root)

    mission_id = get_latest_mission_id(sutra_dir)
    if not mission_id:
        console.print("[bold red]Error:[/] No missions found.")
        raise SystemExit(1)

    run_dir = sutra_dir / "runs" / mission_id
    plan_data = load_plan(run_dir)
    status = plan_data["mission"]["status"]

    if status != "paused":
        console.print(f"[yellow]Mission is not paused (current status: {status}).[/]")
        return

    # Start the execution
    run_mission_start(console, parallel=parallel, worktree=worktree)
