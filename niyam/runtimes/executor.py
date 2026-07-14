"""Execute coding-agent CLIs from RuntimeSpec (correct vendor grammars)."""

from __future__ import annotations

import json
import logging
import os
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from niyam.runtimes.registry import get_runtime_spec
from niyam.runtimes.specs import RuntimeSpec

logger = logging.getLogger(__name__)


@dataclass
class RuntimeInvocation:
    argv: list[str]
    stdin_data: str | None = None
    env: dict[str, str] = field(default_factory=dict)
    spec: RuntimeSpec | None = None


@dataclass
class RuntimeRunResult:
    success: bool
    returncode: int
    stdout: str
    stderr: str
    usage: dict[str, Any] | None = None
    exhaustion_detected: bool = False
    argv: list[str] = field(default_factory=list)
    error: str | None = None


def _render_args(
    template: list[str],
    *,
    prompt: str,
    prompt_file: str,
    model: str | None,
) -> list[str]:
    rendered: list[str] = []
    for part in template:
        value = (
            part.replace("{prompt}", prompt)
            .replace("{prompt_file}", prompt_file)
            .replace("{model}", model or "")
        )
        # Drop empty model placeholders (e.g. trailing empty --model value)
        if value == "" and "{model}" in part:
            # also drop previous flag if it was model_flag alone — handled by caller
            continue
        rendered.append(value)
    return rendered


def build_runtime_invocation(
    runtime_name: str,
    *,
    prompt_text: str | None = None,
    prompt_file: str | Path | None = None,
    model: str | None = None,
    tier: str | None = None,
    mode: str = "exec",
    repo_root: Path | None = None,
    include_sandbox: bool = True,
) -> RuntimeInvocation:
    """Build argv + stdin for a named runtime."""
    spec = get_runtime_spec(runtime_name, repo_root)
    if spec is None:
        raise ValueError(f"Unknown runtime: {runtime_name}")

    prompt_path = Path(prompt_file) if prompt_file else None
    if prompt_text is None and prompt_path and prompt_path.exists():
        prompt_text = prompt_path.read_text(encoding="utf-8")
    if prompt_text is None:
        prompt_text = ""

    resolved_model = spec.resolve_model(tier=tier, model=model)
    args_template = list(spec.exec_args if mode == "exec" else (spec.plan_args or spec.exec_args))

    if include_sandbox and spec.sandbox_args:
        # Insert sandbox args after binary-level subcommand when present
        # e.g. codex exec --sandbox workspace-write --json -
        if args_template and args_template[0] in {"exec", "run"}:
            args_template = [args_template[0], *spec.sandbox_args, *args_template[1:]]
        else:
            args_template = [*spec.sandbox_args, *args_template]

    if resolved_model and spec.model_flag:
        # Append model flag if not already in template
        joined = " ".join(args_template)
        if "{model}" not in joined and spec.model_flag not in args_template:
            args_template = [*args_template, spec.model_flag, "{model}"]

    rendered = _render_args(
        args_template,
        prompt=prompt_text,
        prompt_file=str(prompt_path) if prompt_path else "",
        model=resolved_model,
    )

    # Clean up dangling model flag without value
    cleaned: list[str] = []
    skip_next_empty = False
    for i, part in enumerate(rendered):
        if skip_next_empty:
            skip_next_empty = False
            if part == "":
                continue
        if part in (spec.model_flag, "--model", "-m") and (
            i + 1 >= len(rendered) or rendered[i + 1] == ""
        ):
            skip_next_empty = True
            continue
        cleaned.append(part)
    rendered = cleaned

    stdin_data: str | None = None
    if spec.prompt_delivery == "stdin":
        stdin_data = prompt_text
    elif spec.prompt_delivery == "file-flag" and prompt_path:
        # file path already substituted via {prompt_file}
        pass

    binary = shutil.which(spec.binary) or spec.binary
    argv = [binary, *rendered]
    env = dict(os.environ)
    env.update(spec.env)
    # Hookless runtimes get PATH shims for deny-list command enforcement
    if repo_root is not None:
        try:
            from niyam.policies.path_shim import inject_path_shim_env

            env = inject_path_shim_env(env, Path(repo_root), runtime_name)
        except Exception:
            logger.debug("path-shim inject skipped", exc_info=True)
    return RuntimeInvocation(argv=argv, stdin_data=stdin_data, env=env, spec=spec)


def parse_usage_from_output(
    output_text: str,
    parser: str = "text_regex",
    runtime: str | None = None,
) -> dict[str, Any] | None:
    """Parse token usage from CLI stdout/stderr using a named strategy."""
    text = output_text or ""
    if not text.strip():
        return None

    if parser == "claude_json":
        return _parse_claude_json(text, runtime or "claude") or _parse_text_regex(
            text, runtime or "claude"
        )
    if parser == "codex_jsonl":
        return _parse_codex_jsonl(text, runtime or "codex") or _parse_text_regex(
            text, runtime or "codex"
        )
    if parser == "gemini_json":
        return _parse_gemini_json(text, runtime or "gemini") or _parse_text_regex(
            text, runtime or "gemini"
        )
    if parser == "generic_json":
        return _parse_generic_json(text, runtime) or _parse_text_regex(text, runtime)
    return _parse_text_regex(text, runtime)


def _first_json_object(text: str) -> dict | None:
    # Prefer last JSON object (CLI may print logs then JSON)
    candidates: list[str] = []
    # Full-text JSON
    stripped = text.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        candidates.append(stripped)
    # Fenced or line-based objects
    for match in re.finditer(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", text, re.DOTALL):
        candidates.append(match.group(0))
    for raw in reversed(candidates):
        try:
            data = json.loads(raw)
            if isinstance(data, dict):
                return data
        except Exception:
            continue
    # Line-by-line
    for line in reversed(text.splitlines()):
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            data = json.loads(line)
            if isinstance(data, dict):
                return data
        except Exception:
            continue
    return None


def _usage_dict(
    runtime: str,
    input_tokens: int,
    output_tokens: int,
    cost_usd: float | None = None,
    model: str | None = None,
    estimated: bool = False,
) -> dict[str, Any]:
    total = input_tokens + output_tokens
    return {
        "runtime": runtime,
        "total_tokens": total,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost_usd": cost_usd,
        "model": model,
        "estimated": estimated,
    }


def _parse_claude_json(text: str, runtime: str) -> dict | None:
    data = _first_json_object(text)
    if not data:
        return _parse_text_regex(text, runtime)
    usage = data.get("usage") or data.get("token_usage") or {}
    if isinstance(usage, dict):
        inp = int(usage.get("input_tokens") or usage.get("input") or 0)
        out = int(usage.get("output_tokens") or usage.get("output") or 0)
        cost = usage.get("cost_usd") or data.get("total_cost_usd") or data.get("cost")
        model = data.get("model")
        if inp or out:
            return _usage_dict(
                runtime,
                inp,
                out,
                float(cost) if cost is not None else None,
                model=str(model) if model else None,
            )
    return _parse_text_regex(text, runtime)


def _parse_codex_jsonl(text: str, runtime: str) -> dict | None:
    usage_acc = {"input": 0, "output": 0, "cost": None, "model": None}
    found = False
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            event = json.loads(line)
        except Exception:
            continue
        if not isinstance(event, dict):
            continue
        # Common shapes
        token_usage = event.get("token_usage") or event.get("usage") or {}
        if isinstance(token_usage, dict) and (
            token_usage.get("input_tokens")
            or token_usage.get("output_tokens")
            or token_usage.get("input")
            or token_usage.get("output")
        ):
            found = True
            usage_acc["input"] = int(
                token_usage.get("input_tokens") or token_usage.get("input") or 0
            )
            usage_acc["output"] = int(
                token_usage.get("output_tokens") or token_usage.get("output") or 0
            )
            if token_usage.get("cost_usd") is not None:
                usage_acc["cost"] = float(token_usage["cost_usd"])
        if event.get("model"):
            usage_acc["model"] = event["model"]
        if event.get("type") == "result" and isinstance(event.get("usage"), dict):
            found = True
            u = event["usage"]
            usage_acc["input"] = int(u.get("input_tokens") or u.get("input") or 0)
            usage_acc["output"] = int(u.get("output_tokens") or u.get("output") or 0)
    if found:
        return _usage_dict(
            runtime,
            usage_acc["input"],
            usage_acc["output"],
            usage_acc["cost"],
            model=usage_acc["model"],
        )
    return _parse_claude_json(text, runtime) or _parse_text_regex(text, runtime)


def _parse_gemini_json(text: str, runtime: str) -> dict | None:
    data = _first_json_object(text)
    if not data:
        return _parse_text_regex(text, runtime)
    stats = data.get("stats") or data.get("usage") or data.get("token_usage") or {}
    if isinstance(stats, dict):
        inp = int(
            stats.get("promptTokenCount")
            or stats.get("prompt_tokens")
            or stats.get("input_tokens")
            or stats.get("input")
            or 0
        )
        out = int(
            stats.get("candidatesTokenCount")
            or stats.get("candidates_tokens")
            or stats.get("output_tokens")
            or stats.get("output")
            or 0
        )
        if inp or out:
            cost = stats.get("cost_usd") or data.get("cost")
            return _usage_dict(
                runtime,
                inp,
                out,
                float(cost) if cost is not None else None,
                model=str(data.get("model") or "") or None,
            )
    return _parse_text_regex(text, runtime)


def _parse_generic_json(text: str, runtime: str | None) -> dict | None:
    data = _first_json_object(text)
    if not data:
        return None
    usage = data.get("usage") or data.get("token_usage") or data
    if not isinstance(usage, dict):
        return None
    inp = int(usage.get("input_tokens") or usage.get("input") or 0)
    out = int(usage.get("output_tokens") or usage.get("output") or 0)
    if not (inp or out):
        return None
    cost = usage.get("cost_usd") or usage.get("cost")
    return _usage_dict(
        runtime or "unknown",
        inp,
        out,
        float(cost) if cost is not None else None,
        model=str(data.get("model") or "") or None,
    )


def _parse_text_regex(text: str, runtime: str | None) -> dict | None:
    """Legacy human-readable patterns (fallback only)."""
    claude_total_match = re.search(r"Total tokens:\s*([\d,]+)", text)
    if claude_total_match:
        try:
            total_tokens = int(claude_total_match.group(1).replace(",", ""))
            input_match = re.search(r"input:\s*([\d,]+)", text)
            output_match = re.search(r"output:\s*([\d,]+)", text)
            cost_match = re.search(r"Total cost:\s*\$([\d.]+)", text)
            input_tokens = int(input_match.group(1).replace(",", "")) if input_match else 0
            output_tokens = (
                int(output_match.group(1).replace(",", "")) if output_match else 0
            )
            if input_tokens == 0 and output_tokens == 0:
                input_tokens = total_tokens
            return _usage_dict(
                runtime or "claude",
                input_tokens,
                output_tokens,
                float(cost_match.group(1)) if cost_match else None,
            )
        except Exception:
            pass

    gemini_match = re.search(
        r"Gemini tokens:\s*([\d,]+)\s*\(prompt:\s*([\d,]+)\s*/\s*candidates:\s*([\d,]+)\)",
        text,
    )
    if gemini_match:
        try:
            prompt = int(gemini_match.group(2).replace(",", ""))
            candidates = int(gemini_match.group(3).replace(",", ""))
            cost_match = re.search(r"Cost:\s*\$([\d.]+)", text)
            return _usage_dict(
                runtime or "gemini",
                prompt,
                candidates,
                float(cost_match.group(1)) if cost_match else None,
            )
        except Exception:
            pass

    codex_match = re.search(
        r"Codex tokens:\s*([\d,]+)\s*\(input:\s*([\d,]+)\s*/\s*output:\s*([\d,]+)\)",
        text,
    )
    if codex_match:
        try:
            input_t = int(codex_match.group(2).replace(",", ""))
            output_t = int(codex_match.group(3).replace(",", ""))
            cost_match = re.search(r"Total cost:\s*\$([\d.]+)", text)
            return _usage_dict(
                runtime or "codex",
                input_t,
                output_t,
                float(cost_match.group(1)) if cost_match else None,
            )
        except Exception:
            pass

    return None


def detect_exhaustion(output_text: str, patterns: list[str] | None = None) -> bool:
    text = (output_text or "").lower()
    patterns = patterns or []
    return any(p.lower() in text for p in patterns)


def run_runtime(
    runtime_name: str,
    *,
    prompt_text: str | None = None,
    prompt_file: str | Path | None = None,
    cwd: Path | str | None = None,
    model: str | None = None,
    tier: str | None = None,
    mode: str = "exec",
    timeout: int | None = None,
    repo_root: Path | None = None,
    log_path: Path | None = None,
    include_sandbox: bool = True,
) -> RuntimeRunResult:
    """Invoke a runtime and return structured result + parsed usage."""
    inv = build_runtime_invocation(
        runtime_name,
        prompt_text=prompt_text,
        prompt_file=prompt_file,
        model=model,
        tier=tier,
        mode=mode,
        repo_root=repo_root,
        include_sandbox=include_sandbox,
    )
    spec = inv.spec
    assert spec is not None
    timeout = timeout or spec.default_timeout_seconds
    work_dir = Path(cwd) if cwd else Path.cwd()

    binary = inv.argv[0]
    if not shutil.which(binary) and not Path(binary).exists():
        return RuntimeRunResult(
            success=False,
            returncode=127,
            stdout="",
            stderr=f"Runtime binary not found: {spec.binary}",
            argv=inv.argv,
            error=f"binary_missing:{spec.binary}",
        )

    def _as_text(value: Any) -> str:
        """Coerce subprocess output to str (unit tests often return MagicMock)."""
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        if isinstance(value, (bytes, bytearray)):
            try:
                return value.decode("utf-8", errors="replace")
            except Exception:
                return ""
        return ""

    try:
        completed = subprocess.run(
            inv.argv,
            cwd=str(work_dir),
            input=inv.stdin_data,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=inv.env,
        )
        stdout = _as_text(getattr(completed, "stdout", None))
        stderr = _as_text(getattr(completed, "stderr", None))
        combined = stdout + "\n" + stderr
        if log_path is not None:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            log_path.write_text(combined, encoding="utf-8")

        usage = parse_usage_from_output(combined, parser=spec.usage_parser, runtime=spec.name)
        exhausted = detect_exhaustion(combined, spec.exhaustion_patterns)
        try:
            returncode = int(getattr(completed, "returncode", 1) or 0)
        except (TypeError, ValueError):
            returncode = 1
        return RuntimeRunResult(
            success=returncode == 0,
            returncode=returncode,
            stdout=stdout,
            stderr=stderr,
            usage=usage,
            exhaustion_detected=exhausted,
            argv=inv.argv,
        )
    except subprocess.TimeoutExpired as e:
        out = (e.stdout or "") if isinstance(e.stdout, str) else ""
        err = (e.stderr or "") if isinstance(e.stderr, str) else "timeout"
        if log_path is not None:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            log_path.write_text(out + "\n" + err, encoding="utf-8")
        return RuntimeRunResult(
            success=False,
            returncode=124,
            stdout=out,
            stderr=err,
            argv=inv.argv,
            error="timeout",
        )
    except subprocess.CalledProcessError as e:
        # Some tests/mocks raise CalledProcessError; still surface log content.
        out = (e.stdout or "") if isinstance(getattr(e, "stdout", None), str) else ""
        err = (e.stderr or "") if isinstance(getattr(e, "stderr", None), str) else str(e)
        if log_path is not None and log_path.exists():
            try:
                combined = log_path.read_text(encoding="utf-8")
            except Exception:
                combined = out + "\n" + err
        else:
            combined = out + "\n" + err
            if log_path is not None:
                log_path.parent.mkdir(parents=True, exist_ok=True)
                log_path.write_text(combined, encoding="utf-8")
        exhausted = detect_exhaustion(combined, spec.exhaustion_patterns)
        return RuntimeRunResult(
            success=False,
            returncode=int(getattr(e, "returncode", 1) or 1),
            stdout=out,
            stderr=err,
            exhaustion_detected=exhausted,
            argv=inv.argv,
            error=str(e),
        )
    except Exception as e:
        combined = ""
        if log_path is not None and log_path.exists():
            try:
                combined = log_path.read_text(encoding="utf-8")
            except Exception:
                combined = ""
        exhausted = detect_exhaustion(combined, spec.exhaustion_patterns if spec else None)
        return RuntimeRunResult(
            success=False,
            returncode=1,
            stdout="",
            stderr=str(e),
            exhaustion_detected=exhausted,
            argv=inv.argv,
            error=str(e),
        )
