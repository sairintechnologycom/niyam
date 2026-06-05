"""Unit and integration tests for Niyam external security scanners."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from niyam.core.external_scanners import (
    run_checkov,
    run_gitleaks,
    run_semgrep,
    run_trivy,
)
from niyam.core.scan import run_scanner_checks


def test_run_gitleaks_not_installed() -> None:
    """If gitleaks is not on PATH, it should return no findings."""
    with patch("shutil.which", return_value=None):
        findings = run_gitleaks(Path("."))
        assert findings == []


def test_run_gitleaks_installed_with_findings(tmp_path: Path) -> None:
    """If gitleaks is installed and finds leaks, they should be parsed correctly."""
    mock_report = [
        {
            "Description": "AWS Access Key ID",
            "StartLine": 10,
            "EndLine": 10,
            "File": str(tmp_path / "config.py"),
            "RuleID": "aws-access-key-id",
            "Secret": "AKIAIOSFODNN7EXAMPLE",
        }
    ]

    def mock_subprocess_run(cmd, **kwargs):
        # The 5th arg in cmd is the report-path option: f"--report-path={report_file}"
        report_opt = [arg for arg in cmd if arg.startswith("--report-path=")][0]
        report_file = Path(report_opt.split("=", 1)[1])
        # Write mock report
        report_file.write_text(json.dumps(mock_report), encoding="utf-8")
        return MagicMock(returncode=8)

    with (
        patch("shutil.which", return_value="/usr/local/bin/gitleaks"),
        patch("subprocess.run", side_effect=mock_subprocess_run),
    ):
        findings = run_gitleaks(tmp_path)

        assert len(findings) == 1
        f = findings[0]
        assert f["id"] == "EXT-GITLEAKS-aws-access-key-id"
        assert "AWS Access Key ID" in f["title"]
        assert f["category"] == "secrets"
        assert f["severity"] == "critical"
        assert f["file_path"] == "config.py"
        assert "config.py" in f["description"]
        assert "line 10" in f["description"]


def test_run_semgrep_installed_with_findings(tmp_path: Path) -> None:
    """If semgrep is installed and returns findings, they should be parsed correctly."""
    mock_output = {
        "results": [
            {
                "check_id": "rules.xss-vulnerability",
                "path": "app.js",
                "start": {"line": 15},
                "extra": {
                    "message": "Potential Cross-Site Scripting (XSS) via innerHTML",
                    "severity": "ERROR",
                },
            }
        ]
    }

    mock_res = MagicMock(returncode=0, stdout=json.dumps(mock_output))

    with (
        patch("shutil.which", return_value="/usr/local/bin/semgrep"),
        patch("subprocess.run", return_value=mock_res),
    ):
        findings = run_semgrep(tmp_path)

        assert len(findings) == 1
        f = findings[0]
        assert f["id"] == "EXT-SEMGREP-xss-vulnerability"
        assert "rules.xss-vulnerability" in f["title"]
        assert f["category"] == "security"
        assert f["severity"] == "high"
        assert f["file_path"] == "app.js"
        assert "innerHTML" in f["description"]


def test_run_trivy_installed_with_findings(tmp_path: Path) -> None:
    """If trivy is installed and returns findings, they should be parsed correctly."""
    mock_output = {
        "Results": [
            {
                "Target": "package-lock.json",
                "Vulnerabilities": [
                    {
                        "VulnerabilityID": "CVE-2023-12345",
                        "PkgName": "lodash",
                        "Severity": "CRITICAL",
                        "InstalledVersion": "4.17.20",
                        "FixedVersion": "4.17.21",
                        "Title": "Prototype Pollution in lodash",
                        "Description": "Prototype pollution vulnerability exists in lodash...",
                    }
                ],
            }
        ]
    }

    mock_res = MagicMock(returncode=0, stdout=json.dumps(mock_output))

    with (
        patch("shutil.which", return_value="/usr/local/bin/trivy"),
        patch("subprocess.run", return_value=mock_res),
    ):
        findings = run_trivy(tmp_path)

        assert len(findings) == 1
        f = findings[0]
        assert f["id"] == "EXT-TRIVY-CVE-2023-12345"
        assert "lodash" in f["title"]
        assert f["category"] == "dependencies"
        assert f["severity"] == "critical"
        assert f["file_path"] == "package-lock.json"
        assert "installed version 4.17.20" in f["description"]
        assert (
            "FixedVersion" not in f["recommendation"]
        )  # FixedVersion used in recommendation string
        assert "4.17.21" in f["recommendation"]


def test_run_checkov_installed_with_findings(tmp_path: Path) -> None:
    """If checkov is installed and returns findings, they should be parsed correctly."""
    mock_output = {
        "results": {
            "failed_checks": [
                {
                    "check_id": "CKV_AWS_20",
                    "check_name": "Ensure S3 bucket has MFA delete enabled",
                    "file_path": "/infra/s3.tf",
                    "severity": "MEDIUM",
                    "file_line_range": [1, 10],
                }
            ]
        }
    }

    mock_res = MagicMock(returncode=0, stdout=json.dumps(mock_output))

    with (
        patch("shutil.which", return_value="/usr/local/bin/checkov"),
        patch("subprocess.run", return_value=mock_res),
    ):
        findings = run_checkov(tmp_path)

        assert len(findings) == 1
        f = findings[0]
        assert f["id"] == "EXT-CHECKOV-CKV_AWS_20"
        assert "MFA delete enabled" in f["title"]
        assert f["category"] == "iac"
        assert f["severity"] == "medium"
        assert f["file_path"] == "infra/s3.tf"
        assert "[1, 10]" in f["description"]


def test_run_scanner_checks_integrates_external_scanners(tmp_path: Path) -> None:
    """Main scan entry point run_scanner_checks should successfully compile external scanner findings."""
    readme = tmp_path / "README.md"
    readme.write_text("# Mock repo\n")
    (tmp_path / "test_main.py").write_text("")

    mock_findings = [
        {
            "id": "EXT-GITLEAKS-mock",
            "title": "Mock secret",
            "category": "secrets",
            "severity": "critical",
            "file_path": "config.js",
            "description": "mock leak",
            "recommendation": "fix mock",
        }
    ]

    with patch(
        "niyam.core.external_scanners.run_all_external_scanners",
        return_value=mock_findings,
    ):
        results = run_scanner_checks(tmp_path, profile="startup")

        assert results is not None
        assert results["score"] < 100  # Deduction applied
        assert any(f["id"] == "EXT-GITLEAKS-mock" for f in results["findings"])
        # With new scoring, critical secret blocks and overrides score to 49 and decision to NO_GO
        assert results["score"] == 49
        assert results["decision"] == "NO_GO"


def test_scanner_checks_reports_skipped_scanners(tmp_path: Path) -> None:
    """If external binaries are missing, run_scanner_checks should list them in skipped_scanners."""
    with patch("shutil.which", return_value=None):
        results = run_scanner_checks(tmp_path, profile="startup")
        assert "skipped_scanners" in results
        assert set(results["skipped_scanners"]) == {
            "gitleaks",
            "semgrep",
            "trivy",
            "checkov",
        }
