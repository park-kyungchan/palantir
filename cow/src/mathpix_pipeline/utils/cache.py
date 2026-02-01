"""
Math Image Parsing Pipeline - Caching Layer

This module provides a two-tier caching system (memory + disk) for pipeline results.
It supports async operations, TTL-based expiration, and namespace isolation.

Features:
- Two-tier caching: Fast memory cache with persistent disk fallback
- TTL support: Automatic expiration of stale entries
- Namespace isolation: Separate cache spaces for different pipeline stages
- Image hash computation: Content-based cache keys for images
- Async interface: Non-blocking cache operations

Module Version: 1.0.0
"""

import asyncio
import hashlib
import json
import logging
import os
import pickle
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Generic, Optional, TypeVar, Union

logger = logging.getLogger(__name__)

T = TypeVar("T")


# =============================================================================
# Configuration
# =============================================================================

@dataclass
class CacheConfig:
    """Configuration for the caching layer.

    Attributes:
        cache_dir: Directory for disk-based cache storage.
            Defaults to .cache/mathpix_pipeline in the current directory.
        default_ttl_seconds: Default time-to-live for cache entries in seconds.
            Set to 0 for infinite TTL. Defaults to 3600 (1 hour).
        max_size_mb: Maximum size of disk cache in megabytes.
            When exceeded, oldest entries are evicted. Defaults to 500 MB.
        memory_max_items: Maximum number of items in memory cache.
            Defaults to 1000 items.
        enable_disk_cache: Whether to enable disk-based caching.
            Defaults to True.
        enable_memory_cache: Whether to enable memory-based caching.
            Defaults to True.
        compression_enabled: Whether to compress disk cache entries.
            Defaults to False (for speed).
    """
    cache_dir: str = field(default_factory=lambda: str(Path.cwd() / ".cache" / "mathpix_pipeline"))
    default_ttl_seconds: int = 3600  # 1 hour
    max_size_mb: int = 500
    memory_max_items: int = 1000
    enable_disk_cache: bool = True
    enable_memory_cache: bool = True
    compression_enabled: bool = False

    def __post_init__(self) -> None:
        """Validate configuration values."""
        if self.default_ttl_seconds < 0:
            raise ValueError("default_ttl_seconds must be non-negative")
        if self.max_size_mb <= 0:
            raise ValueError("max_size_mb must be positive")
        if self.memory_max_items <= 0:
            raise ValueError("memory_max_items must be positive")


# =============================================================================
# Cache Entry
# =============================================================================

@dataclass
class CacheEntry(Generic[T]):
    """A single cache entry with metadata.

    Attributes:
        value: The cached value.
        created_at: Timestamp when the entry was created.
        expires_at: Timestamp when the entry expires (0 for never).
        namespace: The namespace this entry belongs to.
        size_bytes: Approximate size of the entry in bytes.
    """
    value: T
    created_at: float
    expires_at: float  # 0 means never expires
    namespace: str
    size_bytes: int = 0

    def is_expired(self) -> bool:
        """Check if this entry has expired."""
        if self.expires_at == 0:
            return False
        return time.time() > self.expires_at


# =============================================================================
# Result Cache
# =============================================================================

class ResultCache:
    """Two-tier cache for pipeline results.

    Provides fast memory caching with disk persistence fallback.
    Supports TTL-based expiration and namespace isolation.

    Example:
        ```python
        config = CacheConfig(cache_dir="/tmp/cache", default_ttl_seconds=3600)
        cache = ResultCache(config)

        # Store a value
        await cache.set("my_key", {"result": "data"}, namespace="stage_a")

        # Retrieve a value
        result = await cache.get("my_key", namespace="stage_a")

        # Invalidate
        await cache.invalidate("my_key", namespace="stage_a")
        ```

    Attributes:
        config: Cache configuration.
    """

    def __init__(self, config: Optional[CacheConfig] = None) -> None:
        """Initialize the cache.

        Args:
            config: Cache configuration. Uses defaults if not provided.

        Thread Safety:
            This cache uses both threading.RLock (for thread safety) and
            asyncio.Lock (for coroutine safety). Safe to use in multi-threaded
            async environments like gunicorn with multiple workers.
        """
        self.config = config or CacheConfig()
        self._memory_cache: Dict[str, CacheEntry[Any]] = {}
        self._access_order: list[str] = []  # For LRU eviction
        # Thread-safe locks (P1 fix: asyncio.Lock alone doesn't protect threads)
        self._thread_lock = threading.RLock()
        self._disk_thread_lock = threading.RLock()
        # Async locks for coroutine synchronization
        self._lock = asyncio.Lock()
        self._disk_lock = asyncio.Lock()
        self._total_disk_size_bytes: int = 0
        self._initialized = False

    async def _ensure_initialized(self) -> None:
        """Ensure the cache directory exists and is initialized."""
        if self._initialized:
            return

        async with self._lock:
            if self._initialized:
                return

            if self.config.enable_disk_cache:
                cache_path = Path(self.config.cache_dir)
                cache_path.mkdir(parents=True, exist_ok=True)
                logger.debug(f"Initialized disk cache at: {cache_path}")

                # Calculate existing disk usage
                await self._calculate_disk_usage()

            self._initialized = True

    async def _calculate_disk_usage(self) -> None:
        """Calculate total disk cache size."""
        cache_path = Path(self.config.cache_dir)
        if not cache_path.exists():
            self._total_disk_size_bytes = 0
            return

        total = 0
        for file_path in cache_path.rglob("*.cache"):
            try:
                total += file_path.stat().st_size
            except OSError:
                continue
        self._total_disk_size_bytes = total

    @staticmethod
    def generate_key(key: str, namespace: str = "default") -> str:
        """Generate a cache key with namespace prefix.

        Args:
            key: The base key.
            namespace: The namespace to prefix.

        Returns:
            A namespaced cache key.
        """
        # Sanitize the key to be filesystem-safe
        safe_key = hashlib.sha256(key.encode()).hexdigest()[:32]
        return f"{namespace}:{safe_key}"

    @staticmethod
    def compute_image_hash(image_data: Union[bytes, str, Path]) -> str:
        """Compute a content-based hash for an image.

        This is useful for creating cache keys based on image content
        rather than file paths, ensuring cache hits for identical images.

        Args:
            image_data: Image bytes, file path string, or Path object.

        Returns:
            SHA-256 hash of the image content (first 32 chars).

        Raises:
            ValueError: If image_data type is not supported.
            FileNotFoundError: If image path does not exist.
        """
        if isinstance(image_data, bytes):
            content = image_data
        elif isinstance(image_data, (str, Path)):
            path = Path(image_data)
            if not path.exists():
                raise FileNotFoundError(f"Image file not found: {path}")
            content = path.read_bytes()
        else:
            raise ValueError(f"Unsupported image_data type: {type(image_data)}")

        return hashlib.sha256(content).hexdigest()[:32]

    def _get_disk_path(self, full_key: str) -> Path:
        """Get the disk path for a cache key."""
        namespace, key = full_key.split(":", 1)
        namespace_dir = Path(self.config.cache_dir) / namespace
        return namespace_dir / f"{key}.cache"

    async def get(
        self,
        key: str,
        namespace: str = "default",
        default: Optional[T] = None,
    ) -> Optional[T]:
        """Retrieve a value from the cache.

        Checks memory cache first, then disk cache.
        Expired entries are automatically removed.

        Args:
            key: The cache key.
            namespace: The namespace to look in.
            default: Value to return if key is not found.

        Returns:
            The cached value, or default if not found/expired.
        """
        await self._ensure_initialized()
        full_key = self.generate_key(key, namespace)

        # Try memory cache first
        if self.config.enable_memory_cache:
            # Thread lock for multi-threaded safety (P1 fix)
            with self._thread_lock:
                async with self._lock:
                    if full_key in self._memory_cache:
                        entry = self._memory_cache[full_key]
                        if entry.is_expired():
                            del self._memory_cache[full_key]
                            if full_key in self._access_order:
                                self._access_order.remove(full_key)
                            logger.debug(f"Cache expired (memory): {full_key}")
                        else:
                            # Update access order for LRU
                            if full_key in self._access_order:
                                self._access_order.remove(full_key)
                            self._access_order.append(full_key)
                            logger.debug(f"Cache hit (memory): {full_key}")
                            return entry.value

        # Try disk cache
        if self.config.enable_disk_cache:
            disk_path = self._get_disk_path(full_key)
            if disk_path.exists():
                async with self._disk_lock:
                    try:
                        entry = await self._read_disk_entry(disk_path)
                        if entry is not None:
                            if entry.is_expired():
                                await self._delete_disk_entry(disk_path)
                                logger.debug(f"Cache expired (disk): {full_key}")
                            else:
                                # Promote to memory cache
                                if self.config.enable_memory_cache:
                                    await self._set_memory(full_key, entry)
                                logger.debug(f"Cache hit (disk): {full_key}")
                                return entry.value
                    except Exception as e:
                        logger.warning(f"Error reading disk cache: {e}")

        logger.debug(f"Cache miss: {full_key}")
        return default

    async def set(
        self,
        key: str,
        value: T,
        namespace: str = "default",
        ttl_seconds: Optional[int] = None,
    ) -> None:
        """Store a value in the cache.

        Stores in both memory and disk cache (if enabled).

        Args:
            key: The cache key.
            value: The value to cache.
            namespace: The namespace to store in.
            ttl_seconds: Time-to-live in seconds. Uses config default if None.
                Set to 0 for infinite TTL.
        """
        await self._ensure_initialized()
        full_key = self.generate_key(key, namespace)

        ttl = ttl_seconds if ttl_seconds is not None else self.config.default_ttl_seconds
        expires_at = 0 if ttl == 0 else time.time() + ttl

        # Estimate size
        try:
            size_bytes = len(pickle.dumps(value))
        except Exception:
            size_bytes = 0

        entry: CacheEntry[T] = CacheEntry(
            value=value,
            created_at=time.time(),
            expires_at=expires_at,
            namespace=namespace,
            size_bytes=size_bytes,
        )

        # Store in memory cache
        if self.config.enable_memory_cache:
            await self._set_memory(full_key, entry)

        # Store in disk cache
        if self.config.enable_disk_cache:
            await self._set_disk(full_key, entry)

        logger.debug(f"Cache set: {full_key} (ttl={ttl}s, size={size_bytes}b)")

    async def _set_memory(self, full_key: str, entry: CacheEntry[Any]) -> None:
        """Store an entry in memory cache with LRU eviction."""
        # Thread lock for multi-threaded safety (P1 fix)
        with self._thread_lock:
            async with self._lock:
                # Evict if at capacity
                while len(self._memory_cache) >= self.config.memory_max_items:
                    if self._access_order:
                        oldest_key = self._access_order.pop(0)
                        if oldest_key in self._memory_cache:
                            del self._memory_cache[oldest_key]
                            logger.debug(f"Evicted from memory cache (LRU): {oldest_key}")
                    else:
                        break

                self._memory_cache[full_key] = entry
                if full_key in self._access_order:
                    self._access_order.remove(full_key)
                self._access_order.append(full_key)

    async def _set_disk(self, full_key: str, entry: CacheEntry[Any]) -> None:
        """Store an entry in disk cache with size-based eviction."""
        async with self._disk_lock:
            disk_path = self._get_disk_path(full_key)
            disk_path.parent.mkdir(parents=True, exist_ok=True)

            # Check if we need to evict
            max_bytes = self.config.max_size_mb * 1024 * 1024
            while self._total_disk_size_bytes + entry.size_bytes > max_bytes:
                evicted = await self._evict_oldest_disk_entry()
                if not evicted:
                    break

            try:
                await self._write_disk_entry(disk_path, entry)
                self._total_disk_size_bytes += entry.size_bytes
            except Exception as e:
                logger.warning(f"Error writing to disk cache: {e}")

    async def _read_disk_entry(self, path: Path) -> Optional[CacheEntry[Any]]:
        """Read a cache entry from disk."""
        try:
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, path.read_bytes)
            return pickle.loads(data)
        except Exception as e:
            logger.warning(f"Error reading disk cache entry {path}: {e}")
            return None

    async def _write_disk_entry(self, path: Path, entry: CacheEntry[Any]) -> None:
        """Write a cache entry to disk."""
        try:
            data = pickle.dumps(entry)
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, path.write_bytes, data)
        except Exception as e:
            logger.warning(f"Error writing disk cache entry {path}: {e}")
            raise

    async def _delete_disk_entry(self, path: Path) -> None:
        """Delete a cache entry from disk."""
        try:
            if path.exists():
                size = path.stat().st_size
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, path.unlink)
                self._total_disk_size_bytes = max(0, self._total_disk_size_bytes - size)
        except Exception as e:
            logger.warning(f"Error deleting disk cache entry {path}: {e}")

    async def _evict_oldest_disk_entry(self) -> bool:
        """Evict the oldest disk cache entry.

        Returns:
            True if an entry was evicted, False otherwise.
        """
        cache_path = Path(self.config.cache_dir)
        if not cache_path.exists():
            return False

        oldest_file: Optional[Path] = None
        oldest_time = float("inf")

        for file_path in cache_path.rglob("*.cache"):
            try:
                mtime = file_path.stat().st_mtime
                if mtime < oldest_time:
                    oldest_time = mtime
                    oldest_file = file_path
            except OSError:
                continue

        if oldest_file:
            await self._delete_disk_entry(oldest_file)
            logger.debug(f"Evicted from disk cache (oldest): {oldest_file}")
            return True
        return False

    async def invalidate(
        self,
        key: str,
        namespace: str = "default",
    ) -> bool:
        """Remove a specific entry from the cache.

        Removes from both memory and disk cache.

        Args:
            key: The cache key.
            namespace: The namespace to invalidate in.

        Returns:
            True if an entry was removed, False otherwise.
        """
        await self._ensure_initialized()
        full_key = self.generate_key(key, namespace)
        removed = False

        # Remove from memory
        if self.config.enable_memory_cache:
            async with self._lock:
                if full_key in self._memory_cache:
                    del self._memory_cache[full_key]
                    if full_key in self._access_order:
                        self._access_order.remove(full_key)
                    removed = True
                    logger.debug(f"Invalidated from memory: {full_key}")

        # Remove from disk
        if self.config.enable_disk_cache:
            disk_path = self._get_disk_path(full_key)
            if disk_path.exists():
                await self._delete_disk_entry(disk_path)
                removed = True
                logger.debug(f"Invalidated from disk: {full_key}")

        return removed

    async def invalidate_namespace(self, namespace: str) -> int:
        """Remove all entries in a namespace.

        Args:
            namespace: The namespace to clear.

        Returns:
            Number of entries removed.
        """
        await self._ensure_initialized()
        count = 0
        prefix = f"{namespace}:"

        # Remove from memory
        if self.config.enable_memory_cache:
            async with self._lock:
                keys_to_remove = [k for k in self._memory_cache if k.startswith(prefix)]
                for key in keys_to_remove:
                    del self._memory_cache[key]
                    if key in self._access_order:
                        self._access_order.remove(key)
                    count += 1

        # Remove from disk
        if self.config.enable_disk_cache:
            namespace_dir = Path(self.config.cache_dir) / namespace
            if namespace_dir.exists():
                async with self._disk_lock:
                    for file_path in namespace_dir.glob("*.cache"):
                        await self._delete_disk_entry(file_path)
                        count += 1
                    try:
                        # Remove empty namespace directory
                        if namespace_dir.exists() and not any(namespace_dir.iterdir()):
                            namespace_dir.rmdir()
                    except OSError:
                        pass

        logger.info(f"Invalidated namespace '{namespace}': {count} entries removed")
        return count

    async def clear(self) -> int:
        """Clear all cache entries.

        Returns:
            Number of entries removed.
        """
        await self._ensure_initialized()
        count = 0

        # Clear memory
        if self.config.enable_memory_cache:
            async with self._lock:
                count += len(self._memory_cache)
                self._memory_cache.clear()
                self._access_order.clear()

        # Clear disk
        if self.config.enable_disk_cache:
            cache_path = Path(self.config.cache_dir)
            if cache_path.exists():
                async with self._disk_lock:
                    for file_path in cache_path.rglob("*.cache"):
                        try:
                            file_path.unlink()
                            count += 1
                        except OSError:
                            continue
                    self._total_disk_size_bytes = 0

                    # Clean up empty directories
                    for dir_path in sorted(cache_path.rglob("*"), reverse=True):
                        if dir_path.is_dir() and not any(dir_path.iterdir()):
                            try:
                                dir_path.rmdir()
                            except OSError:
                                pass

        logger.info(f"Cache cleared: {count} entries removed")
        return count

    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics.
        """
        await self._ensure_initialized()

        memory_count = len(self._memory_cache) if self.config.enable_memory_cache else 0
        memory_size = sum(e.size_bytes for e in self._memory_cache.values()) if self.config.enable_memory_cache else 0

        disk_count = 0
        if self.config.enable_disk_cache:
            cache_path = Path(self.config.cache_dir)
            if cache_path.exists():
                disk_count = sum(1 for _ in cache_path.rglob("*.cache"))

        # Collect namespaces
        namespaces = set()
        for key in self._memory_cache:
            ns = key.split(":")[0]
            namespaces.add(ns)

        if self.config.enable_disk_cache:
            cache_path = Path(self.config.cache_dir)
            if cache_path.exists():
                for dir_path in cache_path.iterdir():
                    if dir_path.is_dir():
                        namespaces.add(dir_path.name)

        return {
            "memory_cache": {
                "enabled": self.config.enable_memory_cache,
                "count": memory_count,
                "max_items": self.config.memory_max_items,
                "size_bytes": memory_size,
            },
            "disk_cache": {
                "enabled": self.config.enable_disk_cache,
                "count": disk_count,
                "max_size_mb": self.config.max_size_mb,
                "size_bytes": self._total_disk_size_bytes,
                "path": self.config.cache_dir,
            },
            "config": {
                "default_ttl_seconds": self.config.default_ttl_seconds,
                "compression_enabled": self.config.compression_enabled,
            },
            "namespaces": sorted(namespaces),
        }

    async def cleanup_expired(self) -> int:
        """Remove all expired entries.

        Returns:
            Number of entries removed.
        """
        await self._ensure_initialized()
        count = 0

        # Cleanup memory
        if self.config.enable_memory_cache:
            async with self._lock:
                expired_keys = [
                    k for k, v in self._memory_cache.items() if v.is_expired()
                ]
                for key in expired_keys:
                    del self._memory_cache[key]
                    if key in self._access_order:
                        self._access_order.remove(key)
                    count += 1

        # Cleanup disk
        if self.config.enable_disk_cache:
            cache_path = Path(self.config.cache_dir)
            if cache_path.exists():
                async with self._disk_lock:
                    for file_path in cache_path.rglob("*.cache"):
                        try:
                            entry = await self._read_disk_entry(file_path)
                            if entry is not None and entry.is_expired():
                                await self._delete_disk_entry(file_path)
                                count += 1
                        except Exception:
                            continue

        logger.info(f"Cleaned up {count} expired entries")
        return count


# =============================================================================
# Global Instance
# =============================================================================

_global_cache: Optional[ResultCache] = None
_global_lock = asyncio.Lock()


async def get_cache(config: Optional[CacheConfig] = None) -> ResultCache:
    """Get or create the global cache instance.

    This is the recommended way to access the cache in most cases.
    The cache is lazily initialized on first access.

    Args:
        config: Optional configuration for the cache.
            Only used if the cache hasn't been initialized yet.

    Returns:
        The global ResultCache instance.

    Example:
        ```python
        cache = await get_cache()
        await cache.set("key", "value")
        result = await cache.get("key")
        ```
    """
    global _global_cache

    if _global_cache is None:
        async with _global_lock:
            if _global_cache is None:
                _global_cache = ResultCache(config)
                await _global_cache._ensure_initialized()
                logger.info("Global cache initialized")

    return _global_cache


def get_cache_sync(config: Optional[CacheConfig] = None) -> ResultCache:
    """Get or create the global cache instance synchronously.

    Use this when you need to access the cache from synchronous code.
    Note: You still need to use async methods for cache operations.

    Args:
        config: Optional configuration for the cache.

    Returns:
        The global ResultCache instance.
    """
    global _global_cache

    if _global_cache is None:
        _global_cache = ResultCache(config)
        logger.info("Global cache initialized (sync)")

    return _global_cache


def reset_global_cache() -> None:
    """Reset the global cache instance.

    This is primarily useful for testing.
    """
    global _global_cache
    _global_cache = None
    logger.debug("Global cache reset")


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "CacheConfig",
    "CacheEntry",
    "ResultCache",
    "get_cache",
    "get_cache_sync",
    "reset_global_cache",
]
