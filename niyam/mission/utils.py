"""Niyam mission shared utilities and locks."""

from __future__ import annotations

import threading
from niyam.core.utils import compute_sha256

# Shared locks for thread-safe operations
print_lock = threading.Lock()
validation_lock = threading.Lock()
plan_lock = threading.RLock()
