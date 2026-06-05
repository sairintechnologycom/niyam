"""Regression tests for Niyam config schema backward compatibility."""

from __future__ import annotations

from pathlib import Path

from niyam.core.config import load_niyam_config, NiyamConfig


def test_legacy_config_without_governance_loads_successfully(tmp_path: Path) -> None:
    """A config file without any governance section must load cleanly."""
    niyam_dir = tmp_path / ".niyam"
    niyam_dir.mkdir()
    config_file = niyam_dir / "niyam.yaml"

    # Write a classic config file
    config_file.write_text(
        "version: 0.1.0\n"
        "project_name: test-legacy-app\n"
        "profile: fullstack\n"
        "runtimes:\n"
        "  - claude\n"
        "packs:\n"
        "  - standard\n"
        "guard:\n"
        "  enabled: true\n"
        "  careful: true\n"
        "  frozen_paths:\n"
        "    - docs/\n"
    )

    config = load_niyam_config(tmp_path)
    assert isinstance(config, NiyamConfig)
    assert config.project_name == "test-legacy-app"
    assert config.version == "0.1.0"
    assert config.profile == "fullstack"
    assert config.runtimes == ["claude"]
    assert config.packs == ["standard"]
    assert config.guard.enabled is True
    assert config.guard.careful is True
    assert config.guard.frozen_paths == ["docs/"]
    assert config.governance is None


def test_minimal_config_loads_with_defaults(tmp_path: Path) -> None:
    """A minimal config file must fill in default values for missing sections."""
    niyam_dir = tmp_path / ".niyam"
    niyam_dir.mkdir()
    config_file = niyam_dir / "niyam.yaml"

    config_file.write_text("version: 0.1.0\n")

    config = load_niyam_config(tmp_path)
    assert isinstance(config, NiyamConfig)
    assert config.version == "0.1.0"
    assert config.project_name == ""
    assert config.profile == "fullstack"
    assert config.runtimes == []
    assert config.packs == []
    assert config.guard.enabled is False
    assert config.guard.careful is False
    assert config.guard.frozen_paths == []
    assert config.governance is None
