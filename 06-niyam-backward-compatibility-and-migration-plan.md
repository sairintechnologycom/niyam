# Backward Compatibility & Migration Plan

This document details how the new governance, scanning, and FinOps features (introduced in v0.4.0+) integrate into existing Niyam workspaces without interrupting current workflows, product behaviors, or commands.

---

## 1. Compatibility Matrix
To ensure a smooth transition, Niyam must remain fully backward-compatible with repositories initialized under v0.3.x.

| Workspace State | Impact of Upgrade | Necessary Action |
| --- | --- | --- |
| **v0.3.x Workspace** (No governance configuration) | **None.** Existing commands like `niyam init`, `niyam sync`, `niyam doctor`, and `niyam context` function exactly as before without errors. | None. Missing configurations default to inactive states. |
| **Legacy Config file** (`niyam.yaml` v0.1.0) | **Automatic Fallback.** The parser loads config files, auto-injecting missing `guard` settings with `enabled: false`. | Run `niyam doctor` to auto-upgrade the workspace schema format. |
| **Missing local Databases** (`mcp-registry.json` or `pricing.json`) | **Dynamic Initialization.** Missing registry files are generated automatically on their first corresponding command call. | None. Files initialize silently. |

### Preserved CLI Behaviors
* **`niyam init`**: Continues to build standard workspace layouts. If run in an upgraded environment, it appends default governance settings to `niyam.yaml`.
* **`niyam doctor`**: Validates the workspace syntax. If the schema version is outdated, it alerts the developer and prompts for a safe schema upgrade.

---

## 2. Configuration Schema Migration
When a repository is upgraded, the `niyam.yaml` file is updated to include the governance keys.

### Schema Transformation Workflow

```
[ v0.3.x niyam.yaml ]
      │
      ▼  (Auto-detected during CLI run or niyam doctor)
[ Check schema version ]
      │
      ├─► Version >= 0.4.0: OK (Skip)
      │
      └─► Version < 0.4.0: 
            1. Inject 'guard:' block
            2. Set 'guard.enabled: false'
            3. Set 'guard.careful: false'
            4. Set 'guard.frozen_paths: []'
            5. Update 'version' to '0.4.0'
```

#### Code Migration Precedent (from `niyam/core/migrate.py`)
```python
def migrate_yaml_schema(content: dict) -> dict:
    """Migrates v0.1.0/v0.3.x configurations to v0.4.0 schema format."""
    if "guard" not in content:
        content["guard"] = {
            "enabled": False,
            "careful": False,
            "frozen_paths": []
        }
    content["version"] = "0.4.0"
    return content
```

---

## 3. Fallback & Resilience Mechanisms
Niyam uses defensive coding patterns to prevent missing or corrupt metadata files from causing CLI crashes.

### A. Missing `pricing.json` Fallback
If `.niyam/pricing.json` is deleted or unparseable:
1. Niyam logs a debug message to standard error: `[WARN] Pricing rate file missing or corrupt. Falling back to default model rates.`
2. The engine loads the internal `DEFAULT_PRICING` dictionary (containing standard rates for Claude, GPT, and Gemini).
3. The CLI execution proceeds without interruption.

### B. Missing `mcp-registry.json` Fallback
If `.niyam/mcp-registry.json` is missing:
1. The registry engine instantiates an empty registry representation in memory: `{"schema_version": "1.0.0", "tools": {}}`.
2. Common native CLI commands (such as `bash`, `git`, and `grep`) are auto-registered with default low/medium risk settings.
3. No file write occurs until a tool registration command is explicitly triggered.

### C. Corrupt JSONL Database Files
If log ledgers (`guard-actions.jsonl` or `cost-events.jsonl`) contain corrupt lines:
1. The file parser opens the logs using standard stream readers.
2. It processes lines within `try/except` blocks. If an individual line fails JSON parsing, Niyam discards it and continues parsing subsequent lines.
3. A summary of skipped corrupt records is printed in `--verbose` mode.

---

## 4. API & CLI Versioning Policy
Niyam adheres to Semantic Versioning (SemVer 2.0.0) policies:

* **Major Releases (v1.0.0)**: Reserved for breaking CLI options changes or complete config model rewrites.
* **Minor Releases (v0.4.0)**: Used for adding new governance features (such as `scan`, `guard`, `mcp`, `cost`, `evidence`) that maintain backward compatibility.
* **Patch Releases (v0.4.1)**: Fixes bugs, expands regex checks, or updates default model rates.
