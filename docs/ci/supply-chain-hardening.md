# Supply-Chain Hardening & SLSA Alignment

Niyam ensures that AI-generated code is not only governed during development but also securely verified when entering your supply chain. This document explains how Niyam aligns with industry-standard supply-chain frameworks like OpenSSF Scorecard and SLSA (Supply-chain Levels for Software Artifacts).

## OpenSSF Scorecard Integration

The OpenSSF Scorecard assesses the security posture of open source and internal repositories by running a series of automated checks.

Niyam integrates deeply with the Scorecard methodology:
- **Hardened Templates:** When you generate a CI pipeline using `niyam ci generate github`, the resulting GitHub Actions workflow automatically includes the `ossf/scorecard-action`.
- **Pre-Commit Checks:** The `niyam ci verify` command performs many of the same conceptual checks as the Scorecard locally (e.g., detecting secrets, checking for dangerous code patterns, ensuring required approvals are met) before code is even pushed.
- **SARIF Outputs:** Both Niyam's own scanners and the OpenSSF Scorecard export findings in the standard SARIF format, which unifies vulnerability reporting in GitHub Advanced Security and Azure DevOps.

## SLSA Provenance

SLSA (Supply-chain Levels for Software Artifacts) is a security framework that prevents tampering, improves integrity, and secures packages and infrastructure in your projects.

Niyam helps projects achieve SLSA compliance by:
1.  **Providing Evidence Packs:** Every Niyam mission produces an `evidence.md` file that cryptographically proves which AI agent ran, what files were touched, and what approvals were granted.
2.  **SBOM Generation:** The hardened CI templates automatically run `syft` to generate a Software Bill of Materials (`sbom.spdx.json`).
3.  **Attesting Build Provenance:** By including `actions/attest-build-provenance` in the hardened GitHub Actions template, we bind the Niyam evidence pack and the SBOM to the OIDC identity of the GitHub Actions runner. This satisfies the SLSA Level 3 requirement for unforgeable build provenance.

## Cryptographic Artifact Signing (Cosign)

To prevent man-in-the-middle attacks where an attacker might tamper with the AI-generated code or the evidence pack after the fact, Niyam's CI templates use **Sigstore's Cosign**.

-   **Keyless Signing (GitHub Actions):** We use OIDC to perform keyless signing of the `evidence.md` and the SBOM. This means the artifacts are cryptographically bound to the specific CI pipeline execution.
-   **Key-Based Signing (Azure DevOps / GitLab):** We use injected environment variables (`COSIGN_PRIVATE_KEY`) to sign the evidence packs before they are uploaded as pipeline artifacts.

## Summary of Hardened Flow

When you run `niyam ci generate <provider>`, Niyam scaffolds a pipeline that:
1.  **Verifies:** Runs `niyam ci verify --strict` to ensure all local governance checks pass.
2.  **Scores:** Executes OpenSSF Scorecard analysis (if on GitHub).
3.  **Inventories:** Generates an SBOM via Syft.
4.  **Signs:** Signs the evidence and SBOM using Cosign.
5.  **Attests:** Attests the build provenance using SLSA tools.
6.  **Uploads:** Safely stores the artifacts for future audits.
