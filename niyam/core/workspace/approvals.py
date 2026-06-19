"""Workspace approvals management."""

from pathlib import Path
from typing import List

from .models import WorkspaceApproval


class WorkspaceApprovals:
    def __init__(self, workspace_dir: Path):
        self.workspace_dir = workspace_dir
        self.approvals_dir = self.workspace_dir / "approvals"
        self.approvals_dir.mkdir(parents=True, exist_ok=True)

    def _get_approval_path(self, session_id: str) -> Path:
        return self.approvals_dir / f"{session_id}.jsonl"

    def request_approval(self, approval: WorkspaceApproval) -> None:
        path = self._get_approval_path(approval.session_id)
        with path.open("a", encoding="utf-8") as f:
            f.write(approval.model_dump_json() + "\n")

        # Remote webhook approval trigger when SaaS is enabled
        try:
            from niyam.core.config import load_niyam_config
            config = load_niyam_config()
            if config.saas and config.saas.enabled:
                self.trigger_remote_approval(approval, config.saas.base_url, config.saas.api_key)
        except Exception:
            pass

    def trigger_remote_approval(self, approval: WorkspaceApproval, base_url: str, api_key: str | None) -> None:
        """Issue an HTTP POST to request remote approval when SaaS is enabled."""
        import urllib.request
        import json

        url = f"{base_url.rstrip('/')}/api/v1/missions/{approval.session_id}/tasks/{approval.id}/approval-request"
        headers = {
            "Content-Type": "application/json",
        }
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        payload = approval.model_dump()
        for k, v in payload.items():
            if hasattr(v, "isoformat"):
                payload[k] = v.isoformat()

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as response:
                pass
        except Exception:
            # Silent fallback / logging in pilot phase
            pass

    def poll_remote_approval(self, session_id: str, approval_id: str, base_url: str, api_key: str | None) -> str | None:
        """Poll the remote endpoint to check approval status."""
        import urllib.request
        import json

        url = f"{base_url.rstrip('/')}/api/v1/missions/{session_id}/tasks/{approval_id}/approval-status"
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        req = urllib.request.Request(url, headers=headers, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode("utf-8"))
                return data.get("status")
        except Exception:
            return None

    def update_approval(self, approval: WorkspaceApproval) -> None:
        """
        Since it's an append-only log, we write the updated state.
        When loading, the latest entry for a given approval ID wins.
        """
        self.request_approval(approval)

    def get_approvals(self, session_id: str) -> List[WorkspaceApproval]:
        path = self._get_approval_path(session_id)
        approvals = {}
        if not path.exists():
            return []
        
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    appr = WorkspaceApproval.model_validate_json(line)
                    approvals[appr.id] = appr
                except Exception:
                    pass
        return sorted(approvals.values(), key=lambda approval: approval.requested_at)
