"""
Regeneration Schema for Stage F (Regeneration) Output.

Stage F regenerates mathematical content from semantic graphs:
- LaTeX output generation
- SVG/TikZ diagram generation
- Delta comparison with original
- Quality scoring

Schema Version: 2.0.0
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import Field, model_validator

from .common import (
    Confidence,
    MathpixBaseModel,
    PipelineStage,
    Provenance,
    ReviewMetadata,
    ReviewSeverity,
    utc_now,
)


# =============================================================================
# Enums
# =============================================================================

class OutputFormat(str, Enum):
    """Supported output formats for regeneration."""
    LATEX = "latex"
    SVG = "svg"
    TIKZ = "tikz"
    MATHML = "mathml"


class DeltaType(str, Enum):
    """Types of differences detected in delta comparison."""
    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"
    UNCHANGED = "unchanged"


class ElementCategory(str, Enum):
    """Categories of elements for regeneration."""
    EQUATION = "equation"
    GRAPH = "graph"
    DIAGRAM = "diagram"
    TEXT = "text"
    SYMBOL = "symbol"
    ANNOTATION = "annotation"


# =============================================================================
# Regeneration Output
# =============================================================================

class RegenerationOutput(MathpixBaseModel):
    """Single format output from regeneration.

    Represents the generated content in a specific format
    with associated metadata and quality metrics.
    """
    format: OutputFormat = Field(..., description="Output format type")
    content: str = Field(..., description="Generated content string")
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence in regeneration quality"
    )
    generation_time_ms: float = Field(
        ...,
        ge=0.0,
        description="Time to generate in milliseconds"
    )

    # Quality metrics
    completeness_score: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Fraction of elements successfully regenerated"
    )
    semantic_fidelity: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Semantic accuracy compared to source graph"
    )

    # Content metadata
    element_count: int = Field(default=0, description="Number of elements regenerated")
    template_used: Optional[str] = Field(default=None, description="Template file used")
    warnings: List[str] = Field(default_factory=list, description="Generation warnings")


class TemplateContext(MathpixBaseModel):
    """Context data passed to Jinja2 templates.

    Contains all variables and settings needed for template rendering.
    """
    # Core data
    nodes: List[Dict[str, Any]] = Field(default_factory=list)
    edges: List[Dict[str, Any]] = Field(default_factory=list)

    # Rendering options
    include_comments: bool = Field(default=False)
    pretty_print: bool = Field(default=True)
    math_mode: str = Field(default="inline")  # inline, display, equation

    # Coordinate system
    coordinate_system: Optional[str] = Field(default=None)
    scale_factor: float = Field(default=1.0)

    # Styling
    line_width: str = Field(default="thin")
    font_size: str = Field(default="normalsize")
    color_scheme: str = Field(default="default")

    # Custom variables
    custom_vars: Dict[str, Any] = Field(default_factory=dict)


# =============================================================================
# Delta Comparison
# =============================================================================

class DeltaElement(MathpixBaseModel):
    """A single element difference in delta comparison.

    Tracks what changed between original and regenerated content.
    """
    element_id: str = Field(..., description="Element identifier")
    delta_type: DeltaType = Field(..., description="Type of change")
    category: ElementCategory = Field(..., description="Element category")

    # Content comparison
    original_content: Optional[str] = Field(default=None)
    regenerated_content: Optional[str] = Field(default=None)

    # Similarity metrics
    similarity_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Similarity between original and regenerated"
    )

    # Location info
    original_position: Optional[Dict[str, float]] = Field(default=None)
    regenerated_position: Optional[Dict[str, float]] = Field(default=None)

    # Details
    change_description: Optional[str] = Field(default=None)


class DeltaReport(MathpixBaseModel):
    """Report of differences between original and regenerated content.

    Provides detailed comparison metrics and element-level diffs.
    """
    # Overall metrics
    similarity_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall similarity between original and regenerated"
    )

    # Element counts by delta type
    added_count: int = Field(default=0)
    removed_count: int = Field(default=0)
    modified_count: int = Field(default=0)
    unchanged_count: int = Field(default=0)

    # Detailed elements
    added_elements: List[DeltaElement] = Field(default_factory=list)
    removed_elements: List[DeltaElement] = Field(default_factory=list)
    modified_elements: List[DeltaElement] = Field(default_factory=list)

    # Quality flags
    has_structural_changes: bool = Field(
        default=False,
        description="True if graph structure differs"
    )
    has_semantic_changes: bool = Field(
        default=False,
        description="True if mathematical meaning differs"
    )
    has_visual_changes: bool = Field(
        default=False,
        description="True if visual representation differs"
    )

    # Comparison metadata
    comparison_method: str = Field(default="structural")
    comparison_time_ms: float = Field(default=0.0)

    @model_validator(mode="after")
    def compute_counts(self) -> "DeltaReport":
        """Ensure counts match element lists.

        Uses object.__setattr__ to bypass validate_assignment and avoid recursion.
        """
        object.__setattr__(self, "added_count", len(self.added_elements))
        object.__setattr__(self, "removed_count", len(self.removed_elements))
        object.__setattr__(self, "modified_count", len(self.modified_elements))
        return self

    @property
    def total_changes(self) -> int:
        """Total number of changes detected."""
        return self.added_count + self.removed_count + self.modified_count

    @property
    def is_identical(self) -> bool:
        """True if no changes detected."""
        return self.total_changes == 0


# =============================================================================
# Regeneration Result
# =============================================================================

class RegenerationResult(MathpixBaseModel):
    """Result of regenerating a single element or group.

    Used for intermediate results during regeneration process.
    """
    element_id: str = Field(..., description="Source element ID")
    category: ElementCategory = Field(..., description="Element category")
    success: bool = Field(default=True, description="Whether regeneration succeeded")

    # Generated content by format
    outputs: Dict[OutputFormat, str] = Field(default_factory=dict)

    # Quality metrics
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    generation_time_ms: float = Field(default=0.0)

    # Error handling
    error_message: Optional[str] = Field(default=None)
    warnings: List[str] = Field(default_factory=list)


# =============================================================================
# Main Schema: RegenerationSpec
# =============================================================================

class RegenerationSpec(MathpixBaseModel):
    """Stage F output: Regeneration Specification.

    Contains all regenerated outputs from a semantic graph:
    - Multiple format outputs (LaTeX, SVG, TikZ, MathML)
    - Delta comparison with original
    - Overall quality metrics

    v2.0.0 Additions:
    - Multi-format output support
    - Delta comparison integration
    - Template-based generation tracking
    - Quality confidence scoring
    """
    # Metadata
    schema_version: str = Field(default="2.0.0")
    image_id: str = Field(..., description="Source image identifier")
    semantic_graph_id: str = Field(..., description="Reference to Stage E output")
    provenance: Provenance = Field(default_factory=lambda: Provenance(
        stage=PipelineStage.REGENERATION,
        model="regeneration-engine-v2"
    ))

    # Generated outputs
    outputs: List[RegenerationOutput] = Field(
        default_factory=list,
        description="Generated outputs in various formats"
    )

    # Delta comparison
    delta_report: Optional[DeltaReport] = Field(
        default=None,
        description="Comparison with original content"
    )

    # Overall metrics
    overall_confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Overall confidence in regeneration quality"
    )
    total_elements_processed: int = Field(default=0)
    total_elements_success: int = Field(default=0)
    total_elements_failed: int = Field(default=0)

    # Individual results (for detailed tracking)
    element_results: List[RegenerationResult] = Field(
        default_factory=list,
        description="Per-element regeneration results"
    )

    # Review
    review: ReviewMetadata = Field(default_factory=ReviewMetadata)

    # Timestamps
    created_at: datetime = Field(default_factory=utc_now)
    processing_time_ms: Optional[float] = Field(default=None)

    @model_validator(mode="after")
    def compute_metrics(self) -> "RegenerationSpec":
        """Compute overall metrics from outputs and results.

        Uses object.__setattr__ to bypass validate_assignment and avoid recursion.
        """
        # Compute overall confidence from outputs
        if self.outputs:
            confidence_sum = sum(o.confidence for o in self.outputs)
            object.__setattr__(self, "overall_confidence", confidence_sum / len(self.outputs))

        # Count element results
        if self.element_results:
            object.__setattr__(self, "total_elements_processed", len(self.element_results))
            object.__setattr__(self, "total_elements_success", len([r for r in self.element_results if r.success]))
            object.__setattr__(self, "total_elements_failed", len([r for r in self.element_results if not r.success]))

        # Set review if confidence is low or delta shows significant changes
        if self.overall_confidence < 0.70:
            self.review.review_required = True
            self.review.review_severity = ReviewSeverity.MEDIUM
            self.review.review_reason = (
                f"Low regeneration confidence: {self.overall_confidence:.2f}"
            )
        elif self.delta_report and not self.delta_report.is_identical:
            if self.delta_report.has_semantic_changes:
                self.review.review_required = True
                self.review.review_severity = ReviewSeverity.HIGH
                self.review.review_reason = "Semantic changes detected in regeneration"

        return self

    def get_output(self, format: OutputFormat) -> Optional[RegenerationOutput]:
        """Get output for a specific format."""
        for output in self.outputs:
            if output.format == format:
                return output
        return None

    def get_latex(self) -> Optional[str]:
        """Convenience method to get LaTeX content."""
        output = self.get_output(OutputFormat.LATEX)
        return output.content if output else None

    def get_svg(self) -> Optional[str]:
        """Convenience method to get SVG content."""
        output = self.get_output(OutputFormat.SVG)
        return output.content if output else None


# =============================================================================
# Export
# =============================================================================

__all__ = [
    # Enums
    "OutputFormat",
    "DeltaType",
    "ElementCategory",
    # Output types
    "RegenerationOutput",
    "TemplateContext",
    # Delta types
    "DeltaElement",
    "DeltaReport",
    # Result types
    "RegenerationResult",
    # Main Schema
    "RegenerationSpec",
]
