"""
PriorityScorer for Human Review system.

Scores tasks to determine review priority based on:
- Confidence levels
- Element complexity
- Time constraints
- Business rules

Module Version: 2.0.0

v2.0.0 Changes:
- Added ThresholdConfig integration for dynamic priority thresholds
- Priority thresholds computed using 3-layer architecture (base → context → feedback)
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional

from .models.task import ReviewTask, ReviewPriority
from ..schemas.threshold import (
    ThresholdConfig,
    ThresholdContext,
    FeedbackStats,
    compute_effective_threshold,
)


logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================

@dataclass
class PriorityScorerConfig:
    """Configuration for PriorityScorer.

    v2.0.0: Added dynamic threshold support via ThresholdConfig.
    When threshold_config is provided, priority thresholds are computed
    dynamically based on element type and context.

    Attributes:
        threshold_config: Optional ThresholdConfig for dynamic thresholds.
            When provided, overrides static confidence thresholds.
        threshold_context: Optional context for threshold computation.
        feedback_stats: Optional feedback statistics for threshold adjustment.

        confidence_weight: Weight for confidence score (default: 0.35).
        complexity_weight: Weight for complexity score (default: 0.25).
        urgency_weight: Weight for urgency score (default: 0.20).
        business_weight: Weight for business rules score (default: 0.20).

        critical_confidence_threshold: Default threshold for CRITICAL priority.
            Elements below this have highest review urgency.
        high_confidence_threshold: Default threshold for HIGH priority.
        medium_confidence_threshold: Default threshold for MEDIUM priority.
    """
    # v2.0.0: Dynamic threshold configuration
    threshold_config: Optional[ThresholdConfig] = None
    threshold_context: Optional[ThresholdContext] = None
    feedback_stats: Optional[FeedbackStats] = None

    # Score weights (must sum to 1.0)
    confidence_weight: float = 0.35
    complexity_weight: float = 0.25
    urgency_weight: float = 0.20
    business_weight: float = 0.20

    # Confidence scoring (fallback when threshold_config is None)
    critical_confidence_threshold: float = 0.30
    high_confidence_threshold: float = 0.45
    medium_confidence_threshold: float = 0.55

    # Complexity factors
    complexity_element_types: Dict[str, float] = field(default_factory=lambda: {
        "equation": 0.8,
        "function": 0.8,
        "graph": 0.9,
        "geometry": 0.7,
        "label": 0.3,
        "annotation": 0.2,
    })

    # Urgency settings
    urgent_due_hours: int = 4
    high_due_hours: int = 12
    medium_due_hours: int = 24

    # Business rule multipliers
    escalation_multiplier: float = 1.5
    repeat_assignment_multiplier: float = 1.2

    def __post_init__(self):
        """Validate weights sum to 1.0."""
        total = (
            self.confidence_weight +
            self.complexity_weight +
            self.urgency_weight +
            self.business_weight
        )
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Weights must sum to 1.0, got {total}")

    def get_effective_threshold(
        self,
        element_type: str,
        priority_level: str = "medium",
    ) -> float:
        """Get effective threshold for a given element type and priority level.

        v2.0.0: When ThresholdConfig is provided, computes dynamic threshold.
        Otherwise falls back to static thresholds.

        Args:
            element_type: Type of element (e.g., "equation", "point", "label")
            priority_level: Priority level ("critical", "high", "medium")

        Returns:
            Effective confidence threshold for the priority level
        """
        if self.threshold_config and self.threshold_context:
            # Use dynamic threshold system
            feedback = self.feedback_stats or FeedbackStats()
            base_threshold = compute_effective_threshold(
                element_type=element_type,
                context=self.threshold_context,
                feedback_stats=feedback,
                config=self.threshold_config,
            )
            # Apply priority level scaling
            # Critical: 50% of base, High: 75% of base, Medium: 100% of base
            scaling = {
                "critical": 0.50,
                "high": 0.75,
                "medium": 1.0,
            }
            return base_threshold * scaling.get(priority_level, 1.0)

        # Fallback to static thresholds
        static_map = {
            "critical": self.critical_confidence_threshold,
            "high": self.high_confidence_threshold,
            "medium": self.medium_confidence_threshold,
        }
        return static_map.get(priority_level, self.medium_confidence_threshold)


# =============================================================================
# PriorityScorer
# =============================================================================

class PriorityScorer:
    """Scores tasks to determine review priority.

    Combines multiple factors to produce a priority score:
    - Confidence gap (how far below threshold)
    - Element complexity (some types harder to verify)
    - Time urgency (due dates, queue age)
    - Business rules (escalations, repeat assignments)

    The scorer outputs a ReviewPriority enum value suitable
    for queue ordering.

    Usage:
        scorer = PriorityScorer(config)
        priority = scorer.score(task)
        task.priority = priority
    """

    def __init__(self, config: Optional[PriorityScorerConfig] = None):
        """Initialize scorer.

        Args:
            config: Scorer configuration
        """
        self.config = config or PriorityScorerConfig()

    def score(self, task: ReviewTask) -> ReviewPriority:
        """Score a task and return priority.

        Args:
            task: ReviewTask to score

        Returns:
            ReviewPriority
        """
        # Calculate component scores (0-1 scale, higher = more urgent)
        confidence_score = self._score_confidence(task)
        complexity_score = self._score_complexity(task)
        urgency_score = self._score_urgency(task)
        business_score = self._score_business(task)

        # Weighted sum
        total_score = (
            confidence_score * self.config.confidence_weight +
            complexity_score * self.config.complexity_weight +
            urgency_score * self.config.urgency_weight +
            business_score * self.config.business_weight
        )

        # Map to priority
        priority = self._map_score_to_priority(total_score)

        logger.debug(
            f"Task {task.task_id} scored: "
            f"confidence={confidence_score:.2f}, "
            f"complexity={complexity_score:.2f}, "
            f"urgency={urgency_score:.2f}, "
            f"business={business_score:.2f}, "
            f"total={total_score:.2f} -> {priority.value}"
        )

        return priority

    def _score_confidence(self, task: ReviewTask) -> float:
        """Score based on confidence level.

        Lower confidence = higher score (more urgent).

        v2.0.0: When ThresholdConfig is provided, uses dynamic thresholds
        computed based on element type and context.
        """
        confidence = task.context.original_confidence
        element_type = task.context.element_type.lower()

        # Get thresholds (dynamic if configured, static otherwise)
        critical_threshold = self.config.get_effective_threshold(
            element_type, "critical"
        )
        high_threshold = self.config.get_effective_threshold(
            element_type, "high"
        )
        medium_threshold = self.config.get_effective_threshold(
            element_type, "medium"
        )

        if confidence <= critical_threshold:
            return 1.0
        elif confidence <= high_threshold:
            # Linear interpolation between critical and high
            range_size = high_threshold - critical_threshold
            if range_size <= 0:
                return 0.9
            position = confidence - critical_threshold
            return 1.0 - (position / range_size) * 0.25
        elif confidence <= medium_threshold:
            # Linear interpolation between high and medium
            range_size = medium_threshold - high_threshold
            if range_size <= 0:
                return 0.65
            position = confidence - high_threshold
            return 0.75 - (position / range_size) * 0.25
        else:
            # Above medium threshold
            return 0.5 * (1.0 - confidence)

    def _score_complexity(self, task: ReviewTask) -> float:
        """Score based on element complexity.

        More complex elements = higher score.
        """
        element_type = task.context.element_type.lower()

        # Get base complexity from config
        base_complexity = self.config.complexity_element_types.get(
            element_type, 0.5
        )

        # Adjust based on related elements
        related_count = len(task.context.related_elements)
        if related_count > 0:
            # More related elements = more complex
            related_factor = min(1.0, 0.5 + (related_count * 0.1))
            base_complexity = base_complexity * related_factor

        return min(1.0, base_complexity)

    def _score_urgency(self, task: ReviewTask) -> float:
        """Score based on time urgency.

        Closer to due date = higher score.
        """
        now = datetime.now(timezone.utc)

        if task.due_at is None:
            # No due date, check queue age instead
            age_hours = (now - task.created_at).total_seconds() / 3600
            if age_hours > self.config.medium_due_hours:
                return 0.7
            elif age_hours > self.config.high_due_hours:
                return 0.5
            else:
                return 0.3

        # Has due date
        time_left = (task.due_at - now).total_seconds() / 3600

        if time_left <= 0:
            # Overdue
            return 1.0
        elif time_left <= self.config.urgent_due_hours:
            return 0.9
        elif time_left <= self.config.high_due_hours:
            # Linear interpolation
            progress = (self.config.high_due_hours - time_left) / (
                self.config.high_due_hours - self.config.urgent_due_hours
            )
            return 0.7 + (progress * 0.2)
        elif time_left <= self.config.medium_due_hours:
            return 0.5
        else:
            return 0.3

    def _score_business(self, task: ReviewTask) -> float:
        """Score based on business rules.

        Escalations, repeat assignments, etc.
        """
        score = 0.0

        # Escalation check
        if task.metrics.escalation_count > 0:
            score += 0.4 * self.config.escalation_multiplier

        # Repeat assignment check
        if task.metrics.assignment_count > 1:
            score += 0.2 * (
                task.metrics.assignment_count *
                self.config.repeat_assignment_multiplier
            )

        # Severity from context
        if task.severity.value == "blocker":
            score += 0.4
        elif task.severity.value == "high":
            score += 0.2

        return min(1.0, score)

    def _map_score_to_priority(self, score: float) -> ReviewPriority:
        """Map numeric score to priority enum.

        Args:
            score: Score from 0-1

        Returns:
            ReviewPriority
        """
        if score >= 0.8:
            return ReviewPriority.CRITICAL
        elif score >= 0.6:
            return ReviewPriority.HIGH
        elif score >= 0.4:
            return ReviewPriority.MEDIUM
        else:
            return ReviewPriority.LOW

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def explain_score(self, task: ReviewTask) -> Dict[str, Any]:
        """Get detailed explanation of scoring.

        v2.0.0: Includes dynamic threshold information when configured.

        Args:
            task: Task to explain

        Returns:
            Dict with score breakdown
        """
        confidence_score = self._score_confidence(task)
        complexity_score = self._score_complexity(task)
        urgency_score = self._score_urgency(task)
        business_score = self._score_business(task)

        total_score = (
            confidence_score * self.config.confidence_weight +
            complexity_score * self.config.complexity_weight +
            urgency_score * self.config.urgency_weight +
            business_score * self.config.business_weight
        )

        element_type = task.context.element_type.lower()

        # Get applied thresholds for explanation
        thresholds = {
            "critical": self.config.get_effective_threshold(element_type, "critical"),
            "high": self.config.get_effective_threshold(element_type, "high"),
            "medium": self.config.get_effective_threshold(element_type, "medium"),
        }

        return {
            "task_id": task.task_id,
            "scores": {
                "confidence": {
                    "raw": confidence_score,
                    "weight": self.config.confidence_weight,
                    "weighted": confidence_score * self.config.confidence_weight,
                },
                "complexity": {
                    "raw": complexity_score,
                    "weight": self.config.complexity_weight,
                    "weighted": complexity_score * self.config.complexity_weight,
                },
                "urgency": {
                    "raw": urgency_score,
                    "weight": self.config.urgency_weight,
                    "weighted": urgency_score * self.config.urgency_weight,
                },
                "business": {
                    "raw": business_score,
                    "weight": self.config.business_weight,
                    "weighted": business_score * self.config.business_weight,
                },
            },
            "total_score": total_score,
            "priority": self._map_score_to_priority(total_score).value,
            "factors": {
                "original_confidence": task.context.original_confidence,
                "threshold_delta": task.context.threshold_delta,
                "element_type": task.context.element_type,
                "related_elements": len(task.context.related_elements),
                "escalation_count": task.metrics.escalation_count,
                "assignment_count": task.metrics.assignment_count,
            },
            "thresholds_applied": {
                "dynamic_enabled": self.config.threshold_config is not None,
                "critical": thresholds["critical"],
                "high": thresholds["high"],
                "medium": thresholds["medium"],
            },
        }

    def recalculate_priority(self, task: ReviewTask) -> bool:
        """Recalculate and update task priority.

        Args:
            task: Task to update

        Returns:
            True if priority changed
        """
        old_priority = task.priority
        new_priority = self.score(task)

        if new_priority != old_priority:
            task.priority = new_priority
            return True
        return False


# =============================================================================
# Factory Function
# =============================================================================

def create_priority_scorer(
    config: Optional[PriorityScorerConfig] = None,
) -> PriorityScorer:
    """Create a PriorityScorer instance.

    Args:
        config: Optional configuration

    Returns:
        PriorityScorer instance
    """
    return PriorityScorer(config)


# =============================================================================
# Export
# =============================================================================

__all__ = [
    "PriorityScorerConfig",
    "PriorityScorer",
    "create_priority_scorer",
]
