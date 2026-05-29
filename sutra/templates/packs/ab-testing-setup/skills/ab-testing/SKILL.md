---
name: ab-testing
description: Guidelines for experiment design, variant handling, and analytics telemetry
---

# A/B Testing Workflow

Enforce experiment guidelines:

1. **Hypothesis definition:** Formulate hypothesis and parameters (primary/secondary metrics) before implementing logic.
2. **Defensive default:** Always fallback to the control variant if feature flag evaluation fails.
3. **Telemetry collection:** Ensure telemetry logging records user allocations and event actions correctly.
