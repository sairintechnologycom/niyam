"""Sutra mission reporter — generate evidence package for completed missions."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
from datetime import datetime
import yaml
from rich.console import Console
from rich.panel import Panel

from sutra.core.config import get_sutra_dir
from sutra.mission.planner import get_latest_mission_id
from sutra.mission.executor import load_plan
import hashlib
import hmac
import os


def compute_sha256(file_path: Path) -> str:
    """Compute the SHA-256 hash of a file."""
    if not file_path.exists() or not file_path.is_file():
        return "DELETED"
    h = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                h.update(chunk)
        return h.hexdigest()
    except Exception as e:
        return f"ERROR: {e}"


def _get_signing_key() -> bytes | None:
    """Get HMAC signing key from environment or .sutra/signing-key file."""
    env_key = os.environ.get("SUTRA_SIGNING_KEY")
    if env_key:
        return env_key.encode("utf-8")
    return None


def compute_manifest_hmac(manifest_files: dict[str, str], signing_key: bytes) -> str:
    """Compute HMAC-SHA256 over canonical manifest content.

    Creates a deterministic string from sorted file paths and their hashes,
    then signs it with the provided key.
    """
    canonical = "\n".join(
        f"{k}:{v}" for k, v in sorted(manifest_files.items())
    )
    return hmac.new(signing_key, canonical.encode("utf-8"), hashlib.sha256).hexdigest()


def get_changed_files(repo_root: Path) -> list[str]:
    """Retrieve list of modified/untracked files from Git."""
    try:
        res = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        )
        files = []
        for line in res.stdout.splitlines():
            if line.strip():
                parts = line.strip().split(maxsplit=1)
                if len(parts) == 2:
                    rel_path = parts[1]
                    if not rel_path.startswith(".sutra") and not rel_path.startswith("evidence.md"):
                        files.append(rel_path)
        return files
    except Exception:
        return []


def run_mission_report(console: Console) -> None:
    """Generate final evidence package for the latest mission."""
    from sutra.core.config import find_sutra_root
    from sutra.core.errors import SutraConfigError

    repo_root = find_sutra_root()
    if not repo_root:
        raise SutraConfigError("Not a Sutra workspace. Run 'sutra init' first.")
    sutra_dir = get_sutra_dir(repo_root)

    mission_id = get_latest_mission_id(sutra_dir)
    if not mission_id:
        console.print("[bold red]Error:[/] No missions found.")
        raise SystemExit(1)

    run_dir = sutra_dir / "runs" / mission_id
    plan_data = load_plan(run_dir)
    mission_meta = plan_data.get("mission", {})

    status = mission_meta.get("status", "unknown")
    created = mission_meta.get("created", "")
    orchestrator = mission_meta.get("orchestrator", "claude")

    # 1. Collect Git Diff
    git_diff = ""
    base_sha = mission_meta.get("base_sha")
    try:
        if base_sha:
            res = subprocess.run(["git", "diff", base_sha], capture_output=True, text=True)
        else:
            res = subprocess.run(["git", "diff"], capture_output=True, text=True)
        if res.returncode == 0:
            git_diff = res.stdout
    except Exception:
        pass

    # Write diff to run directory
    diff_path = run_dir / "diff-summary.md"
    if git_diff:
        diff_path.write_text(f"### Git Diff Summary\n\n```diff\n{git_diff}\n```\n", encoding="utf-8")
    else:
        diff_path.write_text("No changes detected in Git.\n", encoding="utf-8")

    # 2. Collect Validation Results
    val_path = run_dir / "validation-results.md"
    val_results = ""
    if val_path.exists():
        val_results = val_path.read_text(encoding="utf-8")
    else:
        val_results = "*No validation runs recorded for this mission.*\n"

    # 3. Collect Policy Events
    policy_events_path = run_dir / "policy-events.json"
    policy_events: list[dict] = []
    
    # Also check the global policy events and filter by time if possible
    global_policy_path = sutra_dir / "evidence" / "policy-events.json"
    
    # Combine events
    for path in (policy_events_path, global_policy_path):
        if path.exists():
            try:
                with open(path, encoding="utf-8") as f:
                    events = json.load(f)
                    if isinstance(events, list):
                        for e in events:
                            if e not in policy_events:
                                policy_events.append(e)
            except Exception:
                pass

    # Sort events by timestamp
    policy_events.sort(key=lambda e: e.get("timestamp", ""))

    # 4. Collect Execution Log
    exec_log_path = run_dir / "execution-log.json"
    exec_log: list[dict] = []
    if exec_log_path.exists():
        try:
            with open(exec_log_path, encoding="utf-8") as f:
                exec_log = json.load(f)
        except Exception:
            pass

    # 5. Build final evidence.md content
    report_sections = []
    report_sections.append(f"# Sutra Mission Evidence Package - {mission_id}")
    report_sections.append("")
    report_sections.append(f"- **Requirement Source:** `{mission_meta.get('requirement', '')}`")
    report_sections.append(f"- **Generated:** `{datetime.utcnow().isoformat()}Z`")
    report_sections.append(f"- **Status:** `{status.upper()}`")
    report_sections.append(f"- **Orchestrator:** `{orchestrator}`")
    report_sections.append("")
    report_sections.append("## Task Checklist")
    report_sections.append("")
    for task in plan_data.get("tasks", []):
        icon = "✓" if task.get("status") == "completed" else "✗"
        sha_str = f" (commit: `{task['commit_sha'][:7]}`)" if task.get("commit_sha") else ""
        report_sections.append(f"- [{icon}] **{task.get('id', '')}**: {task.get('title', '')} ({task.get('agent', '')}){sha_str}")
    report_sections.append("")

    report_sections.append("## Execution Log")
    report_sections.append("")
    if exec_log:
        for event in exec_log:
            task_str = f" [{event.get('task_id')}]" if event.get("task_id") else ""
            report_sections.append(f"- `{event.get('timestamp')}` **{event.get('event')}**{task_str}: {event.get('details')}")
    else:
        report_sections.append("*No execution logs recorded.*")
    report_sections.append("")

    report_sections.append("## Policy Guard Audit Trail")
    report_sections.append("")
    if policy_events:
        report_sections.append("| Timestamp | Type | Event Details |")
        report_sections.append("|-----------|------|---------------|")
        for event in policy_events:
            report_sections.append(f"| `{event.get('timestamp')}` | `{event.get('type')}` | {event.get('details')} |")
    else:
        report_sections.append("*No policy events triggered.*")
    report_sections.append("")

    report_sections.append("## Validation Results")
    report_sections.append("")
    report_sections.append(val_results)
    report_sections.append("")

    report_sections.append("## Changes Made (Git Diff)")
    report_sections.append("")
    if git_diff:
        report_sections.append(f"```diff\n{git_diff}\n```")
    else:
        report_sections.append("*No changes detected in source code.*")
    report_sections.append("")

    # Generate cryptographic manifest signature block
    manifest_files = {}
    for run_file in ("mission-plan.yaml", "execution-log.json", "validation-results.md", "policy-events.json"):
        full_path = run_dir / run_file
        if full_path.exists():
            manifest_files[run_file] = compute_sha256(full_path)
            
    changed_files = get_changed_files(repo_root)
    for f in changed_files:
        manifest_files[f] = compute_sha256(repo_root / f)
        
    manifest = {
        "mission_id": mission_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "files": manifest_files,
    }

    # Add HMAC signature if signing key is available
    signing_key = _get_signing_key()
    if signing_key:
        manifest["hmac_sha256"] = compute_manifest_hmac(manifest_files, signing_key)
        manifest["signed"] = True
    else:
        manifest["signed"] = False
    
    report_sections.append("## Cryptographic Integrity Manifest")
    report_sections.append("")
    report_sections.append("<!-- SUTRA_SIGNATURE_START")
    report_sections.append(json.dumps(manifest, indent=2))
    report_sections.append("SUTRA_SIGNATURE_END -->")
    report_sections.append("")

    # Write report
    report_file = run_dir / "evidence.md"
    report_file.write_text("\n".join(report_sections), encoding="utf-8")

    # Also copy or link to evidence.json if requested
    evidence_json = run_dir / "evidence.json"
    json_data = {
        "mission_id": mission_id,
        "status": status,
        "created": created,
        "completed": datetime.utcnow().isoformat() + "Z",
        "orchestrator": orchestrator,
        "tasks": plan_data.get("tasks", []),
        "policy_events": policy_events,
        "execution_log": exec_log,
        "signature_manifest": manifest,
    }
    with open(evidence_json, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2)

    console.print(Panel(
        f"Evidence Markdown: [bold cyan]evidence.md[/]\n"
        f"Evidence JSON: [bold cyan]evidence.json[/]\n"
        f"Location: [bold].sutra/runs/{mission_id}/[/]",
        title="[bold green]✓ Evidence Report Generated[/]",
        border_style="green"
    ))


def run_verify_report(evidence_path: str, console: Console) -> None:
    """Verify cryptographic integrity of an evidence report."""
    path = Path(evidence_path)
    if not path.exists():
        console.print(f"[bold red]Error:[/] Evidence file '{evidence_path}' not found.")
        raise SystemExit(1)

    content = path.read_text(encoding="utf-8")
    
    start_tag = "<!-- SUTRA_SIGNATURE_START"
    end_tag = "SUTRA_SIGNATURE_END -->"
    
    if start_tag not in content or end_tag not in content:
        console.print("[bold red]❌ Integrity check failed:[/] No cryptographic signature manifest found in evidence report.")
        raise SystemExit(1)

    try:
        sig_part = content.split(start_tag)[1].split(end_tag)[0].strip()
        manifest = json.loads(sig_part)
    except Exception as e:
        console.print(f"[bold red]❌ Integrity check failed:[/] Signature manifest block is corrupt: {e}")
        raise SystemExit(1)

    run_dir = path.parent
    from sutra.core.config import find_sutra_root
    repo_root = find_sutra_root(start=run_dir) or find_sutra_root() or Path.cwd()

    failures = []
    verified_count = 0

    for rel_file, expected_hash in manifest.get("files", {}).items():
        if rel_file in ("mission-plan.yaml", "execution-log.json", "validation-results.md", "policy-events.json"):
            file_path = run_dir / rel_file
        else:
            file_path = repo_root / rel_file

        actual_hash = compute_sha256(file_path)
        if actual_hash != expected_hash:
            failures.append((rel_file, expected_hash, actual_hash))
        else:
            verified_count += 1

    if failures:
        console.print(f"[bold red]❌ Integrity check failed:[/] {len(failures)} file(s) tampered or modified since the report was generated.")
        for rel_file, exp, act in failures:
            console.print(f"  - [red]{rel_file}[/]: expected `{exp[:10]}...`, got `{act[:10]}...`")
        raise SystemExit(1)

    # Verify HMAC signature if the manifest was signed
    hmac_status = "not signed"
    if manifest.get("signed"):
        signing_key = _get_signing_key()
        if signing_key:
            expected_hmac = manifest.get("hmac_sha256", "")
            actual_hmac = compute_manifest_hmac(manifest.get("files", {}), signing_key)
            if not hmac.compare_digest(expected_hmac, actual_hmac):
                console.print("[bold red]❌ HMAC signature verification FAILED.[/] The manifest may have been tampered with.")
                raise SystemExit(1)
            hmac_status = "[bold green]VERIFIED[/]"
        else:
            hmac_status = "[yellow]signed but SUTRA_SIGNING_KEY not set — cannot verify[/]"

    console.print(Panel(
        f"Mission ID: [bold cyan]{manifest.get('mission_id')}[/]\n"
        f"Signed On: [bold cyan]{manifest.get('timestamp')}[/]\n"
        f"Verified Files: [bold green]{verified_count}[/]\n"
        f"HMAC Signature: {hmac_status}",
        title="[bold green]✓ Evidence Report Verified Successfully[/]",
        border_style="green"
    ))
