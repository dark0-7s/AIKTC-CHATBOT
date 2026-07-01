# backend/cache/cache_manager.py
"""
In-memory registry mapping session IDs to Gemini cached content names.

Gemini's context caching API stores the system instruction + tools server-side,
returning a cache "name" (e.g. "cachedContents/abc123"). We track these per-session
so subsequent turns can skip re-sending the ~85k-char KB + function definitions.

The cache has a server-side TTL (default 1 hour). We mirror that TTL locally to
avoid hitting an expired cache and getting a 404.

Thread-safe via Lock for gunicorn/uvicorn worker safety.
"""

import time
import logging
from threading import Lock

logger = logging.getLogger("aiktc.cache")


class CacheManager:
    """Simple in-memory registry for Gemini context cache IDs per session.

    Gemini caches expire after a set period (default 60 min) or when the
    cache object is deleted. We track the cache ID and creation time,
    then automatically clean up stale entries.
    """

    def __init__(self, ttl: int = 3600):
        self._store: dict[str, tuple[str, float]] = {}  # session_id -> (cache_name, created_at)
        self._lock = Lock()
        self._ttl = ttl  # seconds — must match the ttl sent to Gemini API

    def set(self, session_id: str, cache_name: str) -> None:
        """Register a cache name for a session."""
        with self._lock:
            self._store[session_id] = (cache_name, time.time())
        logger.info(f"Cached content registered: session={session_id[:8]}… → {cache_name}")

    def get(self, session_id: str) -> str | None:
        """Retrieve the cache name if it hasn't expired locally. Returns None if stale/missing."""
        with self._lock:
            entry = self._store.get(session_id)
            if entry is None:
                return None
            cache_name, created = entry
            if time.time() - created > self._ttl:
                del self._store[session_id]
                logger.info(f"Cache expired locally: session={session_id[:8]}…")
                return None
            return cache_name

    def remove(self, session_id: str) -> None:
        """Evict a session's cache entry (e.g. on fallback after 404)."""
        with self._lock:
            removed = self._store.pop(session_id, None)
        if removed:
            logger.info(f"Cache evicted: session={session_id[:8]}…")

    @property
    def size(self) -> int:
        """Number of active cache entries (for health/debug endpoints)."""
        with self._lock:
            return len(self._store)


# ---------------------------------------------------------------------------
# Global singleton — imported by chat route
# ---------------------------------------------------------------------------
cache_manager = CacheManager()
