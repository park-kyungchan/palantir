"""
HumanReview Schema for Stage G (Human Review) Data Types.

Stage G provides human-in-the-loop verification for pipeline outputs:
- ReviewTask: Task queued for human review
- Annotation: Human annotations and corrections
- ReviewResult: Completed review output

Schema Version: 2.0.0
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import Field, model_validator

from .common import (
    BBox,
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

class ReviewStatus(str, Enum):
    """Status of a review task."""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"
    EXPIRED = "expired"
    ESCALATED = "escalated"


class ReviewDecision(str, Enum):
    """Decision made by reviewer."""
    APPROVE = "approve"
    REJECT = "reject"
    MODIFY = "modify"
    ESCALATE = "escalate"
    SKIP = "skip"


class ReviewPriority(str, Enum):
    """Priority levels for review tasks."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class CorrectionType(str, Enum):
    """Types of corrections that can be made."""
    # Content corrections
    TEXT_CORRECTION = "text_correction"
    LATEX_CORRECTION = "latex_correction"
    LABEL_CORRECTION = "label_correction"

    # Structural corrections
    BBOX_ADJUSTMENT = "bbox_adjustment"
    TYPE_CHANGE = "type_change"
    RELATION_ADD = "relation_add"
    RELATION_REMOVE = "relation_remove"

    # Confidence overrides
    CONFIDENCE_OVERRIDE = "confidence_override"
    THRESHOLD_OVERRIDE = "threshold_override"

    # Semantic corrections
    MERGE_ELEMENTS = "merge_elements"
    SPLIT_ELEMENT = "split_element"
    DELETE_ELEMENT = "delete_element"
    ADD_ELEMENT = "add_element"


# =============================================================================
# Correction Model
# =============================================================================

class Correction(MathpixBaseModel):
    """A single correction to an element.

    Represents a specific change made by a reviewer
    to an element during the review process.
    """
    correction_id: str = Field(..., description="Unique correction identifier")
    correction_type: CorrectionType

    # What was changed
    element_id: str = Field(..., description="ID of corrected element")
    field_name: str = Field(..., description="Field that was corrected")

    # Values
    original_value: Any = Field(..., description="Value before correction")
    corrected_value: Any = Field(..., description="Value after correction")

    # Confidence override
    confidence_override: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="New confidence score if overridden"
    )

    # BBox correction
    original_bbox: Optional[BBox] = Field(default=None)
    corrected_bbox: Optional[BBox] = Field(default=None)

    # Reason and notes
    reason: Optional[str] = Field(default=None, description="Why correction was made")
    notes: Optional[str] = Field(default=None, description="Additional reviewer notes")

    # Timestamp
    created_at: datetime = Field(default_factory=utc_now)


# =============================================================================
# Annotation Model
# =============================================================================

class Annotation(MathpixBaseModel):
    """Collection of corrections for a review task.

    Groups all corrections made during a review session
    with metadata about the annotation process.
    """
    annotation_id: str = Field(..., description="Unique annotation identifier")
    task_id: str = Field(..., description="Associated review task ID")
    reviewer_id: str = Field(..., description="Reviewer who made annotations")

    # Corrections
    corrections: List[Correction] = Field(
        default_factory=list,
        description="List of corrections made"
    )

    # Summary
    correction_count: int = Field(default=0)
    confidence_override: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Overall confidence override"
    )

    # Comments
    comments: str = Field(default="", description="General comments from reviewer")

    # Quality flags
    flagged_for_training: bool = Field(
        default=False,
        description="Flag for inclusion in training data"
    )
    flagged_for_edge_case: bool = Field(
        default=False,
        description="Flag as edge case for review"
    )

    # Timestamps
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @model_validator(mode="after")
    def update_counts(self) -> "Annotation":
        """Update correction count."""
        self.correction_count = len(self.corrections)
        return self


# =============================================================================
# Review Task Model
# =============================================================================

class ReviewTaskContext(MathpixBaseModel):
    """Context information for a review task.

    Contains data from pipeline stages to help
    the reviewer understand what needs review.
    """
    # Source information
    image_id: str = Field(..., description="Source image identifier")
    pipeline_stage: PipelineStage = Field(..., description="Stage that flagged for review")

    # Element information
    element_type: str = Field(..., description="Type of element (node, edge, match, etc.)")
    element_id: str = Field(..., description="ID of the element under review")
    element_content: Optional[str] = Field(default=None, description="Textual content if applicable")
    element_bbox: Optional[BBox] = Field(default=None, description="Bounding box if applicable")

    # Confidence information
    original_confidence: float = Field(..., ge=0.0, le=1.0)
    applied_threshold: float = Field(..., ge=0.0, le=1.0)
    threshold_delta: float = Field(default=0.0, description="confidence - threshold")

    # Additional context
    review_reason: str = Field(..., description="Why this element needs review")
    related_elements: List[str] = Field(default_factory=list, description="IDs of related elements")

    @model_validator(mode="after")
    def compute_delta(self) -> "ReviewTaskContext":
        """Compute threshold delta."""
        self.threshold_delta = self.original_confidence - self.applied_threshold
        return self


class ReviewTask(MathpixBaseModel):
    """A task queued for human review.

    Represents a single element that requires human verification,
    containing all context needed for the reviewer to make a decision.
    """
    # Identifiers
    task_id: str = Field(..., description="Unique task identifier")
    image_id: str = Field(..., description="Source image identifier")

    # Priority and status
    priority: ReviewPriority = Field(default=ReviewPriority.MEDIUM)
    status: ReviewStatus = Field(default=ReviewStatus.PENDING)
    severity: ReviewSeverity = Field(default=ReviewSeverity.MEDIUM)

    # Assignment
    assigned_to: Optional[str] = Field(default=None, description="Reviewer ID")
    assigned_queue: Optional[str] = Field(default=None, description="Queue name")

    # Context
    context: ReviewTaskContext = Field(..., description="Review context information")

    # Scheduling
    created_at: datetime = Field(default_factory=utc_now)
    due_at: Optional[datetime] = Field(default=None, description="Optional deadline")
    expires_at: Optional[datetime] = Field(default=None, description="Auto-expire time")

    # Result (populated after review)
    decision: Optional[ReviewDecision] = Field(default=None)
    decision_reason: Optional[str] = Field(default=None)

    @model_validator(mode="after")
    def sync_image_id(self) -> "ReviewTask":
        """Ensure image_id is synced with context."""
        if self.context and hasattr(self.context, 'image_id'):
            if not self.image_id:
                self.image_id = self.context.image_id
        return self


# =============================================================================
# Review Result Model
# =============================================================================

class ReviewResult(MathpixBaseModel):
    """Result of a completed human review.

    Contains the review decision, annotation, and metadata
    from the review process.
    """
    result_id: str = Field(..., description="Unique result identifier")
    task_id: str = Field(..., description="Associated review task ID")
    session_id: Optional[str] = Field(default=None, description="Review session ID")

    # Reviewer
    reviewer_id: str = Field(..., description="Reviewer who completed the review")

    # Decision
    decision: ReviewDecision
    decision_reason: Optional[str] = Field(default=None)

    # Annotation
    annotation: Optional[Annotation] = Field(default=None)

    # Metrics
    review_time_ms: float = Field(..., description="Time spent reviewing in milliseconds")
    correction_count: int = Field(default=0)

    # Final confidence
    final_confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Final confidence after review"
    )

    # Provenance
    provenance: Provenance = Field(default_factory=lambda: Provenance(
        stage=PipelineStage.HUMAN_REVIEW,
        model="human-reviewer"
    ))

    # Timestamps
    created_at: datetime = Field(default_factory=utc_now)

    @model_validator(mode="after")
    def compute_correction_count(self) -> "ReviewResult":
        """Compute correction count from annotation."""
        if self.annotation:
            self.correction_count = self.annotation.correction_count
        return self


# =============================================================================
# Review Statistics
# =============================================================================

class ReviewStatistics(MathpixBaseModel):
    """Statistics for review operations."""
    # Task counts
    total_tasks_created: int = Field(default=0)
    tasks_pending: int = Field(default=0)
    tasks_completed: int = Field(default=0)
    tasks_rejected: int = Field(default=0)
    tasks_escalated: int = Field(default=0)
    tasks_expired: int = Field(default=0)

    # Decision distribution
    approvals: int = Field(default=0)
    rejections: int = Field(default=0)
    modifications: int = Field(default=0)
    escalations: int = Field(default=0)

    # Time metrics (in milliseconds)
    avg_queue_time_ms: float = Field(default=0.0)
    avg_review_time_ms: float = Field(default=0.0)

    # Quality metrics
    avg_corrections_per_review: float = Field(default=0.0)
    flagged_for_training_count: int = Field(default=0)

    # Last updated
    computed_at: datetime = Field(default_factory=utc_now)


# =============================================================================
# Export
# =============================================================================

__all__ = [
    # Enums
    "ReviewStatus",
    "ReviewDecision",
    "ReviewPriority",
    "CorrectionType",
    # Models
    "Correction",
    "Annotation",
    "ReviewTaskContext",
    "ReviewTask",
    "ReviewResult",
    "ReviewStatistics",
]
