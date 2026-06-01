---
name: api-design
description: API response structuring, versioning, pagination, and OpenAPI spec maintenance
---

# API Design & Governance

Standardize all API routes:

1. **Backwards Compatibility:** Never remove fields or change endpoints in a breaking manner without major version bumps.
2. **Error Standards:** Always return a structured JSON response body on failure:
    ```json
    {
      "success": false,
      "error": {
        "code": "BAD_REQUEST",
        "message": "Detailed explanation"
      }
    }
    ```
3. **Spec Generation:** Automatically regenerate OpenAPI documentation during the validation step.
