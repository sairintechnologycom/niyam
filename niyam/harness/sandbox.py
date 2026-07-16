"""Restricted command runners for deterministic harness execution."""

from __future__ import annotations

import subprocess
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SandboxLimits:
    memory: str = "512m"
    cpus: str = "1.0"
    pids: int = 64
    timeout_seconds: int = 60


class LocalSandbox:
    """Test-only runner for a copied workspace; it is not a production boundary."""

    def run(self, command: list[str], workspace: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            command,
            cwd=workspace,
            capture_output=True,
            text=True,
            check=False,
        )


class DockerSandbox:
    """Run one command in a short-lived, non-root, network-denied container."""

    _SHELL_TOKENS = {"|", ";", "&&", "||", ">", ">>", "<", "$("}

    def __init__(
        self,
        image: str = "niyam-harness-python:3.13",
        limits: SandboxLimits | None = None,
        user: str | None = None,
    ) -> None:
        self.image = image
        self.limits = limits or SandboxLimits()
        self.user = user or f"{getattr(os, 'getuid', lambda: 65534)()}:{getattr(os, 'getgid', lambda: 65534)()}"

    def run(self, command: list[str], workspace: Path) -> subprocess.CompletedProcess[str]:
        if not command or any(token in self._SHELL_TOKENS for token in command):
            raise ValueError("shell syntax is not permitted in sandbox commands")

        workspace = workspace.resolve()
        docker_command = [
            "docker", "run", "--rm",
            "--network", "none",
            "--read-only",
            "--cap-drop", "ALL",
            "--security-opt", "no-new-privileges:true",
            "--user", self.user,
            "--pids-limit", str(self.limits.pids),
            "--memory", self.limits.memory,
            "--cpus", self.limits.cpus,
            "--tmpfs", "/tmp:rw,nosuid,nodev,noexec,size=64m",
            "--volume", f"{workspace}:/workspace:rw",
            "--workdir", "/workspace",
            self.image,
            *command,
        ]
        return subprocess.run(
            docker_command,
            capture_output=True,
            text=True,
            timeout=self.limits.timeout_seconds,
            check=False,
        )
