"""
Tests for StrategyVault - Redis Caching Layer
Tests cache manager, fallback behavior, and decorator.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.core.cache import NoOpCache, CacheManager, cache, cached


class TestNoOpCache:
    """Test the fallback no-op cache."""

    def test_get_returns_none(self):
        noop = NoOpCache()
        assert noop.get("any_key") is None

    def test_set_returns_false(self):
        noop = NoOpCache()
        assert noop.set("key", "value") is False

    def test_delete_returns_false(self):
        noop = NoOpCache()
        assert noop.delete("key") is False

    def test_exists_returns_false(self):
        noop = NoOpCache()
        assert noop.exists("key") is False

    def test_ping_returns_false(self):
        noop = NoOpCache()
        assert noop.ping() is False


class TestCacheManager:
    """Test the cache manager."""

    def test_singleton_instance_exists(self):
        """Cache singleton should be importable."""
        assert cache is not None
        assert isinstance(cache, CacheManager)

    def test_cache_key_deterministic(self):
        """Same inputs should produce same cache key."""
        key1 = cache.cache_key("fetch", "BTC-USD", "2y")
        key2 = cache.cache_key("fetch", "BTC-USD", "2y")
        assert key1 == key2

    def test_cache_key_different_inputs(self):
        """Different inputs should produce different keys."""
        key1 = cache.cache_key("fetch", "BTC-USD")
        key2 = cache.cache_key("fetch", "ETH-USD")
        assert key1 != key2

    def test_graceful_fallback_without_redis(self):
        """Cache should work without Redis (no errors thrown)."""
        # This test runs without Redis, so all operations should no-op
        result = cache.get("nonexistent_key")
        assert result is None

    def test_set_without_redis_no_error(self):
        """Setting cache without Redis should not raise."""
        # Should return False (not cached) but no exception
        result = cache.set("test_key", {"data": "test"})
        assert isinstance(result, bool)


class TestCachedDecorator:
    """Test the @cached decorator."""

    def test_decorator_preserves_function(self):
        """Decorated function should still work."""
        @cached(prefix="test")
        def add(a, b):
            return a + b

        assert add(2, 3) == 5

    def test_decorator_preserves_name(self):
        """Decorated function should keep its name."""
        @cached(prefix="test")
        def my_function():
            return 42

        assert my_function.__name__ == "my_function"

    def test_decorator_handles_none_result(self):
        """Decorator should handle functions returning None."""
        @cached(prefix="test")
        def returns_none():
            return None

        assert returns_none() is None


class TestCacheConfig:
    """Test cache configuration."""

    def test_cache_ttl_configured(self):
        from src.core.config import settings
        assert hasattr(settings, "CACHE_TTL_SECONDS")
        assert settings.CACHE_TTL_SECONDS > 0

    def test_cache_enabled_configured(self):
        from src.core.config import settings
        assert hasattr(settings, "CACHE_ENABLED")
        assert isinstance(settings.CACHE_ENABLED, bool)

    def test_redis_url_configured(self):
        from src.core.config import settings
        assert hasattr(settings, "REDIS_URL")
        assert "redis://" in settings.REDIS_URL
