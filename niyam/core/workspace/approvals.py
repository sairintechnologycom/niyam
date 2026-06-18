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
