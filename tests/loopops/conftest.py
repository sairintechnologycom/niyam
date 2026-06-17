import pytest
from pathlib import Path

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
