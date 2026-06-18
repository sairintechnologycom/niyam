import typer
import os
import sys
from niyam.suggestions.shell import generate_completion_script, install_completion_script
from rich.console import Console

console = Console()
completion_app = typer.Typer(name="completion", help="Shell completion tools.")

@completion_app.command(name="script")
def script(
    shell: str = typer.Option(
        None,
        "--shell",
        help="Target shell (bash, zsh, fish, powershell)."
    )
):
    """Print completion script for a given shell."""
    if not shell:
        shell = os.environ.get("SHELL", "bash").split("/")[-1]
    
    script_content = generate_completion_script(shell)
    sys.stdout.write(script_content)

@completion_app.command(name="install")
def install(
    shell: str = typer.Option(
        None,
        "--shell",
        help="Target shell (bash, zsh, fish, powershell)."
    )
):
    """Install completion script for a given shell."""
    if not shell:
        shell = os.environ.get("SHELL", "bash").split("/")[-1]
        
    try:
        install_completion_script(shell)
        console.print(f"[bold green]PASS:[/] Completion installed for {shell}.")
        console.print("Please restart your shell or source your rc file for changes to take effect.")
    except Exception as e:
        console.print(f"[bold red]FAIL:[/] Could not install completion: {e}")
        raise typer.Exit(1)

