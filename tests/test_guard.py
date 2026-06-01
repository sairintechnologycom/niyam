"""Tests for niyam guard command."""

from __future__ import annotations

import os
from pathlib import Path

import yaml
from rich.console import Console


class TestGuard:
    """Tests for the guard command."""

    def test_guard_enable(self, niyam_repo: Path) -> None:
        """guard enable should set guard.enabled to True."""
        from niyam.policies.guard import run_guard_enable

        console = Console(quiet=True)
        os.chdir(niyam_repo)
        run_guard_enable(console=console)

        with open(niyam_repo / ".niyam" / "niyam.yaml") as f:
            config = yaml.safe_load(f)

        assert config["guard"]["enabled"] is True

    def test_guard_disable(self, niyam_repo: Path) -> None:
        """guard disable should set guard.enabled to False."""
        from niyam.policies.guard import run_guard_enable, run_guard_disable

        console = Console(quiet=True)
        os.chdir(niyam_repo)
        run_guard_enable(console=console)
        run_guard_disable(console=console)

        with open(niyam_repo / ".niyam" / "niyam.yaml") as f:
            config = yaml.safe_load(f)

        assert config["guard"]["enabled"] is False

    def test_guard_careful_adds_warn_list(self, niyam_repo: Path) -> None:
        """guard careful should populate warn list in commands.yaml."""
        from niyam.policies.guard import run_guard_careful

        console = Console(quiet=True)
        os.chdir(niyam_repo)
        run_guard_careful(console=console)

        with open(niyam_repo / ".niyam" / "policies" / "commands.yaml") as f:
            data = yaml.safe_load(f)

        assert len(data.get("warn", [])) > 0
        assert "rm -rf" in data["warn"]

    def test_guard_freeze_adds_path(self, niyam_repo: Path) -> None:
        """guard freeze should add frozen path."""
        from niyam.policies.guard import run_guard_freeze

        console = Console(quiet=True)
        os.chdir(niyam_repo)
        run_guard_freeze(path="apps/web", console=console)

        with open(niyam_repo / ".niyam" / "niyam.yaml") as f:
            config = yaml.safe_load(f)

        assert "apps/web" in config["guard"]["frozen_paths"]

    def test_guard_freeze_enables_guard(self, niyam_repo: Path) -> None:
        """guard freeze should auto-enable guard."""
        from niyam.policies.guard import run_guard_freeze

        console = Console(quiet=True)
        os.chdir(niyam_repo)
        run_guard_freeze(path="src", console=console)

        with open(niyam_repo / ".niyam" / "niyam.yaml") as f:
            config = yaml.safe_load(f)

        assert config["guard"]["enabled"] is True
