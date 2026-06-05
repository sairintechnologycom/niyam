# Backward Compatibility & Migration Plan

This document details how the new governance, scanning, and FinOps features (introduced in v0.4.0+) integrate into existing Niyam workspaces without interrupting current workflows, product behaviors, or commands.

---

## 1. Existing Capabilities Protected

To preserve developer velocity and workspace health, Niyam ensures all legacy core capabilities are fully protected. The following existing workflows must remain entirely unaffected:
* **`niyam init`**: Continues to construct standard workspace structures. If run in legacy configurations, it functions normally without demanding governance properties.
* **`niyam sync`**: Continues to sync contexts and workspace mappings without referencing or requiring active governance modules.
* **`niyam doctor`**: Validates the workspace syntax. Legacy config versions are loaded, validated, and flagged with a warning rather than throwing system errors.
* **`niyam context`**: Retrieves, formats, and structures markdown context for agents, ignoring guardrails or logs unless specifically queried.

---

## 2. Compatibility Contract

Niyam commits to a strict backward compatibility contract during the v0.4.x minor release cycle:
1. **Additive Schema Updates:** New configuration parameters (e.g. `guard`, `pricing`) are entirely optional. If missing, they fallback to inactive states or default behaviors.
2. **Crash Prevention:** Missing, corrupt, or legacy configurations inside `.niyam/` must never crash the CLI.
3. **No Retroactive Locks:** Upgrading the Niyam package will not write configuration overrides to user files without developer authorization or running explicit init commands.

---

## 3. Configuration Schema Migration

When a legacy repository is upgraded to v0.4.x+, the config parser dynamically migrates the schema format in memory or alerts the user to save the upgraded structure.

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

### Code Migration Precedent
Config migration logic is implemented in [migrate.py](file:///Users/bhushan/Documents/Projects/sutra/niyam/core/migrate.py):
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

## 4. Fallback & Resilience Mechanisms

* **Missing `pricing.json` Fallback:** If `.niyam/pricing.json` is missing, Niyam uses the internal default pricing dictionary, logging a debug notice: `[WARN] Pricing rate file missing or corrupt. Falling back to default model rates.`
* **Missing `mcp-registry.json` Fallback:** If `.niyam/mcp-registry.json` is absent, an empty in-memory registry (`{"schema_version": "1.0.0", "tools": {}}`) is loaded, ensuring tools can be used or registered dynamically without failure.
* **Corrupt JSONL Database Files:** If log ledgers contain corrupted entries, the parser skips them, continuing execution instead of crashing the process.

---

## 5. Rollback Plan

In the event that an upgrade to v0.4.x causes unexpected build failures, follow these steps to revert the workspace and package:

1. **Backup Config:** Save a copy of your current `.niyam/niyam.yaml` before running migration tools.
2. **Revert Configuration File:** Revert any changes to `niyam.yaml` or restore the backup copy to return it to the v0.3.x structure (e.g., removing the `guard` block and reverting the version key to `0.3.0`).
3. **Clean Up Database Files:** Delete any automatically generated governance metadata files:
   ```bash
   rm -f .niyam/mcp-registry.json
   rm -f .niyam/pricing.json
   rm -rf .niyam/logs/
   ```
4. **Downgrade Niyam Package:** Downgrade the Niyam CLI package via pip to the previous stable release:
   ```bash
   pip install niyam==0.3.0
   ```

---

## 6. Regression Testing Suite

To ensure that backward compatibility remains intact, the automated test suite includes dedicated regression tests:
* **Legacy Configuration Parsing:** [test_migration_and_deprecation.py](file:///Users/bhushan/Documents/Projects/sutra/tests/test_migration_and_deprecation.py) asserts that older `niyam.yaml` shapes are parsed correctly and migrated seamlessly.
* **E2E Compatibility Scenario:** [test_backward_compatibility_e2e.py](file:///Users/bhushan/Documents/Projects/sutra/tests/e2e/test_backward_compatibility_e2e.py) validates that legacy commands (like `niyam doctor` or `niyam init`) execute successfully inside pre-upgrade workspace fixtures.
