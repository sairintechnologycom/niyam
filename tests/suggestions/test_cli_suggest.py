from typer.testing import CliRunner
from niyam.__main__ import app

runner = CliRunner()

def test_suggest_cli_command():
    result = runner.invoke(app, ["suggest", "loop "])
    assert result.exit_code == 0
    assert "run" in result.stdout
    assert "report" in result.stdout

def test_suggest_cli_command_prefix():
    result = runner.invoke(app, ["suggest", "loop r"])
    assert result.exit_code == 0
    assert "run" in result.stdout
    assert "report" in result.stdout
    assert "review" in result.stdout
    assert "init" not in result.stdout

def test_unknown_command_did_you_mean():
    import subprocess
    import sys
    # Calling an unknown command should print did you mean
    result = subprocess.run(
        [sys.executable, "-m", "niyam", "lop"],
        capture_output=True,
        text=True
    )
    # Typer returns 2 for unknown commands
    assert result.returncode == 2
    # Our custom suggestion handler prints to stdout via rich console
    assert "Unknown command 'lop'" in result.stdout
    assert "Did you mean:" in result.stdout
    assert "loop" in result.stdout
    assert "Example usage:" in result.stdout

def test_completion_script():
    result = runner.invoke(app, ["completion", "script", "--shell", "bash"])
    assert result.exit_code == 0
    assert "_niyam_completion()" in result.stdout
