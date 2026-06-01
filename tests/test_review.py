"""Tests for Niyam multi-lens review system."""

from __future__ import annotations

import os
from pathlib import Path
from rich.console import Console

from niyam.core.review import run_review, get_git_diff


class TestReview:
    """Tests for multi-lens review command and prompt generation."""

    def test_get_git_diff_untracked_file(self, niyam_repo: Path) -> None:
        """Should detect untracked files in git diff."""
        os.chdir(niyam_repo)

        # Write untracked file
        untracked_file = niyam_repo / "main.py"
        untracked_file.write_text("print('Hello World')\n", encoding="utf-8")

        diff = get_git_diff()
        assert "main.py" in diff
        assert "print('Hello World')" in diff

    def test_run_review_engineering_lens(self, niyam_repo: Path) -> None:
        """Should run review with engineering lens successfully."""
        os.chdir(niyam_repo)
        console = Console(quiet=True)

        # Create changes
        untracked_file = niyam_repo / "main.py"
        untracked_file.write_text("def test(): pass\n", encoding="utf-8")

        os.environ["NIYAM_TEST"] = "1"
        try:
            # Run engineering collaborative review
            run_review(
                lens="engineering",
                runtime="claude",
                mode="collaborative",
                console=console,
            )

            # Check prompt was saved to runs directory
            prompt_files = list(
                (niyam_repo / ".niyam" / "runs").glob(
                    "review-engineering-collaborative-prompt.md"
                )
            )
            assert len(prompt_files) == 1
            content = prompt_files[0].read_text(encoding="utf-8")
            assert "# Engineering Quality & Architecture Review" in content
            assert "def test(): pass" in content
        finally:
            del os.environ["NIYAM_TEST"]

    def test_run_review_adversarial_mode(self, niyam_repo: Path) -> None:
        """Should include adversarial warning headers when mode is adversarial."""
        os.chdir(niyam_repo)
        console = Console(quiet=True)

        untracked_file = niyam_repo / "main.py"
        untracked_file.write_text("def test(): pass\n", encoding="utf-8")

        os.environ["NIYAM_TEST"] = "1"
        try:
            run_review(
                lens="security", runtime="claude", mode="adversarial", console=console
            )

            prompt_files = list(
                (niyam_repo / ".niyam" / "runs").glob(
                    "review-security-adversarial-prompt.md"
                )
            )
            assert len(prompt_files) == 1
            content = prompt_files[0].read_text(encoding="utf-8")
            assert "ADVERSARIAL MODE ENABLED" in content
            assert "# Secure Code Review" in content
        finally:
            del os.environ["NIYAM_TEST"]

    def test_get_git_diff_file_size_limit(self, niyam_repo: Path) -> None:
        """Should skip untracked files exceeding 50 KB size limit."""
        os.chdir(niyam_repo)

        # Create a large untracked file (60 KB)
        large_file = niyam_repo / "large_file.py"
        large_file.write_text("A" * (60 * 1024), encoding="utf-8")

        diff = get_git_diff(niyam_repo)
        assert "large_file.py" in diff
        assert "exceeds 50 KB size limit" in diff
        assert "AAAAA" not in diff  # Content should not be included

    def test_get_git_diff_budget_limit(self, niyam_repo: Path) -> None:
        """Should skip untracked files that exceed the 200 KB total budget limit."""
        os.chdir(niyam_repo)

        # Create multiple files that total over 200 KB but individually are under 50 KB
        for i in range(5):
            f = niyam_repo / f"file_{i}.py"
            f.write_text("A" * (45 * 1024), encoding="utf-8")

        diff = get_git_diff(niyam_repo)
        assert "exceeds total prompt budget limit" in diff

    def test_get_git_diff_skip_binary_files(self, niyam_repo: Path) -> None:
        """Should skip binary files entirely."""
        os.chdir(niyam_repo)

        binary_file = niyam_repo / "binary.bin"
        binary_file.write_bytes(b"\x00\x01\x02\x03\x00")

        diff = get_git_diff(niyam_repo)
        assert "binary.bin" not in diff

    def test_get_git_diff_redact_secrets(self, niyam_repo: Path) -> None:
        """Should redact secrets (AWS keys, tokens, api keys) in git diff."""
        os.chdir(niyam_repo)

        secret_file = niyam_repo / "secret.py"
        secret_file.write_text(
            "aws_key = 'AKIA1234567890123456'\ntoken = 'my-super-secret-token'\n",
            encoding="utf-8",
        )

        diff = get_git_diff(niyam_repo)
        assert "AKIA1234567890123456" not in diff
        assert "[REDACTED_AWS_KEY]" in diff
        assert "my-super-secret-token" not in diff
        assert "[REDACTED_SECRET]" in diff
