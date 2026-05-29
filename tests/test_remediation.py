"""Remediation tests for Sutra security and logic bug fixes."""

from __future__ import annotations

import os
import yaml
from pathlib import Path
import pytest
from rich.console import Console

from sutra.core.security import validate_command, CommandSecurityError
from sutra.evidence.reporter import run_report
from sutra.core.context import run_context_refresh, run_context_diff
from sutra.runtimes.claude import ClaudeAdapter


def test_bash_sh_blocked() -> None:
    """bash and sh should be blocked by command validation policy."""
    with pytest.raises(CommandSecurityError) as excinfo:
        validate_command("bash -c 'touch bypass'")
    assert "Command executable 'bash' is not in the allowed" in str(excinfo.value)

    with pytest.raises(CommandSecurityError) as excinfo:
        validate_command("sh -c 'touch bypass'")
    assert "Command executable 'sh' is not in the allowed" in str(excinfo.value)

    # Valid command should pass
    parts = validate_command("pytest")
    assert parts == ["pytest"]


def test_report_fails_on_validation_failure(sutra_repo: Path) -> None:
    """sutra report should fail (raise SystemExit(1)) when a validation command fails."""
    os.chdir(sutra_repo)
    console = Console(quiet=True)

    # Run context refresh first to ensure config exists
    run_context_refresh(console=console)

    project_yaml = sutra_repo / ".sutra" / "project.yaml"
    with open(project_yaml) as f:
        data = yaml.safe_load(f) or {}

    # Set a failing validation command
    data["validation"] = {"failing_test": "python -c 'import sys; sys.exit(1)'"}
    with open(project_yaml, "w") as f:
        yaml.dump(data, f)

    # Run report — it should raise SystemExit(1)
    with pytest.raises(SystemExit) as excinfo:
        run_report("md", console=console)
    assert excinfo.value.code == 1


def test_context_diff_ignores_manual_sections(sutra_repo: Path, capsys: pytest.CaptureFixture) -> None:
    """context diff should ignore changes in manual sections of architecture.md."""
    os.chdir(sutra_repo)
    console = Console()

    # 1. Initialize context
    run_context_refresh(console=console)

    # 2. Add manual section to architecture.md
    arch_path = sutra_repo / ".sutra" / "context" / "architecture.md"
    content = arch_path.read_text(encoding="utf-8")
    assert "<!-- MANUAL SECTION:" in content

    idx = content.index("<!-- MANUAL SECTION:")
    newline_idx = content[idx:].index("\n")
    marker_line_end = idx + newline_idx + 1

    modified_content = content[:marker_line_end] + "\nThis is a manual architecture note.\n"
    arch_path.write_text(modified_content, encoding="utf-8")

    # Clear prior output
    capsys.readouterr()

    # 3. Run context diff
    run_context_diff(console=console)
    captured = capsys.readouterr()

    assert "architecture.md — no changes" in captured.out
    assert "changes detected" not in captured.out


def test_claude_hook_script_formatting_and_imports(tmp_path: Path) -> None:
    """Generated Claude pre-tool hook should be clean of unused imports and format violations."""
    import subprocess

    adapter = ClaudeAdapter(repo_root=tmp_path)
    script = adapter._render_hook_script(
        deny_list=[],
        warn_list=[],
        deny_write_patterns=[],
        allow_write_patterns=[],
        frozen_paths=[],
        guard_enabled=False,
        remote_policy_url=None
    )
    assert "import os" not in script

    # Write hook script to tmp file and assert ruff format checks pass
    hook_file = tmp_path / "pre_tool_guard.py"
    hook_file.write_text(script, encoding="utf-8")

    res = subprocess.run(["ruff", "format", "--check", str(hook_file)], capture_output=True, text=True)
    assert res.returncode == 0, f"Ruff format check failed on generated hook: {res.stdout}\n{res.stderr}"
