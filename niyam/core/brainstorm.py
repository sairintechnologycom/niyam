"""Niyam brainstorm — interactive product planning and workspace bootstrapping."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

from niyam.core.config import (
    get_niyam_dir,
    load_niyam_config,
    save_niyam_config,
)
from niyam.core.context import _scan_repo
from niyam.core.init import run_init
from niyam.mission.planner import run_mission_plan


def clean_markdown(text: str) -> str:
    """Clean markdown code block wrapping from response."""
    text = text.strip()
    # Remove leading ```markdown or ```
    text = re.sub(r"^```(?:markdown|md)?\s*", "", text, flags=re.IGNORECASE)
    # Remove trailing ```
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def get_multiline_input(console: Console, prompt_msg: str, default: str) -> str:
    """Collect multi-line input from the user.

    Lines are read one at a time. The user types 'done' on a new line
    or presses Ctrl+D to finish. Returns *default* when nothing is entered.
    """
    console.print(prompt_msg)
    lines = []
    try:
        while True:
            line = input("> ")
            if line.strip().lower() == "done":
                break
            lines.append(line)
    except EOFError:
        # User pressed Ctrl+D, finish input gracefully
        pass
    except KeyboardInterrupt:
        console.print("\n[red]Aborted.[/]")
        raise SystemExit(1)

    content = "\n".join(lines).strip()
    return content if content else default


def _generate_suggested_answers(
    runtime: str,
    questions: list[str],
    repo_context_str: str,
    niche_str: str,
    raw_notes: str,
    console: Console,
) -> list[str]:
    """Generate AI-suggested answers for clarifying questions.

    Returns a list of suggested answer strings, one per question.
    Falls back to empty strings if the runtime is unavailable or fails.
    """
    suggestions: list[str] = [""] * len(questions)

    if not shutil.which(runtime):
        return suggestions

    numbered_questions = "\n".join(f"{i}. {q}" for i, q in enumerate(questions, 1))
    prompt = f"""You are the Niyam product architect. Based on the context below, generate a concise suggested answer for each clarifying question. Use the existing repository stack and developer notes to inform your suggestions.

{repo_context_str}

Product Idea/Niche: {niche_str}
Developer Notes: {raw_notes}

Questions:
{numbered_questions}

For each question, output ONLY a numbered answer (matching the question number). Keep answers concise (1-2 sentences). Do not output any other text, greetings, code blocks, or explanations."""

    cmd = [runtime, "-p", prompt]
    if runtime == "gemini":
        cmd.append("--skip-trust")

    try:
        with console.status("[cyan]Generating suggested answers...[/]"):
            res = subprocess.run(
                cmd,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                timeout=120,
            )
        if res.returncode == 0:
            raw_out = (res.stdout or "").strip()
            for line in raw_out.split("\n"):
                line = line.strip()
                if not line:
                    continue
                match = re.match(r"^(\d+)[\.\)\-:\s]\s*(.*)$", line)
                if match:
                    idx = int(match.group(1)) - 1
                    if 0 <= idx < len(suggestions):
                        suggestions[idx] = match.group(2).strip()
    except Exception:
        pass  # Fall back to empty suggestions silently

    return suggestions


def _extract_section(content: str, keywords: list[str]) -> str:
    """Extract a section from a markdown document based on heading keywords."""
    lines = content.splitlines()
    target_lines = []
    in_section = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#"):
            # Check if this header matches keywords
            header_text = stripped.lstrip("#").strip().lower()
            if any(kw in header_text for kw in keywords):
                in_section = True
                # Include the header in bold formatting
                target_lines.append(f"[bold]{stripped}[/]")
            else:
                in_section = False
        elif in_section:
            # Format bullets nicely
            if (
                stripped.startswith("-")
                or stripped.startswith("*")
                or stripped.startswith("•")
            ):
                target_lines.append(f"  [green]•[/] {stripped.lstrip('-*•').strip()}")
            elif stripped:
                target_lines.append(f"    {stripped}")
    return "\n".join(target_lines).strip()


def _build_preview(prd_content: str, roadmap_content: str) -> Panel:
    """Build a beautiful console preview panel of the generated PRD and Roadmap."""
    features = _extract_section(prd_content, ["feature", "scope", "mvp"])
    tech_stack = _extract_section(
        prd_content, ["tech stack", "technology", "recommendation"]
    )
    phases = _extract_section(
        roadmap_content, ["phase 1", "phase 2", "phase 3", "milestone"]
    )

    preview_parts = []
    if features:
        preview_parts.append("[bold magenta]🔑 MVP Key Features[/]")
        preview_parts.append(features)
        preview_parts.append("")
    if tech_stack:
        preview_parts.append("[bold cyan]🛠️ Architecture & Tech Stack[/]")
        preview_parts.append(tech_stack)
        preview_parts.append("")
    if phases:
        preview_parts.append("[bold yellow]📅 Product Roadmap Phases[/]")
        preview_parts.append(phases)

    content = "\n".join(preview_parts).strip()
    if not content:
        content = "[dim]No key sections could be parsed for preview. You can review the files directly.[/]"

    return Panel(
        content,
        title="[bold green]Preview: PRD & Product Roadmap[/]",
        border_style="green",
        padding=(1, 2),
    )


def _generate_prd_and_roadmap(
    runtime: str,
    repo_context_str: str,
    niche_str: str,
    raw_notes: str,
    q_and_a_str: str,
    refinement_notes: str,
    console: Console,
) -> tuple[str, str, bool]:
    """Call runtime to generate PRD and Roadmap content, optionally applying refinements."""
    refinement_section = ""
    if refinement_notes:
        refinement_section = (
            f"\nUser Refinement Feedback/Adjustments:\n{refinement_notes}\n"
        )

    prompt_generation = f"""You are the Niyam product architect. Based on the product concept, existing repository context, developer notes, clarifying Q&A, and any user feedback below, generate a Product Requirements Document (PRD) and a Product Roadmap.

{repo_context_str}

Product Niche/Idea: {niche_str}
Developer Notes: {raw_notes}

Clarifying Q&A:
{q_and_a_str}
{refinement_section}
Please generate:
1. A Product Requirements Document (PRD) containing:
   - Product Overview & Goals
   - Target Audience & User Personas
   - Key Features (MVP Scope)
   - Tech Stack Recommendations
   - Out of Scope

2. A Product Roadmap containing:
   - Phase 1: MVP Core Features
   - Phase 2: Next Iterations & Advanced Features
   - Phase 3: Scaling & Integration

Please output the PRD contents first, then the divider "=== ROADMAP.md ===", and then the ROADMAP contents. Output ONLY the markdown files and the divider. Do not include markdown code blocks around the files or any introduction/conclusion.
"""

    prd_content = ""
    roadmap_content = ""
    success = False

    if shutil.which(runtime):
        cmd = [runtime, "-p", prompt_generation]
        if runtime == "gemini":
            cmd.append("--skip-trust")

        try:
            with console.status(
                f"[cyan]Generating PRD and Roadmap with {runtime}...[/]"
            ):
                res = subprocess.run(
                    cmd,
                    stdin=subprocess.DEVNULL,
                    capture_output=True,
                    text=True,
                    timeout=180,
                )
            if res.returncode == 0:
                raw_gen = (res.stdout or "").strip()
                parts = re.split(
                    r"===\s*ROADMAP\.md\s*===", raw_gen, flags=re.IGNORECASE
                )
                if len(parts) >= 2:
                    prd_content = clean_markdown(parts[0])
                    roadmap_content = clean_markdown(parts[1])
                    success = True
                else:
                    parts_roadmap = re.split(
                        r"(#+\s*Roadmap|#+\s*Product\s*Roadmap)",
                        raw_gen,
                        flags=re.IGNORECASE,
                    )
                    if len(parts_roadmap) >= 3:
                        prd_content = clean_markdown(parts_roadmap[0])
                        roadmap_content = clean_markdown(
                            parts_roadmap[1] + "\n" + parts_roadmap[2]
                        )
                        success = True
        except Exception as e:
            console.print(f"[yellow]Failed to call runtime CLI for generation: {e}[/]")

    return prd_content, roadmap_content, success


def run_brainstorm(runtime: str | None, console: Console) -> None:
    """Execute the interactive product brainstorming wizard."""
    console.print(
        Panel(
            "[bold magenta]Welcome to the Niyam Product Brainstorming Wizard![/]\n"
            "This wizard will help you design your product, generate a PRD and Roadmap,\n"
            "and bootstrap a planned Niyam workspace, especially for new niches.",
            title="[bold magenta]Niyam Brainstorm[/]",
            border_style="magenta",
        )
    )

    repo_root = Path.cwd()
    niyam_dir = get_niyam_dir(repo_root)

    # Overwrite check
    prd_path = repo_root / "PRD.md"
    roadmap_path = repo_root / "ROADMAP.md"
    if prd_path.exists() or roadmap_path.exists():
        existing_files = []
        if prd_path.exists():
            existing_files.append("PRD.md")
        if roadmap_path.exists():
            existing_files.append("ROADMAP.md")
        files_str = " and ".join(existing_files)
        console.print(
            f"\n[yellow]⚠️ Warning: {files_str} already exist(s) in this directory.[/]"
        )
        if not Confirm.ask("Do you want to overwrite them?", default=False):
            console.print(
                "[red]Aborted brainstorm to prevent overwriting existing files.[/]"
            )
            raise SystemExit(0)

    # 1. Confirm/Choose Runtime
    if not runtime:
        # Detect available runtimes in PATH
        detected_runtimes = [
            rt for rt in ["claude", "gemini", "codex"] if shutil.which(rt)
        ]
        default_rt = detected_runtimes[0] if detected_runtimes else "claude"

        console.print("\n[cyan]1. Configure Brainstorming Runtime Engine[/]")
        if detected_runtimes:
            console.print(f"Detected runtimes in PATH: {', '.join(detected_runtimes)}")
        else:
            console.print(
                "[yellow]⚠️ No runtimes detected in PATH. Defaulting to 'claude'.[/]"
            )

        runtime = Prompt.ask(
            "Which runtime should we use for brainstorming?",
            choices=["claude", "gemini", "codex"],
            default=default_rt,
        )

    if not shutil.which(runtime):
        console.print(
            f"[yellow]⚠️ Warning: Runtime '{runtime}' was not found in your PATH.[/]\n"
            "We will proceed, but querying the AI might fail if the CLI is missing."
        )

    # Scan existing repo context
    console.print("\n[cyan]Scanning existing repository context...[/]")
    scan_result = _scan_repo(repo_root)
    detected_items = []
    if scan_result["languages"]:
        detected_items.append(
            f"Languages: [bold]{', '.join(scan_result['languages'])}[/]"
        )
    if scan_result["frameworks"]:
        detected_items.append(
            f"Frameworks: [bold]{', '.join(scan_result['frameworks'])}[/]"
        )
    if detected_items:
        console.print(f"[green]✓ Detected stack:[/] {', '.join(detected_items)}")
    else:
        console.print("[dim]No existing stack detected (starting fresh).[/]")

    repo_context_lines = []
    if scan_result.get("languages"):
        repo_context_lines.append(f"- Languages: {', '.join(scan_result['languages'])}")
    if scan_result.get("frameworks"):
        repo_context_lines.append(
            f"- Frameworks: {', '.join(scan_result['frameworks'])}"
        )
    if scan_result.get("package_managers"):
        repo_context_lines.append(
            f"- Package Managers: {', '.join(scan_result['package_managers'])}"
        )
    if scan_result.get("source_dirs"):
        repo_context_lines.append(
            f"- Source Directories: {', '.join(scan_result['source_dirs'])}"
        )
    if scan_result.get("db_schema"):
        repo_context_lines.append("- Database Schema Info:")
        for db in scan_result["db_schema"]:
            repo_context_lines.append(f"  * {db}")
    if scan_result.get("api_routes"):
        repo_context_lines.append("- API Routes / Controllers:")
        for route in scan_result["api_routes"]:
            repo_context_lines.append(f"  * {route}")
    if scan_result.get("env_vars"):
        repo_context_lines.append(
            f"- Environment Variables: {', '.join(scan_result['env_vars'])}"
        )

    if repo_context_lines:
        repo_context_str = "Existing Repository Context:\n" + "\n".join(
            repo_context_lines
        )
    else:
        repo_context_str = (
            "Existing Repository Context: Empty directory or no stack detected."
        )

    # 2. Select Niche / Product Idea
    console.print("\n[cyan]2. Select Niche or Product Idea[/]")
    niche_choice = Prompt.ask(
        "Choose a niche or type your own product idea:\n"
        "  [1] Photographers SaaS\n"
        "  [2] Tutors/Learning Platform\n"
        "  [3] Salons & Booking App\n"
        "  [4] Small Agencies Portal\n"
        "  [5] Custom product idea\n"
        "Select [1-5 or custom text]",
        default="5",
    )

    if niche_choice == "1":
        niche_str = "Photographers SaaS"
    elif niche_choice == "2":
        niche_str = "Tutors/Learning Platform"
    elif niche_choice == "3":
        niche_str = "Salons & Booking App"
    elif niche_choice == "4":
        niche_str = "Small Agencies Portal"
    elif niche_choice == "5":
        niche_str = Prompt.ask("Enter your custom product idea")
    else:
        niche_str = niche_choice

    # 3. Collect Raw Notes
    is_non_interactive = os.environ.get("NIYAM_TEST") == "1" or "pytest" in sys.modules
    if is_non_interactive:
        console.print(
            f"\n[cyan]3. Describe your vision for [bold]{niche_str}[/][/]\n"
            "Provide any raw notes, desired features, or PRD ideas below.\n"
            "(Press Ctrl+D when finished, or Enter to use default)"
        )
        raw_notes = "A basic web application with scheduling and payment integrations."
    else:
        raw_notes = get_multiline_input(
            console,
            f"\n[cyan]3. Describe your vision for [bold]{niche_str}[/][/]\n"
            "Provide any raw notes, desired features, or PRD ideas below.\n"
            "Type 'done' on a new line when finished, or press Enter immediately to use default.",
            "A basic web application with scheduling and payment integrations.",
        )

    # 4. Generate Brainstorming Questions via AI
    console.print(
        f"\n[cyan]4. Deep analyzing product concept with {runtime} to generate clarifying questions...[/]"
    )
    prompt_questions = f"""You are the Niyam product architect. The developer wants to start a new project or build on top of an existing one.

{repo_context_str}

Product Idea/Niche: {niche_str}
Raw Developer Notes/Inputs: {raw_notes}

Please generate 3 to 5 critical clarifying questions to refine the requirements, target audience, MVP features, and roadmap. If there is an existing stack/context detected, make sure to tailor the questions to build on top of it or integrate with it.
Format your output as a numbered list of questions. Do not output any other text, greetings, code blocks, or explanations. Only return the questions themselves.
"""

    questions = []
    if shutil.which(runtime):
        cmd = [runtime, "-p", prompt_questions]
        if runtime == "gemini":
            cmd.append("--skip-trust")

        try:
            with console.status(f"[cyan]Analyzing concept with {runtime}...[/]"):
                res = subprocess.run(
                    cmd,
                    stdin=subprocess.DEVNULL,
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
            if res.returncode == 0:
                raw_out = (res.stdout or "").strip()
                lines = [line.strip() for line in raw_out.split("\n") if line.strip()]
                for line in lines:
                    match = re.match(r"^\d+[\.\)\-:\s]\s*(.*)$", line)
                    if match:
                        questions.append(match.group(1).strip())
                    elif line.endswith("?"):
                        questions.append(line)
        except Exception as e:
            console.print(f"[yellow]Failed to call runtime CLI: {e}[/]")

    if not questions:
        console.print("[dim]Using default clarifying questions...[/]")
        questions = [
            "What is the single most important feature or flow of the MVP?",
            "Who is the primary end user (e.g. business owner or client)?",
            "What tech stack do you prefer (e.g. HTML/JS, React, Python FastAPI)?",
        ]

    # 5. Generate suggested answers and gather user input
    console.print("\n[cyan]5. Please answer these questions to refine your plan:[/]")
    suggestions = _generate_suggested_answers(
        runtime, questions, repo_context_str, niche_str, raw_notes, console
    )
    answers = []
    for i, q in enumerate(questions, 1):
        suggestion = suggestions[i - 1] if i - 1 < len(suggestions) else ""
        console.print(f"\n[bold]Q{i}: {q}[/]")
        if suggestion:
            console.print(f"   [dim]💡 Suggested:[/] [italic]{suggestion}[/]")
        if is_non_interactive:
            ans = suggestion if suggestion else f"Sample answer {i}"
            console.print(f"Answer: {ans}")
        else:
            try:
                hint = " [Enter to accept]" if suggestion else ""
                ans = input(f"Answer{hint}: ").strip()
            except (KeyboardInterrupt, EOFError):
                console.print("\n[red]Aborted.[/]")
                raise SystemExit(1)
            if not ans:
                ans = suggestion if suggestion else "Not specified"
        answers.append(ans)

    # 6. Generate PRD and Roadmap
    q_and_a_str = ""
    for i, (q, a) in enumerate(zip(questions, answers), 1):
        q_and_a_str += f"Q{i}: {q}\nA{i}: {a}\n\n"

    prd_content = ""
    roadmap_content = ""
    success = False
    refinement_notes = ""
    iteration = 0
    max_iterations = 3

    while iteration < max_iterations:
        if iteration > 0:
            console.print(
                f"\n[cyan]Regenerating PRD and Roadmap (Attempt {iteration + 1}/{max_iterations})...[/]"
            )
        else:
            console.print(
                f"\n[cyan]6. Generating PRD.md and ROADMAP.md using {runtime}...[/]"
            )

        prd_content, roadmap_content, success = _generate_prd_and_roadmap(
            runtime,
            repo_context_str,
            niche_str,
            raw_notes,
            q_and_a_str,
            refinement_notes,
            console,
        )

        if not success:
            break

        if is_non_interactive:
            break

        # Display preview to user
        console.print(_build_preview(prd_content, roadmap_content))

        choice = (
            Prompt.ask(
                "\nWould you like to accept, refine, or skip?",
                choices=["accept", "refine", "skip"],
                default="accept",
            )
            .strip()
            .lower()
        )

        if choice == "accept":
            break
        elif choice == "skip":
            console.print(
                "[yellow]Skipping further edits. Writing current content to disk...[/]"
            )
            break
        elif choice == "refine":
            iteration += 1
            if iteration >= max_iterations:
                console.print(
                    "[yellow]Maximum refinement attempts reached. Proceeding with current version.[/]"
                )
                break

            refinement_notes = Prompt.ask(
                "Enter refinement feedback / changes to apply"
            ).strip()
            if not refinement_notes:
                refinement_notes = (
                    "Please refine and detailed the requirements based on feedback."
                )

    if not success:
        console.print("[dim]Falling back to template PRD and Roadmap...[/]")
        prd_content = f"""# Product Requirements Document (PRD): {niche_str}

## Product Overview & Goals
A starter template for {niche_str} to organize booking, payments, and client management.

## Target Audience & User Personas
- Service providers (e.g., photographers, tutors, salon owners)
- End-user clients looking to book services

## Key Features (MVP Scope)
- Appointment Scheduling / Calendar
- Basic Profile / Service Listing
- Client Contact Form

## Tech Stack Recommendations
- Frontend: HTML/CSS/Vanilla Javascript or Next.js
- Styling: Vanilla CSS

## Out of Scope
- Multi-tenant marketplace onboarding
"""
        roadmap_content = f"""# Product Roadmap: {niche_str}

## Phase 1: MVP Core Features
- Project structure setup
- Core landing page and booking form
- Mock local storage integration

## Phase 2: Next Iterations & Advanced Features
- Authentication gate
- Database integration (PostgreSQL)

## Phase 3: Scaling & Integration
- Third-party calendar sync (Google Calendar)
"""

    # Write files
    prd_path.write_text(prd_content, encoding="utf-8")
    roadmap_path.write_text(roadmap_content, encoding="utf-8")

    console.print(f"[green]✓ Created [bold]PRD.md[/] at {prd_path}[/]")
    console.print(f"[green]✓ Created [bold]ROADMAP.md[/] at {roadmap_path}[/]")

    # 7. Initialize Niyam if not initialized
    if not niyam_dir.exists():
        console.print("\n[cyan]7. Initializing Niyam workspace configuration...[/]")
        run_init(
            profile="fullstack",
            runtime=runtime,
            dry_run=False,
            force=False,
            console=console,
        )
    else:
        # Enable runtime in existing config if not already enabled
        config = load_niyam_config(repo_root)
        if runtime not in config.runtimes:
            config.runtimes.append(runtime)
            save_niyam_config(config, repo_root)
            console.print(f"[green]✓ Enabled runtime '{runtime}' in niyam.yaml[/]")

    # 8. Run niyam plan on PRD
    plan_success = True
    console.print("\n[cyan]8. Automatically planning Niyam tasks based on PRD.md...[/]")
    try:
        run_mission_plan(
            requirements_path=str(prd_path),
            strict=False,
            console=console,
            template=None,
            runtime_override=runtime,
        )
    except Exception as e:
        console.print(f"[yellow]Warning: Planning tasks from PRD.md failed: {e}[/]")
        plan_success = False

    if plan_success:
        panel_title = "[bold green]Success[/]"
        panel_border = "green"
        panel_text = (
            "[bold green]✓ Brainstorming & Bootstrap Completed Successfully![/]\n\n"
            "  [dim]•[/] Generated [bold]PRD.md[/] & [bold]ROADMAP.md[/]\n"
            "  [dim]•[/] Initialized Niyam workspace and planned task contracts.\n\n"
            "You can now run [bold cyan]niyam next[/] or [bold cyan]niyam status[/] to start building!"
        )
    else:
        panel_title = "[bold yellow]Completed with Warnings[/]"
        panel_border = "yellow"
        panel_text = (
            "[bold yellow]⚠️ Brainstorming Completed with Warnings[/]\n\n"
            "  [dim]•[/] Generated [bold]PRD.md[/] & [bold]ROADMAP.md[/]\n"
            "  [dim]•[/] Initialized Niyam workspace.\n"
            "  [red]• Failed to automatically generate implementation plans.[/]\n\n"
            "You can try generating plans manually using [bold cyan]niyam plan PRD.md[/]."
        )

    console.print(
        Panel(
            panel_text,
            title=panel_title,
            border_style=panel_border,
        )
    )
