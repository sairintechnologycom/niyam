"""Niyam external security scanners integration engine (gitleaks, semgrep, trivy, checkov)."""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

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


class BaseScanner(ABC):
    """Abstract base class for all external scanner adapters."""

    def __init__(self, name: str, binary: str):
        self.name = name
        self.binary = binary

    def is_available(self) -> bool:
        """Check if the scanner binary is available in the current environment."""
        return shutil.which(self.binary) is not None

    @abstractmethod
    def run(self, root: Path, config: dict[str, Any]) -> list[dict[str, Any]]:
        """Execute the scanner and return findings."""
        pass


class GitleaksScanner(BaseScanner):
    def __init__(self):
        super().__init__("gitleaks", "gitleaks")

    def run(self, root: Path, config: dict[str, Any]) -> list[dict[str, Any]]:
        if not self.is_available():
            return []

        findings = []
        with tempfile.TemporaryDirectory() as tmpdir:
            report_file = Path(tmpdir) / "gitleaks-report.json"
            cmd = [
                self.binary,
                "detect",
                f"--source={root}",
                "--no-git",
                "--report-format=json",
                f"--report-path={report_file}",
            ]

            try:
                res = subprocess.run(
                    cmd,
                    cwd=root,
                    capture_output=True,
                    text=True,
                    timeout=60,
                    check=False,
                )

                if (
                    res.returncode == 8 or report_file.exists()
                ) and report_file.stat().st_size > 0:
                    with open(report_file, encoding="utf-8") as f:
                        leaks = json.load(f)
                        for leak in leaks:
                            file_path = leak.get("File", "")
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
            except subprocess.TimeoutExpired:
                logger.warning("Gitleaks execution timed out")
            except Exception as e:
                logger.debug("Failed to run Gitleaks: %s", e, exc_info=True)

        return findings


class SemgrepScanner(BaseScanner):
    def __init__(self):
        super().__init__("semgrep", "semgrep")

    def run(self, root: Path, config: dict[str, Any]) -> list[dict[str, Any]]:
        if not self.is_available():
            return []

        cmd = [self.binary, "scan", "--config=auto", "--json", "--quiet"]
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
        except subprocess.TimeoutExpired:
            logger.warning("Semgrep execution timed out")
        except Exception as e:
            logger.debug("Failed to run Semgrep: %s", e, exc_info=True)

        return findings


class TrivyScanner(BaseScanner):
    def __init__(self):
        super().__init__("trivy", "trivy")

    def run(self, root: Path, config: dict[str, Any]) -> list[dict[str, Any]]:
        if not self.is_available():
            return []

        cmd = [self.binary, "fs", "--format", "json", "--quiet", "."]
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
        except subprocess.TimeoutExpired:
            logger.warning("Trivy execution timed out")
        except Exception as e:
            logger.debug("Failed to run Trivy: %s", e, exc_info=True)

        return findings


class CheckovScanner(BaseScanner):
    def __init__(self):
        super().__init__("checkov", "checkov")

    def run(self, root: Path, config: dict[str, Any]) -> list[dict[str, Any]]:
        if not self.is_available():
            return []

        cmd = [self.binary, "-d", ".", "--output", "json"]
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

                results_list = data if isinstance(data, list) else [data]

                for report in results_list:
                    failed_checks = (
                        report.get("results", {}).get("failed_checks", []) or []
                    )
                    for c in failed_checks:
                        check_id = c.get("check_id", "CKV_UNKNOWN")
                        file_path = c.get("file_path", "")
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
        except subprocess.TimeoutExpired:
            logger.warning("Checkov execution timed out")
        except Exception as e:
            logger.debug("Failed to run Checkov: %s", e, exc_info=True)

        return findings


SCANNER_REGISTRY: list[BaseScanner] = [
    GitleaksScanner(),
    SemgrepScanner(),
    TrivyScanner(),
    CheckovScanner(),
]


def run_all_external_scanners(
    root: Path, config: dict[str, Any] | None = None
) -> list[dict[str, Any]]:
    """Execute all registered external scanners and aggregate findings."""
    root = Path(root).resolve()
    findings = []

    scanner_config = config.get("external_scanners", {}) if config else {}

    for scanner in SCANNER_REGISTRY:
        # Check if enabled in config (default True)
        enabled = scanner_config.get(scanner.name, {}).get("enabled", True)
        if not enabled:
            logger.debug("Scanner %s is disabled in configuration", scanner.name)
            continue

        findings.extend(scanner.run(root, scanner_config.get(scanner.name, {})))

    return findings


# Maintain functional wrappers for backward compatibility
def run_gitleaks(root: Path) -> list[dict[str, Any]]:
    return GitleaksScanner().run(root, {})


def run_semgrep(root: Path) -> list[dict[str, Any]]:
    return SemgrepScanner().run(root, {})


def run_trivy(root: Path) -> list[dict[str, Any]]:
    return TrivyScanner().run(root, {})


def run_checkov(root: Path) -> list[dict[str, Any]]:
    return CheckovScanner().run(root, {})
