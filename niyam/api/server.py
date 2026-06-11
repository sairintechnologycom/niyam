"""Niyam FastAPI server — backend for mission dashboard and API portal."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from niyam.core.config import find_niyam_root, get_niyam_dir

logger = logging.getLogger(__name__)

def _get_auth_token() -> str:
    """Get or generate a persistent authentication token for the portal."""
    repo_root = find_niyam_root()
    if not repo_root:
        return ""
    niyam_dir = get_niyam_dir(repo_root)
    token_file = niyam_dir / "auth_token"

    if token_file.exists():
        return token_file.read_text(encoding="utf-8").strip()

    # Generate new token
    import secrets
    token = secrets.token_hex(24)
    token_file.write_text(token, encoding="utf-8")
    return token

async def verify_token(x_niyam_token: str = Header(None)):
    """Dependency to verify the authentication token."""
    expected = _get_auth_token()
    if not expected:
        return # Not in a workspace, allow for now (or maybe strictly deny?)

    if x_niyam_token != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing X-Niyam-Token header")

app = FastAPI(
    title="Niyam Portal API",
    description="Backend for AI Development Orchestration Dashboard",
    version="1.0.0",
)

from niyam.mission.utils import load_plan
from niyam.mission.dashboard import get_task_durations
from niyam.api.models import (
    MissionSummary,
    MissionDetails,
    TaskInfo,
    TokenMetrics,
    ActionResponse,
)

app = FastAPI(
    title="Niyam Portal API",
    description="Backend for AI Development Orchestration Dashboard",
    version="1.0.0",
)

# Enable CORS for local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_repo_context() -> tuple[Path, Path]:
    """Helper to get repo and niyam directories."""
    repo_root = find_niyam_root()
    if not repo_root:
        raise HTTPException(status_code=500, detail="Not a Niyam workspace.")
    return repo_root, get_niyam_dir(repo_root)


@app.get("/", response_class=HTMLResponse)
def get_portal():
    """Serve the Niyam Portal web interface with injected auth token."""
    template_path = Path(__file__).parent.parent / "templates" / "portal" / "index.html"
    if not template_path.exists():
        return "<h1>Niyam Portal</h1><p>Template not found.</p>"
    
    content = template_path.read_text(encoding="utf-8")
    token = _get_auth_token()
    # Inject token into a global JS variable
    injection = f"<script>window.NIYAM_AUTH_TOKEN = '{token}';</script>"
    content = content.replace("</head>", f"{injection}\n</head>")
    return content


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "niyam-portal"}


def _get_run_readiness(run_dir: Path) -> tuple[int | None, str | None]:
    """Helper to load readiness score and decision from scan reports in run dir."""
    # Try common report filenames
    for fname in ["scan-report.json", "scan.json", "evidence.json"]:
        path = run_dir / fname
        if path.exists():
            try:
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
                    # Handle both raw scan results and evidence reports
                    score = data.get("score") or data.get("readiness_score")
                    decision = data.get("decision")
                    if score is not None:
                        return int(score), decision
            except Exception:
                pass
    return None, None


@app.get("/analytics")
def get_fleet_analytics():
    """Get fleet-wide performance and cost analytics."""
    from niyam.core.analytics import PerformanceMetrics
    repo_root, _ = get_repo_context()
    analytics = PerformanceMetrics(repo_root)
    return analytics.get_fleet_summary()


@app.get("/policies")
def get_policies():
    """Get configured governance policies for the workspace."""
    from niyam.core.config import load_niyam_config
    from niyam.policies.guard import load_security_policy, load_commands_policy
    
    repo_root, niyam_dir = get_repo_context()
    
    try:
        config = load_niyam_config(repo_root)
        guard_config = config.governance.guard.model_dump() if config.governance else {}
    except Exception:
        guard_config = {}

    security_policy = load_security_policy(repo_root)
    commands_policy = load_commands_policy(repo_root)
    
    # Try to load approvals
    app_policy_path = niyam_dir / "policies" / "approvals.yaml"
    approvals = []
    if app_policy_path.exists():
        try:
            from niyam.core.security import safe_load_yaml
            app_data = safe_load_yaml(app_policy_path) or {}
            approvals = app_data.get("approval_required_for", [])
        except Exception:
            pass

    return {
        "security": security_policy,
        "commands": commands_policy,
        "approvals": approvals,
        "guard_config": guard_config
    }


@app.get("/mcp")
def get_mcp_registry():
    """Get the MCP tool registry state."""
    repo_root, _ = get_repo_context()
    try:
        from niyam.core.mcp import load_mcp_registry
        return load_mcp_registry(repo_root).model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load MCP registry: {e}")


@app.get("/fleet")
def get_fleet_config():
    """Get the Fleet configuration."""
    try:
        from niyam.core.fleet import load_fleet_config
        return load_fleet_config().model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load Fleet config: {e}")


@app.get("/swarm")
def get_swarm_state():
    """Get the current Swarm state."""
    repo_root, _ = get_repo_context()
    try:
        from niyam.core.swarm import load_swarm_state
        return load_swarm_state(repo_root).model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load Swarm state: {e}")


@app.get("/guard")
def get_guard_logs():
    """Get the recent guard action logs."""
    _, niyam_dir = get_repo_context()
    log_path = niyam_dir / "logs" / "guard-actions.jsonl"
    if not log_path.exists():
        return []
    
    logs = []
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            for line in reversed(lines[-100:]): # Get last 100 entries, newest first
                if line.strip():
                    logs.append(json.loads(line))
        return logs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load guard logs: {e}")


@app.get("/audits/prompts")
def get_prompt_audits():
    """Get a log of prompts used across missions for auditing."""
    _, niyam_dir = get_repo_context()
    runs_dir = niyam_dir / "runs"
    if not runs_dir.exists():
        return []

    prompts = []
    # Sort by directory mtime (newest first)
    run_dirs = sorted(
        [d for d in runs_dir.iterdir() if d.is_dir()],
        key=lambda x: x.stat().st_mtime,
        reverse=True,
    )

    for run_dir in run_dirs:
        tasks_dir = run_dir / "tasks"
        if not tasks_dir.exists():
            continue
            
        for task_dir in tasks_dir.iterdir():
            if not task_dir.is_dir():
                continue
                
            prompt_file = task_dir / "prompt.md"
            if prompt_file.exists():
                try:
                    content = prompt_file.read_text(encoding="utf-8")
                    prompts.append({
                        "mission_id": run_dir.name,
                        "task_id": task_dir.name,
                        "content": content,
                        "timestamp": task_dir.stat().st_mtime
                    })
                except Exception:
                    pass

    return prompts


@app.get("/missions", response_model=list[MissionSummary])
def list_missions():
    """List all available mission runs."""
    _, niyam_dir = get_repo_context()
    runs_dir = niyam_dir / "runs"
    if not runs_dir.exists():
        return []

    summaries = []
    # Sort by directory mtime (newest first)
    run_dirs = sorted(
        [d for d in runs_dir.iterdir() if d.is_dir()],
        key=lambda x: x.stat().st_mtime,
        reverse=True,
    )

    for run_dir in run_dirs:
        plan_path = run_dir / "mission-plan.yaml"
        if not plan_path.exists():
            continue

        try:
            plan = load_plan(run_dir)
            meta = plan.get("mission", {})
            tasks = plan.get("tasks", [])
            
            score, decision = _get_run_readiness(run_dir)
            
            summaries.append(
                MissionSummary(
                    id=run_dir.name,
                    status=meta.get("status", "unknown"),
                    orchestrator=meta.get("orchestrator", "unknown"),
                    created=meta.get("created", "unknown"),
                    task_count=len(tasks),
                    completed_tasks=sum(
                        1 for t in tasks if t.get("status") == "completed"
                    ),
                    readiness_score=score,
                    decision=decision,
                )
            )
        except Exception as e:
            logger.debug(f"Error loading plan in {run_dir}: {e}")
            continue

    return summaries


@app.get("/missions/{mission_id}", response_model=MissionDetails)
def get_mission(mission_id: str):
    """Get detailed state for a specific mission."""
    _, niyam_dir = get_repo_context()
    run_dir = niyam_dir / "runs" / mission_id
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail=f"Mission {mission_id} not found.")

    plan = load_plan(run_dir)
    meta = plan.get("mission", {})
    tasks_data = plan.get("tasks", [])
    durations = get_task_durations(run_dir)

    tasks = []
    for t in tasks_data:
        tasks.append(
            TaskInfo(
                id=t.get("id", ""),
                title=t.get("title", ""),
                agent=t.get("agent", ""),
                status=t.get("status", "planned"),
                duration=durations.get(t.get("id"), 0.0),
                depends_on=t.get("depends_on", []),
            )
        )

    # Metrics
    metrics = None
    ledger_path = run_dir / "token-ledger.json"
    if ledger_path.exists():
        try:
            with open(ledger_path, encoding="utf-8") as f:
                ledger = json.load(f)
                summary = ledger.get("summary", {})
                metrics = TokenMetrics(
                    actual_tokens=summary.get("total_tokens", 0),
                    actual_cost_usd=summary.get("total_cost_usd", 0.0),
                    wasted_cost_usd=summary.get("total_wasted_cost_usd", 0.0),
                    savings_tokens=max(
                        0,
                        summary.get("total_baseline_tokens", 0)
                        - summary.get("total_tokens", 0),
                    ),
                    savings_cost_usd=max(
                        0.0,
                        summary.get("total_baseline_cost_usd", 0.0)
                        - summary.get("total_cost_usd", 0.0),
                    ),
                    savings_percent=summary.get("savings_percent", 0.0),
                )
        except Exception:
            pass

    score, decision = _get_run_readiness(run_dir)

    # Load approvals info
    approval_data = None
    approval_path = run_dir / "approval.json"
    if approval_path.exists():
        try:
            with open(approval_path, encoding="utf-8") as f:
                approval_data = json.load(f)
        except Exception:
            pass

    # Get required roles
    repo_root, _ = get_repo_context()
    required_roles = ["default"]
    if repo_root:
        try:
            from niyam.core.config import load_niyam_config
            config = load_niyam_config(repo_root)
            if config.governance and config.governance.guard:
                required_roles = config.governance.guard.mission_approval_roles or ["default"]
        except Exception:
            pass

    # Build the approvals summary for UI
    approvals_summary = {
        "approved": approval_data.get("approved", False) if approval_data else False,
        "required_roles": required_roles,
        "current_approvals": approval_data.get("approvals", {}) if approval_data else {}
    }

    return MissionDetails(
        id=mission_id,
        status=meta.get("status", "planned"),
        orchestrator=meta.get("orchestrator", "unknown"),
        created=meta.get("created", "unknown"),
        parallel=meta.get("parallel", 1),
        worktree=meta.get("worktree", True),
        tasks=tasks,
        metrics=metrics,
        readiness_score=score,
        decision=decision,
        approvals=approvals_summary,
    )


@app.get("/missions/{mission_id}/evidence")
def get_mission_evidence(mission_id: str):
    """Return the evidence report content."""
    _, niyam_dir = get_repo_context()
    evidence_path = niyam_dir / "runs" / mission_id / "evidence.md"
    if not evidence_path.exists():
        raise HTTPException(
            status_code=404, detail=f"Evidence for mission {mission_id} not found."
        )
    return {"content": evidence_path.read_text(encoding="utf-8")}


@app.get("/missions/{mission_id}/sarif")
def get_mission_sarif(mission_id: str):
    """Return the SARIF scan results if available."""
    _, niyam_dir = get_repo_context()
    # Try different possible SARIF paths
    for fname in ["scan-report.sarif.json", "scan.sarif", "results.sarif"]:
        path = niyam_dir / "runs" / mission_id / fname
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    
    # Try to generate it on the fly from json if possible
    json_path = niyam_dir / "runs" / mission_id / "scan-report.json"
    if json_path.exists():
        try:
            from niyam.cli.scan import generate_sarif_report
            with open(json_path, encoding="utf-8") as f:
                results = json.load(f)
                sarif_str = generate_sarif_report(results)
                return json.loads(sarif_str)
        except Exception:
            pass

    raise HTTPException(
        status_code=404, detail=f"SARIF report for mission {mission_id} not found."
    )


@app.get("/missions/{mission_id}/tasks/{task_id}/logs")
def get_task_logs(mission_id: str, task_id: str):
    """Return the execution logs for a specific task."""
    _, niyam_dir = get_repo_context()
    log_path = niyam_dir / "runs" / mission_id / "tasks" / task_id / "execution.log"
    if not log_path.exists():
        # Try generic execution log
        log_path = niyam_dir / "runs" / mission_id / "execution-log.json"
        
    if not log_path.exists():
        return {"content": "No logs found for this task."}
        
    return {"content": log_path.read_text(encoding="utf-8")}


@app.post("/missions/{mission_id}/action", response_model=ActionResponse, dependencies=[Depends(verify_token)])
def mission_action(mission_id: str, action: str):
    """Perform a control action on the mission (pause, resume, cancel)."""
    _, niyam_dir = get_repo_context()
    run_dir = niyam_dir / "runs" / mission_id
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail=f"Mission {mission_id} not found.")

    from niyam.mission.state_machine import transition_mission

    if action == "pause":
        transition_mission(run_dir, "paused", reason="Paused via API Portal")
        return ActionResponse(
            success=True, message="Mission paused successfully.", new_status="paused"
        )
    elif action == "resume":
        # Resume logic usually requires a runner. For now, just mark state.
        # Real resume logic would be triggered by a background task if needed.
        transition_mission(run_dir, "approved", reason="Resumed via API Portal")
        return ActionResponse(
            success=True, message="Mission resumed and ready.", new_status="approved"
        )
    elif action == "cancel":
        transition_mission(run_dir, "cancelled", reason="Cancelled via API Portal")
        return ActionResponse(
            success=True,
            message="Mission cancelled successfully.",
            new_status="cancelled",
        )
    elif action == "replan":
        from niyam.mission.planner import run_mission_replan
        from rich.console import Console
        try:
            run_mission_replan(
                console=Console(quiet=True),
                mission_id=mission_id,
                reason="Re-plan requested via API Portal."
            )
            return ActionResponse(
                success=True,
                message="Mission re-planned successfully.",
                new_status="planned",
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported action: {action}")


@app.post("/missions/{mission_id}/approve", response_model=ActionResponse, dependencies=[Depends(verify_token)])
def approve_mission(mission_id: str, role: str = "default"):
    """Approve a planned mission, supporting multi-party role-based approvals."""
    from rich.console import Console
    from niyam.mission.planner import run_mission_approve
    
    console = Console(quiet=True)
    try:
        run_mission_approve(console=console, interactive=False, mission_id=mission_id, role=role)
        
        # Load the updated approvals info to return status
        repo_root, niyam_dir = get_repo_context()
        run_dir = niyam_dir / "runs" / mission_id
        approval_path = run_dir / "approval.json"
        
        approved = False
        pending_roles = []
        if approval_path.exists():
            try:
                with open(approval_path, encoding="utf-8") as f:
                    app_data = json.load(f)
                approved = app_data.get("approved", False)
                # Load configuration to get all required roles
                from niyam.core.config import load_niyam_config
                try:
                    config = load_niyam_config(repo_root)
                    required_approvals = config.governance.guard.mission_approval_roles if config.governance and config.governance.guard else ["default"]
                except Exception:
                    required_approvals = ["default"]
                if not required_approvals:
                    required_approvals = ["default"]
                pending_roles = [r for r in required_approvals if r not in app_data.get("approvals", {})]
            except Exception:
                pass
        
        status = "approved" if approved else "pending_approvals"
        msg = f"Approved as role '{role}'."
        if not approved and pending_roles:
            msg += f" Still waiting for: {', '.join(pending_roles)}"
        else:
            msg += " Mission is now fully approved and ready to start."
            
        return ActionResponse(
            success=True,
            message=msg,
            new_status=status
        )
    except SystemExit:
        raise HTTPException(status_code=400, detail="Approval failed. Check mission plan validation or status.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/missions/{mission_id}/tasks/{task_id}/approve", response_model=ActionResponse, dependencies=[Depends(verify_token)])
def approve_task(mission_id: str, task_id: str):
    """Approve a task that is blocked waiting for manual human approval."""
    _, niyam_dir = get_repo_context()
    run_dir = niyam_dir / "runs" / mission_id
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail=f"Mission {mission_id} not found.")
        
    task_dir = run_dir / "tasks" / task_id
    if not task_dir.exists():
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found.")
        
    approval_file = task_dir / "approval.json"
    
    # Write the approval file so the executor polling loop can pick it up
    try:
        from datetime import datetime, timezone
        approval_data = {
            "approved": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor": "human via portal"
        }
        approval_file.write_text(json.dumps(approval_data, indent=2), encoding="utf-8")
        return ActionResponse(
            success=True,
            message=f"Task {task_id} approved successfully.",
            new_status="approved"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/missions/{mission_id}/tasks/{task_id}/deny", response_model=ActionResponse, dependencies=[Depends(verify_token)])
def deny_task(mission_id: str, task_id: str):
    """Deny a task that is blocked waiting for manual human approval."""
    _, niyam_dir = get_repo_context()
    run_dir = niyam_dir / "runs" / mission_id
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail=f"Mission {mission_id} not found.")
        
    task_dir = run_dir / "tasks" / task_id
    if not task_dir.exists():
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found.")
        
    approval_file = task_dir / "approval.json"
    
    try:
        from datetime import datetime, timezone
        approval_data = {
            "approved": False,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor": "human via portal",
            "reason": "Denied via portal"
        }
        approval_file.write_text(json.dumps(approval_data, indent=2), encoding="utf-8")
        return ActionResponse(
            success=True,
            message=f"Task {task_id} denied.",
            new_status="failed"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def start_server(host: str = "127.0.0.1", port: int = 8080):
    """Entry point for the uvicorn server."""
    import uvicorn

    uvicorn.run(app, host=host, port=port)
