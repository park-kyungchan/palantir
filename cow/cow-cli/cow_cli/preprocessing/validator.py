"""
COW CLI - Image Validator

Validates and preprocesses images before Mathpix API calls.
"""
from typing import Optional, Union
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import io
import logging

from PIL import Image, ExifTags

logger = logging.getLogger("cow-cli.preprocessing")


class ValidationError(Enum):
    """Validation error types."""

    NONE = "none"
    FILE_NOT_FOUND = "file_not_found"
    NOT_A_FILE = "not_a_file"
    FILE_TOO_LARGE = "file_too_large"
    UNSUPPORTED_FORMAT = "unsupported_format"
    CORRUPTED_IMAGE = "corrupted_image"
    RESOLUTION_TOO_LOW = "resolution_too_low"
    CANNOT_READ = "cannot_read"


@dataclass
class ValidationResult:
    """Result of image validation."""

    valid: bool
    error: ValidationError = ValidationError.NONE
    error_message: Optional[str] = None
    format: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    size_bytes: Optional[int] = None
    needs_conversion: bool = False
    exif_rotation: Optional[int] = None

    @property
    def size_mb(self) -> float:
        """Get size in MB."""
        return (self.size_bytes or 0) / (1024 * 1024)


@dataclass
class ImageInfo:
    """Detailed image information."""

    path: Path
    format: str
    width: int
    height: int
    size_bytes: int
    mode: str
    has_exif: bool = False
    exif_rotation: Optional[int] = None
    is_animated: bool = False
    frame_count: int = 1


class ImageValidator:
    """
    Validates images for Mathpix API processing.

    Checks:
    - File existence and accessibility
    - Format support (PNG, JPG, GIF, WEBP, PDF)
    - Size limits
    - Resolution requirements
    - Image integrity
    """

    # Supported formats
    SUPPORTED_FORMATS = {"PNG", "JPEG", "GIF", "WEBP", "PDF"}
    JPEG_ALIASES = {"JPG", "JPEG"}

    # Size limits
    DEFAULT_MAX_SIZE_MB = 10
    DEFAULT_MIN_WIDTH = 50
    DEFAULT_MIN_HEIGHT = 50

    def __init__(
        self,
        max_size_mb: float = DEFAULT_MAX_SIZE_MB,
        min_width: int = DEFAULT_MIN_WIDTH,
        min_height: int = DEFAULT_MIN_HEIGHT,
        strict: bool = False,
    ):
        """
        Initialize validator.

        Args:
            max_size_mb: Maximum file size in MB
            min_width: Minimum image width in pixels
            min_height: Minimum image height in pixels
            strict: If True, reject images that need conversion
        """
        self.max_size_bytes = int(max_size_mb * 1024 * 1024)
        self.min_width = min_width
        self.min_height = min_height
        self.strict = strict

    def validate(self, source: Union[Path, str, bytes]) -> ValidationResult:
        """
        Validate an image.

        Args:
            source: Image path, string path, or bytes

        Returns:
            ValidationResult with validation status
        """
        # Handle different source types
        if isinstance(source, bytes):
            return self._validate_bytes(source)
        elif isinstance(source, str):
            source = Path(source)

        return self._validate_path(source)

    def _validate_path(self, path: Path) -> ValidationResult:
        """Validate image from file path."""
        # Check file exists
        if not path.exists():
            return ValidationResult(
                valid=False,
                error=ValidationError.FILE_NOT_FOUND,
                error_message=f"File not found: {path}",
            )

        # Check it's a file
        if not path.is_file():
            return ValidationResult(
                valid=False,
                error=ValidationError.NOT_A_FILE,
                error_message=f"Not a file: {path}",
            )

        # Check file size
        size_bytes = path.stat().st_size
        if size_bytes > self.max_size_bytes:
            return ValidationResult(
                valid=False,
                error=ValidationError.FILE_TOO_LARGE,
                error_message=f"File too large: {size_bytes / (1024*1024):.2f} MB "
                f"(max: {self.max_size_bytes / (1024*1024):.2f} MB)",
                size_bytes=size_bytes,
            )

        # Try to open and validate image
        try:
            with Image.open(path) as img:
                return self._validate_image(img, size_bytes)
        except Exception as e:
            return ValidationResult(
                valid=False,
                error=ValidationError.CORRUPTED_IMAGE,
                error_message=f"Cannot open image: {e}",
                size_bytes=size_bytes,
            )

    def _validate_bytes(self, data: bytes) -> ValidationResult:
        """Validate image from bytes."""
        size_bytes = len(data)

        # Check size
        if size_bytes > self.max_size_bytes:
            return ValidationResult(
                valid=False,
                error=ValidationError.FILE_TOO_LARGE,
                error_message=f"Data too large: {size_bytes / (1024*1024):.2f} MB",
                size_bytes=size_bytes,
            )

        # Try to open and validate
        try:
            with Image.open(io.BytesIO(data)) as img:
                return self._validate_image(img, size_bytes)
        except Exception as e:
            return ValidationResult(
                valid=False,
                error=ValidationError.CORRUPTED_IMAGE,
                error_message=f"Cannot decode image: {e}",
                size_bytes=size_bytes,
            )

    def _validate_image(self, img: Image.Image, size_bytes: int) -> ValidationResult:
        """Validate opened PIL Image."""
        # Get format
        img_format = img.format
        if img_format is None:
            return ValidationResult(
                valid=False,
                error=ValidationError.UNSUPPORTED_FORMAT,
                error_message="Cannot determine image format",
                size_bytes=size_bytes,
            )

        # Normalize format name
        normalized_format = img_format.upper()
        if normalized_format in self.JPEG_ALIASES:
            normalized_format = "JPEG"

        # Check format support
        needs_conversion = normalized_format not in self.SUPPORTED_FORMATS
        if needs_conversion and self.strict:
            return ValidationResult(
                valid=False,
                error=ValidationError.UNSUPPORTED_FORMAT,
                error_message=f"Unsupported format: {img_format}. "
                f"Supported: {', '.join(sorted(self.SUPPORTED_FORMATS))}",
                format=img_format,
                size_bytes=size_bytes,
            )

        # Get resolution BEFORE verify (verify invalidates the image)
        width, height = img.size

        # Check resolution first
        if width < self.min_width or height < self.min_height:
            return ValidationResult(
                valid=False,
                error=ValidationError.RESOLUTION_TOO_LOW,
                error_message=f"Resolution too low: {width}x{height} "
                f"(min: {self.min_width}x{self.min_height})",
                format=img_format,
                width=width,
                height=height,
                size_bytes=size_bytes,
            )

        # Check EXIF rotation before verify
        exif_rotation = self._get_exif_rotation(img)

        # Verify image integrity (optional - load() is more reliable)
        try:
            # Try to load the image data to verify it's not corrupted
            img.load()
        except Exception as e:
            return ValidationResult(
                valid=False,
                error=ValidationError.CORRUPTED_IMAGE,
                error_message=f"Image verification failed: {e}",
                format=img_format,
                width=width,
                height=height,
                size_bytes=size_bytes,
            )

        return ValidationResult(
            valid=True,
            format=img_format,
            width=width,
            height=height,
            size_bytes=size_bytes,
            needs_conversion=needs_conversion,
            exif_rotation=exif_rotation,
        )

    def _get_exif_rotation(self, img: Image.Image) -> Optional[int]:
        """Get EXIF rotation angle if present."""
        try:
            exif = img.getexif()
            if exif is None:
                return None

            for tag, value in exif.items():
                tag_name = ExifTags.TAGS.get(tag, tag)
                if tag_name == "Orientation":
                    # Map EXIF orientation to degrees
                    rotation_map = {
                        3: 180,
                        6: 270,
                        8: 90,
                    }
                    return rotation_map.get(value)
        except Exception:
            pass
        return None

    def get_info(self, source: Union[Path, str, bytes]) -> Optional[ImageInfo]:
        """
        Get detailed image information.

        Args:
            source: Image path or bytes

        Returns:
            ImageInfo or None if cannot read
        """
        try:
            if isinstance(source, bytes):
                img = Image.open(io.BytesIO(source))
                path = Path("<bytes>")
                size_bytes = len(source)
            else:
                path = Path(source) if isinstance(source, str) else source
                size_bytes = path.stat().st_size
                img = Image.open(path)

            with img:
                exif_rotation = self._get_exif_rotation(img)
                is_animated = getattr(img, "is_animated", False)
                frame_count = getattr(img, "n_frames", 1)

                return ImageInfo(
                    path=path,
                    format=img.format or "UNKNOWN",
                    width=img.size[0],
                    height=img.size[1],
                    size_bytes=size_bytes,
                    mode=img.mode,
                    has_exif=img.getexif() is not None and len(img.getexif()) > 0,
                    exif_rotation=exif_rotation,
                    is_animated=is_animated,
                    frame_count=frame_count,
                )
        except Exception as e:
            logger.warning(f"Cannot get image info: {e}")
            return None


def validate_image(
    source: Union[Path, str, bytes],
    **kwargs,
) -> ValidationResult:
    """Convenience function for image validation."""
    validator = ImageValidator(**kwargs)
    return validator.validate(source)


__all__ = [
    "ValidationError",
    "ValidationResult",
    "ImageInfo",
    "ImageValidator",
    "validate_image",
]
