import os
import subprocess
import sys
from pathlib import Path
import pytest
import yaml
from rich.console import Console
from niyam.cli import deprecated_sutra
from niyam.core.migrate import run_sutra_migration
from niyam.core.config import get_niyam_dir, find_niyam_root, load_niyam_config

def test_deprecated_sutra_warning(capsys) -> None:
    """deprecated_sutra should print warning/guidance and exit 0."""
    with pytest.raises(SystemExit) as excinfo:
        deprecated_sutra()
    
    assert excinfo.value.code == 0
    captured = capsys.readouterr()
    assert "Sutra has been renamed to Niyam" in captured.out
    assert "niyam migrate --from-sutra" in captured.out


def test_python_m_niyam_help() -> None:
    """python -m niyam --help should exit 0 and output Niyam help."""
    env = os.environ.copy()
    # Ensure current dir is in PYTHONPATH so it finds niyam package
    env["PYTHONPATH"] = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    res = subprocess.run(
        [sys.executable, "-m", "niyam", "--help"],
        capture_output=True,
        text=True,
        env=env
    )
    assert res.returncode == 0
    assert "Governed autonomous development for AI coding agents" in res.stdout or "niyam" in res.stdout.lower()


def test_niyam_migration_lifecycle(tmp_repo: Path) -> None:
    """niyam migrate --from-sutra should copy .sutra -> .niyam and update contents."""
    os.chdir(tmp_repo)
    
    # 1. Create a dummy .sutra structure
    sutra_dir = tmp_repo / ".sutra"
    sutra_dir.mkdir()
    
    sutra_yaml = sutra_dir / "sutra.yaml"
    sutra_yaml.write_text(yaml.dump({
        "version": "0.1.0",
        "project_name": "legacy-sutra-project",
        "profile": "fullstack",
        "runtimes": ["claude"],
        "guard": {"enabled": True}
    }), encoding="utf-8")
    
    # Nested folder and files
    agents_dir = sutra_dir / "agents"
    agents_dir.mkdir()
    agent_file = agents_dir / "backend-specialist.md"
    agent_file.write_text("Sutra backend specialist policies. Check `.sutra/context/`.", encoding="utf-8")
    
    # 2. Run migration (copy by default)
    console = Console(quiet=True)
    run_sutra_migration(force=False, move=False, console=console)
    
    # 3. Assertions
    # .sutra directory should still exist (copy by default)
    assert sutra_dir.is_dir()
    
    # .niyam directory should exist
    niyam_dir = tmp_repo / ".niyam"
    assert niyam_dir.is_dir()
    
    # Config should be renamed to niyam.yaml
    assert (niyam_dir / "niyam.yaml").exists()
    assert not (niyam_dir / "sutra.yaml").exists()
    
    # Configuration should be loaded correctly by config functions
    # (since we are in tmp_repo, find_niyam_root should find tmp_repo)
    assert find_niyam_root(tmp_repo) == tmp_repo
    config = load_niyam_config(tmp_repo)
    assert config.project_name == "legacy-niyam-project"
    
    # Internal references should be updated
    migrated_agent = niyam_dir / "agents" / "backend-specialist.md"
    assert migrated_agent.exists()
    content = migrated_agent.read_text(encoding="utf-8")
    assert "Niyam backend specialist policies. Check `.niyam/context/`." in content
    assert "Sutra" not in content
    assert ".sutra" not in content


def test_niyam_migration_fails_if_exists(tmp_repo: Path) -> None:
    """Migration should fail if .niyam/ already exists, unless force=True."""
    os.chdir(tmp_repo)
    
    # Create both .sutra/ and .niyam/
    sutra_dir = tmp_repo / ".sutra"
    sutra_dir.mkdir()
    (sutra_dir / "sutra.yaml").write_text("version: 0.1.0", encoding="utf-8")
    
    niyam_dir = tmp_repo / ".niyam"
    niyam_dir.mkdir()
    
    console = Console(quiet=True)
    with pytest.raises(SystemExit) as excinfo:
        run_sutra_migration(force=False, move=False, console=console)
    assert excinfo.value.code == 1
    
    # Should pass with force=True
    run_sutra_migration(force=True, move=False, console=console)
    assert (niyam_dir / "niyam.yaml").exists()


def test_niyam_migration_move(tmp_repo: Path) -> None:
    """Migration with move=True should delete the old .sutra/ directory."""
    os.chdir(tmp_repo)
    
    sutra_dir = tmp_repo / ".sutra"
    sutra_dir.mkdir()
    (sutra_dir / "sutra.yaml").write_text("version: 0.1.0", encoding="utf-8")
    
    console = Console(quiet=True)
    run_sutra_migration(force=False, move=True, console=console)
    
    # .sutra directory should not exist anymore
    assert not sutra_dir.exists()
    assert (tmp_repo / ".niyam" / "niyam.yaml").exists()
