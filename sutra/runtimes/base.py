"""Abstract base class for runtime adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from rich.console import Console


class RuntimeAdapter(ABC):
    """Base class for all runtime adapters.

    A runtime adapter projects the canonical .sutra/ source of truth
    into runtime-specific files (e.g., CLAUDE.md, .claude/, AGENTS.md).
    """

    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root
        self.sutra_dir = repo_root / ".sutra"

    @property
    @abstractmethod
    def name(self) -> str:
        """Runtime name (e.g., 'claude', 'codex')."""
        ...

    @abstractmethod
    def sync(self, console: Console) -> None:
        """Generate/update runtime-specific files from .sutra/."""
        ...

    @abstractmethod
    def clean(self, console: Console) -> None:
        """Remove all generated runtime files."""
        ...

    def _read_sutra_file(self, rel_path: str) -> str | None:
        """Read a file from .sutra/ if it exists."""
        fpath = self.sutra_dir / rel_path
        if fpath.exists():
            return fpath.read_text(encoding="utf-8")
        return None

    def _list_sutra_dir(self, rel_path: str) -> list[Path]:
        """List files in a .sutra/ subdirectory."""
        dpath = self.sutra_dir / rel_path
        if dpath.is_dir():
            return sorted(dpath.iterdir())
        return []
