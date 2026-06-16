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
  id-token: write      # Required for SLSA and OIDC provenance
  attestations: write  # Required for GitHub artifact attestations
  security-events: write # Required for SARIF upload (OpenSSF Scorecard)

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
          
      - name: Install Niyam CLI and Security Tools
        run: |
          pip install niyam
          curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin
          # Install cosign for artifact signing
          curl -O -L "https://github.com/sigstore/cosign/releases/latest/download/cosign-linux-amd64"
          sudo mv cosign-linux-amd64 /usr/local/bin/cosign
          sudo chmod +x /usr/local/bin/cosign

      - name: Run Niyam Verification (Hardened Gate)
        id: verify
        run: |
          niyam ci verify --target ${{ github.base_ref || 'main' }} --strict
        env:
          NIYAM_PUBLIC_KEY: ${{ secrets.NIYAM_PUBLIC_KEY }}

      - name: Run OpenSSF Scorecard Analysis
        uses: ossf/scorecard-action@v2.3.1
        with:
          results_file: scorecard-results.sarif
          results_format: sarif
          publish_results: true

      - name: Generate SBOM (Supply Chain Hardening)
        run: |
          syft . -o spdx-json=sbom.spdx.json

      - name: Sign Niyam Evidence and SBOM (Cosign Keyless)
        run: |
          # Keyless signing of evidence packs
          for evidence in $(find .niyam/runs -name 'evidence.md'); do
            cosign sign-blob --yes $evidence > ${evidence}.sig
          done
          cosign sign-blob --yes sbom.spdx.json > sbom.spdx.json.sig

      - name: Attest Build Provenance (SLSA Level 3)
        uses: actions/attest-build-provenance@v1
        with:
          subject-path: 'sbom.spdx.json'

      - name: Upload Hardened Evidence Artifacts
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: niyam-evidence
          path: |
            .niyam/runs/**/evidence.md
            .niyam/runs/**/evidence.md.sig
            .niyam/runs/**/mission-plan.yaml
            sbom.spdx.json
            sbom.spdx.json.sig
            scorecard-results.sarif
          retention-days: 90
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
    # Install Syft for SBOM generation
    curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin
    # Install Cosign for artifact signing
    curl -O -L "https://github.com/sigstore/cosign/releases/latest/download/cosign-linux-amd64"
    sudo mv cosign-linux-amd64 /usr/local/bin/cosign
    sudo chmod +x /usr/local/bin/cosign
  displayName: 'Install Niyam CLI and Security Tools'

- script: |
    TARGET_BRANCH=$(System.PullRequest.TargetBranch)
    if [ -z "$TARGET_BRANCH" ]; then
      TARGET_BRANCH="main"
    else
      TARGET_BRANCH=${TARGET_BRANCH#refs/heads/}
    fi
    niyam ci verify --target $TARGET_BRANCH --strict
  displayName: 'Run Niyam Verification (Hardened Gate)'
  env:
    NIYAM_PUBLIC_KEY: $(NIYAM_PUBLIC_KEY)

- script: |
    syft . -o spdx-json=$(System.DefaultWorkingDirectory)/sbom.spdx.json
  displayName: 'Generate SBOM (Supply Chain Hardening)'

- script: |
    # Sign evidence artifacts if keys are available
    if [ -n "$(COSIGN_PRIVATE_KEY)" ]; then
      for evidence in $(find .niyam/runs -name 'evidence.md'); do
        cosign sign-blob --key env://COSIGN_PRIVATE_KEY $evidence > ${evidence}.sig
      done
      cosign sign-blob --key env://COSIGN_PRIVATE_KEY $(System.DefaultWorkingDirectory)/sbom.spdx.json > $(System.DefaultWorkingDirectory)/sbom.spdx.json.sig
    fi
  displayName: 'Sign Niyam Evidence and SBOM'
  env:
    COSIGN_PRIVATE_KEY: $(COSIGN_PRIVATE_KEY)
    COSIGN_PASSWORD: $(COSIGN_PASSWORD)

- task: PublishPipelineArtifact@1
  condition: always()
  inputs:
    targetPath: '$(System.DefaultWorkingDirectory)/.niyam/runs'
    artifact: 'NiyamEvidence'
    publishLocation: 'pipeline'
  displayName: 'Publish Niyam Evidence Artifacts'

- task: PublishPipelineArtifact@1
  condition: always()
  inputs:
    targetPath: '$(System.DefaultWorkingDirectory)/sbom.spdx.json'
    artifact: 'SBOM'
    publishLocation: 'pipeline'
  displayName: 'Publish SBOM Artifact'
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
    - curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin
    - TARGET_BRANCH=${CI_MERGE_REQUEST_TARGET_BRANCH_NAME:-$CI_DEFAULT_BRANCH}
    - niyam ci verify --target $TARGET_BRANCH --strict
    - syft . -o spdx-json=sbom.spdx.json
  artifacts:
    paths:
      - .niyam/runs/**/evidence.md
      - .niyam/runs/**/mission-plan.yaml
      - sbom.spdx.json
    expire_in: 14 days
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
        console.print(f"[bold green]✓[/] Generated Hardened GitHub Actions workflow at: [cyan]{target_file.relative_to(repo_root)}[/]")
        success = True

    elif provider in ["azure", "azure-devops", "ado"]:
        target_file = repo_root / "azure-pipelines.yml"
        
        # If one already exists, maybe don't overwrite blindly
        if target_file.exists():
            console.print(f"[yellow]⚠ Warning:[/] [cyan]azure-pipelines.yml[/] already exists. Writing to [cyan]niyam-azure-pipelines.yml[/] instead.")
            target_file = repo_root / "niyam-azure-pipelines.yml"
            
        target_file.write_text(AZURE_DEVOPS_TEMPLATE, encoding="utf-8")
        console.print(f"[bold green]✓[/] Generated Hardened Azure DevOps pipeline at: [cyan]{target_file.relative_to(repo_root)}[/]")
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
