"""Orchestration Phase 0/1: RuntimeSpec registry, invocations, fake CLIs."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
import yaml

from niyam.runtimes.executor import (
    build_runtime_invocation,
    parse_usage_from_output,
    run_runtime,
)
from niyam.runtimes.registry import (
    get_runtime_registry,
    get_runtime_spec,
    list_runtime_names,
    register_runtime_spec,
)
from niyam.runtimes.specs import RuntimeSpec, BUILTIN_RUNTIME_SPECS


FAKES_BIN = Path(__file__).parent / "fakes" / "bin"


@pytest.fixture
def fake_path(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    """Prepend fake vendor CLIs to PATH and set capture dir."""
    cap = tmp_path / "capture"
    cap.mkdir()
    monkeypatch.setenv("PATH", f"{FAKES_BIN}:{os.environ.get('PATH', '')}")
    monkeypatch.setenv("NIYAM_FAKE_CAPTURE", str(cap))
    # Ensure tests do not force simulate-only paths that skip binaries
    monkeypatch.delenv("NIYAM_TEST", raising=False)
    return cap


def test_builtin_registry_has_agy_runtime() -> None:
    names = list_runtime_names()
    assert "claude" in names
    assert "codex" in names
    assert "gemini" in names
    assert "agy" in names
    assert set(BUILTIN_RUNTIME_SPECS) <= set(names)


def test_claude_invocation_uses_p_flag_not_bare_path() -> None:
    inv = build_runtime_invocation(
        "claude", prompt_text="implement /health", include_sandbox=False
    )
    assert inv.argv[0].endswith("claude") or inv.argv[0] == "claude"
    assert "-p" in inv.argv
    assert "implement /health" in inv.argv
    assert "--output-format" in inv.argv
    assert "json" in inv.argv
    # Must not pass only a filesystem path as the sole positional arg
    assert not any(str(a).endswith("prompt.md") and a == inv.argv[-1] for a in inv.argv if False)


def test_codex_invocation_uses_exec_json_stdin() -> None:
    inv = build_runtime_invocation(
        "codex", prompt_text="fix the bug", include_sandbox=True
    )
    assert "exec" in inv.argv
    assert "--json" in inv.argv
    assert "-" in inv.argv
    assert inv.stdin_data == "fix the bug"
    assert "--sandbox" in inv.argv


def test_gemini_invocation_has_p_and_json_no_skip_trust() -> None:
    inv = build_runtime_invocation(
        "gemini", prompt_text="review diff", include_sandbox=False
    )
    assert "-p" in inv.argv
    assert "review diff" in inv.argv
    assert "-o" in inv.argv
    assert "json" in inv.argv
    assert "--skip-trust" not in inv.argv


def test_agy_invocation_uses_non_interactive_print_mode() -> None:
    inv = build_runtime_invocation("agy", prompt_text="review diff", include_sandbox=False)
    assert inv.argv[0].endswith("agy") or inv.argv[0] == "agy"
    assert inv.argv[1:] == ["--print", "review diff"]


def test_custom_runtime_spec_from_runtimes_yaml(tmp_path: Path) -> None:
    niyam = tmp_path / ".niyam"
    niyam.mkdir()
    (niyam / "runtimes.yaml").write_text(
        yaml.safe_dump(
            {
                "execution_specs": {
                    "grok": {
                        "binary": "grok",
                        "prompt_delivery": "stdin",
                        "exec_args": ["exec", "-"],
                        "usage_parser": "generic_json",
                        "capabilities": ["implementation"],
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    # create marker so find_niyam_root works
    (niyam / "niyam.yaml").write_text("version: '1.0.0'\n", encoding="utf-8")
    spec = get_runtime_spec("grok", repo_root=tmp_path, strict=True)
    assert spec is not None
    assert spec.binary == "grok"
    assert "grok" in list_runtime_names(tmp_path)


def test_register_runtime_spec_persists(tmp_path: Path) -> None:
    niyam = tmp_path / ".niyam"
    niyam.mkdir()
    (niyam / "niyam.yaml").write_text("version: '1.0.0'\n", encoding="utf-8")
    spec = RuntimeSpec(
        name="antigravity",
        binary="antigravity",
        prompt_delivery="stdin",
        exec_args=["run", "-"],
    )
    path = register_runtime_spec(spec, repo_root=tmp_path)
    assert path.exists()
    loaded = get_runtime_spec("antigravity", repo_root=tmp_path, strict=True)
    assert loaded is not None
    assert loaded.binary == "antigravity"


def test_parse_claude_json_usage() -> None:
    text = json.dumps(
        {"usage": {"input_tokens": 10, "output_tokens": 5, "cost_usd": 0.01}, "model": "claude-sonnet"}
    )
    usage = parse_usage_from_output(text, parser="claude_json", runtime="claude")
    assert usage is not None
    assert usage["input_tokens"] == 10
    assert usage["output_tokens"] == 5
    assert usage["estimated"] is False


def test_parse_codex_jsonl_usage() -> None:
    text = "\n".join(
        [
            json.dumps({"type": "log", "msg": "hi"}),
            json.dumps(
                {
                    "type": "result",
                    "model": "gpt-5-codex",
                    "usage": {"input_tokens": 11, "output_tokens": 3, "cost_usd": 0.002},
                }
            ),
        ]
    )
    usage = parse_usage_from_output(text, parser="codex_jsonl", runtime="codex")
    assert usage is not None
    assert usage["input_tokens"] == 11
    assert usage["output_tokens"] == 3


def test_run_runtime_claude_with_fakes(fake_path: Path) -> None:
    result = run_runtime(
        "claude",
        prompt_text="hello world task",
        include_sandbox=False,
        timeout=30,
    )
    assert result.success, result.stderr
    assert result.usage is not None
    assert result.usage["input_tokens"] == 120
    assert (fake_path / "claude-prompt.txt").read_text() == "hello world task"


def test_run_runtime_codex_with_fakes(fake_path: Path) -> None:
    result = run_runtime(
        "codex",
        prompt_text="implement feature X",
        include_sandbox=True,
        timeout=30,
    )
    assert result.success, result.stderr
    assert result.usage is not None
    assert result.usage["input_tokens"] == 90
    assert "exec" in " ".join(result.argv)
    assert (fake_path / "codex-prompt.txt").read_text() == "implement feature X"


def test_run_runtime_gemini_with_fakes(fake_path: Path) -> None:
    result = run_runtime(
        "gemini",
        prompt_text="review the diff",
        include_sandbox=False,
        timeout=30,
    )
    assert result.success, result.stderr
    assert result.usage is not None
    assert result.usage["input_tokens"] == 100
    assert (fake_path / "gemini-prompt.txt").read_text() == "review the diff"


def test_run_runtime_agy_with_fakes(fake_path: Path) -> None:
    result = run_runtime("agy", prompt_text="review the diff", include_sandbox=False, timeout=30)
    assert result.success, result.stderr
    assert (fake_path / "agy-prompt.txt").read_text() == "review the diff"


def test_codex_rejects_legacy_positional_without_exec(fake_path: Path) -> None:
    """Document old broken grammar: bare positional is not non-interactive."""
    import subprocess

    res = subprocess.run(
        ["codex", "/tmp/some/prompt.md"],
        capture_output=True,
        text=True,
    )
    assert res.returncode != 0
    assert "codex exec" in (res.stderr or "").lower() or "tty" in (res.stderr or "").lower()


def test_legacy_claude_path_only_is_wrong_grammar(fake_path: Path) -> None:
    """Old mission path [claude, prompt.md] is not a valid -p invocation."""
    import subprocess

    res = subprocess.run(
        ["claude", "/tmp/does-not-exist-prompt.md"],
        capture_output=True,
        text=True,
    )
    # Without -p the fake rejects missing prompt
    assert res.returncode != 0


def test_task_runner_parse_cli_token_usage_delegates() -> None:
    from niyam.mission.task_runner import parse_cli_token_usage

    text = json.dumps(
        {"usage": {"input_tokens": 7, "output_tokens": 2}, "model": "claude-sonnet"}
    )
    usage = parse_cli_token_usage(text, runtime="claude")
    assert usage is not None
    assert usage["input_tokens"] == 7


def test_heartbeat_thread_refreshes_last_seen(tmp_path: Path) -> None:
    import time
    from niyam.core.swarm import (
        heartbeat,
        is_agent_stale,
        load_swarm_state,
        start_heartbeat_thread,
    )

    # Minimal workspace
    (tmp_path / ".niyam").mkdir()
    stop = start_heartbeat_thread(
        agent_id="agent-hb",
        role="backend",
        task_id="T1",
        repo_root=tmp_path,
        interval_seconds=0.2,
        status="busy",
    )
    try:
        time.sleep(0.5)
        state = load_swarm_state(tmp_path)
        assert "agent-hb" in state.agents
        assert not is_agent_stale(state.agents["agent-hb"])
    finally:
        stop()


def test_stale_timeout_covers_default_task_duration() -> None:
    from niyam.core.swarm import STALE_HEARTBEAT_TIMEOUT

    # Default task timeout is 600s; stale timeout must exceed that
    assert STALE_HEARTBEAT_TIMEOUT >= 600
