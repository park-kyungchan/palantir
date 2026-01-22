"""
AlignmentReport Schema for Stage D (Alignment) Output.

Stage D aligns text content (Stage B) with visual elements (Stage C):
- Matches text labels to diagram elements
- Detects inconsistencies between text and visual
- Applies threshold-based review decisions

Schema Version: 2.0.0
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import Field, computed_field

from .common import (
    BBox,
    Confidence,
    MathpixBaseModel,
    Provenance,
    PipelineStage,
    ReviewMetadata,
    ReviewSeverity,
    RiskLevel,
    utc_now,
)


# =============================================================================
# Enums
# =============================================================================

class MatchType(str, Enum):
    """Types of text-visual matches."""
    LABEL_TO_POINT = "label_to_point"
    LABEL_TO_CURVE = "label_to_curve"
    EQUATION_TO_GRAPH = "equation_to_graph"
    DESCRIPTION_TO_ELEMENT = "description_to_element"
    COORDINATE_TO_POINT = "coordinate_to_point"
    AXIS_LABEL = "axis_label"


class InconsistencyType(str, Enum):
    """Types of text-visual inconsistencies."""
    LABEL_MISMATCH = "label_mismatch"
    COORDINATE_MISMATCH = "coordinate_mismatch"
    EQUATION_GRAPH_MISMATCH = "equation_graph_mismatch"
    MISSING_LABEL = "missing_label"
    EXTRA_LABEL = "extra_label"
    SCALE_INCONSISTENCY = "scale_inconsistency"
    AMBIGUOUS_REFERENCE = "ambiguous_reference"


# =============================================================================
# Sub-Models
# =============================================================================

class TextElement(MathpixBaseModel):
    """Reference to a text element from Stage B."""
    id: str = Field(..., description="Element ID from TextSpec")
    content: str = Field(..., description="Text content")
    latex: Optional[str] = Field(default=None)
    bbox: Optional[BBox] = Field(default=None)
    source_line_id: Optional[str] = Field(default=None)


class VisualElement(MathpixBaseModel):
    """Reference to a visual element from Stage C."""
    id: str = Field(..., description="Element ID from VisionSpec")
    element_class: str = Field(..., description="Element class")
    semantic_label: str = Field(..., description="Semantic label from Claude")
    bbox: BBox
    source_merged_id: Optional[str] = Field(default=None)


class MatchedPair(MathpixBaseModel):
    """A matched pair of text and visual elements."""
    id: str = Field(..., description="Match pair identifier")
    match_type: MatchType

    # Matched elements
    text_element: TextElement
    visual_element: VisualElement

    # Confidence and scoring
    consistency_score: float = Field(..., ge=0.0, le=1.0)
    confidence: Confidence
    applied_threshold: float = Field(..., ge=0.0, le=1.0)

    # Alignment details
    spatial_overlap: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    semantic_similarity: Optional[float] = Field(default=None, ge=0.0, le=1.0)

    @computed_field
    @property
    def threshold_passed(self) -> bool:
        """Computed from consistency_score vs threshold."""
        return self.consistency_score >= self.applied_threshold

    @computed_field
    @property
    def review(self) -> ReviewMetadata:
        """Computed review metadata based on threshold check."""
        if self.consistency_score < self.applied_threshold:
            if self.consistency_score < 0.4:
                severity = ReviewSeverity.HIGH
            else:
                severity = ReviewSeverity.MEDIUM
            return ReviewMetadata(
                review_required=True,
                review_severity=severity,
                review_reason=(
                    f"Consistency score {self.consistency_score:.2f} below "
                    f"threshold {self.applied_threshold:.2f}"
                ),
            )
        return ReviewMetadata()


class Inconsistency(MathpixBaseModel):
    """A detected inconsistency between text and visual."""
    id: str = Field(..., description="Inconsistency identifier")
    inconsistency_type: InconsistencyType
    severity: ReviewSeverity

    # Elements involved
    text_element: Optional[TextElement] = Field(default=None)
    visual_element: Optional[VisualElement] = Field(default=None)

    # Details
    description: str = Field(..., description="Human-readable description")
    expected_value: Optional[str] = Field(default=None)
    actual_value: Optional[str] = Field(default=None)

    # Scoring
    confidence: float = Field(..., ge=0.0, le=1.0)
    threshold_passed: bool = Field(default=False)
    applied_threshold: float = Field(default=0.80)  # inconsistency threshold is high

    # Auto-fix suggestion
    suggested_fix: Optional[str] = Field(default=None)
    auto_fixable: bool = Field(default=False)

    @computed_field
    @property
    def review(self) -> ReviewMetadata:
        """Computed review metadata based on severity."""
        return ReviewMetadata(
            review_required=True,
            review_severity=self.severity,
            review_reason=f"{self.inconsistency_type.value}: {self.description}",
        )


class UnmatchedElement(MathpixBaseModel):
    """An element that could not be matched."""
    id: str
    source: str = Field(..., description="'text' or 'visual'")
    element_id: str = Field(..., description="Original element ID")
    content: str = Field(..., description="Element content/label")
    bbox: Optional[BBox] = Field(default=None)
    reason: str = Field(..., description="Why matching failed")


class AlignmentStatistics(MathpixBaseModel):
    """Statistics about the alignment process.

    Note: Most fields are now computed in AlignmentReport using @computed_field.
    This class retains only input fields that cannot be computed.
    """
    total_text_elements: int = Field(default=0)
    total_visual_elements: int = Field(default=0)


# =============================================================================
# Main Schema
# =============================================================================

class AlignmentReport(MathpixBaseModel):
    """Stage D output: Alignment Report.

    Contains the results of aligning Stage B (text) with Stage C (visual):
    - matched_pairs: Successfully aligned elements
    - inconsistencies: Detected mismatches
    - unmatched: Elements without matches

    v2.0.0 Additions:
    - Threshold integration from threshold_calibration.yaml
    - Per-element threshold application
    - Automatic severity assignment based on threshold

    v2.1.0 Refactor:
    - Converted mutable statistics to @computed_field
    - Eliminated object.__setattr__ bypass patterns
    """
    # Metadata
    schema_version: str = Field(default="2.1.0")
    image_id: str = Field(..., description="Source image identifier")
    text_spec_id: str = Field(..., description="Reference to Stage B output")
    vision_spec_id: str = Field(..., description="Reference to Stage C output")
    provenance: Provenance = Field(default_factory=lambda: Provenance(
        stage=PipelineStage.ALIGNMENT,
        model="alignment-engine-v2"
    ))

    # Alignment results
    matched_pairs: List[MatchedPair] = Field(default_factory=list)
    inconsistencies: List[Inconsistency] = Field(default_factory=list)
    unmatched_elements: List[UnmatchedElement] = Field(default_factory=list)

    # Input statistics (from upstream stages)
    statistics: AlignmentStatistics = Field(default_factory=AlignmentStatistics)

    # Threshold configuration used
    threshold_config_version: str = Field(default="2.0.0")
    base_alignment_threshold: float = Field(default=0.60)
    base_inconsistency_threshold: float = Field(default=0.80)

    # Overall scores
    overall_alignment_score: float = Field(default=0.0, ge=0.0, le=1.0)
    overall_confidence: float = Field(default=0.0, ge=0.0, le=1.0)

    # Timestamps
    created_at: datetime = Field(default_factory=utc_now)
    processing_time_ms: Optional[float] = Field(default=None)

    # ==========================================================================
    # Computed Statistics (v2.1.0 - replaces @model_validator with object.__setattr__)
    # ==========================================================================

    @computed_field
    @property
    def matched_pairs_count(self) -> int:
        """Count of matched pairs."""
        return len(self.matched_pairs)

    @computed_field
    @property
    def inconsistencies_found(self) -> int:
        """Count of inconsistencies found."""
        return len(self.inconsistencies)

    @computed_field
    @property
    def unmatched_text_count(self) -> int:
        """Count of unmatched text elements."""
        return len([e for e in self.unmatched_elements if e.source == "text"])

    @computed_field
    @property
    def unmatched_visual_count(self) -> int:
        """Count of unmatched visual elements."""
        return len([e for e in self.unmatched_elements if e.source == "visual"])

    @computed_field
    @property
    def pairs_above_threshold(self) -> int:
        """Count of pairs above threshold."""
        return len([p for p in self.matched_pairs if p.threshold_passed])

    @computed_field
    @property
    def pairs_below_threshold(self) -> int:
        """Count of pairs below threshold."""
        return len([p for p in self.matched_pairs if not p.threshold_passed])

    @computed_field
    @property
    def avg_consistency_score(self) -> float:
        """Average consistency score across matched pairs."""
        if not self.matched_pairs:
            return 0.0
        scores = [p.consistency_score for p in self.matched_pairs]
        return sum(scores) / len(scores)

    @computed_field
    @property
    def min_consistency_score(self) -> float:
        """Minimum consistency score across matched pairs."""
        if not self.matched_pairs:
            return 1.0
        return min(p.consistency_score for p in self.matched_pairs)

    @computed_field
    @property
    def max_consistency_score(self) -> float:
        """Maximum consistency score across matched pairs."""
        if not self.matched_pairs:
            return 0.0
        return max(p.consistency_score for p in self.matched_pairs)

    @computed_field
    @property
    def blocker_count(self) -> int:
        """Count of blocker-severity inconsistencies."""
        return len([
            i for i in self.inconsistencies
            if i.severity == ReviewSeverity.BLOCKER
        ])

    @computed_field
    @property
    def high_severity_count(self) -> int:
        """Count of high-severity inconsistencies."""
        return len([
            i for i in self.inconsistencies
            if i.severity == ReviewSeverity.HIGH
        ])

    @computed_field
    @property
    def review(self) -> ReviewMetadata:
        """Computed overall review metadata based on severity counts."""
        if self.blocker_count > 0:
            return ReviewMetadata(
                review_required=True,
                review_severity=ReviewSeverity.BLOCKER,
                review_reason=f"{self.blocker_count} blocker inconsistencies",
            )
        elif self.high_severity_count > 0:
            return ReviewMetadata(
                review_required=True,
                review_severity=ReviewSeverity.HIGH,
                review_reason=f"{self.high_severity_count} high-severity issues",
            )
        elif self.pairs_below_threshold > 0:
            return ReviewMetadata(
                review_required=True,
                review_severity=ReviewSeverity.MEDIUM,
                review_reason=f"{self.pairs_below_threshold} pairs below threshold",
            )
        return ReviewMetadata()

    def has_blockers(self) -> bool:
        """Check if any blocker issues exist."""
        return self.blocker_count > 0

    def needs_human_review(self) -> bool:
        """Check if human review is required.

        Returns True if:
        - Top-level review.review_required is True
        - Any inconsistency has review_required=True
        - Any matched pair has review_required=True
        """
        if self.review.review_required:
            return True
        # Check inconsistencies
        for inc in self.inconsistencies:
            if inc.review.review_required:
                return True
        # Check matched pairs below threshold
        for pair in self.matched_pairs:
            if pair.review.review_required:
                return True
        return False


# =============================================================================
# Export
# =============================================================================

__all__ = [
    # Enums
    "MatchType",
    "InconsistencyType",
    # Sub-Models
    "TextElement",
    "VisualElement",
    "MatchedPair",
    "Inconsistency",
    "UnmatchedElement",
    "AlignmentStatistics",
    # Main Schema
    "AlignmentReport",
]
