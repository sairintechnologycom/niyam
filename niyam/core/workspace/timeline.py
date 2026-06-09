"""Workspace timeline for tracking actions."""

from pathlib import Path
from typing import List

from .models import WorkspaceAction


class WorkspaceTimeline:
    def __init__(self, workspace_dir: Path):
        self.workspace_dir = workspace_dir
        self.timelines_dir = self.workspace_dir / "timelines"
        self.timelines_dir.mkdir(parents=True, exist_ok=True)

    def _get_timeline_path(self, session_id: str) -> Path:
        return self.timelines_dir / f"{session_id}.jsonl"

    def log_action(self, action: WorkspaceAction) -> None:
        path = self._get_timeline_path(action.session_id)
        
        from niyam.governance.common.redaction import redact_text

        if action.input:
            redacted_input = redact_text(action.input, with_fingerprint=False)
            if redacted_input != action.input:
                action.input = redacted_input
                action.redacted = True
        if action.output:
            redacted_output = redact_text(action.output, with_fingerprint=False)
            if redacted_output != action.output:
                action.output = redacted_output
                action.redacted = True
            
        with path.open("a", encoding="utf-8") as f:
            f.write(action.model_dump_json() + "\n")

    def get_actions(self, session_id: str) -> List[WorkspaceAction]:
        path = self._get_timeline_path(session_id)
        actions = []
        if not path.exists():
            return actions
        
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    actions.append(WorkspaceAction.model_validate_json(line))
                except Exception:
                    pass
        return actions
