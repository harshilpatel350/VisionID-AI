"""
Token blacklist for logout / revocation.

Stores JTI (JWT ID) claims with their expiration time.
Periodically cleans up expired entries to prevent unbounded memory growth.
"""
from __future__ import annotations

import threading
import time


class TokenBlacklist:
    """Thread-safe in-memory blacklist with TTL-based auto-cleanup."""

    _CLEANUP_INTERVAL = 300  # seconds between automatic cleanups

    def __init__(self) -> None:
        self._store: dict[str, float] = {}  # jti -> expiry timestamp
        self._lock = threading.Lock()
        self._last_cleanup = time.time()

    def revoke(self, jti: str, exp: float) -> None:
        """Add a token's JTI to the blacklist until *exp* (unix timestamp)."""
        with self._lock:
            self._store[jti] = exp
            self._maybe_cleanup()

    def is_revoked(self, jti: str) -> bool:
        with self._lock:
            self._maybe_cleanup()
            return jti in self._store

    def _maybe_cleanup(self) -> None:
        now = time.time()
        if now - self._last_cleanup < self._CLEANUP_INTERVAL:
            return
        self._store = {jti: exp for jti, exp in self._store.items() if exp > now}
        self._last_cleanup = now


# Module-level singleton
blacklist = TokenBlacklist()
