"""Tests for the niyam brainstorm command."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest
from rich.console import Console

from niyam.core.brainstorm import clean_markdown, run_brainstorm
from niyam.core.config import get_niyam_dir


def test_clean_markdown():
    text = "```markdown\n# Hello World\n```"
    assert clean_markdown(text) == "# Hello World"

    text_no_lang = "```\n# Hello World\n```"
    assert clean_markdown(text_no_lang) == "# Hello World"

    text_plain = "# Hello World"
    assert clean_markdown(text_plain) == "# Hello World"


def test_run_brainstorm_fallback(tmp_repo: Path, monkeypatch):
    """Test brainstorming when runtime is missing or fails, falling back to templates."""
    os.chdir(tmp_repo)
    console = Console(quiet=True)

    # Mock inputs:
    # 1. Choose niche: 2 (Tutors/Learning Platform)
    inputs = iter(["2"])
    monkeypatch.setattr("builtins.input", lambda *args: next(inputs))
    # Mock Prompt.ask for the niche choice
    monkeypatch.setattr("rich.prompt.Prompt.ask", lambda *args, **kwargs: "2")

    # Mock shutil.which to say no runtime is available (return None, not False)
    monkeypatch.setattr(shutil, "which", lambda cmd: None)

    run_brainstorm(runtime="claude", console=console)

    # Verify files created
    prd_path = tmp_repo / "PRD.md"
    roadmap_path = tmp_repo / "ROADMAP.md"

    assert prd_path.exists()
    assert roadmap_path.exists()

    prd_content = prd_path.read_text(encoding="utf-8")
    roadmap_content = roadmap_path.read_text(encoding="utf-8")

    assert "Tutors/Learning Platform" in prd_content
    assert "MVP Core Features" in roadmap_content

    # Niyam workspace should be initialized
    assert get_niyam_dir(tmp_repo).exists()


def test_run_brainstorm_success(tmp_repo: Path, monkeypatch):
    """Test brainstorming success path with mocked runtime output."""
    os.chdir(tmp_repo)
    console = Console(quiet=True)

    # Mock inputs: niche = 1 (Photographers SaaS)
    monkeypatch.setattr("rich.prompt.Prompt.ask", lambda *args, **kwargs: "1")

    # Mock shutil.which to find the runtime (return a path string)
    monkeypatch.setattr(shutil, "which", lambda cmd: "/usr/bin/claude")

    # Mock subprocess.run
    call_count = 0

    def mock_run(cmd, *args, **kwargs):
        nonlocal call_count
        call_count += 1
        
        # Determine if it's the first call (questions), second (suggestions), or third (generation)
        prompt = cmd[2] if len(cmd) > 2 else ""
        
        if "generate 3 to 5 critical clarifying questions" in prompt:
            # First call: questions
            stdout = "1. Question One?\n2. Question Two?\n3. Question Three?\n"
            return subprocess.CompletedProcess(cmd, returncode=0, stdout=stdout, stderr="")
        elif "generate a concise suggested answer" in prompt:
            # Second call: suggestions
            stdout = "1. Suggested Answer One\n2. Suggested Answer Two\n3. Suggested Answer Three\n"
            return subprocess.CompletedProcess(cmd, returncode=0, stdout=stdout, stderr="")
        else:
            # Third call: generation
            stdout = """# Mock PRD
## Overview
Photographers SaaS project description.

=== ROADMAP.md ===
# Mock Roadmap
## Phase 1
Setup template files.
"""
            return subprocess.CompletedProcess(cmd, returncode=0, stdout=stdout, stderr="")

    monkeypatch.setattr(subprocess, "run", mock_run)

    run_brainstorm(runtime="claude", console=console)

    assert call_count == 3

    # Verify generated files
    prd_path = tmp_repo / "PRD.md"
    roadmap_path = tmp_repo / "ROADMAP.md"

    assert prd_path.exists()
    assert roadmap_path.exists()

    assert "Mock PRD" in prd_path.read_text(encoding="utf-8")
    assert "Mock Roadmap" in roadmap_path.read_text(encoding="utf-8")

    # Workspace should be initialized
    assert get_niyam_dir(tmp_repo).exists()


def test_run_brainstorm_overwrite_cancel(tmp_repo: Path, monkeypatch):
    """Test that brainstorming aborts if files exist and user cancels overwrite."""
    os.chdir(tmp_repo)
    console = Console(quiet=True)

    # Pre-create files
    prd_path = tmp_repo / "PRD.md"
    prd_path.write_text("existing prd", encoding="utf-8")

    # Mock Confirm.ask to return False (do not overwrite)
    monkeypatch.setattr("rich.prompt.Confirm.ask", lambda *args, **kwargs: False)

    with pytest.raises(SystemExit) as excinfo:
        run_brainstorm(runtime="claude", console=console)

    assert excinfo.value.code == 0
    assert prd_path.read_text(encoding="utf-8") == "existing prd"


def test_run_brainstorm_overwrite_accept(tmp_repo: Path, monkeypatch):
    """Test that brainstorming proceeds and overwrites if files exist and user accepts."""
    os.chdir(tmp_repo)
    console = Console(quiet=True)

    # Pre-create files
    prd_path = tmp_repo / "PRD.md"
    prd_path.write_text("existing prd", encoding="utf-8")

    # Mock inputs/Prompt.ask
    monkeypatch.setattr("rich.prompt.Prompt.ask", lambda *args, **kwargs: "2")
    # Mock Confirm.ask to return True (overwrite)
    monkeypatch.setattr("rich.prompt.Confirm.ask", lambda *args, **kwargs: True)
    # Mock shutil.which to say no runtime
    monkeypatch.setattr(shutil, "which", lambda cmd: None)

    run_brainstorm(runtime="claude", console=console)

    assert prd_path.read_text(encoding="utf-8") != "existing prd"
    assert "Tutors/Learning Platform" in prd_path.read_text(encoding="utf-8")


def test_run_brainstorm_with_repo_context(tmp_repo: Path, monkeypatch):
    """Test that repository context is scanned and injected into prompts."""
    os.chdir(tmp_repo)
    console = Console(quiet=True)

    # Mock repository scan to return FastAPI framework
    monkeypatch.setattr("niyam.core.brainstorm._scan_repo", lambda repo_root: {
        "languages": ["Python"],
        "frameworks": ["FastAPI"],
        "package_managers": ["pip"],
        "validation": {},
        "source_dirs": [],
        "test_dirs": [],
        "ci": [],
        "dependency_versions": [],
        "db_schema": [],
        "api_routes": [],
        "env_vars": [],
        "readme_summary": ""
    })

    monkeypatch.setattr("rich.prompt.Prompt.ask", lambda *args, **kwargs: "1")
    monkeypatch.setattr(shutil, "which", lambda cmd: "/usr/bin/claude")

    prompts_received = []

    def mock_run(cmd, *args, **kwargs):
        # Capture prompts sent to the runtime
        if len(cmd) > 2:
            prompts_received.append(cmd[2])
        return subprocess.CompletedProcess(cmd, returncode=0, stdout="1. Question?\n\n=== ROADMAP.md ===\n# Content", stderr="")

    monkeypatch.setattr(subprocess, "run", mock_run)

    run_brainstorm(runtime="claude", console=console)
    # Verify that prompts received contain the scanned repo context (FastAPI)
    assert len(prompts_received) > 0
    for prompt in prompts_received:
        assert "FastAPI" in prompt
        assert "Python" in prompt


def test_run_brainstorm_interactive_refine(tmp_repo: Path, monkeypatch):
    """Test brainstorming refinement loop when user chooses 'refine' and then 'accept'."""
    os.chdir(tmp_repo)
    console = Console(quiet=True)

    # Mock runtime to be found
    monkeypatch.setattr(shutil, "which", lambda cmd: "/usr/bin/claude")
    monkeypatch.setattr("niyam.core.brainstorm.run_mission_plan", lambda *args, **kwargs: None)

    # Capture subprocess runs
    subprocess_calls = []

    def mock_run(cmd, *args, **kwargs):
        subprocess_calls.append(cmd)
        prompt = cmd[2] if len(cmd) > 2 else ""
        if "generate 3 to 5 critical clarifying questions" in prompt:
            stdout = "1. Question One?\n2. Question Two?\n3. Question Three?\n"
            return subprocess.CompletedProcess(cmd, returncode=0, stdout=stdout, stderr="")
        elif "generate a concise suggested answer" in prompt:
            stdout = "1. S1\n2. S2\n3. S3\n"
            return subprocess.CompletedProcess(cmd, returncode=0, stdout=stdout, stderr="")
        else:
            stdout = """# Mock PRD
## Key Features
- Feature A
- Feature B
=== ROADMAP.md ===
# Mock Roadmap
## Phase 1
- Step A
"""
            return subprocess.CompletedProcess(cmd, returncode=0, stdout=stdout, stderr="")

    monkeypatch.setattr(subprocess, "run", mock_run)

    # Stateful prompts
    prompts_queue = iter([
        "1",                           # Niche choice
        "refine",                      # First preview choice
        "Make features more detailed", # Refinement feedback
        "accept"                       # Second preview choice
    ])
    monkeypatch.setattr("rich.prompt.Prompt.ask", lambda *args, **kwargs: next(prompts_queue))

    # Stateful inputs for Q&A (first is for multiline raw notes step, then answers to Qs)
    inputs_queue = iter(["done", "", "", ""])
    monkeypatch.setattr("builtins.input", lambda *args: next(inputs_queue))

    # Temporarily remove pytest from sys.modules to simulate interactive mode
    import sys
    pytest_module = sys.modules.pop("pytest", None)
    try:
        run_brainstorm(runtime="claude", console=console)
    finally:
        if pytest_module:
            sys.modules["pytest"] = pytest_module

    # We expect:
    # 1. Questions generation
    # 2. Suggestions generation
    # 3. Generation 1
    # 4. Generation 2 (with refinement)
    assert len(subprocess_calls) == 4

    # The last generation should have included the refinement notes
    last_generation_prompt = subprocess_calls[-1][2]
    assert "Make features more detailed" in last_generation_prompt

    # Files should be written correctly
    assert (tmp_repo / "PRD.md").exists()
    assert (tmp_repo / "ROADMAP.md").exists()


def test_run_brainstorm_interactive_skip(tmp_repo: Path, monkeypatch):
    """Test brainstorming preview loop when user chooses 'skip'."""
    os.chdir(tmp_repo)
    console = Console(quiet=True)

    monkeypatch.setattr(shutil, "which", lambda cmd: "/usr/bin/claude")
    monkeypatch.setattr("niyam.core.brainstorm.run_mission_plan", lambda *args, **kwargs: None)

    subprocess_calls = []

    def mock_run(cmd, *args, **kwargs):
        subprocess_calls.append(cmd)
        prompt = cmd[2] if len(cmd) > 2 else ""
        if "generate 3 to 5 critical clarifying questions" in prompt:
            stdout = "1. Question One?\n2. Question Two?\n3. Question Three?\n"
            return subprocess.CompletedProcess(cmd, returncode=0, stdout=stdout, stderr="")
        elif "generate a concise suggested answer" in prompt:
            stdout = "1. S1\n2. S2\n3. S3\n"
            return subprocess.CompletedProcess(cmd, returncode=0, stdout=stdout, stderr="")
        else:
            stdout = """# Mock PRD
## Key Features
- Feature A
=== ROADMAP.md ===
# Mock Roadmap
## Phase 1
- Step A
"""
            return subprocess.CompletedProcess(cmd, returncode=0, stdout=stdout, stderr="")

    monkeypatch.setattr(subprocess, "run", mock_run)

    # Stateful prompts
    prompts_queue = iter([
        "1",                           # Niche choice
        "skip"                         # Choose to skip
    ])
    monkeypatch.setattr("rich.prompt.Prompt.ask", lambda *args, **kwargs: next(prompts_queue))

    # Stateful inputs for Q&A (first is for multiline raw notes step, then answers to Qs)
    inputs_queue = iter(["done", "", "", ""])
    monkeypatch.setattr("builtins.input", lambda *args: next(inputs_queue))

    # Temporarily remove pytest from sys.modules to simulate interactive mode
    import sys
    pytest_module = sys.modules.pop("pytest", None)
    try:
        run_brainstorm(runtime="claude", console=console)
    finally:
        if pytest_module:
            sys.modules["pytest"] = pytest_module

    # We expect:
    # 1. Questions generation
    # 2. Suggestions generation
    # 3. Generation 1
    assert len(subprocess_calls) == 3

    assert (tmp_repo / "PRD.md").exists()
    assert (tmp_repo / "ROADMAP.md").exists()

