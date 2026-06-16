# Integrating Niyam with GitHub Actions

This guide explains how to set up Niyam as a quality and evidence gate in GitHub Actions.

## 1. Using the Hardened Verification Template

The recommended way to integrate Niyam is by generating the hardened workflow. This template enforces Niyam policies, performs OpenSSF Scorecard analysis, generates an SBOM, signs the evidence cryptographically, and attests SLSA provenance.

To generate the template, run:
```bash
niyam ci generate github
```

This will create `.github/workflows/niyam-verification.yml`. 

### Key Features of the Hardened Template:
- **Niyam Verification:** Runs `niyam ci verify --strict` against the target branch.
- **Scorecard Analysis:** Runs `ossf/scorecard-action` and uploads results.
- **SBOM Generation:** Uses `syft` to create an `sbom.spdx.json`.
- **Cryptographic Signing:** Uses Sigstore's `cosign` to keyless-sign the Niyam Evidence Pack and SBOM.
- **SLSA Provenance:** Uses `actions/attest-build-provenance` to guarantee artifact integrity.

## 2. GitHub Security Upload (SARIF)

If you are using GitHub Advanced Security, Niyam outputs findings in SARIF format, which integrates directly with the GitHub Security tab:

```yaml
      - name: Run OpenSSF Scorecard Analysis
        uses: ossf/scorecard-action@v2.3.1
        with:
          results_file: scorecard-results.sarif
          results_format: sarif
          publish_results: true
          
      # Upload SARIF file
      - name: "Upload to code-scanning"
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: scorecard-results.sarif
```

## 3. Legacy Support: Manual Script Gates

If you prefer to run the CLI manually for backward compatibility, you can use the following steps:

```yaml
      - name: Run Niyam scan with Baseline
        run: |
          pip install niyam
          niyam scan . --profile enterprise --baseline .niyam/baseline.json --fail-on high
```
