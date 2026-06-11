import pytest
import os
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
from niyam.core.policy import (
    add_exception,
    load_exceptions,
    is_exception_active,
    PolicyException,
    TeamPolicy,
    PolicyRole,
    PolicyRule,
    load_team_policy
)
from niyam.policies.guard import run_guard_run
from rich.console import Console

def test_policy_exception_lifecycle(tmp_path: Path):
    """Test adding, loading, and matching policy exceptions."""
    # Setup
    gov_dir = tmp_path / ".niyam" / "governance"
    gov_dir.mkdir(parents=True)
    
    now = datetime.now(timezone.utc)
    expires = now + timedelta(days=1)
    
    exception = PolicyException(
        id="EX-TEST",
        pattern="rm -rf /",
        accepted_by="test-user",
        reason="Testing exception logic",
        created_at=now.isoformat(),
        expires_at=expires.isoformat(),
    )
    
    # 1. Add exception
    add_exception(exception, root=tmp_path)
    
    # 2. Load exceptions
    exceptions = load_exceptions(root=tmp_path)
    assert len(exceptions) == 1
    assert exceptions[0].id == "EX-TEST"
    assert exceptions[0].pattern == "rm -rf /"
    
    # 3. Check active exception
    active = is_exception_active("rm -rf /", root=tmp_path)
    assert active is not None
    assert active.id == "EX-TEST"
    
    # 4. Check non-matching pattern
    assert is_exception_active("ls", root=tmp_path) is None
    
    # 5. Check expired exception
    expired_now = now - timedelta(days=2)
    expired_exception = PolicyException(
        id="EX-EXPIRED",
        pattern="expired-pattern",
        accepted_by="test-user",
        reason="Expired",
        created_at=expired_now.isoformat(),
        expires_at=expired_now.isoformat(),
    )
    add_exception(expired_exception, root=tmp_path)
    assert is_exception_active("expired-pattern", root=tmp_path) is None

def test_team_policy_loading(tmp_path: Path):
    """Test loading a team policy from YAML."""
    policy_dir = tmp_path / ".niyam" / "policies"
    policy_dir.mkdir(parents=True)
    
    policy_content = {
        "name": "Test Team",
        "roles": [
            {"name": "admin", "users": ["bhushan"], "permissions": ["all"]}
        ],
        "rules": [
            {"id": "R1", "type": "block", "pattern": "rm -rf", "exception_allowed": False}
        ]
    }
    
    (policy_dir / "team-policy.yaml").write_text(json.dumps(policy_content))
    
    policy = load_team_policy(root=tmp_path)
    assert policy is not None
    assert policy.name == "Test Team"
    assert len(policy.roles) == 1
    assert policy.roles[0].name == "admin"
    assert len(policy.rules) == 1
    assert policy.rules[0].id == "R1"

def test_guard_respects_exceptions(tmp_path: Path, monkeypatch):
    """Test that niyam guard run respects active exceptions."""
    # Setup niyam root
    niyam_dir = tmp_path / ".niyam"
    niyam_dir.mkdir()
    (niyam_dir / "niyam.yaml").write_text("project:\n  name: test\n")
    
    # Mock find_niyam_root to return our tmp_path
    monkeypatch.setattr("niyam.policies.guard.find_niyam_root", lambda: tmp_path)
    monkeypatch.setattr("niyam.core.policy.find_niyam_root", lambda: tmp_path)
    
    # Create a blocked command policy
    (niyam_dir / "policies").mkdir()
    (niyam_dir / "policies" / "commands.yaml").write_text("deny: ['rm -rf /']")
    
    # 1. Verify it blocks without exception
    console = Console()
    with pytest.raises(SystemExit) as excinfo:
        run_guard_run(["rm", "-rf", "/"], capture_output=False, console=console, mode_override="block")
    assert excinfo.value.code == 1
    
    # 2. Add exception
    now = datetime.now(timezone.utc).isoformat()
    exception = PolicyException(
        id="EX-BYPASS",
        pattern="rm -rf /",
        accepted_by="test",
        reason="Bypass for test",
        created_at=now
    )
    add_exception(exception, root=tmp_path)
    
    # 3. Verify it ALLOWS with exception
    # Note: run_guard_run will attempt to execute the command. 
    # We should mock subprocess.Popen or use a safe command.
    
    monkeypatch.setattr("niyam.policies.guard._match_command_pattern", lambda args, pat: True)
    
    # Use a safe command that will definitely exist
    safe_cmd = ["echo", "hello"]
    
    # Update exception pattern to match safe_cmd
    exception.pattern = "echo hello"
    (tmp_path / ".niyam" / "governance" / "policy-exceptions.jsonl").write_text(json.dumps(exception.model_dump()) + "\n")
    
    # Update policy to deny safe_cmd
    (niyam_dir / "policies" / "commands.yaml").write_text("deny: ['echo hello']")
    
    with pytest.raises(SystemExit) as excinfo:
        run_guard_run(safe_cmd, capture_output=False, console=console, mode_override="block")
    
    # Should NOT be 1 (blocked), but the exit code of echo hello (0)
    assert excinfo.value.code == 0
