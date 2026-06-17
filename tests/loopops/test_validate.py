from __future__ import annotations

from niyam.core.loopops import validate_loop_spec

def test_validation_success_minimal() -> None:
    """Should validate a basic valid LoopSpec successfully."""
    valid_data = {
        "apiVersion": "niyam.dev/v1",
        "kind": "LoopSpec",
        "metadata": {
            "name": "valid-loop",
            "owner": "platform",
            "riskTier": "low"
        },
        "goal": {
            "type": "code_change",
            "description": "Safe code changes"
        },
        "actors": {
            "planner": "claude",
            "implementer": "codex"
        },
        "steps": [
            {
                "name": "plan",
                "action": "generate_plan",
                "actor": "claude",
                "requiredEvidence": ["plan_doc"]
            },
            {
                "name": "implement",
                "action": "modify_files",
                "actor": "codex"
            }
        ],
        "budgets": {
            "maxIterations": 5,
            "maxTokens": 1000,
            "maxCostUsd": 1.5,
            "maxRuntimeMinutes": 10
        },
        "stopConditions": [
            "repeatedFailureCount >= 3",
            "policyViolation == critical"
        ]
    }
    errors = validate_loop_spec(valid_data)
    assert not errors

def test_validation_failures() -> None:
    """Should return validation errors for invalid fields and constraints."""
    # 1. Missing name (empty name)
    data_empty_name = {
        "apiVersion": "niyam.dev/v1",
        "kind": "LoopSpec",
        "metadata": {"name": "   ", "owner": "platform"},
        "goal": {"type": "code", "description": "desc"},
        "steps": [{"name": "s1", "action": "act"}],
        "budgets": {"maxIterations": 3}
    }
    errors = validate_loop_spec(data_empty_name)
    assert any("metadata.name cannot be empty." in err or "Schema error" in err for err in errors)

    # 2. No steps defined
    data_no_steps = {
        "apiVersion": "niyam.dev/v1",
        "kind": "LoopSpec",
        "metadata": {"name": "test", "owner": "platform"},
        "goal": {"type": "code", "description": "desc"},
        "steps": [],
        "budgets": {"maxIterations": 3}
    }
    errors = validate_loop_spec(data_no_steps)
    assert "No steps are defined in the loop specification." in errors

    # 3. maxIterations < 1
    data_bad_iterations = {
        "apiVersion": "niyam.dev/v1",
        "kind": "LoopSpec",
        "metadata": {"name": "test", "owner": "platform"},
        "goal": {"type": "code", "description": "desc"},
        "steps": [{"name": "s1", "action": "act"}],
        "budgets": {"maxIterations": 0}
    }
    errors = validate_loop_spec(data_bad_iterations)
    assert "budgets.maxIterations must be greater than or equal to 1." in errors

    # 4. Unknown step actor
    data_bad_actor = {
        "apiVersion": "niyam.dev/v1",
        "kind": "LoopSpec",
        "metadata": {"name": "test", "owner": "platform"},
        "goal": {"type": "code", "description": "desc"},
        "actors": {"planner": "claude"},
        "steps": [{"name": "s1", "action": "act", "actor": "unknown_actor"}],
        "budgets": {"maxIterations": 3}
    }
    errors = validate_loop_spec(data_bad_actor)
    assert "Step 's1' references an unknown actor 'unknown_actor'." in errors

    # 5. Invalid stop conditions syntax
    data_bad_stop = {
        "apiVersion": "niyam.dev/v1",
        "kind": "LoopSpec",
        "metadata": {"name": "test", "owner": "platform"},
        "goal": {"type": "code", "description": "desc"},
        "steps": [{"name": "s1", "action": "act"}],
        "budgets": {"maxIterations": 3},
        "stopConditions": ["invalidCondition", "var = 5", "var >= "]
    }
    errors = validate_loop_spec(data_bad_stop)
    assert any("Stop condition 'invalidCondition' has invalid comparison syntax." in err for err in errors)

    # 6. Malformed requiredEvidence
    data_bad_evidence = {
        "apiVersion": "niyam.dev/v1",
        "kind": "LoopSpec",
        "metadata": {"name": "test", "owner": "platform"},
        "goal": {"type": "code", "description": "desc"},
        "steps": [{"name": "s1", "action": "act", "requiredEvidence": ["", "valid_ev"]}],
        "budgets": {"maxIterations": 3}
    }
    errors = validate_loop_spec(data_bad_evidence)
    assert "Step 's1' requiredEvidence at index 0 must be a non-empty string." in errors
