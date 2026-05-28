"""Sutra doctor — validate workspace integrity."""

from __future__ import annotations

from pathlib import Path

import yaml
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from sutra.core.config import (
    AGENTS_DIR,
    COMMANDS_DIR,
    CONTEXT_DIR,
    EVIDENCE_DIR,
    POLICIES_DIR,
    SKILLS_DIR,
    SUTRA_DIR,
    SUTRA_YAML,
    PROJECT_YAML,
    RUNTIMES_YAML,
    find_sutra_root,
    load_sutra_config,
)


class DiagnosticResult:
    """A single diagnostic check result."""

    def __init__(self, name: str, passed: bool, message: str, severity: str = "error"):
        self.name = name
        self.passed = passed
        self.message = message
        self.severity = severity  # error, warning, info


def _check_sutra_structure(repo_root: Path) -> list[DiagnosticResult]:
    """Check that .sutra/ has the expected structure."""
    results: list[DiagnosticResult] = []
    sutra_dir = repo_root / SUTRA_DIR

    # Required files
    required_files = [SUTRA_YAML, PROJECT_YAML, RUNTIMES_YAML]
    for fname in required_files:
        fpath = sutra_dir / fname
        if fpath.exists():
            results.append(DiagnosticResult(
                f".sutra/{fname}",
                True,
                "Present",
            ))
        else:
            results.append(DiagnosticResult(
                f".sutra/{fname}",
                False,
                "Missing",
            ))

    # Required directories
    required_dirs = [CONTEXT_DIR, AGENTS_DIR, SKILLS_DIR, COMMANDS_DIR, POLICIES_DIR, EVIDENCE_DIR]
    for dname in required_dirs:
        dpath = sutra_dir / dname
        if dpath.is_dir():
            children = list(dpath.iterdir())
            results.append(DiagnosticResult(
                f".sutra/{dname}/",
                True,
                f"{len(children)} items",
            ))
        else:
            results.append(DiagnosticResult(
                f".sutra/{dname}/",
                False,
                "Missing directory",
            ))

    return results


def _check_yaml_validity(repo_root: Path) -> list[DiagnosticResult]:
    """Check that all YAML files parse correctly."""
    results: list[DiagnosticResult] = []
    sutra_dir = repo_root / SUTRA_DIR

    for yaml_file in sutra_dir.rglob("*.yaml"):
        rel = yaml_file.relative_to(sutra_dir)
        try:
            with open(yaml_file) as f:
                yaml.safe_load(f)
            results.append(DiagnosticResult(
                f".sutra/{rel}",
                True,
                "Valid YAML",
                severity="info",
            ))
        except yaml.YAMLError as e:
            results.append(DiagnosticResult(
                f".sutra/{rel}",
                False,
                f"Invalid YAML: {e}",
            ))

    return results


def _check_config_schema(repo_root: Path) -> list[DiagnosticResult]:
    """Check that config files conform to Pydantic schemas."""
    results: list[DiagnosticResult] = []

    try:
        config = load_sutra_config(repo_root)
        results.append(DiagnosticResult("sutra.yaml schema", True, "Valid"))

        # Check runtimes are known
        known_runtimes = {"claude", "codex", "gemini"}
        for rt in config.runtimes:
            if rt in known_runtimes:
                results.append(DiagnosticResult(
                    f"Runtime: {rt}",
                    True,
                    "Known runtime",
                    severity="info",
                ))
            else:
                results.append(DiagnosticResult(
                    f"Runtime: {rt}",
                    False,
                    f"Unknown runtime '{rt}'",
                    severity="warning",
                ))

    except FileNotFoundError:
        results.append(DiagnosticResult(
            "sutra.yaml schema",
            False,
            "File not found",
        ))
    except Exception as e:
        results.append(DiagnosticResult(
            "sutra.yaml schema",
            False,
            f"Validation error: {e}",
        ))

    return results


def _check_claude_runtime(repo_root: Path) -> list[DiagnosticResult]:
    """Check Claude Code projection is valid."""
    results: list[DiagnosticResult] = []

    claude_md = repo_root / "CLAUDE.md"
    claude_dir = repo_root / ".claude"

    if claude_md.exists():
        results.append(DiagnosticResult("CLAUDE.md", True, "Present"))
    else:
        results.append(DiagnosticResult("CLAUDE.md", False, "Missing — run sutra sync"))

    expected_dirs = ["agents", "commands", "skills", "hooks"]
    for dname in expected_dirs:
        dpath = claude_dir / dname
        if dpath.is_dir():
            results.append(DiagnosticResult(
                f".claude/{dname}/",
                True,
                f"{len(list(dpath.iterdir()))} items",
            ))
        else:
            results.append(DiagnosticResult(
                f".claude/{dname}/",
                False,
                "Missing — run sutra sync",
            ))

    settings = claude_dir / "settings.json"
    if settings.exists():
        results.append(DiagnosticResult(".claude/settings.json", True, "Present"))
    else:
        results.append(DiagnosticResult(
            ".claude/settings.json",
            False,
            "Missing — run sutra sync",
            severity="warning",
        ))

    return results


def _check_codex_runtime(repo_root: Path) -> list[DiagnosticResult]:
    """Check Codex CLI projection is valid."""
    results: list[DiagnosticResult] = []

    agents_md = repo_root / "AGENTS.md"
    if agents_md.exists():
        results.append(DiagnosticResult("AGENTS.md", True, "Present"))
    else:
        results.append(DiagnosticResult("AGENTS.md", False, "Missing — run sutra sync"))

    return results


def _check_gemini_runtime(repo_root: Path) -> list[DiagnosticResult]:
    """Check Gemini projection is valid."""
    results: list[DiagnosticResult] = []

    gemini_md = repo_root / "GEMINI.md"
    gemini_dir = repo_root / ".gemini"

    if gemini_md.exists():
        results.append(DiagnosticResult("GEMINI.md", True, "Present"))
    else:
        results.append(DiagnosticResult("GEMINI.md", False, "Missing — run sutra sync"))

    style_md = gemini_dir / "STYLE.md"
    if style_md.exists():
        results.append(DiagnosticResult(".gemini/STYLE.md", True, "Present"))
    else:
        results.append(DiagnosticResult(".gemini/STYLE.md", False, "Missing — run sutra sync"))

    settings = gemini_dir / "settings.json"
    if settings.exists():
        results.append(DiagnosticResult(".gemini/settings.json", True, "Present"))
    else:
        results.append(DiagnosticResult(
            ".gemini/settings.json",
            False,
            "Missing — run sutra sync",
            severity="warning",
        ))

    return results


def run_doctor(
    runtime: str | None,
    console: Console,
) -> None:
    """Run diagnostic checks on the Sutra workspace."""
    root = find_sutra_root()
    if root is None:
        console.print(
            "[bold red]Error:[/] Not a Sutra workspace. Run [bold]sutra init[/] first."
        )
        raise SystemExit(1)

    all_results: list[DiagnosticResult] = []

    # Core checks
    if runtime is None:
        all_results.extend(_check_sutra_structure(root))
        all_results.extend(_check_yaml_validity(root))
        all_results.extend(_check_config_schema(root))

    # Runtime-specific checks
    config = load_sutra_config(root)

    if runtime == "claude" or (runtime is None and "claude" in config.runtimes):
        all_results.extend(_check_claude_runtime(root))

    if runtime == "codex" or (runtime is None and "codex" in config.runtimes):
        all_results.extend(_check_codex_runtime(root))

    if runtime == "gemini" or (runtime is None and "gemini" in config.runtimes):
        all_results.extend(_check_gemini_runtime(root))

    # Display results
    table = Table(title="Sutra Doctor", show_lines=False)
    table.add_column("Check", style="bold")
    table.add_column("Status", justify="center")
    table.add_column("Details")

    errors = 0
    warnings = 0

    for r in all_results:
        if r.passed:
            status = "[bold green]✓[/]"
        elif r.severity == "warning":
            status = "[bold yellow]⚠[/]"
            warnings += 1
        else:
            status = "[bold red]✗[/]"
            errors += 1

        table.add_row(r.name, status, r.message)

    console.print(table)
    console.print()

    if errors == 0 and warnings == 0:
        console.print("[bold green]All checks passed.[/]")
    elif errors == 0:
        console.print(f"[bold yellow]{warnings} warning(s), 0 errors.[/]")
    else:
        console.print(f"[bold red]{errors} error(s), {warnings} warning(s).[/]")
        raise SystemExit(1)
