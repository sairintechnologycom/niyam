"""Niyam governance evidence command shell."""

from __future__ import annotations

from niyam.core.evidence import run_generate_evidence


def execute_generate_evidence(
    from_scan_json: str | None = None,
    fmt: str = "markdown",
    output: str | None = None,
    include: str = "scan,guard,mcp,cost",
    mission_id: str | None = None,
) -> str:
    """Generate evidence report (Experimental)."""
    return run_generate_evidence(
        from_scan_json=from_scan_json,
        fmt=fmt,
        output=output,
        include=include,
        mission_id=mission_id,
    )
