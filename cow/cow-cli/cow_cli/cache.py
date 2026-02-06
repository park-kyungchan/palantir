"""
COW CLI - Response Caching System

Disk-based cache for Mathpix API responses using diskcache.
Cache key: SHA256(image_content + options_json)
"""
from typing import Optional, Any
from pathlib import Path
import hashlib
import json
import time
from dataclasses import dataclass

from diskcache import Cache

from cow_cli.config import load_config


@dataclass
class CacheStats:
    """Cache statistics."""

    hits: int = 0
    misses: int = 0
    size_bytes: int = 0
    item_count: int = 0

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


class MathpixCache:
    """
    Disk-based cache for Mathpix API responses.

    Uses SHA256 hash of image content + options as cache key.
    Supports TTL-based expiration and size limits.
    """

    def __init__(
        self,
        directory: Optional[Path] = None,
        ttl_days: Optional[int] = None,
        max_size_mb: Optional[int] = None,
        enabled: Optional[bool] = None,
    ):
        """
        Initialize cache.

        Args:
            directory: Cache directory path
            ttl_days: Time-to-live in days
            max_size_mb: Maximum cache size in MB
            enabled: Enable/disable caching
        """
        # Load config for defaults
        config = load_config()
        cache_config = config.cache

        self._enabled = enabled if enabled is not None else cache_config.enabled
        self._directory = directory or cache_config.directory
        self._ttl_seconds = (ttl_days or cache_config.ttl_days) * 86400
        self._max_size_bytes = (max_size_mb or cache_config.max_size_mb) * 1024 * 1024

        # Statistics tracking
        self._hits = 0
        self._misses = 0

        # Initialize cache
        if self._enabled:
            self._directory.mkdir(parents=True, exist_ok=True)
            self._cache = Cache(
                str(self._directory),
                size_limit=self._max_size_bytes,
                eviction_policy="least-recently-used",
            )
        else:
            self._cache = None

    @property
    def enabled(self) -> bool:
        """Check if cache is enabled."""
        return self._enabled and self._cache is not None

    def generate_key(self, image_bytes: bytes, options: dict) -> str:
        """
        Generate cache key from image content and options.

        Args:
            image_bytes: Raw image bytes
            options: API request options

        Returns:
            SHA256 hex digest as cache key
        """
        # Sort options for consistent hashing
        options_json = json.dumps(options, sort_keys=True, ensure_ascii=False)
        content = image_bytes + options_json.encode("utf-8")
        return hashlib.sha256(content).hexdigest()

    def get(self, key: str) -> Optional[dict]:
        """
        Retrieve cached response.

        Args:
            key: Cache key (SHA256 hash)

        Returns:
            Cached response dict or None if not found/expired
        """
        if not self.enabled:
            return None

        result = self._cache.get(key)

        if result is not None:
            self._hits += 1
            return result
        else:
            self._misses += 1
            return None

    def set(self, key: str, value: dict) -> bool:
        """
        Store response in cache.

        Args:
            key: Cache key (SHA256 hash)
            value: Response dict to cache

        Returns:
            True if stored successfully
        """
        if not self.enabled:
            return False

        try:
            self._cache.set(key, value, expire=self._ttl_seconds)
            return True
        except Exception:
            return False

    def delete(self, key: str) -> bool:
        """
        Remove entry from cache.

        Args:
            key: Cache key to remove

        Returns:
            True if removed, False if not found
        """
        if not self.enabled:
            return False

        return self._cache.delete(key)

    def clear(self) -> int:
        """
        Clear all cache entries.

        Returns:
            Number of entries cleared
        """
        if not self.enabled:
            return 0

        count = len(self._cache)
        self._cache.clear()
        return count

    def get_stats(self) -> CacheStats:
        """
        Get cache statistics.

        Returns:
            CacheStats with hit/miss counts and size info
        """
        if not self.enabled:
            return CacheStats()

        return CacheStats(
            hits=self._hits,
            misses=self._misses,
            size_bytes=self._cache.volume(),
            item_count=len(self._cache),
        )

    def expire_old_entries(self) -> int:
        """
        Remove expired entries.

        Returns:
            Number of entries removed
        """
        if not self.enabled:
            return 0

        # diskcache handles expiration automatically
        # but we can force cleanup
        return self._cache.expire()

    def close(self) -> None:
        """Close cache and release resources."""
        if self._cache is not None:
            self._cache.close()


class CacheManager:
    """
    Context manager for cached Mathpix API calls.

    Usage:
        with CacheManager() as cache:
            key = cache.generate_key(image_bytes, options)
            if cached := cache.get(key):
                return cached
            result = api_call(...)
            cache.set(key, result)
            return result
    """

    def __init__(self, **kwargs):
        self._cache = MathpixCache(**kwargs)

    def __enter__(self) -> MathpixCache:
        return self._cache

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self._cache.close()


def get_cache_key(image_bytes: bytes, options: dict) -> str:
    """
    Standalone function to generate cache key.

    Args:
        image_bytes: Raw image bytes
        options: API request options

    Returns:
        SHA256 hex digest
    """
    options_json = json.dumps(options, sort_keys=True, ensure_ascii=False)
    content = image_bytes + options_json.encode("utf-8")
    return hashlib.sha256(content).hexdigest()


# Global cache instance (lazy initialization)
_global_cache: Optional[MathpixCache] = None


def get_global_cache() -> MathpixCache:
    """Get or create global cache instance."""
    global _global_cache
    if _global_cache is None:
        _global_cache = MathpixCache()
    return _global_cache


def close_global_cache() -> None:
    """Close global cache instance."""
    global _global_cache
    if _global_cache is not None:
        _global_cache.close()
        _global_cache = None


__all__ = [
    "CacheStats",
    "MathpixCache",
    "CacheManager",
    "get_cache_key",
    "get_global_cache",
    "close_global_cache",
]
