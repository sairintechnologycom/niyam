"""E2E tests for niyam mcp tool registry commands."""

from __future__ import annotations

from pathlib import Path


def test_mcp_registry_workflow(clean_workspace: Path, run_cli) -> None:
    """MCP registry registers, lists, shows, and approves tools."""
    # 1. Initialize Niyam
    init_res = run_cli(["niyam", "init", "--profile", "fullstack"], cwd=clean_workspace)
    assert init_res.returncode == 0

    # 2. Register a tool (unapproved)
    reg_res = run_cli(
        [
            "niyam",
            "mcp",
            "register",
            "test-tool",
            "--type",
            "api",
            "--command-or-url",
            "https://api.test.com",
            "--approved",
            "false",
            "--notes",
            "A simple test tool",
        ],
        cwd=clean_workspace,
    )
    assert reg_res.returncode == 0
    assert "successfully registered" in reg_res.stdout

    # 3. List tools and verify it shows unapproved
    list_res = run_cli(["niyam", "mcp", "list"], cwd=clean_workspace)
    assert list_res.returncode == 0
    assert "test-tool" in list_res.stdout
    assert "No" in list_res.stdout  # Approved is No

    # 4. Show details of the registered tool
    show_res = run_cli(["niyam", "mcp", "show", "test-tool"], cwd=clean_workspace)
    assert show_res.returncode == 0
    assert "test-tool" in show_res.stdout
    assert "https://api.test.com" in show_res.stdout

    # 5. Approve the tool
    app_res = run_cli(["niyam", "mcp", "approve", "test-tool"], cwd=clean_workspace)
    assert app_res.returncode == 0
    assert "successfully approved" in app_res.stdout

    # 6. List tools and verify it is now approved
    list_approved_res = run_cli(["niyam", "mcp", "list"], cwd=clean_workspace)
    assert list_approved_res.returncode == 0
    assert "Yes" in list_approved_res.stdout  # Approved is Yes

    # 7. Generate risk report
    report_res = run_cli(["niyam", "mcp", "risk-report"], cwd=clean_workspace)
    assert report_res.returncode == 0
    assert "Total Registered Tools" in report_res.stdout
