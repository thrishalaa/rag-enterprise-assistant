import time
from functools import lru_cache
from typing import Dict, Any

# Very small manual cache for search results keyed by query text
class SimpleCache:
    def __init__(self, max_items=256, ttl=3600):
        self.store: Dict[str, Dict[str, Any]] = {}
        self.max_items = max_items
        self.ttl = ttl

    def get(self, key: str):
        entry = self.store.get(key)
        if not entry:
            return None
        if time.time() - entry["ts"] > self.ttl:
            del self.store[key]
            return None
        return entry["value"]

    def set(self, key: str, value: Any):
        if len(self.store) >= self.max_items:
            # pop oldest
            oldest_key = min(self.store.keys(), key=lambda k: self.store[k]["ts"])
            del self.store[oldest_key]
        self.store[key] = {"value": value, "ts": time.time()}

# Singleton cache instances
EMBED_CACHE = SimpleCache(max_items=1024, ttl=3600)
SEARCH_CACHE = SimpleCache(max_items=512, ttl=600)
