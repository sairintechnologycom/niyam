"""Niyam setup — interactive onboarding wizard."""

from __future__ import annotations

import shutil
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

from niyam.core.config import (
    find_niyam_root,
    load_niyam_config,
    save_niyam_config,
    get_niyam_dir,
)
from niyam.core.init import run_init
from niyam.core.context import run_context_refresh
from niyam.core.sync import run_runtime_add


def run_setup(console: Console) -> None:
    """Execute the interactive setup wizard."""
    console.print(
        Panel(
            "[bold magenta]Welcome to the Niyam Onboarding Wizard![/]\n"
            "This wizard will guide you through setting up your workspace config.",
            title="[bold magenta]Niyam Setup[/]",
            border_style="magenta",
        )
    )

    repo_root = Path.cwd()
    niyam_dir = get_niyam_dir(repo_root)

    # 1. Initialize if not exists
    if not niyam_dir.exists():
        console.print(
            "[yellow]No .niyam/ directory detected. Let's initialize your workspace![/]"
        )
        profile = Prompt.ask(
            "Which project profile fits your stack?",
            choices=[
                "fullstack",
                "backend",
                "frontend",
                "startup-saas",
                "platform-engineering",
                "governed-enterprise",
            ],
            default="fullstack",
        )
        console.print(f"[cyan]Initializing Niyam with profile: {profile}...[/]")
        run_init(
            profile=profile, runtime=None, dry_run=False, force=False, console=console
        )
        # Refresh root
        repo_root = find_niyam_root() or repo_root
        niyam_dir = get_niyam_dir(repo_root)
    else:
        console.print("[green]✓ .niyam/ directory is already initialized.[/]")

    # 2. Refresh Context
    console.print("\n[cyan]Scanning project structure and stack...[/]")
    run_context_refresh(console=console)

    # 3. Detect Runtimes in PATH
    console.print("\n[cyan]Detecting available runtimes in PATH...[/]")
    detected_runtimes = []
    for rt in ["claude", "agy", "gemini", "codex"]:
        if shutil.which(rt):
            detected_runtimes.append(rt)
            console.print(f"  [green]✓[/] Detected runtime: [bold cyan]{rt}[/]")
        else:
            console.print(f"  [dim]•[/] Runtime [dim]{rt}[/] not found in PATH")

    runtimes_to_enable = []
    if not detected_runtimes:
        console.print(
            "\n[yellow]⚠️ No AI runtimes (claude, agy, gemini, codex) were detected in your PATH.[/]"
        )
        console.print("Please install them or specify the one you plan to use.")
        chosen_rt = Prompt.ask(
            "Which runtime would you like to configure anyway?",
            choices=["claude", "agy", "gemini", "codex", "none"],
            default="none",
        )
        if chosen_rt != "none":
            runtimes_to_enable.append(chosen_rt)
    else:
        for rt in detected_runtimes:
            enable = Confirm.ask(
                f"Would you like to enable the [bold cyan]{rt}[/] runtime?",
                default=True,
            )
            if enable:
                runtimes_to_enable.append(rt)

    # Enable and configure selected runtimes
    for rt in runtimes_to_enable:
        run_runtime_add(runtime=rt, console=console)

    # 4. Agent Customization Info
    console.print("\n[cyan]Customizing Agent Personas[/]")
    agents_dir = niyam_dir / "agents"
    if agents_dir.is_dir():
        agents = [f.stem for f in agents_dir.glob("*.md")]
        console.print(f"Detected agents in .niyam/agents/: {', '.join(agents)}")
        console.print(
            "You can customize these markdown files to adjust agent personas and expertise."
        )

    # 5. Policies & Guardrails
    console.print("\n[cyan]Configuring Guardrails & Security Policies[/]")
    guard_enabled = Confirm.ask(
        "Would you like to enable safety guardrails?", default=True
    )
    careful_mode = Confirm.ask(
        "Would you like careful mode enabled (warnings before executing risky commands)?",
        default=True,
    )

    config = load_niyam_config(repo_root)
    config.guard.enabled = guard_enabled
    config.guard.careful = careful_mode
    save_niyam_config(config, repo_root)
    console.print("[green]✓ Guardrail settings updated in niyam.yaml[/]")

    console.print(
        Panel(
            "[bold green]✓ Niyam Setup Completed Successfully![/]\n\n"
            "Try planning and executing your first mission:\n"
            '  [bold cyan]niyam run "implement a simple hello world test case"[/]',
            title="[bold green]Success[/]",
            border_style="green",
        )
    )
