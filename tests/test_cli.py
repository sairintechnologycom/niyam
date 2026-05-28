"""Tests for sutra CLI commands."""

from __future__ import annotations

from typer.testing import CliRunner

from sutra.cli import app

runner = CliRunner()


class TestCLI:
    """Tests for the CLI entry points."""

    def test_version(self) -> None:
        """sutra version should print the version."""
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output

    def test_help(self) -> None:
        """sutra --help should show all commands."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "init" in result.output
        assert "sync" in result.output
        assert "doctor" in result.output
        assert "report" in result.output

    def test_context_help(self) -> None:
        """sutra context --help should show subcommands."""
        result = runner.invoke(app, ["context", "--help"])
        assert result.exit_code == 0
        assert "refresh" in result.output
        assert "show" in result.output
        assert "diff" in result.output

    def test_guard_help(self) -> None:
        """sutra guard --help should show subcommands."""
        result = runner.invoke(app, ["guard", "--help"])
        assert result.exit_code == 0
        assert "enable" in result.output
        assert "disable" in result.output
        assert "careful" in result.output
        assert "freeze" in result.output

    def test_runtime_help(self) -> None:
        """sutra runtime --help should show subcommands."""
        result = runner.invoke(app, ["runtime", "--help"])
        assert result.exit_code == 0
        assert "add" in result.output

    def test_policy_help(self) -> None:
        """sutra policy --help should show subcommands."""
        result = runner.invoke(app, ["policy", "--help"])
        assert result.exit_code == 0
        assert "validate" in result.output
