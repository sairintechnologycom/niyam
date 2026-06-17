from __future__ import annotations

import json
from pathlib import Path
from niyam.core.loopops import LoopRunner, LoopSpec

def test_report_generation_markdown(tmp_path: Path) -> None:
    """LOOP-REPORT-001, 004, 005, 006, 007, 008, 009, 010: Generate Markdown report with all sections."""
    spec_data = {
        "apiVersion": "niyam.dev/v1",
        "kind": "LoopSpec",
        "metadata": {
            "name": "report-test-loop",
            "owner": "platform",
            "riskTier": "low"
        },
        "goal": {
            "type": "code_change",
            "description": "Report generation testing"
        },
        "budgets": {
            "maxIterations": 5,
            "maxTokens": 100000,
            "maxCostUsd": 10.0
        },
        "stopConditions": []
    }
    spec = LoopSpec.model_validate(spec_data)
    run = LoopRunner.initialize_run(spec)

    # Add mock iteration and complete the loop
    LoopRunner.process_step_result(
        run, spec, {
            "status": "passed",
            "cost_usd": 0.50,
            "tokens_in": 3000,
            "tokens_out": 1500,
        }
    )

    evidence_dir = tmp_path / run.evidence_path
    report_file = evidence_dir / "report.md"
    assert report_file.exists()

    report_content = report_file.read_text(encoding="utf-8")
    assert "Niyam LoopOps Run Report: report-test-loop" in report_content
    assert "## FinOps & Efficiency Analytics" in report_content
    assert "**Total Tokens**: 4,500" in report_content
    assert "Input: 3,000" in report_content
    assert "Output: 1,500" in report_content
