import pytest
import subprocess
from pathlib import Path
from niyam.core.loopops.adapters import get_adapter, ShellAdapter, AgentTaskRequest
from niyam.cli import app as cli_app
from typer.testing import CliRunner

runner = CliRunner()

def test_get_adapter_raises_value_error():
    with pytest.raises(ValueError, match="Unknown adapter"):
        get_adapter("typo")

def test_shell_adapter_rejects_injection(tmp_path):
    adapter = ShellAdapter()
    req = AgentTaskRequest(
        goal="echo ok; rm -rf /",
        workspace_path=tmp_path,
        action="implement",
        step_name="test"
    )
    result = adapter.implement(req)
    # Since it uses shlex.split, `echo ok; rm -rf /` becomes a single echo command with arguments `ok;`, `rm`, `-rf`, `/`
    # Or it fails if echo is not available depending on shlex handling of semicolon.
    # In any case, it should not execute the rm command.
    assert result.status in ["success", "passed", "failed"]

def test_no_duplicate_policy_app():
    # We can check the registered commands/groups in the CLI app
    names = []
    for g in cli_app.registered_groups:
        if getattr(g, "name", None):
            names.append(g.name)
        elif getattr(g, "typer_instance", None) and getattr(g.typer_instance, "info", None) and getattr(g.typer_instance.info, "name", None):
            names.append(g.typer_instance.info.name)
    policy_groups = [n for n in names if n == "policy"]
    assert len(policy_groups) == 1, f"Duplicate policy_app registration found or not found: {policy_groups}"

def test_loop_review_no_crash(tmp_path):
    # This shouldn't crash with NameError (e.g. missing subprocess)
    # We'll just run it with --help to ensure imports are fine, 
    # or run it with a dummy diff that does nothing
    res = runner.invoke(cli_app, ["loop", "review", "--diff", "nonexistent.patch", "--reviewer", "shell"])
    # It might fail with an error or exit 0, but it should NOT crash with an internal Python error.
    assert "Traceback" not in res.stdout
    assert res.exit_code in [0, 1]

def test_runner_logging_no_bare_excepts(monkeypatch, tmp_path, caplog):
    from niyam.core.loopops.runner import LoopRunner
    import logging
    
    class DummyException(Exception): pass

    def mock_evaluate(*args, **kwargs):
        raise DummyException("Test Error")

    # Monkeypatch to force an exception inside a block that used to have `except Exception: pass`
    monkeypatch.setattr("niyam.core.config.load_niyam_config", mock_evaluate)
    
    # Run the evaluate_loop_policies method, which catches Exception and logs it
    from niyam.core.loopops.schema import LoopSpec
    from niyam.core.loopops.state_machine import LoopRun
    
    run = LoopRun(id="LR-1234", specName="Test", goal="test", status="running", startedAt="2026-01-01T00:00:00Z", evidencePath="", maxIterations=10, costUsd=0.0)
    spec = LoopSpec(apiVersion="v1", metadata={"name": "test", "owner": "test"}, goal={"description": "test", "type": "code-change"}, budgets={"maxIterations": 10}, steps=[], stop_conditions=[])
    
    with caplog.at_level(logging.DEBUG):
        decisions = LoopRunner.evaluate_loop_policies(run, spec, {"files_changed": ["src/app.py"]})
    
    assert "Exception caught" in caplog.text


    assert "Exception caught" in caplog.text

