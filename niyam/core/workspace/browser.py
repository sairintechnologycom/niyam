"""Browser workspace module for Phase F."""

import os
import tempfile
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from .models import BrowserAction, BrowserSession
from niyam.core.errors import NiyamError


class BrowserStore:
    def __init__(self, workspace_dir: Path):
        self.browser_dir = workspace_dir / "browser"
        self.browser_dir.mkdir(parents=True, exist_ok=True)
        self.artifacts_dir = workspace_dir / "artifacts"
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

    def _get_session_path(self, workspace_session_id: str) -> Path:
        return self.browser_dir / f"{workspace_session_id}.json"

    def _get_timeline_path(self, workspace_session_id: str) -> Path:
        return self.browser_dir / f"{workspace_session_id}-actions.jsonl"

    def get_session(self, workspace_session_id: str) -> Optional[BrowserSession]:
        path = self._get_session_path(workspace_session_id)
        if not path.exists():
            return None
        return BrowserSession.model_validate_json(path.read_text(encoding="utf-8"))

    def save_session(self, session: BrowserSession) -> None:
        path = self._get_session_path(session.workspace_session_id)
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

    def log_action(self, action: BrowserAction) -> None:
        path = self._get_timeline_path(action.workspace_session_id)

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

    def get_actions(self, workspace_session_id: str) -> List[BrowserAction]:
        path = self._get_timeline_path(workspace_session_id)
        actions = []
        if not path.exists():
            return actions

        with path.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    actions.append(BrowserAction.model_validate_json(line))
                except Exception:
                    pass
        return actions


class BrowserBackend(ABC):
    @abstractmethod
    def start(self, start_url: Optional[str] = None) -> BrowserSession:
        pass

    @abstractmethod
    def navigate(self, url: str) -> BrowserAction:
        pass

    @abstractmethod
    def click(self, selector: str) -> BrowserAction:
        pass

    @abstractmethod
    def type(self, selector: str, text: str) -> BrowserAction:
        pass

    @abstractmethod
    def screenshot(self, output_path: Optional[Path] = None) -> BrowserAction:
        pass

    @abstractmethod
    def close(self) -> BrowserSession:
        pass


class RecorderBrowserBackend(BrowserBackend):
    """A dry-run local recorder backend that doesn't use Playwright."""

    def __init__(self, workspace_session_id: str, store: BrowserStore):
        self.workspace_session_id = workspace_session_id
        self.store = store
        self.session_id = f"BROWSER-{uuid.uuid4().hex[:8].upper()}"

    def _get_or_create_session(self) -> BrowserSession:
        session = self.store.get_session(self.workspace_session_id)
        if not session:
            session = BrowserSession(
                id=self.session_id,
                workspace_session_id=self.workspace_session_id,
                status="created",
                started_at=datetime.now(timezone.utc),
            )
            self.store.save_session(session)
        return session

    def start(self, start_url: Optional[str] = None) -> BrowserSession:
        session = self._get_or_create_session()
        session.status = "running"
        session.start_url = start_url
        session.current_url = start_url
        session.updated_at = datetime.now(timezone.utc)
        self.store.save_session(session)
        return session

    def _create_action(
        self,
        action_type: str,
        risk: str,
        target: Optional[str] = None,
        input: Optional[str] = None,
    ) -> BrowserAction:
        session = self._get_or_create_session()
        action = BrowserAction(
            id=f"BACT-{uuid.uuid4().hex[:8].upper()}",
            browser_session_id=session.id,
            workspace_session_id=self.workspace_session_id,
            action_type=action_type,  # type: ignore
            target=target,
            input=input,
            risk=risk,  # type: ignore
            status="recorded",
            url_before=session.current_url,
        )
        return action

    def navigate(self, url: str) -> BrowserAction:
        action = self._create_action("navigate", "low", target=url)
        action.url_after = url

        session = self._get_or_create_session()
        session.current_url = url
        session.updated_at = datetime.now(timezone.utc)
        self.store.save_session(session)

        return action

    def click(self, selector: str) -> BrowserAction:
        action = self._create_action("click", "medium", target=selector)
        action.url_after = action.url_before
        return action

    def type(self, selector: str, text: str) -> BrowserAction:
        from niyam.governance.common.redaction import contains_secret

        sensitive_terms = ("password", "secret", "token", "key", "credential")
        risk = (
            "high"
            if any(term in selector.lower() for term in sensitive_terms)
            or contains_secret(text)
            else "medium"
        )
        action = self._create_action("type", risk, target=selector, input=text)
        action.url_after = action.url_before
        return action

    def submit(self, selector: Optional[str] = None) -> BrowserAction:
        action = self._create_action("submit", "high", target=selector)
        action.url_after = action.url_before
        return action

    def screenshot(self, output_path: Optional[Path] = None) -> BrowserAction:
        action = self._create_action("screenshot", "low")
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.touch()
            action.output = str(output_path)
        action.url_after = action.url_before
        return action

    def close(self) -> BrowserSession:
        session = self._get_or_create_session()
        session.status = "completed"
        session.completed_at = datetime.now(timezone.utc)
        session.updated_at = datetime.now(timezone.utc)
        self.store.save_session(session)
        return session
