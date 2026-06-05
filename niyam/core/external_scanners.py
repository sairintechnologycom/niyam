"""Niyam external security scanners integration engine (gitleaks, semgrep, trivy, checkov)."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

# Default severity mappings from external tools to Niyam severities
SEVERITY_MAPPINGS = {
    # Semgrep
    "ERROR": "high",
    "WARNING": "medium",
    "INFO": "low",
    # Trivy / Checkov
    "CRITICAL": "critical",
    "HIGH": "high",
    "MEDIUM": "medium",
    "LOW": "low",
}


def run_gitleaks(root: Path) -> list[dict[str, Any]]:
    """Run Gitleaks secrets scanner if installed."""
    if not shutil.which("gitleaks"):
        return []

    findings = []
    # Write report to a temp file to avoid stdout buffering issues
    with tempfile.TemporaryDirectory() as tmpdir:
        report_file = Path(tmpdir) / "gitleaks-report.json"
        cmd = [
            "gitleaks",
            "detect",
            f"--source={root}",
            "--no-git",
            "--report-format=json",
            f"--report-path={report_file}",
        ]

        try:
            # Gitleaks exits with code 8 if leaks are found, 0 if clean, 1+ if error
            res = subprocess.run(
                cmd,
                cwd=root,
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )

            # Read report if exit code is 8 (leaks found) or if file exists
            if (
                res.returncode == 8 or report_file.exists()
            ) and report_file.stat().st_size > 0:
                with open(report_file, encoding="utf-8") as f:
                    leaks = json.load(f)
                    for leak in leaks:
                        file_path = leak.get("File", "")
                        # Make path relative to root if absolute
                        try:
                            file_path = str(Path(file_path).relative_to(root))
                        except ValueError:
                            pass

                        findings.append(
                            {
                                "id": f"EXT-GITLEAKS-{leak.get('RuleID', 'UNKNOWN')}",
                                "title": f"Gitleaks Secret Detected: {leak.get('Description', 'Credential')}",
                                "category": "secrets",
                                "severity": "critical",
                                "file_path": file_path,
                                "description": (
                                    f"Found hardcoded credentials matching rule ID '{leak.get('RuleID')}' "
                                    f"in {file_path} at line {leak.get('StartLine')}."
                                ),
                                "recommendation": (
                                    "Remove the hardcoded secret immediately. Rotate the credential "
                                    "and ensure the file is gitignored or the secret is moved to a vault."
                                ),
                            }
                        )
        except Exception:
            pass

    return findings


def run_semgrep(root: Path) -> list[dict[str, Any]]:
    """Run Semgrep code analyzer if installed."""
    if not shutil.which("semgrep"):
        return []

    cmd = ["semgrep", "scan", "--config=auto", "--json", "--quiet"]
    findings = []

    try:
        res = subprocess.run(
            cmd,
            cwd=root,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )

        if res.returncode in (0, 1) and res.stdout:
            data = json.loads(res.stdout)
            results = data.get("results", [])
            for r in results:
                file_path = r.get("path", "")
                extra = r.get("extra", {})
                sev = SEVERITY_MAPPINGS.get(
                    extra.get("severity", "WARNING").upper(), "medium"
                )
                check_id = r.get("check_id", "semgrep-finding")

                findings.append(
                    {
                        "id": f"EXT-SEMGREP-{check_id.split('.')[-1]}",
                        "title": f"Semgrep Rule Violation: {check_id}",
                        "category": "security",
                        "severity": sev,
                        "file_path": file_path,
                        "description": extra.get(
                            "message", "Semgrep security vulnerability found."
                        ),
                        "recommendation": (
                            "Review the code logic, apply appropriate input/output sanitization, "
                            "or refactor using safe standard libraries."
                        ),
                    }
                )
    except Exception:
        pass

    return findings


def run_trivy(root: Path) -> list[dict[str, Any]]:
    """Run Trivy dependency vulnerability scanner if installed."""
    if not shutil.which("trivy"):
        return []

    cmd = ["trivy", "fs", "--format", "json", "--quiet", "."]
    findings = []

    try:
        res = subprocess.run(
            cmd,
            cwd=root,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )

        if res.returncode == 0 and res.stdout:
            data = json.loads(res.stdout)
            results = data.get("Results", []) or []
            for r in results:
                target = r.get("Target", "")
                vulns = r.get("Vulnerabilities", []) or []
                for v in vulns:
                    vuln_id = v.get("VulnerabilityID", "UNKNOWN")
                    pkg = v.get("PkgName", "package")
                    sev = SEVERITY_MAPPINGS.get(
                        v.get("Severity", "MEDIUM").upper(), "medium"
                    )
                    installed = v.get("InstalledVersion", "")
                    fixed = v.get("FixedVersion", "N/A")

                    findings.append(
                        {
                            "id": f"EXT-TRIVY-{vuln_id}",
                            "title": f"Trivy Vulnerable Package: {pkg} ({vuln_id})",
                            "category": "dependencies",
                            "severity": sev,
                            "file_path": target,
                            "description": (
                                f"Package '{pkg}' (installed version {installed}) is vulnerable. "
                                f"Title: {v.get('Title', 'Vulnerability')}. Details: {v.get('Description', '')}"
                            ),
                            "recommendation": f"Upgrade '{pkg}' to version {fixed} or higher to resolve this vulnerability.",
                        }
                    )
    except Exception:
        pass

    return findings


def run_checkov(root: Path) -> list[dict[str, Any]]:
    """Run Checkov IaC scanner if installed."""
    if not shutil.which("checkov"):
        return []

    cmd = ["checkov", "-d", ".", "--output", "json"]
    findings = []

    try:
        res = subprocess.run(
            cmd,
            cwd=root,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )

        if res.stdout:
            try:
                data = json.loads(res.stdout)
            except json.JSONDecodeError:
                return []

            # Checkov output can be a single dict or a list of dicts (if multiple runners run)
            results_list = data if isinstance(data, list) else [data]

            for report in results_list:
                failed_checks = report.get("results", {}).get("failed_checks", []) or []
                for c in failed_checks:
                    check_id = c.get("check_id", "CKV_UNKNOWN")
                    file_path = c.get("file_path", "")
                    # Strip leading slash from file_path if present
                    if file_path.startswith("/"):
                        file_path = file_path[1:]

                    sev = SEVERITY_MAPPINGS.get(
                        c.get("severity", "MEDIUM").upper(), "medium"
                    )

                    findings.append(
                        {
                            "id": f"EXT-CHECKOV-{check_id}",
                            "title": f"Checkov IaC Finding: {c.get('check_name', check_id)}",
                            "category": "iac",
                            "severity": sev,
                            "file_path": file_path,
                            "description": f"IaC validation failed check '{check_id}' at line range {c.get('file_line_range', '')}.",
                            "recommendation": (
                                f"Update configuration parameters to comply with check rule '{check_id}'. "
                                "Refer to checkov.io guidelines."
                            ),
                        }
                    )
    except Exception:
        pass

    return findings


def run_all_external_scanners(root: Path) -> list[dict[str, Any]]:
    """Execute all installed external scanners and aggregate findings."""
    root = Path(root).resolve()
    findings = []

    findings.extend(run_gitleaks(root))
    findings.extend(run_semgrep(root))
    findings.extend(run_trivy(root))
    findings.extend(run_checkov(root))

    return findings
