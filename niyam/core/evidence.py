"""Niyam evidence generator — audit-ready report builder."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jinja2 import Template

from niyam.core.config import find_niyam_root, load_niyam_config
from niyam.core.scan import run_scanner_checks

# Markdown template
MARKDOWN_TEMPLATE = """# Niyam Governance & Production Readiness Evidence Report

**Project:** {{ metadata.project_name }}
**Branch:** `{{ metadata.branch }}`
**Last Commit:** `{{ metadata.commit_sha }}` by {{ metadata.commit_author }}
**Scan Profile:** `{{ scan.profile }}`
**Generated At:** {{ metadata.timestamp }}

---

## 1. Executive Summary
This document serves as an audit-ready evidence record for the repository readiness. It provides a formal assessment of security, configuration, validation, and AI engineering governance metrics.

## 2. Readiness Assessment Summary

| Metric | Status / Value |
| --- | --- |
| **Readiness Score** | **{{ scan.score }}/100** |
| **Launch Decision** | **{{ scan.decision }}** |
| **Total Findings** | {{ scan.findings_count }} |

### Findings Breakdown
* **Critical:** {{ scan.breakdown.critical }}
* **High:** {{ scan.breakdown.high }}
* **Medium:** {{ scan.breakdown.medium }}
* **Low:** {{ scan.breakdown.low }}
* **Info:** {{ scan.breakdown.info }}

---

## 3. Launch Decision details
Based on the readiness score of **{{ scan.score }}**, the automated gate recommends:
{% if scan.decision == "GO" %}
🟢 **GO**: The project meets all standard readiness guidelines and is safe for production deployment.
{% elif scan.decision == "CONDITIONAL_GO" %}
🟡 **CONDITIONAL GO**: Minor issues were identified. The project is launchable, but the remediation plan should be addressed in the next iteration.
{% elif scan.decision == "HIGH_RISK" %}
🟠 **HIGH RISK**: Several high-severity or medium-severity issues remain. Launch is discouraged without explicit risk sign-off.
{% else %}
🔴 **NO GO**: Critical security or policy violations detected. Immediate remediation is required before build promotion.
{% endif %}

---

## 4. Critical & High Severity Findings
{% if scan.critical_high_findings %}
| ID | Severity | Category | Description | File Path |
| --- | --- | --- | --- | --- |
{% for f in scan.critical_high_findings -%}
| {{ f.id }} | **{{ f.severity.upper() }}** | {{ f.category }} | {{ f.description }} | `{{ f.file_path or 'Global' }}` |
{% endfor %}
{% else %}
✓ No critical or high severity findings detected in the scan.
{% endif %}

---

## 5. Recommended Remediation Plan
{% if scan.findings %}
{% for f in scan.findings -%}
* **[{{ f.id }}] {{ f.title }}** ({{ f.severity.upper() }}):
  * *Finding:* {{ f.description }}
  * *Remediation:* {{ f.recommendation }}
{% endfor %}
{% else %}
✓ No remediation actions required.
{% endif %}

---

## 6. AI Governance & Audit Trail

### Active Policies
* **Frozen Paths:** {{ governance.frozen_paths or 'None' }}
* **Guardrails Status:** {{ governance.guard_status }}

### Recent Execution Logs (Audit Trail)
{% if audit_trail %}
| Mission ID | Date / Time | Orchestrator | Status | Cost (USD) |
| --- | --- | --- | --- | --- |
{% for run in audit_trail -%}
| `{{ run.id }}` | {{ run.created }} | {{ run.orchestrator }} | `{{ run.status }}` | {% if run.cost_usd is not none %}${{ "%.4f"|format(run.cost_usd) }}{% else %}-$0.00{% endif %} |
{% endfor %}
{% else %}
No recent execution history found.
{% endif %}

---

## 7. Risk Acceptance Sign-off
*This section must be completed if launching with a score of less than 85.*

- [ ] **Lead Engineer Approval:**
  - Name: __________________________
  - Date: __________________________
- [ ] **Security Officer Approval:**
  - Name: __________________________
  - Date: __________________________
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
        <h1>Niyam Evidence & Production Readiness Report</h1>
        
        <div class="meta-list">
            <div class="meta-item"><span>Project Name:</span> {{ metadata.project_name }}</div>
            <div class="meta-item"><span>Git Branch:</span> {{ metadata.branch }}</div>
            <div class="meta-item"><span>Commit SHA:</span> {{ metadata.commit_sha }}</div>
            <div class="meta-item"><span>Commit Author:</span> {{ metadata.commit_author }}</div>
            <div class="meta-item"><span>Scan Profile:</span> {{ scan.profile }}</div>
            <div class="meta-item"><span>Timestamp:</span> {{ metadata.timestamp }}</div>
        </div>

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

        <h2>1. Executive Summary</h2>
        <p>This report documents the security checks and compliance validation status for production release. The repository scan score of <strong>{{ scan.score }}</strong> denotes a <strong>{{ scan.decision }}</strong> launch state recommendation.</p>

        <h2>2. Critical & High Findings</h2>
        {% if scan.critical_high_findings %}
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Severity</th>
                        <th>Category</th>
                        <th>Description</th>
                        <th>File Path</th>
                    </tr>
                </thead>
                <tbody>
                    {% for f in scan.critical_high_findings %}
                        <tr>
                            <td>{{ f.id }}</td>
                            <td><span class="badge badge-nogo">{{ f.severity.upper() }}</span></td>
                            <td>{{ f.category }}</td>
                            <td>{{ f.description }}</td>
                            <td><code>{{ f.file_path or 'Global' }}</code></td>
                        </tr>
                    {% endfor %}
                </tbody>
            </table>
        {% else %}
            <p style="color: #16a34a; font-weight: bold;">✓ No critical or high severity findings were detected.</p>
        {% endif %}

        <h2>3. Recommended Remediation Plan</h2>
        {% if scan.findings %}
            {% for f in scan.findings %}
                <div class="remediation-item severity-{{ f.severity }}">
                    <strong>[{{ f.id }}] {{ f.title }}</strong> ({{ f.severity.upper() }})<br>
                    <p style="margin: 8px 0 4px 0;"><em>Finding:</em> {{ f.description }}</p>
                    <p style="margin: 0; color: #2563eb;"><em>Recommendation:</em> {{ f.recommendation }}</p>
                </div>
            {% endfor %}
        {% else %}
            <p>✓ All checks passed successfully. No remediation actions required.</p>
        {% endif %}

        <h2>4. Audit & AI Governance Trail</h2>
        <h3>Policies Config</h3>
        <ul>
            <li><strong>Guardrails Enabled:</strong> {{ governance.guard_status }}</li>
            <li><strong>Frozen Paths:</strong> {{ governance.frozen_paths or 'None' }}</li>
        </ul>
        
        <h3>Recent Run History</h3>
        {% if audit_trail %}
            <table>
                <thead>
                    <tr>
                        <th>Mission ID</th>
                        <th>Timestamp</th>
                        <th>Orchestrator</th>
                        <th>Status</th>
                        <th>Token Cost</th>
                    </tr>
                </thead>
                <tbody>
                    {% for run in audit_trail %}
                        <tr>
                            <td><code>{{ run.id }}</code></td>
                            <td>{{ run.created }}</td>
                            <td>{{ run.orchestrator }}</td>
                            <td><code>{{ run.status }}</code></td>
                            <td>{% if run.cost_usd is not none %}${{ "%.4f"|format(run.cost_usd) }}{% else %}-$0.00{% endif %}</td>
                        </tr>
                    {% endfor %}
                </tbody>
            </table>
        {% else %}
            <p>No recent execution logs found.</p>
        {% endif %}

        <div class="sign-off-box">
            <h3>5. Risk Sign-off & Approvals</h3>
            <p>Signing below acknowledges acceptance of the readiness score and launch risks.</p>
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

def _get_git_metadata(repo_root: Path) -> dict[str, str]:
    """Retrieve current branch, commit hash, and author using git command-line tool."""
    metadata = {
        "branch": "unknown",
        "commit_sha": "unknown",
        "commit_author": "unknown"
    }
    
    try:
        # Branch
        res_branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=repo_root, capture_output=True, text=True, check=False
        )
        if res_branch.returncode == 0:
            metadata["branch"] = res_branch.stdout.strip()
            
        # Commit Hash
        res_sha = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=repo_root, capture_output=True, text=True, check=False
        )
        if res_sha.returncode == 0:
            metadata["commit_sha"] = res_sha.stdout.strip()
            
        # Commit Author
        res_author = subprocess.run(
            ["git", "log", "-1", "--format=%an"],
            cwd=repo_root, capture_output=True, text=True, check=False
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
            reverse=True
        )
        
        for d in subdirs[:5]:  # limit to last 5 runs
            plan_file = d / "mission-plan.yaml"
            ledger_file = d / "token-ledger.json"
            
            run_info = {
                "id": d.name,
                "created": "unknown",
                "orchestrator": "unknown",
                "status": "unknown",
                "cost_usd": None
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
                    run_info["cost_usd"] = sum(float(e.get("cost_usd", 0.0)) for e in events)
                except Exception:
                    pass
                    
            trail.append(run_info)
            
    return trail

def run_generate_evidence(
    from_scan_json: str | None = None,
    fmt: str = "markdown",
    output: str | None = None
) -> str:
    """Generate evidence report locally and return the formatted output string."""
    root = find_niyam_root()
    if root is None:
        root = Path.cwd()

    # Load scan results
    if from_scan_json:
        scan_json_path = Path(from_scan_json).resolve()
        if not scan_json_path.exists():
            raise FileNotFoundError(f"Scan JSON file not found at: {from_scan_json}")
        try:
            with open(scan_json_path, encoding="utf-8") as f:
                scan_results = json.load(f)
        except Exception as e:
            raise ValueError(f"Failed to parse scan JSON file: {e}")
    else:
        # Generate checks dynamically
        scan_results = run_scanner_checks(root)

    # 1. Compile project config metadata
    project_name = "Niyam Project"
    try:
        config = load_niyam_config(root)
        if config and config.project_name:
            project_name = config.project_name
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

    # 3. Governance config
    guard_status = "Disabled"
    frozen_paths = ""
    try:
        config = load_niyam_config(root)
        if config and config.guard:
            guard_status = "Enabled" if config.guard.enabled else "Disabled"
            if config.guard.frozen_paths:
                frozen_paths = ", ".join(config.guard.frozen_paths)
    except Exception:
        pass

    # 4. Audit trail run logs
    audit_trail = _get_audit_trail(root)

    # Prepare Jinja2 context
    context = {
        "metadata": {
            "project_name": project_name,
            "branch": git_meta["branch"],
            "commit_sha": git_meta["commit_sha"],
            "commit_author": git_meta["commit_author"],
            "timestamp": timestamp
        },
        "scan": {
            "profile": scan_results.get("profile", "unknown"),
            "score": scan_results.get("score", 0),
            "decision": scan_results.get("decision", "NO_GO"),
            "findings_count": len(findings),
            "findings": findings,
            "critical_high_findings": critical_high,
            "breakdown": breakdown
        },
        "governance": {
            "guard_status": guard_status,
            "frozen_paths": frozen_paths
        },
        "audit_trail": audit_trail
    }

    # 5. Render report
    if fmt == "json":
        report_str = json.dumps(context, indent=2)
    elif fmt == "html":
        template = Template(HTML_TEMPLATE)
        report_str = template.render(context)
    else:  # markdown
        template = Template(MARKDOWN_TEMPLATE)
        report_str = template.render(context)

    # 6. Output to file if requested
    if output:
        output_path = Path(output).resolve()
        try:
            output_path.write_text(report_str, encoding="utf-8")
        except Exception as e:
            raise IOError(f"Failed to write evidence report to file: {e}")

    return report_str
