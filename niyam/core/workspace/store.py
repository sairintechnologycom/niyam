"""Workspace store for managing session metadata."""

import os
import tempfile
from datetime import datetime, timezone
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
        self._write_session_atomic(path, session)

    def get_session(self, session_id: str) -> Optional[WorkspaceSession]:
        path = self._get_session_path(session_id)
        if not path.exists():
            return None
        return WorkspaceSession.model_validate_json(path.read_text())

    def update_session(self, session: WorkspaceSession) -> None:
        path = self._get_session_path(session.id)
        if not path.exists():
            raise NiyamError(f"Session {session.id} does not exist.", code=1)
        session.updated_at = datetime.now(timezone.utc)
        self._write_session_atomic(path, session)

    def list_sessions(self) -> List[WorkspaceSession]:
        sessions = []
        for path in self.sessions_dir.glob("*.json"):
            try:
                sessions.append(WorkspaceSession.model_validate_json(path.read_text()))
            except Exception:
                pass # skip invalid files
        sessions.sort(key=lambda s: s.created_at, reverse=True)
        return sessions

    def _write_session_atomic(self, path: Path, session: WorkspaceSession) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_path = tempfile.mkstemp(
            dir=path.parent,
            prefix=f"{path.stem}.",
            suffix=".json.tmp",
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(session.model_dump_json(indent=2))
                f.write("\n")
            os.replace(temp_path, path)
        except Exception:
            try:
                os.remove(temp_path)
            except OSError:
                pass
            raise
