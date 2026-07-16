from __future__ import annotations

import sys
from pathlib import Path

from niyam.harness import Harness, ScriptedModel, verify_evidence


FIXTURE = Path(__file__).parent / "e2e/fixtures/bank_account_bug"
FIXED_ACCOUNT = """class Account:
    def __init__(self, balance: int) -> None:
        self.balance = balance

    def withdraw(self, amount: int) -> bool:
        if amount > self.balance:
            return False
        self.balance -= amount
        return True
"""


def _completed_evidence(tmp_path: Path) -> Path:
    return Harness.for_test(
        fixture=FIXTURE,
        workspace=tmp_path / "workspace",
        model=ScriptedModel([
            {"type": "tool_call", "tool": "workspace.patch", "arguments": {"path": "src/account.py", "content": FIXED_ACCOUNT}},
            {"type": "tool_call", "tool": "test.run", "arguments": {"command": f"{sys.executable} -m pytest tests/test_account.py -q"}},
            {"type": "tool_call", "tool": "test.run", "arguments": {"command": f"{sys.executable} -m pytest -q"}},
            {"type": "final", "text": "Done."},
        ]),
    ).run().evidence_path


def test_evidence_manifest_verifies_completed_run(tmp_path: Path) -> None:
    evidence_path = _completed_evidence(tmp_path)

    assert (evidence_path / "manifest.json").exists()
    assert verify_evidence(evidence_path) == []


def test_evidence_verifier_detects_tampering(tmp_path: Path) -> None:
    evidence_path = _completed_evidence(tmp_path)
    (evidence_path / "diff.patch").write_text("tampered\n", encoding="utf-8")

    assert verify_evidence(evidence_path) == ["hash mismatch: diff.patch"]
