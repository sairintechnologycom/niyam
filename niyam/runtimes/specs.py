"""Declarative runtime execution specs for coding-agent CLIs."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


PromptDelivery = Literal["stdin", "argv", "file-flag"]
OutputFormat = Literal["json", "jsonl", "text"]


class RuntimeSpec(BaseModel):
    """How Niyam invokes a coding-agent CLI for plan/exec work.

    Projection (CLAUDE.md / AGENTS.md generation) remains separate in
    ``niyam.runtimes.{claude,codex,gemini,agy}`` adapters. This model only
    describes *execution* against the real vendor grammar.
    """

    name: str
    binary: str
    prompt_delivery: PromptDelivery = "stdin"
    # Arg templates may use {prompt}, {prompt_file}, {model}
    exec_args: list[str] = Field(default_factory=list)
    plan_args: list[str] = Field(default_factory=list)
    model_flag: Optional[str] = None
    models: dict[str, str] = Field(default_factory=dict)
    sandbox_args: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)
    output_format: OutputFormat = "text"
    usage_parser: str = "text_regex"
    exhaustion_patterns: list[str] = Field(
        default_factory=lambda: [
            "rate limit",
            "limit exceeded",
            "quota exceeded",
            "insufficient funds",
            "insufficient credit",
            "exhausted",
            "out of tokens",
            "token limit",
            "overloaded",
        ]
    )
    capabilities: list[str] = Field(default_factory=list)
    default_timeout_seconds: int = 600
    # When True, missing binary is a hard error rather than silent skip
    required: bool = False

    def resolve_model(self, tier: str | None = None, model: str | None = None) -> str | None:
        if model:
            return model
        if tier and tier in self.models:
            return self.models[tier]
        return self.models.get("standard") or self.models.get("default")


# Built-in specs use real-ish vendor CLI grammars (not Claude-only assumptions).
BUILTIN_RUNTIME_SPECS: dict[str, RuntimeSpec] = {
    "claude": RuntimeSpec(
        name="claude",
        binary="claude",
        # Prompt content is substituted into -p (file contents loaded by executor).
        prompt_delivery="argv",
        exec_args=[
            "-p",
            "{prompt}",
            "--output-format",
            "json",
            "--permission-mode",
            "acceptEdits",
        ],
        plan_args=[
            "-p",
            "{prompt}",
            "--output-format",
            "json",
        ],
        model_flag="--model",
        models={
            "premium": "claude-opus",
            "standard": "claude-sonnet",
            "economy": "claude-haiku",
        },
        output_format="json",
        usage_parser="claude_json",
        capabilities=["planning", "implementation", "review", "hooks"],
    ),
    "codex": RuntimeSpec(
        name="codex",
        binary="codex",
        # Non-interactive: codex exec with prompt on stdin ("-")
        prompt_delivery="stdin",
        exec_args=["exec", "--json", "-"],
        plan_args=["exec", "--json", "-"],
        model_flag="--model",
        models={
            "premium": "o3",
            "standard": "gpt-5-codex",
            "economy": "gpt-4.1-mini",
        },
        sandbox_args=["--sandbox", "workspace-write"],
        output_format="jsonl",
        usage_parser="codex_jsonl",
        capabilities=["implementation", "repair"],
    ),
    "gemini": RuntimeSpec(
        name="gemini",
        binary="gemini",
        prompt_delivery="argv",
        exec_args=["-p", "{prompt}", "-o", "json"],
        plan_args=["-p", "{prompt}", "-o", "json"],
        model_flag="-m",
        models={
            "premium": "gemini-2.5-pro",
            "standard": "gemini-2.5-flash",
            "economy": "gemini-2.0-flash",
        },
        output_format="json",
        usage_parser="gemini_json",
        capabilities=["review", "validation", "implementation"],
    ),
    "agy": RuntimeSpec(
        name="agy",
        binary="agy",
        prompt_delivery="argv",
        exec_args=["--print", "{prompt}"],
        plan_args=["--mode", "plan", "--print", "{prompt}"],
        model_flag="--model",
        output_format="text",
        capabilities=["planning", "implementation", "review"],
    ),
}


def runtime_spec_from_dict(data: dict[str, Any]) -> RuntimeSpec:
    """Build a RuntimeSpec from a user config mapping."""
    return RuntimeSpec.model_validate(data)
