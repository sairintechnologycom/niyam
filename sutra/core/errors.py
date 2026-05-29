"""Sutra custom exception types and error codes."""

from __future__ import annotations


class SutraError(Exception):
    """Base exception for all Sutra errors."""

    code: int = 1


class SutraConfigError(SutraError):
    """Raised when configuration files are missing, malformed, or invalid."""

    code = 10


class SutraSecurityError(SutraError):
    """Raised when a security policy is violated or verification fails."""

    code = 20


class SutraExecutionError(SutraError):
    """Raised when a task or command execution fails or times out."""

    code = 30
