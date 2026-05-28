"""Tests for Sutra multi-lens review system."""

from __future__ import annotations

import os
from pathlib import Path
import pytest
from rich.console import Console

from sutra.core.review import run_review, get_git_diff


class TestReview:
    """Tests for multi-lens review command and prompt generation."""

    def test_get_git_diff_untracked_file(self, sutra_repo: Path) -> None:
        """Should detect untracked files in git diff."""
        os.chdir(sutra_repo)

        # Write untracked file
        untracked_file = sutra_repo / "main.py"
        untracked_file.write_text("print('Hello World')\n", encoding="utf-8")

        diff = get_git_diff()
        assert "main.py" in diff
        assert "print('Hello World')" in diff

    def test_run_review_engineering_lens(self, sutra_repo: Path) -> None:
        """Should run review with engineering lens successfully."""
        os.chdir(sutra_repo)
        console = Console(quiet=True)

        # Create changes
        untracked_file = sutra_repo / "main.py"
        untracked_file.write_text("def test(): pass\n", encoding="utf-8")

        os.environ["SUTRA_TEST"] = "1"
        try:
            # Run engineering collaborative review
            run_review(lens="engineering", runtime="claude", mode="collaborative", console=console)
            
            # Check prompt was saved to runs directory
            prompt_files = list((sutra_repo / ".sutra" / "runs").glob("review-engineering-collaborative-prompt.md"))
            assert len(prompt_files) == 1
            content = prompt_files[0].read_text(encoding="utf-8")
            assert "# Engineering Quality & Architecture Review" in content
            assert "def test(): pass" in content
        finally:
            del os.environ["SUTRA_TEST"]

    def test_run_review_adversarial_mode(self, sutra_repo: Path) -> None:
        """Should include adversarial warning headers when mode is adversarial."""
        os.chdir(sutra_repo)
        console = Console(quiet=True)

        untracked_file = sutra_repo / "main.py"
        untracked_file.write_text("def test(): pass\n", encoding="utf-8")

        os.environ["SUTRA_TEST"] = "1"
        try:
            run_review(lens="security", runtime="claude", mode="adversarial", console=console)
            
            prompt_files = list((sutra_repo / ".sutra" / "runs").glob("review-security-adversarial-prompt.md"))
            assert len(prompt_files) == 1
            content = prompt_files[0].read_text(encoding="utf-8")
            assert "ADVERSARIAL MODE ENABLED" in content
            assert "# Secure Code Review" in content
        finally:
            del os.environ["SUTRA_TEST"]
