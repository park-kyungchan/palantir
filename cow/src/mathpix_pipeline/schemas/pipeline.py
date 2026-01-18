"""
Pipeline Schema for Math Image Parsing Pipeline v2.0.

Defines schemas for pipeline orchestration:
- PipelineOptions: Configuration for pipeline execution
- PipelineResult: Complete result from pipeline processing

Schema Version: 2.0.0
"""

from datetime import datetime
from typing import Any, List, Optional

from pydantic import Field, model_validator

from .common import (
    MathpixBaseModel,
    PipelineStage,
    Provenance,
    ReviewMetadata,
    utc_now,
)
from .ingestion import IngestionSpec
from .text_spec import TextSpec
from .vision_spec import VisionSpec
from .alignment import AlignmentReport
from .semantic_graph import SemanticGraph
from .regeneration import RegenerationSpec
from .export import ExportSpec


# =============================================================================
# Pipeline Options
# =============================================================================

class PipelineOptions(MathpixBaseModel):
    """Options for pipeline execution.

    Controls which stages to run, export formats, and other
    pipeline behavior settings.

    Attributes:
        skip_stages: List of pipeline stages to skip
        export_formats: List of export format names to generate
        enable_human_review: Whether to enable human review stage
        timeout_seconds: Maximum time for pipeline execution
        enable_parallel_processing: Whether to enable parallel stage execution
        enable_caching: Whether to cache intermediate results
        strict_validation: Whether to fail on validation warnings
        min_confidence_threshold: Minimum confidence to pass pipeline
    """
    skip_stages: List[PipelineStage] = Field(
        default_factory=list,
        description="Pipeline stages to skip"
    )
    export_formats: List[str] = Field(
        default_factory=lambda: ["json"],
        description="Export formats to generate"
    )
    enable_human_review: bool = Field(
        default=False,
        description="Enable human review stage"
    )
    timeout_seconds: int = Field(
        default=300,
        ge=1,
        le=3600,
        description="Maximum execution time in seconds"
    )
    enable_parallel_processing: bool = Field(
        default=True,
        description="Enable parallel stage execution where possible"
    )
    enable_caching: bool = Field(
        default=True,
        description="Cache intermediate results"
    )
    strict_validation: bool = Field(
        default=False,
        description="Fail on validation warnings"
    )
    min_confidence_threshold: float = Field(
        default=0.60,
        ge=0.0,
        le=1.0,
        description="Minimum confidence threshold"
    )

    def should_skip(self, stage: PipelineStage) -> bool:
        """Check if a stage should be skipped.

        Args:
            stage: Pipeline stage to check

        Returns:
            True if stage should be skipped
        """
        return stage in self.skip_stages


# =============================================================================
# Stage Timing
# =============================================================================

class StageTiming(MathpixBaseModel):
    """Timing information for a single pipeline stage.

    Attributes:
        stage: Pipeline stage identifier
        started_at: When stage started
        completed_at: When stage completed
        duration_ms: Total duration in milliseconds
        success: Whether stage completed successfully
        error_message: Error message if stage failed
    """
    stage: PipelineStage
    started_at: datetime = Field(default_factory=utc_now)
    completed_at: Optional[datetime] = Field(default=None)
    duration_ms: float = Field(default=0.0, ge=0.0)
    success: bool = Field(default=True)
    error_message: Optional[str] = Field(default=None)

    def complete(self, success: bool = True, error: Optional[str] = None) -> None:
        """Mark stage as complete.

        Args:
            success: Whether stage completed successfully
            error: Error message if failed
        """
        self.completed_at = utc_now()
        self.success = success
        self.error_message = error
        if self.completed_at and self.started_at:
            delta = self.completed_at - self.started_at
            self.duration_ms = delta.total_seconds() * 1000


# =============================================================================
# Pipeline Result
# =============================================================================

class PipelineResult(MathpixBaseModel):
    """Result of pipeline execution.

    Contains all outputs from the complete pipeline processing,
    including intermediate stage results and aggregate metrics.

    Attributes:
        image_id: Unique identifier for the processed image
        success: Whether pipeline completed successfully
        stages_completed: List of completed pipeline stages
        ingestion_spec: Stage A output
        text_spec: Stage B output
        vision_spec: Stage C output
        alignment_report: Stage D output
        semantic_graph: Stage E output
        regeneration_spec: Stage F output
        review_result: Stage G output (if enabled)
        export_result: Stage H output
        errors: List of error messages
        warnings: List of warning messages
        processing_time_ms: Total processing time
        stage_timings: Detailed timing for each stage
        overall_confidence: Aggregate confidence score
        provenance: Audit trail information
        created_at: When result was created
        options_used: Pipeline options that were used
    """
    # Identification
    image_id: str = Field(..., min_length=1, description="Image identifier")

    # Overall status
    success: bool = Field(default=False, description="Pipeline success status")
    stages_completed: List[PipelineStage] = Field(
        default_factory=list,
        description="Completed stages"
    )

    # Stage outputs
    ingestion_spec: Optional[IngestionSpec] = Field(
        default=None,
        description="Stage A: Ingestion output"
    )
    text_spec: Optional[TextSpec] = Field(
        default=None,
        description="Stage B: Text parse output"
    )
    vision_spec: Optional[VisionSpec] = Field(
        default=None,
        description="Stage C: Vision parse output"
    )
    alignment_report: Optional[AlignmentReport] = Field(
        default=None,
        description="Stage D: Alignment output"
    )
    semantic_graph: Optional[SemanticGraph] = Field(
        default=None,
        description="Stage E: Semantic graph output"
    )
    regeneration_spec: Optional[RegenerationSpec] = Field(
        default=None,
        description="Stage F: Regeneration output"
    )
    review_result: Optional[Any] = Field(
        default=None,
        description="Stage G: Human review result"
    )
    export_result: Optional[List[ExportSpec]] = Field(
        default=None,
        description="Stage H: Export outputs"
    )

    # Error and warning tracking
    errors: List[str] = Field(
        default_factory=list,
        description="Error messages"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Warning messages"
    )

    # Timing
    processing_time_ms: float = Field(
        default=0.0,
        ge=0.0,
        description="Total processing time"
    )
    stage_timings: List[StageTiming] = Field(
        default_factory=list,
        description="Per-stage timing details"
    )

    # Quality metrics
    overall_confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Aggregate confidence"
    )

    # Metadata
    provenance: Provenance = Field(
        default_factory=lambda: Provenance(
            stage=PipelineStage.EXPORT,  # Final stage
            model="mathpix-pipeline-v2"
        )
    )
    review: ReviewMetadata = Field(default_factory=ReviewMetadata)
    created_at: datetime = Field(default_factory=utc_now)
    options_used: Optional[PipelineOptions] = Field(
        default=None,
        description="Options used for this run"
    )

    @model_validator(mode="after")
    def compute_metrics(self) -> "PipelineResult":
        """Compute aggregate metrics from stage outputs."""
        # Compute overall confidence from available stages
        confidences = []

        if self.alignment_report:
            confidences.append(self.alignment_report.overall_confidence)

        if self.semantic_graph:
            confidences.append(self.semantic_graph.overall_confidence)

        if self.regeneration_spec:
            confidences.append(self.regeneration_spec.overall_confidence)

        if confidences:
            self.overall_confidence = sum(confidences) / len(confidences)

        # Set review requirement if confidence is low
        if self.overall_confidence < 0.70 and not self.review.review_required:
            self.review.review_required = True
            self.review.review_reason = (
                f"Low overall confidence: {self.overall_confidence:.2f}"
            )

        return self

    @property
    def is_complete(self) -> bool:
        """Check if all stages completed."""
        required_stages = [
            PipelineStage.INGESTION,
            PipelineStage.TEXT_PARSE,
            PipelineStage.VISION_PARSE,
            PipelineStage.ALIGNMENT,
            PipelineStage.SEMANTIC_GRAPH,
            PipelineStage.REGENERATION,
            PipelineStage.EXPORT,
        ]
        return all(s in self.stages_completed for s in required_stages)

    @property
    def stage_count(self) -> int:
        """Get number of completed stages."""
        return len(self.stages_completed)

    @property
    def error_count(self) -> int:
        """Get number of errors."""
        return len(self.errors)

    @property
    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return len(self.errors) > 0

    def add_error(self, error: str, stage: Optional[PipelineStage] = None) -> None:
        """Add an error message.

        Args:
            error: Error message
            stage: Optional stage where error occurred
        """
        if stage:
            self.errors.append(f"[{stage.value}] {error}")
        else:
            self.errors.append(error)

    def add_warning(self, warning: str, stage: Optional[PipelineStage] = None) -> None:
        """Add a warning message.

        Args:
            warning: Warning message
            stage: Optional stage where warning occurred
        """
        if stage:
            self.warnings.append(f"[{stage.value}] {warning}")
        else:
            self.warnings.append(warning)

    def mark_stage_complete(self, stage: PipelineStage) -> None:
        """Mark a stage as completed.

        Args:
            stage: Stage that completed
        """
        if stage not in self.stages_completed:
            self.stages_completed.append(stage)

    def get_stage_timing(self, stage: PipelineStage) -> Optional[StageTiming]:
        """Get timing for a specific stage.

        Args:
            stage: Stage to get timing for

        Returns:
            StageTiming or None if not found
        """
        for timing in self.stage_timings:
            if timing.stage == stage:
                return timing
        return None

    def summary(self) -> str:
        """Get human-readable summary.

        Returns:
            Summary string
        """
        status = "SUCCESS" if self.success else "FAILED"
        return (
            f"PipelineResult[{status}]: "
            f"stages={len(self.stages_completed)}/8, "
            f"confidence={self.overall_confidence:.2f}, "
            f"errors={len(self.errors)}, "
            f"time={self.processing_time_ms:.1f}ms"
        )


# =============================================================================
# Export
# =============================================================================

__all__ = [
    "PipelineOptions",
    "StageTiming",
    "PipelineResult",
]
