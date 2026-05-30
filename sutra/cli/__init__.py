"""Sutra CLI package initialization."""

# ruff: noqa: E402

from __future__ import annotations

import logging
import typer
from rich.console import Console

app = typer.Typer(
    name="sutra",
    help="Governed AI-development workspaces for Claude Code, Codex CLI, and future coding runtimes.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)
console = Console()

# Subcommand groups
context_app = typer.Typer(
    name="context",
    help="Manage project context for AI agents.",
    no_args_is_help=True,
)
app.add_typer(context_app)

guard_app = typer.Typer(
    name="guard",
    help="Safety guardrails for AI-assisted development.",
    no_args_is_help=True,
)
app.add_typer(guard_app)

runtime_app = typer.Typer(
    name="runtime",
    help="Manage AI runtime adapters.",
    no_args_is_help=True,
)
app.add_typer(runtime_app)

policy_app = typer.Typer(
    name="policy",
    help="Policy management and validation.",
    no_args_is_help=True,
)
app.add_typer(policy_app)

pack_app = typer.Typer(
    name="pack",
    help="Manage modular pack bundles.",
    no_args_is_help=True,
)
app.add_typer(pack_app)

memory_app = typer.Typer(
    name="memory",
    help="Manage project memory and context.",
    no_args_is_help=True,
)
app.add_typer(memory_app)

mission_app = typer.Typer(
    name="mission",
    help="Manage the single-agent mission lifecycle.",
    no_args_is_help=True,
)
app.add_typer(mission_app)

review_app = typer.Typer(
    name="review",
    help="Run structured reviews on code or pull requests.",
    no_args_is_help=False,
)
app.add_typer(review_app)

pr_app = typer.Typer(
    name="pr",
    help="Manage pull requests with evidence reports.",
    no_args_is_help=True,
)
app.add_typer(pr_app)

ci_app = typer.Typer(
    name="ci",
    help="CI/CD environment verification checks.",
    no_args_is_help=True,
)
app.add_typer(ci_app)


@app.callback()
def main_callback(
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output",
    ),
) -> None:
    """Sutra global callback to handle logging configurations."""
    if verbose:
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s %(name)s %(levelname)s %(message)s",
        )
    else:
        logging.basicConfig(level=logging.WARNING)


def main() -> None:
    """CLI entry point catching SutraError exceptions."""
    from sutra.core.errors import SutraError

    try:
        app()
    except SutraError as e:
        console.print(f"[bold red]Error:[/] {e}")
        raise SystemExit(e.code)


# Import subcommand modules to register their commands on the Typer instances
from sutra.cli import main_cmds  # noqa: F401
from sutra.cli import context  # noqa: F401
from sutra.cli import guard  # noqa: F401
from sutra.cli import runtime  # noqa: F401
from sutra.cli import policy  # noqa: F401
from sutra.cli import pack  # noqa: F401
from sutra.cli import memory  # noqa: F401
from sutra.cli import mission  # noqa: F401
from sutra.cli import review  # noqa: F401
from sutra.cli import pr  # noqa: F401
from sutra.cli import ci  # noqa: F401
