import typer
from rich.console import Console
from niyam.suggestions.registry import registry
from niyam.suggestions.engine import SuggestionEngine

console = Console()
suggest_app = typer.Typer(name="suggest", help="Suggest completions based on partial input.", hidden=True)

@suggest_app.callback(invoke_without_command=True)
def suggest(
    partial_command: str = typer.Argument(..., help="Partial command string")
):
    engine = SuggestionEngine(registry)
    suggestions = engine.suggest(partial_command)
    for s in suggestions:
        print(s)

