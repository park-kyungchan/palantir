"""
Tests for response caching system.
"""
import pytest
from pathlib import Path
import tempfile

from cow_cli.cache import (
    MathpixCache,
    CacheStats,
    CacheManager,
    get_cache_key,
)


class TestCacheKey:
    """Tests for cache key generation."""

    def test_same_input_same_key(self):
        """Test that same inputs produce same key."""
        image = b"test_image_bytes"
        options = {"format": "text", "include_latex": True}

        key1 = get_cache_key(image, options)
        key2 = get_cache_key(image, options)

        assert key1 == key2

    def test_different_image_different_key(self):
        """Test that different images produce different keys."""
        options = {"format": "text"}

        key1 = get_cache_key(b"image1", options)
        key2 = get_cache_key(b"image2", options)

        assert key1 != key2

    def test_different_options_different_key(self):
        """Test that different options produce different keys."""
        image = b"same_image"

        key1 = get_cache_key(image, {"format": "text"})
        key2 = get_cache_key(image, {"format": "data"})

        assert key1 != key2

    def test_option_order_independent(self):
        """Test that option order doesn't affect key."""
        image = b"test_image"

        key1 = get_cache_key(image, {"a": 1, "b": 2})
        key2 = get_cache_key(image, {"b": 2, "a": 1})

        assert key1 == key2

    def test_key_is_sha256_hex(self):
        """Test that key is valid SHA256 hex."""
        key = get_cache_key(b"test", {})

        assert len(key) == 64  # SHA256 produces 64 hex chars
        assert all(c in "0123456789abcdef" for c in key)


class TestCacheStats:
    """Tests for CacheStats."""

    def test_hit_rate_calculation(self):
        """Test hit rate calculation."""
        stats = CacheStats(hits=75, misses=25)

        assert stats.hit_rate == 0.75

    def test_hit_rate_zero_total(self):
        """Test hit rate with no requests."""
        stats = CacheStats(hits=0, misses=0)

        assert stats.hit_rate == 0.0


class TestMathpixCache:
    """Tests for MathpixCache."""

    @pytest.fixture
    def temp_cache_dir(self):
        """Create temporary cache directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_cache_disabled(self):
        """Test cache when disabled."""
        cache = MathpixCache(enabled=False)

        assert cache.enabled is False
        assert cache.get("any_key") is None
        assert cache.set("any_key", {"data": "value"}) is False

    def test_cache_set_get(self, temp_cache_dir):
        """Test basic set/get operations."""
        cache = MathpixCache(
            directory=temp_cache_dir,
            ttl_days=1,
            max_size_mb=10,
            enabled=True,
        )

        key = "test_key_123"
        value = {"result": "test_data", "confidence": 0.95}

        # Set
        assert cache.set(key, value) is True

        # Get
        retrieved = cache.get(key)
        assert retrieved == value

        cache.close()

    def test_cache_miss(self, temp_cache_dir):
        """Test cache miss."""
        cache = MathpixCache(
            directory=temp_cache_dir,
            enabled=True,
        )

        result = cache.get("nonexistent_key")

        assert result is None
        stats = cache.get_stats()
        assert stats.misses == 1

        cache.close()

    def test_cache_hit_tracking(self, temp_cache_dir):
        """Test hit/miss tracking."""
        cache = MathpixCache(
            directory=temp_cache_dir,
            enabled=True,
        )

        cache.set("key1", {"data": 1})
        cache.get("key1")  # Hit
        cache.get("key1")  # Hit
        cache.get("key2")  # Miss

        stats = cache.get_stats()
        assert stats.hits == 2
        assert stats.misses == 1
        assert stats.hit_rate == 2 / 3

        cache.close()

    def test_cache_delete(self, temp_cache_dir):
        """Test cache delete."""
        cache = MathpixCache(
            directory=temp_cache_dir,
            enabled=True,
        )

        cache.set("key", {"data": "value"})
        assert cache.get("key") is not None

        cache.delete("key")
        assert cache.get("key") is None

        cache.close()

    def test_cache_clear(self, temp_cache_dir):
        """Test cache clear."""
        cache = MathpixCache(
            directory=temp_cache_dir,
            enabled=True,
        )

        cache.set("key1", {"data": 1})
        cache.set("key2", {"data": 2})

        count = cache.clear()

        assert count == 2
        assert cache.get("key1") is None
        assert cache.get("key2") is None

        cache.close()


class TestCacheManager:
    """Tests for CacheManager context manager."""

    def test_context_manager(self):
        """Test context manager usage."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with CacheManager(
                directory=Path(tmpdir),
                enabled=True,
            ) as cache:
                cache.set("test", {"value": 1})
                assert cache.get("test") == {"value": 1}

    def test_generate_key_in_context(self):
        """Test key generation in context."""
        with CacheManager(enabled=False) as cache:
            key = cache.generate_key(b"image", {"opt": True})

            assert len(key) == 64
