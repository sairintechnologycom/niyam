"""Niyam CLI fleet commands."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional
import typer
from rich.table import Table
from rich.panel import Panel

from niyam.cli import console, fleet_app
from niyam.core.fleet import (
    load_fleet_config,
    register_repo,
    discover_repos,
    sync_fleet_policies,
    dispatch_fleet_mission,
    FleetRepo
)
from niyam.core.config import find_niyam_root, get_niyam_dir
from niyam.mission.utils import load_plan


@fleet_app.command("register")
def fleet_register(
    path: Path = typer.Argument(..., help="Path to the Niyam workspace to register."),
    alias: Optional[str] = typer.Option(None, "--alias", "-a", help="Alias for the repository."),
    tags: Optional[str] = typer.Option(None, "--tags", "-t", help="Comma-separated list of tags."),
    depends_on: Optional[str] = typer.Option(None, "--depends-on", "-d", help="Comma-separated list of repo aliases this repo depends on."),
) -> None:
    """Register a Niyam workspace in the fleet."""
    if not path.exists():
        console.print(f"[bold red]Error:[/] Path not found: {path}")
        raise typer.Exit(1)
        
    niyam_root = find_niyam_root(path)
    if not niyam_root:
        console.print(f"[bold red]Error:[/] No Niyam workspace found at or above {path}")
        raise typer.Exit(1)
        
    tag_list = [t.strip() for t in tags.split(",")] if tags else None
    dep_list = [d.strip() for d in depends_on.split(",")] if depends_on else None
    repo = register_repo(niyam_root, alias=alias, tags=tag_list, depends_on=dep_list)
    
    console.print(f"[bold green]✓[/] Registered repository: [bold cyan]{repo.alias}[/]")
    console.print(f"  [dim]Path:[/] {repo.path}")
    if repo.tags:
        console.print(f"  [dim]Tags:[/] {', '.join(repo.tags)}")
    if repo.depends_on:
        console.print(f"  [dim]Depends On:[/] {', '.join(repo.depends_on)}")


@fleet_app.command("discover")
def fleet_discover(
    path: Path = typer.Argument(..., help="Root path to start discovery from."),
    depth: int = typer.Option(3, "--depth", "-d", help="Maximum depth to search."),
) -> None:
    """Discover and register all Niyam workspaces in a directory tree."""
    if not path.exists():
        console.print(f"[bold red]Error:[/] Path not found: {path}")
        raise typer.Exit(1)
        
    console.print(f"[cyan]Discovering Niyam workspaces in {path}...[/]")
    repos = discover_repos(path, max_depth=depth)
    
    if not repos:
        console.print("[yellow]No new Niyam workspaces discovered.[/]")
        return
        
    console.print(f"[bold green]✓[/] Discovered and registered {len(repos)} repositories:")
    for repo in repos:
        console.print(f"  - [bold cyan]{repo.alias}[/] ({repo.path})")


@fleet_app.command("list")
def fleet_list() -> None:
    """List all registered repositories in the fleet."""
    config = load_fleet_config()
    
    if not config.repos:
        console.print("[yellow]No repositories registered in the fleet.[/]")
        console.print("Run [bold]niyam fleet register <path>[/] to add one.")
        return
        
    table = Table(title="Niyam Fleet Repositories")
    table.add_column("Alias", style="bold cyan")
    table.add_column("Path", style="dim")
    table.add_column("Tags", style="green")
    table.add_column("Depends On", style="yellow")
    
    for repo in config.repos:
        table.add_row(repo.alias, repo.path, ", ".join(repo.tags), ", ".join(repo.depends_on))
        
    console.print(table)


@fleet_app.command("status")
def fleet_status() -> None:
    """Show the current status of all repositories in the fleet with evidence rollup."""
    import json
    config = load_fleet_config()
    
    if not config.repos:
        console.print("[yellow]No repositories registered in the fleet.[/]")
        return
        
    table = Table(title="Niyam Fleet Status")
    table.add_column("Repository", style="bold cyan")
    table.add_column("Mission", style="magenta", overflow="fold")
    table.add_column("Readiness", justify="center")
    table.add_column("Risks (C/H)", justify="center")
    table.add_column("Status", style="bold")
    table.add_column("Progress", style="dim")
    
    total_score = 0
    scored_repos = 0
    total_critical = 0
    total_high = 0
    
    for repo in config.repos:
        repo_path = Path(repo.path)
        niyam_dir = get_niyam_dir(repo_path)
        runs_dir = niyam_dir / "runs"
        
        latest_mission = "None"
        status = "[dim]No mission[/]"
        progress = "0/0"
        readiness = "[dim]N/A[/]"
        risks = "[dim]0 / 0[/]"
        
        # 1. Try to load latest scan report for readiness score
        scan_report_path = niyam_dir / "reports" / "scan.json"
        if not scan_report_path.exists():
             scan_report_path = niyam_dir / "scan-report.json"
             
        if scan_report_path.exists():
            try:
                with open(scan_report_path, "r", encoding="utf-8") as f:
                    report = json.load(f)
                    score = report.get("score", report.get("readiness_score", 0))
                    
                    score_color = "green" if score >= 80 else "yellow" if score >= 60 else "red"
                    readiness = f"[{score_color}]{score}[/]"
                    
                    total_score += score
                    scored_repos += 1
                    
                    findings = report.get("findings", [])
                    crit = sum(1 for f in findings if f.get("severity") == "critical")
                    high = sum(1 for f in findings if f.get("severity") == "high")
                    
                    total_critical += crit
                    total_high += high
                    
                    risks = f"[bold red]{crit}[/] / [red]{high}[/]"
            except Exception:
                readiness = "[red]Error[/]"

        # 2. Mission status
        if runs_dir.exists():
            # Get latest mission directory by modification time
            mission_dirs = [d for d in runs_dir.iterdir() if d.is_dir()]
            if mission_dirs:
                latest_dir = max(mission_dirs, key=lambda d: d.stat().st_mtime)
                latest_mission = latest_dir.name
                
                try:
                    plan = load_plan(latest_dir)
                    mission_status = plan.get("mission", {}).get("status", "unknown")
                    
                    status_colors = {
                        "planned": "cyan",
                        "approved": "magenta",
                        "running": "yellow",
                        "completed": "green",
                        "failed": "red",
                    }
                    color = status_colors.get(mission_status, "white")
                    status = f"[{color}]{mission_status.upper()}[/]"
                    
                    tasks = plan.get("tasks", [])
                    completed = sum(1 for t in tasks if t.get("status") == "completed")
                    progress = f"{completed}/{len(tasks)}"
                except Exception:
                    status = "[red]Error loading plan[/]"
        
        table.add_row(repo.alias, latest_mission, readiness, risks, status, progress)
        
    console.print(table)
    
    # Fleet Summary Panel
    if scored_repos > 0:
        avg_score = total_score / scored_repos
        avg_color = "green" if avg_score >= 80 else "yellow" if avg_score >= 60 else "red"
        
        summary_content = (
            f"Average Readiness Score: [{avg_color}]{avg_score:.1f}[/]\n"
            f"Total Fleet Critical Risks: [bold red]{total_critical}[/]\n"
            f"Total Fleet High Risks: [red]{total_high}[/]"
        )
        console.print(Panel(summary_content, title="[bold]Fleet Health Summary[/]", border_style="cyan"))


@fleet_app.command("sync")
def fleet_sync(
    source: str = typer.Option(..., "--source", "-s", help="Alias of the source repository."),
    tags: Optional[str] = typer.Option(None, "--tags", "-t", help="Only sync to repos with these tags."),
) -> None:
    """Sync governance policies from a source repository to the fleet."""
    config = load_fleet_config()
    
    source_repo = next((r for r in config.repos if r.alias == source), None)
    if not source_repo:
        console.print(f"[bold red]Error:[/] Source repository alias '{source}' not found in fleet.")
        raise typer.Exit(1)
        
    target_tags = [t.strip() for t in tags.split(",")] if tags else []
    
    targets = []
    for repo in config.repos:
        if repo.alias == source:
            continue
        if not target_tags or any(tag in repo.tags for tag in target_tags):
            targets.append(repo)
            
    if not targets:
        console.print("[yellow]No target repositories found to sync with.[/]")
        return
        
    console.print(f"[cyan]Syncing policies from {source} to {len(targets)} repositories...[/]")
    synced = sync_fleet_policies(source_repo, targets)
    
    if synced:
        console.print(f"[bold green]✓[/] Successfully synced policies to: {', '.join(synced)}")
    else:
        console.print("[yellow]No policies were synced.[/]")


@fleet_app.command("run")
def fleet_run(
    requirement: str = typer.Argument(..., help="Mission requirement text or file."),
    repos: str = typer.Option(None, "--repos", "-r", help="Comma-separated list of repo aliases."),
    tags: Optional[str] = typer.Option(None, "--tags", "-t", help="Only run on repos with these tags."),
    runtime: Optional[str] = typer.Option(None, "--runtime", help="Runtime override."),
    auto_approve: bool = typer.Option(False, "--auto-approve", help="Skip approval gates."),
    workers: int = typer.Option(4, "--workers", "-w", help="Number of parallel workers per wave."),
) -> None:
    """Dispatch a mission to multiple repositories in parallel waves."""
    config = load_fleet_config()
    
    target_aliases = [a.strip() for a in repos.split(",")] if repos else []
    target_tags = [t.strip() for t in tags.split(",")] if tags else []
    
    targets = []
    for repo in config.repos:
        if target_aliases and repo.alias in target_aliases:
            targets.append(repo)
        elif target_tags and any(tag in repo.tags for tag in target_tags):
            targets.append(repo)
        elif not target_aliases and not target_tags:
            targets.append(repo)
            
    if not targets:
        console.print("[yellow]No target repositories found.[/]")
        return
        
    console.print(f"[cyan]Resolving dependencies and dispatching mission to {len(targets)} repositories...[/]")
    
    try:
        results = dispatch_fleet_mission(
            requirement=requirement,
            target_repos=targets,
            runtime=runtime,
            auto_approve=auto_approve,
            max_workers=workers
        )
        
        for wave in results["waves"]:
            console.print(f"\n[bold]Wave {wave['wave_index']}:[/]")
            for res in wave["results"]:
                status = "[green]SUCCESS[/]" if res["success"] else "[red]FAILED[/]"
                console.print(f"  - [bold cyan]{res['alias']}[/]: {status}")
                if not res["success"]:
                    console.print(f"    [dim]Error:[/] {res['output_preview']}")
        
        console.print(f"\n[bold green]✓[/] Dispatch complete.")
        console.print(f"  Success: {len(results['success'])}")
        console.print(f"  Failed:  {len(results['failed'])}")
        
    except ValueError as e:
        console.print(f"[bold red]Error:[/] {e}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[bold red]Error:[/] Unexpected failure: {e}")
        raise typer.Exit(1)
