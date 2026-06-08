"""Niyam memory manager — cross-session learning and project knowledge accumulation."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from rich.console import Console
from rich.panel import Panel

from niyam.core.config import get_niyam_dir

MEMORY_DIR = "memory"


def get_memory_dir(repo_root: Path) -> Path:
    """Get the memory directory path."""
    return get_niyam_dir(repo_root) / MEMORY_DIR


def get_memory_file(repo_root: Path, name: str) -> Path:
    """Get a specific memory file, supporting with or without .md extension."""
    from niyam.core.security import sanitize_filename

    # Strip .md first, sanitize the base, then append .md back
    if name.endswith(".md"):
        base_name = name[:-3]
    else:
        base_name = name

    sanitized_base = sanitize_filename(base_name)
    name = f"{sanitized_base}.md"

    mem_dir = get_memory_dir(repo_root)
    filepath = mem_dir / name
    if not filepath.exists():
        raise FileNotFoundError(
            f"Memory file '{name}' does not exist. "
            f"Available memories: {', '.join(f.stem for f in mem_dir.glob('*.md'))}"
        )
    return filepath


def _append_memory_record(repo_root: Path, memory_file: str, note: str) -> None:
    """Append a structured memory record without changing markdown projections."""
    import fcntl

    records_path = get_memory_dir(repo_root) / "index.jsonl"
    records_path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "id": datetime.now(timezone.utc).strftime("mem-%Y%m%d%H%M%S%f"),
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "type": "note",
        "scope": "project",
        "memory_file": memory_file,
        "source": "manual",
        "confidence": "user-provided",
        "content": note,
    }
    with open(records_path, "a+", encoding="utf-8") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            f.write(json.dumps(record, sort_keys=True) + "\n")
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


def run_memory_show(console: Console) -> None:
    """Display all memory files and their content."""
    from niyam.core.config import find_niyam_root
    from niyam.core.errors import NiyamConfigError

    repo_root = find_niyam_root()
    if not repo_root:
        raise NiyamConfigError("Not a Niyam workspace. Run 'niyam init' first.")
    mem_dir = get_memory_dir(repo_root)

    if not mem_dir.exists():
        console.print(
            "[yellow]No memory directory found. Initialize workspace first.[/]"
        )
        return

    files = sorted(mem_dir.glob("*.md"))
    if not files:
        console.print("[yellow]No memory files found.[/]")
        return

    for filepath in files:
        title = filepath.stem.replace("-", " ").title()
        content = filepath.read_text(encoding="utf-8")
        console.print(
            Panel(content, title=f"[bold cyan]{title}[/]", border_style="cyan")
        )


def run_memory_add(file: str, note: str, console: Console) -> None:
    """Append a note to a memory file."""
    from niyam.core.config import find_niyam_root
    from niyam.core.errors import NiyamConfigError

    repo_root = find_niyam_root()
    if not repo_root:
        raise NiyamConfigError("Not a Niyam workspace. Run 'niyam init' first.")
    try:
        filepath = get_memory_file(repo_root, file)
    except FileNotFoundError as e:
        console.print(f"[bold red]Error:[/] {e}")
        return

    # Check if we need a leading newline
    content = filepath.read_text(encoding="utf-8")
    suffix = "\n" if not content.endswith("\n") else ""

    # Append the note as a bullet point
    filepath.write_text(content + suffix + f"- {note}\n", encoding="utf-8")
    _append_memory_record(repo_root, filepath.name, note)
    console.print(f"[bold green]✓[/] Added note to memory '[cyan]{filepath.name}[/]'.")


def run_memory_clear(file: str, console: Console) -> None:
    """Clear a memory file, resetting it to its title/headers."""
    from niyam.core.config import find_niyam_root
    from niyam.core.errors import NiyamConfigError

    repo_root = find_niyam_root()
    if not repo_root:
        raise NiyamConfigError("Not a Niyam workspace. Run 'niyam init' first.")
    try:
        filepath = get_memory_file(repo_root, file)
    except FileNotFoundError as e:
        console.print(f"[bold red]Error:[/] {e}")
        return

    # Read first line to preserve the title header
    content = filepath.read_text(encoding="utf-8")
    lines = content.split("\n")
    title_line = ""
    for line in lines:
        if line.startswith("#"):
            title_line = line
            break

    if not title_line:
        # Fallback to file name
        title_line = f"# {filepath.stem.replace('-', ' ').title()}"

    initial_content = (
        f"{title_line}\n\n<!-- Cleared memory. Add new entries below. -->\n"
    )
    filepath.write_text(initial_content, encoding="utf-8")
    console.print(f"[bold green]✓[/] Cleared memory '[cyan]{filepath.name}[/]'.")


class CodebaseIndexer:
    """Lightweight local code index stored under `.niyam/db/`."""

    DEFAULT_SKIP_DIRS = {
        ".git",
        ".niyam",
        ".venv",
        "__pycache__",
        "node_modules",
        "dist",
        "build",
        ".pytest_cache",
    }

    TEXT_EXTENSIONS = {
        ".py",
        ".js",
        ".jsx",
        ".ts",
        ".tsx",
        ".md",
        ".toml",
        ".yaml",
        ".yml",
        ".json",
        ".txt",
        ".sh",
        ".css",
        ".html",
    }

    def __init__(self, repo_root: Path, collection_name: str = "codebase") -> None:
        self.repo_root = repo_root.resolve()
        self.db_dir = get_niyam_dir(self.repo_root) / "db"
        self.collection_name = collection_name

    def _iter_files(self) -> list[Path]:
        if (self.repo_root / ".git").exists():
            res = subprocess.run(
                ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=False,
            )
            if res.returncode == 0:
                return [
                    self.repo_root / line
                    for line in res.stdout.splitlines()
                    if self._should_index(self.repo_root / line)
                ]

        files: list[Path] = []
        for root, dirs, filenames in os.walk(self.repo_root):
            dirs[:] = [d for d in dirs if d not in self.DEFAULT_SKIP_DIRS]
            for filename in filenames:
                path = Path(root) / filename
                if self._should_index(path):
                    files.append(path)
        return files

    def _should_index(self, path: Path) -> bool:
        if any(part in self.DEFAULT_SKIP_DIRS for part in path.parts):
            return False
        if path.suffix.lower() not in self.TEXT_EXTENSIONS:
            return False
        try:
            return path.stat().st_size <= 512_000
        except OSError:
            return False

    def chunk_file(self, path: Path, max_chars: int = 4000) -> list[str]:
        text = path.read_text(encoding="utf-8", errors="ignore")
        chunks = []
        for start in range(0, len(text), max_chars):
            chunk = text[start : start + max_chars].strip()
            if chunk:
                chunks.append(chunk)
        return chunks

    def build_index(self) -> int:
        """Index files into Chroma when available, else JSONL fallback."""
        self.db_dir.mkdir(parents=True, exist_ok=True)
        files = self._iter_files()

        try:
            if os.environ.get("NIYAM_DISABLE_CHROMA") == "1":
                raise RuntimeError("Chroma disabled by environment")
            import chromadb

            client = chromadb.PersistentClient(path=str(self.db_dir))
            collection = client.get_or_create_collection(self.collection_name)
            ids: list[str] = []
            docs: list[str] = []
            metas: list[dict[str, str | int]] = []
            for path in files:
                rel = str(path.relative_to(self.repo_root))
                for index, chunk in enumerate(self.chunk_file(path)):
                    ids.append(f"{rel}:{index}")
                    docs.append(chunk)
                    metas.append({"path": rel, "chunk": index})
            if ids:
                collection.upsert(ids=ids, documents=docs, metadatas=metas)
            return len(ids)
        except Exception:
            index_path = self.db_dir / "codebase-index.jsonl"
            count = 0
            with open(index_path, "w", encoding="utf-8") as f:
                for path in files:
                    rel = str(path.relative_to(self.repo_root))
                    for index, chunk in enumerate(self.chunk_file(path)):
                        f.write(
                            json.dumps(
                                {"id": f"{rel}:{index}", "path": rel, "text": chunk}
                            )
                            + "\n"
                        )
                        count += 1
            return count

    def search(self, query: str, k: int = 8) -> list[dict[str, str | float]]:
        """Search indexed code context without creating indexes as a side effect."""
        if not query.strip():
            return []

        if not self.db_dir.exists():
            return []

        try:
            if os.environ.get("NIYAM_DISABLE_CHROMA") == "1":
                raise RuntimeError("Chroma disabled by environment")
            import chromadb

            client = chromadb.PersistentClient(path=str(self.db_dir))
            collection = client.get_or_create_collection(self.collection_name)
            result = collection.query(query_texts=[query], n_results=k)
            docs = result.get("documents", [[]])[0]
            metas = result.get("metadatas", [[]])[0]
            distances = result.get("distances", [[]])[0]
            matches = []
            for doc, meta, distance in zip(docs, metas, distances):
                matches.append(
                    {
                        "path": str(meta.get("path", "")) if meta else "",
                        "text": doc,
                        "score": float(distance),
                    }
                )
            return matches
        except Exception:
            pass

        index_path = self.db_dir / "codebase-index.jsonl"
        if not index_path.exists():
            return []
        terms = {term.lower() for term in query.split() if len(term) >= 3}
        scored: list[tuple[int, dict[str, str | float]]] = []
        try:
            with open(index_path, encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    item = json.loads(line)
                    text = str(item.get("text", ""))
                    haystack = f"{item.get('path', '')}\n{text}".lower()
                    score = sum(haystack.count(term) for term in terms)
                    if score:
                        scored.append(
                            (
                                score,
                                {
                                    "path": str(item.get("path", "")),
                                    "text": text,
                                    "score": float(score),
                                },
                            )
                        )
        except Exception:
            return []
        scored.sort(key=lambda item: item[0], reverse=True)
        return [item for _, item in scored[:k]]
