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
        assert plan["mission"].get("schema_version") == "1.0"
        assert len(plan["tasks"]) == 5

        # Check task schema additions
        task_0 = plan["tasks"][0]
        assert task_0.get("version") == "1.0"
        assert "evidence_refs" in task_0
        assert task_0.get("retry_policy") == "auto"

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

    def test_mission_metrics_command(self, niyam_repo: Path) -> None:
        """Should output mission metrics using the CLI command."""
        os.chdir(niyam_repo)
        console = Console(quiet=True)

        req_file = niyam_repo / "requirements.md"
        req_file.write_text("# Implement Auth\n", encoding="utf-8")
        mission_id = run_mission_plan(str(req_file), console=console)
        run_mission_approve(console=console)
        
        # Mock environment to run mission
        os.environ["NIYAM_TEST"] = "1"
        try:
            run_mission_start(console=console)
        finally:
            del os.environ["NIYAM_TEST"]
            
        from typer.testing import CliRunner
        from niyam.cli.mission import mission_app
        
        runner = CliRunner()
        # Test global metrics
        result = runner.invoke(mission_app, ["metrics"])
        assert result.exit_code == 0
        assert "Global Agent Performance Ranking" in result.stdout
        assert "Tokens" in result.stdout
        assert "Total Cost" in result.stdout

        # Test specific mission metrics
        result_specific = runner.invoke(mission_app, ["metrics", "--mission", mission_id])
        assert result_specific.exit_code == 0
        assert "Mission Metrics:" in result_specific.stdout
        assert mission_id in result_specific.stdout
        assert "Tokens" in result_specific.stdout
        assert "Total Cost" in result_specific.stdout

    def test_mission_explain_command(self, niyam_repo: Path) -> None:
        """Explain should show execution layers and task policy details."""
        os.chdir(niyam_repo)
        console = Console(quiet=True)

        req_file = niyam_repo / "requirements.md"
        req_file.write_text("# Explain Mission\n", encoding="utf-8")
        mission_id = run_mission_plan(str(req_file), console=console)

        from typer.testing import CliRunner
        from niyam.cli import app

        runner = CliRunner()
        result = runner.invoke(app, ["mission", "explain", "--mission", mission_id])

        assert result.exit_code == 0
        assert "Execution Preview" in result.stdout
        assert "Swarm locks" in result.stdout

    def test_mission_audit_command(self, niyam_repo: Path) -> None:
        """Should output or export mission audit log using the CLI command."""
        os.chdir(niyam_repo)
        console = Console(quiet=True)

        req_file = niyam_repo / "requirements.md"
        req_file.write_text("# Implement Auth\n", encoding="utf-8")
        mission_id = run_mission_plan(str(req_file), console=console)
        run_mission_approve(console=console)
        
        # Mock environment to run mission
        os.environ["NIYAM_TEST"] = "1"
        try:
            run_mission_start(console=console)
        finally:
            del os.environ["NIYAM_TEST"]
            
        from typer.testing import CliRunner
        from niyam.cli.mission import mission_app
        
        runner = CliRunner()
        
        # Test audit command to stdout
        result = runner.invoke(mission_app, ["audit", "--mission", mission_id])
        assert result.exit_code == 0
        assert f"Prompt Traceability Audit: Mission {mission_id}" in result.stdout
        assert "Executed Prompt" in result.stdout
        
        # Test audit command to file
        output_file = str(niyam_repo / "audit.md")
        result_export = runner.invoke(mission_app, ["audit", "--mission", mission_id, "--output", output_file])
        assert result_export.exit_code == 0
        assert os.path.exists(output_file)
        
        content = Path(output_file).read_text(encoding="utf-8")
        assert f"# Prompt Traceability Audit: Mission {mission_id}" in content
        assert "### Executed Prompt" in content

    def test_budget_enforcer(self, niyam_repo: Path) -> None:
        """Should fail the mission if budget is breached."""
        os.chdir(niyam_repo)
        console = Console(quiet=True)
        
        # Setup budget config
        from niyam.core.config import load_niyam_config, save_niyam_config, GovernanceConfig, BudgetConfig
        config = load_niyam_config(niyam_repo)
        if not config.governance:
            config.governance = GovernanceConfig()
        if not config.governance.budget:
            config.governance.budget = BudgetConfig()
            
        config.governance.budget.max_mission_cost_usd = -1.0  # Force breach immediately
        save_niyam_config(config, niyam_repo)
        
        # Plan and approve
        req_file = niyam_repo / "requirements.md"
        req_file.write_text("# Implement Auth\n", encoding="utf-8")
        mission_id = run_mission_plan(str(req_file), console=console)
        run_mission_approve(console=console)
        
        # Mock environment to run mission
        os.environ["NIYAM_TEST"] = "1"
        try:
            with pytest.raises(SystemExit) as excinfo:
                run_mission_start(console=console)
            # The executor will SystemExit(1) due to mission failure (budget breach)
            assert excinfo.value.code == 1
        finally:
            del os.environ["NIYAM_TEST"]
            
        # Verify it was failed for the correct reason
        run_dir = get_niyam_dir(niyam_repo) / "runs" / mission_id
        plan = load_plan(run_dir)
        assert plan["mission"]["status"] == "failed"
        
        # Read the event logs
        events_path = run_dir / "events.jsonl"
        events = []
        with open(events_path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    events.append(json.loads(line))
                    
        # Check that the mission failed because of the budget
        failure_events = [e for e in events if e.get("event") == "MISSION_STATE_TRANSITION" and e.get("to_status") == "failed"]
        assert len(failure_events) > 0
        assert "Mission budget breached" in failure_events[0].get("reason", "")

    def test_mission_multi_role_approval(self, niyam_repo: Path) -> None:
        """Should require approvals from all configured roles before transitioning mission status to approved."""
        os.chdir(niyam_repo)
        console = Console(quiet=True)

        # 1. Update config to require multiple approval roles
        from niyam.core.config import load_niyam_config, save_niyam_config, GovernanceConfig, GuardConfig
        config = load_niyam_config(niyam_repo)
        if not config.governance:
            config.governance = GovernanceConfig()
        if not config.governance.guard:
            config.governance.guard = GuardConfig()
        config.governance.guard.mission_approval_roles = ["tech_lead", "security"]
        save_niyam_config(config, niyam_repo)


        # 2. Plan a new mission
        req_file = niyam_repo / "requirements.md"
        req_file.write_text("# Implement Multi-Role Auth\n", encoding="utf-8")
        mission_id = run_mission_plan(str(req_file), console=console)

        run_dir = get_niyam_dir(niyam_repo) / "runs" / mission_id

        # 3. Check status is planned and approval is not approved
        plan = load_plan(run_dir)
        assert plan["mission"]["status"] == "planned"

        # 4. Approve as 'tech_lead'
        run_mission_approve(console=console, role="tech_lead")

        # Status should still be planned since 'security' has not approved
        plan = load_plan(run_dir)
        assert plan["mission"]["status"] == "planned"

        # Check approval.json details
        with open(run_dir / "approval.json", encoding="utf-8") as f:
            app_data = json.load(f)
        assert not app_data["approved"]
        assert "tech_lead" in app_data["approvals"]
        assert "security" not in app_data["approvals"]

        # 5. Approve as 'security'
        run_mission_approve(console=console, role="security")

        # Status should now transition to approved
        plan = load_plan(run_dir)
        assert plan["mission"]["status"] == "approved"

        with open(run_dir / "approval.json", encoding="utf-8") as f:
            app_data = json.load(f)
        assert app_data["approved"]
        assert "tech_lead" in app_data["approvals"]
        assert "security" in app_data["approvals"]

    def test_budget_enforcer_token_limit(self, niyam_repo: Path) -> None:
        """Should fail the mission if token budget is breached."""
        os.chdir(niyam_repo)
        console = Console(quiet=True)

        # Setup budget config
        from niyam.core.config import load_niyam_config, save_niyam_config, GovernanceConfig, BudgetConfig
        config = load_niyam_config(niyam_repo)
        if not config.governance:
            config.governance = GovernanceConfig()
        if not config.governance.budget:
            config.governance.budget = BudgetConfig()

        config.governance.budget.max_mission_tokens = -1  # Force breach immediately
        save_niyam_config(config, niyam_repo)

        # Plan and approve
        req_file = niyam_repo / "requirements.md"
        req_file.write_text("# Implement Auth\n", encoding="utf-8")
        mission_id = run_mission_plan(str(req_file), console=console)
        run_mission_approve(console=console)

        # Mock environment to run mission
        os.environ["NIYAM_TEST"] = "1"
        try:
            with pytest.raises(SystemExit) as excinfo:
                run_mission_start(console=console)
            assert excinfo.value.code == 1
        finally:
            del os.environ["NIYAM_TEST"]

        run_dir = get_niyam_dir(niyam_repo) / "runs" / mission_id
        plan = load_plan(run_dir)
        assert plan["mission"]["status"] == "failed"

        # Read the event logs
        events_path = run_dir / "events.jsonl"
        events = []
        with open(events_path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    events.append(json.loads(line))

        # Check that the mission failed because of the token budget
        failure_events = [e for e in events if e.get("event") == "MISSION_STATE_TRANSITION" and e.get("to_status") == "failed"]
        assert len(failure_events) > 0
        assert "Mission token budget breached" in failure_events[0].get("reason", "")

    def test_task_budget_enforcer(self, niyam_repo: Path) -> None:
        """Should fail the task and mission if task budget (cost or tokens) is breached."""
        os.chdir(niyam_repo)
        console = Console(quiet=True)

        # Setup budget config
        from niyam.core.config import load_niyam_config, save_niyam_config, GovernanceConfig, BudgetConfig
        config = load_niyam_config(niyam_repo)
        if not config.governance:
            config.governance = GovernanceConfig()
        if not config.governance.budget:
            config.governance.budget = BudgetConfig()

        config.governance.budget.max_task_cost_usd = -1.0  # Force breach immediately
        save_niyam_config(config, niyam_repo)

        # Plan and approve
        req_file = niyam_repo / "requirements.md"
        req_file.write_text("# Implement Auth\n", encoding="utf-8")
        mission_id = run_mission_plan(str(req_file), console=console)
        run_mission_approve(console=console)

        # Mock environment to run mission
        os.environ["NIYAM_TEST"] = "1"
        try:
            with pytest.raises(SystemExit) as excinfo:
                run_mission_start(console=console)
            assert excinfo.value.code == 1
        finally:
            del os.environ["NIYAM_TEST"]

        run_dir = get_niyam_dir(niyam_repo) / "runs" / mission_id
        plan = load_plan(run_dir)
        # Check first task is failed
        assert plan["tasks"][0]["status"] == "failed"

        # Read the event logs
        events_path = run_dir / "events.jsonl"
        events = []
        with open(events_path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    events.append(json.loads(line))

        # Check for BUDGET_VIOLATION event
        violation_events = [e for e in events if e.get("event") == "BUDGET_VIOLATION"]
        assert len(violation_events) > 0
        assert violation_events[0]["type"] == "TASK_COST_BREACH"

    def test_saas_telemetry_integration(self, niyam_repo: Path) -> None:
        """Should trigger SaaS webhooks on transitions when SaaS is enabled."""
        os.chdir(niyam_repo)
        console = Console(quiet=True)

        # Enable SaaS integration in config
        from niyam.core.config import load_niyam_config, save_niyam_config
        config = load_niyam_config(niyam_repo)
        config.saas.enabled = True
        config.saas.api_key = "test-api-key"
        config.saas.project_id = "test-project-id"
        save_niyam_config(config, niyam_repo)

        from unittest.mock import patch

        with patch("niyam.core.saas.SaaSClient.trigger_webhook") as mock_webhook:
            # Plan and approve
            req_file = niyam_repo / "requirements.md"
            req_file.write_text("# Test Telemetry\n", encoding="utf-8")
            run_mission_plan(str(req_file), console=console)
            run_mission_approve(console=console)

            # Mock environment to run mission
            os.environ["NIYAM_TEST"] = "1"
            try:
                run_mission_start(console=console)
            finally:
                del os.environ["NIYAM_TEST"]

            # Verify that trigger_webhook was called
            assert mock_webhook.called
            
            # The calls should include MISSION_STATE_TRANSITION and TASK_STATE_TRANSITION
            called_types = {call.args[0] for call in mock_webhook.call_args_list}
            assert "MISSION_STATE_TRANSITION" in called_types
            assert "TASK_STATE_TRANSITION" in called_types
