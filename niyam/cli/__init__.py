"""Niyam CLI package initialization."""

# ruff: noqa: E402

from __future__ import annotations

import builtins
import typing
import typer

builtins.Annotated = typing.Annotated
builtins.Optional = typing.Optional
builtins.typer = typer

import logging
from rich.console import Console

class NiyamTyper(typer.Typer):
    def __call__(self, *args, **kwargs):
        from niyam.core.errors import NiyamError
        try:
            super().__call__(*args, **kwargs)
        except NiyamError as e:
            console.print(f"[bold red]Error:[/] {e}")
            raise SystemExit(e.code)

app = NiyamTyper(
    name="niyam",
    help="Governed autonomous development for AI coding agents.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)
console = Console()

def deprecated_sutra() -> None:
    """Print deprecation warning for legacy sutra command."""
    console.print("[yellow]Sutra has been renamed to Niyam.[/]\n")
    console.print("Use:")
    console.print("  [cyan]niyam <command>[/]\n")
    console.print("Migration:")
    console.print("  [cyan]niyam migrate --from-sutra[/]\n")
    console.print("The deprecated `sutra` command will be removed in a future release.")
    raise SystemExit(0)

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
    """Niyam global callback to handle logging configurations."""
    if verbose:
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s %(name)s %(levelname)s %(message)s",
        )
    else:
        logging.basicConfig(level=logging.WARNING)


def main() -> None:
    """CLI entry point catching NiyamError exceptions."""
    from niyam.core.errors import NiyamError

    try:
        app()
    except NiyamError as e:
        console.print(f"[bold red]Error:[/] {e}")
        raise SystemExit(e.code)


# Import subcommand modules to register their commands on the Typer instances
from niyam.cli import main_cmds  # noqa: F401
from niyam.cli import context  # noqa: F401
from niyam.cli import guard  # noqa: F401
from niyam.cli import runtime  # noqa: F401
from niyam.cli import policy  # noqa: F401
from niyam.cli import pack  # noqa: F401
from niyam.cli import memory  # noqa: F401
from niyam.cli import mission  # noqa: F401
from niyam.cli import review  # noqa: F401
from niyam.cli import pr  # noqa: F401
from niyam.cli import ci  # noqa: F401
from niyam.cli import scan  # noqa: F401

