"""Sutra pack manager — manage modular skill/agent/command bundles."""

from __future__ import annotations

from pathlib import Path
import yaml
from rich.console import Console

from sutra.core.config import (
    get_sutra_dir,
    load_sutra_config,
    save_sutra_config,
)

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
PACKS_DIR = TEMPLATES_DIR / "packs"


def get_pack_dir(name: str) -> Path:
    """Get the pack template directory."""
    pack_dir = PACKS_DIR / name
    if not pack_dir.exists() or not pack_dir.is_dir():
        raise ValueError(f"Pack '{name}' not found in templates.")
    return pack_dir


def load_pack_manifest(name: str) -> dict:
    """Load the pack.yaml manifest."""
    pack_dir = get_pack_dir(name)
    manifest_path = pack_dir / "pack.yaml"
    if not manifest_path.exists():
        raise ValueError(f"Pack '{name}' is missing pack.yaml manifest.")
    with open(manifest_path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def list_packs(repo_root: Path) -> list[dict]:
    """List all available packs with their installation status."""
    try:
        config = load_sutra_config(repo_root)
        installed_packs = set(config.packs)
    except Exception:
        installed_packs = set()

    packs = []
    if PACKS_DIR.exists():
        for d in sorted(PACKS_DIR.iterdir()):
            if d.is_dir() and (d / "pack.yaml").exists():
                try:
                    manifest = load_pack_manifest(d.name)
                    packs.append(
                        {
                            "name": d.name,
                            "version": manifest.get("version", "0.1.0"),
                            "description": manifest.get("description", ""),
                            "installed": d.name in installed_packs,
                        }
                    )
                except Exception:
                    pass
    return packs


def add_pack(
    repo_root: Path, name: str, force: bool = False, console: Console | None = None
) -> None:
    """Install a pack into the .sutra/ directory."""
    pack_dir = get_pack_dir(name)
    load_pack_manifest(name)
    sutra_dir = get_sutra_dir(repo_root)

    if not sutra_dir.exists():
        raise FileNotFoundError(
            "Sutra workspace is not initialized. Run `sutra init` first."
        )

    config = load_sutra_config(repo_root)

    # 1. Collect files to copy (exclude pack.yaml)
    files_to_copy = []
    for p in pack_dir.rglob("*"):
        if p.is_file() and p.name != "pack.yaml":
            rel_path = p.relative_to(pack_dir)
            target_path = sutra_dir / rel_path
            files_to_copy.append((p, target_path, rel_path))

    # 2. Conflict detection
    if not force:
        conflicts = []
        for src, dst, rel in files_to_copy:
            if dst.exists():
                # Check if it was written by the same pack. If it has the header, maybe it's fine,
                # but if we are adding it and not forcing, let's treat any pre-existing file as a conflict
                # unless its content is identical.
                try:
                    existing_content = dst.read_text(encoding="utf-8")
                    # Read target content
                    content = src.read_text(encoding="utf-8")
                    # Construct expected content with header
                    header = (
                        f"<!-- pack: {name} -->\n\n"
                        if dst.suffix == ".md"
                        else f"# pack: {name}\n\n"
                    )
                    expected_content = header + content
                    if existing_content != expected_content:
                        conflicts.append(str(rel))
                except Exception:
                    conflicts.append(str(rel))

        if conflicts:
            raise ValueError(
                "Conflict detected! The following files already exist in .sutra/:\n"
                + "\n".join(f"  - {c}" for c in conflicts)
                + "\nUse --force to overwrite them."
            )

    # 3. Copy files and prepend header comment
    for src, dst, rel in files_to_copy:
        dst.parent.mkdir(parents=True, exist_ok=True)
        content = src.read_text(encoding="utf-8")

        # Prepend header for traceability
        if dst.suffix == ".md":
            header = f"<!-- pack: {name} -->\n\n"
        elif dst.suffix in (".yaml", ".yml"):
            header = f"# pack: {name}\n\n"
        else:
            header = f"# pack: {name}\n\n"

        dst.write_text(header + content, encoding="utf-8")

    # 4. Update config
    if name not in config.packs:
        config.packs.append(name)
        save_sutra_config(config, repo_root)


def remove_pack(repo_root: Path, name: str, console: Console | None = None) -> None:
    """Remove a pack from the .sutra/ directory."""
    sutra_dir = get_sutra_dir(repo_root)
    if not sutra_dir.exists():
        raise FileNotFoundError("Sutra workspace is not initialized.")

    config = load_sutra_config(repo_root)
    if name not in config.packs:
        raise ValueError(f"Pack '{name}' is not installed.")

    pack_dir = get_pack_dir(name)

    # Walk pack to find what files were added
    deleted_files = 0
    for p in pack_dir.rglob("*"):
        if p.is_file() and p.name != "pack.yaml":
            rel_path = p.relative_to(pack_dir)
            target_path = sutra_dir / rel_path
            if target_path.exists():
                # Verify header to avoid deleting user modifications if possible, or just delete it
                try:
                    content = target_path.read_text(encoding="utf-8")
                    header_md = f"<!-- pack: {name} -->"
                    header_yaml = f"# pack: {name}"
                    if content.startswith(header_md) or content.startswith(header_yaml):
                        target_path.unlink()
                        deleted_files += 1
                    else:
                        # Fallback: if force or just regular remove, let's delete it anyway
                        target_path.unlink()
                        deleted_files += 1
                except Exception:
                    target_path.unlink()
                    deleted_files += 1

    # Clean up empty parent directories
    for p in sorted(pack_dir.rglob("*"), key=lambda x: len(x.parts), reverse=True):
        if p.is_dir() and p.name != "pack.yaml":
            rel_path = p.relative_to(pack_dir)
            target_path = sutra_dir / rel_path
            if target_path.exists() and target_path.is_dir():
                try:
                    # Only remove if empty
                    if not any(target_path.iterdir()):
                        target_path.rmdir()
                except Exception:
                    pass

    # Update config
    config.packs.remove(name)
    save_sutra_config(config, repo_root)


def sync_packs(repo_root: Path, console: Console | None = None) -> None:
    """Sync all packs listed in sutra.yaml by re-applying them."""
    config = load_sutra_config(repo_root)
    for name in config.packs:
        add_pack(repo_root, name, force=True, console=console)
