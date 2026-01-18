"""
Image preprocessor for Stage A (Ingestion).

Applies preprocessing operations to improve image quality for downstream processing:
- Resolution normalization
- Contrast enhancement
- Deskewing
- Noise removal
- Region detection

Schema Version: 2.0.0
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from .exceptions import PreprocessingError
from .loader import LoadedImage

logger = logging.getLogger(__name__)


# =============================================================================
# Enums
# =============================================================================

class PreprocessingOp(str, Enum):
    """Available preprocessing operations."""
    NORMALIZE_RESOLUTION = "normalize_resolution"
    ENHANCE_CONTRAST = "enhance_contrast"
    DESKEW = "deskew"
    REMOVE_NOISE = "remove_noise"
    DETECT_REGIONS = "detect_regions"
    CONVERT_GRAYSCALE = "convert_grayscale"
    SHARPEN = "sharpen"


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class Region:
    """Detected region in image.

    Attributes:
        x: X coordinate of top-left corner
        y: Y coordinate of top-left corner
        width: Region width
        height: Region height
        region_type: Type of region (e.g., 'math', 'text', 'diagram')
        confidence: Detection confidence
    """
    x: int
    y: int
    width: int
    height: int
    region_type: str = "unknown"
    confidence: float = 1.0


@dataclass
class PreprocessingResult:
    """Result of preprocessing operations.

    Attributes:
        data: Processed image bytes
        width: Processed image width
        height: Processed image height
        format: Output format
        operations_applied: List of operations that were applied
        regions: Detected regions (if detect_regions was run)
        metadata: Additional preprocessing metadata
    """
    data: bytes
    width: int
    height: int
    format: str
    operations_applied: List[str] = field(default_factory=list)
    regions: List[Region] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# Preprocessor
# =============================================================================

class Preprocessor:
    """Image preprocessor for quality improvement.

    Applies various preprocessing operations to improve image quality
    for downstream OCR and vision processing.

    Usage:
        preprocessor = Preprocessor()
        result = preprocessor.process(
            image,
            operations=[
                PreprocessingOp.NORMALIZE_RESOLUTION,
                PreprocessingOp.ENHANCE_CONTRAST,
            ]
        )
    """

    def __init__(
        self,
        target_dpi: int = 300,
        max_dimension: int = 4096,
        contrast_factor: float = 1.2,
        denoise_strength: int = 5,
    ):
        """Initialize preprocessor.

        Args:
            target_dpi: Target DPI for resolution normalization
            max_dimension: Maximum dimension after normalization
            contrast_factor: Contrast enhancement factor (1.0 = no change)
            denoise_strength: Strength of noise removal (1-10)
        """
        self.target_dpi = target_dpi
        self.max_dimension = max_dimension
        self.contrast_factor = contrast_factor
        self.denoise_strength = denoise_strength
        self._pil_available = self._check_pil()

    def _check_pil(self) -> bool:
        """Check if PIL is available."""
        try:
            from PIL import Image
            return True
        except ImportError:
            logger.warning("PIL not available, preprocessing will be limited")
            return False

    def _load_pil_image(self, image: LoadedImage) -> Any:
        """Load image data into PIL Image.

        Args:
            image: LoadedImage to convert

        Returns:
            PIL Image object

        Raises:
            PreprocessingError: If loading fails
        """
        from PIL import Image
        import io

        try:
            return Image.open(io.BytesIO(image.data))
        except Exception as e:
            raise PreprocessingError(
                f"Failed to load image for preprocessing: {e}",
                operation="load",
                reason=str(e),
            )

    def _save_pil_image(self, img: Any, format: str) -> bytes:
        """Save PIL Image to bytes.

        Args:
            img: PIL Image object
            format: Output format

        Returns:
            Image bytes
        """
        import io

        buffer = io.BytesIO()
        save_format = "JPEG" if format == "jpg" else format.upper()
        if save_format == "JPG":
            save_format = "JPEG"

        img.save(buffer, format=save_format)
        return buffer.getvalue()

    def normalize_resolution(
        self,
        img: Any,
        target_dpi: Optional[int] = None,
        max_dimension: Optional[int] = None,
    ) -> Any:
        """Normalize image resolution.

        Scales image to target DPI while respecting maximum dimension.

        Args:
            img: PIL Image
            target_dpi: Target DPI (uses instance default if not specified)
            max_dimension: Maximum dimension (uses instance default if not specified)

        Returns:
            Normalized PIL Image
        """
        target_dpi = target_dpi or self.target_dpi
        max_dimension = max_dimension or self.max_dimension

        # Get current DPI
        current_dpi = 72  # Default assumption
        if hasattr(img, "info") and "dpi" in img.info:
            dpi = img.info["dpi"]
            current_dpi = dpi[0] if isinstance(dpi, tuple) else dpi

        # Calculate scale factor
        scale = target_dpi / current_dpi

        # Calculate new dimensions
        new_width = int(img.width * scale)
        new_height = int(img.height * scale)

        # Respect maximum dimension
        if max(new_width, new_height) > max_dimension:
            ratio = max_dimension / max(new_width, new_height)
            new_width = int(new_width * ratio)
            new_height = int(new_height * ratio)

        # Only resize if dimensions change significantly
        if abs(new_width - img.width) > 10 or abs(new_height - img.height) > 10:
            from PIL import Image
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        return img

    def enhance_contrast(
        self,
        img: Any,
        factor: Optional[float] = None,
    ) -> Any:
        """Enhance image contrast.

        Args:
            img: PIL Image
            factor: Contrast factor (1.0 = no change, >1 = more contrast)

        Returns:
            Contrast-enhanced PIL Image
        """
        from PIL import ImageEnhance

        factor = factor or self.contrast_factor
        enhancer = ImageEnhance.Contrast(img)
        return enhancer.enhance(factor)

    def deskew(self, img: Any) -> Any:
        """Deskew image (correct rotation).

        Uses Hough transform to detect skew angle and correct it.

        Args:
            img: PIL Image

        Returns:
            Deskewed PIL Image
        """
        try:
            import numpy as np
            from PIL import Image

            # Convert to grayscale for analysis
            gray = img.convert("L")
            gray_array = np.array(gray)

            # Simple edge-based skew detection
            # Calculate horizontal projection profile variance at different angles
            best_angle = 0
            best_variance = 0

            for angle in range(-10, 11, 1):  # Check -10 to +10 degrees
                rotated = img.rotate(angle, expand=False, fillcolor="white")
                rotated_gray = np.array(rotated.convert("L"))

                # Calculate horizontal projection
                projection = np.sum(rotated_gray, axis=1)
                variance = np.var(projection)

                if variance > best_variance:
                    best_variance = variance
                    best_angle = angle

            # Apply correction if significant skew detected
            if abs(best_angle) > 0.5:
                img = img.rotate(best_angle, expand=True, fillcolor="white")
                logger.debug(f"Deskewed image by {best_angle} degrees")

            return img

        except ImportError:
            logger.warning("numpy not available, skipping deskew")
            return img

    def remove_noise(
        self,
        img: Any,
        strength: Optional[int] = None,
    ) -> Any:
        """Remove noise from image.

        Uses median filter for noise removal.

        Args:
            img: PIL Image
            strength: Filter strength (kernel size)

        Returns:
            Denoised PIL Image
        """
        from PIL import ImageFilter

        strength = strength or self.denoise_strength
        # MedianFilter kernel size must be odd
        kernel_size = strength if strength % 2 == 1 else strength + 1

        return img.filter(ImageFilter.MedianFilter(size=kernel_size))

    def detect_regions(self, img: Any) -> List[Region]:
        """Detect content regions in image.

        Uses simple connected component analysis to find regions
        that likely contain content (text, diagrams, equations).

        Args:
            img: PIL Image

        Returns:
            List of detected regions
        """
        regions: List[Region] = []

        try:
            import numpy as np
            from PIL import Image

            # Convert to binary
            gray = img.convert("L")
            gray_array = np.array(gray)

            # Simple threshold
            threshold = 200
            binary = (gray_array < threshold).astype(np.uint8)

            # Find bounding box of content
            rows = np.any(binary, axis=1)
            cols = np.any(binary, axis=0)

            if np.any(rows) and np.any(cols):
                y_min, y_max = np.where(rows)[0][[0, -1]]
                x_min, x_max = np.where(cols)[0][[0, -1]]

                # Add padding
                padding = 10
                x_min = max(0, x_min - padding)
                y_min = max(0, y_min - padding)
                x_max = min(img.width, x_max + padding)
                y_max = min(img.height, y_max + padding)

                # Create main content region
                main_region = Region(
                    x=int(x_min),
                    y=int(y_min),
                    width=int(x_max - x_min),
                    height=int(y_max - y_min),
                    region_type="content",
                    confidence=0.9,
                )
                regions.append(main_region)

                # Try to detect sub-regions (simplified)
                content_area = binary[y_min:y_max, x_min:x_max]
                content_density = np.mean(content_area)

                if content_density > 0.3:
                    main_region.region_type = "dense_content"
                elif content_density < 0.05:
                    main_region.region_type = "sparse_content"

        except ImportError:
            logger.warning("numpy not available, skipping region detection")
        except Exception as e:
            logger.warning(f"Region detection failed: {e}")

        return regions

    def convert_grayscale(self, img: Any) -> Any:
        """Convert image to grayscale.

        Args:
            img: PIL Image

        Returns:
            Grayscale PIL Image
        """
        return img.convert("L")

    def sharpen(self, img: Any) -> Any:
        """Sharpen image.

        Args:
            img: PIL Image

        Returns:
            Sharpened PIL Image
        """
        from PIL import ImageEnhance

        enhancer = ImageEnhance.Sharpness(img)
        return enhancer.enhance(1.5)

    def process(
        self,
        image: LoadedImage,
        operations: Optional[List[PreprocessingOp]] = None,
        output_format: Optional[str] = None,
    ) -> PreprocessingResult:
        """Apply preprocessing operations to image.

        Args:
            image: LoadedImage to process
            operations: List of operations to apply (default: common set)
            output_format: Output format (default: same as input)

        Returns:
            PreprocessingResult with processed image

        Raises:
            PreprocessingError: If processing fails
        """
        if not self._pil_available:
            raise PreprocessingError(
                "PIL is required for preprocessing",
                operation="init",
                reason="PIL not installed",
            )

        # Default operations
        if operations is None:
            operations = [
                PreprocessingOp.NORMALIZE_RESOLUTION,
                PreprocessingOp.ENHANCE_CONTRAST,
            ]

        output_format = output_format or image.format
        operations_applied: List[str] = []
        regions: List[Region] = []
        metadata: Dict[str, Any] = {}

        # Load image
        img = self._load_pil_image(image)
        original_size = img.size

        # Apply operations in order
        for op in operations:
            try:
                if op == PreprocessingOp.NORMALIZE_RESOLUTION:
                    img = self.normalize_resolution(img)
                    operations_applied.append(op.value)
                    metadata["normalized_from"] = original_size
                    metadata["normalized_to"] = img.size

                elif op == PreprocessingOp.ENHANCE_CONTRAST:
                    img = self.enhance_contrast(img)
                    operations_applied.append(op.value)
                    metadata["contrast_factor"] = self.contrast_factor

                elif op == PreprocessingOp.DESKEW:
                    img = self.deskew(img)
                    operations_applied.append(op.value)

                elif op == PreprocessingOp.REMOVE_NOISE:
                    img = self.remove_noise(img)
                    operations_applied.append(op.value)
                    metadata["denoise_strength"] = self.denoise_strength

                elif op == PreprocessingOp.DETECT_REGIONS:
                    regions = self.detect_regions(img)
                    operations_applied.append(op.value)
                    metadata["regions_detected"] = len(regions)

                elif op == PreprocessingOp.CONVERT_GRAYSCALE:
                    img = self.convert_grayscale(img)
                    operations_applied.append(op.value)

                elif op == PreprocessingOp.SHARPEN:
                    img = self.sharpen(img)
                    operations_applied.append(op.value)

            except Exception as e:
                raise PreprocessingError(
                    f"Preprocessing operation '{op.value}' failed: {e}",
                    operation=op.value,
                    reason=str(e),
                )

        # Save processed image
        processed_data = self._save_pil_image(img, output_format)

        return PreprocessingResult(
            data=processed_data,
            width=img.width,
            height=img.height,
            format=output_format,
            operations_applied=operations_applied,
            regions=regions,
            metadata=metadata,
        )


# =============================================================================
# Export
# =============================================================================

__all__ = [
    "PreprocessingOp",
    "Region",
    "PreprocessingResult",
    "Preprocessor",
]
