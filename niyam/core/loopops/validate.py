"""Validation logic for Niyam LoopSpecs."""

from __future__ import annotations

import re
from typing import Any
from pydantic import ValidationError

from niyam.core.loopops.schema import LoopSpec

# Regex for validating stop condition comparison: <variable> <operator> <value>
# Variable name must start with letter/underscore and contain alphanumeric/underscore.
# Operators: >=, <=, >, <, ==, !=
# Value: non-whitespace sequence
STOP_CONDITION_REGEX = re.compile(
    r"^([a-zA-Z_][a-zA-Z0-9_]*)\s*(>=|<=|==|!=|>|<)\s*([a-zA-Z0-9_\.]+)$"
)


def validate_loop_spec(data: Any) -> list[str]:
    """Validate a loop specification dictionary against schema and semantic rules.

    Returns a list of validation error strings. If valid, returns an empty list.
    """
    errors: list[str] = []

    if not isinstance(data, dict):
        return ["LoopSpec must be a YAML mapping (dictionary)."]

    # 1. Pydantic Schema Validation
    try:
        spec = LoopSpec.model_validate(data)
    except ValidationError as e:
        for err in e.errors():
            loc_path = " -> ".join(str(loc) for loc in err["loc"])
            msg = err["msg"]
            errors.append(f"Schema error at {loc_path}: {msg}")
        return errors

    # 2. Semantic Validation

    # A. Validate metadata.name is not empty
    if not spec.metadata.name.strip():
        errors.append("metadata.name cannot be empty.")

    # B. Validate steps are defined
    if not spec.steps:
        errors.append("No steps are defined in the loop specification.")

    # C. Validate budgets.maxIterations is >= 1
    if spec.budgets.max_iterations < 1:
        errors.append("budgets.maxIterations must be greater than or equal to 1.")

    # D. Validate step actors/evaluators reference known actors
    known_actors = set(spec.actors.keys()) | set(spec.actors.values())
    for i, step in enumerate(spec.steps):
        step_id = step.name or f"step {i}"
        if step.actor and step.actor not in known_actors:
            errors.append(
                f"Step '{step_id}' references an unknown actor '{step.actor}'."
            )
        if step.evaluator and step.evaluator not in known_actors:
            errors.append(
                f"Step '{step_id}' references an unknown evaluator '{step.evaluator}'."
            )

    # E. Validate stopConditions syntax
    for cond in spec.stop_conditions:
        if not STOP_CONDITION_REGEX.match(cond.strip()):
            errors.append(
                f"Stop condition '{cond}' has invalid comparison syntax. "
                "Must be in format '<variable> <operator> <value>'."
            )

    # F. Validate requiredEvidence is list of strings
    # (Pydantic validates this, but let's double check if any are empty/whitespace)
    for i, step in enumerate(spec.steps):
        step_id = step.name or f"step {i}"
        if step.required_evidence is not None:
            if not isinstance(step.required_evidence, list):
                errors.append(f"Step '{step_id}' requiredEvidence must be a list.")
            else:
                for idx, ev in enumerate(step.required_evidence):
                    if not isinstance(ev, str) or not ev.strip():
                        errors.append(
                            f"Step '{step_id}' requiredEvidence at index {idx} must be a non-empty string."
                        )

    # G. Validate evaluators
    evaluator_names: set[str] = set()
    for i, ev in enumerate(spec.evaluators):
        ev_id = ev.name or f"evaluator {i}"

        # Name must be non-empty
        if not ev.name or not ev.name.strip():
            errors.append(f"Evaluator at index {i} must have a non-empty name.")

        # Name must be unique
        if ev.name in evaluator_names:
            errors.append(f"Evaluator name '{ev.name}' is duplicated.")
        evaluator_names.add(ev.name)

        # ai_critic must have actor
        if ev.type == "ai_critic":
            if not ev.actor or not ev.actor.strip():
                errors.append(
                    f"Evaluator '{ev_id}' of type 'ai_critic' must specify an 'actor'."
                )
            elif ev.actor not in known_actors:
                errors.append(
                    f"Evaluator '{ev_id}' references an unknown actor '{ev.actor}'."
                )

        # command must have command
        if ev.type == "command":
            if not ev.command or not ev.command.strip():
                errors.append(
                    f"Evaluator '{ev_id}' of type 'command' must specify a 'command'."
                )

    return errors


def check_runtime_drift(root: Path) -> list[str]:
    """Check for CLAUDE.md/GEMINI.md configuration drift.

    Generates the expected content in memory and compares it to the file on disk.
    """
    from pathlib import Path
    warnings = []

    # Check CLAUDE.md
    claude_md = root / "CLAUDE.md"
    if claude_md.exists():
        try:
            from niyam.runtimes.claude import ClaudeAdapter
            from rich.console import Console

            captured_content = None
            def mock_write(target_path, content, console):
                nonlocal captured_content
                if target_path.name == "CLAUDE.md":
                    captured_content = content

            adapter = ClaudeAdapter(root, dry_run=True)
            adapter._write_file = mock_write
            adapter._generate_claude_md(Console())

            if captured_content is not None:
                actual_content = claude_md.read_text(encoding="utf-8")
                if actual_content != captured_content:
                    warnings.append("CLAUDE.md configuration drift detected. File on disk does not match Niyam source of truth. Run `niyam sync` to update.")
        except Exception:
            pass

    # Check GEMINI.md
    gemini_md = root / "GEMINI.md"
    if gemini_md.exists():
        try:
            from niyam.runtimes.gemini import GeminiAdapter
            from rich.console import Console

            captured_content = None
            def mock_write(target_path, content, console):
                nonlocal captured_content
                if target_path.name == "GEMINI.md":
                    captured_content = content

            adapter = GeminiAdapter(root, dry_run=True)
            adapter._write_file = mock_write
            adapter._generate_gemini_md(Console())

            if captured_content is not None:
                actual_content = gemini_md.read_text(encoding="utf-8")
                if actual_content != captured_content:
                    warnings.append("GEMINI.md configuration drift detected. File on disk does not match Niyam source of truth. Run `niyam sync` to update.")
        except Exception:
            pass

    return warnings


