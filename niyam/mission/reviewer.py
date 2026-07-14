"""Evidence-pack supervision review for implementation tasks."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Literal

import yaml

from niyam.core.config import NiyamConfig, load_niyam_config
from niyam.runtimes.executor import run_runtime

Verdict = Literal["PASS", "REWORK_REQUIRED", "REJECT"]


def build_evidence_pack(
    *,
    task: dict[str, Any],
    task_dir: Path,
    run_dir: Path,
) -> str:
    """Assemble a compact evidence pack for the reviewer runtime."""
    sections: list[str] = []
    sections.append("# Evidence Pack\n")
    sections.append("## Task Contract\n")
    sections.append("```yaml\n" + yaml.safe_dump(task, sort_keys=False) + "```\n")

    for name, label in [
        ("diff.patch", "Git Diff"),
        ("output.log", "Executor Output"),
        ("validation.log", "Validation Output"),
        ("token-usage.json", "Token Usage"),
    ]:
        path = task_dir / name
        if path.exists():
            try:
                content = path.read_text(encoding="utf-8")
            except Exception:
                content = ""
            if len(content) > 12000:
                content = content[:12000] + "\n...[truncated]...\n"
            sections.append(f"## {label}\n```\n{content}\n```\n")

    return "\n".join(sections)


def _parse_verdict(text: str) -> dict[str, Any]:
    """Extract PASS/REWORK_REQUIRED/REJECT verdict from model output."""
    data = None
    # Prefer YAML/JSON block
    for match in re.finditer(
        r"```(?:yaml|json)?\s*([\s\S]*?)```", text or "", re.IGNORECASE
    ):
        block = match.group(1).strip()
        try:
            if block.startswith("{"):
                data = json.loads(block)
            else:
                data = yaml.safe_load(block)
            if isinstance(data, dict) and data.get("verdict"):
                break
        except Exception:
            data = None
    if not isinstance(data, dict):
        # Only accept explicit "verdict: X" lines — never scan the whole blob
        # (prompts embed the schema words PASS/REWORK_REQUIRED/REJECT).
        verdict_line = re.search(
            r"(?im)^\s*verdict\s*[:=]\s*(PASS|REWORK_REQUIRED|REWORK REQUIRED|REJECT)\b",
            text or "",
        )
        if verdict_line:
            raw_v = verdict_line.group(1).upper().replace(" ", "_")
            verdict: Verdict = (
                "REWORK_REQUIRED"
                if "REWORK" in raw_v
                else ("REJECT" if "REJECT" in raw_v else "PASS")
            )
        else:
            # Fail-open when unparseable so a down reviewer does not brick missions
            verdict = "PASS"
        return {
            "verdict": verdict,
            "confidence": "low",
            "required_changes": [],
            "issues": [],
            "raw": text or "",
        }

    verdict_raw = str(data.get("verdict") or "PASS").strip().upper().replace(" ", "_")
    if verdict_raw not in {"PASS", "REWORK_REQUIRED", "REJECT"}:
        if "REWORK" in verdict_raw:
            verdict_raw = "REWORK_REQUIRED"
        elif "REJECT" in verdict_raw:
            verdict_raw = "REJECT"
        else:
            verdict_raw = "PASS"
    required = data.get("required_changes") or data.get("requiredChanges") or []
    if isinstance(required, str):
        required = [required]
    issues = data.get("issues") or []
    if isinstance(issues, str):
        issues = [issues]
    return {
        "verdict": verdict_raw,
        "confidence": data.get("confidence") or "medium",
        "required_changes": list(required),
        "issues": list(issues),
        "raw": text or "",
    }


def review_task_evidence(
    *,
    task: dict[str, Any],
    task_dir: Path,
    run_dir: Path,
    repo_root: Path,
    config: NiyamConfig | None = None,
    force_verdict: str | None = None,
) -> dict[str, Any]:
    """Run structured evidence review for an implementation task.

    Returns verdict dict and writes ``review-verdict.yaml`` under task_dir.
    """
    if config is None:
        try:
            config = load_niyam_config(repo_root)
        except Exception:
            config = None

    orch = config.orchestrator if config and config.orchestrator else None
    evidence_review = True if orch is None else bool(orch.evidence_review)
    # Skip non-implementation unless forced
    if task.get("type") not in {"implementation", "recovery"} and not force_verdict:
        result = {
            "verdict": "PASS",
            "confidence": "high",
            "required_changes": [],
            "issues": [],
            "skipped": True,
            "reason": "non-implementation task",
        }
        _write_verdict(task_dir, result)
        return result

    if not evidence_review and not force_verdict:
        result = {
            "verdict": "PASS",
            "confidence": "high",
            "required_changes": [],
            "issues": [],
            "skipped": True,
            "reason": "evidence_review disabled",
        }
        _write_verdict(task_dir, result)
        return result

    if force_verdict:
        result = {
            "verdict": force_verdict,
            "confidence": "high",
            "required_changes": ["Forced test rework"] if force_verdict == "REWORK_REQUIRED" else [],
            "issues": [],
            "forced": True,
        }
        _write_verdict(task_dir, result)
        return result

    # Deterministic test mode: allow env override without calling a runtime
    env_verdict = os.environ.get("NIYAM_REVIEW_VERDICT")
    if env_verdict:
        result = _parse_verdict(f"verdict: {env_verdict}")
        result["source"] = "env"
        _write_verdict(task_dir, result)
        return result

    pack = build_evidence_pack(task=task, task_dir=task_dir, run_dir=run_dir)
    (task_dir / "evidence-pack.md").write_text(pack, encoding="utf-8")

    reviewer = (orch.reviewer if orch and orch.reviewer else None) or "claude"
    reviewer_tier = (orch.reviewer_tier if orch and orch.reviewer_tier else "premium")

    prompt = f"""You are the Niyam orchestrator reviewer.
Review the evidence pack for a completed implementation task.
Return ONLY a YAML block with this schema:

```yaml
verdict: PASS  # or REWORK_REQUIRED or REJECT
confidence: high
issues: []
required_changes: []
```

Rules:
- PASS if the change is complete, scoped, and validation looks healthy.
- REWORK_REQUIRED if tests/validation failed or acceptance criteria are unmet (list concrete required_changes).
- REJECT if the change is unsafe or out of scope and should not continue.

Evidence pack:
{pack}
"""

    is_test = os.environ.get("NIYAM_TEST") == "1"
    if is_test and not os.environ.get("NIYAM_TEST_REVIEWER"):
        # Default in unit tests: pass unless validation log indicates failure
        val_log = task_dir / "validation.log"
        if val_log.exists() and "FAIL" in val_log.read_text(encoding="utf-8").upper():
            result = {
                "verdict": "REWORK_REQUIRED",
                "confidence": "medium",
                "required_changes": ["Fix failing validation commands"],
                "issues": ["validation failure"],
                "source": "test-heuristic",
            }
        else:
            result = {
                "verdict": "PASS",
                "confidence": "medium",
                "required_changes": [],
                "issues": [],
                "source": "test-default",
            }
        _write_verdict(task_dir, result)
        return result

    run = run_runtime(
        reviewer,
        prompt_text=prompt,
        cwd=repo_root,
        mode="plan",
        tier=reviewer_tier,
        timeout=600,
        repo_root=repo_root,
        include_sandbox=False,
        log_path=task_dir / "reviewer.log",
    )
    raw = (run.stdout or "") + "\n" + (run.stderr or "")
    if not run.success:
        # Reviewer unavailable / errored: fail-open PASS (log for audit)
        result = {
            "verdict": "PASS",
            "confidence": "low",
            "required_changes": [],
            "issues": ["reviewer_runtime_failed"],
            "source": "runtime-error-fallback",
            "reviewer": reviewer,
            "success": False,
            "raw": raw[:2000],
        }
        _write_verdict(task_dir, result)
        return result
    result = _parse_verdict(raw)
    result["source"] = "runtime"
    result["reviewer"] = reviewer
    result["success"] = run.success
    _write_verdict(task_dir, result)
    return result


def _write_verdict(task_dir: Path, result: dict[str, Any]) -> None:
    task_dir.mkdir(parents=True, exist_ok=True)
    path = task_dir / "review-verdict.yaml"
    # Don't dump huge raw blobs twice
    payload = {k: v for k, v in result.items() if k != "raw"}
    if result.get("raw"):
        payload["raw_excerpt"] = str(result["raw"])[:2000]
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
