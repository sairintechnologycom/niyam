from __future__ import annotations

from pathlib import Path
from typing import List
import json


def get_runtimes() -> List[str]:
    return ["claude", "codex", "gemini", "antigravity"]


def get_loop_specs() -> List[str]:
    from niyam.core.config import find_niyam_root
    root = find_niyam_root() or Path.cwd()
    specs = []
    for d in [root / "loops", root / ".niyam" / "loops"]:
        if d.exists() and d.is_dir():
            for file in d.glob("*.yaml"):
                # Return relative paths from current working directory or just filenames
                try:
                    rel_path = file.relative_to(Path.cwd())
                    specs.append(str(rel_path))
                except ValueError:
                    specs.append(str(file))
            for file in d.glob("*.yml"):
                try:
                    rel_path = file.relative_to(Path.cwd())
                    specs.append(str(rel_path))
                except ValueError:
                    specs.append(str(file))
    return specs


def get_recent_loop_runs() -> List[str]:
    from niyam.core.config import find_niyam_root
    root = find_niyam_root() or Path.cwd()
    run_ids = []
    
    # Check .niyam/evidence/loops, .sutra/evidence/loops, and .niyam/runs
    for loops_dir in [
        root / ".niyam" / "evidence" / "loops",
        root / ".sutra" / "evidence" / "loops",
        root / ".niyam" / "runs",
    ]:
        if loops_dir.is_dir():
            for p in loops_dir.glob("**/run.json"):
                try:
                    with open(p, encoding="utf-8") as f:
                        run_data = json.load(f)
                        if "id" in run_data:
                            run_ids.append(run_data["id"])
                except Exception:
                    continue

    # De-duplicate while maintaining some order
    return list(dict.fromkeys(run_ids))
