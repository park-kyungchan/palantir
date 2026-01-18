"""
Export Schema for Stage H (Export) Output.

Stage H handles final export of pipeline results:
- Multiple export formats (JSON, PDF, LaTeX, SVG)
- Batch export operations
- Storage management
- API response structures

Schema Version: 2.0.0
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import Field, field_validator, model_validator

from .common import (
    MathpixBaseModel,
    PipelineStage,
    Provenance,
    ReviewMetadata,
    utc_now,
)


# =============================================================================
# Enums
# =============================================================================

class ExportFormat(str, Enum):
    """Supported export formats."""
    JSON = "json"
    PDF = "pdf"
    LATEX = "latex"
    SVG = "svg"
    PNG = "png"
    ZIP = "zip"  # Bundle format


class ExportStatus(str, Enum):
    """Status of export operation."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StorageType(str, Enum):
    """Types of storage destinations."""
    LOCAL = "local"
    S3 = "s3"
    GCS = "gcs"  # Google Cloud Storage
    AZURE = "azure"
    MEMORY = "memory"  # In-memory (for testing)


# =============================================================================
# Export Options
# =============================================================================

class ExportOptions(MathpixBaseModel):
    """Options for export operations.

    Controls various aspects of the export process including
    metadata inclusion, compression, and format-specific settings.
    """
    # General options
    include_metadata: bool = Field(
        default=True,
        description="Include pipeline metadata in export"
    )
    include_provenance: bool = Field(
        default=True,
        description="Include provenance chain"
    )
    compress: bool = Field(
        default=False,
        description="Compress output files"
    )
    compression_level: int = Field(
        default=6,
        ge=1,
        le=9,
        description="Compression level (1-9)"
    )

    # Content options
    include_original_image: bool = Field(
        default=False,
        description="Include original image in export"
    )
    include_intermediate_stages: bool = Field(
        default=False,
        description="Include outputs from all pipeline stages"
    )
    include_confidence_scores: bool = Field(
        default=True,
        description="Include confidence metrics"
    )
    include_review_data: bool = Field(
        default=True,
        description="Include human review annotations"
    )

    # Format-specific options
    pdf_options: Dict[str, Any] = Field(
        default_factory=lambda: {
            "page_size": "letter",
            "margins": {"top": 1, "bottom": 1, "left": 1, "right": 1},
            "include_toc": False,
        }
    )
    latex_options: Dict[str, Any] = Field(
        default_factory=lambda: {
            "document_class": "article",
            "packages": ["amsmath", "amssymb", "tikz"],
            "standalone": False,
        }
    )
    svg_options: Dict[str, Any] = Field(
        default_factory=lambda: {
            "width": 800,
            "height": 600,
            "embed_fonts": True,
        }
    )

    # Naming options
    filename_template: str = Field(
        default="{image_id}_{format}_{timestamp}",
        description="Template for output filenames"
    )


class StorageConfig(MathpixBaseModel):
    """Configuration for export storage.

    Defines where and how exported files are stored.
    """
    storage_type: StorageType = Field(default=StorageType.LOCAL)
    base_path: str = Field(
        default="./exports",
        description="Base path for local storage"
    )

    # Cloud storage options
    bucket: Optional[str] = Field(default=None, description="Bucket name for cloud storage")
    prefix: Optional[str] = Field(default=None, description="Key prefix for cloud storage")
    region: Optional[str] = Field(default=None, description="Cloud region")

    # Retention options
    retention_days: int = Field(default=30, description="Days to retain exports")
    auto_cleanup: bool = Field(default=True, description="Auto-delete expired exports")


# =============================================================================
# Export Spec
# =============================================================================

class ExportSpec(MathpixBaseModel):
    """Specification for a single export output.

    Contains metadata about an exported file including
    location, format, size, and timing information.
    """
    # Identification
    export_id: str = Field(..., description="Unique export identifier")
    image_id: str = Field(..., description="Source image identifier")

    # Format and content
    format: ExportFormat = Field(..., description="Export format")
    content_type: str = Field(
        default="application/octet-stream",
        description="MIME content type"
    )

    # Storage location
    file_path: Optional[str] = Field(default=None, description="Local file path")
    storage_url: Optional[str] = Field(default=None, description="Cloud storage URL")
    storage_type: StorageType = Field(default=StorageType.LOCAL)

    # File metadata
    file_size: int = Field(default=0, ge=0, description="File size in bytes")
    checksum: Optional[str] = Field(default=None, description="SHA256 checksum")
    compressed: bool = Field(default=False, description="Whether file is compressed")

    # Content summary
    element_count: int = Field(default=0, description="Number of elements exported")
    page_count: int = Field(default=1, description="Number of pages (for PDF)")

    # Quality metrics
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Export quality confidence"
    )

    # Timestamps
    created_at: datetime = Field(default_factory=utc_now)
    expires_at: Optional[datetime] = Field(default=None)
    processing_time_ms: float = Field(default=0.0)

    @property
    def is_expired(self) -> bool:
        """Check if export has expired."""
        if self.expires_at is None:
            return False
        return datetime.now(self.expires_at.tzinfo) > self.expires_at


class BatchExportSpec(MathpixBaseModel):
    """Specification for a batch export operation.

    Contains multiple ExportSpecs from a batch operation
    along with aggregate statistics.
    """
    # Identification
    batch_id: str = Field(..., description="Unique batch identifier")

    # Individual exports
    exports: List[ExportSpec] = Field(
        default_factory=list,
        description="Individual export specifications"
    )

    # Statistics
    total_requested: int = Field(default=0)
    total_completed: int = Field(default=0)
    total_failed: int = Field(default=0)
    total_size_bytes: int = Field(default=0)

    # Timing
    started_at: datetime = Field(default_factory=utc_now)
    completed_at: Optional[datetime] = Field(default=None)
    total_time_ms: float = Field(default=0.0)

    @model_validator(mode="after")
    def compute_stats(self) -> "BatchExportSpec":
        """Compute statistics from exports list.

        Uses object.__setattr__ to bypass validate_assignment and avoid recursion.
        """
        object.__setattr__(self, "total_completed", len([e for e in self.exports]))
        object.__setattr__(self, "total_size_bytes", sum(e.file_size for e in self.exports))
        return self


# =============================================================================
# Export Job
# =============================================================================

class ExportJob(MathpixBaseModel):
    """Represents an async export job.

    Used for tracking long-running export operations,
    especially batch exports or PDF generation.
    """
    # Identification
    job_id: str = Field(..., description="Unique job identifier")
    image_id: Optional[str] = Field(default=None, description="Single image ID")
    image_ids: List[str] = Field(default_factory=list, description="Batch image IDs")

    # Job configuration
    formats: List[ExportFormat] = Field(default_factory=list)
    options: ExportOptions = Field(default_factory=ExportOptions)
    storage_config: StorageConfig = Field(default_factory=StorageConfig)

    # Status
    status: ExportStatus = Field(default=ExportStatus.PENDING)
    progress_percent: float = Field(default=0.0, ge=0.0, le=100.0)
    current_step: Optional[str] = Field(default=None)

    # Results
    result: Optional[ExportSpec] = Field(default=None)
    batch_result: Optional[BatchExportSpec] = Field(default=None)

    # Error handling
    error_message: Optional[str] = Field(default=None)
    retry_count: int = Field(default=0)
    max_retries: int = Field(default=3)

    # Timestamps
    created_at: datetime = Field(default_factory=utc_now)
    started_at: Optional[datetime] = Field(default=None)
    completed_at: Optional[datetime] = Field(default=None)

    @property
    def is_batch(self) -> bool:
        """Check if this is a batch job."""
        return len(self.image_ids) > 1

    @property
    def is_complete(self) -> bool:
        """Check if job is complete (success or failure)."""
        return self.status in (ExportStatus.COMPLETED, ExportStatus.FAILED, ExportStatus.CANCELLED)


# =============================================================================
# API Types
# =============================================================================

class ExportRequest(MathpixBaseModel):
    """API request for export operation.

    Standard request structure for export endpoints.
    """
    image_id: Optional[str] = Field(default=None, description="Single image to export")
    image_ids: List[str] = Field(default_factory=list, description="Multiple images to export")
    formats: List[ExportFormat] = Field(
        default_factory=lambda: [ExportFormat.JSON],
        description="Desired export formats"
    )
    options: ExportOptions = Field(default_factory=ExportOptions)
    async_mode: bool = Field(
        default=False,
        description="Run export asynchronously"
    )

    @model_validator(mode="after")
    def validate_images(self) -> "ExportRequest":
        """Ensure at least one image is specified."""
        if not self.image_id and not self.image_ids:
            raise ValueError("Either image_id or image_ids must be provided")
        return self


class ExportResponse(MathpixBaseModel):
    """API response for export operation.

    Standard response structure for export endpoints.
    """
    success: bool = Field(default=True)
    message: Optional[str] = Field(default=None)

    # For sync exports
    export: Optional[ExportSpec] = Field(default=None)
    exports: List[ExportSpec] = Field(default_factory=list)

    # For async exports
    job_id: Optional[str] = Field(default=None)
    job: Optional[ExportJob] = Field(default=None)

    # Timing
    processing_time_ms: float = Field(default=0.0)


class ExportStatusResponse(MathpixBaseModel):
    """API response for export status check."""
    job_id: str
    status: ExportStatus
    progress_percent: float = Field(default=0.0)
    current_step: Optional[str] = Field(default=None)
    result: Optional[ExportSpec] = Field(default=None)
    batch_result: Optional[BatchExportSpec] = Field(default=None)
    error_message: Optional[str] = Field(default=None)


# =============================================================================
# Export
# =============================================================================

__all__ = [
    # Enums
    "ExportFormat",
    "ExportStatus",
    "StorageType",
    # Options
    "ExportOptions",
    "StorageConfig",
    # Specs
    "ExportSpec",
    "BatchExportSpec",
    # Job
    "ExportJob",
    # API Types
    "ExportRequest",
    "ExportResponse",
    "ExportStatusResponse",
]
