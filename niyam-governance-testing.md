# Niyam Governance E2E Testing Strategy

## Goal
Implement a robust E2E testing strategy, build test fixtures, and create an automated testing suite and E2E script for Niyam's AI governance capabilities without regression.

## Tasks
- [x] Task 1: Move governance documentation files to `docs/governance/` directory. → Verify: Check if files exist at `docs/governance/*.md` and are removed from the project root.
- [x] Task 2: Create test fixtures for the three sample repositories under `test-fixtures/apps/` and `test-fixtures/niyam/`. → Verify: Run `ls test-fixtures/apps/clean-nextjs-app` and verify required files are present.
- [x] Task 3: Create custom rules fixtures `test-fixtures/rules/custom-rules.yaml` and `test-fixtures/rules/invalid-rules.yaml`. → Verify: Verify files contain valid and invalid YAML syntax respectively.
- [x] Task 4: Add comprehensive automated tests under `tests/` covering scan, rule engine loading, evidence generator, guard observe, guard policy, MCP, cost, and integrated reports. → Verify: Run `pytest` on the new tests.
- [x] Task 5: Implement the E2E verification script `scripts/test-governance-e2e.sh`. → Verify: Run `chmod +x scripts/test-governance-e2e.sh` and execute it, verifying all stages pass.
- [x] Task 6: Add E2E test plan documentation at `docs/governance/e2e-test-plan.md`. → Verify: Check that `docs/governance/e2e-test-plan.md` exists and contains correct content.

## Done When
- [x] All 189+ existing tests pass.
- [x] All new tests pass successfully.
- [x] `scripts/test-governance-e2e.sh` runs successfully to completion.
- [x] Governance documentation is moved and E2E test plan documentation is added.
