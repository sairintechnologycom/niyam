"""E2E tests for niyam evidence generation and secret redaction."""

from __future__ import annotations

from pathlib import Path


def test_evidence_report_combination_and_redaction(tmp_path: Path, run_cli) -> None:
    """Evidence report combines scan, guard, and MCP, and secrets are redacted."""
    # 1. Initialize Niyam
    init_res = run_cli(["niyam", "init", "--profile", "fullstack"], cwd=tmp_path)
    assert init_res.returncode == 0

    # 2. Setup a code file with a secret
    secret_file = tmp_path / "app_secrets.py"
    secret_file.write_text(
        'OPENAI_KEY = "sk-proj-abcdefghijklmnopqrstuvwxyz123456"\n'
        'AWS_KEY = "AKIA1234567890123456"\n',
        encoding="utf-8",
    )

    # 3. Create .gitignore and README to minimize unrelated findings
    (tmp_path / ".gitignore").write_text(".env\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("# Test App\n", encoding="utf-8")
    (tmp_path / "package-lock.json").write_text("{}", encoding="utf-8")

    # 4. Register an MCP tool
    reg_res = run_cli(
        [
            "niyam",
            "mcp",
            "register",
            "secret-caller-tool",
            "--type",
            "api",
            "--command-or-url",
            "https://api.test.com/v1?key=sk-proj-abcdefghijklmnopqrstuvwxyz123456",
            "--approved",
            "false",
        ],
        cwd=tmp_path,
    )
    assert reg_res.returncode == 0

    # 5. Run a guard observed command containing a secret
    guard_res = run_cli(
        [
            "niyam",
            "guard",
            "run",
            "--",
            "echo",
            "Secret token is sk-proj-abcdefghijklmnopqrstuvwxyz123456",
        ],
        cwd=tmp_path,
    )
    assert guard_res.returncode == 0

    # 6. Run the repository readiness scan and save it
    scan_json = tmp_path / "scan.json"
    scan_res = run_cli(
        ["niyam", "scan", "--output", "json", "--report-file", str(scan_json)],
        cwd=tmp_path,
    )
    assert scan_res.returncode == 0 or scan_res.returncode == 2

    # 7. Verify scan report exists and does not contain raw secrets
    assert scan_json.exists()
    scan_content = scan_json.read_text(encoding="utf-8")
    assert "sk-proj-abcdefghijklmnopqrstuvwxyz123456" not in scan_content
    assert "AKIA1234567890123456" not in scan_content

    # 8. Generate the evidence report
    evidence_md = tmp_path / "evidence.md"
    ev_res = run_cli(
        [
            "niyam",
            "evidence",
            "generate",
            "--from",
            str(scan_json),
            "--format",
            "markdown",
            "--output",
            str(evidence_md),
        ],
        cwd=tmp_path,
    )
    assert ev_res.returncode == 0

    # 9. Verify evidence report combined all three sections and redacted secrets
    assert evidence_md.exists()
    evidence_content = evidence_md.read_text(encoding="utf-8")

    # Check sections
    assert "Readiness Score" in evidence_content  # Scan section
    assert "Agent Governance" in evidence_content  # Guard section
    assert "MCP" in evidence_content or "Tool" in evidence_content  # MCP section

    # Check secrets redaction in the evidence report
    assert "sk-proj-abcdefghijklmnopqrstuvwxyz123456" not in evidence_content
    assert "AKIA1234567890123456" not in evidence_content
    assert "[REDACTED_SECRET]" in evidence_content or "REDACTED" in evidence_content
