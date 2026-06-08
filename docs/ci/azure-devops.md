# Integrating Niyam with Azure DevOps Pipelines

This guide explains how to set up `niyam scan` as a pull request quality gate and static analysis reporting tool in Azure Pipelines (`azure-pipelines.yml`).

## 1. Using the Official Niyam Azure DevOps Task

The easiest way to integrate Niyam is using the official extension. This automatically handles Niyam installation and readiness score verification.

```yaml
trigger: none
pr:
  branches:
    include:
      - main

jobs:
- job: GovernanceVerify
  displayName: 'Niyam Governance Verify'
  pool:
    vmImage: 'ubuntu-latest'
  steps:
  - task: NiyamVerify@0
    inputs:
      targetBranch: 'main'
      minScore: 70
      strict: true
      publicKey: $(NIYAM_PUBLIC_KEY)
    displayName: 'Run Niyam Governance Verify'
```

## 2. Basic Pull Request Gate (Manual Script)

If you prefer to run the CLI manually, you can use the following steps:

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
