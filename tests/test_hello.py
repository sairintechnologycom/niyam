from typer.testing import CliRunner
from sutra.cli import app

runner = CliRunner()


def test_hello_no_args():
    result = runner.invoke(app, ["hello"])
    assert result.exit_code == 0
    assert "Hello, Sutra Developer!" in result.stdout


def test_hello_with_name():
    result = runner.invoke(app, ["hello", "--name", "TestUser"])
    assert result.exit_code == 0
    assert "Hello, TestUser!" in result.stdout
