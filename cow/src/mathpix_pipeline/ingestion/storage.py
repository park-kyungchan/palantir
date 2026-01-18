"""
Storage manager for Stage A (Ingestion).

Handles temporary and persistent storage for processed images:
- Temporary storage for pipeline processing
- Caching for repeat processing
- Cleanup of temporary files

Schema Version: 2.0.0
"""

import hashlib
import json
import logging
import shutil
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .exceptions import StorageError
from .loader import LoadedImage
from .preprocessor import PreprocessingResult, Region

logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

DEFAULT_CACHE_DIR = ".mathpix_cache"
DEFAULT_TEMP_PREFIX = "mathpix_"


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class StoredImage:
    """Metadata for a stored image.

    Attributes:
        image_id: Unique identifier for the image
        path: File system path to the image
        format: Image format
        width: Image width
        height: Image height
        content_hash: SHA256 hash of image data
        source_type: Original source type
        source_location: Original source location
        preprocessing_applied: List of preprocessing operations
        stored_at: When the image was stored
        expires_at: When the image should be cleaned up (optional)
    """
    image_id: str
    path: str
    format: str
    width: int
    height: int
    content_hash: str
    source_type: str
    source_location: Optional[str]
    preprocessing_applied: List[str]
    stored_at: datetime
    expires_at: Optional[datetime] = None


# =============================================================================
# Storage Manager
# =============================================================================

class StorageManager:
    """Manages temporary and persistent image storage.

    Provides caching, temporary storage, and cleanup for images
    during pipeline processing.

    Usage:
        storage = StorageManager()
        stored = storage.save_processed(image, result, "img-001")
        cached = storage.load_cached("img-001")
        storage.cleanup()
    """

    def __init__(
        self,
        cache_dir: Optional[Union[str, Path]] = None,
        temp_dir: Optional[Union[str, Path]] = None,
        use_temp: bool = True,
        cache_enabled: bool = True,
    ):
        """Initialize storage manager.

        Args:
            cache_dir: Directory for persistent cache (default: .mathpix_cache)
            temp_dir: Directory for temporary files (default: system temp)
            use_temp: Whether to use temporary storage
            cache_enabled: Whether to enable caching
        """
        self.cache_enabled = cache_enabled
        self.use_temp = use_temp

        # Set up cache directory
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            self.cache_dir = Path.cwd() / DEFAULT_CACHE_DIR

        # Set up temp directory
        if temp_dir:
            self.temp_dir = Path(temp_dir)
        elif use_temp:
            self.temp_dir = Path(tempfile.mkdtemp(prefix=DEFAULT_TEMP_PREFIX))
        else:
            self.temp_dir = self.cache_dir / "temp"

        # Create directories
        self._ensure_directories()

        # Track stored images
        self._stored: Dict[str, StoredImage] = {}
        self._temp_files: List[Path] = []

    def _ensure_directories(self) -> None:
        """Create storage directories if they don't exist."""
        try:
            if self.cache_enabled:
                self.cache_dir.mkdir(parents=True, exist_ok=True)
                (self.cache_dir / "images").mkdir(exist_ok=True)
                (self.cache_dir / "metadata").mkdir(exist_ok=True)

            if self.use_temp:
                self.temp_dir.mkdir(parents=True, exist_ok=True)

        except OSError as e:
            raise StorageError(
                f"Failed to create storage directories: {e}",
                path=str(self.cache_dir),
                operation="mkdir",
            )

    def _generate_id(self, image: LoadedImage) -> str:
        """Generate unique ID for an image.

        Args:
            image: LoadedImage to generate ID for

        Returns:
            Unique image ID
        """
        return image.content_hash[:16]

    def _get_image_path(self, image_id: str, format: str, temp: bool = False) -> Path:
        """Get file path for image storage.

        Args:
            image_id: Image identifier
            format: Image format
            temp: Whether to use temp directory

        Returns:
            Path for image file
        """
        base_dir = self.temp_dir if temp else (self.cache_dir / "images")
        return base_dir / f"{image_id}.{format}"

    def _get_metadata_path(self, image_id: str) -> Path:
        """Get file path for image metadata.

        Args:
            image_id: Image identifier

        Returns:
            Path for metadata file
        """
        return self.cache_dir / "metadata" / f"{image_id}.json"

    def _save_metadata(self, stored: StoredImage) -> None:
        """Save image metadata to disk.

        Args:
            stored: StoredImage metadata to save
        """
        if not self.cache_enabled:
            return

        try:
            metadata_path = self._get_metadata_path(stored.image_id)
            metadata = asdict(stored)

            # Convert datetime to ISO format
            metadata["stored_at"] = stored.stored_at.isoformat()
            if stored.expires_at:
                metadata["expires_at"] = stored.expires_at.isoformat()

            with open(metadata_path, "w") as f:
                json.dump(metadata, f, indent=2)

        except Exception as e:
            logger.warning(f"Failed to save metadata for {stored.image_id}: {e}")

    def _load_metadata(self, image_id: str) -> Optional[StoredImage]:
        """Load image metadata from disk.

        Args:
            image_id: Image identifier

        Returns:
            StoredImage or None if not found
        """
        metadata_path = self._get_metadata_path(image_id)

        if not metadata_path.exists():
            return None

        try:
            with open(metadata_path, "r") as f:
                metadata = json.load(f)

            # Parse datetime
            metadata["stored_at"] = datetime.fromisoformat(metadata["stored_at"])
            if metadata.get("expires_at"):
                metadata["expires_at"] = datetime.fromisoformat(metadata["expires_at"])

            return StoredImage(**metadata)

        except Exception as e:
            logger.warning(f"Failed to load metadata for {image_id}: {e}")
            return None

    def save_processed(
        self,
        original: LoadedImage,
        result: PreprocessingResult,
        image_id: Optional[str] = None,
        temp: bool = False,
        expires_in_hours: Optional[int] = None,
    ) -> StoredImage:
        """Save processed image to storage.

        Args:
            original: Original LoadedImage
            result: PreprocessingResult with processed data
            image_id: Optional custom image ID
            temp: Whether to store in temp directory
            expires_in_hours: Auto-cleanup after this many hours

        Returns:
            StoredImage metadata

        Raises:
            StorageError: If storage fails
        """
        image_id = image_id or self._generate_id(original)

        # Determine storage path
        image_path = self._get_image_path(image_id, result.format, temp=temp)

        # Save image data
        try:
            with open(image_path, "wb") as f:
                f.write(result.data)

            if temp:
                self._temp_files.append(image_path)

        except OSError as e:
            raise StorageError(
                f"Failed to save image: {e}",
                path=str(image_path),
                operation="write",
            )

        # Calculate expiration
        expires_at = None
        if expires_in_hours:
            from datetime import timedelta
            expires_at = datetime.now(timezone.utc) + timedelta(hours=expires_in_hours)

        # Create metadata
        stored = StoredImage(
            image_id=image_id,
            path=str(image_path.absolute()),
            format=result.format,
            width=result.width,
            height=result.height,
            content_hash=original.content_hash,
            source_type=original.source_type,
            source_location=original.source_location,
            preprocessing_applied=result.operations_applied,
            stored_at=datetime.now(timezone.utc),
            expires_at=expires_at,
        )

        # Save metadata
        self._save_metadata(stored)

        # Track in memory
        self._stored[image_id] = stored

        logger.debug(f"Saved processed image: {image_id} -> {image_path}")

        return stored

    def load_cached(self, image_id: str) -> Optional[LoadedImage]:
        """Load image from cache.

        Args:
            image_id: Image identifier

        Returns:
            LoadedImage or None if not found/expired
        """
        if not self.cache_enabled:
            return None

        # Check in-memory cache first
        stored = self._stored.get(image_id)

        # Try loading from disk
        if not stored:
            stored = self._load_metadata(image_id)
            if stored:
                self._stored[image_id] = stored

        if not stored:
            return None

        # Check expiration
        if stored.expires_at and datetime.now(timezone.utc) > stored.expires_at:
            self.remove(image_id)
            return None

        # Load image data
        image_path = Path(stored.path)
        if not image_path.exists():
            return None

        try:
            data = image_path.read_bytes()

            return LoadedImage(
                data=data,
                format=stored.format,
                size_bytes=len(data),
                source_type="cache",
                source_location=stored.path,
                content_hash=stored.content_hash,
                width=stored.width,
                height=stored.height,
            )

        except OSError as e:
            logger.warning(f"Failed to load cached image {image_id}: {e}")
            return None

    def exists(self, image_id: str) -> bool:
        """Check if image exists in storage.

        Args:
            image_id: Image identifier

        Returns:
            True if image exists and is not expired
        """
        stored = self._stored.get(image_id) or self._load_metadata(image_id)

        if not stored:
            return False

        # Check expiration
        if stored.expires_at and datetime.now(timezone.utc) > stored.expires_at:
            return False

        # Check file exists
        return Path(stored.path).exists()

    def get_metadata(self, image_id: str) -> Optional[StoredImage]:
        """Get metadata for stored image.

        Args:
            image_id: Image identifier

        Returns:
            StoredImage metadata or None
        """
        return self._stored.get(image_id) or self._load_metadata(image_id)

    async def get_image_bytes(self, image_id: str) -> Optional[bytes]:
        """Get raw image bytes for API calls.

        Args:
            image_id: The unique image identifier

        Returns:
            Raw image bytes or None if not found
        """
        # Get metadata to find the image path
        stored = self.get_metadata(image_id)
        if stored and stored.path:
            path = Path(stored.path)
            if path.exists():
                return path.read_bytes()
        return None

    def remove(self, image_id: str) -> bool:
        """Remove image from storage.

        Args:
            image_id: Image identifier

        Returns:
            True if removed, False if not found
        """
        stored = self._stored.pop(image_id, None) or self._load_metadata(image_id)

        if not stored:
            return False

        # Remove image file
        image_path = Path(stored.path)
        if image_path.exists():
            try:
                image_path.unlink()
            except OSError as e:
                logger.warning(f"Failed to remove image file {image_path}: {e}")

        # Remove metadata
        metadata_path = self._get_metadata_path(image_id)
        if metadata_path.exists():
            try:
                metadata_path.unlink()
            except OSError as e:
                logger.warning(f"Failed to remove metadata {metadata_path}: {e}")

        return True

    def cleanup(self, force: bool = False) -> int:
        """Clean up temporary and expired files.

        Args:
            force: If True, remove all temporary files regardless of expiration

        Returns:
            Number of files removed
        """
        removed_count = 0

        # Clean up tracked temp files
        for temp_path in list(self._temp_files):
            if temp_path.exists():
                try:
                    temp_path.unlink()
                    removed_count += 1
                except OSError as e:
                    logger.warning(f"Failed to remove temp file {temp_path}: {e}")
            self._temp_files.remove(temp_path)

        # Clean up expired cached files
        if self.cache_enabled:
            now = datetime.now(timezone.utc)

            for image_id, stored in list(self._stored.items()):
                if force or (stored.expires_at and now > stored.expires_at):
                    if self.remove(image_id):
                        removed_count += 1

        # Clean up temp directory if using system temp
        if force and self.use_temp and self.temp_dir.exists():
            try:
                if str(self.temp_dir).startswith(tempfile.gettempdir()):
                    shutil.rmtree(self.temp_dir)
                    logger.debug(f"Removed temp directory: {self.temp_dir}")
            except OSError as e:
                logger.warning(f"Failed to remove temp directory: {e}")

        logger.debug(f"Cleanup removed {removed_count} files")
        return removed_count

    def list_cached(self) -> List[StoredImage]:
        """List all cached images.

        Returns:
            List of StoredImage metadata
        """
        if not self.cache_enabled:
            return []

        # Scan metadata directory
        metadata_dir = self.cache_dir / "metadata"
        if not metadata_dir.exists():
            return []

        results = []
        for metadata_file in metadata_dir.glob("*.json"):
            image_id = metadata_file.stem
            stored = self._load_metadata(image_id)
            if stored:
                results.append(stored)

        return results

    def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics.

        Returns:
            Dict with storage statistics
        """
        stats = {
            "cache_enabled": self.cache_enabled,
            "cache_dir": str(self.cache_dir),
            "temp_dir": str(self.temp_dir),
            "cached_images": 0,
            "temp_files": len(self._temp_files),
            "total_size_bytes": 0,
        }

        if self.cache_enabled and self.cache_dir.exists():
            images_dir = self.cache_dir / "images"
            if images_dir.exists():
                image_files = list(images_dir.iterdir())
                stats["cached_images"] = len(image_files)
                stats["total_size_bytes"] = sum(f.stat().st_size for f in image_files if f.is_file())

        return stats


# =============================================================================
# Export
# =============================================================================

__all__ = [
    "DEFAULT_CACHE_DIR",
    "StoredImage",
    "StorageManager",
]
