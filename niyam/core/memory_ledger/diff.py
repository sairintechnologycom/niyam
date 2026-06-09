"""Diff logic for memory manifests."""

from __future__ import annotations

from niyam.core.memory_ledger.models import MemoryRecord


class MemoryDiff:
    """Represents differences between two sets of memory records."""
    
    def __init__(self, added: list[MemoryRecord], removed: list[MemoryRecord], changed: list[tuple[MemoryRecord, MemoryRecord]]):
        self.added = added
        self.removed = removed
        self.changed = changed

    def is_empty(self) -> bool:
        return not self.added and not self.removed and not self.changed


def diff_manifests(before: list[MemoryRecord], after: list[MemoryRecord]) -> MemoryDiff:
    """Compare two sets of memory records and return their differences."""
    before_map = {r.id: r for r in before}
    after_map = {r.id: r for r in after}

    added = []
    removed = []
    changed = []

    for r_id, r_after in after_map.items():
        if r_id not in before_map:
            added.append(r_after)
        else:
            r_before = before_map[r_id]
            # Compare using model_dump to ignore things like instance identity
            if r_before.model_dump() != r_after.model_dump():
                changed.append((r_before, r_after))

    for r_id, r_before in before_map.items():
        if r_id not in after_map:
            removed.append(r_before)

    return MemoryDiff(added=added, removed=removed, changed=changed)
