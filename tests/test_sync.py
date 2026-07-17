"""Tests for niyam sync and Claude/Codex adapters."""

from __future__ import annotations

import os
from pathlib import Path

import yaml
from rich.console import Console


class TestClaudeSync:
    """Tests for Claude runtime sync."""

    def test_claude_sync_creates_claude_md(self, niyam_repo: Path) -> None:
        """Sync should create CLAUDE.md."""
        from niyam.core.sync import run_runtime_add

        console = Console(quiet=True)
        os.chdir(niyam_repo)
        run_runtime_add(runtime="claude", console=console)

        assert (niyam_repo / "CLAUDE.md").exists()

    def test_claude_sync_creates_claude_dir(self, niyam_repo: Path) -> None:
        """Sync should create .claude/ directory structure."""
        from niyam.core.sync import run_runtime_add

        console = Console(quiet=True)
        os.chdir(niyam_repo)
        run_runtime_add(runtime="claude", console=console)

        claude_dir = niyam_repo / ".claude"
        assert claude_dir.is_dir()
        assert (claude_dir / "agents").is_dir()
        assert (claude_dir / "commands").is_dir()
        assert (claude_dir / "skills").is_dir()
        assert (claude_dir / "hooks").is_dir()

    def test_claude_sync_creates_agents(self, niyam_repo: Path) -> None:
        """Sync should project agents to .claude/agents/."""
        from niyam.core.sync import run_runtime_add

        console = Console(quiet=True)
        os.chdir(niyam_repo)
        run_runtime_add(runtime="claude", console=console)

        agents = list((niyam_repo / ".claude" / "agents").glob("*.md"))
        assert len(agents) >= 4

    def test_claude_sync_creates_hooks(self, niyam_repo: Path) -> None:
        """Sync should generate pre_tool_guard.py hook."""
        from niyam.core.sync import run_runtime_add

        console = Console(quiet=True)
        os.chdir(niyam_repo)
        run_runtime_add(runtime="claude", console=console)

        hook = niyam_repo / ".claude" / "hooks" / "pre_tool_guard.py"
        assert hook.exists()
        content = hook.read_text()
        assert "DENY_PATTERNS" in content

    def test_claude_sync_creates_settings(self, niyam_repo: Path) -> None:
        """Sync should generate settings.json."""
        from niyam.core.sync import run_runtime_add

        console = Console(quiet=True)
        os.chdir(niyam_repo)
        run_runtime_add(runtime="claude", console=console)

        settings = niyam_repo / ".claude" / "settings.json"
        assert settings.exists()

    def test_claude_md_contains_policies(self, niyam_repo: Path) -> None:
        """CLAUDE.md should contain policy information."""
        from niyam.core.sync import run_runtime_add

        console = Console(quiet=True)
        os.chdir(niyam_repo)
        run_runtime_add(runtime="claude", console=console)

        content = (niyam_repo / "CLAUDE.md").read_text()
        assert "Policies" in content or "Denied" in content


class TestCodexSync:
    """Tests for Codex runtime sync."""

    def test_codex_sync_creates_agents_md(self, niyam_repo: Path) -> None:
        """Sync should create AGENTS.md."""
        from niyam.core.sync import run_runtime_add

        console = Console(quiet=True)
        os.chdir(niyam_repo)
        run_runtime_add(runtime="codex", console=console)

        assert (niyam_repo / "AGENTS.md").exists()

    def test_agents_md_contains_policies(self, niyam_repo: Path) -> None:
        """AGENTS.md should contain policy information."""
        from niyam.core.sync import run_runtime_add

        console = Console(quiet=True)
        os.chdir(niyam_repo)
        run_runtime_add(runtime="codex", console=console)

        content = (niyam_repo / "AGENTS.md").read_text()
        assert "Policies" in content or "Denied" in content

    def test_codex_sync_creates_hooks_and_settings(self, niyam_repo: Path) -> None:
        """Sync should generate hooks/pre_tool_guard.py and settings.json for Codex."""
        from niyam.core.sync import run_runtime_add

        console = Console(quiet=True)
        os.chdir(niyam_repo)
        run_runtime_add(runtime="codex", console=console)

        codex_dir = niyam_repo / ".codex"
        assert codex_dir.is_dir()
        assert (codex_dir / "hooks" / "pre_tool_guard.py").exists()
        assert (codex_dir / "settings.json").exists()


class TestGeminiSync:
    """Tests for Gemini runtime sync."""

    def test_gemini_sync_creates_gemini_md(self, niyam_repo: Path) -> None:
        """Sync should create GEMINI.md."""
        from niyam.core.sync import run_runtime_add

        console = Console(quiet=True)
        os.chdir(niyam_repo)
        run_runtime_add(runtime="gemini", console=console)

        assert (niyam_repo / "GEMINI.md").exists()

    def test_gemini_sync_creates_gemini_dir(self, niyam_repo: Path) -> None:
        """Sync should create .gemini/ directory structure."""
        from niyam.core.sync import run_runtime_add

        console = Console(quiet=True)
        os.chdir(niyam_repo)
        run_runtime_add(runtime="gemini", console=console)

        gemini_dir = niyam_repo / ".gemini"
        assert gemini_dir.is_dir()
        assert (gemini_dir / "STYLE.md").exists()
        assert (gemini_dir / "settings.json").exists()

    def test_gemini_md_contains_policies(self, niyam_repo: Path) -> None:
        """GEMINI.md should contain policy information."""
        from niyam.core.sync import run_runtime_add

        console = Console(quiet=True)
        os.chdir(niyam_repo)
        run_runtime_add(runtime="gemini", console=console)

        content = (niyam_repo / "GEMINI.md").read_text()
        assert "Policies" in content or "Denied" in content

    def test_gemini_sync_creates_hooks_and_settings(self, niyam_repo: Path) -> None:
        """Sync should generate hooks/pre_tool_guard.py and settings.json for Gemini."""
        from niyam.core.sync import run_runtime_add

        console = Console(quiet=True)
        os.chdir(niyam_repo)
        run_runtime_add(runtime="gemini", console=console)

        gemini_dir = niyam_repo / ".gemini"
        assert gemini_dir.is_dir()
        assert (gemini_dir / "hooks" / "pre_tool_guard.py").exists()
        assert (gemini_dir / "settings.json").exists()


class TestAgySync:
    def test_agy_sync_creates_shared_agents_md(self, niyam_repo: Path) -> None:
        from niyam.core.sync import run_runtime_add

        console = Console(quiet=True)
        os.chdir(niyam_repo)
        run_runtime_add(runtime="agy", console=console)

        assert (niyam_repo / "AGENTS.md").exists()
        with open(niyam_repo / ".niyam" / "niyam.yaml") as f:
            assert "agy" in yaml.safe_load(f)["runtimes"]


class TestRuntimeAdd:
    """Tests for runtime add command."""

    def test_runtime_add_updates_config(self, niyam_repo: Path) -> None:
        """runtime add should update niyam.yaml."""
        from niyam.core.sync import run_runtime_add

        console = Console(quiet=True)
        os.chdir(niyam_repo)
        run_runtime_add(runtime="claude", console=console)

        with open(niyam_repo / ".niyam" / "niyam.yaml") as f:
            config = yaml.safe_load(f)

        assert "claude" in config["runtimes"]

    def test_runtime_add_duplicate_is_safe(self, niyam_repo: Path) -> None:
        """runtime add should be idempotent."""
        from niyam.core.sync import run_runtime_add

        console = Console(quiet=True)
        os.chdir(niyam_repo)
        run_runtime_add(runtime="claude", console=console)
        run_runtime_add(runtime="claude", console=console)

        with open(niyam_repo / ".niyam" / "niyam.yaml") as f:
            config = yaml.safe_load(f)

        assert config["runtimes"].count("claude") == 1
