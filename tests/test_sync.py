"""Tests for sutra sync and Claude/Codex adapters."""

from __future__ import annotations

import os
from pathlib import Path

import yaml
from rich.console import Console


class TestClaudeSync:
    """Tests for Claude runtime sync."""

    def test_claude_sync_creates_claude_md(self, sutra_repo: Path) -> None:
        """Sync should create CLAUDE.md."""
        from sutra.core.sync import run_runtime_add

        console = Console(quiet=True)
        os.chdir(sutra_repo)
        run_runtime_add(runtime="claude", console=console)

        assert (sutra_repo / "CLAUDE.md").exists()

    def test_claude_sync_creates_claude_dir(self, sutra_repo: Path) -> None:
        """Sync should create .claude/ directory structure."""
        from sutra.core.sync import run_runtime_add

        console = Console(quiet=True)
        os.chdir(sutra_repo)
        run_runtime_add(runtime="claude", console=console)

        claude_dir = sutra_repo / ".claude"
        assert claude_dir.is_dir()
        assert (claude_dir / "agents").is_dir()
        assert (claude_dir / "commands").is_dir()
        assert (claude_dir / "skills").is_dir()
        assert (claude_dir / "hooks").is_dir()

    def test_claude_sync_creates_agents(self, sutra_repo: Path) -> None:
        """Sync should project agents to .claude/agents/."""
        from sutra.core.sync import run_runtime_add

        console = Console(quiet=True)
        os.chdir(sutra_repo)
        run_runtime_add(runtime="claude", console=console)

        agents = list((sutra_repo / ".claude" / "agents").glob("*.md"))
        assert len(agents) >= 4

    def test_claude_sync_creates_hooks(self, sutra_repo: Path) -> None:
        """Sync should generate pre_tool_guard.py hook."""
        from sutra.core.sync import run_runtime_add

        console = Console(quiet=True)
        os.chdir(sutra_repo)
        run_runtime_add(runtime="claude", console=console)

        hook = sutra_repo / ".claude" / "hooks" / "pre_tool_guard.py"
        assert hook.exists()
        content = hook.read_text()
        assert "DENY_PATTERNS" in content

    def test_claude_sync_creates_settings(self, sutra_repo: Path) -> None:
        """Sync should generate settings.json."""
        from sutra.core.sync import run_runtime_add

        console = Console(quiet=True)
        os.chdir(sutra_repo)
        run_runtime_add(runtime="claude", console=console)

        settings = sutra_repo / ".claude" / "settings.json"
        assert settings.exists()

    def test_claude_md_contains_policies(self, sutra_repo: Path) -> None:
        """CLAUDE.md should contain policy information."""
        from sutra.core.sync import run_runtime_add

        console = Console(quiet=True)
        os.chdir(sutra_repo)
        run_runtime_add(runtime="claude", console=console)

        content = (sutra_repo / "CLAUDE.md").read_text()
        assert "Policies" in content or "Denied" in content


class TestCodexSync:
    """Tests for Codex runtime sync."""

    def test_codex_sync_creates_agents_md(self, sutra_repo: Path) -> None:
        """Sync should create AGENTS.md."""
        from sutra.core.sync import run_runtime_add

        console = Console(quiet=True)
        os.chdir(sutra_repo)
        run_runtime_add(runtime="codex", console=console)

        assert (sutra_repo / "AGENTS.md").exists()

    def test_agents_md_contains_policies(self, sutra_repo: Path) -> None:
        """AGENTS.md should contain policy information."""
        from sutra.core.sync import run_runtime_add

        console = Console(quiet=True)
        os.chdir(sutra_repo)
        run_runtime_add(runtime="codex", console=console)

        content = (sutra_repo / "AGENTS.md").read_text()
        assert "Policies" in content or "Denied" in content


class TestGeminiSync:
    """Tests for Gemini runtime sync."""

    def test_gemini_sync_creates_gemini_md(self, sutra_repo: Path) -> None:
        """Sync should create GEMINI.md."""
        from sutra.core.sync import run_runtime_add

        console = Console(quiet=True)
        os.chdir(sutra_repo)
        run_runtime_add(runtime="gemini", console=console)

        assert (sutra_repo / "GEMINI.md").exists()

    def test_gemini_sync_creates_gemini_dir(self, sutra_repo: Path) -> None:
        """Sync should create .gemini/ directory structure."""
        from sutra.core.sync import run_runtime_add

        console = Console(quiet=True)
        os.chdir(sutra_repo)
        run_runtime_add(runtime="gemini", console=console)

        gemini_dir = sutra_repo / ".gemini"
        assert gemini_dir.is_dir()
        assert (gemini_dir / "STYLE.md").exists()
        assert (gemini_dir / "settings.json").exists()

    def test_gemini_md_contains_policies(self, sutra_repo: Path) -> None:
        """GEMINI.md should contain policy information."""
        from sutra.core.sync import run_runtime_add

        console = Console(quiet=True)
        os.chdir(sutra_repo)
        run_runtime_add(runtime="gemini", console=console)

        content = (sutra_repo / "GEMINI.md").read_text()
        assert "Policies" in content or "Denied" in content



class TestRuntimeAdd:
    """Tests for runtime add command."""

    def test_runtime_add_updates_config(self, sutra_repo: Path) -> None:
        """runtime add should update sutra.yaml."""
        from sutra.core.sync import run_runtime_add

        console = Console(quiet=True)
        os.chdir(sutra_repo)
        run_runtime_add(runtime="claude", console=console)

        with open(sutra_repo / ".sutra" / "sutra.yaml") as f:
            config = yaml.safe_load(f)

        assert "claude" in config["runtimes"]

    def test_runtime_add_duplicate_is_safe(self, sutra_repo: Path) -> None:
        """runtime add should be idempotent."""
        from sutra.core.sync import run_runtime_add

        console = Console(quiet=True)
        os.chdir(sutra_repo)
        run_runtime_add(runtime="claude", console=console)
        run_runtime_add(runtime="claude", console=console)

        with open(sutra_repo / ".sutra" / "sutra.yaml") as f:
            config = yaml.safe_load(f)

        assert config["runtimes"].count("claude") == 1
