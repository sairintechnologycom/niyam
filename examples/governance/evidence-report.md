# Niyam Governance & Production Readiness Evidence Report

## 1. Executive Summary
This document serves as an audit-ready evidence record for the repository readiness and AI agent governance. It aggregates static analysis, dependency health, and runtime agent execution safety logs.

## 2. Project Metadata
* **Project Name:** niyam
* **Generated At:** 2026-06-09 03:26 UTC
* **Git Branch / Commit:** `Branch: main, Commit: c965efd`


## 3. Readiness Score
* **Readiness Score:** **100/100**

### Readiness Score Breakdown
| Dimension | Weight | Score |
| --- | --- | --- |
| Secrets | 20% | 20/20 |
| Auth | 15% | 15/15 |
| Dependencies | 15% | 15/15 |
| Cloud | 15% | 15/15 |
| Production Ops | 10% | 10/10 |
| Ai Risk | 10% | 10/10 |
| Data Protection | 10% | 10/10 |
| Documentation | 5% | 5/5 |

| **Total** | **100%** | **100/100** |

## 4. Launch Decision
* **Launch Decision:** **GO**

## 5. Decision Reason
* **Decision Reason:** *Scan completed successfully.*

## 6. Critical and High Findings

| ID | Title | Category | Severity | File Path |
| --- | --- | --- | --- | --- |
| MCP-filesystem | Unapproved High-Risk Tool: filesystem | mcp | **HIGH** | `Global` |



## 7. Risk Register

| Severity | Count |
| --- | --- |
| Critical | 0 |
| High | 1 |
| Medium | 0 |
| Low | 0 |
| Info | 0 |


## 8. Recommended Remediation Plan

Remediation actions are recommended below:
* **[MCP-filesystem] Unapproved High-Risk Tool: filesystem** (HIGH): Approve the tool using 'niyam mcp approve filesystem' if it is safe to use.




## 9. AI-Assisted Development Governance Notes
* **AI-Risk Placeholders / Commented Assertions:** Checked.
* **Agent Governance / Guardrails Status:** Disabled
### Agent Governance Summary (Niyam Guard)
* **Total Actions:** 1
* **Total Blocked:** 0
* **Total Warned:** 0
* **Total Approval Required:** 0
* **Total Failed:** 0
* **Top Command Categories:** echo (1)

#### Latest Session Details
* **Session ID:** `main-a92c5eb6-45ea-415d-a1b1-f4c9e3ad54c1`
* **Session Total Actions:** 1
* **Session Blocked:** 0
* **Session Warned:** 0
* **Session Failed:** 0

### Recent Observed Actions (Agent Governance)
| Timestamp | Actor | Command | Policy Decision | Exit Code |
| --- | --- | --- | --- | --- |
| 2026-06-08T11:56:18.479813Z | unknown | `echo hello from guard` | allow | 0 |



* **MCP / Tool Approval Posture:** 1/2 tools approved.
  * **Total Registered Tools:** 2
  * **Approved Tools:** 1
  * **Unapproved Tools:** 1
  * **High-risk Tools:** 1
  * **Critical-risk Tools:** 0
  * **High/Critical Unapproved Tools:** 1


### Registered Tools (MCP)
| Name | Type | Risk Level | Approved | Owner |
| --- | --- | --- | --- | --- |
| filesystem | mcp_server | **HIGH** | No | N/A |
| docs-search | mcp_server | **MEDIUM** | Yes | N/A |




### Recommended MCP Actions
* **[filesystem]** Approve tool 'filesystem' (Risk: high) via 'niyam mcp approve filesystem'.


* **AI Engineering Cost Summary:** Estimated Cost: $0.0675 (Input tokens: 10000, Output tokens: 2500)

## 10. Appendix Summary
* **Redaction Status:** Redacted: True (Engine: niyam-redaction)
* **Branch:** `main`
* **Commit SHA:** `c965efd`
* **Commit Author:** Bhushan