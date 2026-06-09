"""Export and Import manifest for memory records."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel
import yaml

from niyam.core.memory_ledger.models import MemoryRecord
from niyam.core.memory_ledger.schemas import MemoryManifest


def export_manifest(records: list[MemoryRecord], output_path: Path, fmt: Literal["json", "yaml"] = "json") -> None:
    """Export records to a manifest file in JSON or YAML format."""
    manifest = MemoryManifest(records=records)
    
    if fmt == "json":
        data = manifest.model_dump_json(exclude_none=True, indent=2)
        output_path.write_text(data, encoding="utf-8")
    elif fmt == "yaml":
        # Dump to dict first to get basic types (like str for datetime) handled 
        # or use standard yaml dump with dict
        data_dict = manifest.model_dump(exclude_none=True, mode="json")
        with open(output_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(data_dict, f, sort_keys=False)
    else:
        raise ValueError(f"Unsupported format: {fmt}")


def import_manifest(input_path: Path) -> list[MemoryRecord]:
    """Import records from a JSON or YAML manifest file."""
    if input_path.suffix in (".yaml", ".yml"):
        with open(input_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            manifest = MemoryManifest.model_validate(data)
            return manifest.records
    elif input_path.suffix == ".json":
        data = input_path.read_text(encoding="utf-8")
        manifest = MemoryManifest.model_validate_json(data)
        return manifest.records
    else:
        raise ValueError("Unsupported file extension. Must be .json, .yaml, or .yml")
