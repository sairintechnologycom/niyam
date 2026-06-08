"""Niyam multi-lens review manager — structured reviews from different perspectives."""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import json
from rich.console import Console
from rich.panel import Panel

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
REVIEWS_DIR = TEMPLATES_DIR / "reviews"


def is_binary_file(path: Path) -> bool:
    try:
        with open(path, "rb") as f:
            chunk = f.read(1024)
            return b"\x00" in chunk
    except Exception:
        return True


def redact_secrets(content: str) -> str:
    import re

    # AWS access key ID
    content = re.sub(r"AKIA[A-Z0-9]{16}", "[REDACTED_AWS_KEY]", content)
    # Generic secret pattern
    secret_pattern = re.compile(
        r"(?i)(api[_-]?key|secret|password|passwd|token|private[_-]?key)\s*[:=]\s*([\"'])([a-zA-Z0-9_\-\.\:\/\+]{12,})(\2)",
        re.IGNORECASE,
    )
    content = secret_pattern.sub(r"\1 = \2[REDACTED_SECRET]\4", content)
    return content


def get_git_diff(repo_root: Path | None = None) -> str:
    """Fetch the current git diff of tracked and untracked changes with safety caps."""
    if repo_root is None:
        from niyam.core.config import find_niyam_root

        repo_root = find_niyam_root() or Path.cwd()

    try:
        # Get diff of tracked files
        res = subprocess.run(
            ["git", "diff"], cwd=repo_root, capture_output=True, text=True
        )
        tracked = res.stdout if res.returncode == 0 else ""

        # Get diff of staged files
        res_staged = subprocess.run(
            ["git", "diff", "--cached"], cwd=repo_root, capture_output=True, text=True
        )
        staged = res_staged.stdout if res_staged.returncode == 0 else ""

        # Get untracked files
        res_untracked = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            cwd=repo_root,
            capture_output=True,
            text=True,
        )
        untracked_files = (
            res_untracked.stdout.splitlines() if res_untracked.returncode == 0 else []
        )

        MAX_UNTRACKED_FILE_SIZE = 50 * 1024  # 50 KB
        MAX_UNTRACKED_BUDGET = 200 * 1024  # 200 KB
        total_budget_used = 0

        untracked = ""
        for f in untracked_files:
            file_path = repo_root / f
            if file_path.is_file():
                if is_binary_file(file_path):
                    continue

                file_size = file_path.stat().st_size
                if file_size > MAX_UNTRACKED_FILE_SIZE:
                    untracked += f"\n\n--- Untracked File: {f} (Skipped: exceeds 50 KB size limit) ---\n"
                    continue

                if total_budget_used + file_size > MAX_UNTRACKED_BUDGET:
                    untracked += f"\n\n--- Untracked File: {f} (Skipped: exceeds total prompt budget limit) ---\n"
                    continue

                try:
                    content = file_path.read_text(encoding="utf-8")
                    content = redact_secrets(content)
                    untracked += f"\n\n--- Untracked File: {f} ---\n{content}"
                    total_budget_used += file_size
                except Exception:
                    pass

        # Also redact secrets from tracked and staged diffs
        combined_diff = (staged + "\n" + tracked + "\n" + untracked).strip()
        return redact_secrets(combined_diff)
    except Exception:
        return ""


def get_task_review_content(repo_root: Path, task_id: str, console: Console) -> str | None:
    """Fetch task diff, validation results, and execution details for review."""
    from niyam.core.config import get_niyam_dir
    from niyam.mission.planner import resolve_mission_id
    from niyam.mission.utils import load_plan

    niyam_dir = get_niyam_dir(repo_root)
    mission_id = resolve_mission_id(niyam_dir)
    if not mission_id:
        return None

    run_dir = niyam_dir / "runs" / mission_id
    plan_data = load_plan(run_dir)
    
    target_task = None
    for t in plan_data.get("tasks", []):
        if t["id"] == task_id:
            target_task = t
            break

    if not target_task:
        return None

    task_dir = run_dir / "tasks" / task_id
    content = f"# Code Review for Task {task_id}: {target_task.get('title')}\n\n"
    content += f"## Task Contract\n```json\n{json.dumps(target_task, indent=2)}\n```\n\n"
    
    diff_path = task_dir / "diff.patch"
    if diff_path.exists():
        content += f"## Git Diff\n```diff\n{redact_secrets(diff_path.read_text(encoding='utf-8'))}\n```\n\n"
    else:
        content += "## Git Diff\nNo diff available for this task.\n\n"

    validation_path = task_dir / "validation.json"
    if validation_path.exists():
        try:
            val_data = json.loads(validation_path.read_text(encoding="utf-8"))
            content += f"## Validation Results\n```json\n{json.dumps(val_data, indent=2)}\n```\n\n"
        except Exception:
            pass

    log_path = task_dir / "output.log"
    if log_path.exists():
        log_text = log_path.read_text(encoding="utf-8")
        if len(log_text) > 2000:
            log_text = log_text[-2000:]
        content += f"## Executor Summary (tail)\n```text\n{log_text}\n```\n\n"

    return content


def run_review(
    lens: str,
    runtime: str,
    mode: str,
    console: Console,
    task_id: str | None = None,
) -> None:
    """Run code review with the specified lens, runtime, and mode."""
    from niyam.core.config import find_niyam_root
    from niyam.core.errors import NiyamConfigError

    repo_root = find_niyam_root()
    if not repo_root:
        raise NiyamConfigError("Not a Niyam workspace. Run 'niyam init' first.")

    # 1. Fetch review content
    review_content = ""
    
    if task_id:
        review_content = get_task_review_content(repo_root, task_id, console)
        if not review_content:
            console.print(f"[bold red]Error:[/] Could not retrieve evidence for task '{task_id}'.")
            return
    elif lens == "evidence":
        from niyam.core.config import get_niyam_dir
        from niyam.mission.planner import resolve_mission_id
        niyam_dir = get_niyam_dir(repo_root)
        mission_id = resolve_mission_id(niyam_dir)
        if not mission_id:
            console.print("[yellow]No active mission found to collect evidence from.[/]")
            return
        
        evidence_path = niyam_dir / "runs" / mission_id / "evidence.md"
        if not evidence_path.exists():
            console.print("[yellow]Evidence report not found. Generating it...[/]")
            from niyam.mission.reporter import run_mission_report
            run_mission_report(console=console, mission_id=mission_id)
        
        if evidence_path.exists():
            review_content = evidence_path.read_text(encoding="utf-8")
        else:
            console.print("[red]Error: Failed to generate or locate evidence.md[/]")
            return
    else:
        review_content = get_git_diff(repo_root)

    if not review_content:
        if lens == "evidence":
            console.print("[yellow]No evidence found to review.[/]")
        else:
            console.print(
                "[yellow]No local changes detected to review. Try making some changes first.[/]"
            )
        return

    # 2. Get template
    template_path = REVIEWS_DIR / f"{lens}.md"
    if not template_path.exists():
        console.print(
            f"[bold red]Error:[/] Review template for lens '{lens}' not found."
        )
        return

    template_content = template_path.read_text(encoding="utf-8")

    # 3. Apply mode modification
    prefix = ""
    if mode == "adversarial":
        prefix = (
            "> [!WARNING]\n"
            "> **ADVERSARIAL MODE ENABLED**\n"
            "> You are acting as an adversarial, highly critical reviewer. "
            "Aggressively seek out bugs, race conditions, design flaws, styling inconsistencies, and security issues. "
            "Do not accept compromises. Critique every line of the content below.\n\n"
        )

    if task_id or lens == "evidence":
        compiled_prompt = prefix + template_content.replace("{{evidence_content}}", review_content).replace("{{git_diff}}", review_content)
    else:
        compiled_prompt = prefix + template_content.replace("{{git_diff}}", review_content)

    # 4. Show or run prompt
    console.print(
        Panel(
            f"Lens: [bold cyan]{lens.upper()}[/]\n"
            f"Runtime: [bold cyan]{runtime}[/]\n"
            f"Mode: [bold cyan]{mode.upper()}[/]",
            title="[bold]Code Review Plan[/]",
            border_style="cyan",
        )
    )

    # Save to a temporary prompt file for reference
    temp_dir = repo_root / ".niyam" / "runs"
    temp_dir.mkdir(parents=True, exist_ok=True)
    prompt_file = temp_dir / f"review-{lens}-{mode}-prompt.md"
    prompt_file.write_text(compiled_prompt, encoding="utf-8")

    is_test = os.environ.get("NIYAM_TEST") == "1"

    if is_test:
        console.print("[dim]Mocking review execution...[/]")
        console.print("[green]✓[/] Code review successfully generated.")
    else:
        if shutil.which(runtime):
            console.print(f"[cyan]Invoking {runtime} CLI for review...[/]")
            try:
                subprocess.run([runtime, str(prompt_file)], check=True)
            except Exception:
                console.print(f"[yellow]Warning: {runtime} execution failed.[/]")
                console.print(
                    "Here is the review prompt. You can copy-paste it into your AI session:\n"
                )
                console.print(compiled_prompt)
        else:
            console.print(f"[yellow]CLI '{runtime}' not found in PATH.[/]")
            console.print(
                "Here is the generated review prompt. You can copy-paste it into your session:\n"
            )
            console.print(compiled_prompt)
            console.print(f"\n[dim]Prompt also saved to: {prompt_file}[/]")
