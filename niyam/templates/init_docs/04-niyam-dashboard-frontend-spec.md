# Dashboard & Frontend Specification: Niyam Governance Portal

## 1. Design System & Aesthetics
The Niyam Governance Portal is a high-fidelity local dashboard designed to visualize readiness scores, audit trails, and token cost summaries. It features a premium, responsive dark-mode design system.

### Color Tokens (Hex / HSL)
* **Background Deep:** `#090D16` / `hsl(222, 40%, 6%)`
* **Surface Card (Frosted Glass):** `#111827` / `hsl(223, 30%, 11%)` (with `backdrop-filter: blur(16px)` and border `1px solid rgba(255,255,255,0.06)`)
* **Primary Blue:** `#3B82F6` / `hsl(217, 91%, 60%)`
* **Success Green:** `#10B981` / `hsl(162, 76%, 45%)` (neon glow accents)
* **Warning Amber:** `#FBBF24` / `hsl(43, 96%, 56%)`
* **Danger Red:** `#EF4444` / `hsl(0, 84%, 60%)`
* **Text High-Contrast:** `#F9FAFB` / `hsl(0, 0%, 98%)`
* **Text Secondary:** `#9CA3AF` / `hsl(220, 9%, 76%)`

### Typography
* **Primary Sans:** Inter (Clean, readable sans-serif)
* **Code / Monospace:** JetBrains Mono (For terminal logs, regex matches, rule IDs)

---

## 2. Portal Layout & Navigation
The interface is structured around a persistent glassmorphism sidebar navigation and a wide content area.

```
+-----------------------------------------------------------------------------------+
|  [Niyam Logo]             [Search anything...]                  [Profile: Team v] |
+-----------------------------------------------------------------------------------+
|  ( ) Overview      |  Aggregate Readiness Score        Token Cost Trend (7 Days)  |
|  ( ) Scan Reports  |  +--------------------------+    +-------------------------+ |
|  ( ) MCP Registry  |  |           92%            |    |  $$                     | |
|  ( ) FinOps Ledger |  |         [ GO ]           |    |  $$$$                   | |
|  ( ) Evidence Hub  |  +--------------------------+    +-------------------------+ |
|                    +--------------------------------------------------------------+
|  [Settings]        |  Critical Findings               Wasted Budget Card          |
|  [Local Mode]      |  - SEC001: Hardcoded AWS Key    |  Total Leak: $14.50      | |
+--------------------+--------------------------------------------------------------+
```

---

## 3. View Specifications

### I. Executive Overview
* **aggregate readiness Score Gauge:** A large glowing circular chart showing the current project score ($0 - 100$) and the gate decision badge (`GO`, `CONDITIONAL_GO`, `HIGH_RISK`, `NO_GO`).
* **KPI Matrix Cards:**
  * Total Scan Findings (Click to jump to Scanner view)
  * Active MCP Tools (Approved vs. Unapproved counts)
  * Estimated Session Cost (Total budget spent)
  * Wasted Budget Indicator (Cost lost in repeated or failed tasks)
* **Cost Trend Chart:** A bar chart showing token expenses accumulated over the past $7$ days.

### II. Readiness Scan Explorer
* **Filter Bar:** Multi-select dropdowns for Severity (`critical`, `high`, `medium`, `low`) and Category (`secrets`, `dependencies`, `tests`, `ai_risk`).
* **Findings Grid:** A interactive table containing:
  * **Rule ID Badge** (e.g. `SEC001`, `IAC002`).
  * **Severity Tag** (color-coded).
  * **File Target** (with clickable IDE links, e.g. `tests/test_auth.py:L24`).
  * **Short Description** of the finding.
  * **Collapsible Remediation Drawer:** Renders the rule's specific recommendation guidelines and quick terminal commands to resolve the issue.

### III. MCP Tool Catalog
* **Grid Layout Cards:** Lists all tools from `.niyam/mcp-registry.json`.
  * Each card displays the Tool Name, Type Icon (MCP, API, CLI), and heuristic Risk badge (`low` to `critical`).
  * **Approval Toggle:** Interacts directly with the local JSON database to mark tools as approved.
  * **Data Access Inspector:** Lists folder paths or API scopes accessed by the tool.

### IV. FinOps Ledger
* **Token Cost Ratio Chart:** A pie chart illustrating the ratio between Prompt (Input) and Completion (Output) token costs.
* **Session Run Ledger Table:** Displays all runs sorted by date. Shows session ID, target Git branch, model used, total tokens consumed, cost in USD, and exit status. Highlight runs labeled as `failed` or `repeated` with a caution icon denoting budget leakage.

### V. Evidence Hub
* **Compilation Control Panel:** A form to trigger a fresh repository check and build a new report. Supports checklist selections for sections (`scan`, `guard`, `mcp`, `cost`) and formatting options (Markdown or HTML).
* **Audit Trail Table:** Timed records of previously compiled reports. Includes quick-action icons to view, export, or download files locally.

---

## 4. Component Interactive Spec
* **Collapsible Code Blocks:** Renders redacted stdin/stdout terminal flows inside a syntax-highlighted wrapper.
* **Modal Overlay Dialogs:** Form interfaces for manual tool registrations and custom scan profile edits.
* **Interactive Tooltips:** Explain the heuristic indicator triggers for classified risks when hovering over risk badges.

---

## 5. Frontend Architecture & API Bridge
The frontend is built using **Vite + React + TypeScript** and styled with **Vanilla CSS Variables**.

### Local API Server Bridging
Because Niyam operates local-first, the dashboard is served via a lightweight Node.js API server spawned locally (port `8080`) when typing `niyam dashboard` in the terminal:

* **`GET /api/status`**: Loads version and configuration from `.niyam/niyam.yaml`.
* **`GET /api/scan`**: Runs a repository scan and returns the JSON payload.
* **`GET /api/mcp`**: Retrieves registered tools from `mcp-registry.json`.
* **`POST /api/mcp/approve`**: Updates a tool's approval status in the registry.
* **`GET /api/cost`**: Reads and aggregates data from `cost-events.jsonl` and `pricing.json`.
* **`POST /api/evidence/generate`**: Calls the core evidence report compiler and returns the result file paths.
