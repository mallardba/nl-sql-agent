from functools import lru_cache

# Simple process-local cache for demo purposes.
_store = {}

def get_cache(key: str):
    return _store.get(key)

def set_cache(key: str, value):
    _store[key] = value
    return True
