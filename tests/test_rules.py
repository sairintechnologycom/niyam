"""Tests for Niyam scan YAML-based rule engine."""

from __future__ import annotations

import json
from pathlib import Path
import pytest
from typer.testing import CliRunner
from niyam.cli import app

from niyam.core.scan import load_rules_from_yaml, evaluate_rule, run_scanner_checks


def test_load_valid_rules(tmp_path: Path) -> None:
    """Should load and validate a standard rules file successfully."""
    rules_file = tmp_path / "valid-rules.yaml"
    rules_file.write_text("""
rules:
  - id: RULE001
    title: Test Rule
    category: tests
    severity: low
    description: A description
    recommendation: Some recommendation
    match:
      type: file_exists
      patterns:
        - "*.py"
""")
    rules = load_rules_from_yaml(rules_file)
    assert len(rules) == 1
    assert rules[0].id == "RULE001"
    assert rules[0].match.type == "file_exists"


def test_reject_invalid_rules_cleanly(tmp_path: Path) -> None:
    """Should fail with a clear ValueError if the rules format is malformed or invalid."""
    invalid_file = tmp_path / "invalid-rules.yaml"

    # Missing required keys
    invalid_file.write_text("""
rules:
  - id: RULE001
    title: Test Rule
""")
    with pytest.raises(ValueError) as exc:
        load_rules_from_yaml(invalid_file)
    assert "Validation error" in str(exc.value)

    # Invalid match type
    invalid_file.write_text("""
rules:
  - id: RULE002
    title: Test Rule
    category: tests
    severity: low
    description: Desc
    recommendation: Rec
    match:
      type: invalid_match_type
      patterns:
        - "*.py"
""")
    with pytest.raises(ValueError) as exc:
        load_rules_from_yaml(invalid_file)
    assert "unsupported match type" in str(exc.value)


def test_match_file_exists(tmp_path: Path) -> None:
    """Evaluate file_exists rule logic."""
    rule_data = {
        "id": "R001",
        "title": "Config detected",
        "category": "env_config",
        "severity": "medium",
        "description": "Config file found",
        "recommendation": "Check config details",
        "match": {"type": "file_exists", "patterns": ["config.yaml"]},
    }
    from niyam.core.scan import GovernanceRule

    rule = GovernanceRule(**rule_data)

    # Create test folder files
    config_file = tmp_path / "config.yaml"
    config_file.write_text("key: value")

    findings = evaluate_rule(rule, tmp_path, [config_file])
    assert len(findings) == 1
    assert findings[0]["id"] == "R001"
    assert findings[0]["file_path"] == "config.yaml"


def test_match_file_missing(tmp_path: Path) -> None:
    """Evaluate file_missing rule logic."""
    rule_data = {
        "id": "R002",
        "title": "Missing Config",
        "category": "env_config",
        "severity": "high",
        "description": "Config file was missing",
        "recommendation": "Create config.yaml",
        "match": {"type": "file_missing", "patterns": ["config.yaml"]},
    }
    from niyam.core.scan import GovernanceRule

    rule = GovernanceRule(**rule_data)

    # Evaluate when missing
    findings = evaluate_rule(rule, tmp_path, [])
    assert len(findings) == 1
    assert findings[0]["id"] == "R002"
    assert findings[0]["file_path"] == ""

    # Evaluate when file exists
    config_file = tmp_path / "config.yaml"
    config_file.touch()
    findings = evaluate_rule(rule, tmp_path, [config_file])
    assert len(findings) == 0


def test_match_content_regex(tmp_path: Path) -> None:
    """Evaluate content_regex rule logic."""
    rule_data = {
        "id": "R003",
        "title": "AWS key",
        "category": "secrets",
        "severity": "critical",
        "description": "AWS access key leaked",
        "recommendation": "Remove key",
        "match": {
            "type": "content_regex",
            "patterns": ["AKIA[A-Z0-9]{16}"],
            "files": ["*.py"],
        },
    }
    from niyam.core.scan import GovernanceRule

    rule = GovernanceRule(**rule_data)

    # Match leaked key
    code_file = tmp_path / "app.py"
    code_file.write_text("key = 'AKIA1234567890123456'")

    findings = evaluate_rule(rule, tmp_path, [code_file])
    assert len(findings) == 1
    assert findings[0]["id"] == "R003"

    # Safe file should not match
    safe_file = tmp_path / "safe.py"
    safe_file.write_text("key = 'safe_value'")
    findings = evaluate_rule(rule, tmp_path, [safe_file])
    assert len(findings) == 0


def test_run_profile_based_scan(tmp_path: Path) -> None:
    """Should run scan with default rules for startup profile."""
    # Write a test app containing env and readme
    readme = tmp_path / "README.md"
    readme.write_text("# Startup Project")

    # Run scan
    results = run_scanner_checks(tmp_path, profile="startup")
    assert results["profile"] == "startup"
    # findings list should have items about missing lockfiles, etc.
    assert len(results["findings"]) > 0


def test_scan_cli_custom_rules(tmp_path: Path) -> None:
    """Should execute scan CLI command with custom rules option successfully."""
    # Write a custom rule file
    rules_file = tmp_path / "custom-rules.yaml"
    rules_file.write_text("""
rules:
  - id: CUST001
    title: Custom Rule
    category: secrets
    severity: high
    description: Custom secret check
    recommendation: Fix it
    match:
      type: file_exists
      patterns:
        - "secret.txt"
""")

    # Create the matched file
    secret_file = tmp_path / "secret.txt"
    secret_file.touch()

    runner = CliRunner()
    result = runner.invoke(
        app, ["scan", str(tmp_path), "--rules", str(rules_file), "--output", "json"]
    )
    assert result.exit_code == 0

    data = json.loads(result.stdout)
    assert data["profile"] == "custom"
    assert len(data["findings"]) == 1
    assert data["findings"][0]["id"] == "CUST001"


def test_load_all_builtin_profiles() -> None:
    """Should load all default built-in rule profiles: startup, team, enterprise, regulated."""
    from niyam.core.scan import load_profile_rules
    for profile in ["startup", "team", "enterprise", "regulated"]:
        rules = load_profile_rules(profile)
        assert len(rules) > 0
        for r in rules:
            assert r.id is not None
            assert r.title is not None
            assert r.category is not None
            assert r.severity is not None


def test_match_directory_exists(tmp_path: Path) -> None:
    """Evaluate directory_exists rule logic."""
    from niyam.core.scan import GovernanceRule
    rule_data = {
        "id": "R004",
        "title": "Directory present",
        "category": "env_config",
        "severity": "medium",
        "description": "Required directory exists",
        "recommendation": "Maintain it",
        "match": {"type": "directory_exists", "patterns": ["deploy"]},
    }
    rule = GovernanceRule(**rule_data)

    # 1. Directory does not exist => no findings
    findings = evaluate_rule(rule, tmp_path, [])
    assert len(findings) == 0

    # 2. Directory exists => 1 finding
    deploy_dir = tmp_path / "deploy"
    deploy_dir.mkdir()
    findings = evaluate_rule(rule, tmp_path, [])
    assert len(findings) == 1
    assert findings[0]["id"] == "R004"
    assert findings[0]["file_path"] == "deploy"


def test_match_filename_pattern(tmp_path: Path) -> None:
    """Evaluate filename_pattern rule logic."""
    from niyam.core.scan import GovernanceRule
    rule_data = {
        "id": "R005",
        "title": "Match by name",
        "category": "env_config",
        "severity": "medium",
        "description": "Secrets file found by name pattern",
        "recommendation": "Remove it",
        "match": {"type": "filename_pattern", "patterns": ["*.secret"]},
    }
    rule = GovernanceRule(**rule_data)

    test_file = tmp_path / "key.secret"
    test_file.touch()

    findings = evaluate_rule(rule, tmp_path, [test_file])
    assert len(findings) == 1
    assert findings[0]["id"] == "R005"
    assert findings[0]["file_path"] == "key.secret"


def test_match_content_contains(tmp_path: Path) -> None:
    """Evaluate content_contains rule logic."""
    from niyam.core.scan import GovernanceRule
    rule_data = {
        "id": "R006",
        "title": "Match contains string",
        "category": "secrets",
        "severity": "high",
        "description": "Sensitive keyword found",
        "recommendation": "Remove it",
        "match": {
            "type": "content_contains",
            "patterns": ["PASSWORD_PLAIN_TEXT"],
            "files": ["*.py"]
        },
    }
    rule = GovernanceRule(**rule_data)

    # Match containing string
    code_file = tmp_path / "main.py"
    code_file.write_text("pwd = 'PASSWORD_PLAIN_TEXT'")

    findings = evaluate_rule(rule, tmp_path, [code_file])
    assert len(findings) == 1
    assert findings[0]["id"] == "R006"
    assert findings[0]["line_number"] == 1

    # Safe file
    safe_file = tmp_path / "safe.py"
    safe_file.write_text("pwd = 'safe'")
    findings = evaluate_rule(rule, tmp_path, [safe_file])
    assert len(findings) == 0
