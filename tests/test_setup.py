"""Tests for the interactive onboarding setup wizard."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch
from rich.console import Console

from sutra.core.config import load_sutra_config, get_sutra_dir
from sutra.core.setup import run_setup


def test_setup_wizard_fresh_initialization(tmp_repo: Path) -> None:
    """Should run setup, initialize sutra with selected profile, detected runtimes, and guardrails."""
    os.chdir(tmp_repo)
    console = Console(quiet=True)

    # 1. Assert .sutra does not exist yet
    sutra_dir = get_sutra_dir(tmp_repo)
    assert not sutra_dir.exists()

    # 2. Patch inputs and detections
    # Profile prompt: "backend"
    # Runtime "claude" is enabled (detected)
    # Runtime "gemini" is disabled (detected but user says False)
    # Guardrails: True
    # Careful mode: True
    def mock_ask(prompt_text, **kwargs):
        if "profile fits your stack" in prompt_text:
            return "backend"
        return kwargs.get("default", "")

    def mock_confirm(prompt_text, **kwargs):
        if "enable the" in prompt_text:
            if "claude" in prompt_text:
                return True
            if "gemini" in prompt_text:
                return False
        if "safety guardrails" in prompt_text:
            return True
        if "careful mode" in prompt_text:
            return True
        return kwargs.get("default", True)

    def mock_which(cmd):
        # Mocking that both claude and gemini are in PATH, but codex is not
        if cmd in ("claude", "gemini"):
            return f"/usr/local/bin/{cmd}"
        return None

    with (
        patch("rich.prompt.Prompt.ask", side_effect=mock_ask),
        patch("rich.prompt.Confirm.ask", side_effect=mock_confirm),
        patch("shutil.which", side_effect=mock_which),
    ):
        run_setup(console=console)

    # 3. Verify .sutra/ is initialized
    assert sutra_dir.exists()
    assert (sutra_dir / "sutra.yaml").exists()

    # 4. Verify config settings
    config = load_sutra_config(tmp_repo)
    # Runtimes list should have claude, but not gemini or codex
    assert "claude" in config.runtimes
    assert "gemini" not in config.runtimes

    # Verify guards
    assert config.guard.enabled is True
    assert config.guard.careful is True
