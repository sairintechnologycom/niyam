"""Tests for Niyam Portal API."""

from __future__ import annotations

from pathlib import Path
from fastapi.testclient import TestClient

from niyam.api.server import app
from niyam.mission.utils import save_plan

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "niyam-portal"}


def test_list_missions_empty(niyam_repo: Path):
    """Should return empty list if no missions exist."""
    from unittest.mock import patch
    with patch("niyam.api.server.find_niyam_root", return_value=niyam_repo), \
         patch("niyam.core.config.find_niyam_root", return_value=niyam_repo):
        response = client.get("/missions")
        assert response.status_code == 200
        assert response.json() == []


def test_mission_endpoints(niyam_repo: Path):
    """Should list and retrieve mission details."""
    from unittest.mock import patch
    niyam_dir = niyam_repo / ".niyam"
    mission_id = "test-mission-api"
    run_dir = niyam_dir / "runs" / mission_id
    run_dir.mkdir(parents=True, exist_ok=True)

    plan = {
        "mission": {
            "id": mission_id,
            "status": "completed",
            "orchestrator": "claude",
            "created": "2026-06-06T12:00:00Z",
            "parallel": 1,
            "worktree": False,
            "requirement": "dummy",
        },
        "tasks": [
            {
                "id": "T1",
                "title": "Task 1",
                "agent": "default",
                "status": "completed",
                "depends_on": [],
                "type": "implementation",
            }
        ],
    }
    save_plan(run_dir, plan)
    (run_dir / "evidence.md").write_text("# Evidence", encoding="utf-8")

    with patch("niyam.api.server.find_niyam_root", return_value=niyam_repo), \
         patch("niyam.core.config.find_niyam_root", return_value=niyam_repo):
        # Test List
        response = client.get("/missions")
        assert response.status_code == 200
        missions = response.json()
        assert len(missions) >= 1
        assert missions[0]["id"] == mission_id
        assert missions[0]["status"] == "completed"

        # Test Get Details
        response = client.get(f"/missions/{mission_id}")
        assert response.status_code == 200
        details = response.json()
        assert details["id"] == mission_id
        assert len(details["tasks"]) == 1
        assert details["tasks"][0]["id"] == "T1"

        # Test Evidence
        response = client.get(f"/missions/{mission_id}/evidence")
        assert response.status_code == 200
        assert response.json()["content"] == "# Evidence"


def test_mission_action(niyam_repo: Path):
    """Should transition mission status via action endpoint."""
    from unittest.mock import patch
    niyam_dir = niyam_repo / ".niyam"
    mission_id = "test-mission-action"
    run_dir = niyam_dir / "runs" / mission_id
    run_dir.mkdir(parents=True, exist_ok=True)

    plan = {
        "mission": {
            "id": mission_id,
            "status": "running",
            "orchestrator": "claude",
            "created": "2026-06-06T12:00:00Z",
            "parallel": 1,
            "worktree": False,
            "requirement": "dummy",
        },
        "tasks": [],
    }
    save_plan(run_dir, plan)

    with patch("niyam.api.server.find_niyam_root", return_value=niyam_repo), \
         patch("niyam.core.config.find_niyam_root", return_value=niyam_repo):
        response = client.post(f"/missions/{mission_id}/action?action=pause")
        assert response.status_code == 200
        assert response.json()["success"] is True
        assert response.json()["new_status"] == "paused"

        # Verify filesystem state
        from niyam.mission.utils import load_plan
        updated_plan = load_plan(run_dir)
        assert updated_plan["mission"]["status"] == "paused"


def test_policies_endpoint(niyam_repo: Path):
    """Should return the security, commands, approvals policies and guard config."""
    from unittest.mock import patch
    with patch("niyam.api.server.find_niyam_root", return_value=niyam_repo), \
         patch("niyam.core.config.find_niyam_root", return_value=niyam_repo):
        response = client.get("/policies")
        assert response.status_code == 200
        data = response.json()
        assert "security" in data
        assert "commands" in data
        assert "approvals" in data
        assert "guard_config" in data


def test_prompt_audits_endpoint(niyam_repo: Path):
    """Should return prompt audit logs from runs."""
    from unittest.mock import patch
    niyam_dir = niyam_repo / ".niyam"
    mission_id = "test-mission-audit-prompt"
    task_id = "T1"
    prompt_dir = niyam_dir / "runs" / mission_id / "tasks" / task_id
    prompt_dir.mkdir(parents=True, exist_ok=True)
    (prompt_dir / "prompt.md").write_text("Test prompt content", encoding="utf-8")

    with patch("niyam.api.server.find_niyam_root", return_value=niyam_repo), \
         patch("niyam.core.config.find_niyam_root", return_value=niyam_repo):
        response = client.get("/audits/prompts")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["mission_id"] == mission_id
        assert data[0]["task_id"] == task_id
        assert data[0]["content"] == "Test prompt content"


def test_approve_deny_task(niyam_repo: Path):
    """Should write approval.json for task approve and deny endpoints."""
    from unittest.mock import patch
    niyam_dir = niyam_repo / ".niyam"
    mission_id = "test-mission-task-gate"
    task_id = "T1"
    task_dir = niyam_dir / "runs" / mission_id / "tasks" / task_id
    task_dir.mkdir(parents=True, exist_ok=True)

    with patch("niyam.api.server.find_niyam_root", return_value=niyam_repo), \
         patch("niyam.core.config.find_niyam_root", return_value=niyam_repo):
        # Approve task
        response = client.post(f"/missions/{mission_id}/tasks/{task_id}/approve")
        assert response.status_code == 200
        assert response.json()["success"] is True
        assert (task_dir / "approval.json").exists()
        
        # Deny task
        response = client.post(f"/missions/{mission_id}/tasks/{task_id}/deny")
        assert response.status_code == 200
        assert response.json()["success"] is True
        
        # Check file content
        import json
        with open(task_dir / "approval.json", encoding="utf-8") as f:
            approval_data = json.load(f)
        assert approval_data["approved"] is False
        assert approval_data["reason"] == "Denied via portal"


def test_approve_mission_via_api(niyam_repo: Path):
    """Should approve planned mission with specific roles."""
    from unittest.mock import patch
    niyam_dir = niyam_repo / ".niyam"
    mission_id = "test-mission-approve-api"
    run_dir = niyam_dir / "runs" / mission_id
    run_dir.mkdir(parents=True, exist_ok=True)

    plan = {
        "mission": {
            "id": mission_id,
            "status": "planned",
            "orchestrator": "claude",
            "created": "2026-06-06T12:00:00Z",
            "parallel": 1,
            "worktree": False,
            "requirement": "dummy",
        },
        "tasks": [],
    }
    save_plan(run_dir, plan)

    with patch("niyam.api.server.find_niyam_root", return_value=niyam_repo), \
         patch("niyam.core.config.find_niyam_root", return_value=niyam_repo):
        response = client.post(f"/missions/{mission_id}/approve?role=default")
        assert response.status_code == 200
        assert response.json()["success"] is True
        assert response.json()["new_status"] == "approved"

        # Verify plan status is updated
        from niyam.mission.utils import load_plan
        updated_plan = load_plan(run_dir)
        assert updated_plan["mission"]["status"] == "approved"
