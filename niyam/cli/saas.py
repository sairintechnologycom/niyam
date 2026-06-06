"""Niyam CLI SaaS commands."""

from __future__ import annotations

import json
from pathlib import Path
import typer
from rich.panel import Panel

from niyam.cli import console, saas_app
from niyam.core.config import load_niyam_config, save_niyam_config
from niyam.core.saas import SaaSClient


@saas_app.command("config")
def saas_config(
    api_key: str = typer.Option(None, "--api-key", help="API key for Niyam Dashboard."),
    project_id: str = typer.Option(None, "--project-id", help="Target project ID."),
    base_url: str = typer.Option(None, "--url", help="Override Dashboard base URL."),
    enable: bool = typer.Option(None, "--enable/--disable", help="Enable or disable SaaS integration."),
) -> None:
    """Configure SaaS Dashboard integration."""
    config = load_niyam_config()
    
    if enable is not None:
        config.saas.enabled = enable
    if api_key:
        config.saas.api_key = api_key
    if project_id:
        config.saas.project_id = project_id
    if base_url:
        config.saas.base_url = base_url
        
    save_niyam_config(config)
    
    status = "[bold green]Enabled[/]" if config.saas.enabled else "[bold red]Disabled[/]"
    console.print(f"SaaS Integration Status: {status}")
    console.print(f"Base URL: {config.saas.base_url}")
    console.print(f"Project ID: {config.saas.project_id or 'Not set'}")
    if config.saas.api_key:
        console.print(f"API Key: sha256:{config.saas.api_key[:8]}...")
    else:
        console.print("API Key: Not set")


@saas_app.command("upload")
def saas_upload(
    report_path: str = typer.Argument(..., help="Path to evidence.json to upload."),
) -> None:
    """Upload a specific evidence report to the dashboard."""
    path = Path(report_path)
    if not path.exists():
        console.print(f"[bold red]Error:[/] File not found: {report_path}")
        raise SystemExit(1)
        
    try:
        with open(path, encoding="utf-8") as f:
            report_data = json.load(f)
    except Exception as e:
        console.print(f"[bold red]Error:[/] Failed to parse JSON: {e}")
        raise SystemExit(1)
        
    client = SaaSClient()
    console.print(f"[cyan]Uploading report to dashboard...[/]")
    try:
        result = client.upload_report(report_data)
        console.print(f"[bold green]✓[/] Report uploaded successfully.")
        if "url" in result:
            console.print(f"  - [dim]View at:[/] {result['url']}")
    except Exception as e:
        console.print(f"[bold red]Upload failed:[/] {e}")
        raise SystemExit(1)
