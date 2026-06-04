from typer.testing import CliRunner
from niyam.cli import app

runner = CliRunner()


def test_info_command_exists():
    """Test that 'niyam info' command is available."""
    result = runner.invoke(app, ["info", "--help"])
    assert result.exit_code == 0
    assert "Display system and workspace information" in result.stdout


def test_info_output_contains_versions():
    """Test that 'niyam info' output contains version info."""
    result = runner.invoke(app, ["info"])
    # This should fail initially until the command is implemented
    assert result.exit_code == 0
    assert "Niyam Version" in result.stdout
    assert "Python Version" in result.stdout
    assert "OS" in result.stdout
