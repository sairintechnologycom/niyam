"""Tests for EPIC-006: Enterprise Integrity & Parallel Isolation."""

import os
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from niyam.core.identity import ensure_identity, get_public_key_bytes, sign_data, verify_signature
from niyam.mission.task_runner import check_overlap
from niyam.mission.reporter import compute_manifest_signature, run_verify_report
from rich.console import Console


def test_ed25519_lifecycle(tmp_path):
    """Test key generation, signing, and verification."""
    with patch("niyam.core.config.find_niyam_root", return_value=tmp_path):
        # 1. Generate key
        private_key = ensure_identity(tmp_path)
        public_key_pem = get_public_key_bytes(tmp_path)
        
        assert b"BEGIN PUBLIC KEY" in public_key_pem
        
        # 2. Sign
        data = "test data"
        signature = sign_data(data, private_key)
        
        # 3. Verify
        assert verify_signature(data, signature, public_key_pem) is True
        assert verify_signature(data + " tampered", signature, public_key_pem) is False


def test_advanced_collision_detection():
    """Test the hardened check_overlap logic with complex globs."""
    # Exact overlap
    assert check_overlap(["src/a.py"], ["src/a.py"]) is True
    
    # Disjoint
    assert check_overlap(["src/backend/**"], ["src/frontend/**"]) is False
    assert check_overlap(["src/a.py"], ["src/b.py"]) is False
    
    # Nested overlap
    assert check_overlap(["src/**"], ["src/components/Button.tsx"]) is True
    assert check_overlap(["src/components/*"], ["src/components/Button.tsx"]) is True
    assert check_overlap(["src/components/Button.tsx"], ["src/**"]) is True
    
    # Universal overlap
    assert check_overlap(["*"], ["src/a.py"]) is True
    assert check_overlap(["src/a.py"], ["all"]) is True
    assert check_overlap(["**"], ["tests/test_x.py"]) is True
    
    # Multiple files
    assert check_overlap(["src/a.py", "src/b.py"], ["src/c.py", "src/a.py"]) is True
    assert check_overlap(["src/a.py", "src/b.py"], ["src/c.py", "src/d.py"]) is False


def test_evidence_manifest_asymmetric_signing(tmp_path):
    """Test that the manifest signature uses the new Ed25519 scheme."""
    with patch("niyam.core.config.find_niyam_root", return_value=tmp_path):
        private_key = ensure_identity(tmp_path)
        manifest_files = {"file1.txt": "hash1", "file2.txt": "hash2"}
        
        sig = compute_manifest_signature(manifest_files, private_key)
        assert len(sig) > 64 # Hex signature for Ed25519 is 128 chars
        
        # Verify canonicalization
        canonical = "file1.txt:hash1\nfile2.txt:hash2"
        public_key_pem = get_public_key_bytes(tmp_path)
        assert verify_signature(canonical, sig, public_key_pem) is True
