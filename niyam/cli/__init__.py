"""Niyam CLI package initialization."""

# ruff: noqa: E402

from __future__ import annotations

import typer


import logging
import sys
from difflib import get_close_matches
from rich.console import Console


class NiyamTyper(typer.Typer):
    def __call__(self, *args, **kwargs):
        from niyam.core.errors import NiyamError

        _print_command_suggestion(self)
        try:
            super().__call__(*args, **kwargs)
        except NiyamError as e:
            console.print(f"[bold red]Error:[/] {e}")
            raise SystemExit(e.code)


def _print_command_suggestion(cli: typer.Typer) -> None:
    """Print a best-effort suggestion for mistyped top-level commands."""
    if len(sys.argv) < 2:
        return
    command = sys.argv[1]
    if command.startswith("-"):
        return

    known = [
        cmd.name
        if isinstance(cmd.name, str)
        else cmd.callback.__name__.replace("_", "-")
        for cmd in cli.registered_commands
        if cmd.callback is not None
    ]
    known.extend(
        group.name
        if isinstance(group.name, str)
        else group.typer_instance.info.name
        for group in cli.registered_groups
        if isinstance(group.name, str)
        or isinstance(group.typer_instance.info.name, str)
    )
    known = [name for name in known if isinstance(name, str)]
    if command in known:
        return

    matches = get_close_matches(command, known, n=1, cutoff=0.68)
    if matches:
        console.print(f"[yellow]Unknown command '{command}'. Did you mean '{matches[0]}'?[/]")


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

mcp_app = typer.Typer(
    name="mcp",
    help="Manage AI agent tools and MCP servers.",
    no_args_is_help=True,
)
app.add_typer(mcp_app)

rules_app = typer.Typer(
    name="rules",
    help="Manage scan and governance rules.",
    no_args_is_help=True,
)
app.add_typer(rules_app)

skills_app = typer.Typer(
    name="skills",
    help="Manage and govern AI agent skills.",
    no_args_is_help=True,
)
app.add_typer(skills_app)

policy_app = typer.Typer(
    name="policy",
    help="Manage enterprise governance policies and risk acceptance.",
    no_args_is_help=True,
)
app.add_typer(policy_app)

cost_app = typer.Typer(
    name="cost",
    help="Track AI engineering token usage and costs.",
    no_args_is_help=True,
)
app.add_typer(cost_app)

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

evidence_app = typer.Typer(
    name="evidence",
    help="Audit-ready evidence and readiness report generation.",
    no_args_is_help=True,
)
# Note: we do NOT add_typer(evidence_app) here to avoid collision with top-level 'evidence' command.
# evidence.py will handle its own registration.

identity_app = typer.Typer(
    name="identity",
    help="Manage local cryptographic identities for signing reports.",
    no_args_is_help=True,
)
app.add_typer(identity_app)

saas_app = typer.Typer(
    name="saas",
    help="Interact with the Niyam Dashboard (SaaS) control plane.",
    no_args_is_help=True,
)
app.add_typer(saas_app)

fleet_app = typer.Typer(
    name="fleet",
    help="Manage AI missions across multiple repositories.",
    no_args_is_help=True,
)
app.add_typer(fleet_app)

swarm_app = typer.Typer(
    name="swarm",
    help="Coordinate multiple AI agents in a shared workspace.",
    no_args_is_help=True,
)
app.add_typer(swarm_app)

workspace_app = typer.Typer(
    name="workspace",
    help="Manage supervised Control Room task sessions.",
    no_args_is_help=True,
)
app.add_typer(workspace_app)


@app.callback()
def main_callback(
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output",
    ),
    json_logs: bool = typer.Option(
        False,
        "--json-logs",
        help="Emit structured JSON logs.",
    ),
) -> None:
    """Niyam global callback to handle logging configurations."""
    from niyam.core.utils import configure_logging

    configure_logging(
        json_logs=json_logs,
        level=logging.DEBUG if verbose else logging.WARNING,
    )


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
from niyam.cli import mcp  # noqa: F401
from niyam.cli import cost  # noqa: F401
from niyam.cli import runtime  # noqa: F401
from niyam.cli import policy  # noqa: F401
from niyam.cli import pack  # noqa: F401
from niyam.cli import memory  # noqa: F401
from niyam.cli import mission  # noqa: F401
from niyam.cli import review  # noqa: F401
from niyam.cli import pr  # noqa: F401
from niyam.cli import ci  # noqa: F401
from niyam.cli import scan  # noqa: F401
from niyam.cli import rules  # noqa: F401
from niyam.cli import skills  # noqa: F401
from niyam.cli import policy  # noqa: F401
from niyam.cli import evidence  # noqa: F401
from niyam.cli import identity  # noqa: F401
from niyam.cli import saas  # noqa: F401
from niyam.cli import fleet  # noqa: F401
from niyam.cli import swarm  # noqa: F401
from niyam.cli import workspace  # noqa: F401


def _harden_typer_parsing() -> None:
    """
    Monkeypatch Typer's internal command execution to support flexible boolean flags.
    Allows passing --approved and --requires-approval as either standalone flags
    or with explicit true/false values.
    """
    import sys
    import typer.core

    original_command_main = typer.core.TyperCommand.main

    def normalize_args(args):
        normalized = []
        i = 0
        while i < len(args):
            arg = args[i]
            if arg == "--no-approved":
                normalized.append("--approved")
                normalized.append("false")
            elif arg == "--no-requires-approval":
                normalized.append("--requires-approval")
                normalized.append("false")
            else:
                normalized.append(arg)
                if arg in ("--approved", "--requires-approval"):
                    if i + 1 >= len(args) or args[i + 1].startswith("-"):
                        normalized.append("true")
            i += 1
        return normalized

    def custom_command_main(self, args=None, *args_rest, **kwargs):
        if args is None:
            args = normalize_args(sys.argv[1:])
        else:
            args = normalize_args(list(args))
        return original_command_main(self, args=args, *args_rest, **kwargs)

    typer.core.TyperCommand.main = custom_command_main

    original_group_main = typer.core.TyperGroup.main

    def custom_group_main(self, args=None, *args_rest, **kwargs):
        if args is None:
            args = normalize_args(sys.argv[1:])
        else:
            args = normalize_args(list(args))
        return original_group_main(self, args=args, *args_rest, **kwargs)

    typer.core.TyperGroup.main = custom_group_main


# Apply the hardening
_harden_typer_parsing()
