# Integrating Niyam with Azure DevOps Pipelines

This guide explains how to set up `niyam scan` as a pull request quality gate and static analysis reporting tool in Azure Pipelines (`azure-pipelines.yml`).

## 1. Basic Pull Request Gate

This pipeline runs on every PR target branch merge, failing the build if any `high` or `critical` severity findings are detected:

```yaml
trigger: none
pr:
  branches:
    include:
      - main
      - dev

jobs:
- job: GovernanceScan
  displayName: 'Niyam Governance Scan'
  pool:
    vmImage: 'ubuntu-latest'
  steps:
  - task: UsePythonVersion@0
    inputs:
      versionSpec: '3.11'
    displayName: 'Use Python 3.11'

  - script: |
      python -m pip install --upgrade pip
      pip install niyam-dev
    displayName: 'Install Niyam'

  - script: |
      niyam scan . --profile enterprise --fail-on high --report-file $(Build.ArtifactStagingDirectory)/niyam-report.md
    displayName: 'Run Niyam Scan'

  - task: PublishBuildArtifacts@1
    inputs:
      PathtoPublish: '$(Build.ArtifactStagingDirectory)/niyam-report.md'
      ArtifactName: 'niyam-readiness-report'
      publishLocations: 'Container'
    displayName: 'Publish Scan Report'
    condition: always()
```

## 2. Using Baselines to Prevent Failure on Legacy Code

For existing repositories with known legacy issues, run with a baseline so only new findings trigger build failures:

```yaml
  - script: |
      niyam scan . --profile enterprise --baseline .niyam/baseline.json --fail-on high
    displayName: 'Run Niyam Scan with Baseline'
```

## 3. Azure DevOps Security Tab / SARIF Integration

If you have GitHub Advanced Security for Azure DevOps enabled, you can output findings in SARIF format and upload them to the code analysis tab:

```yaml
  - script: |
      niyam scan . --output sarif --report-file $(Build.ArtifactStagingDirectory)/niyam-findings.sarif
    displayName: 'Run Niyam Scan (SARIF)'

  # Upload SARIF file using Microsoft's advanced security upload task
  - task: AdvancedSecurity-Publish@1
    inputs:
      SarifFile: '$(Build.ArtifactStagingDirectory)/niyam-findings.sarif'
    displayName: 'Publish SARIF findings'
```
