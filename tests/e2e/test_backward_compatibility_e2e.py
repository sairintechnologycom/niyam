"""E2E tests for backward compatibility and help outputs."""

from __future__ import annotations

import json
import os
from pathlib import Path
import yaml


def test_existing_niyam_commands(clean_workspace: Path, run_cli) -> None:
    """Existing Niyam commands still work and have correct output."""
    # 1. Initialize Niyam
    init_res = run_cli(["niyam", "init", "--profile", "fullstack"], cwd=clean_workspace)
    assert init_res.returncode == 0

    # 2. niyam doctor command runs successfully
    doc_res = run_cli(["niyam", "doctor"], cwd=clean_workspace)
    assert doc_res.returncode == 0
    assert "0 errors" in doc_res.stdout

    # 3. niyam --help lists existing/new commands
    help_res = run_cli(["niyam", "--help"], cwd=clean_workspace)
    assert help_res.returncode == 0
    assert "init" in help_res.stdout
    assert "doctor" in help_res.stdout
    assert "scan" in help_res.stdout
    assert "guard" in help_res.stdout


def test_governance_commands_help(clean_workspace: Path, run_cli) -> None:
    """New governance commands have help output."""
    # scan --help
    scan_help = run_cli(["niyam", "scan", "--help"], cwd=clean_workspace)
    assert scan_help.returncode == 0
    assert "profile" in scan_help.stdout
    assert "output" in scan_help.stdout

    # guard --help
    guard_help = run_cli(["niyam", "guard", "--help"], cwd=clean_workspace)
    assert guard_help.returncode == 0
    assert "enable" in guard_help.stdout
    assert "run" in guard_help.stdout

    # mcp --help
    mcp_help = run_cli(["niyam", "mcp", "--help"], cwd=clean_workspace)
    assert mcp_help.returncode == 0
    assert "register" in mcp_help.stdout
    assert "list" in mcp_help.stdout

    # evidence --help
    ev_help = run_cli(["niyam", "evidence", "--help"], cwd=clean_workspace)
    assert ev_help.returncode == 0
    assert "generate" in ev_help.stdout


def test_legacy_config_backward_compatibility(clean_workspace: Path, run_cli) -> None:
    """Existing config without governance section still works."""
    # 1. Initialize Niyam (creates valid structure)
    init_res = run_cli(["niyam", "init", "--profile", "fullstack"], cwd=clean_workspace)
    assert init_res.returncode == 0

    # 2. Read niyam.yaml and remove governance key
    niyam_yaml_path = clean_workspace / ".niyam" / "niyam.yaml"
    with open(niyam_yaml_path, encoding="utf-8") as f:
        config_data = yaml.safe_load(f) or {}

    if "governance" in config_data:
        del config_data["governance"]

    with open(niyam_yaml_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(config_data, f)

    # 3. Run doctor to make sure it validates successfully
    doc_res = run_cli(["niyam", "doctor"], cwd=clean_workspace)
    assert doc_res.returncode == 0

    # 4. Run scan to ensure it runs without governance config block
    scan_res = run_cli(["niyam", "scan"], cwd=clean_workspace)
    assert scan_res.returncode == 0
    assert "Readiness Score:" in scan_res.stdout


def test_ci_offline_invocation(clean_workspace: Path, run_cli) -> None:
    """CI-like invocation works offline."""
    # 1. Initialize Niyam
    init_res = run_cli(["niyam", "init", "--profile", "fullstack"], cwd=clean_workspace)
    assert init_res.returncode == 0

    # 2. Run scan in "CI" mode (simulated via env/flags)
    # Ensure it runs offline (which is true, no APIs hit) and outputs correct JSON format
    os.environ["CI"] = "true"
    try:
        scan_res = run_cli(["niyam", "scan", "--output", "json"], cwd=clean_workspace)
        assert scan_res.returncode == 0
        data = json.loads(scan_res.stdout)
        assert "score" in data
        assert data["score"] >= 85
    finally:
        os.environ.pop("CI", None)
