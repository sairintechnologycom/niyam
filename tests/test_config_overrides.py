"""Tests for Niyam config environment variable overrides."""

from __future__ import annotations

import os
from pathlib import Path
import yaml

from niyam.core.config import load_niyam_config


def test_load_niyam_config_env_overrides(tmp_path: Path, monkeypatch) -> None:
    """Should load config and overlay env vars on top of it."""
    niyam_dir = tmp_path / ".niyam"
    niyam_dir.mkdir()
    config_file = niyam_dir / "niyam.yaml"

    initial_config = {
        "version": "0.1.0",
        "project_name": "test-project",
        "profile": "fullstack",
        "saas": {
            "enabled": False,
            "base_url": "https://api.niyam.ai",
            "api_key": "original-key",
            "project_id": "original-proj",
            "organization_id": "original-org",
        }
    }
    with open(config_file, "w", encoding="utf-8") as f:
        yaml.dump(initial_config, f)

    # 1. Without overrides
    config = load_niyam_config(tmp_path)
    assert config.saas.enabled is False
    assert config.saas.api_key == "original-key"

    # 2. With environment overrides
    monkeypatch.setenv("NIYAM_SAAS_ENABLED", "true")
    monkeypatch.setenv("NIYAM_SAAS_API_KEY", "env-key")
    monkeypatch.setenv("NIYAM_SAAS_BASE_URL", "https://custom.api.niyam.ai")
    monkeypatch.setenv("NIYAM_SAAS_PROJECT_ID", "env-proj")
    monkeypatch.setenv("NIYAM_SAAS_ORGANIZATION_ID", "env-org")
    monkeypatch.setenv("NIYAM_SAAS_PRICING_URL", "https://custom.pricing")

    config_overridden = load_niyam_config(tmp_path)
    assert config_overridden.saas.enabled is True
    assert config_overridden.saas.api_key == "env-key"
    assert config_overridden.saas.base_url == "https://custom.api.niyam.ai"
    assert config_overridden.saas.project_id == "env-proj"
    assert config_overridden.saas.organization_id == "env-org"
    assert config_overridden.saas.pricing_url == "https://custom.pricing"
