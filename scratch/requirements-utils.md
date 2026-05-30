# Requirement: Core Utilities Module

Create a core utilities module in `sutra/core/utils.py` that implements helper functions.

## Feature Specifications

1. Implement `format_date_iso(dt: datetime) -> str`:
   - Formats a Python `datetime` object into ISO-8601 UTC representation (e.g. `2026-05-30T11:49:17Z`).
   - If timezone is not present (naive datetime), treat it as UTC.
2. Implement associated unit tests in `tests/test_utils.py` using pytest.
