"""
Embedding Cache Layer (4.1.4)
=============================
Caching layer for embedding results to reduce API calls and improve performance.

Features:
- LRU cache with configurable size
- TTL (time-to-live) support
- Thread-safe operations
- Async-compatible
- Memory and disk persistence options

Usage:
    from lib.oda.semantic.cache import EmbeddingCache, CacheConfig

    config = CacheConfig(max_size=10000, ttl_seconds=3600)
    cache = EmbeddingCache(config)

    # Check cache
    result = await cache.get(text_hash)
    if result is None:
        result = await provider.embed(text)
        await cache.set(text_hash, result)
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import sqlite3
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

from lib.oda.semantic.embedding import EmbeddingResult


class CacheConfig(BaseModel):
    """Configuration for embedding cache."""

    max_size: int = Field(
        default=10000,
        ge=100,
        description="Maximum number of entries in cache"
    )
    ttl_seconds: Optional[int] = Field(
        default=3600 * 24,  # 24 hours
        ge=0,
        description="Time-to-live in seconds (None for no expiry)"
    )
    persist_to_disk: bool = Field(
        default=True,
        description="Whether to persist cache to disk"
    )
    cache_dir: Optional[str] = Field(
        default=None,
        description="Directory for disk cache (default: ~/.cache/oda/embeddings)"
    )
    write_through: bool = Field(
        default=True,
        description="Write to disk immediately on set"
    )
    preload_on_init: bool = Field(
        default=True,
        description="Load existing cache from disk on initialization"
    )

    def get_cache_dir(self) -> Path:
        """Get the cache directory path."""
        if self.cache_dir:
            return Path(self.cache_dir)
        return Path.home() / ".cache" / "oda" / "embeddings"


@dataclass
class CacheEntry:
    """A single cache entry with metadata."""
    result: EmbeddingResult
    created_at: float = field(default_factory=time.time)
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)

    def is_expired(self, ttl_seconds: Optional[int]) -> bool:
        """Check if entry has expired."""
        if ttl_seconds is None:
            return False
        return (time.time() - self.created_at) > ttl_seconds


class CacheStats(BaseModel):
    """Statistics for cache operations."""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    size: int = 0
    max_size: int = 0

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


class EmbeddingCache:
    """
    LRU cache for embedding results with TTL support.

    Thread-safe and async-compatible. Supports both memory and disk storage.
    """

    def __init__(self, config: Optional[CacheConfig] = None):
        """
        Initialize the embedding cache.

        Args:
            config: Cache configuration
        """
        self._config = config or CacheConfig()
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        self._stats = CacheStats(max_size=self._config.max_size)

        # Initialize disk cache if enabled
        self._db: Optional[sqlite3.Connection] = None
        if self._config.persist_to_disk:
            self._init_disk_cache()

        # Preload from disk if configured
        if self._config.preload_on_init and self._config.persist_to_disk:
            self._preload_from_disk()

    def _init_disk_cache(self) -> None:
        """Initialize SQLite database for disk cache."""
        cache_dir = self._config.get_cache_dir()
        cache_dir.mkdir(parents=True, exist_ok=True)
        db_path = cache_dir / "embeddings.db"

        self._db = sqlite3.connect(str(db_path), check_same_thread=False)
        self._db.execute("""
            CREATE TABLE IF NOT EXISTS embeddings (
                text_hash TEXT PRIMARY KEY,
                vector BLOB NOT NULL,
                dimension INTEGER NOT NULL,
                model TEXT NOT NULL,
                token_count INTEGER,
                normalized INTEGER,
                metadata TEXT,
                created_at REAL NOT NULL,
                access_count INTEGER DEFAULT 0,
                last_accessed REAL
            )
        """)
        self._db.execute("""
            CREATE INDEX IF NOT EXISTS idx_created_at ON embeddings(created_at)
        """)
        self._db.commit()

    def _preload_from_disk(self) -> None:
        """Preload cache entries from disk."""
        if self._db is None:
            return

        try:
            cursor = self._db.execute("""
                SELECT text_hash, vector, dimension, model, token_count,
                       normalized, metadata, created_at, access_count, last_accessed
                FROM embeddings
                ORDER BY last_accessed DESC
                LIMIT ?
            """, (self._config.max_size,))

            for row in cursor:
                text_hash = row[0]
                vector = json.loads(row[1])
                result = EmbeddingResult(
                    vector=vector,
                    dimension=row[2],
                    model=row[3],
                    text_hash=text_hash,
                    token_count=row[4],
                    normalized=bool(row[5]),
                    metadata=json.loads(row[6]) if row[6] else {}
                )
                entry = CacheEntry(
                    result=result,
                    created_at=row[7],
                    access_count=row[8] or 0,
                    last_accessed=row[9] or row[7]
                )
                self._cache[text_hash] = entry

            self._stats.size = len(self._cache)

        except Exception:
            # Ignore preload errors
            pass

    @staticmethod
    def compute_hash(text: str) -> str:
        """
        Compute hash key for text.

        Args:
            text: Input text

        Returns:
            Hash string suitable for cache key
        """
        return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]

    async def get(self, text: str) -> Optional[EmbeddingResult]:
        """
        Get embedding from cache.

        Args:
            text: Original text (will be hashed)

        Returns:
            EmbeddingResult if found and not expired, None otherwise
        """
        text_hash = self.compute_hash(text)
        return await self.get_by_hash(text_hash)

    async def get_by_hash(self, text_hash: str) -> Optional[EmbeddingResult]:
        """
        Get embedding from cache by hash.

        Args:
            text_hash: Pre-computed text hash

        Returns:
            EmbeddingResult if found and not expired, None otherwise
        """
        with self._lock:
            entry = self._cache.get(text_hash)

            if entry is None:
                self._stats.misses += 1
                return None

            # Check expiry
            if entry.is_expired(self._config.ttl_seconds):
                del self._cache[text_hash]
                self._stats.misses += 1
                self._stats.size = len(self._cache)
                return None

            # Update access stats
            entry.access_count += 1
            entry.last_accessed = time.time()

            # Move to end (most recently used)
            self._cache.move_to_end(text_hash)

            self._stats.hits += 1
            return entry.result

    async def set(
        self,
        text: str,
        result: EmbeddingResult
    ) -> None:
        """
        Store embedding in cache.

        Args:
            text: Original text (will be hashed)
            result: Embedding result to cache
        """
        text_hash = self.compute_hash(text)
        await self.set_by_hash(text_hash, result)

    async def set_by_hash(
        self,
        text_hash: str,
        result: EmbeddingResult
    ) -> None:
        """
        Store embedding in cache by hash.

        Args:
            text_hash: Pre-computed text hash
            result: Embedding result to cache
        """
        with self._lock:
            # Evict if at capacity
            while len(self._cache) >= self._config.max_size:
                # Remove oldest (first item in OrderedDict)
                evicted_hash, _ = self._cache.popitem(last=False)
                self._stats.evictions += 1
                # Remove from disk cache too
                if self._db is not None:
                    try:
                        self._db.execute(
                            "DELETE FROM embeddings WHERE text_hash = ?",
                            (evicted_hash,)
                        )
                    except Exception:
                        pass

            # Add new entry
            entry = CacheEntry(result=result)
            self._cache[text_hash] = entry
            self._stats.size = len(self._cache)

            # Write to disk if configured
            if self._config.write_through and self._db is not None:
                await self._write_to_disk(text_hash, entry)

    async def _write_to_disk(self, text_hash: str, entry: CacheEntry) -> None:
        """Write entry to disk cache."""
        if self._db is None:
            return

        try:
            self._db.execute("""
                INSERT OR REPLACE INTO embeddings
                (text_hash, vector, dimension, model, token_count,
                 normalized, metadata, created_at, access_count, last_accessed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                text_hash,
                json.dumps(entry.result.vector),
                entry.result.dimension,
                entry.result.model,
                entry.result.token_count,
                int(entry.result.normalized),
                json.dumps(entry.result.metadata),
                entry.created_at,
                entry.access_count,
                entry.last_accessed
            ))
            self._db.commit()
        except Exception:
            # Ignore disk write errors
            pass

    async def delete(self, text: str) -> bool:
        """
        Remove embedding from cache.

        Args:
            text: Original text (will be hashed)

        Returns:
            True if entry was removed, False if not found
        """
        text_hash = self.compute_hash(text)
        return await self.delete_by_hash(text_hash)

    async def delete_by_hash(self, text_hash: str) -> bool:
        """
        Remove embedding from cache by hash.

        Args:
            text_hash: Pre-computed text hash

        Returns:
            True if entry was removed, False if not found
        """
        with self._lock:
            if text_hash in self._cache:
                del self._cache[text_hash]
                self._stats.size = len(self._cache)

                # Remove from disk
                if self._db is not None:
                    try:
                        self._db.execute(
                            "DELETE FROM embeddings WHERE text_hash = ?",
                            (text_hash,)
                        )
                        self._db.commit()
                    except Exception:
                        pass

                return True
            return False

    async def clear(self) -> None:
        """Clear all entries from cache."""
        with self._lock:
            self._cache.clear()
            self._stats.size = 0
            self._stats.evictions += self._stats.size

            # Clear disk cache
            if self._db is not None:
                try:
                    self._db.execute("DELETE FROM embeddings")
                    self._db.commit()
                except Exception:
                    pass

    async def get_batch(
        self,
        texts: List[str]
    ) -> Tuple[List[EmbeddingResult], List[str]]:
        """
        Get multiple embeddings from cache.

        Args:
            texts: List of texts to look up

        Returns:
            Tuple of (found results, texts not found)
        """
        found: List[EmbeddingResult] = []
        not_found: List[str] = []

        for text in texts:
            result = await self.get(text)
            if result is not None:
                found.append(result)
            else:
                not_found.append(text)

        return found, not_found

    async def set_batch(
        self,
        texts: List[str],
        results: List[EmbeddingResult]
    ) -> None:
        """
        Store multiple embeddings in cache.

        Args:
            texts: List of original texts
            results: List of embedding results
        """
        for text, result in zip(texts, results):
            await self.set(text, result)

    def get_stats(self) -> CacheStats:
        """Get cache statistics."""
        with self._lock:
            self._stats.size = len(self._cache)
            return self._stats.model_copy()

    async def cleanup_expired(self) -> int:
        """
        Remove all expired entries.

        Returns:
            Number of entries removed
        """
        if self._config.ttl_seconds is None:
            return 0

        removed = 0
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired(self._config.ttl_seconds)
            ]
            for key in expired_keys:
                del self._cache[key]
                removed += 1

            # Update disk cache
            if self._db is not None and removed > 0:
                cutoff = time.time() - self._config.ttl_seconds
                try:
                    self._db.execute(
                        "DELETE FROM embeddings WHERE created_at < ?",
                        (cutoff,)
                    )
                    self._db.commit()
                except Exception:
                    pass

            self._stats.size = len(self._cache)

        return removed

    def close(self) -> None:
        """Close cache and release resources."""
        with self._lock:
            if self._db is not None:
                self._db.close()
                self._db = None

    def __enter__(self) -> "EmbeddingCache":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()


class CachedEmbeddingProvider:
    """
    Wrapper that adds caching to any EmbeddingProvider.

    Usage:
        from lib.oda.semantic.providers.openai import OpenAIEmbeddingProvider

        provider = OpenAIEmbeddingProvider(config)
        cached = CachedEmbeddingProvider(provider)

        result = await cached.embed("Hello, world!")  # API call
        result = await cached.embed("Hello, world!")  # Cache hit
    """

    def __init__(
        self,
        provider: Any,  # EmbeddingProvider
        cache: Optional[EmbeddingCache] = None,
        cache_config: Optional[CacheConfig] = None
    ):
        """
        Initialize cached provider.

        Args:
            provider: Base embedding provider
            cache: Optional existing cache instance
            cache_config: Config for new cache (if cache not provided)
        """
        self._provider = provider
        self._cache = cache or EmbeddingCache(cache_config)

    @property
    def dimension(self) -> int:
        """Return dimension from underlying provider."""
        return self._provider.dimension

    @property
    def model_name(self) -> str:
        """Return model name from underlying provider."""
        return self._provider.model_name

    async def embed(self, text: str) -> EmbeddingResult:
        """
        Generate embedding with cache lookup.

        Args:
            text: Text to embed

        Returns:
            EmbeddingResult from cache or provider
        """
        # Check cache first
        cached = await self._cache.get(text)
        if cached is not None:
            return cached

        # Generate embedding
        result = await self._provider.embed(text)

        # Store in cache
        await self._cache.set(text, result)

        return result

    async def embed_batch(
        self,
        texts: List[str],
        *,
        show_progress: bool = False
    ) -> List[EmbeddingResult]:
        """
        Generate embeddings with cache lookup.

        Args:
            texts: List of texts to embed
            show_progress: Whether to show progress

        Returns:
            List of EmbeddingResult
        """
        # Check cache for all texts
        found, not_found = await self._cache.get_batch(texts)

        # Generate embeddings for cache misses
        if not_found:
            new_results = await self._provider.embed_batch(
                not_found,
                show_progress=show_progress
            )
            await self._cache.set_batch(not_found, new_results)
            found.extend(new_results)

        return found

    def get_cache_stats(self) -> CacheStats:
        """Get cache statistics."""
        return self._cache.get_stats()

    async def close(self) -> None:
        """Close provider and cache."""
        await self._provider.close()
        self._cache.close()
