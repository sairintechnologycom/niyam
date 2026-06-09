"""Redaction logic for Memory Ledger."""

from __future__ import annotations

from typing import Any
from niyam.core.memory_ledger.models import MemoryRecord


def redact_memory_records(records: list[MemoryRecord]) -> tuple[list[MemoryRecord], int]:
    """Redact secrets from a list of memory records.
    Returns the redacted list and a count of how many records were actually modified.
    """
    from niyam.governance.common.redaction import redact_text, redact_dict, contains_secret

    redacted_records = []
    modified_count = 0

    for record in records:
        modified = False
        
        new_content = redact_text(record.content, with_fingerprint=False)
        if new_content != record.content:
            record.content = new_content
            modified = True
            
        if record.summary:
            new_summary = redact_text(record.summary, with_fingerprint=False)
            if new_summary != record.summary:
                record.summary = new_summary
                modified = True
                
        # Check string metadata values
        if record.metadata:
            new_metadata: dict[str, Any] = {}
            for k, v in record.metadata.items():
                if isinstance(v, str):
                    new_v = redact_text(v, with_fingerprint=False)
                    new_metadata[k] = new_v
                    if new_v != v:
                        modified = True
                elif isinstance(v, dict):
                    # Existing redact_dict redacts based on specific key names usually,
                    # but we can apply it broadly if is_sensitive=True or false
                    new_v = redact_dict(v, with_fingerprint=False)
                    new_metadata[k] = new_v
                    if new_v != v:
                        modified = True
                else:
                    new_metadata[k] = v
            record.metadata = new_metadata
            
        redacted_records.append(record)
        if modified:
            modified_count += 1

    return redacted_records, modified_count
