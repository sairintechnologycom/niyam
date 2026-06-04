"""Niyam evidence generator — audit-ready report builder."""

from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jinja2 import Template

from niyam.core.config import find_niyam_root, load_niyam_config

# Markdown template
MARKDOWN_TEMPLATE = """# Niyam Governance & Production Readiness Evidence Report

## 1. Executive Summary
This document serves as an audit-ready evidence record for the repository readiness and AI agent governance. It aggregates static analysis, dependency health, and runtime agent execution safety logs.

## 2. Project Metadata
* **Project Name:** {{ project }}
* **Generated At:** {{ generated_at }}
* **Git Branch / Commit:** `{{ source }}`

{% if "scan" in include %}
## 3. Readiness Score
* **Readiness Score:** **{{ readiness_score }}/100**

## 4. Launch Decision
* **Launch Decision:** **{{ decision.replace('_', ' ') }}**

## 5. Decision Reason
* **Decision Reason:** *{{ decision_reason }}*

## 6. Critical and High Findings
{% if scan.critical_high_findings %}
| ID | Title | Category | Severity | File Path |
| --- | --- | --- | --- | --- |
{% for f in scan.critical_high_findings -%}
| {{ f.id }} | {{ f.title }} | {{ f.category }} | **{{ f.severity.upper() }}** | `{{ f.file_path or 'Global' }}` |
{% endfor %}
{% else %}
✓ No Critical or High findings detected in the repository scan.
{% endif %}

## 7. Risk Register
{% if risk_summary %}
| Severity | Count |
| --- | --- |
| Critical | {{ risk_summary.critical }} |
| High | {{ risk_summary.high }} |
| Medium | {{ risk_summary.medium }} |
| Low | {{ risk_summary.low }} |
| Info | {{ risk_summary.info }} |
{% else %}
No risk register data available.
{% endif %}

## 8. Recommended Remediation Plan
{% if remediation_plan %}
Remediation actions are recommended below:
{% for item in remediation_plan -%}
* **[{{ item.id }}] {{ item.title }}** ({{ item.severity.upper() }}): {{ item.recommendation }}
{% endfor %}
{% else %}
✓ No remediation actions required.
{% endif %}
{% endif %}

## 9. AI-Assisted Development Governance Notes
* **AI-Risk Placeholders / Commented Assertions:** Checked.
{% if "guard" in include -%}
* **Agent Governance / Guardrails Status:** {{ governance.guard_status }}
{% if guard_logs %}
### Recent Observed Actions (Agent Governance)
| Timestamp | Actor | Command | Exit Code | Duration (ms) |
| --- | --- | --- | --- | --- |
{% for log in guard_logs -%}
| {{ log.timestamp }} | {{ log.actor_type }} | `{{ log.command }}` | {{ log.exit_code }} | {{ log.duration_ms }} |
{% endfor %}
{% endif %}
{% if violations %}
### Policy Violations (Agent Governance)
| Timestamp | Command | Exit Code |
| --- | --- | --- |
{% for v in violations -%}
| {{ v.timestamp }} | `{{ v.command }}` | {{ v.exit_code }} |
{% endfor %}
{% endif %}
{%- endif %}
{%- if "mcp" in include -%}
* **MCP / Tool Approval Posture:** {{ mcp.approved }}/{{ mcp.total }} tools approved.
{% if mcp.tools %}
### Registered Tools (MCP)
| Name | Type | Risk Level | Approved | Owner |
| --- | --- | --- | --- | --- |
{% for t in mcp.tools -%}
| {{ t.name }} | {{ t.type }} | **{{ t.risk_level.upper() }}** | {{ 'Yes' if t.approved else 'No' }} | {{ t.owner or 'N/A' }} |
{% endfor %}
{% endif %}
{%- endif %}
{%- if "cost" in include and cost.total_cost is not none -%}
* **AI Engineering Cost Summary:** Estimated Cost: ${{ "%.4f"|format(cost.total_cost) }} (Input tokens: {{ cost.total_input_tokens }}, Output tokens: {{ cost.total_output_tokens }})
{%- endif %}

## 10. Appendix Summary
* **Redaction Status:** Redacted: {{ redaction_status.redacted }} (Engine: {{ redaction_status.engine }})
* **Branch:** `{{ metadata.branch }}`
* **Commit SHA:** `{{ metadata.commit_sha }}`
* **Commit Author:** {{ metadata.commit_author }}
"""

# Premium HTML template with CSS styling
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Niyam Evidence Report — {{ metadata.project_name }}</title>
    <style>
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            color: #1e293b;
            background-color: #f8fafc;
            line-height: 1.6;
            margin: 0;
            padding: 40px 20px;
        }
        .container {
            max-width: 900px;
            margin: 0 auto;
            background: #ffffff;
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
            border: 1px solid #e2e8f0;
        }
        h1, h2, h3 {
            color: #0f172a;
        }
        h1 {
            font-size: 2rem;
            margin-top: 0;
            border-bottom: 2px solid #f1f5f9;
            padding-bottom: 20px;
        }
        h2 {
            font-size: 1.4rem;
            margin-top: 40px;
            border-bottom: 1px solid #f1f5f9;
            padding-bottom: 8px;
        }
        .badge {
            display: inline-block;
            padding: 6px 12px;
            border-radius: 9999px;
            font-weight: bold;
            font-size: 0.85rem;
            text-transform: uppercase;
        }
        .badge-go { background-color: #dcfce7; color: #15803d; }
        .badge-cond { background-color: #fef9c3; color: #a16207; }
        .badge-risk { background-color: #ffedd5; color: #c2410c; }
        .badge-nogo { background-color: #fee2e2; color: #b91c1c; }
        
        .score-card {
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: #f1f5f9;
            padding: 24px;
            border-radius: 8px;
            margin: 24px 0;
        }
        .score-val {
            font-size: 2.5rem;
            font-weight: 800;
            color: #0f172a;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        th, td {
            text-align: left;
            padding: 12px;
            border-bottom: 1px solid #e2e8f0;
        }
        th {
            background-color: #f8fafc;
            color: #475569;
            font-weight: 600;
        }
        .meta-list {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
            background: #fafafa;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
        }
        .meta-item span {
            font-weight: bold;
            color: #475569;
        }
        .remediation-item {
            background: #fafafa;
            padding: 16px;
            border-radius: 6px;
            margin-bottom: 12px;
            border-left: 4px solid #3b82f6;
        }
        .remediation-item.severity-critical { border-left-color: #ef4444; }
        .remediation-item.severity-high { border-left-color: #f97316; }
        .remediation-item.severity-medium { border-left-color: #eab308; }
        .remediation-item.severity-low { border-left-color: #22c55e; }
        
        .sign-off-box {
            border: 2px dashed #cbd5e1;
            padding: 24px;
            border-radius: 8px;
            margin-top: 40px;
        }
        .sign-line {
            margin-top: 20px;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 40px;
        }
        .line-blank {
            border-bottom: 1px solid #94a3b8;
            height: 30px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Niyam Evidence & Governance Report</h1>
        
        <div class="meta-list">
            <div class="meta-item"><span>Project Name:</span> {{ metadata.project_name }}</div>
            <div class="meta-item"><span>Git Branch:</span> {{ metadata.branch }}</div>
            <div class="meta-item"><span>Commit SHA:</span> {{ metadata.commit_sha }}</div>
            <div class="meta-item"><span>Commit Author:</span> {{ metadata.commit_author }}</div>
            <div class="meta-item"><span>Timestamp:</span> {{ metadata.timestamp }}</div>
        </div>

        <h2>1. Executive Summary</h2>
        <p>This report documents the security checks and compliance validation status for production release. Included sections:
        {%- if "scan" in include %} Production Readiness;{% endif %}
        {%- if "guard" in include %} Agent Governance;{% endif %}
        {%- if "mcp" in include %} Tool/MCP Risk Posture;{% endif %}
        {%- if "cost" in include %} Cost Tracking MVP;{% endif %}
        </p>

        {% if "scan" in include %}
        <h2>2. Production Readiness</h2>
        <div class="score-card">
            <div>
                <div style="font-size: 0.9rem; color: #64748b; font-weight: bold;">READINESS SCORE</div>
                <div class="score-val">{{ scan.score }} <span style="font-size: 1.2rem; font-weight: normal; color: #64748b;">/ 100</span></div>
            </div>
            <div>
                <span class="badge 
                    {% if scan.decision == 'GO' %}badge-go
                    {% elif scan.decision == 'CONDITIONAL_GO' %}badge-cond
                    {% elif scan.decision == 'HIGH_RISK' %}badge-risk
                    {% else %}badge-nogo{% endif %}">
                    {{ scan.decision }}
                </span>
            </div>
        </div>
        {% endif %}

        {% if "guard" in include %}
        <h2>3. Agent Governance Activity</h2>
        <ul>
            <li><strong>Guardrails Enabled:</strong> {{ governance.guard_status }}</li>
            <li><strong>Careful Mode:</strong> {{ governance.careful_mode }}</li>
            <li><strong>Frozen Paths:</strong> {{ governance.frozen_paths or 'None' }}</li>
        </ul>
        
        <h3>Recent Observed Actions</h3>
        {% if guard_logs %}
            <table>
                <thead>
                    <tr>
                        <th>Timestamp</th>
                        <th>Actor</th>
                        <th>Command</th>
                        <th>Exit Code</th>
                        <th>Duration (ms)</th>
                    </tr>
                </thead>
                <tbody>
                    {% for log in guard_logs %}
                        <tr>
                            <td>{{ log.timestamp }}</td>
                            <td>{{ log.actor_type }}</td>
                            <td><code>{{ log.command }}</code></td>
                            <td>{{ log.exit_code }}</td>
                            <td>{{ log.duration_ms }}</td>
                        </tr>
                    {% endfor %}
                </tbody>
            </table>
        {% else %}
            <p>✓ No recent observed actions logged.</p>
        {% endif %}
        {% endif %}

        {% if "mcp" in include %}
        <h2>4. Tool/MCP Risk Posture</h2>
        <ul>
            <li><strong>Total Registered Tools:</strong> {{ mcp.total }}</li>
            <li><strong>Approved Tools:</strong> {{ mcp.approved }}</li>
            <li><strong>Unapproved Tools:</strong> {{ mcp.unapproved }}</li>
        </ul>
        {% if mcp.tools %}
            <table>
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Type</th>
                        <th>Risk Level</th>
                        <th>Approved</th>
                        <th>Owner</th>
                    </tr>
                </thead>
                <tbody>
                    {% for t in mcp.tools %}
                        <tr>
                            <td>{{ t.name }}</td>
                            <td>{{ t.type }}</td>
                            <td><strong>{{ t.risk_level }}</strong></td>
                            <td>{{ 'Yes' if t.approved else 'No' }}</td>
                            <td>{{ t.owner or 'N/A' }}</td>
                        </tr>
                    {% endfor %}
                </tbody>
            </table>
        {% endif %}
        {% endif %}

        {% if "cost" in include %}
        <h2>5. AI Engineering Cost Summary</h2>
        <ul>
            <li><strong>Total Estimated Cost:</strong> ${{ "%.4f"|format(cost.total_cost) }}</li>
            <li><strong>Total Input Tokens:</strong> {{ "{:,}".format(cost.total_input_tokens) }}</li>
            <li><strong>Total Output Tokens:</strong> {{ "{:,}".format(cost.total_output_tokens) }}</li>
        </ul>
        {% if cost.by_day %}
            <table>
                <thead>
                    <tr>
                        <th>Day</th>
                        <th>Estimated Cost</th>
                    </tr>
                </thead>
                <tbody>
                    {% for day, val in cost.by_day.items()|sort %}
                        <tr>
                            <td>{{ day }}</td>
                            <td>${{ "%.4f"|format(val) }}</td>
                        </tr>
                    {% endfor %}
                </tbody>
            </table>
        {% endif %}
        {% endif %}

        <h2>6. Policy Violations or Blocked Actions</h2>
        {% if "guard" in include and violations %}
            <table>
                <thead>
                    <tr>
                        <th>Timestamp</th>
                        <th>Command</th>
                        <th>Exit Code</th>
                    </tr>
                </thead>
                <tbody>
                    {% for v in violations %}
                        <tr>
                            <td>{{ v.timestamp }}</td>
                            <td><code>{{ v.command }}</code></td>
                            <td>{{ v.exit_code }}</td>
                        </tr>
                    {% endfor %}
                </tbody>
            </table>
        {% else %}
            <p style="color: #16a34a; font-weight: bold;">✓ No policy violations or blocked actions detected.</p>
        {% endif %}

        <h2>7. Recommended Next Actions</h2>
        {% set remediation_needed = false %}
        {% if "scan" in include and scan.findings %}{% set remediation_needed = true %}{% endif %}
        {% if "mcp" in include and mcp.unapproved_high %}{% set remediation_needed = true %}{% endif %}

        {% if remediation_needed %}
            {% if "scan" in include %}
                {% for f in scan.findings %}
                    <div class="remediation-item severity-{{ f.severity }}">
                        <strong>[Readiness] [{{ f.id }}] {{ f.title }}</strong> ({{ f.severity.upper() }})<br>
                        <p style="margin: 8px 0 4px 0;">{{ f.description }}</p>
                        <p style="margin: 0; color: #2563eb;">Recommendation: {{ f.recommendation }}</p>
                    </div>
                {% endfor %}
            {% endif %}
            {% if "mcp" in include %}
                {% for t in mcp.unapproved_high %}
                    <div class="remediation-item severity-high">
                        <strong>[Tool Governance] Approve High-Risk Tool: {{ t.name }}</strong> ({{ t.risk_level.upper() }})<br>
                        <p style="margin: 8px 0 4px 0;">Tool has high/critical risk and has not been approved.</p>
                    </div>
                {% endfor %}
            {% endif %}
        {% else %}
            <p style="color: #16a34a; font-weight: bold;">✓ All governance checks are healthy. No next actions required.</p>
        {% endif %}

        <div class="sign-off-box">
            <h3>8. Audit Sign-off</h3>
            <p>Git Commit SHA: <code>{{ metadata.commit_sha }}</code> | Author: {{ metadata.commit_author }} | UTC: {{ metadata.timestamp }}</p>
            <div class="sign-line">
                <div>
                    Lead Engineer Approval:
                    <div class="line-blank"></div>
                </div>
                <div>
                    Security Officer Approval:
                    <div class="line-blank"></div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""


def redact_secrets_recursive(data: Any) -> Any:
    """Recursively search and redact secrets in dictionaries, lists, and strings."""
    if isinstance(data, str):
        # Match pattern containing api_key, password, private_key, token, etc.
        pattern = r"(?i)(api_key|apikey|secret_key|private_key|token|auth_token|password|pass)\s*[=:]\s*[\"']?[a-zA-Z0-9_\-\.]{8,}[\"']?"
        return re.sub(pattern, r"\1=REDACTED", data)
    elif isinstance(data, dict):
        return {k: redact_secrets_recursive(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [redact_secrets_recursive(x) for x in data]
    return data


def _get_git_metadata(repo_root: Path) -> dict[str, str]:
    """Retrieve current branch, commit hash, and author using git command-line tool."""
    metadata = {
        "branch": "unknown",
        "commit_sha": "unknown",
        "commit_author": "unknown",
    }

    try:
        # Branch
        res_branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if res_branch.returncode == 0:
            metadata["branch"] = res_branch.stdout.strip()

        # Commit Hash
        res_sha = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if res_sha.returncode == 0:
            metadata["commit_sha"] = res_sha.stdout.strip()

        # Commit Author
        res_author = subprocess.run(
            ["git", "log", "-1", "--format=%an"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if res_author.returncode == 0:
            metadata["commit_author"] = res_author.stdout.strip()
    except Exception:
        pass

    return metadata


def _get_audit_trail(repo_root: Path) -> list[dict[str, Any]]:
    """Scan the runs folder to retrieve audit trail history."""
    runs_dir = repo_root / ".niyam" / "runs"
    trail = []

    if runs_dir.is_dir():
        import yaml

        # Sort run subdirectories by creation time
        subdirs = sorted(
            [d for d in runs_dir.iterdir() if d.is_dir()],
            key=lambda d: d.stat().st_mtime,
            reverse=True,
        )

        for d in subdirs[:5]:  # limit to last 5 runs
            plan_file = d / "mission-plan.yaml"
            ledger_file = d / "token-ledger.json"

            run_info = {
                "id": d.name,
                "created": "unknown",
                "orchestrator": "unknown",
                "status": "unknown",
                "cost_usd": None,
            }

            if plan_file.exists():
                try:
                    with open(plan_file, encoding="utf-8") as f:
                        plan_data = yaml.safe_load(f) or {}
                    mission = plan_data.get("mission", {})
                    run_info["created"] = mission.get("created", "unknown")
                    run_info["orchestrator"] = mission.get("orchestrator", "unknown")
                    run_info["status"] = mission.get("status", "unknown")
                except Exception:
                    pass

            if ledger_file.exists():
                try:
                    with open(ledger_file, encoding="utf-8") as f:
                        ledger_data = json.load(f) or {}
                    events = ledger_data.get("events", [])
                    run_info["cost_usd"] = sum(
                        float(e.get("cost_usd", 0.0)) for e in events
                    )
                except Exception:
                    pass

            trail.append(run_info)

    return trail


def _get_guard_logs(repo_root: Path) -> list[dict[str, Any]]:
    """Load latest guard observed commands logs."""
    path = repo_root / ".niyam" / "logs" / "guard-actions.jsonl"
    if not path.exists():
        return []
    logs = []
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        logs.append(json.loads(line))
                    except Exception:
                        pass
    except Exception:
        pass
    return logs[-10:]


def _get_violations(guard_logs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Extract failed or problematic actions from guard logs."""
    violations = []
    for log in guard_logs:
        if log.get("exit_code", 0) != 0:
            violations.append(log)
    return violations


def _get_mcp_data(repo_root: Path) -> dict[str, Any]:
    """Retrieve MCP/Tool registry analytics."""
    try:
        from niyam.core.mcp import load_mcp_registry

        registry = load_mcp_registry(repo_root)
        tools_list = list(registry.tools.values())
    except Exception:
        tools_list = []

    total = len(tools_list)
    approved = sum(1 for t in tools_list if t.approved)
    unapproved = total - approved
    unapproved_high = [
        t for t in tools_list if not t.approved and t.risk_level in ("high", "critical")
    ]

    return {
        "total": total,
        "approved": approved,
        "unapproved": unapproved,
        "tools": [t.model_dump() for t in tools_list],
        "unapproved_high": [t.model_dump() for t in unapproved_high],
    }


def _get_cost_data(repo_root: Path) -> dict[str, Any]:
    """Retrieve FinOps cost usage tracking details."""
    try:
        from niyam.core.cost import load_cost_events, generate_cost_metrics

        events = load_cost_events(repo_root)
        metrics = generate_cost_metrics(events)
    except Exception:
        metrics = {
            "total_cost": 0.0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "by_day": {},
        }
    return metrics


def run_generate_evidence(
    from_scan_json: str | None = None,
    fmt: str = "markdown",
    output: str | None = None,
    include: str = "scan,guard,mcp,cost",
) -> str:
    """Generate evidence report locally and return the formatted output string."""
    root = find_niyam_root()
    if root is None:
        root = Path.cwd()

    include_list = [s.strip() for s in include.split(",")]

    # Load scan results
    if from_scan_json:
        scan_json_path = Path(from_scan_json).resolve()
        if not scan_json_path.exists():
            raise FileNotFoundError(f"Scan JSON file not found at: {from_scan_json}")
    else:
        # Search for default scan report under .niyam/reports/scan.json
        scan_json_path = root / ".niyam" / "reports" / "scan.json"
        if not scan_json_path.exists():
            # Check fallback to .sutra/reports/scan.json
            scan_json_path = root / ".sutra" / "reports" / "scan.json"
            if not scan_json_path.exists():
                raise FileNotFoundError(
                    "No scan report input found. Please specify --from or run niyam scan first."
                )

    try:
        with open(scan_json_path, encoding="utf-8") as f:
            scan_results = json.load(f)
    except Exception as e:
        raise ValueError(f"Failed to parse scan JSON file: {e}")

    # 1. Compile project config metadata
    project_name = "Niyam Project"
    guard_status = "Disabled"
    careful_mode = "Disabled"
    frozen_paths = ""
    try:
        config = load_niyam_config(root)
        if config:
            if config.project_name:
                project_name = config.project_name
            if config.guard:
                guard_status = "Enabled" if config.guard.enabled else "Disabled"
                careful_mode = "Enabled" if config.guard.careful else "Disabled"
                if config.guard.frozen_paths:
                    frozen_paths = ", ".join(config.guard.frozen_paths)
    except Exception:
        pass

    git_meta = _get_git_metadata(root)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # 2. Findings breakdown & critical/high counts
    findings = scan_results.get("findings", [])
    critical_high = [f for f in findings if f.get("severity") in ("critical", "high")]

    breakdown = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    for f in findings:
        sev = f.get("severity", "info").lower()
        if sev in breakdown:
            breakdown[sev] += 1

    # 3. Dynamic loaders for sections
    guard_logs = _get_guard_logs(root) if "guard" in include_list else []
    violations = _get_violations(guard_logs) if "guard" in include_list else []
    mcp_data = (
        _get_mcp_data(root)
        if "mcp" in include_list
        else {
            "total": 0,
            "approved": 0,
            "unapproved": 0,
            "tools": [],
            "unapproved_high": [],
        }
    )
    cost_data = (
        _get_cost_data(root)
        if "cost" in include_list
        else {
            "total_cost": 0.0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "by_day": {},
        }
    )

    # 4. Audit trail run logs
    audit_trail = _get_audit_trail(root)

    # Map context to the required evidence output schema keys
    source_str = f"Branch: {git_meta['branch']}, Commit: {git_meta['commit_sha']}"

    risk_summary = {
        "total_findings": len(findings),
        "critical": breakdown.get("critical", 0),
        "high": breakdown.get("high", 0),
        "medium": breakdown.get("medium", 0),
        "low": breakdown.get("low", 0),
        "info": breakdown.get("info", 0)
    }

    findings_summary = [
        {
            "id": f.get("id"),
            "severity": f.get("severity"),
            "category": f.get("category"),
            "title": f.get("title"),
            "file_path": f.get("file_path")
        }
        for f in findings
    ]

    remediation_plan = [
        {
            "id": f.get("id"),
            "title": f.get("title"),
            "severity": f.get("severity"),
            "recommendation": f.get("recommendation")
        }
        for f in findings
    ]

    # Prepare Jinja2 context and new output schema keys
    context = {
        "schema_version": "1.0.0",
        "generated_at": timestamp,
        "source": source_str,
        "project": project_name,
        "readiness_score": scan_results.get("score", 0),
        "decision": scan_results.get("decision", "NO_GO"),
        "decision_reason": scan_results.get("decision_reason", "Scan completed successfully."),
        "risk_summary": risk_summary,
        "findings_summary": findings_summary,
        "remediation_plan": remediation_plan,
        "redaction_status": {"redacted": True, "engine": "niyam-redaction"},
        "include": include_list,
        "metadata": {
            "project_name": project_name,
            "branch": git_meta["branch"],
            "commit_sha": git_meta["commit_sha"],
            "commit_author": git_meta["commit_author"],
            "timestamp": timestamp,
        },
        "scan": {
            "profile": scan_results.get("profile", "unknown"),
            "score": scan_results.get("score", 0),
            "decision": scan_results.get("decision", "NO_GO"),
            "findings_count": len(findings),
            "findings": findings,
            "critical_high_findings": critical_high,
            "breakdown": breakdown,
        },
        "governance": {
            "guard_status": guard_status,
            "careful_mode": careful_mode,
            "frozen_paths": frozen_paths,
        },
        "guard_logs": guard_logs,
        "violations": violations,
        "mcp": mcp_data,
        "cost": cost_data,
        "audit_trail": audit_trail,
    }

    # 5. Redact secrets recursively across the context dictionary using the shared redaction utility
    from niyam.governance.common.redaction import redact_secrets, redact_text
    context = redact_secrets(context)

    # 6. Render report
    if fmt == "json":
        report_str = json.dumps(context, indent=2)
    elif fmt == "html":
        template = Template(HTML_TEMPLATE)
        report_str = template.render(context)
    else:  # markdown
        template = Template(MARKDOWN_TEMPLATE)
        report_str = template.render(context)

    # Apply secondary redaction on final text to double check safety
    report_str = redact_text(report_str)

    # 7. Output to file if requested
    if output:
        output_path = Path(output).resolve()
        try:
            output_path.write_text(report_str, encoding="utf-8")
        except Exception as e:
            raise IOError(f"Failed to write evidence report to file: {e}")

    return report_str
