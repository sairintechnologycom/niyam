"""Tests for Phase C Memory Ledger Lineage."""

from pathlib import Path
from niyam.core.memory_ledger.lineage import LocalMemoryLineageStore, create_lineage_event

def test_lineage_store_append_and_iter(tmp_path: Path):
    store_path = tmp_path / "recall-events.jsonl"
    store = LocalMemoryLineageStore(store_path)
    store.init_store()
    
    event = create_lineage_event("created", record_id="mem-1", reason="test")
    store.append(event)
    
    events = list(store.iter_events())
    assert len(events) == 1
    assert events[0].record_id == "mem-1"
    assert events[0].event_type == "created"

def test_trace_command_handles_missing_lineage_file(tmp_path: Path):
    store_path = tmp_path / "non_existent.jsonl"
    store = LocalMemoryLineageStore(store_path)
    
    events = store.get_events_for_record("mem-1")
    assert len(events) == 0
