"""CI/CD Integration Generators for Niyam."""

from __future__ import annotations

import os
from pathlib import Path
from rich.console import Console

GITHUB_ACTIONS_TEMPLATE = """name: Niyam Governance & Quality Gates

on:
  pull_request:
    branches: [ "main", "master" ]
  push:
    branches: [ "main", "master" ]

permissions:
  contents: read
  id-token: write
  attestations: write

jobs:
  niyam-verification:
    name: Verify AI Development Evidence
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0 # Need full history for git diff against target branch

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          
      - name: Install Niyam CLI and SBOM Tool
        run: |
          pip install niyam
          curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin

      - name: Run Niyam Verification
        id: verify
        run: |
          niyam ci verify --target ${{ github.base_ref || 'main' }} --strict
        env:
          NIYAM_PUBLIC_KEY: ${{ secrets.NIYAM_PUBLIC_KEY }}

      - name: Generate SBOM
        run: |
          syft . -o spdx-json=sbom.spdx.json

      - name: Attest Build Provenance
        uses: actions/attest-build-provenance@v1
        with:
          subject-path: 'sbom.spdx.json'

      - name: Upload Evidence Artifacts
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: niyam-evidence
          path: |
            .niyam/runs/**/evidence.md
            .niyam/runs/**/mission-plan.yaml
            sbom.spdx.json
          retention-days: 14
"""

AZURE_DEVOPS_TEMPLATE = """trigger:
  - main
  - master

pr:
  - main
  - master

pool:
  vmImage: 'ubuntu-latest'

steps:
- checkout: self
  fetchDepth: 0 # Need full history for git diff against target branch

- task: UsePythonVersion@0
  inputs:
    versionSpec: '3.11'
    addToPath: true

- script: |
    pip install niyam
  displayName: 'Install Niyam CLI'

- script: |
    TARGET_BRANCH=$(System.PullRequest.TargetBranch)
    if [ -z "$TARGET_BRANCH" ]; then
      TARGET_BRANCH="main"
    else
      # Strip refs/heads/ from target branch if present
      TARGET_BRANCH=${TARGET_BRANCH#refs/heads/}
    fi
    niyam ci verify --target $TARGET_BRANCH --strict
  displayName: 'Run Niyam Verification'
  env:
    NIYAM_PUBLIC_KEY: $(NIYAM_PUBLIC_KEY)

- task: PublishPipelineArtifact@1
  condition: always()
  inputs:
    targetPath: '$(System.DefaultWorkingDirectory)/.niyam/runs'
    artifact: 'NiyamEvidence'
    publishLocation: 'pipeline'
  displayName: 'Publish Niyam Evidence Artifacts'
"""

GITLAB_CI_TEMPLATE = """stages:
  - verify

niyam-verification:
  stage: verify
  image: python:3.11
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
  variables:
    GIT_DEPTH: 0 # Need full history for git diff against target branch
  script:
    - pip install niyam
    - TARGET_BRANCH=${CI_MERGE_REQUEST_TARGET_BRANCH_NAME:-$CI_DEFAULT_BRANCH}
    - niyam ci verify --target $TARGET_BRANCH --strict
"""

def generate_ci_integration(provider: str, repo_root: Path, console: Console) -> bool:
    """Generate CI/CD pipeline files for the specified provider."""
    provider = provider.lower()
    success = False

    if provider in ["github", "github-actions"]:
        target_dir = repo_root / ".github" / "workflows"
        target_dir.mkdir(parents=True, exist_ok=True)
        target_file = target_dir / "niyam-verification.yml"
        
        target_file.write_text(GITHUB_ACTIONS_TEMPLATE, encoding="utf-8")
        console.print(f"[bold green]✓[/] Generated GitHub Actions workflow at: [cyan]{target_file.relative_to(repo_root)}[/]")
        success = True

    elif provider in ["azure", "azure-devops", "ado"]:
        target_file = repo_root / "azure-pipelines.yml"
        
        # If one already exists, maybe don't overwrite blindly
        if target_file.exists():
            console.print(f"[yellow]⚠ Warning:[/] [cyan]azure-pipelines.yml[/] already exists. Writing to [cyan]niyam-azure-pipelines.yml[/] instead.")
            target_file = repo_root / "niyam-azure-pipelines.yml"
            
        target_file.write_text(AZURE_DEVOPS_TEMPLATE, encoding="utf-8")
        console.print(f"[bold green]✓[/] Generated Azure DevOps pipeline at: [cyan]{target_file.relative_to(repo_root)}[/]")
        success = True

    elif provider in ["gitlab", "gitlab-ci"]:
        target_file = repo_root / ".gitlab-ci.yml"
        
        if target_file.exists():
            console.print(f"[yellow]⚠ Warning:[/] [cyan].gitlab-ci.yml[/] already exists. Writing to [cyan]niyam-gitlab-ci.yml[/] instead.")
            target_file = repo_root / "niyam-gitlab-ci.yml"
            
        target_file.write_text(GITLAB_CI_TEMPLATE, encoding="utf-8")
        console.print(f"[bold green]✓[/] Generated GitLab CI pipeline at: [cyan]{target_file.relative_to(repo_root)}[/]")
        success = True

    else:
        console.print(f"[bold red]❌ Error:[/] Unsupported CI provider: '{provider}'. Supported providers: github, azure, gitlab.")

    return success
