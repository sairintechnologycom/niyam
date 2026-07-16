"""Evidence manifest creation and verification for harness runs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


REQUIRED_ARTIFACTS = (
    "task-contract.yaml", "execution-plan.yaml", "events.jsonl", "tool-calls.jsonl",
    "diff.patch", "tests-before.txt", "tests-after.txt", "evaluator-results.json",
    "provenance.json", "final-report.md",
)


def write_manifest(evidence_path: Path, run_id: str) -> None:
    artifacts = [
        {"path": name, "sha256": _sha256(evidence_path / name), "size": (evidence_path / name).stat().st_size}
        for name in REQUIRED_ARTIFACTS
    ]
    (evidence_path / "manifest.json").write_text(
        json.dumps({"schema_version": 1, "run_id": run_id, "artifacts": artifacts}, indent=2) + "\n",
        encoding="utf-8",
    )


def verify_evidence(evidence_path: Path) -> list[str]:
    manifest_path = evidence_path / "manifest.json"
    if not manifest_path.exists():
        return ["missing manifest.json"]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected = {artifact["path"]: artifact["sha256"] for artifact in manifest["artifacts"]}
    errors: list[str] = []
    for name in REQUIRED_ARTIFACTS:
        artifact = evidence_path / name
        if not artifact.exists():
            errors.append(f"missing artifact: {name}")
        elif expected.get(name) != _sha256(artifact):
            errors.append(f"hash mismatch: {name}")
    return errors


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
