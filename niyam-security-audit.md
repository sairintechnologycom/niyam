# Security Audit Report: Niyam Governance Suite

**Date:** June 10, 2026  
**Auditor:** security-auditor  
**Project:** Niyam (formerly Sutra)  
**Status:** DRAFT - HIGH SEVERITY FINDINGS

---

## 1. Executive Summary
A comprehensive security audit was performed on the Niyam project, focusing on its local-first governance and safety guardrails. While the architecture is well-documented, several critical flaws were identified that allow for total bypass of the governance engine, arbitrary code execution, and tampering with audit trails.

**Overall Risk Rating: CRITICAL**

---

## 2. Detailed Findings

### FINDING-001: Unauthenticated Mission/Task Approval via API Portal
- **Severity:** Critical
- **Description:** The FastAPI backend (`niyam/api/server.py`) lack any form of authentication or authorization. Critical endpoints like `/missions/{id}/approve` and `/missions/{id}/tasks/{id}/approve` permit anyone with network access to the server to approve malicious missions or tasks.
- **Impact:** Total bypass of "Human-in-the-loop" governance. An agent or external actor can self-approve destructive actions.
- **Evidence:** `niyam/api/server.py` implements approval by writing directly to `approval.json` without verifying the caller's identity.

### FINDING-002: Arbitrary Code Execution via Allowed Interpreters
- **Severity:** High
- **Description:** The `ALLOWED_VALIDATION_EXECUTABLES` and the default guard policy allow full-featured programming languages like `python` and `node`.
- **Impact:** Agents can write malicious scripts to the repository and execute them via `niyam guard run -- python malicious.py`, effectively bypassing all specific command restrictions (e.g., `rm` blocks).
- **Evidence:** `niyam/core/security.py` includes `python` and `node` in the allowlist. Verified via PoC: `niyam guard run --mode block -- python -c "..."` executes successfully.

### FINDING-003: Path Freeze Implementation Bypass & Configuration Mismatch
- **Severity:** High
- **Description:**
    1.  The `niyam guard freeze` command updates legacy `GuardState` config, which is ignored by the modern `GuardConfig` used in `run_guard_run`.
    2.  The path checking logic (`_is_protected_file_match`) uses a simple suffix match on arguments, which is trivial to bypass.
- **Impact:** Frozen directories are not actually protected from modification by the modern execution engine.
- **Evidence:** `niyam/policies/guard.py:run_guard_run` ignores `config.guard.frozen_paths`. Verified via PoC: modifying a "frozen" file using `python` is permitted.

### FINDING-004: Cryptographic Integrity Bypass (Signature Stripping)
- **Severity:** High
- **Description:** The verification engine (`run_verify_report`) only checks the cryptographic signature if the manifest explicitly contains `"signed": true`.
- **Impact:** An attacker who has modified the evidence files can simply set `"signed": false` in the manifest to bypass signature verification. The tool will then only verify hashes, which the attacker can also update.
- **Evidence:** `niyam/mission/reporter.py` line 456.

---

## 3. Remediation Roadmap

### Immediate Actions (High Priority)
1.  **API Hardening:** Add a local-only authentication token to the FastAPI server. Ensure it binds only to `127.0.0.1` unless explicitly overridden with a warning.
2.  **Unified Configuration:** Merge `GuardState` and `GuardConfig` to ensure `freeze` and `careful` settings are respected by all execution paths.
3.  **Strict Integrity:** Modify `ci verify` to require a valid signature for any report claiming "passed" status, regardless of the `"signed"` flag in the manifest.

### Medium-Term Actions
1.  **Restricted Execution:** Implement a more robust sandbox for validation tasks, or restrict `python`/`node` usage to specific, pre-approved scripts.
2.  **Robust Path Matching:** Use absolute path resolution and prefix checking for all file-related guardrails to prevent traversal and suffix-match bypasses.
3.  **Enhanced Redaction:** Implement positional argument redaction for sensitive commands.
