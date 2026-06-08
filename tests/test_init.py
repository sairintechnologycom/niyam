"""Tests for niyam init command."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
import yaml
from rich.console import Console


class TestInit:
    """Tests for the init command."""

    def test_init_creates_niyam_directory(self, tmp_repo: Path) -> None:
        """niyam init should create .niyam/ directory."""
        from niyam.core.init import run_init

        console = Console(quiet=True)
        os.chdir(tmp_repo)
        run_init(
            profile="fullstack",
            runtime=None,
            dry_run=False,
            force=False,
            console=console,
        )

        assert (tmp_repo / ".niyam").is_dir()
        assert not (tmp_repo / ".sutra").exists()

        # Check governance documents in root
        expected_docs = [
            "01-niyam-governance-prd.md",
            "02-niyam-technical-architecture.md",
            "03-niyam-security-access-governance.md",
            "04-niyam-dashboard-frontend-spec.md",
            "05-niyam-feature-ticket-list.md",
            "06-niyam-backward-compatibility-and-migration-plan.md",
        ]
        for doc in expected_docs:
            assert (tmp_repo / doc).is_file()

    def test_init_creates_mvp_directories(self, tmp_repo: Path) -> None:
        """niyam init should create required MVP subdirectories."""
        from niyam.core.init import run_init

        console = Console(quiet=True)
        os.chdir(tmp_repo)
        run_init(
            profile="fullstack",
            runtime=None,
            dry_run=False,
            force=False,
            console=console,
        )

        for subdir in ["tasks", "runs", "templates", "worktrees", "evidence"]:
            assert (tmp_repo / ".niyam" / subdir).is_dir()

    def test_init_creates_niyam_yaml(self, tmp_repo: Path) -> None:
        """niyam init should create valid niyam.yaml."""
        from niyam.core.init import run_init

        console = Console(quiet=True)
        os.chdir(tmp_repo)
        run_init(
            profile="fullstack",
            runtime=None,
            dry_run=False,
            force=False,
            console=console,
        )

        niyam_yaml = tmp_repo / ".niyam" / "niyam.yaml"
        assert niyam_yaml.exists()

        with open(niyam_yaml) as f:
            data = yaml.safe_load(f)

        assert data["version"] == "0.1.0"
        assert data["profile"] == "fullstack"
        assert data["project_name"] == tmp_repo.name

    def test_init_creates_agents(self, tmp_repo: Path) -> None:
        """niyam init should create agent files."""
        from niyam.core.init import run_init

        console = Console(quiet=True)
        os.chdir(tmp_repo)
        run_init(
            profile="fullstack",
            runtime=None,
            dry_run=False,
            force=False,
            console=console,
        )

        agents_dir = tmp_repo / ".niyam" / "agents"
        assert agents_dir.is_dir()
        agent_files = list(agents_dir.glob("*.md"))
        assert len(agent_files) >= 4

    def test_init_creates_skills(self, tmp_repo: Path) -> None:
        """niyam init should create skill directories."""
        from niyam.core.init import run_init

        console = Console(quiet=True)
        os.chdir(tmp_repo)
        run_init(
            profile="fullstack",
            runtime=None,
            dry_run=False,
            force=False,
            console=console,
        )

        skills_dir = tmp_repo / ".niyam" / "skills"
        assert skills_dir.is_dir()
        skill_dirs = [d for d in skills_dir.iterdir() if d.is_dir()]
        assert len(skill_dirs) >= 4

    def test_init_creates_commands(self, tmp_repo: Path) -> None:
        """niyam init should create command files."""
        from niyam.core.init import run_init

        console = Console(quiet=True)
        os.chdir(tmp_repo)
        run_init(
            profile="fullstack",
            runtime=None,
            dry_run=False,
            force=False,
            console=console,
        )

        commands_dir = tmp_repo / ".niyam" / "commands"
        assert commands_dir.is_dir()
        command_files = list(commands_dir.glob("*.md"))
        assert len(command_files) >= 4

    def test_init_creates_policies(self, tmp_repo: Path) -> None:
        """niyam init should create policy files."""
        from niyam.core.init import run_init

        console = Console(quiet=True)
        os.chdir(tmp_repo)
        run_init(
            profile="fullstack",
            runtime=None,
            dry_run=False,
            force=False,
            console=console,
        )

        policies_dir = tmp_repo / ".niyam" / "policies"
        assert policies_dir.is_dir()
        policy_files = list(policies_dir.glob("*.yaml"))
        assert len(policy_files) >= 4

    def test_init_is_idempotent_if_already_exists(self, niyam_repo: Path) -> None:
        """niyam init should no-op if .niyam/ already exists."""
        from niyam.core.init import run_init

        console = Console(quiet=True)
        os.chdir(niyam_repo)
        marker = niyam_repo / ".niyam" / "marker.txt"
        marker.write_text("keep me", encoding="utf-8")

        run_init(
            profile="fullstack",
            runtime=None,
            dry_run=False,
            force=False,
            console=console,
        )

        assert marker.read_text(encoding="utf-8") == "keep me"

    def test_init_force_overwrites(self, niyam_repo: Path) -> None:
        """niyam init --force should overwrite existing .niyam/."""
        from niyam.core.init import run_init

        console = Console(quiet=True)
        os.chdir(niyam_repo)

        # Should not raise
        run_init(
            profile="fullstack",
            runtime=None,
            dry_run=False,
            force=True,
            console=console,
        )

        assert (niyam_repo / ".niyam" / "niyam.yaml").exists()

    def test_init_dry_run_creates_nothing(self, tmp_repo: Path) -> None:
        """niyam init --dry-run should not create any files."""
        from niyam.core.init import run_init

        console = Console(quiet=True)
        os.chdir(tmp_repo)
        run_init(
            profile="fullstack",
            runtime=None,
            dry_run=True,
            force=False,
            console=console,
        )

        assert not (tmp_repo / ".niyam").exists()

        # Check governance documents are not created in dry run
        expected_docs = [
            "01-niyam-governance-prd.md",
            "02-niyam-technical-architecture.md",
            "03-niyam-security-access-governance.md",
            "04-niyam-dashboard-frontend-spec.md",
            "05-niyam-feature-ticket-list.md",
            "06-niyam-backward-compatibility-and-migration-plan.md",
        ]
        for doc in expected_docs:
            assert not (tmp_repo / doc).exists()

    def test_init_with_claude_runtime(self, tmp_repo: Path) -> None:
        """niyam init --runtime claude should also generate Claude files."""
        from niyam.core.init import run_init

        console = Console(quiet=True)
        os.chdir(tmp_repo)
        run_init(
            profile="fullstack",
            runtime="claude",
            dry_run=False,
            force=False,
            console=console,
        )

        assert (tmp_repo / ".niyam").is_dir()
        assert (tmp_repo / "CLAUDE.md").exists()
        assert (tmp_repo / ".claude").is_dir()

    def test_init_invalid_profile_fails(self, tmp_repo: Path) -> None:
        """niyam init with unknown profile should fail."""
        from niyam.core.init import run_init

        console = Console(quiet=True)
        os.chdir(tmp_repo)

        with pytest.raises(SystemExit):
            run_init(
                profile="nonexistent",
                runtime=None,
                dry_run=False,
                force=False,
                console=console,
            )

    def test_init_backend_profile(self, tmp_repo: Path) -> None:
        """niyam init --profile backend should create only backend-related agents."""
        from niyam.core.init import run_init

        console = Console(quiet=True)
        os.chdir(tmp_repo)
        run_init(
            profile="backend", runtime=None, dry_run=False, force=False, console=console
        )

        agents_dir = tmp_repo / ".niyam" / "agents"
        assert agents_dir.is_dir()
        agent_names = {f.name for f in agents_dir.glob("*.md")}
        assert agent_names == {
            "backend-specialist.md",
            "security-reviewer.md",
            "qa-reviewer.md",
        }

    def test_init_frontend_profile(self, tmp_repo: Path) -> None:
        """niyam init --profile frontend should create only frontend-related agents."""
        from niyam.core.init import run_init

        console = Console(quiet=True)
        os.chdir(tmp_repo)
        run_init(
            profile="frontend",
            runtime=None,
            dry_run=False,
            force=False,
            console=console,
        )

        agents_dir = tmp_repo / ".niyam" / "agents"
        assert agents_dir.is_dir()
        agent_names = {f.name for f in agents_dir.glob("*.md")}
        assert agent_names == {"frontend-specialist.md", "qa-reviewer.md"}
