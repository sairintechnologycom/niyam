"""LoopSpec initialization and starter template generation."""

from __future__ import annotations

import os


def generate_starter_spec(name: str = "my-loop", goal_type: str = "code-change") -> str:
    """Generate a starter LoopSpec YAML string."""
    owner = os.environ.get("USER", "platform-engineering")

    # Clean the name to be lowercase/alphanumeric/hyphen
    import re
    clean_name = re.sub(r"[^a-zA-Z0-9_\-]+", "-", name).strip("-").lower()
    if not clean_name:
        clean_name = "my-loop"

    template = f"""apiVersion: niyam.dev/v1
kind: LoopSpec
metadata:
  name: {clean_name}
  owner: {owner}
  riskTier: medium

goal:
  type: {goal_type}
  description: Implement the requested {goal_type} tasks safely with validation

actors:
  planner: claude
  implementer: codex
  reviewer: gemini
  approver: human

steps:
  - name: understand
    action: inspect_repository
    requiredEvidence:
      - repo_tree
      - relevant_files

  - name: plan
    action: generate_implementation_plan
    maxAttempts: 2

  - name: implement
    action: modify_code
    policy:
      requireBranch: true
      blockSecrets: true
      maxFilesChanged: 20

  - name: validate
    action: run_tests
    requiredEvidence:
      - test_output
      - lint_output

  - name: review
    action: ai_review
    evaluator: gemini

  - name: decide
    action: policy_decision
    gates:
      - no_critical_vulnerabilities
      - tests_passed
      - cost_under_budget
      - no_secret_leakage

budgets:
  maxIterations: 5
  maxTokens: 150000
  maxCostUsd: 3.00
  maxRuntimeMinutes: 30

stopConditions:
  - repeatedFailureCount >= 3
  - sameErrorRepeated >= 2
  - policyViolation == critical
  - humanApprovalRequired == true
"""
    return template
