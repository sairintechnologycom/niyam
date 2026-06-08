"""Niyam identity management — cryptographic signing and verification."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Optional

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

from niyam.core.config import find_niyam_root, get_niyam_dir


def get_identity_key_path(repo_root: Path | None = None) -> Path:
    """Get path to the local identity key file (private)."""
    if repo_root is None:
        repo_root = find_niyam_root()
    if repo_root is None:
        repo_root = Path.cwd()
    return get_niyam_dir(repo_root) / "identity.pem"


def ensure_identity(repo_root: Path | None = None) -> ed25519.Ed25519PrivateKey:
    """Ensure a local Ed25519 identity key exists, generating one if missing."""
    key_path = get_identity_key_path(repo_root)
    legacy_path = key_path.with_name("identity.key")
    
    # Handle legacy migration (Alpha phase: just overwrite if old hex key found)
    if legacy_path.exists() and not key_path.exists():
        try:
            legacy_path.unlink()
        except Exception:
            pass

    if key_path.exists():
        try:
            private_key = serialization.load_pem_private_key(
                key_path.read_bytes(),
                password=None,
            )
            if isinstance(private_key, ed25519.Ed25519PrivateKey):
                return private_key
        except Exception:
            # If corrupt, we'll re-generate
            pass

    # Generate a new Ed25519 private key
    private_key = ed25519.Ed25519PrivateKey.generate()
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    
    key_path.parent.mkdir(parents=True, exist_ok=True)
    key_path.write_bytes(pem)
    
    # Restrict permissions (Unix-only)
    try:
        key_path.chmod(0o600)
    except Exception:
        pass
        
    return private_key


def get_public_key_bytes(repo_root: Path | None = None) -> bytes:
    """Export the public key in PEM format."""
    private_key = ensure_identity(repo_root)
    public_key = private_key.public_key()
    return public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )


def sign_data(data: str, private_key: ed25519.Ed25519PrivateKey) -> str:
    """Compute Ed25519 signature for data string."""
    signature = private_key.sign(data.encode("utf-8"))
    return signature.hex()


def verify_signature(data: str, signature_hex: str, public_key_pem: bytes) -> bool:
    """Verify that an Ed25519 signature matches the data and public key."""
    try:
        public_key = serialization.load_pem_public_key(public_key_pem)
        if not isinstance(public_key, ed25519.Ed25519PublicKey):
            return False
            
        signature = bytes.fromhex(signature_hex)
        public_key.verify(signature, data.encode("utf-8"))
        return True
    except Exception:
        return False
