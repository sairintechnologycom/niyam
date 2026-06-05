"""Niyam governance readiness scoring engine."""

from __future__ import annotations

from typing import Any

# Default weights by dimension for different profiles
# Each profile must sum to 100
PROFILE_WEIGHTS = {
    "startup": {
        "secrets": 20,
        "auth": 15,
        "dependencies": 15,
        "cloud": 15,
        "production_ops": 10,
        "ai_risk": 10,
        "data_protection": 10,
        "documentation": 5,
    },
    "team": {
        "secrets": 25,
        "auth": 15,
        "dependencies": 10,
        "cloud": 15,
        "production_ops": 10,
        "ai_risk": 10,
        "data_protection": 10,
        "documentation": 5,
    },
    "enterprise": {
        "secrets": 30,
        "auth": 20,
        "dependencies": 10,
        "cloud": 15,
        "production_ops": 10,
        "ai_risk": 5,
        "data_protection": 7,
        "documentation": 3,
    },
    "regulated": {
        "secrets": 30,
        "auth": 20,
        "dependencies": 10,
        "cloud": 15,
        "production_ops": 10,
        "ai_risk": 5,
        "data_protection": 7,
        "documentation": 3,
    },
}

# Standard deductions by severity
DEDUCTIONS = {
    "critical": 25,
    "high": 15,
    "medium": 8,
    "low": 3,
    "info": 0,
}

DIMENSION_LABELS = {
    "secrets": "Secrets and credentials",
    "auth": "Authentication and authorization",
    "dependencies": "Dependencies and supply chain",
    "cloud": "Cloud/IaC exposure",
    "production_ops": "Production operations",
    "ai_risk": "AI-specific risks",
    "data_protection": "Data protection",
    "documentation": "Documentation and runbook",
}


def map_finding_to_dimension(finding: dict[str, Any]) -> str:
    """Map a scan finding to one of the 8 scoring dimensions."""
    category = str(finding.get("category", "")).lower().strip()
    fid = str(finding.get("id", "")).upper().strip()
    title = str(finding.get("title", "")).lower()

    # 1. Secrets and credentials
    if (
        category in ("secrets", "secret")
        or fid.startswith("SEC")
        or "GITLEAKS" in fid
        or "secret" in title
        or "private key" in title
    ):
        return "secrets"

    # 2. Authentication and authorization
    if (
        category in ("auth", "authentication", "authorization")
        or fid.startswith("AUT")
        or "auth" in category
        or "auth" in fid
        or "auth" in title
        or "login" in title
        or "permission" in title
    ):
        return "auth"

    # 3. Dependencies and supply chain
    if (
        category in ("dependencies", "dependency", "supply_chain")
        or fid.startswith("DEP")
        or "TRIVY" in fid
        or "lockfile" in title
        or "package" in title
    ):
        return "dependencies"

    # 4. Cloud/IaC exposure
    if (
        category in ("iac", "cloud", "env_config")
        or fid.startswith("ENV")
        or fid.startswith("IAC")
        or "CHECKOV" in fid
        or "terraform" in title
        or "aws" in title
        or "gcp" in title
        or "azure" in title
        or "kubernetes" in title
    ):
        return "cloud"

    # 5. AI-specific risks
    if (
        category in ("ai_risk", "ai", "ai-risk")
        or fid.startswith("AI")
        or "ai" in category
        or "ai" in title
        or "placeholder" in title
        or "stub" in title
    ):
        return "ai_risk"

    # 6. Data protection
    if (
        category in ("data_protection", "data", "privacy", "gdpr", "pii")
        or fid.startswith("DAT")
        or fid.startswith("PRV")
        or "data" in category
        or "privacy" in category
        or "gdpr" in title
        or "encryption" in title
    ):
        return "data_protection"

    # 7. Documentation and runbook
    if (
        category in ("docs", "documentation", "runbook")
        or fid.startswith("DOC")
        or "readme" in title
        or "documentation" in title
    ):
        return "documentation"

    # 8. Production operations (default fallback, covers health, cicd, tests, ops, security)
    return "production_ops"


def calculate_readiness_score(
    findings: list[dict[str, Any]],
    profile: str = "startup",
    custom_weights: dict[str, int] | None = None,
) -> tuple[int, dict[str, int], dict[str, int]]:
    """Calculate deterministic readiness score and breakdown per dimension.

    Returns:
        tuple of (total_score, dimension_scores, dimension_weights)
    """
    # 1. Determine weights to use
    profile_lower = profile.lower()
    weights = PROFILE_WEIGHTS.get(profile_lower, PROFILE_WEIGHTS["startup"])
    if custom_weights:
        weights = {**weights, **custom_weights}

    # Standardize weights sum to 100 or adjust proportionally if custom weights are passed
    total_weight = sum(weights.values())
    if total_weight <= 0:
        # Avoid division by zero
        weights = PROFILE_WEIGHTS["startup"]
        total_weight = 100

    # 2. Group findings by dimension
    findings_by_dimension: dict[str, list[dict[str, Any]]] = {
        dim: [] for dim in weights
    }
    for finding in findings:
        dim = map_finding_to_dimension(finding)
        if dim not in findings_by_dimension:
            # Fallback if dimension is not in weights (e.g. custom dimensions)
            findings_by_dimension[dim] = []
        findings_by_dimension[dim].append(finding)

    # 3. Calculate score per dimension
    dimension_scores = {}
    for dim, dim_weight in weights.items():
        dim_findings = findings_by_dimension.get(dim, [])
        total_deduction = sum(
            DEDUCTIONS.get(f.get("severity", "info").lower(), 0) for f in dim_findings
        )
        dim_score = max(0, dim_weight - total_deduction)
        dimension_scores[dim] = dim_score

    # 4. Calculate total score (0 to 100)
    raw_total = sum(dimension_scores.values())

    # If using custom weights and sum != 100, normalize the score to 0-100 range
    if total_weight != 100:
        total_score = int(round((raw_total / total_weight) * 100))
    else:
        total_score = int(raw_total)

    total_score = max(0, min(100, total_score))
    return total_score, dimension_scores, weights
