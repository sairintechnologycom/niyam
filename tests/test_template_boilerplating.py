"""Tests for CLI command template auto-boilerplating."""

from __future__ import annotations

import os
from pathlib import Path
from rich.console import Console

from niyam.core.context import run_context_refresh
from niyam.core.config import get_niyam_dir


def test_template_boilerplating_on_refresh(niyam_repo: Path) -> None:
    os.chdir(niyam_repo)
    console = Console(quiet=True)

    # Trigger context refresh
    run_context_refresh(console)

    # Check that missing commands are boilerplated
    commands_dir = get_niyam_dir(niyam_repo) / "commands"
    assert commands_dir.is_dir()

    # We expect niyam-hello.md and others to be created
    hello_template = commands_dir / "niyam-hello.md"
    assert hello_template.is_file()

    content = hello_template.read_text(encoding="utf-8")
    assert "# niyam hello" in content
    assert "## Usage" in content
    assert "niyam hello" in content
