# Integrating Niyam with Azure DevOps Pipelines

This guide explains how to set up Niyam as a quality and evidence gate in Azure Pipelines.

## 1. Using the Hardened Verification Template

The recommended way to integrate Niyam is by generating the hardened workflow. This template installs Niyam, generates an SBOM, signs the evidence cryptographically using Cosign, and publishes the pipeline artifacts.

To generate the template, run:
```bash
niyam ci generate azure
```

This will create `azure-pipelines.yml`.

### Key Features of the Hardened Template:
- **Niyam Verification:** Runs `niyam ci verify --strict` against the target branch.
- **SBOM Generation:** Uses `syft` to create an `sbom.spdx.json`.
- **Cryptographic Signing:** Uses `cosign` (with environment variables `COSIGN_PRIVATE_KEY` and `COSIGN_PASSWORD`) to sign the Niyam Evidence Pack and SBOM.
- **Artifact Publishing:** Automatically attaches the signed Evidence Pack and SBOM to the Azure Pipeline run.

## 2. Azure DevOps Security Tab / SARIF Integration

If you have GitHub Advanced Security for Azure DevOps enabled, Niyam outputs findings in SARIF format, which can be uploaded to the code analysis tab:

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

## 3. Legacy Support: Manual Script Gates

If you prefer to run the CLI manually with baselines for backward compatibility:

```yaml
  - script: |
      niyam scan . --profile enterprise --baseline .niyam/baseline.json --fail-on high
    displayName: 'Run Niyam Scan with Baseline'
```
