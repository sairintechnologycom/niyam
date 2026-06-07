"""Tests for Niyam cryptographic report signing and verification."""

from __future__ import annotations

import os
from pathlib import Path
import pytest
from rich.console import Console

from niyam.core.config import get_niyam_dir
from niyam.mission.planner import run_mission_plan, run_mission_approve
from niyam.mission.executor import run_mission_start
from niyam.mission.reporter import run_mission_report, run_verify_report


def test_verification_lifecycle(niyam_repo: Path) -> None:
    """Should successfully verify untampered report and fail if files are modified."""
    os.chdir(niyam_repo)
    console = Console(quiet=True)

    # 1. Create a dummy file in the repo that will be changed in mission
    dummy_src = niyam_repo / "src_file.py"
    dummy_src.write_text("print('hello')", encoding="utf-8")

    req_file = niyam_repo / "requirements.md"
    req_file.write_text("# Test requirement\n", encoding="utf-8")

    # 2. Plan, Approve, Run, Report
    mission_id = run_mission_plan(str(req_file), console=console)
    run_mission_approve(console=console)

    os.environ["NIYAM_TEST"] = "1"
    try:
        run_mission_start(console=console)
    finally:
        del os.environ["NIYAM_TEST"]

    run_mission_report(console=console)

    niyam_dir = get_niyam_dir(niyam_repo)
    run_dir = niyam_dir / "runs" / mission_id
    evidence_path = run_dir / "evidence.md"

    # 3. Verification of untampered files should succeed
    run_verify_report(str(evidence_path), console=console)

    # 4. Tamper with a file listed in the manifest
    tampered_file = niyam_repo / "change-T3.txt"
    tampered_file.write_text("print('hello tampered')", encoding="utf-8")

    # Verification should now fail
    with pytest.raises(SystemExit) as excinfo:
        run_verify_report(str(evidence_path), console=console)
    assert excinfo.value.code == 1
