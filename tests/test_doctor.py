"""Tests for sutra doctor command."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from rich.console import Console


class TestDoctor:
    """Tests for the doctor command."""

    def test_doctor_passes_on_fresh_init(self, sutra_repo: Path) -> None:
        """Doctor should pass on a freshly initialized workspace."""
        from sutra.core.doctor import run_doctor

        console = Console(quiet=True)
        os.chdir(sutra_repo)
        # Should not raise
        run_doctor(runtime=None, console=console)

    def test_doctor_fails_without_sutra(self, tmp_repo: Path) -> None:
        """Doctor should fail if not a Sutra workspace."""
        from sutra.core.doctor import run_doctor

        console = Console(quiet=True)
        os.chdir(tmp_repo)

        with pytest.raises(SystemExit):
            run_doctor(runtime=None, console=console)

    def test_doctor_detects_missing_files(self, sutra_repo: Path) -> None:
        """Doctor should detect missing required files."""
        from sutra.core.doctor import run_doctor

        # Remove a required file
        (sutra_repo / ".sutra" / "project.yaml").unlink()

        console = Console(quiet=True)
        os.chdir(sutra_repo)

        with pytest.raises(SystemExit):
            run_doctor(runtime=None, console=console)

    def test_doctor_detects_invalid_yaml(self, sutra_repo: Path) -> None:
        """Doctor should detect invalid YAML."""
        # Write invalid YAML
        (sutra_repo / ".sutra" / "project.yaml").write_text(
            "invalid: yaml: [broken", encoding="utf-8"
        )

        from sutra.core.doctor import run_doctor

        console = Console(quiet=True)
        os.chdir(sutra_repo)

        with pytest.raises(SystemExit):
            run_doctor(runtime=None, console=console)
