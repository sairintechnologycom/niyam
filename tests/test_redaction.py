"""Unit tests for Niyam governance shared secret redaction engine."""

from __future__ import annotations

import pytest
from niyam.governance.common.redaction import (
    redact_text,
    redact_dict,
    contains_secret,
    get_secret_fingerprint,
    redact_secrets,
)

def test_redact_openai_key() -> None:
    # OpenAI sk- proj format
    raw = "key = sk-proj-1234567890abcdef1234567890abcdef"
    assert "1234567" not in redact_text(raw)
    assert redact_text(raw) == "key = [REDACTED_SECRET]"

    # OpenAI basic format
    raw_basic = "my sk-1234567890abcdef1234567890abcdef1234567890abcdef"
    assert "123456" not in redact_text(raw_basic)
    assert redact_text(raw_basic) == "my [REDACTED_SECRET]"


def test_redact_anthropic_key() -> None:
    raw = "anthropic_key = sk-ant-sid-1234567890abcdef1234567890abcdef"
    assert "sid-" not in redact_text(raw)
    assert redact_text(raw) == "anthropic_key = [REDACTED_SECRET]"


def test_redact_github_token() -> None:
    raw_ghp = "ghp_1234567890abcdef1234567890abcdef1234"
    assert "1234" not in redact_text(raw_ghp)
    assert redact_text(raw_ghp) == "[REDACTED_SECRET]"

    raw_pat = "github_pat_1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
    assert "pat_" not in redact_text(raw_pat)
    assert redact_text(raw_pat) == "[REDACTED_SECRET]"


def test_redact_aws_keys() -> None:
    raw_aws_id = "AWS ID is AKIAIOSFODNN7EXAMPLE"
    assert "AKIA" not in redact_text(raw_aws_id)
    assert redact_text(raw_aws_id) == "AWS ID is [REDACTED_AWS_KEY]"


def test_redact_azure_conn() -> None:
    raw = "DefaultEndpointsProtocol=https;AccountName=test;AccountKey=1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef==;EndpointSuffix=core.windows.net"
    assert "123456" not in redact_text(raw)
    assert "[REDACTED_SECRET]" in redact_text(raw)


def test_redact_jwt() -> None:
    raw = "bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    assert "eyJ" not in redact_text(raw)
    assert redact_text(raw) == "bearer [REDACTED_SECRET]"


def test_redact_private_key() -> None:
    raw = """-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEA0Y2X...
-----END RSA PRIVATE KEY-----"""
    assert "MIIE" not in redact_text(raw)
    assert redact_text(raw) == "[REDACTED_PRIVATE_KEY]"


def test_redact_db_url() -> None:
    raw = "postgresql://myuser:mypassword123@localhost:5432/mydb"
    assert "mypassword123" not in redact_text(raw)
    assert redact_text(raw) == "postgresql://myuser:[REDACTED_SECRET]@localhost:5432/mydb"


def test_redact_generic_assignments() -> None:
    # password assignment
    assert redact_text("password = \"mypass12345\"") == "password = \"[REDACTED_SECRET]\""
    # api key assignment
    assert redact_text("api_key: 'key1234567'") == "api_key: '[REDACTED_SECRET]'"
    # token assignment
    assert redact_text("token = abcdefgh123") == "token = [REDACTED_SECRET]"


def test_non_secret_unchanged() -> None:
    safe = "This is a safe sentence with no secrets. password = short"
    assert redact_text(safe) == safe


def test_redact_dict() -> None:
    raw = {
        "project": "niyam",
        "config": {
            "openai_key": "sk-proj-1234567890abcdef1234567890abcdef",
            "db_pass": "password=supersecretpassword",
        },
        "safe_list": ["hello", "world"],
        "secret_list": ["ghp_1234567890abcdef1234567890abcdef1234"],
    }
    redacted = redact_dict(raw)
    assert redacted["project"] == "niyam"
    assert redacted["config"]["openai_key"] == "[REDACTED_SECRET]"
    assert redacted["config"]["db_pass"] == "password=[REDACTED_SECRET]"
    assert redacted["safe_list"] == ["hello", "world"]
    assert redacted["secret_list"] == ["[REDACTED_SECRET]"]


def test_contains_secret() -> None:
    assert contains_secret("key = sk-proj-1234567890abcdef1234567890abcdef") is True
    assert contains_secret("This is a clean line") is False


def test_secret_fingerprint() -> None:
    secret = "sk-proj-1234567890abcdef"
    fp = get_secret_fingerprint(secret)
    assert len(fp) == 8
    # Test text redaction with fingerprint enabled
    raw = "key = sk-proj-1234567890abcdef1234567890abcdef"
    expected_fp = get_secret_fingerprint("sk-proj-1234567890abcdef1234567890abcdef")
    assert f"[REDACTED_SECRET_{expected_fp}]" in redact_text(raw, with_fingerprint=True)


def test_redact_secrets_generic() -> None:
    # test list redaction
    lst = ["sk-proj-1234567890abcdef1234567890abcdef", "safe"]
    assert redact_secrets(lst) == ["[REDACTED_SECRET]", "safe"]


def test_code_quality_review_findings() -> None:
    # 1. Nested list of secrets under a dictionary key
    nested_dict = {
        "data": [
            ["sk-ant-123456789012345678901234"],
            "safe_val",
            {"key": "sk-proj-1234567890abcdef1234567890abcdef"}
        ]
    }
    redacted_nested = redact_dict(nested_dict)
    assert redacted_nested["data"][0][0] == "[REDACTED_SECRET]"
    assert redacted_nested["data"][1] == "safe_val"
    assert redacted_nested["data"][2]["key"] == "[REDACTED_SECRET]"

    # 2. Generic assignments with special characters
    special_char_pass = 'password = "mySecret#2026!"'
    assert redact_text(special_char_pass) == 'password = "[REDACTED_SECRET]"'

    special_char_token = 'token: "auth@token_123$%"'
    assert redact_text(special_char_token) == 'token: "[REDACTED_SECRET]"'

    # 3. Direct key-based dictionary redaction
    direct_dict = {
        "api_key": "some-random-val",
        "safe_key": "safe-val",
        "secret": "another-val",
        "auth_token": "token-val"
    }
    redacted_direct = redact_dict(direct_dict)
    assert redacted_direct["api_key"] == "[REDACTED_SECRET]"
    assert redacted_direct["safe_key"] == "safe-val"
    assert redacted_direct["secret"] == "[REDACTED_SECRET]"
    assert redacted_direct["auth_token"] == "[REDACTED_SECRET]"


def test_nested_bypass_scenarios() -> None:
    # A list of custom secrets under a sensitive key is fully redacted.
    # A nested dictionary under a sensitive key is fully redacted.
    data = {
        "api_key": [
            "custom_secret_1",
            "custom_secret_2",
            {"nested_key": "custom_secret_3"}
        ]
    }
    redacted = redact_secrets(data)
    assert redacted["api_key"] == [
        "[REDACTED_SECRET]",
        "[REDACTED_SECRET]",
        {"nested_key": "[REDACTED_SECRET]"}
    ]

