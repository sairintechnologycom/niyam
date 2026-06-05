"""Niyam scan baseline and risk acceptance support."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from niyam.governance.common.redaction import redact_text


def parse_iso_datetime(dt_str: str) -> datetime:
    """Safely parse ISO datetime string, supporting Z suffix in Python 3.10+."""
    clean_str = re.sub(r"Z$", "+00:00", dt_str.strip())
    dt = datetime.fromisoformat(clean_str)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def is_hard_blocker(finding: dict[str, Any]) -> bool:
    """Check if the scan finding is classified as a hard blocker."""
    severity = str(finding.get("severity", "")).lower().strip()
    category = str(finding.get("category", "")).lower().strip()
    fid = str(finding.get("id", "")).upper().strip()
    title = str(finding.get("title", "")).lower()
    desc = str(finding.get("description", "")).lower()
    fpath = str(finding.get("file_path", ""))

    # 1. Critical secrets
    if severity == "critical" and (
        category == "secrets" or "GITLEAKS" in fid or "SEC" in fid or "secret" in title
    ):
        return True
    if fid == "SEC001" or Path(fpath).name.startswith(".env"):
        return True

    # 2. Private Key exposure
    if "private key" in title or "private key" in desc or "-----BEGIN" in desc:
        return True

    # 3. Public Cloud Exposure in IaC
    if category in ("iac", "cloud") or "checkov" in fid.lower():
        if severity in ("high", "critical") and (
            "public" in title
            or "public" in desc
            or "expose" in title
            or "expose" in desc
            or "open" in title
            or "open" in desc
        ):
            return True

    # 4. Missing Authentication on API
    if category in ("auth", "authentication", "authorization") or fid.startswith("AUT"):
        if "api" in title or "api" in desc or "route" in title or "route" in desc:
            if (
                "missing" in title
                or "missing" in desc
                or "no auth" in title
                or "no auth" in desc
                or "unauthenticated" in title
                or "unauthenticated" in desc
            ):
                return True

    return False


def load_baseline(path: Path) -> dict[str, Any]:
    """Load, validate, and return baseline JSON mapping."""
    if not path.exists():
        raise FileNotFoundError(f"Baseline file not found at: {path}")

    try:
        import json

        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        raise ValueError(f"Failed to parse baseline JSON file: {e}")

    if not isinstance(data, dict):
        raise ValueError("Baseline file must be a JSON object mapping.")
    if "schema_version" not in data:
        raise ValueError("Baseline is missing required field: schema_version")
    if "accepted_findings" not in data:
        raise ValueError("Baseline is missing required field: accepted_findings")
    if not isinstance(data["accepted_findings"], list):
        raise ValueError("'accepted_findings' must be a list.")

    for idx, entry in enumerate(data["accepted_findings"]):
        if not isinstance(entry, dict):
            raise ValueError(
                f"Baseline finding entry at index {idx} is not a JSON object."
            )
        for field in ("fingerprint", "rule_id", "severity", "reason"):
            if field not in entry:
                raise ValueError(
                    f"Baseline finding entry at index {idx} is missing required field: {field}"
                )

    return data


def apply_baseline(
    findings: list[dict[str, Any]], baseline: dict[str, Any]
) -> list[dict[str, Any]]:
    """Mark findings as accepted_existing or open based on baseline mappings."""
    if not baseline or "accepted_findings" not in baseline:
        for f in findings:
            f["status"] = "open"
        return findings

    # Build lookup by fingerprint
    accepted = {entry["fingerprint"]: entry for entry in baseline["accepted_findings"]}
    now = datetime.now(timezone.utc)

    for f in findings:
        fingerprint = f.get("fingerprint")
        if fingerprint in accepted:
            entry = accepted[fingerprint]

            # Check expiry
            expired = False
            expires_at_str = entry.get("expires_at")
            if expires_at_str:
                try:
                    expires_at = parse_iso_datetime(expires_at_str)
                    if now > expires_at:
                        expired = True
                except Exception:
                    expired = True  # Treat malformed expiry as expired to be safe

            # Blocker checks (must have a reason)
            reason = str(entry.get("reason", "")).strip()
            is_blocker = is_hard_blocker(f)
            has_no_reason = is_blocker and not reason

            if not expired and not has_no_reason:
                f["status"] = "accepted_existing"
            else:
                f["status"] = "open"
        else:
            f["status"] = "open"

    return findings


def save_baseline(
    path: Path, findings: list[dict[str, Any]], project_name: str
) -> None:
    """Serialize scan findings to the baseline JSON file with secret redaction."""
    import json

    accepted_findings = []
    for f in findings:
        accepted_findings.append(
            {
                "fingerprint": f.get("fingerprint"),
                "rule_id": f.get("id"),
                "severity": f.get("severity"),
                "reason": f"Baseline auto-generated on {datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
                "accepted_by": "system",
                "expires_at": None,
            }
        )

    baseline_data = {
        "schema_version": "1.0.0",
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "project": project_name,
        "accepted_findings": accepted_findings,
    }

    path.parent.mkdir(parents=True, exist_ok=True)
    json_str = json.dumps(baseline_data, indent=2)
    redacted_json = redact_text(json_str)
    path.write_text(redacted_json, encoding="utf-8")
