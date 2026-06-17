"""Playwright-based browser backend for the Control Room."""

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

try:
    from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page, Playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    Playwright = None
    Browser = None
    BrowserContext = None
    Page = None

from .models import BrowserAction, BrowserSession
from .browser import BrowserBackend, BrowserStore
from niyam.core.errors import NiyamError

class PlaywrightBrowserBackend(BrowserBackend):
    """A real browser backend using Playwright."""

    def __init__(self, workspace_session_id: str, store: BrowserStore):
        if not PLAYWRIGHT_AVAILABLE:
            raise NiyamError("Playwright is not installed. Run 'pip install playwright' to use this backend.")
        
        self.workspace_session_id = workspace_session_id
        self.store = store
        self.session_id = f"BROWSER-{uuid.uuid4().hex[:8].upper()}"
        
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
        # Determine if we should run headful or headless based on environment
        import os
        self.headless = os.environ.get("NIYAM_BROWSER_HEADLESS", "true").lower() == "true"


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

    def _ensure_browser(self):
        """Ensure playwright and the browser are running."""
        if not self.page:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=self.headless)
            self.context = self.browser.new_context()
            self.page = self.context.new_page()

    def start(self, start_url: Optional[str] = None) -> BrowserSession:
        session = self._get_or_create_session()
        session.status = "running"
        session.start_url = start_url
        session.current_url = start_url
        session.updated_at = datetime.now(timezone.utc)
        self.store.save_session(session)
        
        self._ensure_browser()
        if start_url and self.page:
            self.page.goto(start_url)
            session.current_url = self.page.url
            self.store.save_session(session)

        return session

    def navigate(self, url: str) -> BrowserAction:
        self._ensure_browser()
        action = self._create_action("navigate", "low", target=url)
        
        if self.page:
            self.page.goto(url)
            action.url_after = self.page.url
            
            session = self._get_or_create_session()
            session.current_url = self.page.url
            session.updated_at = datetime.now(timezone.utc)
            self.store.save_session(session)
            
        return action

    def click(self, selector: str) -> BrowserAction:
        self._ensure_browser()
        action = self._create_action("click", "medium", target=selector)
        
        if self.page:
            self.page.click(selector)
            self.page.wait_for_load_state("networkidle")
            action.url_after = self.page.url
            
            session = self._get_or_create_session()
            session.current_url = self.page.url
            self.store.save_session(session)
            
        return action

    def type(self, selector: str, text: str) -> BrowserAction:
        self._ensure_browser()
        from niyam.governance.common.redaction import contains_secret

        sensitive_terms = ("password", "secret", "token", "key", "credential")
        risk = (
            "high"
            if any(term in selector.lower() for term in sensitive_terms)
            or contains_secret(text)
            else "medium"
        )
        action = self._create_action("type", risk, target=selector, input=text)
        
        if self.page:
            self.page.fill(selector, text)
            action.url_after = self.page.url
            
        return action

    def submit(self, selector: Optional[str] = None) -> BrowserAction:
        self._ensure_browser()
        action = self._create_action("submit", "high", target=selector)
        
        if self.page:
            if selector:
                self.page.press(selector, "Enter")
            else:
                self.page.keyboard.press("Enter")
            self.page.wait_for_load_state("networkidle")
            action.url_after = self.page.url
            
            session = self._get_or_create_session()
            session.current_url = self.page.url
            self.store.save_session(session)
            
        return action

    def screenshot(self, output_path: Optional[Path] = None) -> BrowserAction:
        self._ensure_browser()
        action = self._create_action("screenshot", "low")
        
        if self.page and output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            self.page.screenshot(path=str(output_path))
            action.output = str(output_path)
            action.url_after = self.page.url
            
        return action

    def close(self) -> BrowserSession:
        if self.page:
            self.page.close()
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
            
        session = self._get_or_create_session()
        session.status = "completed"
        session.completed_at = datetime.now(timezone.utc)
        session.updated_at = datetime.now(timezone.utc)
        self.store.save_session(session)
        return session
