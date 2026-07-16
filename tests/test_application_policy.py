"""Tests for cross-Application attribute policy enforcement."""

from pathlib import Path
from unittest.mock import Mock

import pytest
import yaml
from rich.console import Console

from niyam.core.applications import register_application
from niyam.core.inventory import register_inventory_object
from niyam.core.policy import evaluate_application_policy
from niyam.policies.guard import run_guard_run


def _write_policy(root: Path, rules: list[dict]) -> None:
    path = root / ".niyam" / "policies" / "team-policy.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump({"name": "Enterprise", "rules": rules}))


def test_policy_targets_application_and_linked_data_attributes(tmp_path: Path) -> None:
    register_application(
        "finance-copilot",
        name="Finance Copilot",
        owner="finance",
        status="production",
        root=tmp_path,
    )
    register_inventory_object(
        "dataset",
        "payroll",
        name="Payroll",
        version="v1",
        tags=["restricted"],
        application_id="finance-copilot",
        root=tmp_path,
    )
    register_inventory_object(
        "model",
        "finance-model",
        name="Finance Model",
        version="v1",
        owner="external-vendor",
        application_id="finance-copilot",
        root=tmp_path,
    )
    _write_policy(
        tmp_path,
        [
            {
                "id": "block-restricted-data",
                "type": "block",
                "selector": {"object_type": "dataset", "tag": "restricted"},
                "description": "Restricted data is not approved.",
            }
        ],
    )

    decision = evaluate_application_policy("finance-copilot", root=tmp_path)

    assert decision.result == "block"
    assert decision.rule_id == "block-restricted-data"

    _write_policy(
        tmp_path,
        [
            {
                "id": "block-external-model",
                "type": "block",
                "selector": {
                    "object_type": "model",
                    "owner": "external-vendor",
                },
            }
        ],
    )
    assert (
        evaluate_application_policy("finance-copilot", root=tmp_path).rule_id
        == "block-external-model"
    )


def test_guard_fails_closed_before_execution(tmp_path: Path, monkeypatch) -> None:
    register_application(
        "finance-copilot",
        name="Finance Copilot",
        owner="finance",
        root=tmp_path,
    )
    _write_policy(
        tmp_path,
        [
            {
                "id": "block-finance",
                "type": "block",
                "selector": {"object_type": "application", "owner": "finance"},
            }
        ],
    )
    monkeypatch.setattr("niyam.policies.guard.find_niyam_root", lambda: tmp_path)
    popen = Mock()
    monkeypatch.setattr("niyam.policies.guard.subprocess.Popen", popen)

    with pytest.raises(SystemExit) as blocked:
        run_guard_run(
            ["echo", "must-not-run"],
            capture_output=False,
            console=Console(),
            mode_override="observe",
            application_id="finance-copilot",
        )

    assert blocked.value.code == 1

    with pytest.raises(SystemExit) as missing_context:
        run_guard_run(
            ["echo", "must-not-run"],
            capture_output=False,
            console=Console(),
            mode_override="observe",
        )

    assert missing_context.value.code == 1
    assert all(
        call.args[0] != ["echo", "must-not-run"] for call in popen.call_args_list
    )
