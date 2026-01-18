"""
Storage Manager for Stage H (Export).

Manages storage of exported files:
- Local filesystem storage
- Cloud storage abstraction (S3, GCS, Azure)
- Caching and cleanup
- URL generation

Module Version: 1.0.0
"""

import hashlib
import logging
import os
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol

from ..schemas.export import (
    ExportSpec,
    StorageConfig,
    StorageType,
)
from .exceptions import StorageError

logger = logging.getLogger(__name__)


# =============================================================================
# Storage Protocol
# =============================================================================

class StorageBackend(Protocol):
    """Protocol for storage backend implementations."""

    def save(self, data: bytes, path: str) -> str:
        """Save data to storage."""
        ...

    def load(self, path: str) -> bytes:
        """Load data from storage."""
        ...

    def delete(self, path: str) -> bool:
        """Delete file from storage."""
        ...

    def exists(self, path: str) -> bool:
        """Check if file exists."""
        ...

    def get_url(self, path: str, expires_in: int = 3600) -> str:
        """Get URL for file access."""
        ...


# =============================================================================
# Local Storage Backend
# =============================================================================

class LocalStorageBackend:
    """Local filesystem storage backend.

    Stores files on the local filesystem with basic
    organization and cleanup capabilities.
    """

    def __init__(self, base_path: Path):
        """Initialize local storage.

        Args:
            base_path: Base directory for storage
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _resolve_path(self, path: str) -> Path:
        """Resolve relative path to absolute.

        Args:
            path: Relative path

        Returns:
            Absolute Path
        """
        resolved = self.base_path / path
        # Security: ensure path doesn't escape base
        if not str(resolved.resolve()).startswith(str(self.base_path.resolve())):
            raise StorageError(
                f"Path escapes base directory: {path}",
                storage_type="local",
                path=path,
            )
        return resolved

    def save(self, data: bytes, path: str) -> str:
        """Save data to local filesystem.

        Args:
            data: Data to save
            path: Relative path

        Returns:
            Absolute path to saved file
        """
        filepath = self._resolve_path(path)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        try:
            filepath.write_bytes(data)
            logger.debug(f"Saved {len(data)} bytes to {filepath}")
            return str(filepath.absolute())

        except Exception as e:
            raise StorageError(
                f"Failed to save file: {e}",
                storage_type="local",
                path=str(filepath),
                operation="save",
            )

    def load(self, path: str) -> bytes:
        """Load data from local filesystem.

        Args:
            path: Relative or absolute path

        Returns:
            File contents as bytes
        """
        # Handle both relative and absolute paths
        if Path(path).is_absolute():
            filepath = Path(path)
        else:
            filepath = self._resolve_path(path)

        try:
            return filepath.read_bytes()

        except FileNotFoundError:
            raise StorageError(
                f"File not found: {path}",
                storage_type="local",
                path=str(filepath),
                operation="load",
            )
        except Exception as e:
            raise StorageError(
                f"Failed to load file: {e}",
                storage_type="local",
                path=str(filepath),
                operation="load",
            )

    def delete(self, path: str) -> bool:
        """Delete file from local filesystem.

        Args:
            path: Relative path

        Returns:
            True if deleted, False if not found
        """
        filepath = self._resolve_path(path)

        try:
            if filepath.exists():
                filepath.unlink()
                logger.debug(f"Deleted {filepath}")
                return True
            return False

        except Exception as e:
            raise StorageError(
                f"Failed to delete file: {e}",
                storage_type="local",
                path=str(filepath),
                operation="delete",
            )

    def exists(self, path: str) -> bool:
        """Check if file exists.

        Args:
            path: Relative path

        Returns:
            True if exists
        """
        filepath = self._resolve_path(path)
        return filepath.exists()

    def get_url(self, path: str, expires_in: int = 3600) -> str:
        """Get file:// URL for local file.

        Args:
            path: Relative path
            expires_in: Ignored for local storage

        Returns:
            file:// URL
        """
        filepath = self._resolve_path(path)
        return f"file://{filepath.absolute()}"

    def list_files(self, prefix: str = "") -> List[str]:
        """List files with optional prefix.

        Args:
            prefix: Path prefix filter

        Returns:
            List of relative paths
        """
        base = self._resolve_path(prefix) if prefix else self.base_path
        files = []

        if base.exists():
            for filepath in base.rglob("*"):
                if filepath.is_file():
                    rel_path = filepath.relative_to(self.base_path)
                    files.append(str(rel_path))

        return sorted(files)

    def cleanup_expired(
        self,
        max_age_days: int = 30,
        dry_run: bool = False,
    ) -> List[str]:
        """Remove files older than max_age_days.

        Args:
            max_age_days: Maximum file age
            dry_run: If True, don't actually delete

        Returns:
            List of deleted (or would-be-deleted) files
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)
        deleted = []

        for filepath in self.base_path.rglob("*"):
            if filepath.is_file():
                mtime = datetime.fromtimestamp(
                    filepath.stat().st_mtime,
                    tz=timezone.utc
                )
                if mtime < cutoff:
                    rel_path = str(filepath.relative_to(self.base_path))
                    if not dry_run:
                        filepath.unlink()
                    deleted.append(rel_path)

        logger.info(
            f"Cleanup: {'would delete' if dry_run else 'deleted'} "
            f"{len(deleted)} expired files"
        )
        return deleted


# =============================================================================
# Memory Storage Backend (for testing)
# =============================================================================

class MemoryStorageBackend:
    """In-memory storage backend for testing."""

    def __init__(self):
        self._storage: Dict[str, bytes] = {}

    def save(self, data: bytes, path: str) -> str:
        self._storage[path] = data
        return path

    def load(self, path: str) -> bytes:
        if path not in self._storage:
            raise StorageError(f"File not found: {path}", storage_type="memory")
        return self._storage[path]

    def delete(self, path: str) -> bool:
        if path in self._storage:
            del self._storage[path]
            return True
        return False

    def exists(self, path: str) -> bool:
        return path in self._storage

    def get_url(self, path: str, expires_in: int = 3600) -> str:
        return f"memory://{path}"

    def clear(self):
        """Clear all stored data."""
        self._storage.clear()


# =============================================================================
# Storage Manager
# =============================================================================

class StorageManager:
    """Manages export file storage.

    Provides a unified interface for storing and retrieving
    export files across different storage backends.

    Usage:
        manager = StorageManager()

        # Save export
        path = manager.save_export(export_spec, content)

        # Load export
        content = manager.load_export(export_spec)

        # Cleanup old exports
        manager.cleanup_expired(max_age_days=30)
    """

    def __init__(self, config: Optional[StorageConfig] = None):
        """Initialize storage manager.

        Args:
            config: Storage configuration
        """
        self.config = config or StorageConfig()
        self._backend = self._create_backend()

        self._stats = {
            "saves": 0,
            "loads": 0,
            "deletes": 0,
            "bytes_saved": 0,
            "bytes_loaded": 0,
        }

        logger.debug(
            f"StorageManager initialized: type={self.config.storage_type.value}, "
            f"base_path={self.config.base_path}"
        )

    @property
    def stats(self) -> Dict[str, int]:
        """Get storage statistics."""
        return self._stats.copy()

    def _create_backend(self) -> StorageBackend:
        """Create storage backend based on config.

        Returns:
            Storage backend instance
        """
        if self.config.storage_type == StorageType.LOCAL:
            return LocalStorageBackend(Path(self.config.base_path))

        elif self.config.storage_type == StorageType.MEMORY:
            return MemoryStorageBackend()

        elif self.config.storage_type == StorageType.S3:
            # S3 backend would require boto3
            logger.warning("S3 storage not fully implemented, using local fallback")
            return LocalStorageBackend(Path(self.config.base_path))

        elif self.config.storage_type == StorageType.GCS:
            # GCS backend would require google-cloud-storage
            logger.warning("GCS storage not fully implemented, using local fallback")
            return LocalStorageBackend(Path(self.config.base_path))

        elif self.config.storage_type == StorageType.AZURE:
            # Azure backend would require azure-storage-blob
            logger.warning("Azure storage not fully implemented, using local fallback")
            return LocalStorageBackend(Path(self.config.base_path))

        else:
            raise StorageError(
                f"Unknown storage type: {self.config.storage_type}",
                storage_type=self.config.storage_type.value,
            )

    def _generate_path(
        self,
        export_id: str,
        format_type: str,
        image_id: str,
    ) -> str:
        """Generate storage path for export.

        Args:
            export_id: Export identifier
            format_type: Export format
            image_id: Source image ID

        Returns:
            Storage path
        """
        # Organize by date and format
        date_prefix = datetime.now(timezone.utc).strftime("%Y/%m/%d")
        return f"{date_prefix}/{format_type}/{image_id}_{export_id}"

    def save_export(
        self,
        spec: ExportSpec,
        content: bytes,
    ) -> str:
        """Save export content.

        Args:
            spec: Export specification
            content: Content to save

        Returns:
            Storage path/URL
        """
        path = self._generate_path(
            spec.export_id,
            spec.format.value,
            spec.image_id,
        )

        # Add extension
        ext_map = {
            "json": ".json",
            "pdf": ".pdf",
            "latex": ".tex",
            "svg": ".svg",
            "zip": ".zip",
        }
        ext = ext_map.get(spec.format.value, "")
        path = f"{path}{ext}"

        result = self._backend.save(content, path)

        self._stats["saves"] += 1
        self._stats["bytes_saved"] += len(content)

        logger.debug(f"Saved export {spec.export_id} to {path}")
        return result

    def load_export(self, spec: ExportSpec) -> bytes:
        """Load export content.

        Args:
            spec: Export specification with file_path

        Returns:
            Export content bytes
        """
        path = spec.file_path or spec.storage_url

        if not path:
            raise StorageError(
                "No storage path in export spec",
                storage_type=self.config.storage_type.value,
            )

        content = self._backend.load(path)

        self._stats["loads"] += 1
        self._stats["bytes_loaded"] += len(content)

        return content

    def delete_export(self, spec: ExportSpec) -> bool:
        """Delete export file.

        Args:
            spec: Export specification

        Returns:
            True if deleted
        """
        path = spec.file_path or spec.storage_url

        if not path:
            return False

        result = self._backend.delete(path)

        if result:
            self._stats["deletes"] += 1

        return result

    def get_url(
        self,
        spec: ExportSpec,
        expires_in: int = 3600,
    ) -> str:
        """Get access URL for export.

        Args:
            spec: Export specification
            expires_in: URL expiration in seconds

        Returns:
            Access URL
        """
        path = spec.file_path or spec.storage_url

        if not path:
            raise StorageError(
                "No storage path in export spec",
                storage_type=self.config.storage_type.value,
            )

        return self._backend.get_url(path, expires_in)

    def cleanup_expired(
        self,
        max_age_days: Optional[int] = None,
        dry_run: bool = False,
    ) -> List[str]:
        """Remove expired export files.

        Args:
            max_age_days: Maximum age (uses config default if None)
            dry_run: If True, don't actually delete

        Returns:
            List of deleted file paths
        """
        age = max_age_days or self.config.retention_days

        if hasattr(self._backend, "cleanup_expired"):
            return self._backend.cleanup_expired(age, dry_run)

        logger.warning(f"Cleanup not supported for {self.config.storage_type}")
        return []


# =============================================================================
# Factory Function
# =============================================================================

def create_storage_manager(
    config: Optional[StorageConfig] = None,
    **kwargs,
) -> StorageManager:
    """Factory function to create StorageManager.

    Args:
        config: Optional StorageConfig
        **kwargs: Config overrides

    Returns:
        Configured StorageManager instance
    """
    if config is None and kwargs:
        config = StorageConfig(**kwargs)
    return StorageManager(config=config)


# =============================================================================
# Export
# =============================================================================

__all__ = [
    "StorageManager",
    "StorageConfig",
    "LocalStorageBackend",
    "MemoryStorageBackend",
    "create_storage_manager",
]
