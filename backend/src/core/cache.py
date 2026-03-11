"""
StrategyVault - Redis Caching Layer
Provides cache management with graceful fallback when Redis is unavailable.

Features:
- Redis connection with auto-reconnect
- No-op fallback cache when Redis is unavailable
- TTL-based expiration
- JSON serialization for complex data
"""

import json
import time
import hashlib
from typing import Any, Optional
from functools import wraps

from src.core.config import settings


class NoOpCache:
    """Fallback cache that does nothing (used when Redis is unavailable)."""

    def get(self, key: str) -> Optional[str]:
        return None

    def set(self, key: str, value: str, ex: int = None) -> bool:
        return False

    def delete(self, key: str) -> bool:
        return False

    def exists(self, key: str) -> bool:
        return False

    def ping(self) -> bool:
        return False


class CacheManager:
    """
    Redis-backed cache with graceful fallback.
    
    If Redis is unavailable, all operations silently no-op
    so the application continues working without caching.
    """

    def __init__(self):
        self._client = None
        self._is_available = False
        self._last_check = 0
        self._check_interval = 30  # Re-check Redis every 30s

        if settings.CACHE_ENABLED:
            self._connect()

    def _connect(self):
        """Try to connect to Redis."""
        try:
            import redis
            self._client = redis.Redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2,
            )
            self._client.ping()
            self._is_available = True
        except Exception:
            self._client = NoOpCache()
            self._is_available = False

    @property
    def is_available(self) -> bool:
        """Check if Redis is currently available."""
        now = time.time()
        if not self._is_available and (now - self._last_check) > self._check_interval:
            self._last_check = now
            self._connect()
        return self._is_available

    def get(self, key: str) -> Optional[Any]:
        """Get a value from cache, deserializing JSON."""
        try:
            value = self._client.get(f"sv:{key}")
            if value is not None:
                return json.loads(value)
        except Exception:
            pass
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set a value in cache, serializing to JSON."""
        try:
            ttl = ttl or settings.CACHE_TTL_SECONDS
            serialized = json.dumps(value, default=str)
            self._client.set(f"sv:{key}", serialized, ex=ttl)
            return True
        except Exception:
            return False

    def delete(self, key: str) -> bool:
        """Delete a key from cache."""
        try:
            self._client.delete(f"sv:{key}")
            return True
        except Exception:
            return False

    def cache_key(self, *args) -> str:
        """Generate a deterministic cache key from arguments."""
        raw = ":".join(str(a) for a in args)
        return hashlib.md5(raw.encode()).hexdigest()


# Singleton cache instance
cache = CacheManager()


def cached(ttl: Optional[int] = None, prefix: str = ""):
    """
    Decorator that caches function results.
    
    Args:
        ttl: Time to live in seconds (uses default from config if None)
        prefix: Key prefix for namespacing
        
    Usage:
        @cached(ttl=3600, prefix="market")
        def fetch_data(symbol, period):
            return expensive_api_call()
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not cache.is_available:
                return func(*args, **kwargs)

            # Build cache key from function name + args
            key_parts = [prefix or func.__name__] + [str(a) for a in args]
            key_parts += [f"{k}={v}" for k, v in sorted(kwargs.items())]
            key = cache.cache_key(*key_parts)

            # Try cache first
            result = cache.get(key)
            if result is not None:
                return result

            # Compute and cache
            result = func(*args, **kwargs)
            if result is not None:
                cache.set(key, result, ttl=ttl)
            return result

        return wrapper
    return decorator
