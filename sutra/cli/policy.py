"""Sutra CLI policy commands."""

from __future__ import annotations

from sutra.cli import console, policy_app


@policy_app.command("validate")
def policy_validate() -> None:
    """Validate all policy YAML files."""
    from sutra.policies.validator import run_policy_validate

    run_policy_validate(console=console)
