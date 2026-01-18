"""
Stage A: Ingestion Schemas for Math Image Parsing Pipeline v2.0.

This module defines the data schemas for the ingestion stage:
- ImageMetadata: Basic image properties
- ValidationResult: Results of image validation
- IngestionSpec: Complete specification of an ingested image

Schema Version: 2.0.0
"""

from datetime import datetime
from typing import List, Optional

from pydantic import Field, field_validator

from .common import (
    MathpixBaseModel,
    PipelineStage,
    Provenance,
    utc_now,
)


# =============================================================================
# Image Metadata
# =============================================================================

class ImageMetadata(MathpixBaseModel):
    """Basic metadata about an image.

    Attributes:
        format: Image format (e.g., 'png', 'jpg', 'pdf')
        width: Image width in pixels
        height: Image height in pixels
        dpi: Image DPI (dots per inch), if available
        color_mode: Color mode (e.g., 'RGB', 'RGBA', 'L', 'CMYK')
        file_size_bytes: Size of the image file in bytes
        content_hash: SHA256 hash of image content
    """
    format: str = Field(..., description="Image format (png, jpg, etc.)")
    width: int = Field(..., gt=0, description="Width in pixels")
    height: int = Field(..., gt=0, description="Height in pixels")
    dpi: Optional[int] = Field(default=None, ge=1, description="DPI if available")
    color_mode: str = Field(..., description="Color mode (RGB, L, etc.)")
    file_size_bytes: int = Field(..., gt=0, description="File size in bytes")
    content_hash: Optional[str] = Field(
        default=None,
        min_length=64,
        max_length=64,
        description="SHA256 hash"
    )

    @property
    def aspect_ratio(self) -> float:
        """Calculate aspect ratio (width / height)."""
        return self.width / self.height

    @property
    def megapixels(self) -> float:
        """Calculate megapixels."""
        return (self.width * self.height) / 1_000_000


# =============================================================================
# Validation Result
# =============================================================================

class ValidationResult(MathpixBaseModel):
    """Result of image validation checks.

    Attributes:
        is_valid: Whether all required checks passed
        checks_passed: List of validation checks that passed
        checks_failed: List of validation checks that failed
        warnings: Non-fatal warnings about the image
        error_details: Details about failures (if any)
    """
    is_valid: bool = Field(..., description="Overall validation status")
    checks_passed: List[str] = Field(
        default_factory=list,
        description="Checks that passed"
    )
    checks_failed: List[str] = Field(
        default_factory=list,
        description="Checks that failed"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Non-fatal warnings"
    )
    error_details: Optional[str] = Field(
        default=None,
        description="Detailed error message if validation failed"
    )

    @field_validator("checks_passed", "checks_failed", "warnings")
    @classmethod
    def unique_items(cls, v: List[str]) -> List[str]:
        """Ensure list items are unique."""
        return list(dict.fromkeys(v))


# =============================================================================
# Region
# =============================================================================

class Region(MathpixBaseModel):
    """A detected region within an image.

    Attributes:
        x: X coordinate of top-left corner
        y: Y coordinate of top-left corner
        width: Region width in pixels
        height: Region height in pixels
        region_type: Type of region (e.g., 'math', 'text', 'diagram')
        confidence: Detection confidence score
        label: Optional label for the region
    """
    x: int = Field(..., ge=0, description="X coordinate of top-left")
    y: int = Field(..., ge=0, description="Y coordinate of top-left")
    width: int = Field(..., gt=0, description="Region width")
    height: int = Field(..., gt=0, description="Region height")
    region_type: str = Field(default="unknown", description="Type of region")
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Detection confidence"
    )
    label: Optional[str] = Field(default=None, description="Optional label")

    @property
    def area(self) -> int:
        """Calculate region area in pixels."""
        return self.width * self.height

    @property
    def center(self) -> tuple:
        """Get center point of region."""
        return (self.x + self.width // 2, self.y + self.height // 2)


# =============================================================================
# Ingestion Spec
# =============================================================================

class IngestionSpec(MathpixBaseModel):
    """Complete specification for an ingested image.

    This is the primary output of Stage A (Ingestion) and serves as
    input to subsequent pipeline stages.

    Attributes:
        image_id: Unique identifier for the image
        source_path: Original file path (if loaded from file)
        source_url: Original URL (if loaded from URL)
        metadata: Image metadata (format, dimensions, etc.)
        validation: Results of validation checks
        preprocessing_applied: List of preprocessing operations applied
        regions_detected: Detected content regions
        math_content_confidence: Estimated confidence of math content
        provenance: Audit trail information
        created_at: When the spec was created
        stored_path: Path where processed image is stored
        notes: Optional processing notes
    """
    image_id: str = Field(..., min_length=1, description="Unique image identifier")
    source_path: Optional[str] = Field(default=None, description="Original file path")
    source_url: Optional[str] = Field(default=None, description="Original URL")

    metadata: ImageMetadata = Field(..., description="Image metadata")
    validation: ValidationResult = Field(..., description="Validation results")

    preprocessing_applied: List[str] = Field(
        default_factory=list,
        description="Applied preprocessing operations"
    )
    regions_detected: List[Region] = Field(
        default_factory=list,
        description="Detected content regions"
    )

    math_content_confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Confidence that image contains math"
    )

    provenance: Provenance = Field(
        default_factory=lambda: Provenance(
            stage=PipelineStage.INGESTION,
            model="ingestion-pipeline",
        ),
        description="Audit trail"
    )

    created_at: datetime = Field(
        default_factory=utc_now,
        description="Creation timestamp"
    )

    stored_path: Optional[str] = Field(
        default=None,
        description="Path to stored processed image"
    )

    notes: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Processing notes"
    )

    @field_validator("preprocessing_applied")
    @classmethod
    def unique_operations(cls, v: List[str]) -> List[str]:
        """Ensure preprocessing operations are unique."""
        return list(dict.fromkeys(v))

    @property
    def is_from_file(self) -> bool:
        """Check if image was loaded from a file."""
        return self.source_path is not None

    @property
    def is_from_url(self) -> bool:
        """Check if image was loaded from a URL."""
        return self.source_url is not None

    @property
    def has_math_content(self) -> bool:
        """Check if image likely contains math content."""
        return self.math_content_confidence >= 0.5

    @property
    def region_count(self) -> int:
        """Get number of detected regions."""
        return len(self.regions_detected)


# =============================================================================
# Factory Functions
# =============================================================================

def create_ingestion_spec(
    image_id: str,
    format: str,
    width: int,
    height: int,
    file_size_bytes: int,
    color_mode: str = "RGB",
    dpi: Optional[int] = None,
    content_hash: Optional[str] = None,
    source_path: Optional[str] = None,
    source_url: Optional[str] = None,
    is_valid: bool = True,
    checks_passed: Optional[List[str]] = None,
    checks_failed: Optional[List[str]] = None,
    warnings: Optional[List[str]] = None,
    preprocessing_applied: Optional[List[str]] = None,
    regions: Optional[List[Region]] = None,
    math_confidence: float = 0.5,
    stored_path: Optional[str] = None,
) -> IngestionSpec:
    """Factory function to create an IngestionSpec.

    This provides a convenient way to create an IngestionSpec
    with common default values.

    Args:
        image_id: Unique identifier
        format: Image format
        width: Width in pixels
        height: Height in pixels
        file_size_bytes: File size
        color_mode: Color mode
        dpi: DPI if available
        content_hash: SHA256 hash
        source_path: Original file path
        source_url: Original URL
        is_valid: Validation status
        checks_passed: Passed validation checks
        checks_failed: Failed validation checks
        warnings: Validation warnings
        preprocessing_applied: Applied preprocessing
        regions: Detected regions
        math_confidence: Math content confidence
        stored_path: Storage path

    Returns:
        Configured IngestionSpec
    """
    return IngestionSpec(
        image_id=image_id,
        source_path=source_path,
        source_url=source_url,
        metadata=ImageMetadata(
            format=format,
            width=width,
            height=height,
            dpi=dpi,
            color_mode=color_mode,
            file_size_bytes=file_size_bytes,
            content_hash=content_hash,
        ),
        validation=ValidationResult(
            is_valid=is_valid,
            checks_passed=checks_passed or [],
            checks_failed=checks_failed or [],
            warnings=warnings or [],
        ),
        preprocessing_applied=preprocessing_applied or [],
        regions_detected=regions or [],
        math_content_confidence=math_confidence,
        stored_path=stored_path,
    )


# =============================================================================
# Export
# =============================================================================

__all__ = [
    "ImageMetadata",
    "ValidationResult",
    "Region",
    "IngestionSpec",
    "create_ingestion_spec",
]
