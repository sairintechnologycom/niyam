"""Niyam evidence generator — audit-ready report builder."""

from __future__ import annotations

import json
import logging
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jinja2 import Template

from niyam.core.config import find_niyam_root, load_niyam_config

logger = logging.getLogger(__name__)

# ── Template Loading ───────────────────────────────────────────────────


def _load_template(filename: str) -> str:
    """Load a Jinja2 template from the niyam/templates directory."""
    template_path = Path(__file__).parent.parent / "templates" / filename
    if not template_path.exists():
        return f"# Error: Template {filename} not found at {template_path}\n"
    return template_path.read_text(encoding="utf-8")



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
                except Exception as e:
                    logger.debug("Failed to read mission plan %s: %s", plan_file, e)

            if ledger_file.exists():
                try:
                    with open(ledger_file, encoding="utf-8") as f:
                        ledger_data = json.load(f) or {}
                    events = ledger_data.get("events", [])
                    run_info["cost_usd"] = sum(
                        float(e.get("cost_usd", 0.0)) for e in events
                    )
                except Exception as e:
                    logger.debug("Failed to read cost ledger %s: %s", ledger_file, e)

            trail.append(run_info)

    return trail


def _get_guard_logs(repo_root: Path) -> list[dict[str, Any]]:
    """Load all guard observed commands logs."""
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
    return logs


def _get_top_command_categories(logs: list[dict[str, Any]]) -> list[str]:
    """Extract top command categories/executables from logs."""
    categories: dict[str, int] = {}
    for log in logs:
        cmd = log.get("command", "")
        if not cmd:
            continue
        # Extract the first token of the command
        tokens = cmd.split()
        if tokens:
            executable = tokens[0]
            # Strip path if it looks like an absolute/relative path
            executable = Path(executable).name
            categories[executable] = categories.get(executable, 0) + 1

    # Sort categories by count descending
    sorted_cats = sorted(categories.items(), key=lambda x: x[1], reverse=True)
    return [f"{exe} ({count})" for exe, count in sorted_cats[:5]]


def _get_violations(guard_logs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Extract failed or problematic actions from guard logs."""
    violations = []
    for log in guard_logs:
        if log.get("exit_code", 0) != 0:
            violations.append(log)
    return violations


def _get_mcp_data(repo_root: Path) -> dict[str, Any]:
    """Retrieve MCP/Tool registry analytics."""
    from niyam.core.mcp import get_mcp_registry_path, load_mcp_registry
    from niyam.governance.common.redaction import redact_secrets

    path = get_mcp_registry_path(repo_root)
    exists = path.exists()

    if not exists:
        return {
            "exists": False,
            "total": 0,
            "approved": 0,
            "unapproved": 0,
            "high_risk": 0,
            "critical_risk": 0,
            "unapproved_high_critical_count": 0,
            "tools": [],
            "unapproved_high": [],
            "unapproved_high_critical_tools": [],
            "recommended_actions": [],
        }

    try:
        registry = load_mcp_registry(repo_root)
        tools_list = list(registry.tools.values())
    except Exception:
        tools_list = []

    total = len(tools_list)
    approved = sum(1 for t in tools_list if t.approved)
    unapproved = total - approved
    high_risk = sum(1 for t in tools_list if t.risk_level == "high")
    critical_risk = sum(1 for t in tools_list if t.risk_level == "critical")

    unapproved_high_critical = [
        t for t in tools_list if not t.approved and t.risk_level in ("high", "critical")
    ]
    unapproved_high_critical_count = len(unapproved_high_critical)

    # Build recommended actions for all unapproved tools
    recommended_actions = []
    for t in tools_list:
        if not t.approved:
            recommended_actions.append(
                {
                    "tool": t.name,
                    "risk_level": t.risk_level,
                    "action": f"Approve tool '{t.name}' (Risk: {t.risk_level}) via 'niyam mcp approve {t.name}'.",
                }
            )

    # Redact sensitive fields of tools
    redacted_tools = [redact_secrets(t.model_dump()) for t in tools_list]
    redacted_unapproved_high_critical = [
        redact_secrets(t.model_dump()) for t in unapproved_high_critical
    ]

    return {
        "exists": True,
        "total": total,
        "approved": approved,
        "unapproved": unapproved,
        "high_risk": high_risk,
        "critical_risk": critical_risk,
        "unapproved_high_critical_count": unapproved_high_critical_count,
        "tools": redacted_tools,
        "unapproved_high": redacted_unapproved_high_critical,
        "unapproved_high_critical_tools": redacted_unapproved_high_critical,
        "recommended_actions": recommended_actions,
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
    mission_id: str | None = None,
) -> str:
    """Generate evidence report locally and return the formatted output string."""
    root = find_niyam_root()
    if root is None:
        root = Path.cwd()

    include_list = [s.strip() for s in include.split(",")]

    # 0. Find the best scan report input
    scan_json_path = None
    
    if from_scan_json:
        scan_json_path = Path(from_scan_json).resolve()
        if not scan_json_path.exists():
            raise FileNotFoundError(f"Scan JSON file not found at: {from_scan_json}")
    elif mission_id:
        from niyam.mission.planner import resolve_mission_id
        try:
            m_id = resolve_mission_id(root, mission_id)
            run_dir = root / ".niyam" / "runs" / m_id
            for fname in ["scan-report.json", "scan.json"]:
                if (run_dir / fname).exists():
                    scan_json_path = run_dir / fname
                    break
        except Exception:
            pass

    if not scan_json_path:
        # Search for default scan report under .niyam/reports/scan.json
        for candidate in [
            root / ".niyam" / "reports" / "scan.json",
            root / ".niyam" / "scan-report.json",
            root / ".sutra" / "reports" / "scan.json"
        ]:
            if candidate.exists():
                scan_json_path = candidate
                break

    if not scan_json_path:
         # Final fallback: create a dummy "clean" scan result if we just want a report of other things
         scan_results = {
             "score": 100,
             "findings": [],
             "decision": "GO",
             "generated_at": datetime.now(timezone.utc).isoformat()
         }
    else:
        try:
            with open(scan_json_path, encoding="utf-8") as f:
                scan_results = json.load(f)
        except Exception as e:
            raise ValueError(f"Failed to parse scan JSON file {scan_json_path}: {e}")

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

    # Load MCP data early to allow finding injection if high/critical unapproved
    mcp_data = (
        _get_mcp_data(root)
        if "mcp" in include_list
        else {
            "exists": False,
            "total": 0,
            "approved": 0,
            "unapproved": 0,
            "high_risk": 0,
            "critical_risk": 0,
            "unapproved_high_critical_count": 0,
            "tools": [],
            "unapproved_high": [],
            "unapproved_high_critical_tools": [],
            "recommended_actions": [],
        }
    )

    # 2. Findings breakdown & critical/high counts
    findings = list(scan_results.get("findings", []))

    # Inject findings from MCP risk report if high/critical unapproved
    if "mcp" in include_list and mcp_data.get("exists", False):
        for tool in mcp_data.get("unapproved_high_critical_tools", []):
            findings.append(
                {
                    "id": f"MCP-{tool['name']}",
                    "title": f"Unapproved {tool['risk_level'].capitalize()}-Risk Tool: {tool['name']}",
                    "category": "mcp",
                    "severity": tool["risk_level"],
                    "file_path": "",
                    "description": f"The tool '{tool['name']}' is registered with {tool['risk_level']} risk level but is not approved.",
                    "recommendation": f"Approve the tool using 'niyam mcp approve {tool['name']}' if it is safe to use.",
                }
            )

    critical_high = [f for f in findings if f.get("severity") in ("critical", "high")]

    breakdown = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    for f in findings:
        sev = f.get("severity", "info").lower()
        if sev in breakdown:
            breakdown[sev] += 1

    # 3. Dynamic loaders for sections
    guard_logs_all = _get_guard_logs(root) if "guard" in include_list else []

    # Calculate guard action metrics
    guard_summary = None
    if "guard" in include_list and guard_logs_all:
        total_actions = len(guard_logs_all)
        total_blocked = sum(
            1
            for log in guard_logs_all
            if log.get("decision") in ("blocked", "denied")
            or log.get("policy_decision") == "block"
        )
        total_warned = sum(
            1
            for log in guard_logs_all
            if log.get("decision") == "warned" or log.get("policy_decision") == "warn"
        )
        total_approval_required = sum(
            1
            for log in guard_logs_all
            if log.get("policy_decision") == "approval_required"
            or log.get("decision") in ("denied", "approved")
        )
        total_failed = sum(
            1
            for log in guard_logs_all
            if log.get("exit_code", 0) != 0
            and log.get("decision") not in ("blocked", "denied")
            and log.get("policy_decision") != "block"
        )

        top_command_categories = _get_top_command_categories(guard_logs_all)

        latest_session_id = None
        latest_session_logs = []
        if guard_logs_all:
            latest_session_id = guard_logs_all[-1].get("session_id")
            if latest_session_id:
                latest_session_logs = [
                    log
                    for log in guard_logs_all
                    if log.get("session_id") == latest_session_id
                ]

        latest_session_details = {
            "session_id": latest_session_id,
            "total_actions": len(latest_session_logs),
            "total_blocked": sum(
                1
                for log in latest_session_logs
                if log.get("decision") in ("blocked", "denied")
                or log.get("policy_decision") == "block"
            ),
            "total_warned": sum(
                1
                for log in latest_session_logs
                if log.get("decision") == "warned"
                or log.get("policy_decision") == "warn"
            ),
            "total_approval_required": sum(
                1
                for log in latest_session_logs
                if log.get("policy_decision") == "approval_required"
                or log.get("decision") in ("denied", "approved")
            ),
            "total_failed": sum(
                1
                for log in latest_session_logs
                if log.get("exit_code", 0) != 0
                and log.get("decision") not in ("blocked", "denied")
                and log.get("policy_decision") != "block"
            ),
        }

        guard_summary = {
            "total_actions": total_actions,
            "total_blocked": total_blocked,
            "total_warned": total_warned,
            "total_approval_required": total_approval_required,
            "total_failed": total_failed,
            "top_command_categories": top_command_categories,
            "latest_session": latest_session_details,
            "latest_actions_summary": [
                {
                    "timestamp": log.get("timestamp"),
                    "session_id": log.get("session_id"),
                    "actor_type": log.get("actor_type"),
                    "command": log.get("command"),
                    "exit_code": log.get("exit_code"),
                    "duration_ms": log.get("duration_ms"),
                    "policy_decision": log.get("policy_decision"),
                    "decision": log.get("decision"),
                }
                for log in guard_logs_all[-5:]
            ],
        }

    guard_logs = guard_logs_all[-10:]
    violations = _get_violations(guard_logs_all) if "guard" in include_list else []

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
        "info": breakdown.get("info", 0),
    }

    findings_summary = [
        {
            "id": f.get("id"),
            "severity": f.get("severity"),
            "category": f.get("category"),
            "title": f.get("title"),
            "file_path": f.get("file_path"),
        }
        for f in findings
    ]

    remediation_plan = [
        {
            "id": f.get("id"),
            "title": f.get("title"),
            "severity": f.get("severity"),
            "recommendation": f.get("recommendation"),
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
        "decision_reason": scan_results.get(
            "decision_reason", "Scan completed successfully."
        ),
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
        "guard_summary": guard_summary,
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
        template_str = _load_template("evidence_html.j2")
        template = Template(template_str)
        report_str = template.render(context)
    else:  # markdown
        template_str = _load_template("evidence_markdown.j2")
        template = Template(template_str)
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
