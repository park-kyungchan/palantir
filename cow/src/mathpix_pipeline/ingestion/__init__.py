"""
Stage A: Ingestion Module for Math Image Parsing Pipeline v2.0.

This module handles the ingestion of images into the pipeline:
- Loading images from various sources (files, URLs, bytes, base64)
- Validating image format, resolution, and content
- Preprocessing to improve image quality
- Storage management for caching and temporary files

Schema Version: 2.0.0

Usage:
    from mathpix_pipeline.ingestion import (
        ImageLoader,
        ImageValidator,
        Preprocessor,
        StorageManager,
    )

    # Load image
    loader = ImageLoader()
    image = await loader.load_from_path("image.png")

    # Validate
    validator = ImageValidator()
    result = validator.validate(image)

    # Preprocess
    preprocessor = Preprocessor()
    processed = preprocessor.process(image)

    # Store
    storage = StorageManager()
    stored = storage.save_processed(image, processed)
"""

# Exceptions
from .exceptions import (
    IngestionError,
    ImageFormatError,
    ImageSizeError,
    ValidationError,
    StorageError,
    PreprocessingError,
)

# Loader
from .loader import (
    SUPPORTED_FORMATS,
    MAX_FILE_SIZE,
    LoadedImage,
    ImageLoader,
)

# Validator
from .validator import (
    MIN_RESOLUTION,
    MAX_RESOLUTION,
    ValidationResult,
    ImageValidator,
)

# Preprocessor
from .preprocessor import (
    PreprocessingOp,
    Region,
    PreprocessingResult,
    Preprocessor,
)

# Storage
from .storage import (
    DEFAULT_CACHE_DIR,
    StoredImage,
    StorageManager,
)


# Version
__version__ = "2.0.0"


__all__ = [
    # Version
    "__version__",

    # === Exceptions ===
    "IngestionError",
    "ImageFormatError",
    "ImageSizeError",
    "ValidationError",
    "StorageError",
    "PreprocessingError",

    # === Loader ===
    "SUPPORTED_FORMATS",
    "MAX_FILE_SIZE",
    "LoadedImage",
    "ImageLoader",

    # === Validator ===
    "MIN_RESOLUTION",
    "MAX_RESOLUTION",
    "ValidationResult",
    "ImageValidator",

    # === Preprocessor ===
    "PreprocessingOp",
    "Region",
    "PreprocessingResult",
    "Preprocessor",

    # === Storage ===
    "DEFAULT_CACHE_DIR",
    "StoredImage",
    "StorageManager",
]
