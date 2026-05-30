"""Tests for Sutra pack system."""

from __future__ import annotations

import os
from pathlib import Path
import pytest
from rich.console import Console

from sutra.core.config import load_sutra_config
from sutra.core.packs import list_packs, add_pack, remove_pack, sync_packs


class TestPacks:
    """Tests for pack commands and logic."""

    def test_list_packs(self, sutra_repo: Path) -> None:
        """Should list available packs."""
        packs = list_packs(sutra_repo)
        names = {p["name"] for p in packs}
        assert "agentic-engineering" in names
        assert "superpowers-methodology" in names

        # Initially none are installed
        for p in packs:
            assert not p["installed"]

    def test_add_pack_copies_files(self, sutra_repo: Path) -> None:
        """add_pack should copy pack files into .sutra/ and update sutra.yaml."""
        os.chdir(sutra_repo)
        console = Console(quiet=True)

        add_pack(sutra_repo, "superpowers-methodology", console=console)

        # Check config updated
        config = load_sutra_config(sutra_repo)
        assert "superpowers-methodology" in config.packs

        # Check files created with header comments
        skill_file = sutra_repo / ".sutra" / "skills" / "superpowers" / "SKILL.md"
        assert skill_file.exists()
        content = skill_file.read_text(encoding="utf-8")
        assert content.startswith("<!-- pack: superpowers-methodology -->")

        command_file = sutra_repo / ".sutra" / "commands" / "superpower.md"
        assert command_file.exists()
        cmd_content = command_file.read_text(encoding="utf-8")
        assert cmd_content.startswith("<!-- pack: superpowers-methodology -->")

    def test_add_pack_conflict(self, sutra_repo: Path) -> None:
        """add_pack without force should raise error if files already exist with different content."""
        os.chdir(sutra_repo)
        console = Console(quiet=True)

        # Create conflicting file in .sutra/
        conflict_file = sutra_repo / ".sutra" / "commands" / "superpower.md"
        conflict_file.parent.mkdir(parents=True, exist_ok=True)
        conflict_file.write_text("User custom command content", encoding="utf-8")

        with pytest.raises(ValueError, match="Conflict detected"):
            add_pack(
                sutra_repo, "superpowers-methodology", force=False, console=console
            )

        # Overwrite with --force should succeed
        add_pack(sutra_repo, "superpowers-methodology", force=True, console=console)
        assert conflict_file.read_text(encoding="utf-8").startswith(
            "<!-- pack: superpowers-methodology -->"
        )

    def test_remove_pack(self, sutra_repo: Path) -> None:
        """remove_pack should delete pack files and update config."""
        os.chdir(sutra_repo)
        console = Console(quiet=True)

        # Add it first
        add_pack(sutra_repo, "superpowers-methodology", console=console)
        skill_file = sutra_repo / ".sutra" / "skills" / "superpowers" / "SKILL.md"
        assert skill_file.exists()

        # Remove it
        remove_pack(sutra_repo, "superpowers-methodology", console=console)

        config = load_sutra_config(sutra_repo)
        assert "superpowers-methodology" not in config.packs
        assert not skill_file.exists()
        assert not (sutra_repo / ".sutra" / "skills" / "superpowers").exists()

    def test_sync_packs(self, sutra_repo: Path) -> None:
        """sync_packs should re-apply installed packs."""
        os.chdir(sutra_repo)
        console = Console(quiet=True)

        # Manually inject pack into config without writing files
        config = load_sutra_config(sutra_repo)
        config.packs.append("superpowers-methodology")
        from sutra.core.config import save_sutra_config

        save_sutra_config(config, sutra_repo)

        # Skill file should not exist yet
        skill_file = sutra_repo / ".sutra" / "skills" / "superpowers" / "SKILL.md"
        assert not skill_file.exists()

        # Sync packs should write the files
        sync_packs(sutra_repo, console=console)
        assert skill_file.exists()
