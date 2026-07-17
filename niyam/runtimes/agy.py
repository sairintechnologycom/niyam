"""Antigravity CLI runtime adapter."""

from rich.console import Console

from niyam.runtimes.codex import CodexAdapter


class AgyAdapter(CodexAdapter):
    """Project Niyam instructions to AGENTS.md for the ``agy`` CLI."""

    @property
    def name(self) -> str:
        return "agy"

    def sync(self, console: Console) -> None:
        self._generate_agents_md(console)
        console.print("[green]✓[/] Antigravity CLI runtime synced")

    def clean(self, console: Console) -> None:
        # AGENTS.md may also be shared with Codex, so this adapter never removes it.
        console.print("[yellow]AGENTS.md retained because it may be shared with Codex[/]")
