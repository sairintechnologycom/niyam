"""Niyam governance scan command shell."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from niyam.core.scan import run_scanner_checks


def execute_scan(
    path: str = ".",
    profile: str = "startup",
    custom_rules_path: Path | None = None,
    baseline_path: Path | None = None,
    create_baseline_path: Path | None = None,
) -> dict[str, Any]:
    """Execute repository scan for production readiness (Experimental)."""
    scan_path = Path(path).resolve()
    return run_scanner_checks(
        scan_path,
        profile=profile,
        custom_rules_path=custom_rules_path,
        baseline_path=baseline_path,
        create_baseline_path=create_baseline_path,
    )
