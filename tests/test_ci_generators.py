"""Tests for CI/CD generator templates."""

from pathlib import Path
from rich.console import Console

from niyam.core.ci_generators import generate_ci_integration


def test_generate_github_actions(tmp_path: Path):
    console = Console(quiet=True)
    success = generate_ci_integration("github", tmp_path, console)
    
    assert success
    target_file = tmp_path / ".github" / "workflows" / "niyam-verification.yml"
    assert target_file.exists()
    
    content = target_file.read_text(encoding="utf-8")
    assert "name: Niyam Governance & Quality Gates" in content
    assert "syft . -o spdx-json=sbom.spdx.json" in content
    assert "actions/attest-build-provenance@v1" in content
    assert "cosign sign-blob" in content
    assert "ossf/scorecard-action" in content


def test_generate_azure_devops(tmp_path: Path):
    console = Console(quiet=True)
    success = generate_ci_integration("azure", tmp_path, console)
    
    assert success
    target_file = tmp_path / "azure-pipelines.yml"
    assert target_file.exists()
    
    content = target_file.read_text(encoding="utf-8")
    assert "niyam ci verify" in content
    assert "syft . -o spdx-json=$(System.DefaultWorkingDirectory)/sbom.spdx.json" in content
    assert "cosign sign-blob" in content


def test_generate_azure_devops_exists(tmp_path: Path):
    console = Console(quiet=True)
    
    existing = tmp_path / "azure-pipelines.yml"
    existing.write_text("dummy", encoding="utf-8")
    
    success = generate_ci_integration("azure", tmp_path, console)
    
    assert success
    target_file = tmp_path / "niyam-azure-pipelines.yml"
    assert target_file.exists()
    
    content = target_file.read_text(encoding="utf-8")
    assert "niyam ci verify" in content


def test_generate_gitlab_ci(tmp_path: Path):
    console = Console(quiet=True)
    success = generate_ci_integration("gitlab", tmp_path, console)
    
    assert success
    target_file = tmp_path / ".gitlab-ci.yml"
    assert target_file.exists()
    
    content = target_file.read_text(encoding="utf-8")
    assert "syft" in content
    assert "niyam ci verify" in content


def test_generate_unsupported(tmp_path: Path):
    console = Console(quiet=True)
    success = generate_ci_integration("unsupported", tmp_path, console)
    assert not success
