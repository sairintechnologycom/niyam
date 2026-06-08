"""Tests for Niyam memory system."""

from __future__ import annotations

import os
import json
from pathlib import Path
from rich.console import Console

from niyam.core.memory import (
    CodebaseIndexer,
    run_memory_show,
    run_memory_add,
    run_memory_clear,
    get_memory_file,
)
from niyam.core.sync import run_sync


class TestMemory:
    """Tests for memory commands and logic."""

    def test_memory_show(self, niyam_repo: Path) -> None:
        """Should run memory show without error."""
        os.chdir(niyam_repo)
        console = Console(quiet=True)
        # Should not raise
        run_memory_show(console=console)

    def test_memory_add(self, niyam_repo: Path) -> None:
        """memory add should append note as a bullet point."""
        os.chdir(niyam_repo)
        console = Console(quiet=True)

        run_memory_add("project-lessons", "Test lesson entry", console=console)

        filepath = get_memory_file(niyam_repo, "project-lessons")
        content = filepath.read_text(encoding="utf-8")
        assert "- Test lesson entry" in content

        records_path = filepath.parent / "index.jsonl"
        assert records_path.exists()
        records = [
            json.loads(line)
            for line in records_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        assert records[-1]["memory_file"] == "project-lessons.md"
        assert records[-1]["content"] == "Test lesson entry"
        assert records[-1]["source"] == "manual"

    def test_memory_clear(self, niyam_repo: Path) -> None:
        """memory clear should reset file content but keep the header."""
        os.chdir(niyam_repo)
        console = Console(quiet=True)

        filepath = get_memory_file(niyam_repo, "project-lessons")
        # First add something
        run_memory_add("project-lessons", "Some content", console=console)

        # Clear it
        run_memory_clear("project-lessons", console=console)

        content = filepath.read_text(encoding="utf-8")
        assert "Some content" not in content
        assert "# Project Lessons" in content

    def test_memory_sync_propagates_to_runtimes(self, niyam_repo: Path) -> None:
        """Sync should include memory file contents in CLAUDE.md and AGENTS.md."""
        os.chdir(niyam_repo)
        console = Console(quiet=True)

        # Configure runtimes
        from niyam.core.config import load_niyam_config, save_niyam_config

        config = load_niyam_config(niyam_repo)
        config.runtimes = ["claude", "codex"]
        save_niyam_config(config, niyam_repo)

        # Add a custom lesson
        run_memory_add("project-lessons", "Sync test lesson note", console=console)

        # Run sync
        run_sync(runtime=None, console=console)

        # Check CLAUDE.md
        claude_md = niyam_repo / "CLAUDE.md"
        assert claude_md.exists()
        claude_content = claude_md.read_text(encoding="utf-8")
        assert "Sync test lesson note" in claude_content

        # Check AGENTS.md
        agents_md = niyam_repo / "AGENTS.md"
        assert agents_md.exists()
        agents_content = agents_md.read_text(encoding="utf-8")
        assert "Sync test lesson note" in agents_content

    def test_codebase_indexer_search_jsonl_fallback(self, niyam_repo: Path) -> None:
        """Codebase search should return relevant snippets without Chroma."""
        os.chdir(niyam_repo)
        target = niyam_repo / "src" / "billing.py"
        target.parent.mkdir()
        target.write_text(
            "def calculate_invoice_total():\n    return 'invoice total'\n",
            encoding="utf-8",
        )
        os.environ["NIYAM_DISABLE_CHROMA"] = "1"

        try:
            indexer = CodebaseIndexer(niyam_repo)
            count = indexer.build_index()
            matches = indexer.search("invoice total", k=3)
        finally:
            os.environ.pop("NIYAM_DISABLE_CHROMA", None)

        assert count > 0
        assert any(match["path"] == "src/billing.py" for match in matches)
