"""Tests for niyam context add/list/remove commands."""

from __future__ import annotations

import os
from pathlib import Path

import yaml
from rich.console import Console


class TestContextAdd:
    """Tests for the context add command."""

    def test_context_add_inline_text(self, niyam_repo: Path) -> None:
        """context add should save inline text as a context document."""
        from niyam.core.context import run_context_add

        console = Console(quiet=True)
        os.chdir(niyam_repo)
        doc_path = run_context_add(
            context_type="prd",
            text="Build a todo app with user authentication and social login.",
            console=console,
            repo_root=niyam_repo,
        )

        assert doc_path.exists()
        content = doc_path.read_text()
        assert "todo app" in content
        assert "type: prd" in content
        assert "source: inline" in content

    def test_context_add_from_file(self, niyam_repo: Path) -> None:
        """context add should import content from a file."""
        from niyam.core.context import run_context_add

        console = Console(quiet=True)
        os.chdir(niyam_repo)

        # Create a PRD file
        prd_file = niyam_repo / "PRD.md"
        prd_file.write_text("# Product Requirements\n\nBuild a SaaS dashboard.", encoding="utf-8")

        doc_path = run_context_add(
            context_type="prd",
            file_path=str(prd_file),
            console=console,
            repo_root=niyam_repo,
        )

        assert doc_path.exists()
        content = doc_path.read_text()
        assert "SaaS dashboard" in content
        assert "source: file" in content
        assert "name: PRD" in content  # name derived from file stem

    def test_context_add_saves_to_docs_dir(self, niyam_repo: Path) -> None:
        """context add should save to .niyam/context/docs/."""
        from niyam.core.context import run_context_add

        console = Console(quiet=True)
        doc_path = run_context_add(
            context_type="overview",
            text="A brief project overview.",
            name="my-project",
            console=console,
            repo_root=niyam_repo,
        )

        expected_dir = niyam_repo / ".niyam" / "context" / "docs"
        assert expected_dir.exists()
        assert doc_path.parent == expected_dir
        assert doc_path.name == "overview-my-project.md"

    def test_context_add_custom_name(self, niyam_repo: Path) -> None:
        """context add should use custom name when provided."""
        from niyam.core.context import run_context_add

        console = Console(quiet=True)
        doc_path = run_context_add(
            context_type="user-stories",
            text="As a user, I want to log in.",
            name="auth-stories",
            console=console,
            repo_root=niyam_repo,
        )

        assert doc_path.name == "user-stories-auth-stories.md"

    def test_context_add_prd_updates_project_yaml(self, niyam_repo: Path) -> None:
        """Adding a PRD should update the project.yaml description."""
        from niyam.core.context import run_context_add

        console = Console(quiet=True)
        run_context_add(
            context_type="prd",
            text="Build an AI-powered code review platform for enterprise teams.",
            console=console,
            repo_root=niyam_repo,
        )

        with open(niyam_repo / ".niyam" / "project.yaml", encoding="utf-8") as f:
            project = yaml.safe_load(f)

        assert "description" in project
        assert "AI-powered code review" in project["description"]

    def test_context_add_rejects_empty(self, niyam_repo: Path) -> None:
        """context add should reject empty content."""
        import pytest
        from niyam.core.context import run_context_add

        console = Console(quiet=True)
        with pytest.raises(SystemExit):
            run_context_add(
                context_type="prd",
                text="   ",
                console=console,
                repo_root=niyam_repo,
            )

    def test_context_add_rejects_invalid_type(self, niyam_repo: Path) -> None:
        """context add should reject invalid context types."""
        import pytest
        from niyam.core.context import run_context_add

        console = Console(quiet=True)
        with pytest.raises(SystemExit):
            run_context_add(
                context_type="invalid-type",
                text="Some content.",
                console=console,
                repo_root=niyam_repo,
            )

    def test_context_add_overwrites_existing(self, niyam_repo: Path) -> None:
        """context add should overwrite an existing document with the same name."""
        from niyam.core.context import run_context_add

        console = Console(quiet=True)

        # Add first version
        run_context_add(
            context_type="prd",
            text="Version 1 of the PRD.",
            name="main",
            console=console,
            repo_root=niyam_repo,
        )

        # Overwrite with second version
        doc_path = run_context_add(
            context_type="prd",
            text="Version 2 of the PRD.",
            name="main",
            console=console,
            repo_root=niyam_repo,
        )

        content = doc_path.read_text()
        assert "Version 2" in content
        assert "Version 1" not in content

    def test_context_add_rejects_multiple_sources(self, niyam_repo: Path) -> None:
        """context add should reject providing both text and file."""
        import pytest
        from niyam.core.context import run_context_add

        console = Console(quiet=True)
        prd_file = niyam_repo / "PRD.md"
        prd_file.write_text("content", encoding="utf-8")

        with pytest.raises(SystemExit):
            run_context_add(
                context_type="prd",
                text="inline text",
                file_path=str(prd_file),
                console=console,
                repo_root=niyam_repo,
            )


class TestContextList:
    """Tests for the context list command."""

    def test_context_list_empty(self, niyam_repo: Path) -> None:
        """context list should handle no documents gracefully."""
        from niyam.core.context import run_context_list

        console = Console(quiet=True)
        # Should not raise
        run_context_list(console=console, repo_root=niyam_repo)

    def test_context_list_shows_documents(self, niyam_repo: Path) -> None:
        """context list should show added documents."""
        from niyam.core.context import run_context_add, load_context_documents

        console = Console(quiet=True)
        run_context_add(
            context_type="prd",
            text="Build a todo app.",
            name="todo-prd",
            console=console,
            repo_root=niyam_repo,
        )
        run_context_add(
            context_type="tech-spec",
            text="Use React and FastAPI.",
            name="stack",
            console=console,
            repo_root=niyam_repo,
        )

        docs = load_context_documents(niyam_repo)
        assert len(docs) == 2

        types = {d["meta"]["type"] for d in docs}
        assert "prd" in types
        assert "tech-spec" in types


class TestContextRemove:
    """Tests for the context remove command."""

    def test_context_remove_by_stem(self, niyam_repo: Path) -> None:
        """context remove should remove a document by type-name stem."""
        from niyam.core.context import run_context_add, run_context_remove, load_context_documents

        console = Console(quiet=True)
        run_context_add(
            context_type="prd",
            text="Build a todo app.",
            name="main",
            console=console,
            repo_root=niyam_repo,
        )

        docs = load_context_documents(niyam_repo)
        assert len(docs) == 1

        run_context_remove("prd-main", console=console, repo_root=niyam_repo)

        docs = load_context_documents(niyam_repo)
        assert len(docs) == 0

    def test_context_remove_by_filename(self, niyam_repo: Path) -> None:
        """context remove should work with full filename."""
        from niyam.core.context import run_context_add, run_context_remove, load_context_documents

        console = Console(quiet=True)
        run_context_add(
            context_type="overview",
            text="A project overview.",
            name="v1",
            console=console,
            repo_root=niyam_repo,
        )

        run_context_remove("overview-v1.md", console=console, repo_root=niyam_repo)

        docs = load_context_documents(niyam_repo)
        assert len(docs) == 0

    def test_context_remove_not_found(self, niyam_repo: Path) -> None:
        """context remove should handle missing documents gracefully."""
        from niyam.core.context import run_context_remove

        console = Console(quiet=True)
        # Should not raise, just print error
        run_context_remove("nonexistent", console=console, repo_root=niyam_repo)


class TestLoadContextDocuments:
    """Tests for load_context_documents helper."""

    def test_load_empty(self, niyam_repo: Path) -> None:
        """load_context_documents should return empty list when no docs exist."""
        from niyam.core.context import load_context_documents

        docs = load_context_documents(niyam_repo)
        assert docs == []

    def test_load_parses_frontmatter(self, niyam_repo: Path) -> None:
        """load_context_documents should parse YAML frontmatter correctly."""
        from niyam.core.context import run_context_add, load_context_documents

        console = Console(quiet=True)
        run_context_add(
            context_type="prd",
            text="The actual body content.",
            name="test",
            console=console,
            repo_root=niyam_repo,
        )

        docs = load_context_documents(niyam_repo)
        assert len(docs) == 1

        doc = docs[0]
        assert doc["meta"]["type"] == "prd"
        assert doc["meta"]["name"] == "test"
        assert doc["meta"]["source"] == "inline"
        assert doc["content"] == "The actual body content."


class TestContextShowWithDocs:
    """Tests for context show including added documents."""

    def test_context_show_displays_added_docs(self, niyam_repo: Path) -> None:
        """context show should mention added context documents."""
        from niyam.core.context import run_context_add, run_context_show
        from io import StringIO

        os.chdir(niyam_repo)
        quiet_console = Console(quiet=True)
        run_context_add(
            context_type="prd",
            text="Build a todo app.",
            name="todo",
            console=quiet_console,
            repo_root=niyam_repo,
        )

        # Capture output
        buf = StringIO()
        out_console = Console(file=buf, force_terminal=False)
        run_context_show(console=out_console, repo_root=niyam_repo)

        output = buf.getvalue()
        assert "prd" in output.lower()
        assert "todo" in output.lower()
