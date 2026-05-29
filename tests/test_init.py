"""Tests for sutra init command."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
import yaml
from rich.console import Console


class TestInit:
    """Tests for the init command."""

    def test_init_creates_sutra_directory(self, tmp_repo: Path) -> None:
        """sutra init should create .sutra/ directory."""
        from sutra.core.init import run_init

        console = Console(quiet=True)
        os.chdir(tmp_repo)
        run_init(profile="fullstack", runtime=None, dry_run=False, force=False, console=console)

        assert (tmp_repo / ".sutra").is_dir()

    def test_init_creates_mvp_directories(self, tmp_repo: Path) -> None:
        """sutra init should create required MVP subdirectories."""
        from sutra.core.init import run_init

        console = Console(quiet=True)
        os.chdir(tmp_repo)
        run_init(profile="fullstack", runtime=None, dry_run=False, force=False, console=console)

        for subdir in ["tasks", "runs", "templates", "worktrees", "evidence"]:
            assert (tmp_repo / ".sutra" / subdir).is_dir()

    def test_init_creates_sutra_yaml(self, tmp_repo: Path) -> None:
        """sutra init should create valid sutra.yaml."""
        from sutra.core.init import run_init

        console = Console(quiet=True)
        os.chdir(tmp_repo)
        run_init(profile="fullstack", runtime=None, dry_run=False, force=False, console=console)

        sutra_yaml = tmp_repo / ".sutra" / "sutra.yaml"
        assert sutra_yaml.exists()

        with open(sutra_yaml) as f:
            data = yaml.safe_load(f)

        assert data["version"] == "0.1.0"
        assert data["profile"] == "fullstack"
        assert data["project_name"] == tmp_repo.name

    def test_init_creates_agents(self, tmp_repo: Path) -> None:
        """sutra init should create agent files."""
        from sutra.core.init import run_init

        console = Console(quiet=True)
        os.chdir(tmp_repo)
        run_init(profile="fullstack", runtime=None, dry_run=False, force=False, console=console)

        agents_dir = tmp_repo / ".sutra" / "agents"
        assert agents_dir.is_dir()
        agent_files = list(agents_dir.glob("*.md"))
        assert len(agent_files) >= 4

    def test_init_creates_skills(self, tmp_repo: Path) -> None:
        """sutra init should create skill directories."""
        from sutra.core.init import run_init

        console = Console(quiet=True)
        os.chdir(tmp_repo)
        run_init(profile="fullstack", runtime=None, dry_run=False, force=False, console=console)

        skills_dir = tmp_repo / ".sutra" / "skills"
        assert skills_dir.is_dir()
        skill_dirs = [d for d in skills_dir.iterdir() if d.is_dir()]
        assert len(skill_dirs) >= 4

    def test_init_creates_commands(self, tmp_repo: Path) -> None:
        """sutra init should create command files."""
        from sutra.core.init import run_init

        console = Console(quiet=True)
        os.chdir(tmp_repo)
        run_init(profile="fullstack", runtime=None, dry_run=False, force=False, console=console)

        commands_dir = tmp_repo / ".sutra" / "commands"
        assert commands_dir.is_dir()
        command_files = list(commands_dir.glob("*.md"))
        assert len(command_files) >= 4

    def test_init_creates_policies(self, tmp_repo: Path) -> None:
        """sutra init should create policy files."""
        from sutra.core.init import run_init

        console = Console(quiet=True)
        os.chdir(tmp_repo)
        run_init(profile="fullstack", runtime=None, dry_run=False, force=False, console=console)

        policies_dir = tmp_repo / ".sutra" / "policies"
        assert policies_dir.is_dir()
        policy_files = list(policies_dir.glob("*.yaml"))
        assert len(policy_files) >= 4

    def test_init_fails_if_already_exists(self, sutra_repo: Path) -> None:
        """sutra init should fail if .sutra/ already exists."""
        from sutra.core.init import run_init

        console = Console(quiet=True)
        os.chdir(sutra_repo)

        with pytest.raises(SystemExit):
            run_init(profile="fullstack", runtime=None, dry_run=False, force=False, console=console)

    def test_init_force_overwrites(self, sutra_repo: Path) -> None:
        """sutra init --force should overwrite existing .sutra/."""
        from sutra.core.init import run_init

        console = Console(quiet=True)
        os.chdir(sutra_repo)

        # Should not raise
        run_init(profile="fullstack", runtime=None, dry_run=False, force=True, console=console)

        assert (sutra_repo / ".sutra" / "sutra.yaml").exists()

    def test_init_dry_run_creates_nothing(self, tmp_repo: Path) -> None:
        """sutra init --dry-run should not create any files."""
        from sutra.core.init import run_init

        console = Console(quiet=True)
        os.chdir(tmp_repo)
        run_init(profile="fullstack", runtime=None, dry_run=True, force=False, console=console)

        assert not (tmp_repo / ".sutra").exists()

    def test_init_with_claude_runtime(self, tmp_repo: Path) -> None:
        """sutra init --runtime claude should also generate Claude files."""
        from sutra.core.init import run_init

        console = Console(quiet=True)
        os.chdir(tmp_repo)
        run_init(profile="fullstack", runtime="claude", dry_run=False, force=False, console=console)

        assert (tmp_repo / ".sutra").is_dir()
        assert (tmp_repo / "CLAUDE.md").exists()
        assert (tmp_repo / ".claude").is_dir()

    def test_init_invalid_profile_fails(self, tmp_repo: Path) -> None:
        """sutra init with unknown profile should fail."""
        from sutra.core.init import run_init

        console = Console(quiet=True)
        os.chdir(tmp_repo)

        with pytest.raises(SystemExit):
            run_init(profile="nonexistent", runtime=None, dry_run=False, force=False, console=console)

    def test_init_backend_profile(self, tmp_repo: Path) -> None:
        """sutra init --profile backend should create only backend-related agents."""
        from sutra.core.init import run_init

        console = Console(quiet=True)
        os.chdir(tmp_repo)
        run_init(profile="backend", runtime=None, dry_run=False, force=False, console=console)

        agents_dir = tmp_repo / ".sutra" / "agents"
        assert agents_dir.is_dir()
        agent_names = {f.name for f in agents_dir.glob("*.md")}
        assert agent_names == {"backend-specialist.md", "security-reviewer.md", "qa-reviewer.md"}

    def test_init_frontend_profile(self, tmp_repo: Path) -> None:
        """sutra init --profile frontend should create only frontend-related agents."""
        from sutra.core.init import run_init

        console = Console(quiet=True)
        os.chdir(tmp_repo)
        run_init(profile="frontend", runtime=None, dry_run=False, force=False, console=console)

        agents_dir = tmp_repo / ".sutra" / "agents"
        assert agents_dir.is_dir()
        agent_names = {f.name for f in agents_dir.glob("*.md")}
        assert agent_names == {"frontend-specialist.md", "qa-reviewer.md"}

