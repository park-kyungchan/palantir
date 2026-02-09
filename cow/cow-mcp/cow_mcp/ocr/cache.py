"""Disk-based OCR result cache using diskcache with SHA256 content-hash keys."""

import hashlib
import json
import logging
from pathlib import Path
from typing import Optional

import diskcache

logger = logging.getLogger("cow-mcp.ocr.cache")

DEFAULT_CACHE_DIR = Path.home() / ".cow" / "cache" / "ocr"
DEFAULT_SIZE_LIMIT = 1024 * 1024 * 512  # 512 MB


class OcrCache:
    """Disk cache for OCR results keyed by content hash."""

    def __init__(
        self,
        cache_dir: str | Path | None = None,
        size_limit: int = DEFAULT_SIZE_LIMIT,
    ):
        self._cache_dir = Path(cache_dir) if cache_dir else DEFAULT_CACHE_DIR
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._cache = diskcache.Cache(
            str(self._cache_dir),
            size_limit=size_limit,
        )

    @staticmethod
    def content_hash(image_bytes: bytes, options: dict | None = None) -> str:
        """Generate SHA256 hash from image bytes and options."""
        h = hashlib.sha256(image_bytes)
        if options:
            h.update(json.dumps(options, sort_keys=True).encode())
        return h.hexdigest()

    def get(self, content_hash: str) -> Optional[dict]:
        """Retrieve cached OCR result by content hash. Returns raw dict or None."""
        try:
            value = self._cache.get(content_hash)
            if value is not None:
                logger.debug(f"Cache hit: {content_hash[:16]}...")
                return json.loads(value) if isinstance(value, str) else value
        except Exception as e:
            logger.warning(f"Cache read error: {e}")
        return None

    def set(self, content_hash: str, result_dict: dict) -> None:
        """Store OCR result dict in cache."""
        try:
            self._cache.set(content_hash, json.dumps(result_dict))
            logger.debug(f"Cached: {content_hash[:16]}...")
        except Exception as e:
            logger.warning(f"Cache write error: {e}")

    def close(self) -> None:
        """Close the cache."""
        self._cache.close()
