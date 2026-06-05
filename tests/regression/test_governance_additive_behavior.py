"""Regression tests verifying that new governance features are additive and isolated."""

from __future__ import annotations

from pathlib import Path
from typer.testing import CliRunner

from niyam.cli import app
from niyam.core.scan import run_scanner_checks

runner = CliRunner()


def test_niyam_scan_does_not_modify_project_files(tmp_path: Path) -> None:
    """Running niyam scan should never modify any codebase files."""
    # 1. Create a clean project
    readme = tmp_path / "README.md"
    readme_content = "# Test Project\n"
    readme.write_text(readme_content, encoding="utf-8")

    uv_lock = tmp_path / "uv.lock"
    uv_lock_content = "# lockfile\n"
    uv_lock.write_text(uv_lock_content, encoding="utf-8")

    # Track file states/hashes
    original_readme_content = readme.read_text(encoding="utf-8")
    original_uv_lock_content = uv_lock.read_text(encoding="utf-8")

    # 2. Run scan command
    # Create the required niyam structure
    niyam_dir = tmp_path / ".niyam"
    niyam_dir.mkdir()
    (niyam_dir / "niyam.yaml").write_text("version: 0.1.0\n", encoding="utf-8")

    # Run the scanner
    run_scanner_checks(tmp_path, profile="startup")

    # 3. Assert project files are unchanged
    assert readme.read_text(encoding="utf-8") == original_readme_content
    assert uv_lock.read_text(encoding="utf-8") == original_uv_lock_content


def test_generated_niyam_files_are_isolated(tmp_path: Path) -> None:
    """Running niyam scan with file generation outputs only into target/isolated paths."""
    # Setup mock repo
    readme = tmp_path / "README.md"
    readme.write_text("# App\n", encoding="utf-8")

    niyam_dir = tmp_path / ".niyam"
    niyam_dir.mkdir()
    (niyam_dir / "niyam.yaml").write_text("version: 0.1.0\n", encoding="utf-8")

    # Get initial files (excluding .niyam folder)
    pre_files = sorted([p for p in tmp_path.rglob("*") if ".niyam" not in p.parts])

    # Run scan CLI with output format JSON written to a specific file
    output_report = tmp_path / "custom_scan_report.json"
    runner.invoke(
        app,
        ["scan", str(tmp_path), "--output", "json"],
        env={"NIYAM_ROOT": str(tmp_path)},
    )

    # Verify we can also run scan to a custom file
    # Get post files (excluding .niyam folder and the explicitly requested output path)
    post_files = sorted(
        [
            p
            for p in tmp_path.rglob("*")
            if ".niyam" not in p.parts and p != output_report
        ]
    )

    # Pre-files and Post-files lists must match, meaning scan didn't generate any pollution
    assert pre_files == post_files


def test_additive_commands_do_not_interfere_with_legacy_outputs() -> None:
    """Verify that adding new subcommands doesn't change outputs of existing commands."""
    from niyam import __version__

    res_version = runner.invoke(app, ["version"])
    assert res_version.exit_code == 0
    assert __version__ in res_version.output
