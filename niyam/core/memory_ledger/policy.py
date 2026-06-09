"""Policy check logic for Memory Ledger."""

from __future__ import annotations

from datetime import datetime, timezone
import yaml
from pathlib import Path

from niyam.core.memory_ledger.models import MemoryRecord, MemoryPolicy, MemoryPolicyFinding


def load_policy(policy_path: Path | None) -> MemoryPolicy:
    """Load memory policy from a YAML file, or return a default conservative policy."""
    if not policy_path or not policy_path.exists():
        return MemoryPolicy()

    try:
        with open(policy_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid memory policy YAML: {e}") from e
    except OSError as e:
        raise ValueError(f"Unable to read memory policy: {e}") from e

    if not isinstance(data, dict):
        raise ValueError("Memory policy must be a YAML mapping.")

    try:
        return MemoryPolicy.model_validate(data)
    except Exception as e:
        raise ValueError(f"Invalid memory policy: {e}") from e


def check_record(record: MemoryRecord, policy: MemoryPolicy) -> list[MemoryPolicyFinding]:
    """Check a single memory record against the given policy."""
    from niyam.governance.common.redaction import contains_secret

    findings: list[MemoryPolicyFinding] = []
    
    # 1. Scope not allowed
    if record.scope not in policy.allowed_scopes:
        findings.append(
            MemoryPolicyFinding(
                record_id=record.id,
                severity="medium",
                code="MEM001",
                message=f"Scope '{record.scope}' is not in allowed scopes: {policy.allowed_scopes}",
                field="scope"
            )
        )

    # 2. Expired memory
    now = datetime.now(timezone.utc)
    if record.expires_at and record.expires_at < now:
        findings.append(
            MemoryPolicyFinding(
                record_id=record.id,
                severity="low",
                code="MEM002",
                message=f"Memory expired at {record.expires_at.isoformat()}",
                field="expires_at"
            )
        )

    # 3. Retention exceeded
    if policy.max_retention_days is not None:
        age_days = (now - record.created_at).days
        if age_days > policy.max_retention_days:
            findings.append(
                MemoryPolicyFinding(
                    record_id=record.id,
                    severity="low",
                    code="MEM003",
                    message=f"Memory age ({age_days} days) exceeds max retention ({policy.max_retention_days} days)",
                    field="created_at"
                )
            )

    # 4. Source ref missing when required
    if policy.require_source_ref and not record.source_ref:
        findings.append(
            MemoryPolicyFinding(
                record_id=record.id,
                severity="medium",
                code="MEM004",
                message="Source reference is required but missing",
                field="source_ref"
            )
        )

    # 5. Confidence below minimum
    if policy.min_confidence is not None:
        if record.confidence is None or record.confidence < policy.min_confidence:
            findings.append(
                MemoryPolicyFinding(
                    record_id=record.id,
                    severity="low",
                    code="MEM005",
                    message=f"Confidence ({record.confidence}) is below minimum ({policy.min_confidence})",
                    field="confidence"
                )
            )

    # 6. Type not allowed
    if policy.allowed_types is not None and record.type not in policy.allowed_types:
        findings.append(
            MemoryPolicyFinding(
                record_id=record.id,
                severity="medium",
                code="MEM006",
                message=f"Type '{record.type}' is not in allowed types: {policy.allowed_types}",
                field="type"
            )
        )

    # 7. Blocked tag present
    for tag in record.tags:
        if tag in policy.blocked_tags:
            findings.append(
                MemoryPolicyFinding(
                    record_id=record.id,
                    severity="high",
                    code="MEM007",
                    message=f"Tag '{tag}' is blocked",
                    field="tags"
                )
            )

    # 8. Secret detected in content/summary/metadata
    if policy.redact_secrets:
        if contains_secret(record.content):
            findings.append(
                MemoryPolicyFinding(
                    record_id=record.id,
                    severity="critical",
                    code="MEM008",
                    message="Secret detected in content",
                    field="content"
                )
            )
        if record.summary and contains_secret(record.summary):
            findings.append(
                MemoryPolicyFinding(
                    record_id=record.id,
                    severity="critical",
                    code="MEM008",
                    message="Secret detected in summary",
                    field="summary"
                )
            )
        # simplistic check for strings in metadata
        for k, v in record.metadata.items():
            if isinstance(v, str) and contains_secret(v):
                findings.append(
                    MemoryPolicyFinding(
                        record_id=record.id,
                        severity="critical",
                        code="MEM008",
                        message=f"Secret detected in metadata field '{k}'",
                        field=f"metadata.{k}"
                    )
                )

    return findings


def run_policy_check(records: list[MemoryRecord], policy: MemoryPolicy) -> list[MemoryPolicyFinding]:
    """Run policy check across multiple records."""
    all_findings = []
    for record in records:
        all_findings.extend(check_record(record, policy))
    return all_findings
