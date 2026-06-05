"""Unit tests for the Niyam governance readiness scoring and decision engine."""

from __future__ import annotations

from pathlib import Path

from niyam.governance.scoring import calculate_readiness_score
from niyam.governance.decision import evaluate_decision


def test_scoring_no_findings() -> None:
    """Test that zero findings yields a perfect score of 100 and GO decision."""
    findings = []

    # Check scoring
    score, breakdown, weights = calculate_readiness_score(findings, profile="startup")
    assert score == 100
    for dim, weight in weights.items():
        assert breakdown[dim] == weight

    # Check decision
    decision, reason, overridden_score = evaluate_decision(
        findings, score, profile="startup"
    )
    assert decision == "GO"
    assert overridden_score == 100
    assert reason == "Scan completed successfully."


def test_scoring_critical_secret_no_go() -> None:
    """Test that one critical secret finding forces a NO_GO decision and caps the score."""
    findings = [
        {
            "id": "SEC002",
            "title": "Hardcoded Secrets Detected",
            "category": "secrets",
            "severity": "critical",
            "description": "Found a pattern matching standard secrets.",
            "recommendation": "Move secrets to env variables.",
            "file_path": "main.py",
        }
    ]

    score, breakdown, weights = calculate_readiness_score(findings, profile="startup")
    # startup secrets weight is 20, deduction is 25 => secrets score is 0. Total score = 100 - 20 = 80.
    assert score == 80
    assert breakdown["secrets"] == 0

    decision, reason, overridden_score = evaluate_decision(
        findings, score, profile="startup"
    )
    assert decision == "NO_GO"
    assert overridden_score <= 49
    assert "critical secrets finding" in reason.lower() or "secrets" in reason.lower()


def test_scoring_obvious_private_key_no_go(tmp_path: Path) -> None:
    """Test that a committed private key triggers a hard blocker NO_GO override."""
    # Write a dummy private key file
    key_file = tmp_path / "id_rsa"
    key_file.write_text(
        "-----BEGIN RSA PRIVATE KEY-----\nsomekeycontent\n-----END RSA PRIVATE KEY-----"
    )

    findings = [
        {
            "id": "SEC002",
            "title": "Private Key Exposure",
            "category": "secrets",
            "severity": "high",
            "description": "Committed private key.",
            "recommendation": "Remove it.",
            "file_path": "id_rsa",
        }
    ]

    score, _, _ = calculate_readiness_score(findings, profile="startup")

    decision, reason, overridden_score = evaluate_decision(
        findings, score, profile="startup", project_root=tmp_path
    )
    assert decision == "NO_GO"
    assert overridden_score <= 49
    assert "private key" in reason.lower()


def test_no_auth_on_api_in_enterprise_profile() -> None:
    """Test that missing auth on API in enterprise profile triggers NO_GO, but not in startup."""
    findings = [
        {
            "id": "AUT001",
            "title": "Missing API Authentication",
            "category": "auth",
            "severity": "high",
            "description": "The route /api/v1/admin lacks authentication.",
            "recommendation": "Add authentication token check.",
            "file_path": "api.py",
        }
    ]

    # 1. Startup profile (no blocker override, just normal score subtraction)
    score_startup, _, _ = calculate_readiness_score(findings, profile="startup")
    decision_startup, reason_startup, score_over_startup = evaluate_decision(
        findings, score_startup, profile="startup"
    )
    # startup auth weight is 15, deduction is 15 => auth score is 0. Total score = 100 - 15 = 85.
    assert score_startup == 85
    assert decision_startup == "GO"

    # 2. Enterprise profile (should trigger blocker override -> NO_GO)
    score_ent, _, _ = calculate_readiness_score(findings, profile="enterprise")
    decision_ent, reason_ent, score_over_ent = evaluate_decision(
        findings, score_ent, profile="enterprise"
    )
    assert decision_ent == "NO_GO"
    assert score_over_ent <= 49
    assert "no authentication/authorization" in reason_ent.lower()


def test_scoring_high_public_iac_exposure() -> None:
    """Test that a high/critical public IaC exposure forces HIGH_RISK or NO_GO."""
    findings = [
        {
            "id": "CKV_AWS_101",
            "title": "Public S3 bucket",
            "category": "iac",
            "severity": "high",
            "description": "S3 bucket is publicly accessible.",
            "recommendation": "Restrict bucket access.",
            "file_path": "s3.tf",
        }
    ]

    score, _, _ = calculate_readiness_score(findings, profile="startup")
    decision, reason, overridden_score = evaluate_decision(
        findings, score, profile="startup"
    )

    assert decision == "HIGH_RISK"
    assert overridden_score <= 69
    assert "public iac exposure" in reason.lower() or "exposure" in reason.lower()


def test_scoring_more_than_three_high_findings() -> None:
    """Test that having more than 3 high findings caps the decision to HIGH_RISK maximum."""
    findings = [
        {
            "id": f"DEP00{i}",
            "title": f"Vulnerability {i}",
            "category": "dependencies",
            "severity": "high",
            "description": "Vulnerable component.",
            "recommendation": "Upgrade.",
            "file_path": "package.json",
        }
        for i in range(4)
    ]

    score, _, _ = calculate_readiness_score(findings, profile="startup")
    decision, reason, overridden_score = evaluate_decision(
        findings, score, profile="startup"
    )

    assert decision == "HIGH_RISK"
    assert overridden_score <= 69
    assert "more than 3 high findings" in reason.lower()


def test_scoring_medium_only_findings() -> None:
    """Test that medium findings yield CONDITIONAL_GO or GO depending on score."""
    # 1. Single medium finding
    findings_1 = [
        {
            "id": "DEP001",
            "title": "Missing Lockfile",
            "category": "dependencies",
            "severity": "medium",
            "description": "Missing dependency lockfile.",
            "recommendation": "Generate one.",
            "file_path": "package.json",
        }
    ]
    score_1, _, _ = calculate_readiness_score(findings_1, profile="startup")
    # startup dependencies weight is 15, deduction is 8 => 7. Total score = 92.
    assert score_1 == 92
    decision_1, _, _ = evaluate_decision(findings_1, score_1, profile="startup")
    assert decision_1 == "GO"

    # 2. Multiple medium findings
    findings_3 = [
        {
            "id": f"DEP00{i}",
            "title": f"Medium issue {i}",
            "category": "dependencies",
            "severity": "medium",
            "description": "Medium issue.",
            "recommendation": "Fix.",
            "file_path": "package.json",
        }
        for i in range(3)
    ]
    score_3, _, _ = calculate_readiness_score(findings_3, profile="startup")
    # startup dependencies weight is 15, deduction is 3*8 = 24 => score for dependencies is 0. Total score = 85.
    assert score_3 == 85
    decision_3, _, _ = evaluate_decision(findings_3, score_3, profile="startup")
    assert decision_3 == "GO"

    # 4 medium findings across different categories
    findings_4 = [
        {
            "id": "DEP001",
            "title": "Medium DEP",
            "category": "dependencies",
            "severity": "medium",
            "description": "Medium issue.",
            "recommendation": "Fix.",
            "file_path": "package.json",
        },
        {
            "id": "ENV002",
            "title": "Medium ENV",
            "category": "env_config",
            "severity": "medium",
            "description": "Medium issue.",
            "recommendation": "Fix.",
            "file_path": ".gitignore",
        },
        {
            "id": "HLT001",
            "title": "Medium HLT",
            "category": "health",
            "severity": "medium",
            "description": "Medium issue.",
            "recommendation": "Fix.",
            "file_path": "main.py",
        },
        {
            "id": "DOC001",
            "title": "Medium DOC",
            "category": "docs",
            "severity": "medium",
            "description": "Medium issue.",
            "recommendation": "Fix.",
            "file_path": "README.md",
        },
    ]
    score_4, _, _ = calculate_readiness_score(findings_4, profile="startup")
    # deductions:
    # dep (weight 15) deduction 8 => 7
    # env (cloud, weight 15) deduction 8 => 7
    # hlt (production_ops, weight 10) deduction 8 => 2
    # doc (documentation, weight 5) deduction 8 => 0
    # Total score = 20 (secrets) + 15 (auth) + 7 (dependencies) + 7 (cloud) + 2 (ops) + 10 (ai) + 10 (data) + 0 (docs) = 71
    assert score_4 == 71
    decision_4, _, _ = evaluate_decision(findings_4, score_4, profile="startup")
    assert decision_4 == "CONDITIONAL_GO"


def test_scoring_clamping() -> None:
    """Test that score is always clamped between 0 and 100."""
    # Create critical findings across all categories to drive the scores of all dimensions to 0
    categories = [
        "secrets",
        "auth",
        "dependencies",
        "env_config",
        "ai_risk",
        "data_protection",
        "docs",
        "health",
    ]
    findings = [
        {
            "id": f"RULE{i}",
            "title": f"Critical Issue {cat}",
            "category": cat,
            "severity": "critical",
            "description": "Committed critical issue.",
            "recommendation": "Fix.",
            "file_path": "config.py",
        }
        for i, cat in enumerate(categories)
    ]

    score, breakdown, _ = calculate_readiness_score(findings, profile="startup")
    assert score == 0
    for dim in breakdown:
        assert breakdown[dim] == 0

    decision, _, overridden_score = evaluate_decision(
        findings, score, profile="startup"
    )
    assert overridden_score == 0
    assert decision == "NO_GO"
