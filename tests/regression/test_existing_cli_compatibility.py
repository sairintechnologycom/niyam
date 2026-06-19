"""Regression tests for existing Niyam CLI commands compatibility."""

from __future__ import annotations

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
        assert result.exit_code == 0, (
            f"Command {' '.join(cmd)} failed with code {result.exit_code}"
        )


def test_version_command() -> None:
    """Verify the version command works and returns the correct version."""
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert __version__ in result.output


def test_cli_entrypoint_import() -> None:
    """Verify the package entrypoint main function can be imported and runs."""
    from niyam.cli import main

    assert callable(main)


def test_deprecated_commands_warnings() -> None:
    """Verify that deprecated top-level commands emit warnings."""
    # 1. status
    result = runner.invoke(app, ["status", "--mission", "NONEXISTENT"])
    assert "is deprecated" in result.output
    assert "mission show" in result.output

    # 2. validate
    result = runner.invoke(app, ["validate", "T123"])
    assert "is deprecated" in result.output
    assert "mission validate-task" in result.output

    # 3. dashboard
    result = runner.invoke(app, ["dashboard"])
    assert "is deprecated" in result.output
    assert "mission dashboard" in result.output

    # 4. report
    result = runner.invoke(app, ["report", "-f", "json"])
    assert "is deprecated" in result.output
    assert "mission report --branch" in result.output

    # 5. start
    result = runner.invoke(app, ["start"], input="\n\n")
    assert "is deprecated" in result.output
    assert "mission start-wizard" in result.output


def test_new_subgroup_commands_exist() -> None:
    """Verify new subgroup commands are registered under 'mission' and help works."""
    assert runner.invoke(app, ["mission", "validate-task", "--help"]).exit_code == 0
    assert runner.invoke(app, ["mission", "start-wizard", "--help"]).exit_code == 0
    
    # Verify mission report help lists --branch option
    result = runner.invoke(app, ["mission", "report", "--help"])
    assert result.exit_code == 0
    assert "--branch" in result.output

    # Verify new canonical subgroup commands do not output deprecation warnings
    res_val = runner.invoke(app, ["mission", "validate-task", "T123"])
    assert "is deprecated" not in res_val.output

    res_rep = runner.invoke(app, ["mission", "report", "--branch", "--format", "json"])
    assert "is deprecated" not in res_rep.output


def report_output_lower(output: str) -> str:
    """Helper to convert output to lowercase for safe matching."""
    return output.lower()
