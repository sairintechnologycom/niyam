from __future__ import annotations

import json
import yaml
from pathlib import Path
from niyam.core.loopops import LoopRunner, LoopSpec

def test_policy_protected_files(tmp_path: Path) -> None:
    """LOOP-POLICY-004: Should correctly block or require approval for writing to protected files."""
    config_data = {
        "version": "0.1.0",
        "governance": {
            "guard": {
                "protected_files": ["src/auth/**", "config/*.json"]
            }
        }
    }
    with open(tmp_path / ".niyam" / "niyam.yaml", "w") as f:
        yaml.dump(config_data, f)

    spec_data = {
        "apiVersion": "niyam.dev/v1",
        "kind": "LoopSpec",
        "metadata": {
            "name": "policy-test",
            "owner": "platform",
            "riskTier": "medium"
        },
        "goal": {
            "type": "testing",
            "description": "Policy integration testing"
        },
        "budgets": {
            "maxIterations": 3
        }
    }
    spec = LoopSpec.model_validate(spec_data)
    run = LoopRunner.initialize_run(spec)

    # 1. Allowed file change
    result = LoopRunner.process_step_result(
        run, spec, {
            "status": "success",
            "files_changed": ["src/clean.py"]
        }
    )
    assert result is None
    assert run.status == "running"

    # 2. Protected file change -> requires_approval
    result = LoopRunner.process_step_result(
        run, spec, {
            "status": "success",
            "files_changed": ["src/auth/login.py"]
        }
    )
    assert "Requires human approval" in result
    assert run.status == "requires_approval"

    # Verify policy-results.json trace exists and lists the decision
    evidence_dir = tmp_path / run.evidence_path
    with open(evidence_dir / "artifacts" / "policy-results.json", encoding="utf-8") as f:
        policy_res = json.load(f)
    assert policy_res["requires_approval"] is True
    assert len(policy_res["decisions"]) == 1
    assert policy_res["decisions"][0]["ruleId"] == "protected_file:src/auth/**"
    assert policy_res["decisions"][0]["result"] == "approval_required"

def test_policy_unapproved_mcp_tools(tmp_path: Path) -> None:
    """LOOP-POLICY-008: Should check MCP tools against registry and block or require approval based on risk."""
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

def test_policy_exceptions(tmp_path: Path) -> None:
    """Should downgrade policy block/approvals to allow when active exceptions exist."""
    config_data = {
        "version": "0.1.0",
        "governance": {
            "guard": {
                "protected_files": ["src/auth/**"]
            }
        }
    }
    with open(tmp_path / ".niyam" / "niyam.yaml", "w") as f:
        yaml.dump(config_data, f)

    mcp_data = {
        "schema_version": "1.0.0",
        "tools": {
            "my_mcp/critical_tool": {
                "name": "my_mcp/critical_tool",
                "type": "mcp_server",
                "risk_level": "critical",
                "approved": False
            }
        }
    }
    with open(tmp_path / ".niyam" / "mcp-registry.json", "w") as f:
        json.dump(mcp_data, f)

    # Register exceptions
    exceptions_dir = tmp_path / ".niyam" / "governance"
    exceptions_dir.mkdir(parents=True, exist_ok=True)
    with open(exceptions_dir / "policy-exceptions.jsonl", "w") as f:
        f.write(json.dumps({
            "id": "EX-FILE",
            "pattern": "src/auth/**",
            "accepted_by": "security-officer",
            "reason": "Temporary file access exception for test",
            "created_at": "2026-06-17T12:00:00Z"
        }) + "\n")
        f.write(json.dumps({
            "id": "EX-TOOL",
            "pattern": "my_mcp/critical_tool",
            "accepted_by": "security-officer",
            "reason": "Temporary tool exception for test",
            "created_at": "2026-06-17T12:00:00Z"
        }) + "\n")

    spec_data = {
        "apiVersion": "niyam.dev/v1",
        "kind": "LoopSpec",
        "metadata": {
            "name": "exception-test",
            "owner": "platform",
            "riskTier": "high"
        },
        "goal": {
            "type": "testing",
            "description": "Risk Exceptions testing"
        },
        "budgets": {
            "maxIterations": 3
        }
    }
    spec = LoopSpec.model_validate(spec_data)
    run = LoopRunner.initialize_run(spec)

    result = LoopRunner.process_step_result(
        run, spec, {
            "status": "success",
            "files_changed": ["src/auth/login.py"],
            "tools_used": ["my_mcp/critical_tool"]
        }
    )
    assert result is None
    assert run.status == "running"
