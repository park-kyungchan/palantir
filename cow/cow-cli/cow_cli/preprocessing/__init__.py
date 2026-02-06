"""
COW CLI - Image Preprocessing Module

Provides validation and deduplication for images.
"""
from cow_cli.preprocessing.validator import (
    ValidationError,
    ValidationResult,
    ImageInfo,
    ImageValidator,
    validate_image,
)
from cow_cli.preprocessing.deduplicator import (
    DuplicateInfo,
    DeduplicationResult,
    ImageDeduplicator,
    BatchDeduplicator,
    find_duplicates,
)

__all__ = [
    # Validator
    "ValidationError",
    "ValidationResult",
    "ImageInfo",
    "ImageValidator",
    "validate_image",
    # Deduplicator
    "DuplicateInfo",
    "DeduplicationResult",
    "ImageDeduplicator",
    "BatchDeduplicator",
    "find_duplicates",
]
