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


def test_pr_create_mocked(niyam_repo: Path) -> None:
    """Should push branch, read/generate evidence report, and create PR."""
    os.chdir(niyam_repo)
    console = Console(quiet=True)

    # Mock git commands and PR creation api call
    with (
        patch("subprocess.run") as mock_run,
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
        (run_dir / "evidence.md").write_text("# Test Evidence\n", encoding="utf-8")

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
        assert "Adds login validations." in args[3]
        assert "# Test Evidence" in args[3]
