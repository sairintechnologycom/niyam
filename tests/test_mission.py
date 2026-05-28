"""Tests for Sutra mission mode."""

from __future__ import annotations

import os
import json
from pathlib import Path
import pytest
import yaml
from rich.console import Console

from sutra.core.config import get_sutra_dir
from sutra.mission.planner import run_mission_plan, run_mission_approve, get_latest_mission_id
from sutra.mission.executor import run_mission_start, run_mission_pause, run_mission_resume, load_plan
from sutra.mission.status import run_mission_status
from sutra.mission.reporter import run_mission_report


class TestMission:
    """Tests for mission mode lifecycle."""

    def test_mission_plan_creates_files(self, sutra_repo: Path) -> None:
        """Should create runs dir, copy req file, and generate YAML templates."""
        os.chdir(sutra_repo)
        console = Console(quiet=True)

        # Create requirements file
        req_file = sutra_repo / "requirements.md"
        req_file.write_text("# Implement Authentication\n\nRequire login validation.", encoding="utf-8")

        mission_id = run_mission_plan(str(req_file), console=console)
        assert mission_id is not None

        sutra_dir = get_sutra_dir(sutra_repo)
        run_dir = sutra_dir / "runs" / mission_id
        assert run_dir.is_dir()

        # Check copied requirement
        assert (run_dir / "requirement.md").exists()
        assert (run_dir / "requirement.md").read_text(encoding="utf-8") == req_file.read_text(encoding="utf-8")

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

    def test_mission_approve(self, sutra_repo: Path) -> None:
        """Should update approval.json and plan status."""
        os.chdir(sutra_repo)
        console = Console(quiet=True)

        req_file = sutra_repo / "requirements.md"
        req_file.write_text("# Implement Auth\n", encoding="utf-8")
        mission_id = run_mission_plan(str(req_file), console=console)

        # Approve it
        run_mission_approve(console=console)

        run_dir = get_sutra_dir(sutra_repo) / "runs" / mission_id
        with open(run_dir / "approval.json", encoding="utf-8") as f:
            app_data = json.load(f)
        assert app_data["approved"]

        plan = load_plan(run_dir)
        assert plan["mission"]["status"] == "approved"

    def test_mission_execution_lifecycle(self, sutra_repo: Path) -> None:
        """Should sequentially run tasks, log events, and generate report."""
        os.chdir(sutra_repo)
        console = Console(quiet=True)

        req_file = sutra_repo / "requirements.md"
        req_file.write_text("# Implement Auth\n", encoding="utf-8")
        mission_id = run_mission_plan(str(req_file), console=console)
        run_mission_approve(console=console)

        # Run start with test mock environment
        os.environ["SUTRA_TEST"] = "1"
        try:
            run_mission_start(console=console)
        finally:
            del os.environ["SUTRA_TEST"]

        run_dir = get_sutra_dir(sutra_repo) / "runs" / mission_id
        plan = load_plan(run_dir)
        assert plan["mission"]["status"] == "completed"

        # Check all tasks are completed
        for task in plan["tasks"]:
            assert task["status"] == "completed"

        # Check execution log
        exec_log_path = run_dir / "execution-log.json"
        assert exec_log_path.exists()
        with open(exec_log_path, encoding="utf-8") as f:
            logs = json.load(f)
        assert len(logs) > 0
        assert logs[0]["event"] == "MISSION_STARTED"
        assert logs[-1]["event"] == "MISSION_COMPLETED"

        # Check status command runs
        run_mission_status(console=console)

        # Generate report
        run_mission_report(console=console)
        assert (run_dir / "evidence.md").exists()
        report_content = (run_dir / "evidence.md").read_text(encoding="utf-8")
        assert "Sutra Mission Evidence Package" in report_content
        assert "Execution Log" in report_content
        assert "Task Checklist" in report_content

    def test_mission_pause_resume(self, sutra_repo: Path) -> None:
        """Should support pause and resume mid-execution."""
        os.chdir(sutra_repo)
        console = Console(quiet=True)

        req_file = sutra_repo / "requirements.md"
        req_file.write_text("# Implement Auth\n", encoding="utf-8")
        mission_id = run_mission_plan(str(req_file), console=console)
        run_mission_approve(console=console)

        # Manually set running status
        run_dir = get_sutra_dir(sutra_repo) / "runs" / mission_id
        plan = load_plan(run_dir)
        plan["mission"]["status"] = "running"
        from sutra.mission.executor import save_plan
        save_plan(run_dir, plan)

        # Pause
        run_mission_pause(console=console)
        plan = load_plan(run_dir)
        assert plan["mission"]["status"] == "paused"

        # Resume with mock environment
        os.environ["SUTRA_TEST"] = "1"
        try:
            run_mission_resume(console=console)
        finally:
            del os.environ["SUTRA_TEST"]

        plan = load_plan(run_dir)
        assert plan["mission"]["status"] == "completed"

    def test_mission_plan_strict(self, sutra_repo: Path) -> None:
        """Should raise SystemExit when strict=True and AI planner is not available."""
        os.chdir(sutra_repo)
        console = Console(quiet=True)

        req_file = sutra_repo / "requirements.md"
        req_file.write_text("# Strict planning test\n", encoding="utf-8")

        with pytest.raises(SystemExit) as excinfo:
            run_mission_plan(str(req_file), strict=True, console=console)
        assert excinfo.value.code == 1
