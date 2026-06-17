from __future__ import annotations

from niyam.core.loopops.evaluator import LoopEvaluationResult

def test_evaluator_result_score_metadata() -> None:
    """Should correctly store score metadata in LoopEvaluationResult."""
    result = LoopEvaluationResult(
        evaluatorName="security-review",
        evaluatorType="ai_critic",
        result="pass",
        details="No security issues found.",
        score=0.95,
        required=True,
        timestamp="2026-06-17T12:00:00Z",
    )
    assert result.evaluator_name == "security-review"
    assert result.result == "pass"
    assert result.score == 0.95
    assert result.required is True
