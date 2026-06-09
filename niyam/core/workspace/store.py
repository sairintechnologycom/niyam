"""Workspace store for managing session metadata."""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from .models import WorkspaceSession
from niyam.core.errors import NiyamError

class WorkspaceStore:
    def __init__(self, workspace_dir: Path):
        self.workspace_dir = workspace_dir
        self.sessions_dir = self.workspace_dir / "sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

    def _get_session_path(self, session_id: str) -> Path:
        return self.sessions_dir / f"{session_id}.json"

    def create_session(self, session: WorkspaceSession) -> None:
        path = self._get_session_path(session.id)
        if path.exists():
            raise NiyamError(f"Session {session.id} already exists.", code=1)
        path.write_text(session.model_dump_json(indent=2))

    def get_session(self, session_id: str) -> Optional[WorkspaceSession]:
        path = self._get_session_path(session_id)
        if not path.exists():
            return None
        return WorkspaceSession.model_validate_json(path.read_text())

    def update_session(self, session: WorkspaceSession) -> None:
        path = self._get_session_path(session.id)
        if not path.exists():
            raise NiyamError(f"Session {session.id} does not exist.", code=1)
        session.updated_at = datetime.utcnow()
        path.write_text(session.model_dump_json(indent=2))

    def list_sessions(self) -> List[WorkspaceSession]:
        sessions = []
        for path in self.sessions_dir.glob("*.json"):
            try:
                sessions.append(WorkspaceSession.model_validate_json(path.read_text()))
            except Exception:
                pass # skip invalid files
        sessions.sort(key=lambda s: s.created_at, reverse=True)
        return sessions
