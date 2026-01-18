"""
Annotation model for Human Review system.

Represents human annotations and corrections:
- Correction: A single correction to an element
- Annotation: Collection of corrections with metadata
- AnnotationSession: Active review session

Module Version: 1.0.0
"""

from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import Field, model_validator

from ...schemas.common import (
    BBox,
    MathpixBaseModel,
    utc_now,
)


# =============================================================================
# Enums
# =============================================================================

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


class SessionStatus(str, Enum):
    """Status of an annotation session."""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ABANDONED = "abandoned"
    EXPIRED = "expired"


# =============================================================================
# Correction
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
# Annotation
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
    internal_notes: Optional[str] = Field(
        default=None,
        description="Internal notes (not shown to external systems)"
    )

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

    def add_correction(self, correction: Correction) -> None:
        """Add a correction to the annotation."""
        self.corrections.append(correction)
        self.correction_count = len(self.corrections)
        self.updated_at = datetime.now(timezone.utc)

    def remove_correction(self, correction_id: str) -> bool:
        """Remove a correction by ID."""
        original_count = len(self.corrections)
        self.corrections = [c for c in self.corrections if c.correction_id != correction_id]
        self.correction_count = len(self.corrections)
        self.updated_at = datetime.now(timezone.utc)
        return len(self.corrections) < original_count


# =============================================================================
# Annotation Session
# =============================================================================

class AnnotationSession(MathpixBaseModel):
    """Active review session for a task.

    Tracks the state of an ongoing review including
    time limits and session metadata.
    """
    session_id: str = Field(..., description="Unique session identifier")
    task_id: str = Field(..., description="Associated review task ID")
    reviewer_id: str = Field(..., description="Reviewer ID")

    # Session state
    status: SessionStatus = Field(default=SessionStatus.ACTIVE)
    annotation: Optional[Annotation] = Field(default=None)

    # Timing
    started_at: datetime = Field(default_factory=utc_now)
    last_activity_at: datetime = Field(default_factory=utc_now)
    expires_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc) + timedelta(hours=1)
    )

    # Session limits
    timeout_minutes: int = Field(default=60, description="Session timeout in minutes")
    max_duration_minutes: int = Field(default=120, description="Maximum session duration")

    # Activity tracking
    action_count: int = Field(default=0)
    save_count: int = Field(default=0)

    @property
    def is_active(self) -> bool:
        """Check if session is still active."""
        if self.status != SessionStatus.ACTIVE:
            return False
        return datetime.now(timezone.utc) < self.expires_at

    @property
    def is_expired(self) -> bool:
        """Check if session has expired."""
        return datetime.now(timezone.utc) >= self.expires_at

    @property
    def duration_ms(self) -> float:
        """Calculate session duration in milliseconds."""
        end_time = datetime.now(timezone.utc)
        return (end_time - self.started_at).total_seconds() * 1000

    def record_activity(self) -> None:
        """Record activity to extend session."""
        now = datetime.now(timezone.utc)
        self.last_activity_at = now
        self.action_count += 1
        # Extend expiration (sliding window)
        self.expires_at = now + timedelta(minutes=self.timeout_minutes)

    def save_progress(self, annotation: Annotation) -> None:
        """Save annotation progress."""
        self.annotation = annotation
        self.save_count += 1
        self.record_activity()

    def pause(self) -> None:
        """Pause the session."""
        self.status = SessionStatus.PAUSED
        self.last_activity_at = datetime.now(timezone.utc)

    def resume(self) -> None:
        """Resume a paused session."""
        if self.status == SessionStatus.PAUSED:
            self.status = SessionStatus.ACTIVE
            self.record_activity()

    def complete(self) -> None:
        """Mark session as completed."""
        self.status = SessionStatus.COMPLETED
        self.last_activity_at = datetime.now(timezone.utc)

    def abandon(self) -> None:
        """Mark session as abandoned."""
        self.status = SessionStatus.ABANDONED
        self.last_activity_at = datetime.now(timezone.utc)

    def expire(self) -> None:
        """Mark session as expired."""
        self.status = SessionStatus.EXPIRED


# =============================================================================
# Export
# =============================================================================

__all__ = [
    # Enums
    "CorrectionType",
    "SessionStatus",
    # Models
    "Correction",
    "Annotation",
    "AnnotationSession",
]
