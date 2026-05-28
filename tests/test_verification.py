"""Tests for Sutra cryptographic report signing and verification."""

from __future__ import annotations

import os
import json
from pathlib import Path
import pytest
from rich.console import Console

from sutra.core.config import get_sutra_dir
from sutra.mission.planner import run_mission_plan, run_mission_approve
from sutra.mission.executor import run_mission_start
from sutra.mission.reporter import run_mission_report, run_verify_report


def test_verification_lifecycle(sutra_repo: Path) -> None:
    """Should successfully verify untampered report and fail if files are modified."""
    os.chdir(sutra_repo)
    console = Console(quiet=True)

    # 1. Create a dummy file in the repo that will be changed in mission
    dummy_src = sutra_repo / "src_file.py"
    dummy_src.write_text("print('hello')", encoding="utf-8")

    req_file = sutra_repo / "requirements.md"
    req_file.write_text("# Test requirement\n", encoding="utf-8")
    
    # 2. Plan, Approve, Run, Report
    mission_id = run_mission_plan(str(req_file), console=console)
    run_mission_approve(console=console)

    os.environ["SUTRA_TEST"] = "1"
    try:
        run_mission_start(console=console)
    finally:
        del os.environ["SUTRA_TEST"]

    run_mission_report(console=console)

    sutra_dir = get_sutra_dir(sutra_repo)
    run_dir = sutra_dir / "runs" / mission_id
    evidence_path = run_dir / "evidence.md"

    # 3. Verification of untampered files should succeed
    run_verify_report(str(evidence_path), console=console)

    # 4. Tamper with a source file listed in git diff/git status
    dummy_src.write_text("print('hello tampered')", encoding="utf-8")

    # Verification should now fail
    with pytest.raises(SystemExit) as excinfo:
        run_verify_report(str(evidence_path), console=console)
    assert excinfo.value.code == 1
