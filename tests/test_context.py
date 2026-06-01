"""Tests for niyam context commands."""

from __future__ import annotations

import os
from pathlib import Path

import yaml
from rich.console import Console


class TestContextRefresh:
    """Tests for the context refresh command."""

    def test_context_refresh_creates_architecture(self, niyam_repo: Path) -> None:
        """context refresh should create architecture.md."""
        from niyam.core.context import run_context_refresh

        console = Console(quiet=True)
        os.chdir(niyam_repo)
        run_context_refresh(console=console)

        arch = niyam_repo / ".niyam" / "context" / "architecture.md"
        assert arch.exists()

    def test_context_refresh_creates_validation(self, niyam_repo: Path) -> None:
        """context refresh should create validation.md."""
        from niyam.core.context import run_context_refresh

        console = Console(quiet=True)
        os.chdir(niyam_repo)
        run_context_refresh(console=console)

        val = niyam_repo / ".niyam" / "context" / "validation.md"
        assert val.exists()

    def test_context_refresh_detects_python(self, niyam_repo: Path) -> None:
        """context refresh should detect Python project."""
        # Create a pyproject.toml
        (niyam_repo / "pyproject.toml").write_text(
            '[project]\nname = "test"\n', encoding="utf-8"
        )

        from niyam.core.context import run_context_refresh

        console = Console(quiet=True)
        os.chdir(niyam_repo)
        run_context_refresh(console=console)

        with open(niyam_repo / ".niyam" / "project.yaml") as f:
            project = yaml.safe_load(f)

        assert "Python" in project["stack"]["languages"]

    def test_context_refresh_detects_node(self, niyam_repo: Path) -> None:
        """context refresh should detect Node.js project."""
        # Create a package.json
        (niyam_repo / "package.json").write_text('{"name": "test"}', encoding="utf-8")

        from niyam.core.context import run_context_refresh

        console = Console(quiet=True)
        os.chdir(niyam_repo)
        run_context_refresh(console=console)

        with open(niyam_repo / ".niyam" / "project.yaml") as f:
            project = yaml.safe_load(f)

        assert "JavaScript/TypeScript" in project["stack"]["languages"]

    def test_context_refresh_preserves_manual_section(self, niyam_repo: Path) -> None:
        """context refresh should preserve manual notes."""
        from niyam.core.context import run_context_refresh

        console = Console(quiet=True)
        os.chdir(niyam_repo)

        # First refresh
        run_context_refresh(console=console)

        # Add manual notes
        arch_path = niyam_repo / ".niyam" / "context" / "architecture.md"
        content = arch_path.read_text()
        content += "\nThis is my manual note.\n"
        arch_path.write_text(content, encoding="utf-8")

        # Second refresh
        run_context_refresh(console=console)

        updated = arch_path.read_text()
        assert "This is my manual note." in updated
