"""Tests for Niyam mission dashboard and token ledger operations."""

from __future__ import annotations

import json
import os
from pathlib import Path
from rich.console import Console
from unittest.mock import patch

from niyam.core.config import get_niyam_dir
from niyam.mission.planner import run_mission_plan, run_mission_approve
from niyam.mission.executor import run_mission_start
from niyam.mission.dashboard import run_mission_dashboard, generate_dashboard_renderable


def test_dashboard_rendering(niyam_repo: Path) -> None:
    """Should correctly render dashboard with and without token ledger data."""
    os.chdir(niyam_repo)
    console = Console(quiet=True)

    # 1. Create requirements file and plan
    req_file = niyam_repo / "requirements.md"
    req_file.write_text("# Test Requirements\n", encoding="utf-8")
    mission_id = run_mission_plan(str(req_file), console=console)
    run_mission_approve(console=console)

    run_dir = get_niyam_dir(niyam_repo) / "runs" / mission_id

    # 2. Render dashboard when no token ledger exists (should not raise error)
    renderable = generate_dashboard_renderable(
        run_dir, get_niyam_dir(niyam_repo), mission_id
    )
    assert renderable is not None

    # Enable marketing metrics so savings are calculated
    import yaml

    niyam_config_path = get_niyam_dir(niyam_repo) / "niyam.yaml"
    with open(niyam_config_path, "r", encoding="utf-8") as f:
        niyam_data = yaml.safe_load(f) or {}
    niyam_data["show_marketing_metrics"] = True
    with open(niyam_config_path, "w", encoding="utf-8") as f:
        yaml.dump(niyam_data, f)

    # Run start in test mode (this will populate the token ledger)
    os.environ["NIYAM_TEST"] = "1"
    try:
        run_mission_start(console=console)
    finally:
        del os.environ["NIYAM_TEST"]

    # 3. Check token ledger file was created and is valid
    ledger_path = run_dir / "token-ledger.json"
    assert ledger_path.exists()
    with open(ledger_path, encoding="utf-8") as f:
        ledger = json.load(f)

    assert "summary" in ledger
    assert "events" in ledger
    assert ledger["summary"]["total_tokens"] > 0
    assert ledger["summary"]["total_cost_usd"] > 0.0
    assert ledger["summary"]["total_savings_usd"] > 0.0

    # 4. Render dashboard with token ledger (should contain token and cost details)
    renderable_with_ledger = generate_dashboard_renderable(
        run_dir, get_niyam_dir(niyam_repo), mission_id
    )
    assert renderable_with_ledger is not None

    # Call run_mission_dashboard (non-watch mode)
    with patch("rich.console.Console.print") as mock_print:
        run_mission_dashboard(watch=False, console=console)
        # Should render and output dashboard to console
        assert mock_print.called


def test_dashboard_watch_mode(niyam_repo: Path) -> None:
    """Should gracefully start and terminate in watch mode."""
    os.chdir(niyam_repo)
    console = Console(quiet=True)

    req_file = niyam_repo / "requirements.md"
    req_file.write_text("# Test Requirements\n", encoding="utf-8")
    run_mission_plan(str(req_file), console=console)
    run_mission_approve(console=console)

    # Mock time.sleep to raise KeyboardInterrupt to exit loop immediately
    with (
        patch("time.sleep", side_effect=KeyboardInterrupt),
        patch("rich.live.Live.update"),
    ):
        run_mission_dashboard(watch=True, console=console)
        # Should not raise exception (handled KeyboardInterrupt gracefully)
