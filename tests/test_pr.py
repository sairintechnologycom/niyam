"""Tests for Niyam GitHub PR Integration."""

from __future__ import annotations

import os
from pathlib import Path
from rich.console import Console
from unittest.mock import patch, MagicMock

from niyam.core.pr import run_pr_review, run_pr_create


def test_pr_review_mocked(niyam_repo: Path) -> None:
    """Should fetch PR diff, mock execution, and post comment."""
    os.chdir(niyam_repo)
    console = Console(quiet=True)

    # Mock get_pr_diff and post_pr_comment
    with (
        patch(
            "niyam.core.pr.get_pr_diff", return_value="+++ added line"
        ) as mock_get_diff,
        patch("niyam.core.pr.post_pr_comment") as mock_post_comment,
        patch(
            "niyam.core.pr.get_github_repo_owner_name", return_value=("owner", "repo")
        ),
    ):
        os.environ["NIYAM_TEST"] = "1"
        try:
            run_pr_review(
                pr_id="42",
                lens="engineering",
                runtime="claude",
                mode="collaborative",
                token="dummy_token",
                console=console,
            )
        finally:
            del os.environ["NIYAM_TEST"]

        mock_get_diff.assert_called_once_with("42", "dummy_token", niyam_repo)
        mock_post_comment.assert_called_once_with(
            "42",
            "Mocked structured code review for PR #42 using engineering lens.",
            "dummy_token",
            niyam_repo,
        )


def test_pr_review_evidence_lens(niyam_repo: Path) -> None:
    """Should fetch evidence.md and perform review with evidence lens."""
    os.chdir(niyam_repo)
    console = Console(quiet=True)

    # Mock get_github_repo_owner_name
    with (
        patch("niyam.core.pr.post_pr_comment") as mock_post_comment,
        patch("niyam.core.pr.get_github_repo_owner_name", return_value=("owner", "repo")),
        patch("niyam.mission.planner.resolve_mission_id", return_value="test-mission-123"),
    ):
        # Write dummy evidence report
        niyam_dir = niyam_repo / ".niyam"
        run_dir = niyam_dir / "runs" / "test-mission-123"
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "evidence.md").write_text("# Mission Evidence\nALL_TESTS_PASSED", encoding="utf-8")

        os.environ["NIYAM_TEST"] = "1"
        try:
            run_pr_review(
                pr_id="42",
                lens="evidence",
                runtime="claude",
                mode="collaborative",
                token="dummy_token",
                console=console,
            )
        finally:
            del os.environ["NIYAM_TEST"]

        # Check if it was called with the right mocked output
        mock_post_comment.assert_called_once_with(
            "42",
            "Mocked structured code review for PR #42 using evidence lens.",
            "dummy_token",
            niyam_repo,
        )
        
        # Verify prompt file exists and contains evidence
        prompt_file = niyam_dir / "runs" / "review-pr-42-evidence-collaborative-prompt.md"
        assert prompt_file.exists()
        prompt_content = prompt_file.read_text(encoding="utf-8")
        assert "# Mission Evidence" in prompt_content
        assert "ALL_TESTS_PASSED" in prompt_content


def test_pr_review_evidence_from_body(niyam_repo: Path) -> None:
    """Should extract evidence from PR body if local evidence is missing."""
    os.chdir(niyam_repo)
    console = Console(quiet=True)

    pr_body = (
        "This is a PR.\n"
        "<details>\n"
        "<summary>Evidence</summary>\n\n"
        "# Embedded Evidence\nFROM_PR_BODY\n"
        "</details>"
    )

    # Mock get_github_repo_owner_name and get_pr_body
    with (
        patch("niyam.core.pr.post_pr_comment") as mock_post_comment,
        patch("niyam.core.pr.get_github_repo_owner_name", return_value=("owner", "repo")),
        patch("niyam.core.pr.get_pr_body", return_value=pr_body),
        patch("niyam.mission.planner.resolve_mission_id", return_value=None), # Force PR body path
    ):
        os.environ["NIYAM_TEST"] = "1"
        try:
            run_pr_review(
                pr_id="42",
                lens="evidence",
                runtime="claude",
                mode="collaborative",
                token="dummy_token",
                console=console,
            )
        finally:
            del os.environ["NIYAM_TEST"]

        # Verify prompt file exists and contains evidence from body
        niyam_dir = niyam_repo / ".niyam"
        prompt_file = niyam_dir / "runs" / "review-pr-42-evidence-collaborative-prompt.md"
        assert prompt_file.exists()
        prompt_content = prompt_file.read_text(encoding="utf-8")
        assert "# Embedded Evidence" in prompt_content
        assert "FROM_PR_BODY" in prompt_content


def test_pr_create_mocked(niyam_repo: Path) -> None:
    """Should push branch, read/generate evidence report, and create PR."""
    os.chdir(niyam_repo)
    console = Console(quiet=True)

    # Mock git commands and PR creation api call
    with (
        patch("subprocess.run") as mock_run,
        patch("shutil.which", return_value=None),
        patch(
            "niyam.core.pr.create_pr_api",
            return_value="https://github.com/owner/repo/pull/42",
        ) as mock_create_pr,
        patch(
            "niyam.core.pr.get_github_repo_owner_name", return_value=("owner", "repo")
        ),
    ):
        # Setup git branch name mock response and git push success
        def mock_subprocess_run(args, **kwargs):
            res = MagicMock()
            res.returncode = 0
            if "rev-parse" in args:
                res.stdout = "feature-branch\n"
            else:
                res.stdout = ""
            return res

        mock_run.side_effect = mock_subprocess_run

        # Write dummy mission run and evidence report
        niyam_dir = niyam_repo / ".niyam"
        run_dir = niyam_dir / "runs" / "test-mission-123"
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "evidence.md").write_text("# Test Evidence\n## Cryptographic Integrity Manifest\nSIG_BLOCK", encoding="utf-8")
        import json
        (run_dir / "evidence.json").write_text(json.dumps({
            "status": "completed",
            "orchestrator": "claude",
            "tasks": [{"id": "T1", "status": "completed"}]
        }), encoding="utf-8")

        # Set latest mission
        (niyam_dir / "runs" / "test-mission-123").touch()

        run_pr_create(
            title="Implement Auth Feature",
            body="Adds login validations.",
            base="main",
            token="dummy_token",
            console=console,
        )

        mock_create_pr.assert_called_once()
        args, kwargs = mock_create_pr.call_args
        assert args[0] == "owner"
        assert args[1] == "repo"
        assert args[2] == "Implement Auth Feature"
        body_content = args[3]
        assert "Adds login validations." in body_content
        assert "## Niyam Mission Summary" in body_content
        assert "COMPLETED" in body_content
        assert "## Cryptographic Integrity Manifest" in body_content
        assert "<details>" in body_content
        assert "# Test Evidence" in body_content
