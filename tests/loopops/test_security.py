from __future__ import annotations

import json
import yaml
from pathlib import Path
from niyam.core.loopops import LoopRunner, LoopSpec

def test_security_protected_write_denial(tmp_path: Path) -> None:
    """LOOP-SEC-005, 007: Modifying protected config files should be blocked or require approval."""
    # Configure protected paths
    config_data = {
        "version": "0.1.0",
        "governance": {
            "guard": {
                "protected_files": [".niyam/policies/**", "src/auth/**"]
            }
        }
    }
    with open(tmp_path / ".niyam" / "niyam.yaml", "w") as f:
        yaml.dump(config_data, f)

    spec_data = {
        "apiVersion": "niyam.dev/v1",
        "kind": "LoopSpec",
        "metadata": {
            "name": "security-test",
            "owner": "security-team",
            "riskTier": "high"
        },
        "goal": {
            "type": "testing",
            "description": "Verify security policy gates"
        },
        "budgets": {
            "maxIterations": 2
        }
    }
    spec = LoopSpec.model_validate(spec_data)
    run = LoopRunner.initialize_run(spec)

    # Modify policy file -> blocked or requires approval
    result = LoopRunner.process_step_result(
        run, spec, {
            "status": "success",
            "files_changed": [".niyam/policies/security.yaml"]
        }
    )
    assert result is not None
    assert "Requires human approval" in result
    assert run.status == "requires_approval"
