"""Niyam SaaS client — communicate with the centralized control plane."""

from __future__ import annotations

import json
import logging
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any, Optional

from niyam.core.config import load_niyam_config

logger = logging.getLogger(__name__)


class SaaSClient:
    """Simple HTTP client for Niyam Dashboard interactions."""

    def __init__(self, repo_root: Path | None = None):
        config = load_niyam_config(repo_root)
        self.base_url = config.saas.base_url.rstrip("/")
        self.api_key = config.saas.api_key
        self.project_id = config.saas.project_id
        self.enabled = config.saas.enabled

    def _request(
        self, method: str, path: str, data: Any = None, headers: dict | None = None
    ) -> dict:
        """Perform an authenticated HTTP request."""
        if not self.enabled:
            raise RuntimeError("SaaS integration is disabled in niyam.yaml")
        if not self.api_key:
            raise RuntimeError("NIYAM_API_KEY (saas.api_key) is not configured")

        url = f"{self.base_url}/{path.lstrip('/')}"
        
        req_headers = {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key,
            "User-Agent": "Niyam-CLI/0.4.0",
        }
        if headers:
            req_headers.update(headers)

        body = None
        if data is not None:
            body = json.dumps(data).encode("utf-8")

        req = urllib.request.Request(url, data=body, headers=req_headers, method=method)

        try:
            with urllib.request.urlopen(req) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8")
            try:
                msg = json.loads(err_body).get("detail", str(e))
            except Exception:
                msg = str(e)
            logger.error("SaaS request failed (%d): %s", e.code, msg)
            raise RuntimeError(f"Dashboard error: {msg}")
        except Exception as e:
            logger.error("Failed to connect to Niyam Dashboard: %s", e)
            raise RuntimeError(f"Connection failed: {e}")

    def upload_report(self, report_data: dict) -> dict:
        """Upload an evidence report to the dashboard."""
        if not self.project_id:
            raise RuntimeError("saas.project_id is not configured")
            
        path = f"projects/{self.project_id}/reports"
        return self._request("POST", path, data=report_data)

    def trigger_webhook(self, event_type: str, payload: dict) -> dict:
        """Fire a webhook event to the control plane."""
        path = "webhooks/notify"
        data = {
            "type": event_type,
            "project_id": self.project_id,
            "payload": payload
        }
        return self._request("POST", path, data=data)

    def ping(self) -> dict:
        """Verify API connectivity and key validity."""
        return self._request("GET", "auth/ping")
