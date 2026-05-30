"""Tests for CLI command template auto-boilerplating."""

from __future__ import annotations

import os
from pathlib import Path
from rich.console import Console

from sutra.core.context import run_context_refresh
from sutra.core.config import get_sutra_dir


def test_template_boilerplating_on_refresh(sutra_repo: Path) -> None:
    os.chdir(sutra_repo)
    console = Console(quiet=True)

    # Trigger context refresh
    run_context_refresh(console)

    # Check that missing commands are boilerplated
    commands_dir = get_sutra_dir(sutra_repo) / "commands"
    assert commands_dir.is_dir()

    # We expect sutra-hello.md and others to be created
    hello_template = commands_dir / "sutra-hello.md"
    assert hello_template.is_file()

    content = hello_template.read_text(encoding="utf-8")
    assert "# sutra hello" in content
    assert "## Usage" in content
    assert "sutra hello" in content
