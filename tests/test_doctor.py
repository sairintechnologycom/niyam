"""Tests for niyam doctor command."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from rich.console import Console


class TestDoctor:
    """Tests for the doctor command."""

    def test_doctor_passes_on_fresh_init(self, niyam_repo: Path) -> None:
        """Doctor should pass on a freshly initialized workspace."""
        from niyam.core.doctor import run_doctor

        console = Console(quiet=True)
        os.chdir(niyam_repo)
        # Should not raise
        run_doctor(runtime=None, console=console)

    def test_doctor_fails_without_niyam(self, tmp_repo: Path) -> None:
        """Doctor should fail if not a Niyam workspace."""
        from niyam.core.doctor import run_doctor

        console = Console(quiet=True)
        os.chdir(tmp_repo)

        with pytest.raises(SystemExit):
            run_doctor(runtime=None, console=console)

    def test_doctor_detects_missing_files(self, niyam_repo: Path) -> None:
        """Doctor should detect missing required files."""
        from niyam.core.doctor import run_doctor

        # Remove a required file
        (niyam_repo / ".niyam" / "project.yaml").unlink()

        console = Console(quiet=True)
        os.chdir(niyam_repo)

        with pytest.raises(SystemExit):
            run_doctor(runtime=None, console=console)

    def test_doctor_detects_invalid_yaml(self, niyam_repo: Path) -> None:
        """Doctor should detect invalid YAML."""
        # Write invalid YAML
        (niyam_repo / ".niyam" / "project.yaml").write_text(
            "invalid: yaml: [broken", encoding="utf-8"
        )

        from niyam.core.doctor import run_doctor

        console = Console(quiet=True)
        os.chdir(niyam_repo)

        with pytest.raises(SystemExit):
            run_doctor(runtime=None, console=console)
