"""Tests for Niyam MCP registry commands."""

from __future__ import annotations

import json
from pathlib import Path
import pytest
from typer.testing import CliRunner

from niyam.cli import app


@pytest.fixture(autouse=True)
def setup_workspace(tmp_path: Path, monkeypatch) -> None:
    """Fixture to ensure tests run in a workspace relative to tmp_path."""
    monkeypatch.chdir(tmp_path)
    # Create mock .niyam directory to mock find_niyam_root
    niyam_dir = tmp_path / ".niyam"
    niyam_dir.mkdir(exist_ok=True)
    # Write empty config
    with open(niyam_dir / "niyam.yaml", "w") as f:
        f.write("version: 0.1.0\n")


def test_mcp_register_tool(tmp_path: Path) -> None:
    """Should register a tool and save to registry."""
    runner = CliRunner()

    # Register filesystem mcp server with explicitly defined fields
    result = runner.invoke(
        app,
        [
            "mcp",
            "register",
            "filesystem",
            "--type",
            "mcp_server",
            "--risk",
            "high",
            "--approved",
            "--command-or-url",
            "npx -y filesystem",
            "--owner",
            "test-user",
            "--capabilities",
            "read_file,write_file",
            "--data-access",
            "local files",
            "--notes",
            "Access to local workspace files.",
        ],
    )
    assert result.exit_code == 0
    assert "filesystem successfully registered" in result.stdout

    # Verify JSON file exists and contains registered tool
    registry_file = tmp_path / ".niyam" / "mcp-registry.json"
    assert registry_file.exists()

    with open(registry_file) as f:
        data = json.load(f)

    assert data["schema_version"] == "1.0.0"
    assert "filesystem" in data["tools"]
    tool = data["tools"]["filesystem"]
    assert tool["name"] == "filesystem"
    assert tool["type"] == "mcp_server"
    assert tool["risk_level"] == "high"
    assert tool["approved"] is True
    assert tool["owner"] == "test-user"
    assert tool["command_or_url"] == "npx -y filesystem"
    assert tool["capabilities"] == ["read_file", "write_file"]
    assert tool["data_access"] == "local files"
    assert tool["notes"] == "Access to local workspace files."


def test_mcp_register_duplicate(tmp_path: Path) -> None:
    """Should fail to register a duplicate tool name."""
    runner = CliRunner()

    # First registration
    result = runner.invoke(app, ["mcp", "register", "tool1", "--type", "cli"])
    assert result.exit_code == 0

    # Duplicate registration
    result2 = runner.invoke(app, ["mcp", "register", "tool1", "--type", "api"])
    assert result2.exit_code == 1
    assert "already registered" in result2.stdout


def test_mcp_register_heuristic_risk(tmp_path: Path) -> None:
    """Should automatically calculate risk if risk is not specified."""
    runner = CliRunner()

    # Heuristic: shell access -> critical
    runner.invoke(
        app,
        [
            "mcp",
            "register",
            "shell-tool",
            "--type",
            "cli",
            "--notes",
            "Allows execution of bash commands",
        ],
    )

    # Heuristic: filesystem -> high
    runner.invoke(
        app,
        [
            "mcp",
            "register",
            "file-tool",
            "--type",
            "local_tool",
            "--notes",
            "Reads local files",
        ],
    )

    # Heuristic: docs -> medium
    runner.invoke(
        app,
        [
            "mcp",
            "register",
            "docs-tool",
            "--type",
            "api",
            "--notes",
            "Access documentation wiki",
        ],
    )

    # Heuristic: search -> low
    runner.invoke(
        app,
        [
            "mcp",
            "register",
            "search-tool",
            "--type",
            "other",
            "--notes",
            "Google search tool",
        ],
    )

    # Heuristic: default fallback -> medium
    runner.invoke(
        app,
        [
            "mcp",
            "register",
            "fallback-tool",
            "--type",
            "api",
            "--notes",
            "Just some random api",
        ],
    )

    registry_file = tmp_path / ".niyam" / "mcp-registry.json"
    with open(registry_file) as f:
        data = json.load(f)

    tools = data["tools"]
    assert tools["shell-tool"]["risk_level"] == "critical"
    assert tools["file-tool"]["risk_level"] == "high"
    assert tools["docs-tool"]["risk_level"] == "medium"
    assert tools["search-tool"]["risk_level"] == "low"
    assert tools["fallback-tool"]["risk_level"] == "medium"


def test_mcp_list_tools(tmp_path: Path) -> None:
    """Should list registered tools."""
    runner = CliRunner()

    # Empty list
    res_empty = runner.invoke(app, ["mcp", "list"])
    assert "No tools registered yet." in res_empty.stdout

    # Register tools
    runner.invoke(app, ["mcp", "register", "tool1", "--type", "cli", "--risk", "low"])
    runner.invoke(app, ["mcp", "register", "tool2", "--type", "api", "--risk", "high"])

    result = runner.invoke(app, ["mcp", "list"])
    assert result.exit_code == 0
    assert "tool1" in result.stdout
    assert "tool2" in result.stdout


def test_mcp_show_tool(tmp_path: Path) -> None:
    """Should show detailed info of a tool."""
    runner = CliRunner()

    # Show non-existent
    res_fail = runner.invoke(app, ["mcp", "show", "nonexistent"])
    assert res_fail.exit_code == 1
    assert "not found in registry" in res_fail.stdout

    # Register
    runner.invoke(
        app,
        [
            "mcp",
            "register",
            "mytool",
            "--type",
            "browser",
            "--risk",
            "critical",
            "--notes",
            "Selenium browser tool",
        ],
    )

    result = runner.invoke(app, ["mcp", "show", "mytool"])
    assert result.exit_code == 0
    assert "mytool" in result.stdout
    assert "browser" in result.stdout
    assert "critical" in result.stdout
    assert "Selenium browser tool" in result.stdout


def test_mcp_risk_report(tmp_path: Path) -> None:
    """Should generate a risk report, highlighting unapproved high-risk tools."""
    runner = CliRunner()

    # Empty registry
    res_empty = runner.invoke(app, ["mcp", "risk-report"])
    assert "No tools registered to analyze." in res_empty.stdout

    # Register tools
    runner.invoke(
        app,
        ["mcp", "register", "tool-low", "--type", "api", "--risk", "low", "--approved"],
    )
    runner.invoke(
        app,
        [
            "mcp",
            "register",
            "tool-high-approved",
            "--type",
            "mcp_server",
            "--risk",
            "high",
            "--approved",
        ],
    )
    runner.invoke(
        app,
        [
            "mcp",
            "register",
            "tool-critical-unapproved",
            "--type",
            "cli",
            "--risk",
            "critical",
            "--no-approved",
            "--notes",
            "Unapproved critical root access.",
        ],
    )

    result = runner.invoke(app, ["mcp", "risk-report"])
    assert result.exit_code == 0
    assert "Total Registered Tools" in result.stdout
    assert "Approved Tools" in result.stdout
    assert "Unapproved Tools" in result.stdout
    assert "Unapproved High/Critical Risk Tools" in result.stdout
    assert "tool-critical-unapproved" in result.stdout
    assert "Unapproved critical root" in result.stdout


def test_mcp_tool_model_fields():
    from niyam.core.mcp import MCPTool
    tool = MCPTool(
        name="test-fields",
        type="mcp_server",
        risk_level="low",
        network_access="localhost",
        requires_approval=True,
        created_at="2026-06-05T10:00:00Z",
        updated_at="2026-06-05T10:00:00Z",
    )
    data = tool.model_dump()
    assert data["schema_version"] == "1.0.0"
    assert data["network_access"] == "localhost"
    assert data["requires_approval"] is True
    assert data["created_at"] == "2026-06-05T10:00:00Z"
    assert data["updated_at"] == "2026-06-05T10:00:00Z"


def test_mcp_tool_validation_error():
    from pydantic import ValidationError
    from niyam.core.mcp import MCPTool

    # Invalid type
    with pytest.raises(ValidationError):
        MCPTool(
            name="invalid-type-tool",
            type="invalid_type",  # type Literal
            risk_level="low",
        )

    # Invalid risk_level
    with pytest.raises(ValidationError):
        MCPTool(
            name="invalid-risk-tool",
            type="mcp_server",
            risk_level="invalid_risk",  # risk_level Literal
        )


