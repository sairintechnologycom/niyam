# Evidence Report — my-sample-app

**Project:** my-sample-app
**Branch:** `main`
**Last Commit:** `a7b8c9d1e2f3a7b8c9d1e2f3a7b8c9d1e2f3a7b8` by Developer
**Generated At:** 2026-06-04 10:45 UTC

---

## 1. Executive Summary
This document serves as an audit-ready evidence record for the repository readiness and AI agent governance.

Included sections:
 * Production Readiness
 * Agent Governance Activity
 * Tool/MCP Risk Posture
 * AI Engineering Cost Summary

---

## 2. Production Readiness

| Metric | Status / Value |
| --- | --- |
| **Readiness Score** | **89/100** |
| **Launch Decision** | **GO** |
| **Total Findings** | 2 |

### Findings Breakdown
* **Critical:** 0
* **High:** 0
* **Medium:** 1
* **Low:** 1
* **Info:** 0

### Launch Decision details
Based on the readiness score of **89**, the automated gate recommends:

🟢 **GO**: The project meets all standard readiness guidelines and is safe for production deployment.

---

## 3. Agent Governance Activity

* **Guardrails Status:** Enabled
* **Careful Mode:** Enabled
* **Frozen Paths:** `['src/components', 'src/utils']`

### Recent Observed Actions (Guard Logs)

| Timestamp | Actor | Command | Exit Code | Duration (ms) |
| --- | --- | --- | --- | --- |
| 2026-06-04T10:01:00Z | agent | `git checkout main` | 0 | 150 |
| 2026-06-04T10:02:15Z | agent | `npm install` | 0 | 3500 |
| 2026-06-04T10:05:00Z | agent | `npm run test` | 0 | 1250 |
| 2026-06-04T10:07:30Z | agent | `python script.py --key REDACTED` | 0 | 480 |

---

## 4. Tool/MCP Risk Posture

* **Total Registered Tools:** 4
* **Approved Tools:** 3
* **Unapproved Tools:** 1

### Registered Tools Risk Breakdown

| Name | Type | Risk Level | Approved | Owner |
| --- | --- | --- | --- | --- |
| filesystem | mcp_server | **HIGH** | Yes | Niyam Team |
| shell-executor | cli | **CRITICAL** | No | System |
| slack-api | api | **MEDIUM** | Yes | DevOps Team |
| web-search | api | **LOW** | Yes | Search Specialist |

---

## 5. AI Engineering Cost Summary

* **Total Estimated Cost:** **$0.2095**
* **Total Input Tokens:** 38,000
* **Total Output Tokens:** 8,300

### Cost Breakdown by Day

| Day | Estimated Cost |
| --- | --- |
| 2026-06-04 | $0.2095 |

---

## 6. Policy Violations or Blocked Actions

✓ No policy violations or blocked actions detected.

---

## 7. Recommended Next Actions

Remediation actions are recommended below:

* **[Readiness] [DEP001] Missing Dependency Lockfile** (MEDIUM): Install dependencies using npm or yarn to generate a lockfile, then commit it to the repository.
* **[Readiness] [TST001] Missing Test Suite** (LOW): Initialize a test directory (such as tests/) and write basic verification tests for your components.
* **[Tool Governance] Approve High-Risk Tool**: Tool `shell-executor` has **CRITICAL** risk and needs review/approval.

---

## 8. Audit Appendix
This appendix contains cryptographic metadata and environment info for verification.

* **Git Last Commit:** `a7b8c9d1e2f3a7b8c9d1e2f3a7b8c9d1e2f3a7b8`
* **Git Author:** Developer
* **Timestamp (UTC):** 2026-06-04 10:45 UTC
