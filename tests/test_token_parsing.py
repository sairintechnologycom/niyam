"""Tests for token parsing and honest ledger metrics."""

from __future__ import annotations

import json
import yaml
from pathlib import Path

from sutra.mission.executor import parse_cli_token_usage, update_token_ledger


def test_parse_claude_cli_output() -> None:
    """Should correctly parse token counts and cost from Claude CLI stdout."""
    sample_stdout = """
    Thinking Process:
    1. Analyze the requirements...
    
    Total tokens: 12,345 (input: 8,000 / output: 4,345)
    Total cost: $0.1234
    """
    parsed = parse_cli_token_usage(sample_stdout)
    assert parsed is not None
    assert parsed["runtime"] == "claude"
    assert parsed["total_tokens"] == 12345
    assert parsed["input_tokens"] == 8000
    assert parsed["output_tokens"] == 4345
    assert parsed["cost_usd"] == 0.1234
    assert not parsed["estimated"]


def test_parse_unknown_format_returns_none() -> None:
    """Should return None if output format is unknown or missing token info."""
    sample_stdout = "Doing task now...\nDone!"
    assert parse_cli_token_usage(sample_stdout) is None


def test_ledger_labels_estimates_honestly(tmp_path: Path) -> None:
    """Should store estimated: true and estimation_method when using fallback estimation."""
    run_dir = tmp_path / "runs" / "test-mission"
    run_dir.mkdir(parents=True)

    update_token_ledger(
        run_dir=run_dir,
        task_id="T1",
        agent="backend-specialist",
        runtime="claude",
        input_tokens=100,
        output_tokens=50,
        estimated=True,
        estimation_method="char_count_heuristic",
    )

    ledger_file = run_dir / "token-ledger.json"
    assert ledger_file.exists()

    with open(ledger_file) as f:
        ledger = json.load(f)

    event = ledger["events"][0]
    assert event["estimated"] is True
    assert event["estimation_method"] == "char_count_heuristic"
    # By default, marketing/baseline columns should NOT be present
    assert "baseline_tokens" not in event
    assert "savings_usd" not in event


def test_ledger_uses_real_values_when_available(tmp_path: Path) -> None:
    """Should store estimated: false and use cost_override when available from parsed CLI output."""
    run_dir = tmp_path / "runs" / "test-mission"
    run_dir.mkdir(parents=True)

    update_token_ledger(
        run_dir=run_dir,
        task_id="T1",
        agent="backend-specialist",
        runtime="claude",
        input_tokens=8000,
        output_tokens=4345,
        estimated=False,
        cost_override=0.1234,
    )

    ledger_file = run_dir / "token-ledger.json"
    assert ledger_file.exists()

    with open(ledger_file) as f:
        ledger = json.load(f)

    event = ledger["events"][0]
    assert event["estimated"] is False
    assert "estimation_method" not in event
    assert event["cost_usd"] == 0.1234
    assert event["input_tokens"] == 8000
    assert event["output_tokens"] == 4345


def test_baseline_multiplier_opt_in(tmp_path: Path) -> None:
    """Should only include baseline & savings metrics in the ledger if show_marketing_metrics is enabled in config."""
    # Setup mock workspace structure under tmp_path
    sutra_dir = tmp_path / ".sutra"
    sutra_dir.mkdir()

    # Write a sutra.yaml with show_marketing_metrics=true
    with open(sutra_dir / "sutra.yaml", "w") as f:
        yaml.dump({"show_marketing_metrics": True, "baseline_multiplier": 4.0}, f)

    run_dir = sutra_dir / "runs" / "test-mission"
    run_dir.mkdir(parents=True)

    # Run update_token_ledger
    update_token_ledger(
        run_dir=run_dir,
        task_id="T1",
        agent="backend-specialist",
        runtime="claude",
        input_tokens=100,
        output_tokens=50,
        estimated=True,
        estimation_method="char_count_heuristic",
    )

    ledger_file = run_dir / "token-ledger.json"
    assert ledger_file.exists()

    with open(ledger_file) as f:
        ledger = json.load(f)

    event = ledger["events"][0]
    assert event["baseline_tokens"] == 600  # (100 + 50) * 4.0
    assert "baseline_cost_usd" in event
    assert "savings_usd" in event
    assert "projected_estimate_labeled" in event

    assert "total_baseline_tokens" in ledger["summary"]
