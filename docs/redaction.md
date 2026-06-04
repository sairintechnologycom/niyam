# Niyam Secret Redaction Utility Documentation

This document describes the design, implementation, and usage of the shared secret redaction foundation in Niyam, introduced in Phase 1B.

---

## 1. Overview & Purpose

The shared secret redaction utility (`niyam/governance/common/redaction.py`) provides a central, offline, lightweight library to sanitize outputs (logs, reports, terminal stdin/stdout streams, and evidence files) before they are written to disk or shown in the UI.

The goal is to prevent inadvertent leakage of credentials and sensitive keys during AI-assisted development sessions.

---

## 2. API Reference

The module exposes the following function signatures:

### `redact_text(value: str, with_fingerprint: bool = False) -> str`
Detects and redacts common secrets in string values. Returns the sanitized string.
* If `with_fingerprint` is True, appends the first 8 hex characters of the SHA-256 hash of the secret (e.g. `[REDACTED_SECRET_a1b2c3d4]`) to allow matching corresponding secrets in log analysis without revealing the raw values.

### `redact_dict(value: dict, with_fingerprint: bool = False) -> dict`
Recursively traverses dicts, lists, and strings to sanitize nested values.

### `contains_secret(value: str) -> bool`
Returns `True` if the text contains any matching secret pattern. Useful for gate checks.

### `redact_secrets(data: Any, with_fingerprint: bool = False) -> Any`
A generic router that delegates to `redact_text`, `redact_dict`, or lists depending on the input type.

### `get_secret_fingerprint(secret: str) -> str`
Calculates the SHA-256 hash of the cleaned secret and returns the first 8 hex characters.

---

## 3. Supported Patterns

Initially, the engine detects:
1. **OpenAI-style keys:** `sk-...`
2. **Anthropic-style keys:** `sk-ant-...`
3. **GitHub tokens:** `ghp_...`, `github_pat_...`
4. **AWS Access Key IDs:** `AKIA...`, `ASCA...`, `ASIA...`
5. **Azure connection strings:** Containing `AccountKey=`
6. **JWT-like tokens:** Starting with `eyJ`
7. **Private key blocks:** PEM block markers (`-----BEGIN ... PRIVATE KEY-----`)
8. **Generic assignments:** Config/env-like strings matching keywords (`password`, `api_key`, `token`, etc.) followed by value separators (`=`, `:`) and strings (length 8-128).
9. **Database URLs:** Embedded passwords inside `protocol://user:password@host` format.

---

## 4. Usage Examples

```python
from niyam.governance.common.redaction import redact_text, redact_dict, contains_secret

# 1. Simple text redaction
raw_text = "OPENAI_API_KEY=sk-proj-1234567890abcdef1234567890abcdef"
clean_text = redact_text(raw_text)
# Result: "OPENAI_API_KEY=[REDACTED_SECRET]"

# 2. Text redaction with fingerprinting
clean_text_fp = redact_text(raw_text, with_fingerprint=True)
# Result: "OPENAI_API_KEY=[REDACTED_SECRET_4cf7b6a1]"

# 3. Dictionary redaction
raw_dict = {
    "auth": {
        "token": "ghp_1234567890abcdef1234567890abcdef1234"
    },
    "env": "production"
}
clean_dict = redact_dict(raw_dict)
# Result: {"auth": {"token": "[REDACTED_SECRET]"}, "env": "production"}

# 4. Checking if text contains secrets
has_secret = contains_secret("My database connection string: postgres://user:pass1234@localhost/db")
# Result: True
```

---

## 5. Compatibility & Risk Summary

### False Positives
* **Risk:** The generic assignment pattern (`password = value`, `token = value`) matches keys of length 8 to 128. It is possible that valid, non-secret variables of length 8 or more matching key-like names (e.g. `password_format = "standard"`) could be redacted.
* **Mitigation:** The regex matches word boundaries and checks for common assignments. Shorter values (< 8 characters) are ignored to avoid redacting simple words/placeholders like `password = "short"`.

### Performance Impact
* **Risk:** Running nine compiled regexes over large log streams or large evidence files could add a minor latency overhead.
* **Mitigation:** Regexes are pre-compiled at module load time. The operations run locally in standard Python C-based regex engine, which is highly optimized. If performance bottlenecks are found in future phases, a fast pre-filter (checking `contains_secret`) can skip the detailed sub-passes.

### Offline Guarantee
* **Risk:** Secret detection engines sometimes call remote model endpoints or API checks.
* **Mitigation:** The Niyam redaction utility operates 100% offline using deterministic pattern matching. No external network requests are made.

---

## 6. Rollback Approach

If a bug or high false-positive rate is discovered:
1. **Disable Redaction Gate:** Set `governance.redact_logs: false` in `.niyam/niyam.yaml` to bypass the redaction engine during execution.
2. **Revert Module:** Revert the redaction engine code to the baseline by running:
   ```bash
   git checkout HEAD -- niyam/governance/common/redaction.py
   ```
3. **Run Unit Tests:** Run `pytest tests/test_redaction.py` to verify that any hotfix maintains key redaction rules.
