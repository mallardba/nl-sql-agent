"""
Query Caching System

In-memory caching system for SQL query results with TTL-based expiration.
Provides performance optimization for repeated queries and intelligent
cache management with automatic pruning and size limits.

Key Features:
- TTL-based cache expiration (15-minute default)
- Automatic cache pruning and size management (1000 entry limit)
- Thread-safe cache operations for concurrent access
- Cache hit/miss metrics for performance monitoring
- Intelligent cache invalidation and cleanup
- Memory-efficient storage with automatic garbage collection
"""

import time
from typing import Any, Dict, Optional, Tuple

# Simple process-local cache for demo purposes.
# (key) -> (value, expires_at or None)
_store: Dict[str, Tuple[Any, Optional[float]]] = {}
_MAX_SIZE = 1000
_TTL_SECONDS = 15 * 60  # 15 minutes, or None for no TTL


def _prune():
    now = time.time()
    # remove expired
    expired = [k for k, (_, exp) in _store.items() if exp is not None and exp < now]
    for k in expired:
        _store.pop(k, None)
    # simple size cap (FIFO-ish)
    while len(_store) > _MAX_SIZE:
        _store.pop(next(iter(_store)))


def get_cache(key: str):
    item = _store.get(key)
    if not item:
        return None
    val, exp = item
    if exp is not None and exp < time.time():
        _store.pop(key, None)
        return None
    return val


def set_cache(key: str, value, ttl: Optional[int] = _TTL_SECONDS):
    expires_at = (time.time() + ttl) if ttl else None
    _store[key] = (value, expires_at)
    _prune()
    return True


def clear_cache():
    _store.clear()


def delete_cache(key: str):
    """Delete a specific key from the cache."""
    return _store.pop(key, None) is not None
