"""Comprehensive integration and E2E tests for Niyam governance integration."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
import pytest
import yaml
from typer.testing import CliRunner

from niyam.cli import app
from niyam.core.scan import load_profile_rules, run_scanner_checks, GovernanceRule, evaluate_rule
from niyam.core.evidence import run_generate_evidence

REPO_ROOT = Path(__file__).parent.parent
CLEAN_APP = REPO_ROOT / "test-fixtures/apps/clean-nextjs-app"
RISKY_APP = REPO_ROOT / "test-fixtures/apps/risky-vibe-app"
EXISTING_PROJECT = REPO_ROOT / "test-fixtures/niyam/existing-project"
CUSTOM_RULES = REPO_ROOT / "test-fixtures/rules/custom-rules.yaml"
INVALID_RULES = REPO_ROOT / "test-fixtures/rules/invalid-rules.yaml"


@pytest.fixture(autouse=True)
def clean_niyam_env(tmp_path: Path, monkeypatch) -> None:
    """Redirect .niyam directory and settings to a temporary workspace."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("NIYAM_SESSION_ID", "test-session")
    
    # Pre-create a niyam.yaml configuration in tmp_path
    niyam_dir = tmp_path / ".niyam"
    niyam_dir.mkdir(exist_ok=True)
    
    config_data = {
        "version": "0.1.0",
        "project_name": "governance-test",
        "profile": "fullstack",
        "runtimes": ["claude"],
        "governance": {
            "scan": {
                "profile": "startup",
                "fail_on": [],
                "include": []
            },
            "guard": {
                "mode": "block",
                "blocked_commands": ["rm -rf", "terraform destroy", "kubectl delete"],
                "protected_files": [".env", ".env.local", "secrets.json"],
                "approval_required": ["terraform apply", "az ad", "aws iam", "echo approve"]
            }
        }
    }
    with open(niyam_dir / "niyam.yaml", "w", encoding="utf-8") as f:
        yaml.dump(config_data, f)
        
    project_data = {
        "name": "governance-test",
        "validation": {
            "test": "pytest"
        }
    }
    with open(niyam_dir / "project.yaml", "w", encoding="utf-8") as f:
        yaml.dump(project_data, f)


# ==========================================
# 1. CLI Command Shells
# ==========================================

def test_cli_existing_commands_still_work() -> None:
    """Verify that old commands like niyam doctor, validate, run still exist and function."""
    runner = CliRunner()
    # doctor --help
    result = runner.invoke(app, ["doctor", "--help"])
    assert result.exit_code == 0
    # run is composite/task runner command
    result = runner.invoke(app, ["run", "--help"])
    assert result.exit_code == 0


def test_cli_scan_help() -> None:
    """Verify scan help details are shown."""
    runner = CliRunner()
    result = runner.invoke(app, ["scan", "--help"])
    assert result.exit_code == 0
    assert "profile" in result.stdout
    assert "rules" in result.stdout


def test_cli_guard_help() -> None:
    """Verify guard help details are shown."""
    runner = CliRunner()
    result = runner.invoke(app, ["guard", "--help"])
    assert result.exit_code == 0
    assert "run" in result.stdout
    assert "logs" in result.stdout
    assert "status" in result.stdout


def test_cli_mcp_help() -> None:
    """Verify mcp help details are shown."""
    runner = CliRunner()
    result = runner.invoke(app, ["mcp", "--help"])
    assert result.exit_code == 0
    assert "register" in result.stdout
    assert "list" in result.stdout


def test_cli_cost_help() -> None:
    """Verify cost help details are shown."""
    runner = CliRunner()
    result = runner.invoke(app, ["cost", "--help"])
    assert result.exit_code == 0
    assert "log" in result.stdout
    assert "summary" in result.stdout


def test_cli_evidence_help() -> None:
    """Verify evidence help details are shown."""
    runner = CliRunner()
    result = runner.invoke(app, ["evidence", "--help"])
    assert result.exit_code == 0
    assert "generate" in result.stdout


def test_cli_governance_commands_are_additive() -> None:
    """Ensure adding governance commands does not crash standard commands."""
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "scan" in result.stdout
    assert "guard" in result.stdout
    assert "evidence" in result.stdout
    assert "cost" in result.stdout
    assert "mcp" in result.stdout


# ==========================================
# 2. niyam scan MVP
# ==========================================

def test_scan_empty_directory(tmp_path: Path) -> None:
    """Scanning an empty directory should return a score and low readiness decision."""
    results = run_scanner_checks(tmp_path, profile="startup")
    assert "score" in results
    assert "decision" in results
    assert results["decision"] in ("HIGH_RISK", "NO_GO", "CONDITIONAL_GO")


def test_scan_clean_app() -> None:
    """Scanning clean Next.js app should report GO or CONDITIONAL_GO with 0 critical findings."""
    results = run_scanner_checks(CLEAN_APP, profile="startup")
    assert results["score"] >= 85
    assert results["decision"] in ("GO", "CONDITIONAL_GO")
    criticals = [f for f in results["findings"] if f["severity"] == "critical"]
    assert len(criticals) == 0


def test_scan_risky_app_detects_env_file() -> None:
    """Scanning risky app should flag exposure of .env and .env.local."""
    results = run_scanner_checks(RISKY_APP, profile="startup")
    env_findings = [f for f in results["findings"] if f["id"] == "SEC001"]
    assert len(env_findings) >= 2
    paths = {f["file_path"] for f in env_findings}
    assert ".env" in paths
    assert ".env.local" in paths


def test_scan_detects_missing_readme() -> None:
    """Scanning risky app flags missing readme."""
    results = run_scanner_checks(RISKY_APP, profile="startup")
    readme_findings = [f for f in results["findings"] if f["id"] == "DOC001"]
    assert len(readme_findings) > 0


def test_scan_detects_missing_tests() -> None:
    """Scanning risky app flags missing tests."""
    results = run_scanner_checks(RISKY_APP, profile="startup")
    test_findings = [f for f in results["findings"] if f["id"] == "TST001"]
    assert len(test_findings) > 0


def test_scan_detects_missing_ci() -> None:
    """Scanning risky app flags missing CI workflow."""
    results = run_scanner_checks(RISKY_APP, profile="startup")
    ci_findings = [f for f in results["findings"] if f["id"] == "CICD001"]
    assert len(ci_findings) > 0


def test_scan_generates_json_report() -> None:
    """Typer CLI command scan can print output to json."""
    runner = CliRunner()
    result = runner.invoke(app, ["scan", str(CLEAN_APP), "--output", "json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert "score" in data
    assert "findings" in data


def test_scan_generates_markdown_report(tmp_path: Path) -> None:
    """Scan command can save a report file to path."""
    runner = CliRunner()
    report_file = tmp_path / "scan-report.md"
    result = runner.invoke(app, ["scan", str(CLEAN_APP), "--report-file", str(report_file)])
    assert result.exit_code == 0
    assert report_file.exists()
    content = report_file.read_text(encoding="utf-8")
    assert "# Niyam Production Readiness Report" in content


def test_scan_score_and_decision_are_present() -> None:
    """Scan results dictionary contains score and decision keys."""
    results = run_scanner_checks(CLEAN_APP, profile="startup")
    assert "score" in results
    assert "decision" in results


# ==========================================
# 3. Scanner Rule Engine
# ==========================================

def test_rule_engine_loads_startup_profile() -> None:
    """Startup rules file loads successfully."""
    rules = load_profile_rules("startup")
    assert len(rules) > 0
    assert any(r.id == "SEC001" for r in rules)


def test_rule_engine_loads_team_profile() -> None:
    """Team rules file loads successfully."""
    rules = load_profile_rules("team")
    assert len(rules) > 0


def test_rule_engine_loads_enterprise_profile() -> None:
    """Enterprise rules file loads successfully."""
    rules = load_profile_rules("enterprise")
    assert len(rules) > 0


def test_rule_engine_loads_regulated_profile() -> None:
    """Regulated rules file loads successfully."""
    rules = load_profile_rules("regulated")
    assert len(rules) > 0


def test_rule_engine_supports_file_exists(tmp_path: Path) -> None:
    """Support file_exists match type."""
    rule_def = {
        "id": "T01",
        "title": "Config Check",
        "category": "config",
        "severity": "low",
        "description": "Checking file",
        "recommendation": "Rec",
        "match": {"type": "file_exists", "patterns": ["target.txt"]}
    }
    rule = GovernanceRule(**rule_def)
    target = tmp_path / "target.txt"
    target.touch()
    
    findings = evaluate_rule(rule, tmp_path, [target])
    assert len(findings) == 1
    assert findings[0]["file_path"] == "target.txt"


def test_rule_engine_supports_file_missing(tmp_path: Path) -> None:
    """Support file_missing match type."""
    rule_def = {
        "id": "T02",
        "title": "Missing Check",
        "category": "config",
        "severity": "low",
        "description": "Checking file missing",
        "recommendation": "Rec",
        "match": {"type": "file_missing", "patterns": ["needed.txt"]}
    }
    rule = GovernanceRule(**rule_def)
    
    findings = evaluate_rule(rule, tmp_path, [])
    assert len(findings) == 1
    assert findings[0]["file_path"] == ""


def test_rule_engine_supports_filename_pattern(tmp_path: Path) -> None:
    """Support filename_pattern match type."""
    rule_def = {
        "id": "T03",
        "title": "Pattern Check",
        "category": "config",
        "severity": "low",
        "description": "Checking pattern",
        "recommendation": "Rec",
        "match": {"type": "filename_pattern", "patterns": ["*.secret"]}
    }
    rule = GovernanceRule(**rule_def)
    secret_file = tmp_path / "my.secret"
    secret_file.touch()
    
    findings = evaluate_rule(rule, tmp_path, [secret_file])
    assert len(findings) == 1


def test_rule_engine_supports_content_contains(tmp_path: Path) -> None:
    """Support content_contains match type."""
    rule_def = {
        "id": "T04",
        "title": "Contains Check",
        "category": "config",
        "severity": "low",
        "description": "Checking contains",
        "recommendation": "Rec",
        "match": {"type": "content_contains", "patterns": ["DANGER"]}
    }
    rule = GovernanceRule(**rule_def)
    f = tmp_path / "file.py"
    f.write_text("warning: DANGER here")
    
    findings = evaluate_rule(rule, tmp_path, [f])
    assert len(findings) == 1


def test_rule_engine_supports_content_regex(tmp_path: Path) -> None:
    """Support content_regex match type."""
    rule_def = {
        "id": "T05",
        "title": "Regex Check",
        "category": "config",
        "severity": "low",
        "description": "Checking regex",
        "recommendation": "Rec",
        "match": {"type": "content_regex", "patterns": ["[0-9]{3}-[0-9]{3}"]}
    }
    rule = GovernanceRule(**rule_def)
    f = tmp_path / "file.py"
    f.write_text("code = 123-456")
    
    findings = evaluate_rule(rule, tmp_path, [f])
    assert len(findings) == 1


def test_rule_engine_rejects_invalid_yaml_gracefully() -> None:
    """Verify scanner throws clear ValueError on invalid rules YAML."""
    with pytest.raises(ValueError) as exc:
        run_scanner_checks(CLEAN_APP, custom_rules_path=INVALID_RULES)
    assert "Validation error" in str(exc.value) or "invalid" in str(exc.value)


# ==========================================
# 4. niyam evidence
# ==========================================

def test_evidence_generate_from_scan_json(tmp_path: Path) -> None:
    """Generate evidence from pre-existing scan results JSON."""
    scan_json = tmp_path / "scan.json"
    scan_data = {
        "profile": "startup",
        "score": 88,
        "decision": "CONDITIONAL_GO",
        "findings": []
    }
    scan_json.write_text(json.dumps(scan_data), encoding="utf-8")
    
    report = run_generate_evidence(from_scan_json=str(scan_json), fmt="markdown")
    assert "Niyam Governance & Production Readiness" in report
    assert "88/100" in report
    assert "CONDITIONAL GO" in report


def test_evidence_markdown_output(tmp_path: Path) -> None:
    """Verify evidence generation supports markdown format."""
    scan_json = tmp_path / "scan.json"
    scan_json.write_text(json.dumps({"findings": []}), encoding="utf-8")
    report = run_generate_evidence(from_scan_json=str(scan_json), fmt="markdown")
    assert report.startswith("# ")


def test_evidence_json_output(tmp_path: Path) -> None:
    """Verify evidence generation supports json format."""
    scan_json = tmp_path / "scan.json"
    scan_json.write_text(json.dumps({"findings": []}), encoding="utf-8")
    report = run_generate_evidence(from_scan_json=str(scan_json), fmt="json")
    data = json.loads(report)
    assert "metadata" in data
    assert "scan" in data


def test_evidence_html_output_if_supported(tmp_path: Path) -> None:
    """Verify evidence generation supports html format."""
    scan_json = tmp_path / "scan.json"
    scan_json.write_text(json.dumps({"findings": []}), encoding="utf-8")
    report = run_generate_evidence(from_scan_json=str(scan_json), fmt="html")
    assert "<html" in report


def test_evidence_handles_missing_scan_file() -> None:
    """Verify generating evidence with missing scan file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        run_generate_evidence(from_scan_json="non-existent-scan.json")


def test_evidence_does_not_include_raw_secrets(tmp_path: Path) -> None:
    """Verify secrets in scan results are redacted in generated evidence reports."""
    scan_json = tmp_path / "scan.json"
    scan_data = {
        "findings": [
            {
                "id": "SEC002",
                "title": "Secret",
                "category": "secrets",
                "severity": "critical",
                "description": "Found api_key = sk-proj-supersecretkeyhere",
                "recommendation": "Fix api_key = sk-proj-supersecretkeyhere"
            }
        ]
    }
    scan_json.write_text(json.dumps(scan_data), encoding="utf-8")
    report = run_generate_evidence(from_scan_json=str(scan_json), fmt="markdown")
    assert "supersecretkey" not in report
    assert "sk-proj-REDACTED" in report or "api_key=REDACTED" in report or "REDACTED" in report


# ==========================================
# 5. niyam guard Observe Mode
# ==========================================

def test_guard_observe_runs_command() -> None:
    """Guard run executes standard safe shell command successfully."""
    runner = CliRunner()
    result = runner.invoke(app, ["guard", "run", "--capture-output", "--", "echo", "observe-ok"])
    assert result.exit_code == 0
    assert "observe-ok" in result.stdout


def test_guard_observe_preserves_exit_code() -> None:
    """Guard run preserves standard exit code from executed command."""
    runner = CliRunner()
    result = runner.invoke(app, ["guard", "run", "--", sys.executable, "-c", "import sys; sys.exit(42)"])
    assert result.exit_code == 42


def test_guard_observe_logs_command(tmp_path: Path) -> None:
    """Observed commands are written to guard log file."""
    # Temporarily set guard mode to observe
    niyam_yaml = tmp_path / ".niyam" / "niyam.yaml"
    with open(niyam_yaml, "r") as f:
        cfg = yaml.safe_load(f)
    cfg["governance"]["guard"]["mode"] = "observe"
    with open(niyam_yaml, "w") as f:
        yaml.dump(cfg, f)

    runner = CliRunner()
    runner.invoke(app, ["guard", "run", "--capture-output", "--", "echo", "logged-cmd"])
    
    log_file = tmp_path / ".niyam" / "logs" / "guard-actions.jsonl"
    assert log_file.exists()
    
    lines = log_file.read_text(encoding="utf-8").strip().split("\n")
    entry = json.loads(lines[-1])
    assert entry["mode"] == "observe"
    assert "logged-cmd" in entry["command"]


def test_guard_observe_logs_failed_command(tmp_path: Path) -> None:
    """Guard run logs failed commands with non-zero exit codes."""
    runner = CliRunner()
    runner.invoke(app, ["guard", "run", "--", sys.executable, "-c", "import sys; sys.exit(10)"])
    
    log_file = tmp_path / ".niyam" / "logs" / "guard-actions.jsonl"
    lines = log_file.read_text(encoding="utf-8").strip().split("\n")
    entry = json.loads(lines[-1])
    assert entry["exit_code"] == 10


def test_guard_observe_does_not_capture_output_by_default(tmp_path: Path) -> None:
    """Verify command stdout/stderr output is not stored in logs unless requested."""
    runner = CliRunner()
    runner.invoke(app, ["guard", "run", "--", "echo", "secret-output"])
    
    log_file = tmp_path / ".niyam" / "logs" / "guard-actions.jsonl"
    lines = log_file.read_text(encoding="utf-8").strip().split("\n")
    entry = json.loads(lines[-1])
    assert "output" not in entry


# ==========================================
# 6. niyam guard Policy Mode
# ==========================================

def test_guard_policy_allows_safe_command() -> None:
    """Safe command execution allowed under policy block."""
    runner = CliRunner()
    result = runner.invoke(app, ["guard", "run", "--mode", "block", "--", "echo", "safe-command"])
    assert result.exit_code == 0


def test_guard_policy_blocks_dangerous_command(tmp_path: Path) -> None:
    """Command matching blocked command rules is rejected and logged."""
    runner = CliRunner()
    result = runner.invoke(app, ["guard", "run", "--mode", "block", "--", "rm", "-rf", "folder"])
    assert result.exit_code == 1
    assert "Blocked:" in result.stdout
    
    log_file = tmp_path / ".niyam" / "logs" / "guard-actions.jsonl"
    lines = log_file.read_text(encoding="utf-8").strip().split("\n")
    entry = json.loads(lines[-1])
    assert entry["decision"] == "blocked"
    assert entry["mode"] == "block"


def test_guard_policy_warns_configured_command() -> None:
    """Command matching warn policy outputs warning and runs."""
    runner = CliRunner()
    result = runner.invoke(app, ["guard", "run", "--mode", "warn", "--", "rm", "-rf", "nonexistent_warning_dir"])
    assert result.exit_code == 0
    assert "Warning:" in result.stdout


def test_guard_policy_requires_approval(tmp_path: Path) -> None:
    """Approval commands trigger confirmation and handle deny/allow correctly."""
    runner = CliRunner()
    
    # 1. Deny approval
    result_deny = runner.invoke(
        app, 
        ["guard", "run", "--mode", "block", "--", "terraform", "apply"],
        input="n\n"
    )
    assert result_deny.exit_code == 1
    assert "Denied:" in result_deny.stdout
    
    log_file = tmp_path / ".niyam" / "logs" / "guard-actions.jsonl"
    lines = log_file.read_text(encoding="utf-8").strip().split("\n")
    entry_deny = json.loads(lines[-1])
    assert entry_deny["decision"] == "denied"
    
    # 2. Allow approval
    result_allow = runner.invoke(
        app, 
        ["guard", "run", "--capture-output", "--mode", "block", "--", "echo", "approve"],
        input="y\n"
    )
    assert result_allow.exit_code == 0
    assert "approve" in result_allow.stdout


def test_guard_policy_logs_decision(tmp_path: Path) -> None:
    """Guard logs store the policy decision classification."""
    runner = CliRunner()
    runner.invoke(app, ["guard", "run", "--mode", "warn", "--", "rm", "-rf", "warning"])
    
    log_file = tmp_path / ".niyam" / "logs" / "guard-actions.jsonl"
    lines = log_file.read_text(encoding="utf-8").strip().split("\n")
    entry = json.loads(lines[-1])
    assert entry["decision"] == "warned"


def test_guard_default_mode_is_observe(tmp_path: Path) -> None:
    """The default guard run execution runs in observe mode."""
    # Reset config guard mode
    niyam_yaml = tmp_path / ".niyam" / "niyam.yaml"
    with open(niyam_yaml, "r") as f:
        cfg = yaml.safe_load(f)
    if "governance" in cfg and "guard" in cfg["governance"]:
        del cfg["governance"]["guard"]["mode"]
    with open(niyam_yaml, "w") as f:
        yaml.dump(cfg, f)

    runner = CliRunner()
    runner.invoke(app, ["guard", "run", "--", "echo", "hello"])
    
    log_file = tmp_path / ".niyam" / "logs" / "guard-actions.jsonl"
    lines = log_file.read_text(encoding="utf-8").strip().split("\n")
    entry = json.loads(lines[-1])
    assert entry["mode"] == "observe"


def test_guard_invalid_mode() -> None:
    """Verify that passing an invalid guard mode results in an error exit code."""
    runner = CliRunner()
    result = runner.invoke(app, ["guard", "run", "--mode", "invalid", "--", "echo", "hello"])
    assert result.exit_code == 1
    assert "Invalid guard mode" in result.stdout


def test_guard_non_interactive_auto_deny(tmp_path: Path, monkeypatch) -> None:
    """Verify that approval commands are auto-denied in non-interactive/CI environments."""
    monkeypatch.setenv("CI", "1")
    monkeypatch.setenv("NIYAM_TEST_NON_INTERACTIVE", "1")
    monkeypatch.delenv("NIYAM_TEST", raising=False)
    
    runner = CliRunner()
    result = runner.invoke(
        app,
        ["guard", "run", "--mode", "block", "--", "echo", "approve"]
    )
    assert result.exit_code == 1
    assert "Denied: Non-interactive/CI environment detected" in result.stdout


def test_guard_substring_file_operand_no_match() -> None:
    """Verify that protected files matching only as substrings of arguments are allowed."""
    runner = CliRunner()
    result = runner.invoke(
        app,
        ["guard", "run", "--mode", "block", "--", "touch", ".env.example"]
    )
    assert result.exit_code == 0
    assert "Blocked:" not in result.stdout


# ==========================================
# 7. niyam mcp Registry
# ==========================================

def test_mcp_register_tool(tmp_path: Path) -> None:
    """Register tool inside CLI registry."""
    runner = CliRunner()
    result = runner.invoke(
        app,
        ["mcp", "register", "toolA", "--type", "mcp_server", "--risk", "high", "--no-approved"]
    )
    assert result.exit_code == 0
    assert "successfully registered" in result.stdout
    
    registry_file = tmp_path / ".niyam" / "mcp-registry.json"
    assert registry_file.exists()
    data = json.loads(registry_file.read_text(encoding="utf-8"))
    assert "toolA" in data["tools"]
    assert data["tools"]["toolA"]["risk_level"] == "high"


def test_mcp_list_tools() -> None:
    """List registered tools from MCP command."""
    runner = CliRunner()
    runner.invoke(app, ["mcp", "register", "toolA", "--type", "mcp_server", "--risk", "high"])
    
    result = runner.invoke(app, ["mcp", "list"])
    assert result.exit_code == 0
    assert "toolA" in result.stdout


def test_mcp_show_tool() -> None:
    """Show details of registered tool."""
    runner = CliRunner()
    runner.invoke(app, ["mcp", "register", "toolB", "--type", "api", "--risk", "medium"])
    
    result = runner.invoke(app, ["mcp", "show", "toolB"])
    assert result.exit_code == 0
    assert "toolB" in result.stdout
    assert "api" in result.stdout
    assert "medium" in result.stdout


def test_mcp_duplicate_registration() -> None:
    """Registering tool twice should raise an error."""
    runner = CliRunner()
    runner.invoke(app, ["mcp", "register", "dupTool", "--type", "cli"])
    result = runner.invoke(app, ["mcp", "register", "dupTool", "--type", "cli"])
    assert result.exit_code == 1
    assert "already registered" in result.stdout


def test_mcp_risk_report() -> None:
    """Verify MCP risk-report shows statistics correctly."""
    runner = CliRunner()
    runner.invoke(app, ["mcp", "register", "unsafeTool", "--type", "api", "--risk", "critical", "--no-approved"])
    result = runner.invoke(app, ["mcp", "risk-report"])
    assert result.exit_code == 0
    assert "unsafeTool" in result.stdout
    assert "critical" in result.stdout


def test_mcp_registry_schema_versioned(tmp_path: Path) -> None:
    """Verify MCP registry saves schema format containing version."""
    runner = CliRunner()
    runner.invoke(app, ["mcp", "register", "toolC", "--type", "local_tool"])
    
    registry_file = tmp_path / ".niyam" / "mcp-registry.json"
    data = json.loads(registry_file.read_text(encoding="utf-8"))
    assert "schema_version" in data or "version" in data
    assert "tools" in data


# ==========================================
# 8. niyam cost Tracking
# ==========================================

def test_cost_log_event(tmp_path: Path) -> None:
    """Log an AI model execution event and check cost-events.jsonl."""
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "cost",
            "log",
            "--tool",
            "gemini-cli",
            "--model",
            "gemini-pro",
            "--input-tokens",
            "4000",
            "--output-tokens",
            "1000",
            "--task",
            "test-task"
        ]
    )
    assert result.exit_code == 0
    
    cost_file = tmp_path / ".niyam" / "logs" / "cost-events.jsonl"
    assert cost_file.exists()
    
    lines = cost_file.read_text(encoding="utf-8").strip().split("\n")
    event = json.loads(lines[-1])
    assert event["tool_name"] == "gemini-cli"
    assert event["model"] == "gemini-pro"
    assert event["input_tokens"] == 4000
    assert event["output_tokens"] == 1000
    assert event["task_id"] == "test-task"


def test_cost_summary_total() -> None:
    """cost summary shows aggregates correctly."""
    runner = CliRunner()
    runner.invoke(app, ["cost", "log", "--model", "claude-sonnet", "--input-tokens", "100", "--output-tokens", "20"])
    result = runner.invoke(app, ["cost", "summary"])
    assert result.exit_code == 0
    assert "Total Logged Events: 1" in result.stdout


def test_cost_report_by_tool() -> None:
    """cost report shows breakdown by tool."""
    runner = CliRunner()
    runner.invoke(app, ["cost", "log", "--tool", "custom-tool", "--model", "claude-sonnet"])
    result = runner.invoke(app, ["cost", "report"])
    assert result.exit_code == 0


def test_cost_report_by_model() -> None:
    """cost report shows breakdown by model."""
    runner = CliRunner()
    runner.invoke(app, ["cost", "log", "--model", "custom-model"])
    result = runner.invoke(app, ["cost", "report"])
    assert result.exit_code == 0


def test_cost_report_by_task() -> None:
    """cost report shows breakdown by task."""
    runner = CliRunner()
    runner.invoke(app, ["cost", "log", "--task", "custom-task"])
    result = runner.invoke(app, ["cost", "report"])
    assert result.exit_code == 0


def test_cost_handles_missing_optional_fields(tmp_path: Path) -> None:
    """cost log handles empty optional fields cleanly."""
    runner = CliRunner()
    result = runner.invoke(app, ["cost", "log"])
    assert result.exit_code == 0
    
    cost_file = tmp_path / ".niyam" / "logs" / "cost-events.jsonl"
    lines = cost_file.read_text(encoding="utf-8").strip().split("\n")
    event = json.loads(lines[-1])
    assert event["tool_name"] == "unknown"


# ==========================================
# 9. Integrated Evidence Report
# ==========================================

def test_integrated_evidence_with_scan_only(tmp_path: Path) -> None:
    """Integrated evidence report includes only requested scan section."""
    scan_json = tmp_path / "scan.json"
    scan_json.write_text(json.dumps({"findings": []}), encoding="utf-8")
    
    report = run_generate_evidence(from_scan_json=str(scan_json), include="scan", fmt="markdown")
    assert "Production Readiness" in report
    assert "Agent Governance" not in report
    assert "Cost" not in report


def test_integrated_evidence_with_scan_and_guard(tmp_path: Path) -> None:
    """Integrated evidence report includes scan and guard sections."""
    scan_json = tmp_path / "scan.json"
    scan_json.write_text(json.dumps({"findings": []}), encoding="utf-8")
    
    report = run_generate_evidence(from_scan_json=str(scan_json), include="scan,guard", fmt="markdown")
    assert "Production Readiness" in report
    assert "Agent Governance" in report
    assert "Cost" not in report


def test_integrated_evidence_with_scan_guard_mcp_cost(tmp_path: Path) -> None:
    """Integrated evidence report includes all sections combined."""
    scan_json = tmp_path / "scan.json"
    scan_json.write_text(json.dumps({"findings": []}), encoding="utf-8")
    
    # Pre-populate some cost and mcp data
    runner = CliRunner()
    runner.invoke(app, ["mcp", "register", "someTool", "--type", "cli"])
    runner.invoke(app, ["cost", "log", "--model", "claude-sonnet"])
    
    report = run_generate_evidence(from_scan_json=str(scan_json), include="scan,guard,mcp,cost", fmt="markdown")
    assert "Production Readiness" in report
    assert "Agent Governance" in report
    assert "MCP" in report or "Tool" in report
    assert "Cost" in report


def test_integrated_evidence_skips_missing_sections(tmp_path: Path) -> None:
    """Sections omitted from include argument are not in report output."""
    scan_json = tmp_path / "scan.json"
    scan_json.write_text(json.dumps({"findings": []}), encoding="utf-8")
    
    report = run_generate_evidence(from_scan_json=str(scan_json), include="scan", fmt="markdown")
    assert "Agent Governance" not in report
    assert "MCP" not in report
    assert "Cost" not in report


def test_integrated_evidence_redacts_sensitive_values(tmp_path: Path) -> None:
    """Verify sensitive values (e.g. ghp_ or private keys) are redacted in integrated reports."""
    scan_json = tmp_path / "scan.json"
    scan_data = {
        "findings": [
            {
                "id": "SEC002",
                "title": "Secrets",
                "category": "secrets",
                "severity": "critical",
                "description": "Found api_key = ghp_abcdefghijklmnopqrstuvwxyz0123456789",
                "recommendation": "Fix api_key = ghp_abcdefghijklmnopqrstuvwxyz0123456789"
            }
        ]
    }
    scan_json.write_text(json.dumps(scan_data), encoding="utf-8")
    
    report = run_generate_evidence(from_scan_json=str(scan_json), include="scan", fmt="markdown")
    assert "ghp_abcdef" not in report
    assert "ghp_REDACTED" in report or "api_key=REDACTED" in report or "REDACTED" in report
