"""Tests for Niyam Portal API."""

from __future__ import annotations

import json
from pathlib import Path
from fastapi.testclient import TestClient
import pytest

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
    with patch("niyam.api.server.find_niyam_root", return_value=niyam_repo):
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

    with patch("niyam.api.server.find_niyam_root", return_value=niyam_repo):
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

    with patch("niyam.api.server.find_niyam_root", return_value=niyam_repo):
        response = client.post(f"/missions/{mission_id}/action?action=pause")
        assert response.status_code == 200
        assert response.json()["success"] is True
        assert response.json()["new_status"] == "paused"

        # Verify filesystem state
        from niyam.mission.utils import load_plan
        updated_plan = load_plan(run_dir)
        assert updated_plan["mission"]["status"] == "paused"
