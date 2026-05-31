"""Sutra doctor — validate workspace integrity."""

from __future__ import annotations

from pathlib import Path

import yaml
from rich.console import Console
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
    SutraConfig,
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
            results.append(
                DiagnosticResult(
                    f".sutra/{fname}",
                    True,
                    "Present",
                )
            )
        else:
            results.append(
                DiagnosticResult(
                    f".sutra/{fname}",
                    False,
                    "Missing",
                )
            )

    # Required directories
    required_dirs = [
        CONTEXT_DIR,
        AGENTS_DIR,
        SKILLS_DIR,
        COMMANDS_DIR,
        POLICIES_DIR,
        EVIDENCE_DIR,
    ]
    for dname in required_dirs:
        dpath = sutra_dir / dname
        if dpath.is_dir():
            children = list(dpath.iterdir())
            results.append(
                DiagnosticResult(
                    f".sutra/{dname}/",
                    True,
                    f"{len(children)} items",
                )
            )
        else:
            results.append(
                DiagnosticResult(
                    f".sutra/{dname}/",
                    False,
                    "Missing directory",
                )
            )

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
            results.append(
                DiagnosticResult(
                    f".sutra/{rel}",
                    True,
                    "Valid YAML",
                    severity="info",
                )
            )
        except yaml.YAMLError as e:
            results.append(
                DiagnosticResult(
                    f".sutra/{rel}",
                    False,
                    f"Invalid YAML: {e}",
                )
            )

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
                results.append(
                    DiagnosticResult(
                        f"Runtime: {rt}",
                        True,
                        "Known runtime",
                        severity="info",
                    )
                )
            else:
                results.append(
                    DiagnosticResult(
                        f"Runtime: {rt}",
                        False,
                        f"Unknown runtime '{rt}'",
                        severity="warning",
                    )
                )

    except FileNotFoundError:
        results.append(
            DiagnosticResult(
                "sutra.yaml schema",
                False,
                "File not found",
            )
        )
    except Exception as e:
        results.append(
            DiagnosticResult(
                "sutra.yaml schema",
                False,
                f"Validation error: {e}",
            )
        )

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
            results.append(
                DiagnosticResult(
                    f".claude/{dname}/",
                    True,
                    f"{len(list(dpath.iterdir()))} items",
                )
            )
        else:
            results.append(
                DiagnosticResult(
                    f".claude/{dname}/",
                    False,
                    "Missing — run sutra sync",
                )
            )

    settings = claude_dir / "settings.json"
    if settings.exists():
        results.append(DiagnosticResult(".claude/settings.json", True, "Present"))
    else:
        results.append(
            DiagnosticResult(
                ".claude/settings.json",
                False,
                "Missing — run sutra sync",
                severity="warning",
            )
        )

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
        results.append(
            DiagnosticResult(".gemini/STYLE.md", False, "Missing — run sutra sync")
        )

    settings = gemini_dir / "settings.json"
    if settings.exists():
        results.append(DiagnosticResult(".gemini/settings.json", True, "Present"))
    else:
        results.append(
            DiagnosticResult(
                ".gemini/settings.json",
                False,
                "Missing — run sutra sync",
                severity="warning",
            )
        )

    return results


def _check_runtimes_in_path(
    repo_root: Path, config: SutraConfig
) -> list[DiagnosticResult]:
    import shutil

    results = []
    for rt in config.runtimes:
        if shutil.which(rt):
            results.append(
                DiagnosticResult(f"Runtime in PATH: {rt}", True, "Found in PATH")
            )
        else:
            results.append(
                DiagnosticResult(
                    f"Runtime in PATH: {rt}",
                    False,
                    f"Binary '{rt}' not found in PATH",
                    severity="warning",
                )
            )
    return results


def _check_agents_validity(repo_root: Path) -> list[DiagnosticResult]:
    results = []
    agents_dir = repo_root / ".sutra" / "agents"
    if agents_dir.is_dir():
        for agent_file in agents_dir.glob("*.md"):
            try:
                content = agent_file.read_text(encoding="utf-8").strip()
                if not content:
                    results.append(
                        DiagnosticResult(
                            f"Agent persona: {agent_file.name}",
                            False,
                            "File is empty",
                            severity="warning",
                        )
                    )
                else:
                    results.append(
                        DiagnosticResult(
                            f"Agent persona: {agent_file.name}",
                            True,
                            "Valid and non-empty",
                            severity="info",
                        )
                    )
            except Exception as e:
                results.append(
                    DiagnosticResult(
                        f"Agent persona: {agent_file.name}",
                        False,
                        f"Failed to read: {e}",
                        severity="warning",
                    )
                )
    return results


def _check_validation_commands_in_path(repo_root: Path) -> list[DiagnosticResult]:
    import shutil
    from sutra.core.config import load_project_config

    results = []
    try:
        project_config = load_project_config(repo_root)
        if project_config.validation:
            v_cmds = project_config.validation
            checks = {
                "build": v_cmds.build,
                "test": v_cmds.test,
                "lint": v_cmds.lint,
                "format": v_cmds.format,
                "typecheck": v_cmds.typecheck,
            }
            for name, cmd in checks.items():
                if cmd:
                    binary = cmd.split()[0]
                    if shutil.which(binary):
                        results.append(
                            DiagnosticResult(
                                f"Validation: {name} command",
                                True,
                                f"Binary '{binary}' found",
                            )
                        )
                    else:
                        results.append(
                            DiagnosticResult(
                                f"Validation: {name} command",
                                False,
                                f"Binary '{binary}' (from '{cmd}') not found in PATH",
                                severity="warning",
                            )
                        )
    except Exception:
        pass
    return results


def _check_git_status(repo_root: Path) -> list[DiagnosticResult]:
    import subprocess

    results = []
    git_dir = repo_root / ".git"
    if not git_dir.exists():
        results.append(
            DiagnosticResult(
                "Git Repository", False, "Not a Git repository", severity="warning"
            )
        )
        return results

    results.append(DiagnosticResult("Git Repository", True, "Detected"))

    # Check commits
    res = subprocess.run(
        ["git", "rev-parse", "--verify", "HEAD"], cwd=repo_root, capture_output=True
    )
    if res.returncode != 0:
        results.append(
            DiagnosticResult(
                "Git Commits",
                False,
                "No commits found in repository",
                severity="warning",
            )
        )
        return results
    else:
        results.append(DiagnosticResult("Git Commits", True, "Commits found"))

    # Check clean
    res = subprocess.run(
        ["git", "status", "--porcelain"], cwd=repo_root, capture_output=True, text=True
    )
    if res.returncode == 0:
        clean = not res.stdout.strip()
        if clean:
            results.append(
                DiagnosticResult(
                    "Git Status", True, "Working directory clean", severity="info"
                )
            )
        else:
            results.append(
                DiagnosticResult(
                    "Git Status",
                    False,
                    "Uncommitted changes present (may conflict with worktree isolation)",
                    severity="warning",
                )
            )

    return results


def _check_lint_format(repo_root: Path) -> list[DiagnosticResult]:
    """Run lint/format validation commands if configured."""
    from sutra.core.config import load_project_config
    from sutra.core.security import safe_run_command, CommandSecurityError
    import subprocess

    results = []
    try:
        project_config = load_project_config(repo_root)
        validation = project_config.validation
        if not validation:
            results.append(
                DiagnosticResult(
                    "Validation Check",
                    True,
                    "No validation commands configured",
                    severity="info",
                )
            )
            return results

        checks = {
            "lint": validation.lint,
            "format": validation.format,
        }

        for name, cmd in checks.items():
            if not cmd:
                continue
            try:
                res = safe_run_command(cmd, cwd=repo_root, timeout=60)
                if res.returncode == 0:
                    results.append(
                        DiagnosticResult(
                            f"Validation: {name}",
                            True,
                            f"Passed ({cmd})",
                            severity="info",
                        )
                    )
                else:
                    details = (res.stdout or "") + (res.stderr or "")
                    if len(details) > 200:
                        details = details[:200] + "..."
                    results.append(
                        DiagnosticResult(
                            f"Validation: {name}",
                            False,
                            f"Failed: {details.strip()}",
                        )
                    )
            except CommandSecurityError as e:
                results.append(
                    DiagnosticResult(
                        f"Validation: {name}",
                        False,
                        f"Blocked by security: {e}",
                    )
                )
            except subprocess.TimeoutExpired:
                results.append(
                    DiagnosticResult(
                        f"Validation: {name}",
                        False,
                        "Timed out (60s)",
                    )
                )
            except Exception as e:
                results.append(
                    DiagnosticResult(
                        f"Validation: {name}",
                        False,
                        f"Error: {e}",
                    )
                )

    except Exception as e:
        results.append(
            DiagnosticResult(
                "Validation Check",
                False,
                f"Failed to load project config: {e}",
            )
        )

    return results


def _run_planner_smoke(engine: str) -> tuple[bool, str]:
    import subprocess

    prompt = "Return exactly this text and nothing else: SUTRA_PLANNER_OK"
    cmd = [engine, "-p", prompt]
    if engine == "gemini":
        cmd.append("--skip-trust")
    elif engine == "codex":
        cmd = ["codex", "exec", prompt]
    try:
        res = subprocess.run(
            cmd,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=60,
        )
        output = (res.stdout or "") + (res.stderr or "")
        return ("SUTRA_PLANNER_OK" in output and res.returncode == 0), output.strip()[
            :100
        ]
    except Exception as e:
        return False, str(e)


def _run_claude_smoke() -> tuple[bool, str]:
    import subprocess

    prompt = "Return exactly this text and nothing else: SUTRA_CLAUDE_OK"
    try:
        res = subprocess.run(
            ["claude", "-p", prompt],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=60,
        )
        output = (res.stdout or "") + (res.stderr or "")
        return ("SUTRA_CLAUDE_OK" in output and res.returncode == 0), output.strip()[
            :100
        ]
    except Exception as e:
        return False, str(e)


def run_doctor(
    runtime: str | None,
    console: Console,
    check: bool = False,
    smoke_test: bool = False,
) -> None:
    """Run diagnostic checks on the Sutra workspace."""
    import os

    root = find_sutra_root()
    if root is None:
        console.print(
            "[bold red]Error:[/] Not a Sutra workspace. Run [bold]sutra init[/] first."
        )
        raise SystemExit(1)

    all_results: list[DiagnosticResult] = []

    # core load config
    config = load_sutra_config(root)

    # Core checks
    if runtime is None:
        all_results.extend(_check_sutra_structure(root))
        all_results.extend(_check_yaml_validity(root))
        all_results.extend(_check_config_schema(root))
        all_results.extend(_check_runtimes_in_path(root, config))
        all_results.extend(_check_agents_validity(root))
        all_results.extend(_check_validation_commands_in_path(root))
        all_results.extend(_check_git_status(root))
        if check:
            all_results.extend(_check_lint_format(root))

    if runtime == "claude" or (runtime is None and "claude" in config.runtimes):
        all_results.extend(_check_claude_runtime(root))

    if runtime == "codex" or (runtime is None and "codex" in config.runtimes):
        all_results.extend(_check_codex_runtime(root))

    if runtime == "gemini" or (runtime is None and "gemini" in config.runtimes):
        all_results.extend(_check_gemini_runtime(root))

    if smoke_test:
        engine = runtime or (config.runtimes[0] if config.runtimes else "claude")
        if engine in ("gemini", "codex"):
            p_ok, p_msg = _run_planner_smoke(engine)
            all_results.append(
                DiagnosticResult(
                    f"{engine} headless smoke test",
                    p_ok,
                    p_msg or "Passed",
                )
            )
            if not p_ok and engine == "gemini":
                gemini_key = os.environ.get("GOOGLE_API_KEY")
                if not gemini_key:
                    all_results.append(
                        DiagnosticResult(
                            "GOOGLE_API_KEY",
                            False,
                            "MISSING (required for Gemini API/headless mode)",
                        )
                    )

        c_ok, c_msg = _run_claude_smoke()
        all_results.append(
            DiagnosticResult(
                "Claude headless smoke test",
                c_ok,
                c_msg or "Passed",
            )
        )
        if not c_ok:
            anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
            if not anthropic_key:
                all_results.append(
                    DiagnosticResult(
                        "ANTHROPIC_API_KEY",
                        False,
                        "MISSING (required for Claude API/headless mode)",
                    )
                )

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
