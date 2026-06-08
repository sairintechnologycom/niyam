"""Niyam test coverage parser and validator."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional
import xml.etree.ElementTree as ET


def parse_cobertura_coverage(file_path: Path) -> Optional[float]:
    """Parse Cobertura coverage.xml format."""
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        line_rate = float(root.attrib.get("line-rate", 0))
        return line_rate * 100.0
    except Exception:
        return None


def parse_istanbul_coverage(file_path: Path) -> Optional[float]:
    """Parse Istanbul coverage-summary.json format."""
    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
        total = data.get("total", {})
        lines = total.get("lines", {})
        pct = lines.get("pct")
        if pct is not None:
            return float(pct)
        return None
    except Exception:
        return None


def parse_lcov_coverage(file_path: Path) -> Optional[float]:
    """Parse lcov.info format."""
    try:
        content = file_path.read_text(encoding="utf-8")
        total_lines = 0
        hit_lines = 0
        for line in content.splitlines():
            if line.startswith("LF:"):
                total_lines += int(line.split(":")[1])
            elif line.startswith("LH:"):
                hit_lines += int(line.split(":")[1])
        if total_lines == 0:
            return 0.0
        return (hit_lines / total_lines) * 100.0
    except Exception:
        return None


def find_and_parse_coverage(repo_root: Path) -> Optional[dict]:
    """Attempt to find and parse common coverage formats in the repository."""
    # Look for common coverage files
    coverage_files = {
        "coverage.xml": parse_cobertura_coverage,
        "coverage/coverage-summary.json": parse_istanbul_coverage,
        "coverage/lcov.info": parse_lcov_coverage,
    }

    for rel_path, parser in coverage_files.items():
        file_path = repo_root / rel_path
        if file_path.exists():
            pct = parser(file_path)
            if pct is not None:
                return {
                    "file": rel_path,
                    "percentage": round(pct, 2),
                }
    return None
