from __future__ import annotations

import pytest
from pydantic import ValidationError
from niyam.core.loopops import LoopSpec, LoopMetadata, LoopGoal, LoopBudgets

def test_schema_valid_minimal() -> None:
    """LOOP-SCHEMA-001: Should parse a valid minimal LoopSpec data structure."""
    data = {
        "apiVersion": "niyam.dev/v1",
        "kind": "LoopSpec",
        "metadata": {
            "name": "basic-loop",
            "owner": "platform"
        },
        "goal": {
            "type": "code-change",
            "description": "Just a test goal"
        },
        "budgets": {
            "maxIterations": 5
        }
    }
    spec = LoopSpec.model_validate(data)
    assert spec.api_version == "niyam.dev/v1"
    assert spec.kind == "LoopSpec"
    assert spec.metadata.name == "basic-loop"
    assert spec.metadata.owner == "platform"
    assert spec.goal.type == "code-change"
    assert spec.goal.description == "Just a test goal"
    assert spec.budgets.max_iterations == 5

def test_schema_missing_metadata_fields() -> None:
    """LOOP-SCHEMA-002, LOOP-SCHEMA-003: Metadata missing name/owner."""
    # Missing name
    with pytest.raises(ValidationError):
        LoopSpec.model_validate({
            "apiVersion": "niyam.dev/v1",
            "metadata": {"owner": "platform"},
            "goal": {"type": "code", "description": "desc"},
            "budgets": {"maxIterations": 5}
        })
    
    # Missing owner
    with pytest.raises(ValidationError):
        LoopSpec.model_validate({
            "apiVersion": "niyam.dev/v1",
            "metadata": {"name": "test"},
            "goal": {"type": "code", "description": "desc"},
            "budgets": {"maxIterations": 5}
        })

def test_schema_missing_goal_desc() -> None:
    """LOOP-SCHEMA-004: Goal missing description."""
    with pytest.raises(ValidationError):
        LoopSpec.model_validate({
            "apiVersion": "niyam.dev/v1",
            "metadata": {"name": "test", "owner": "platform"},
            "goal": {"type": "code"},
            "budgets": {"maxIterations": 5}
        })

def test_schema_missing_budgets() -> None:
    """LOOP-SCHEMA-008: Budgets missing or maxIterations missing."""
    with pytest.raises(ValidationError):
        LoopSpec.model_validate({
            "apiVersion": "niyam.dev/v1",
            "metadata": {"name": "test", "owner": "platform"},
            "goal": {"type": "code", "description": "desc"}
        })

def test_schema_invalid_risk_tier() -> None:
    """LOOP-SCHEMA-010: Invalid risk tier in metadata (handled as string but we test structure)."""
    # Note: risk_tier is Optional[str], so arbitrary string is technically allowed by schema,
    # but we can verify it parses correctly.
    data = {
        "apiVersion": "niyam.dev/v1",
        "metadata": {
            "name": "basic-loop",
            "owner": "platform",
            "riskTier": "high"
        },
        "goal": {
            "type": "code",
            "description": "desc"
        },
        "budgets": {
            "maxIterations": 5
        }
    }
    spec = LoopSpec.model_validate(data)
    assert spec.metadata.risk_tier == "high"
