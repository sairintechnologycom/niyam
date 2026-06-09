"""Recall logic for Memory Ledger."""

from __future__ import annotations

from niyam.core.memory_ledger.models import MemoryRecord


def recall_records(
    records: list[MemoryRecord],
    query: str,
    limit: int | None = None,
    scope: str | None = None
) -> list[MemoryRecord]:
    """Simple keyword matching recall."""
    if not query.strip():
        return []

    terms = [t.lower() for t in query.split() if len(t) >= 3]
    if not terms:
        return []

    scored_records: list[tuple[int, MemoryRecord]] = []
    
    for record in records:
        if scope and record.scope != scope:
            continue
            
        score = 0
        searchable_text = f"{record.content} {record.summary or ''} {' '.join(record.tags)}".lower()
        
        for term in terms:
            score += searchable_text.count(term)
            
        if score > 0:
            scored_records.append((score, record))
            
    # Sort by score descending
    scored_records.sort(key=lambda x: x[0], reverse=True)
    
    results = [record for score, record in scored_records]
    
    if limit is not None and limit > 0:
        return results[:limit]
        
    return results
