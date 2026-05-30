"""Tests for Sutra memory system."""

from __future__ import annotations

import os
from pathlib import Path
from rich.console import Console

from sutra.core.memory import (
    run_memory_show,
    run_memory_add,
    run_memory_clear,
    get_memory_file,
)
from sutra.core.sync import run_sync


class TestMemory:
    """Tests for memory commands and logic."""

    def test_memory_show(self, sutra_repo: Path) -> None:
        """Should run memory show without error."""
        os.chdir(sutra_repo)
        console = Console(quiet=True)
        # Should not raise
        run_memory_show(console=console)

    def test_memory_add(self, sutra_repo: Path) -> None:
        """memory add should append note as a bullet point."""
        os.chdir(sutra_repo)
        console = Console(quiet=True)

        run_memory_add("project-lessons", "Test lesson entry", console=console)

        filepath = get_memory_file(sutra_repo, "project-lessons")
        content = filepath.read_text(encoding="utf-8")
        assert "- Test lesson entry" in content

    def test_memory_clear(self, sutra_repo: Path) -> None:
        """memory clear should reset file content but keep the header."""
        os.chdir(sutra_repo)
        console = Console(quiet=True)

        filepath = get_memory_file(sutra_repo, "project-lessons")
        # First add something
        run_memory_add("project-lessons", "Some content", console=console)

        # Clear it
        run_memory_clear("project-lessons", console=console)

        content = filepath.read_text(encoding="utf-8")
        assert "Some content" not in content
        assert "# Project Lessons" in content

    def test_memory_sync_propagates_to_runtimes(self, sutra_repo: Path) -> None:
        """Sync should include memory file contents in CLAUDE.md and AGENTS.md."""
        os.chdir(sutra_repo)
        console = Console(quiet=True)

        # Configure runtimes
        from sutra.core.config import load_sutra_config, save_sutra_config

        config = load_sutra_config(sutra_repo)
        config.runtimes = ["claude", "codex"]
        save_sutra_config(config, sutra_repo)

        # Add a custom lesson
        run_memory_add("project-lessons", "Sync test lesson note", console=console)

        # Run sync
        run_sync(runtime=None, console=console)

        # Check CLAUDE.md
        claude_md = sutra_repo / "CLAUDE.md"
        assert claude_md.exists()
        claude_content = claude_md.read_text(encoding="utf-8")
        assert "Sync test lesson note" in claude_content

        # Check AGENTS.md
        agents_md = sutra_repo / "AGENTS.md"
        assert agents_md.exists()
        agents_content = agents_md.read_text(encoding="utf-8")
        assert "Sync test lesson note" in agents_content
