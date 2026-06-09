"""Tests for Phase C Memory Ledger Evidence."""

from pathlib import Path
from niyam.core.evidence import run_generate_evidence

def test_evidence_without_memory_is_unchanged(niyam_repo: Path):
    out = run_generate_evidence(fmt="markdown", include="scan,guard")
    assert "Memory Ledger Posture" not in out
    
def test_evidence_with_memory_includes_summary(niyam_repo: Path):
    out = run_generate_evidence(fmt="markdown", include="scan,guard,memory")
    assert "Memory Ledger Posture" in out
