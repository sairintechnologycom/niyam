"""Opt-in proof that the configured Docker sandbox can execute a non-root command."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from niyam.harness.sandbox import DockerSandbox


pytestmark = pytest.mark.skipif(
    os.environ.get("NIYAM_RUN_DOCKER_E2E") != "1",
    reason="set NIYAM_RUN_DOCKER_E2E=1 after building the harness image",
)


def test_docker_sandbox_has_no_network_and_runs_as_non_root(tmp_path: Path) -> None:
    sandbox = DockerSandbox()
    result = sandbox.run(
        ["python", "-c", "import os, socket; assert os.geteuid() != 0; socket.create_connection(('example.com', 80), 1)"],
        tmp_path,
    )

    assert result.returncode != 0
