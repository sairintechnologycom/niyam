"""Tests for Niyam mission mode."""

from __future__ import annotations

import os
import json
from pathlib import Path
import pytest
import yaml
from rich.console import Console

from niyam.core.config import get_niyam_dir
from niyam.mission.planner import (
    run_mission_plan,
    run_mission_approve,
    resolve_mission_id,
)
from niyam.mission.executor import (
    run_mission_start,
    run_mission_pause,
    run_mission_resume,
    load_plan,
)
from niyam.mission.status import run_mission_status
from niyam.mission.reporter import run_mission_report


class TestMission:
    """Tests for mission mode lifecycle."""

    def test_mission_plan_creates_files(self, niyam_repo: Path) -> None:
        """Should create runs dir, copy req file, and generate YAML templates."""
        os.chdir(niyam_repo)
        console = Console(quiet=True)

        # Create requirements file
        req_file = niyam_repo / "requirements.md"
        req_file.write_text(
            "# Implement Authentication\n\nRequire login validation.", encoding="utf-8"
        )

        mission_id = run_mission_plan(str(req_file), console=console)
        assert mission_id is not None

        niyam_dir = get_niyam_dir(niyam_repo)
        run_dir = niyam_dir / "runs" / mission_id
        assert run_dir.is_dir()

        # Check copied requirement
        assert (run_dir / "requirement.md").exists()
        assert (run_dir / "requirement.md").read_text(
            encoding="utf-8"
        ) == req_file.read_text(encoding="utf-8")

        # Check plan
        plan_path = run_dir / "mission-plan.yaml"
        assert plan_path.exists()
        with open(plan_path, encoding="utf-8") as f:
            plan = yaml.safe_load(f)
        assert plan["mission"]["id"] == mission_id
        assert plan["mission"]["status"] == "planned"
        assert len(plan["tasks"]) == 5

        # Check task list
        assert (run_dir / "task-list.yaml").exists()

        # Check approval.json
        assert (run_dir / "approval.json").exists()
        with open(run_dir / "approval.json", encoding="utf-8") as f:
            app_data = json.load(f)
        assert not app_data["approved"]

    def test_mission_approve(self, niyam_repo: Path) -> None:
        """Should update approval.json and plan status."""
        os.chdir(niyam_repo)
        console = Console(quiet=True)

        req_file = niyam_repo / "requirements.md"
        req_file.write_text("# Implement Auth\n", encoding="utf-8")
        mission_id = run_mission_plan(str(req_file), console=console)

        # Approve it
        run_mission_approve(console=console)

        run_dir = get_niyam_dir(niyam_repo) / "runs" / mission_id
        with open(run_dir / "approval.json", encoding="utf-8") as f:
            app_data = json.load(f)
        assert app_data["approved"]

        plan = load_plan(run_dir)
        assert plan["mission"]["status"] == "approved"

    def test_mission_execution_lifecycle(self, niyam_repo: Path) -> None:
        """Should sequentially run tasks, log events, and generate report."""
        os.chdir(niyam_repo)
        console = Console(quiet=True)

        req_file = niyam_repo / "requirements.md"
        req_file.write_text("# Implement Auth\n", encoding="utf-8")
        mission_id = run_mission_plan(str(req_file), console=console)

        run_dir = get_niyam_dir(niyam_repo) / "runs" / mission_id
        plan = load_plan(run_dir)
        plan["tasks"][0]["acceptance_criteria"] = [
            "The discovery task records current implementation boundaries."
        ]
        from niyam.mission.executor import save_plan

        save_plan(run_dir, plan)
        run_mission_approve(console=console)

        # Run start with test mock environment
        os.environ["NIYAM_TEST"] = "1"
        try:
            run_mission_start(console=console)
        finally:
            del os.environ["NIYAM_TEST"]

        plan = load_plan(run_dir)
        assert plan["mission"]["status"] == "completed"

        # Check all tasks are completed
        for task in plan["tasks"]:
            assert task["status"] == "completed"

        # Check mission events
        events_path = run_dir / "events.jsonl"
        assert events_path.exists()
        events = []
        with open(events_path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    events.append(json.loads(line))
        
        assert len(events) > 0
        # First event should be mission transition to running
        assert events[0]["event"] == "MISSION_STATE_TRANSITION"
        assert events[0]["to_status"] == "running"
        # Last event should be mission transition to completed
        assert events[-1]["event"] == "MISSION_STATE_TRANSITION"
        assert events[-1]["to_status"] == "completed"

        acceptance_path = run_dir / "acceptance-checks.json"
        assert acceptance_path.exists()
        with open(acceptance_path, encoding="utf-8") as f:
            acceptance = json.load(f)
        assert acceptance[0]["criterion_id"] == "T1-AC1"
        assert acceptance[0]["status"] == "requires_review"

        # Check status command runs
        run_mission_status(console=console)

        # Generate report
        run_mission_report(console=console)
        assert (run_dir / "evidence.md").exists()
        report_content = (run_dir / "evidence.md").read_text(encoding="utf-8")
        assert "Niyam Mission Evidence Package" in report_content
        assert "Mission Timeline" in report_content
        assert "Task Checklist" in report_content
        assert "Acceptance Criteria Evidence" in report_content

    def test_mission_pause_resume(self, niyam_repo: Path) -> None:
        """Should support pause and resume mid-execution."""
        os.chdir(niyam_repo)
        console = Console(quiet=True)

        req_file = niyam_repo / "requirements.md"
        req_file.write_text("# Implement Auth\n", encoding="utf-8")
        mission_id = run_mission_plan(str(req_file), console=console)
        run_mission_approve(console=console)

        # Manually set running status
        run_dir = get_niyam_dir(niyam_repo) / "runs" / mission_id
        plan = load_plan(run_dir)
        plan["mission"]["status"] = "running"
        from niyam.mission.executor import save_plan

        save_plan(run_dir, plan)

        # Pause
        run_mission_pause(console=console)
        plan = load_plan(run_dir)
        assert plan["mission"]["status"] == "paused"

        # Resume with mock environment
        os.environ["NIYAM_TEST"] = "1"
        try:
            run_mission_resume(console=console)
        finally:
            del os.environ["NIYAM_TEST"]

        plan = load_plan(run_dir)
        assert plan["mission"]["status"] == "completed"

    def test_mission_plan_strict(self, niyam_repo: Path) -> None:
        """Should raise SystemExit when strict=True and AI planner is not available."""
        os.chdir(niyam_repo)
        console = Console(quiet=True)

        req_file = niyam_repo / "requirements.md"
        req_file.write_text("# Strict planning test\n", encoding="utf-8")

        with pytest.raises(SystemExit) as excinfo:
            run_mission_plan(str(req_file), strict=True, console=console)
        assert excinfo.value.code == 1

    def test_resolve_mission_prefers_active_over_completed(
        self, niyam_repo: Path
    ) -> None:
        """Mission resolution should avoid surprising completed-history selection."""
        os.chdir(niyam_repo)
        console = Console(quiet=True)

        completed_req = niyam_repo / "completed.md"
        completed_req.write_text("# Completed\n", encoding="utf-8")
        completed_id = run_mission_plan(str(completed_req), console=console)
        completed_dir = get_niyam_dir(niyam_repo) / "runs" / completed_id
        completed_plan = load_plan(completed_dir)
        completed_plan["mission"]["status"] = "completed"

        from niyam.mission.executor import save_plan

        save_plan(completed_dir, completed_plan)

        active_req = niyam_repo / "active.md"
        active_req.write_text("# Active\n", encoding="utf-8")
        active_id = run_mission_plan(str(active_req), console=console)

        assert resolve_mission_id(get_niyam_dir(niyam_repo)) == active_id
        assert (
            resolve_mission_id(get_niyam_dir(niyam_repo), completed_id) == completed_id
        )
