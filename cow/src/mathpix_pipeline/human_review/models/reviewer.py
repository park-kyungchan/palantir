"""
Reviewer model for Human Review system.

Represents reviewers and their capabilities:
- Reviewer: Reviewer profile and credentials
- ReviewerCapability: What a reviewer can review
- ReviewerStats: Performance statistics

Module Version: 1.0.0
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Set

from pydantic import Field, model_validator

from ...schemas.common import MathpixBaseModel, PipelineStage, utc_now


# =============================================================================
# Enums
# =============================================================================

class ReviewerRole(str, Enum):
    """Roles for reviewers."""
    JUNIOR = "junior"
    STANDARD = "standard"
    SENIOR = "senior"
    EXPERT = "expert"
    ADMIN = "admin"


class ReviewerStatus(str, Enum):
    """Status of a reviewer."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    ON_BREAK = "on_break"


# =============================================================================
# Reviewer Capability
# =============================================================================

class ReviewerCapability(MathpixBaseModel):
    """Capabilities and specializations of a reviewer.

    Defines what types of elements and stages
    a reviewer is qualified to review.
    """
    # Stage qualifications
    qualified_stages: List[PipelineStage] = Field(
        default_factory=list,
        description="Pipeline stages reviewer can review"
    )

    # Element type qualifications
    element_types: List[str] = Field(
        default_factory=list,
        description="Element types reviewer can review"
    )

    # Specializations
    specializations: List[str] = Field(
        default_factory=list,
        description="Special areas of expertise (e.g., 'geometry', 'calculus')"
    )

    # Languages
    languages: List[str] = Field(
        default_factory=lambda: ["en"],
        description="Languages reviewer can handle"
    )

    # Complexity limits
    max_complexity: str = Field(
        default="high",
        description="Maximum complexity level (low, medium, high, critical)"
    )

    # Throughput limits
    max_concurrent_tasks: int = Field(
        default=5,
        description="Maximum simultaneous tasks"
    )
    max_daily_tasks: int = Field(
        default=50,
        description="Maximum tasks per day"
    )

    def can_review_stage(self, stage: PipelineStage) -> bool:
        """Check if reviewer can review a stage."""
        return stage in self.qualified_stages

    def can_review_element(self, element_type: str) -> bool:
        """Check if reviewer can review an element type."""
        return element_type in self.element_types or not self.element_types


# =============================================================================
# Reviewer Stats
# =============================================================================

class ReviewerStats(MathpixBaseModel):
    """Performance statistics for a reviewer."""
    # Task counts
    total_tasks_completed: int = Field(default=0)
    tasks_today: int = Field(default=0)
    tasks_this_week: int = Field(default=0)
    tasks_this_month: int = Field(default=0)

    # Quality metrics
    accuracy_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    agreement_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    escalation_rate: float = Field(default=0.0, ge=0.0, le=1.0)

    # Time metrics (in milliseconds)
    avg_review_time_ms: float = Field(default=0.0)
    median_review_time_ms: float = Field(default=0.0)
    total_review_time_ms: float = Field(default=0.0)

    # Decision distribution
    approve_count: int = Field(default=0)
    reject_count: int = Field(default=0)
    modify_count: int = Field(default=0)
    escalate_count: int = Field(default=0)

    # Quality flags
    flagged_reviews: int = Field(default=0)
    overturned_decisions: int = Field(default=0)

    # Last activity
    last_task_at: Optional[datetime] = Field(default=None)
    last_stats_update: datetime = Field(default_factory=utc_now)

    def record_task(
        self,
        decision: str,
        review_time_ms: float,
    ) -> None:
        """Record a completed task."""
        self.total_tasks_completed += 1
        self.tasks_today += 1
        self.tasks_this_week += 1
        self.tasks_this_month += 1

        # Update decision counts
        if decision == "approve":
            self.approve_count += 1
        elif decision == "reject":
            self.reject_count += 1
        elif decision == "modify":
            self.modify_count += 1
        elif decision == "escalate":
            self.escalate_count += 1

        # Update time metrics
        self.total_review_time_ms += review_time_ms
        if self.total_tasks_completed > 0:
            self.avg_review_time_ms = self.total_review_time_ms / self.total_tasks_completed

        self.last_task_at = datetime.now(timezone.utc)
        self.last_stats_update = datetime.now(timezone.utc)

    def reset_daily_counts(self) -> None:
        """Reset daily task count."""
        self.tasks_today = 0
        self.last_stats_update = datetime.now(timezone.utc)

    def reset_weekly_counts(self) -> None:
        """Reset weekly task count."""
        self.tasks_this_week = 0
        self.last_stats_update = datetime.now(timezone.utc)

    def reset_monthly_counts(self) -> None:
        """Reset monthly task count."""
        self.tasks_this_month = 0
        self.last_stats_update = datetime.now(timezone.utc)


# =============================================================================
# Reviewer
# =============================================================================

class Reviewer(MathpixBaseModel):
    """A human reviewer in the system.

    Represents a person who reviews tasks with their
    capabilities, status, and performance metrics.
    """
    # Identity
    reviewer_id: str = Field(..., description="Unique reviewer identifier")
    name: str = Field(..., description="Display name")
    email: Optional[str] = Field(default=None, description="Email address")

    # Role and status
    role: ReviewerRole = Field(default=ReviewerRole.STANDARD)
    status: ReviewerStatus = Field(default=ReviewerStatus.ACTIVE)

    # Capabilities
    capabilities: ReviewerCapability = Field(
        default_factory=ReviewerCapability
    )

    # Statistics
    stats: ReviewerStats = Field(default_factory=ReviewerStats)

    # Current workload
    current_task_ids: List[str] = Field(
        default_factory=list,
        description="Currently assigned task IDs"
    )

    # Preferences
    preferred_queues: List[str] = Field(
        default_factory=list,
        description="Preferred queue names"
    )
    auto_assign: bool = Field(
        default=True,
        description="Allow automatic task assignment"
    )

    # Timestamps
    created_at: datetime = Field(default_factory=utc_now)
    last_active_at: datetime = Field(default_factory=utc_now)

    @property
    def is_available(self) -> bool:
        """Check if reviewer is available for new tasks."""
        if self.status != ReviewerStatus.ACTIVE:
            return False
        if len(self.current_task_ids) >= self.capabilities.max_concurrent_tasks:
            return False
        if self.stats.tasks_today >= self.capabilities.max_daily_tasks:
            return False
        return True

    @property
    def current_workload(self) -> int:
        """Get current number of assigned tasks."""
        return len(self.current_task_ids)

    @property
    def workload_percentage(self) -> float:
        """Get workload as percentage of capacity."""
        if self.capabilities.max_concurrent_tasks == 0:
            return 100.0
        return (
            len(self.current_task_ids) /
            self.capabilities.max_concurrent_tasks * 100
        )

    def assign_task(self, task_id: str) -> bool:
        """Assign a task to this reviewer."""
        if not self.is_available:
            return False
        if task_id in self.current_task_ids:
            return False
        self.current_task_ids.append(task_id)
        self.last_active_at = datetime.now(timezone.utc)
        return True

    def unassign_task(self, task_id: str) -> bool:
        """Remove a task from this reviewer."""
        if task_id not in self.current_task_ids:
            return False
        self.current_task_ids.remove(task_id)
        return True

    def complete_task(
        self,
        task_id: str,
        decision: str,
        review_time_ms: float,
    ) -> None:
        """Record task completion."""
        self.unassign_task(task_id)
        self.stats.record_task(decision, review_time_ms)
        self.last_active_at = datetime.now(timezone.utc)

    def can_review(
        self,
        stage: PipelineStage,
        element_type: Optional[str] = None,
    ) -> bool:
        """Check if reviewer can review a specific item."""
        if not self.is_available:
            return False
        if not self.capabilities.can_review_stage(stage):
            return False
        if element_type and not self.capabilities.can_review_element(element_type):
            return False
        return True


# =============================================================================
# Export
# =============================================================================

__all__ = [
    # Enums
    "ReviewerRole",
    "ReviewerStatus",
    # Models
    "ReviewerCapability",
    "ReviewerStats",
    "Reviewer",
]
