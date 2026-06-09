"""Models for Memory Ledger."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class MemoryRecord(BaseModel):
    """A structured memory record in the memory ledger."""

    id: str
    type: Literal["semantic", "episodic", "procedural", "preference", "note"]
    content: str
    summary: str | None = None
    scope: Literal["user", "project", "workspace", "organization"] = "project"
    source_kind: Literal[
        "manual", "conversation", "document", "tool_call", "agent_task", "import"
    ] = "manual"
    source_ref: str | None = None
    confidence: float | None = None
    created_at: datetime
    updated_at: datetime | None = None
    expires_at: datetime | None = None
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    schema_version: str = "1.0.0"

    @model_validator(mode="before")
    @classmethod
    def compatibility_parsing(cls, data: Any) -> Any:
        """Parse legacy JSONL records into structured MemoryRecord."""
        if not isinstance(data, dict):
            return data
        data = data.copy()

        # Map 'source' to 'source_kind'
        if "source" in data and "source_kind" not in data:
            data["source_kind"] = data.pop("source")

        # Map 'memory_file' to metadata
        if "memory_file" in data:
            metadata = data.setdefault("metadata", {})
            metadata["memory_file"] = data.pop("memory_file")

        # Handle 'confidence' string "user-provided"
        if "confidence" in data:
            if data["confidence"] == "user-provided":
                data.pop("confidence")
                metadata = data.setdefault("metadata", {})
                metadata["original_confidence"] = "user-provided"
            elif isinstance(data["confidence"], str):
                try:
                    data["confidence"] = float(data["confidence"])
                except ValueError:
                    metadata = data.setdefault("metadata", {})
                    metadata["original_confidence"] = data.pop("confidence")

        return data
