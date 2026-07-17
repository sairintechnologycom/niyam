#!/usr/bin/env python3
"""Fake vendor coding CLIs for orchestration truth harness.

Emulates real-ish argument grammars:
- claude: requires -p PROMPT (or -p with next arg); supports --output-format json
- codex: non-interactive requires ``exec``; bare positional simulates TUI failure
- gemini: requires -p PROMPT; rejects legacy --skip-trust

Capture directory: set NIYAM_FAKE_CAPTURE to a directory; prompt + argv are written.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def _capture(name: str, argv: list[str], prompt: str) -> None:
    cap = os.environ.get("NIYAM_FAKE_CAPTURE")
    if not cap:
        return
    root = Path(cap)
    root.mkdir(parents=True, exist_ok=True)
    (root / f"{name}-argv.txt").write_text("\n".join(argv), encoding="utf-8")
    (root / f"{name}-prompt.txt").write_text(prompt, encoding="utf-8")


def _extract_p_prompt(argv: list[str]) -> str | None:
    for i, arg in enumerate(argv):
        if arg in ("-p", "--prompt", "--print") and i + 1 < len(argv):
            return argv[i + 1]
        if arg.startswith("-p=") or arg.startswith("--prompt=") or arg.startswith("--print="):
            return arg.split("=", 1)[1]
    return None


def run_claude(argv: list[str]) -> int:
    # Reject unknown legacy flags that look like wrong adapters
    if "--bare" in argv:
        print("error: unknown option --bare", file=sys.stderr)
        return 2
    prompt = _extract_p_prompt(argv)
    if prompt is None:
        # stdin fallback
        if not sys.stdin.isatty():
            prompt = sys.stdin.read()
    if not prompt:
        print("error: missing -p prompt", file=sys.stderr)
        return 2
    _capture("claude", argv, prompt)
    if "--output-format" in argv and "json" in argv:
        payload = {
            "result": f"ok: {prompt[:80]}",
            "model": "claude-sonnet",
            "usage": {
                "input_tokens": 120,
                "output_tokens": 40,
                "cost_usd": 0.0012,
            },
        }
        print(json.dumps(payload))
    else:
        print(f"Total tokens: 160 (input: 120 / output: 40)")
        print("Total cost: $0.0012")
        print(prompt[:200])
    return 0


def run_codex(argv: list[str]) -> int:
    # Real codex non-interactive uses `exec`. Bare positional is TUI.
    if not argv or argv[0] != "exec":
        print(
            "error: interactive TUI requires a tty; use `codex exec` for non-interactive",
            file=sys.stderr,
        )
        return 2
    prompt = ""
    if "-" in argv:
        prompt = sys.stdin.read()
    else:
        # trailing free text
        for a in reversed(argv[1:]):
            if not a.startswith("-"):
                prompt = a
                break
    if not prompt:
        print("error: empty prompt", file=sys.stderr)
        return 2
    _capture("codex", argv, prompt)
    # JSONL event stream
    print(
        json.dumps(
            {
                "type": "result",
                "model": "gpt-5-codex",
                "usage": {"input_tokens": 90, "output_tokens": 30, "cost_usd": 0.0009},
                "message": "ok",
            }
        )
    )
    return 0


def run_gemini(argv: list[str]) -> int:
    if "--skip-trust" in argv:
        print("error: unknown option --skip-trust (use --approval-mode)", file=sys.stderr)
        return 2
    prompt = _extract_p_prompt(argv)
    if prompt is None and not sys.stdin.isatty():
        prompt = sys.stdin.read()
    if not prompt:
        print("error: missing -p prompt", file=sys.stderr)
        return 2
    _capture("gemini", argv, prompt)
    if "-o" in argv and "json" in argv:
        print(
            json.dumps(
                {
                    "model": "gemini-2.5-flash",
                    "stats": {
                        "promptTokenCount": 100,
                        "candidatesTokenCount": 25,
                        "cost_usd": 0.0005,
                    },
                    "response": "ok",
                }
            )
        )
    else:
        print(prompt[:200])
    return 0


def run_agy(argv: list[str]) -> int:
    prompt = _extract_p_prompt(argv)
    if prompt is None:
        print("error: missing --print prompt", file=sys.stderr)
        return 2
    _capture("agy", argv, prompt)
    print(f"Total tokens: 125 (input: 95 / output: 30)")
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(argv if argv is not None else sys.argv[1:])
    # Determine identity from symlink/name or NIYAM_FAKE_RUNTIME
    name = os.environ.get("NIYAM_FAKE_RUNTIME")
    if not name:
        prog = Path(sys.argv[0]).name.lower()
        if "claude" in prog:
            name = "claude"
        elif "codex" in prog:
            name = "codex"
        elif "gemini" in prog:
            name = "gemini"
        elif "agy" in prog:
            name = "agy"
        else:
            name = "claude"
    if name == "claude":
        return run_claude(argv)
    if name == "codex":
        return run_codex(argv)
    if name == "gemini":
        return run_gemini(argv)
    if name == "agy":
        return run_agy(argv)
    print(f"unknown fake runtime {name}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
