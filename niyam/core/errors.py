"""Niyam custom exception types and error codes."""

from __future__ import annotations


class NiyamError(Exception):
    """Base exception for all Niyam errors."""

    code: int = 1


class NiyamConfigError(NiyamError):
    """Raised when configuration files are missing, malformed, or invalid."""

    code = 10


class NiyamSecurityError(NiyamError):
    """Raised when a security policy is violated or verification fails."""

    code = 20


class NiyamExecutionError(NiyamError):
    """Raised when a task or command execution fails or times out."""

    code = 30
