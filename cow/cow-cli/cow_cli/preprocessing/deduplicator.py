"""
COW CLI - Image Deduplicator

Perceptual hash-based duplicate detection for images.
"""
from typing import Optional, Union
from pathlib import Path
from dataclasses import dataclass, field
from collections import defaultdict
import io
import logging

import imagehash
from PIL import Image

logger = logging.getLogger("cow-cli.preprocessing")


@dataclass
class DuplicateInfo:
    """Information about a duplicate image."""

    duplicate_path: Path
    original_path: Path
    hash_distance: int
    hash_type: str


@dataclass
class DeduplicationResult:
    """Result of batch deduplication."""

    unique_images: list[Path] = field(default_factory=list)
    duplicates: list[DuplicateInfo] = field(default_factory=list)
    failed: list[tuple[Path, str]] = field(default_factory=list)

    @property
    def total_processed(self) -> int:
        """Total images processed."""
        return len(self.unique_images) + len(self.duplicates) + len(self.failed)

    @property
    def duplicate_count(self) -> int:
        """Number of duplicates found."""
        return len(self.duplicates)

    @property
    def api_calls_saved(self) -> int:
        """Number of API calls saved by deduplication."""
        return self.duplicate_count

    def get_duplicate_groups(self) -> dict[Path, list[Path]]:
        """Group duplicates by their original."""
        groups: dict[Path, list[Path]] = defaultdict(list)
        for dup in self.duplicates:
            groups[dup.original_path].append(dup.duplicate_path)
        return dict(groups)


class ImageDeduplicator:
    """
    Detects duplicate images using perceptual hashing.

    Uses imagehash library for:
    - pHash (perceptual hash) - default, best for similar images
    - dHash (difference hash) - faster, good for identical images
    - aHash (average hash) - fastest, less accurate

    Hamming distance threshold determines similarity:
    - 0: Exact match
    - <= 5: Very similar (default for duplicates)
    - <= 10: Somewhat similar
    - > 10: Different
    """

    DEFAULT_THRESHOLD = 5
    # Note: imagehash uses 'average_hash' for ahash
    HASH_TYPES = {"phash", "dhash", "whash", "average_hash"}

    def __init__(
        self,
        threshold: int = DEFAULT_THRESHOLD,
        hash_type: str = "phash",
    ):
        """
        Initialize deduplicator.

        Args:
            threshold: Maximum Hamming distance for duplicates (0-64)
            hash_type: Hash algorithm (phash, dhash, ahash, whash)
        """
        if hash_type not in self.HASH_TYPES:
            raise ValueError(f"Unknown hash type: {hash_type}. "
                           f"Supported: {', '.join(sorted(self.HASH_TYPES))}")

        self.threshold = threshold
        self.hash_type = hash_type
        self._hash_func = getattr(imagehash, hash_type)

        # Cache: path -> hash
        self._hashes: dict[Path, imagehash.ImageHash] = {}

    def compute_hash(
        self,
        source: Union[Path, str, bytes],
    ) -> Optional[imagehash.ImageHash]:
        """
        Compute perceptual hash for an image.

        Args:
            source: Image path or bytes

        Returns:
            ImageHash or None if cannot process
        """
        try:
            if isinstance(source, bytes):
                img = Image.open(io.BytesIO(source))
            else:
                path = Path(source) if isinstance(source, str) else source
                img = Image.open(path)

            with img:
                return self._hash_func(img)
        except Exception as e:
            logger.warning(f"Cannot compute hash: {e}")
            return None

    def is_duplicate(
        self,
        source: Union[Path, str, bytes],
        path: Optional[Path] = None,
    ) -> Optional[Path]:
        """
        Check if an image is a duplicate of previously seen images.

        Args:
            source: Image to check (path or bytes)
            path: Path to use for caching (required for bytes)

        Returns:
            Path of original if duplicate, None otherwise
        """
        # Determine path for caching
        if isinstance(source, bytes):
            if path is None:
                # Cannot cache without a path
                current_path = Path(f"<bytes-{id(source)}>")
            else:
                current_path = path
        else:
            current_path = Path(source) if isinstance(source, str) else source

        # Compute hash
        current_hash = self.compute_hash(source)
        if current_hash is None:
            return None

        # Check against existing hashes
        for existing_path, existing_hash in self._hashes.items():
            distance = current_hash - existing_hash
            if distance <= self.threshold:
                logger.debug(
                    f"Duplicate found: {current_path} matches {existing_path} "
                    f"(distance: {distance})"
                )
                return existing_path

        # Not a duplicate - add to cache
        self._hashes[current_path] = current_hash
        return None

    def find_duplicates(
        self,
        images: list[Union[Path, str]],
    ) -> DeduplicationResult:
        """
        Find duplicates in a list of images.

        Args:
            images: List of image paths

        Returns:
            DeduplicationResult with unique/duplicate/failed lists
        """
        result = DeduplicationResult()

        # Reset cache for fresh comparison
        self._hashes.clear()

        for source in images:
            path = Path(source) if isinstance(source, str) else source

            try:
                hash_value = self.compute_hash(path)
                if hash_value is None:
                    result.failed.append((path, "Cannot compute hash"))
                    continue

                # Check for duplicate
                original = self._find_similar(path, hash_value)

                if original is not None:
                    result.duplicates.append(
                        DuplicateInfo(
                            duplicate_path=path,
                            original_path=original,
                            hash_distance=hash_value - self._hashes[original],
                            hash_type=self.hash_type,
                        )
                    )
                else:
                    self._hashes[path] = hash_value
                    result.unique_images.append(path)

            except Exception as e:
                result.failed.append((path, str(e)))

        return result

    def _find_similar(
        self,
        path: Path,
        hash_value: imagehash.ImageHash,
    ) -> Optional[Path]:
        """Find similar hash in cache."""
        for existing_path, existing_hash in self._hashes.items():
            if hash_value - existing_hash <= self.threshold:
                return existing_path
        return None

    def clear_cache(self) -> None:
        """Clear the hash cache."""
        self._hashes.clear()

    @property
    def cache_size(self) -> int:
        """Number of hashes in cache."""
        return len(self._hashes)


class BatchDeduplicator:
    """
    Batch processor for directory-based deduplication.

    Usage:
        dedup = BatchDeduplicator()
        result = dedup.process_directory(Path("./images"), pattern="*.png")
        print(f"Found {result.duplicate_count} duplicates")
        print(f"Saved {result.api_calls_saved} API calls")
    """

    def __init__(
        self,
        threshold: int = ImageDeduplicator.DEFAULT_THRESHOLD,
        hash_type: str = "phash",
    ):
        self.deduplicator = ImageDeduplicator(
            threshold=threshold,
            hash_type=hash_type,
        )

    def process_directory(
        self,
        directory: Union[Path, str],
        pattern: str = "*.png",
        recursive: bool = False,
    ) -> DeduplicationResult:
        """
        Process all images in a directory.

        Args:
            directory: Directory path
            pattern: Glob pattern for image files
            recursive: Include subdirectories

        Returns:
            DeduplicationResult
        """
        dir_path = Path(directory)
        if not dir_path.is_dir():
            raise ValueError(f"Not a directory: {directory}")

        if recursive:
            images = list(dir_path.rglob(pattern))
        else:
            images = list(dir_path.glob(pattern))

        # Sort for deterministic results
        images.sort()

        logger.info(f"Processing {len(images)} images from {directory}")
        return self.deduplicator.find_duplicates(images)

    def generate_report(self, result: DeduplicationResult) -> str:
        """
        Generate a human-readable deduplication report.

        Args:
            result: DeduplicationResult

        Returns:
            Formatted report string
        """
        lines = [
            "=" * 60,
            "IMAGE DEDUPLICATION REPORT",
            "=" * 60,
            "",
            f"Total processed:    {result.total_processed}",
            f"Unique images:      {len(result.unique_images)}",
            f"Duplicates found:   {result.duplicate_count}",
            f"Failed to process:  {len(result.failed)}",
            f"API calls saved:    {result.api_calls_saved}",
            "",
        ]

        if result.duplicates:
            lines.append("DUPLICATE GROUPS:")
            lines.append("-" * 40)
            for original, dupes in result.get_duplicate_groups().items():
                lines.append(f"\n  Original: {original}")
                for dup in dupes:
                    lines.append(f"    - {dup}")

        if result.failed:
            lines.append("\nFAILED TO PROCESS:")
            lines.append("-" * 40)
            for path, error in result.failed:
                lines.append(f"  {path}: {error}")

        lines.append("")
        lines.append("=" * 60)

        return "\n".join(lines)


def find_duplicates(
    images: list[Union[Path, str]],
    threshold: int = ImageDeduplicator.DEFAULT_THRESHOLD,
) -> DeduplicationResult:
    """Convenience function for finding duplicates."""
    dedup = ImageDeduplicator(threshold=threshold)
    return dedup.find_duplicates(images)


__all__ = [
    "DuplicateInfo",
    "DeduplicationResult",
    "ImageDeduplicator",
    "BatchDeduplicator",
    "find_duplicates",
]
