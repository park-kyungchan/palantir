"""
Image validator for Stage A (Ingestion).

Validates loaded images against quality requirements:
- Format validation
- Resolution bounds checking
- Content validation (not corrupted)
- Math content detection heuristics

Schema Version: 2.0.0
"""

import logging
from dataclasses import dataclass, field
from typing import List, Optional, Set, Tuple

from .exceptions import ValidationError
from .loader import LoadedImage, SUPPORTED_FORMATS

logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

MIN_RESOLUTION: Tuple[int, int] = (100, 100)
MAX_RESOLUTION: Tuple[int, int] = (10000, 10000)

# Aspect ratio bounds (width/height)
MIN_ASPECT_RATIO: float = 0.1
MAX_ASPECT_RATIO: float = 10.0

# Minimum file size to detect empty/placeholder images
MIN_FILE_SIZE: int = 100  # bytes


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class ValidationResult:
    """Result of image validation.

    Attributes:
        is_valid: Whether all required checks passed
        checks_passed: List of passed check names
        checks_failed: List of failed check names
        warnings: List of non-fatal warnings
        math_content_confidence: Estimated confidence that image contains math
        details: Additional details about validation
    """
    is_valid: bool
    checks_passed: List[str] = field(default_factory=list)
    checks_failed: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    math_content_confidence: float = 0.0
    details: dict = field(default_factory=dict)


# =============================================================================
# Image Validator
# =============================================================================

class ImageValidator:
    """Validates images for pipeline processing.

    Performs multiple validation checks:
    - Format validation
    - Resolution validation
    - Content validation (not corrupted)
    - Math content heuristics

    Usage:
        validator = ImageValidator()
        result = validator.validate(loaded_image)
        if not result.is_valid:
            print(f"Validation failed: {result.checks_failed}")
    """

    def __init__(
        self,
        supported_formats: Optional[Set[str]] = None,
        min_resolution: Tuple[int, int] = MIN_RESOLUTION,
        max_resolution: Tuple[int, int] = MAX_RESOLUTION,
        min_aspect_ratio: float = MIN_ASPECT_RATIO,
        max_aspect_ratio: float = MAX_ASPECT_RATIO,
        min_file_size: int = MIN_FILE_SIZE,
    ):
        """Initialize validator.

        Args:
            supported_formats: Set of supported image formats
            min_resolution: Minimum (width, height) in pixels
            max_resolution: Maximum (width, height) in pixels
            min_aspect_ratio: Minimum width/height ratio
            max_aspect_ratio: Maximum width/height ratio
            min_file_size: Minimum file size in bytes
        """
        self.supported_formats = supported_formats or SUPPORTED_FORMATS
        self.min_resolution = min_resolution
        self.max_resolution = max_resolution
        self.min_aspect_ratio = min_aspect_ratio
        self.max_aspect_ratio = max_aspect_ratio
        self.min_file_size = min_file_size

    def validate_format(self, image: LoadedImage) -> Tuple[bool, Optional[str]]:
        """Validate image format.

        Args:
            image: Loaded image to validate

        Returns:
            Tuple of (passed, error_message or None)
        """
        if image.format not in self.supported_formats:
            return False, f"Unsupported format: {image.format}"
        return True, None

    def validate_resolution(self, image: LoadedImage) -> Tuple[bool, Optional[str]]:
        """Validate image resolution.

        Args:
            image: Loaded image to validate

        Returns:
            Tuple of (passed, error_message or None)
        """
        if image.width is None or image.height is None:
            return True, None  # Skip if dimensions unknown

        # Check minimum
        if image.width < self.min_resolution[0]:
            return False, f"Width {image.width}px below minimum {self.min_resolution[0]}px"
        if image.height < self.min_resolution[1]:
            return False, f"Height {image.height}px below minimum {self.min_resolution[1]}px"

        # Check maximum
        if image.width > self.max_resolution[0]:
            return False, f"Width {image.width}px exceeds maximum {self.max_resolution[0]}px"
        if image.height > self.max_resolution[1]:
            return False, f"Height {image.height}px exceeds maximum {self.max_resolution[1]}px"

        # Check aspect ratio
        aspect = image.width / image.height
        if aspect < self.min_aspect_ratio:
            return False, f"Aspect ratio {aspect:.2f} below minimum {self.min_aspect_ratio}"
        if aspect > self.max_aspect_ratio:
            return False, f"Aspect ratio {aspect:.2f} exceeds maximum {self.max_aspect_ratio}"

        return True, None

    def validate_content(self, image: LoadedImage) -> Tuple[bool, Optional[str]]:
        """Validate image content is not corrupted.

        Args:
            image: Loaded image to validate

        Returns:
            Tuple of (passed, error_message or None)
        """
        # Check minimum file size
        if image.size_bytes < self.min_file_size:
            return False, f"File size {image.size_bytes} bytes below minimum {self.min_file_size}"

        # Try to decode the image to verify it's not corrupted
        if image.format != "pdf":
            try:
                from PIL import Image
                import io

                with Image.open(io.BytesIO(image.data)) as img:
                    # Force decode by accessing pixels
                    img.load()

            except ImportError:
                logger.warning("PIL not available, skipping content validation")
                return True, None
            except Exception as e:
                return False, f"Image appears corrupted: {e}"

        return True, None

    def is_math_content(self, image: LoadedImage) -> Tuple[float, List[str]]:
        """Estimate confidence that image contains mathematical content.

        Uses heuristics based on image characteristics to estimate
        likelihood of math content. This is a pre-filter before
        more expensive ML-based detection.

        Args:
            image: Loaded image to analyze

        Returns:
            Tuple of (confidence 0-1, list of indicators found)
        """
        confidence = 0.5  # Start with neutral confidence
        indicators: List[str] = []

        if image.format == "pdf":
            # PDFs are commonly used for math documents
            confidence += 0.1
            indicators.append("pdf_format")

        # Check image dimensions for common document/diagram sizes
        if image.width and image.height:
            # Check for typical diagram aspect ratios
            aspect = image.width / image.height
            if 0.5 <= aspect <= 2.0:
                confidence += 0.05
                indicators.append("typical_diagram_aspect")

            # Check for reasonable diagram size
            if 200 <= image.width <= 2000 and 200 <= image.height <= 2000:
                confidence += 0.05
                indicators.append("typical_diagram_size")

        # Color mode analysis
        if image.color_mode:
            if image.color_mode in ("L", "1"):
                # Grayscale or binary - common for math documents
                confidence += 0.1
                indicators.append("grayscale_or_binary")
            elif image.color_mode in ("RGB", "RGBA"):
                # Color images - could be anything
                pass

        # Try image analysis if PIL available
        try:
            from PIL import Image, ImageStat
            import io

            if image.format != "pdf":
                with Image.open(io.BytesIO(image.data)) as img:
                    # Convert to grayscale for analysis
                    gray = img.convert("L")
                    stat = ImageStat.Stat(gray)

                    # High contrast suggests text/diagrams
                    if stat.stddev[0] > 50:
                        confidence += 0.1
                        indicators.append("high_contrast")

                    # Check for white/light background (common in documents)
                    if stat.mean[0] > 200:
                        confidence += 0.05
                        indicators.append("light_background")

                    # Low color variance often indicates diagrams
                    if img.mode in ("RGB", "RGBA"):
                        rgb_stat = ImageStat.Stat(img)
                        color_variance = sum(rgb_stat.var[:3]) / 3
                        if color_variance < 1000:
                            confidence += 0.05
                            indicators.append("low_color_variance")

        except ImportError:
            logger.debug("PIL not available, skipping advanced math content detection")
        except Exception as e:
            logger.debug(f"Math content detection failed: {e}")

        # Clamp confidence to [0, 1]
        confidence = max(0.0, min(1.0, confidence))

        return confidence, indicators

    def validate(
        self,
        image: LoadedImage,
        raise_on_failure: bool = False,
    ) -> ValidationResult:
        """Run all validation checks on image.

        Args:
            image: Loaded image to validate
            raise_on_failure: If True, raise ValidationError on failure

        Returns:
            ValidationResult with all check results

        Raises:
            ValidationError: If raise_on_failure=True and validation fails
        """
        checks_passed: List[str] = []
        checks_failed: List[str] = []
        warnings: List[str] = []
        details: dict = {}

        # Format validation
        passed, error = self.validate_format(image)
        if passed:
            checks_passed.append("format")
        else:
            checks_failed.append("format")
            details["format_error"] = error

        # Resolution validation
        if image.width is None or image.height is None:
            warnings.append("resolution_unknown")
            details["resolution_warning"] = "Image dimensions could not be determined"
        else:
            passed, error = self.validate_resolution(image)
            if passed:
                checks_passed.append("resolution")
            else:
                checks_failed.append("resolution")
                details["resolution_error"] = error

        # Content validation
        passed, error = self.validate_content(image)
        if passed:
            checks_passed.append("content")
        else:
            checks_failed.append("content")
            details["content_error"] = error

        # Math content detection (informational, not a validation failure)
        math_confidence, math_indicators = self.is_math_content(image)
        details["math_indicators"] = math_indicators

        if math_confidence < 0.3:
            warnings.append("low_math_confidence")

        is_valid = len(checks_failed) == 0

        result = ValidationResult(
            is_valid=is_valid,
            checks_passed=checks_passed,
            checks_failed=checks_failed,
            warnings=warnings,
            math_content_confidence=math_confidence,
            details=details,
        )

        if not is_valid and raise_on_failure:
            raise ValidationError(
                f"Image validation failed: {', '.join(checks_failed)}",
                checks_failed=checks_failed,
                checks_passed=checks_passed,
            )

        return result


# =============================================================================
# Export
# =============================================================================

__all__ = [
    "MIN_RESOLUTION",
    "MAX_RESOLUTION",
    "ValidationResult",
    "ImageValidator",
]
