from __future__ import annotations

import json
from pathlib import Path
from niyam.core.loopops import LoopRunner, LoopSpec

def test_mcp_tool_governance(tmp_path: Path) -> None:
    """LOOP-MCP-001 to 010: Verify unapproved MCP tools are governed based on risk level."""
    # Write mock MCP registry
    mcp_data = {
        "schema_version": "1.0.0",
        "tools": {
            "my_mcp/critical_tool": {
                "name": "my_mcp/critical_tool",
                "type": "mcp_server",
                "risk_level": "critical",
                "approved": False
            },
            "my_mcp/medium_tool": {
                "name": "my_mcp/medium_tool",
                "type": "mcp_server",
                "risk_level": "medium",
                "approved": False
            }
        }
    }
    with open(tmp_path / ".niyam" / "mcp-registry.json", "w") as f:
        json.dump(mcp_data, f)

    spec_data = {
        "apiVersion": "niyam.dev/v1",
        "kind": "LoopSpec",
        "metadata": {
            "name": "mcp-policy-test",
            "owner": "platform",
            "riskTier": "medium"
        },
        "goal": {
            "type": "testing",
            "description": "MCP Tool testing"
        },
        "budgets": {
            "maxIterations": 3
        }
    }
    spec = LoopSpec.model_validate(spec_data)

    # 1. Medium risk unapproved tool -> requires_approval
    run_medium = LoopRunner.initialize_run(spec)
    result = LoopRunner.process_step_result(
        run_medium, spec, {
            "status": "success",
            "tools_used": ["my_mcp/medium_tool"]
        }
    )
    assert "Requires human approval" in result
    assert run_medium.status == "requires_approval"

    # 2. Critical risk unapproved tool -> failed (blocked)
    run_critical = LoopRunner.initialize_run(spec)
    result = LoopRunner.process_step_result(
        run_critical, spec, {
            "status": "success",
            "tools_used": ["my_mcp/critical_tool"]
        }
    )
    assert "Blocked by policy" in result
    assert run_critical.status == "blocked"
