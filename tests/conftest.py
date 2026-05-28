"""Test fixtures for Sutra."""

from __future__ import annotations

import os
from pathlib import Path

import pytest


@pytest.fixture
def tmp_repo(tmp_path: Path) -> Path:
    """Create a temporary directory simulating a git repo."""
    # Initialize a minimal git repo
    os.system(f"cd {tmp_path} && git init -q && git config user.email 'test@test.com' && git config user.name 'Test'")
    return tmp_path


@pytest.fixture
def sutra_repo(tmp_repo: Path) -> Path:
    """Create a temporary repo with sutra initialized."""
    from sutra.core.init import run_init
    from rich.console import Console

    console = Console(quiet=True)
    original_dir = os.getcwd()
    os.chdir(tmp_repo)
    try:
        run_init(profile="fullstack", runtime=None, dry_run=False, force=False, console=console)
    finally:
        os.chdir(original_dir)
    return tmp_repo
