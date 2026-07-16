"""CLI commands for read-only enterprise discovery."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Annotated, Optional

import typer

from niyam.cli import console, discovery_app
from niyam.core.config import find_niyam_root
from niyam.core.source_discovery import (
    discover_source_repositories,
    register_discovered_applications,
    save_source_discovery,
)
from niyam.core.runtime_discovery import (
    discover_runtime_assets,
    register_runtime_assets,
    save_runtime_discovery,
)


TOKEN_ENV = {
    "github": "GITHUB_TOKEN",
    "gitlab": "GITLAB_TOKEN",
    "azure-devops": "AZURE_DEVOPS_TOKEN",
}


@discovery_app.command("source")
def discovery_source(
    provider: Annotated[
        str, typer.Option("--provider", help="github, gitlab, or azure-devops.")
    ],
    organization: Annotated[
        str, typer.Option("--organization", help="Organization or group name.")
    ],
    project: Annotated[
        Optional[str], typer.Option("--project", help="Azure DevOps project.")
    ] = None,
    base_url: Annotated[
        Optional[str],
        typer.Option("--base-url", help="Self-hosted provider API base URL."),
    ] = None,
    token_env: Annotated[
        Optional[str],
        typer.Option(
            "--token-env", help="Environment variable containing a read token."
        ),
    ] = None,
    max_pages: Annotated[
        int, typer.Option("--max-pages", help="Maximum pages to request.")
    ] = 10,
    register_all: Annotated[
        bool,
        typer.Option(
            "--register-all", help="Register every repository, not only AI candidates."
        ),
    ] = False,
) -> None:
    """Discover repository metadata without modifying the provider."""
    root = find_niyam_root() or Path.cwd()
    token = os.environ.get(token_env or TOKEN_ENV.get(provider, "")) or None
    try:
        result = discover_source_repositories(
            provider,
            organization,
            project=project,
            token=token,
            base_url=base_url,
            max_pages=max_pages,
        )
        artifact = save_source_discovery(result, root)
        registered = register_discovered_applications(
            result, root, register_all=register_all
        )
    except Exception as exc:
        console.print(f"[bold red]Error:[/] Source discovery failed: {exc}")
        raise typer.Exit(1)
    console.print(
        f"[bold green]✓[/] Discovered {len(result.repositories)} repositories; "
        f"registered {len(registered)} AI Applications."
    )
    console.print(f"  [dim]Evidence:[/] {artifact}")


@discovery_app.command("runtime")
def discovery_runtime(
    provider: Annotated[
        str, typer.Option("--provider", help="aws, azure, gcp, or kubernetes.")
    ],
    application: Annotated[
        Optional[str],
        typer.Option("--application", help="Registered AI Application ID to link."),
    ] = None,
    region: Annotated[
        Optional[str], typer.Option("--region", help="AWS or GCP region.")
    ] = None,
    project: Annotated[
        Optional[str], typer.Option("--project", help="GCP project.")
    ] = None,
    resource_group: Annotated[
        Optional[str],
        typer.Option("--resource-group", help="Azure resource group."),
    ] = None,
    workspace: Annotated[
        Optional[str], typer.Option("--workspace", help="Azure ML workspace.")
    ] = None,
    subscription: Annotated[
        Optional[str], typer.Option("--subscription", help="Azure subscription.")
    ] = None,
    context: Annotated[
        Optional[str], typer.Option("--context", help="Kubernetes context.")
    ] = None,
) -> None:
    """Discover cloud or Kubernetes AI runtime metadata using fixed list commands."""
    root = find_niyam_root() or Path.cwd()
    try:
        result = discover_runtime_assets(
            provider,
            region=region,
            project=project,
            resource_group=resource_group,
            workspace=workspace,
            subscription=subscription,
            context=context,
        )
        artifact = save_runtime_discovery(result, root)
        linked = (
            register_runtime_assets(result, application, root) if application else 0
        )
    except Exception as exc:
        console.print(f"[bold red]Error:[/] Runtime discovery failed: {exc}")
        raise typer.Exit(1)
    console.print(
        f"[bold green]✓[/] Discovered {len(result.assets)} runtime assets; "
        f"linked {linked} to Applications."
    )
    if result.errors:
        console.print(f"[yellow]Partial failures:[/] {len(result.errors)}")
        for error in result.errors:
            console.print(f"  - {error}")
    console.print(f"  [dim]Evidence:[/] {artifact}")
