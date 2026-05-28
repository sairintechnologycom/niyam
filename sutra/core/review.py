"""Sutra multi-lens review manager — structured reviews from different perspectives."""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
from rich.console import Console
from rich.panel import Panel

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
REVIEWS_DIR = TEMPLATES_DIR / "reviews"


def get_git_diff() -> str:
    """Fetch the current git diff of tracked and untracked changes."""
    try:
        # Get diff of tracked files
        res = subprocess.run(["git", "diff"], capture_output=True, text=True)
        tracked = res.stdout if res.returncode == 0 else ""

        # Get diff of staged files
        res_staged = subprocess.run(["git", "diff", "--cached"], capture_output=True, text=True)
        staged = res_staged.stdout if res_staged.returncode == 0 else ""

        # Get untracked files
        res_untracked = subprocess.run(["git", "ls-files", "--others", "--exclude-standard"], capture_output=True, text=True)
        untracked_files = res_untracked.stdout.splitlines() if res_untracked.returncode == 0 else []

        untracked = ""
        for f in untracked_files:
            if Path(f).is_file():
                try:
                    content = Path(f).read_text(encoding="utf-8")
                    untracked += f"\n\n--- Untracked File: {f} ---\n{content}"
                except Exception:
                    pass

        return (staged + "\n" + tracked + "\n" + untracked).strip()
    except Exception:
        return ""


def run_review(
    lens: str,
    runtime: str,
    mode: str,
    console: Console,
) -> None:
    """Run code review with the specified lens, runtime, and mode."""
    # 1. Fetch git diff
    diff = get_git_diff()
    if not diff:
        console.print("[yellow]No local changes detected to review. Try making some changes first.[/]")
        return

    # 2. Get template
    template_path = REVIEWS_DIR / f"{lens}.md"
    if not template_path.exists():
        console.print(f"[bold red]Error:[/] Review template for lens '{lens}' not found.")
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
            "Do not accept compromises. Critique every line of the changes below.\n\n"
        )
    
    compiled_prompt = prefix + template_content.replace("{{git_diff}}", diff)

    # 4. Show or run prompt
    console.print(Panel(
        f"Lens: [bold cyan]{lens.upper()}[/]\n"
        f"Runtime: [bold cyan]{runtime}[/]\n"
        f"Mode: [bold cyan]{mode.upper()}[/]",
        title="[bold]Code Review Plan[/]",
        border_style="cyan"
    ))

    # Save to a temporary prompt file for reference
    temp_dir = Path.cwd() / ".sutra" / "runs"
    temp_dir.mkdir(parents=True, exist_ok=True)
    prompt_file = temp_dir / f"review-{lens}-{mode}-prompt.md"
    prompt_file.write_text(compiled_prompt, encoding="utf-8")

    is_test = os.environ.get("SUTRA_TEST") == "1"

    if is_test:
        console.print("[dim]Mocking review execution...[/]")
        console.print(f"[green]✓[/] Code review successfully generated.")
    else:
        if shutil.which(runtime):
            console.print(f"[cyan]Invoking {runtime} CLI for review...[/]")
            try:
                subprocess.run([runtime, str(prompt_file)], check=True)
            except Exception:
                console.print(f"[yellow]Warning: {runtime} execution failed.[/]")
                console.print(f"Here is the review prompt. You can copy-paste it into your AI session:\n")
                console.print(compiled_prompt)
        else:
            console.print(f"[yellow]CLI '{runtime}' not found in PATH.[/]")
            console.print(f"Here is the generated review prompt. You can copy-paste it into your session:\n")
            console.print(compiled_prompt)
            console.print(f"\n[dim]Prompt also saved to: {prompt_file}[/]")
