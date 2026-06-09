"""Niyam governance readiness launch decision engine."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from niyam.governance.common.redaction import contains_secret

logger = logging.getLogger(__name__)


def evaluate_decision(
    findings: list[dict[str, Any]],
    score: int,
    profile: str = "startup",
    project_root: Path | None = None,
) -> tuple[str, str, int]:
    """Evaluate readiness score and blocker rules to determine launch decision.

    Returns:
        tuple of (decision, decision_reason, overridden_score)
    """
    decision = "GO"
    decision_reason = "Scan completed successfully."
    overridden_score = score

    # Track which blocker rules were triggered
    triggered_blockers = []

    # 1. Check critical secrets findings or private key exposure
    has_critical_secret = False
    has_private_key = False

    for f in findings:
        severity = f.get("severity", "").lower()
        category = f.get("category", "").lower()
        fid = f.get("id", "").upper()
        title = f.get("title", "").lower()
        desc = f.get("description", "").lower()
        fpath = f.get("file_path", "")

        # Blocker 1: critical secrets finding
        if severity == "critical" and (
            category == "secrets"
            or "GITLEAKS" in fid
            or "SEC" in fid
            or "secret" in title
        ):
            has_critical_secret = True
            triggered_blockers.append(
                "Critical secrets finding detected in repository."
            )

        # Also look for .env file secrets using our existing code logic
        if fid == "SEC001" or (fpath and Path(fpath).name.startswith(".env")):
            if project_root:
                try:
                    env_path = project_root / fpath
                    if env_path.is_file():
                        env_content = env_path.read_text(
                            encoding="utf-8", errors="ignore"
                        )
                        if contains_secret(env_content) or any(
                            line.strip() and "=" in line
                            for line in env_content.splitlines()
                        ):
                            has_critical_secret = True
                            triggered_blockers.append(
                                "Committed environment configuration file (.env) with possible secrets."
                            )
                except Exception as e:
                    logger.debug("Failed to check .env file %s: %s", fpath, e)

        # Blocker 2: private key exposure
        # Check both finding descriptions and file content if available
        if "private key" in title or "private key" in desc or "-----BEGIN" in desc:
            has_private_key = True
            triggered_blockers.append("Private key exposure detected in findings.")

        if project_root and fpath:
            try:
                file_p = project_root / fpath
                if file_p.is_file():
                    content = file_p.read_text(encoding="utf-8", errors="ignore")
                    if "-----BEGIN" in content and "PRIVATE KEY" in content:
                        has_private_key = True
                        triggered_blockers.append(
                            f"Obvious private key committed in source code: {fpath}"
                        )
            except Exception as e:
                logger.debug("Failed to check file content for private keys in %s: %s", fpath, e)

        # Check for public cloud exposure patterns in file content
        if project_root and fpath:
            try:
                file_p = project_root / fpath
                if file_p.is_file():
                    content = file_p.read_text(encoding="utf-8", errors="ignore")
                    if "AKIA" in content or "AccountKey=" in content:
                        has_critical_secret = True
                        triggered_blockers.append(
                            f"Public cloud exposure pattern detected in source code: {fpath}"
                        )
            except Exception as e:
                logger.debug("Failed to check file content for cloud patterns in %s: %s", fpath, e)

    # 2. Blocker 3: no auth on detected API in enterprise profile
    # Let's inspect findings to see if there is a missing auth on API
    # We can detect if category is "auth", "authentication", or "authorization" and description/title contains "missing" or "no" or "unauthenticated"
    # Or if finding ID contains API and AUT or title contains "api" and "auth"
    has_no_auth_on_api = False
    if profile.lower() in ("enterprise", "regulated"):
        for f in findings:
            category = f.get("category", "").lower()
            fid = f.get("id", "").upper()
            title = f.get("title", "").lower()
            desc = f.get("description", "").lower()

            is_api_missing_auth = (
                (
                    category in ("auth", "authentication", "authorization")
                    or fid.startswith("AUT")
                )
                and (
                    "api" in title
                    or "api" in desc
                    or "route" in title
                    or "route" in desc
                )
                and (
                    "missing" in title
                    or "missing" in desc
                    or "no auth" in title
                    or "no auth" in desc
                    or "unauthenticated" in title
                    or "unauthenticated" in desc
                )
            )
            if is_api_missing_auth:
                has_no_auth_on_api = True
                triggered_blockers.append(
                    f"No authentication/authorization configured on detected API: {f.get('title')}"
                )

    # 3. Blocker 4: high/critical public IaC exposure
    # Check findings for high/critical severity and category "iac" or "cloud" with "public" in title/description
    has_public_iac_exposure = False
    for f in findings:
        severity = f.get("severity", "").lower()
        category = f.get("category", "").lower()
        title = f.get("title", "").lower()
        desc = f.get("description", "").lower()

        if severity in ("high", "critical") and (
            category in ("iac", "cloud") or "checkov" in f.get("id", "").lower()
        ):
            if (
                "public" in title
                or "public" in desc
                or "expose" in title
                or "expose" in desc
                or "open" in title
                or "open" in desc
            ):
                has_public_iac_exposure = True
                triggered_blockers.append(
                    f"High/Critical public IaC exposure detected: {f.get('title')}"
                )

    # 4. Blocker 5: more than 3 high findings => HIGH_RISK maximum
    # Count findings with severity "high"
    high_count = sum(1 for f in findings if f.get("severity", "").lower() == "high")
    has_many_high_findings = high_count > 3
    if has_many_high_findings:
        triggered_blockers.append(
            f"More than 3 High findings detected ({high_count} found)."
        )

    # Evaluate blockers override:
    # First: NO_GO blockers
    if (
        has_critical_secret
        or has_private_key
        or (profile.lower() == "enterprise" and has_no_auth_on_api)
    ):
        decision = "NO_GO"
        # Overridden score is min(49, score) to force it below 50
        overridden_score = min(49, score)
        
        # Deduplicate and limit reason length
        unique_blockers = []
        for b in triggered_blockers:
            if b not in unique_blockers:
                unique_blockers.append(b)
        
        reason_text = " | ".join(unique_blockers[:5])
        if len(unique_blockers) > 5:
            reason_text += f" (and {len(unique_blockers) - 5} more...)"
            
        decision_reason = "Hard blocker triggered: " + reason_text
    # Second: HIGH_RISK blockers or public IaC exposure
    elif has_public_iac_exposure or has_many_high_findings:
        decision = "HIGH_RISK"
        overridden_score = min(69, score)
        
        # Deduplicate
        unique_blockers = []
        for b in triggered_blockers:
            if b not in unique_blockers:
                unique_blockers.append(b)
        decision_reason = "Hard blocker triggered: " + " | ".join(unique_blockers)
    else:
        # Decision based on score
        if score >= 90:
            decision = "GO"
        elif score >= 75:
            decision = "CONDITIONAL_GO"
        elif score >= 50:
            decision = "HIGH_RISK"
        else:
            decision = "NO_GO"
            decision_reason = "Readiness score is below 50."


    return decision, decision_reason, overridden_score
