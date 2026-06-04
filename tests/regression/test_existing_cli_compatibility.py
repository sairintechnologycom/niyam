"""Regression tests for existing Niyam CLI commands compatibility."""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

from niyam import __version__
from niyam.cli import app

runner = CliRunner()


def test_existing_cli_help() -> None:
    """Verify that niyam --help works and lists all existing commands."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "init" in result.output
    assert "sync" in report_output_lower(result.output)
    assert "doctor" in result.output
    assert "report" in result.output
    assert "start" in result.output
    assert "next" in result.output
    assert "update" in result.output
    assert "version" in result.output


def test_existing_commands_help() -> None:
    """Verify that --help works for all existing subcommands/groups."""
    commands = [
        ["init", "--help"],
        ["sync", "--help"],
        ["doctor", "--help"],
        ["report", "--help"],
        ["start", "--help"],
        ["next", "--help"],
        ["update", "--help"],
        ["context", "--help"],
        ["runtime", "--help"],
        ["policy", "--help"],
        ["pack", "--help"],
        ["memory", "--help"],
        ["mission", "--help"],
        ["review", "--help"],
        ["pr", "--help"],
        ["ci", "--help"],
    ]
    for cmd in commands:
        result = runner.invoke(app, cmd)
        assert result.exit_code == 0, f"Command {' '.join(cmd)} failed with code {result.exit_code}"


def test_version_command() -> None:
    """Verify the version command works and returns the correct version."""
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert __version__ in result.output


def test_cli_entrypoint_import() -> None:
    """Verify the package entrypoint main function can be imported and runs."""
    from niyam.cli import main
    assert callable(main)


def report_output_lower(output: str) -> str:
    """Helper to convert output to lowercase for safe matching."""
    return output.lower()
