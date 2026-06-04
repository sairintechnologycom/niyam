# Niyam Backward Compatibility & Regression Policy

This document defines Niyam's backward compatibility rules and stability guarantees. As Niyam integrates governance features, it is vital to ensure that existing orchestration, context, and command workflows remain intact and fully functional.

---

## 1. CLI Commands Stability

All core Niyam commands are stable and guaranteed not to be renamed or modified:
- **Core Commands:** `init`, `sync`, `doctor`, `report`, `start`, `next`, `update`, `version`.
- **Command Groups:** `context`, `runtime`, `policy`, `pack`, `memory`, `mission`, `review`, `pr`, `ci`.
- **Stability Guarantee:** Options, behavior, and output format for legacy command lines are protected. Any changes that change outputs or exit codes of these commands are strictly prohibited.

---

## 2. Governance Commands are Additive

New governance and safety features are additive and isolated:
- **Additive Commands:** `scan`, `guard`, `mcp`, `cost`, `evidence`.
- **Isolation Guarantee:** Adding these command structures must not modify the behavior or options of existing commands. Legacy workflows run unchanged, and their performance/resource consumption must not be impacted by the presence of governance logic.

---

## 3. Configuration File Compatibility

Existing configs (`niyam.yaml`, `project.yaml`, `runtimes.yaml`) must load without raising errors:
- **Governance Optionality:** The `governance` config section in `niyam.yaml` is optional.
- **Default Resolution:** Config files without a `governance` section load cleanly and resolve all schema defaults safely, guaranteeing that legacy projects continue to initialize, validate, and execute without modification.

---

## 4. Major Version Bumps for Breaking Changes

Any breaking changes to the core contract require a major version bump:
- **Versioning Policy:** Niyam follows semantic versioning (`MAJOR.MINOR.PATCH`).
- **Breaking definition:** Removing commands, changing non-experimental options, or modifying schema validation constraints in a way that breaks existing configurations requires a major version increment.

---

## 5. Experimental Governance Modules

Governance modules (`scan`, `guard`, `mcp`, `cost`, `evidence`) may evolve independently:
- **Evolution Buffer:** While experimental governance subcommands may undergo schema changes or output format enhancements, they must do so without causing compilation errors or runtime failures in core orchestration workflows.
- **Safety Gate Isolation:** The scanning gates and observed guardrails operate asynchronously or as additive verification checkpoints, ensuring they do not interrupt core loop execution unless explicitly configured as a hard-blocking policy.
