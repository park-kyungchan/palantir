"""
COW CLI - Priority Scorer

Calculates review priority scores for HITL queue management.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
from datetime import datetime, timezone
from enum import Enum
import logging

logger = logging.getLogger("cow-cli.review.priority")


class UrgencyLevel(str, Enum):
    """Urgency level classifications."""
    CRITICAL = "critical"  # Priority >= 300
    HIGH = "high"          # Priority >= 200
    MEDIUM = "medium"      # Priority >= 100
    LOW = "low"            # Priority < 100


@dataclass
class PriorityScore:
    """Detailed priority score breakdown."""
    total: float
    confidence_gap_score: float = 0.0
    criticality_score: float = 0.0
    blocking_score: float = 0.0
    age_score: float = 0.0
    urgency: UrgencyLevel = UrgencyLevel.LOW
    factors: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "total": self.total,
            "confidence_gap_score": self.confidence_gap_score,
            "criticality_score": self.criticality_score,
            "blocking_score": self.blocking_score,
            "age_score": self.age_score,
            "urgency": self.urgency.value,
            "factors": self.factors,
        }


class PriorityScorer:
    """
    Calculates priority scores for review queue ordering.

    Priority components:
    - Confidence gap: How far below threshold
    - Type criticality: Importance of element type
    - Blocking status: Whether item blocks others
    - Age: How long in queue
    - Custom factors: Additional scoring factors
    """

    # Default weights for priority components
    DEFAULT_WEIGHTS = {
        "confidence_gap": 100.0,   # Max points from confidence gap
        "criticality": 50.0,       # Max points from type criticality
        "blocking": 200.0,         # Bonus for blocking items
        "age_per_hour": 2.0,       # Points per hour in queue
        "age_max": 100.0,          # Maximum age bonus
    }

    # Type criticality scores
    DEFAULT_CRITICALITY = {
        "math": 1.0,
        "equation": 1.0,
        "formula": 1.0,
        "text": 0.7,
        "paragraph": 0.6,
        "heading": 0.8,
        "table": 0.9,
        "diagram": 0.8,
        "chart": 0.8,
        "figure": 0.6,
        "image": 0.4,
        "default": 0.5,
    }

    # Urgency thresholds
    URGENCY_THRESHOLDS = {
        UrgencyLevel.CRITICAL: 300,
        UrgencyLevel.HIGH: 200,
        UrgencyLevel.MEDIUM: 100,
        UrgencyLevel.LOW: 0,
    }

    def __init__(
        self,
        weights: Optional[Dict[str, float]] = None,
        criticality: Optional[Dict[str, float]] = None,
    ):
        """
        Initialize scorer.

        Args:
            weights: Custom weight configuration
            criticality: Custom type criticality scores
        """
        self.weights = {**self.DEFAULT_WEIGHTS}
        if weights:
            self.weights.update(weights)

        self.criticality = {**self.DEFAULT_CRITICALITY}
        if criticality:
            self.criticality.update(criticality)

    def get_criticality(self, element_type: str) -> float:
        """Get criticality score for an element type."""
        normalized = element_type.lower().strip()
        return self.criticality.get(normalized, self.criticality["default"])

    def calculate(
        self,
        confidence: float,
        threshold: float,
        element_type: str,
        is_blocking: bool = False,
        created_at: Optional[datetime] = None,
        custom_factors: Optional[Dict[str, float]] = None,
    ) -> PriorityScore:
        """
        Calculate priority score.

        Args:
            confidence: OCR confidence (0-1)
            threshold: Acceptance threshold (0-1)
            element_type: Type of element
            is_blocking: Whether element blocks others
            created_at: When item was created (for age calculation)
            custom_factors: Additional scoring factors {name: score}

        Returns:
            PriorityScore with detailed breakdown
        """
        # Confidence gap score
        if confidence < threshold:
            gap_ratio = (threshold - confidence) / threshold
            confidence_gap_score = gap_ratio * self.weights["confidence_gap"]
        else:
            confidence_gap_score = 0.0

        # Type criticality score
        crit = self.get_criticality(element_type)
        criticality_score = crit * self.weights["criticality"]

        # Blocking bonus
        blocking_score = self.weights["blocking"] if is_blocking else 0.0

        # Age score
        age_score = 0.0
        if created_at:
            # Handle timezone-naive datetimes
            now = datetime.now(timezone.utc)
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            age_hours = (now - created_at).total_seconds() / 3600
            age_score = min(
                age_hours * self.weights["age_per_hour"],
                self.weights["age_max"]
            )

        # Custom factors
        custom_score = 0.0
        factors = {}
        if custom_factors:
            for name, score in custom_factors.items():
                factors[name] = score
                custom_score += score

        # Total
        total = (
            confidence_gap_score +
            criticality_score +
            blocking_score +
            age_score +
            custom_score
        )

        # Determine urgency level
        urgency = self._get_urgency(total)

        return PriorityScore(
            total=round(total, 2),
            confidence_gap_score=round(confidence_gap_score, 2),
            criticality_score=round(criticality_score, 2),
            blocking_score=round(blocking_score, 2),
            age_score=round(age_score, 2),
            urgency=urgency,
            factors=factors,
        )

    def calculate_from_item(
        self,
        item: Dict[str, Any],
        threshold: Optional[float] = None,
    ) -> PriorityScore:
        """
        Calculate priority from a review item dict.

        Args:
            item: Review item dictionary
            threshold: Optional threshold override

        Returns:
            PriorityScore
        """
        confidence = item.get("confidence") or item.get("confidence_rate") or 0.0
        element_type = item.get("element_type") or item.get("type") or "default"
        is_blocking = item.get("is_blocking", False)
        created_at = item.get("created_at")

        # Parse created_at if string
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at)
            except ValueError:
                created_at = None

        # Use provided threshold or estimate from type
        if threshold is None:
            threshold = self._estimate_threshold(element_type)

        return self.calculate(
            confidence=confidence,
            threshold=threshold,
            element_type=element_type,
            is_blocking=is_blocking,
            created_at=created_at,
        )

    def batch_calculate(
        self,
        items: List[Dict[str, Any]],
        threshold: Optional[float] = None,
    ) -> List[PriorityScore]:
        """
        Calculate priorities for multiple items.

        Args:
            items: List of review items
            threshold: Optional threshold override

        Returns:
            List of PriorityScore
        """
        return [self.calculate_from_item(item, threshold) for item in items]

    def sort_by_priority(
        self,
        items: List[Dict[str, Any]],
        threshold: Optional[float] = None,
        descending: bool = True,
    ) -> List[tuple[Dict[str, Any], PriorityScore]]:
        """
        Sort items by priority.

        Args:
            items: List of review items
            threshold: Optional threshold override
            descending: Sort highest priority first

        Returns:
            List of (item, score) tuples sorted by priority
        """
        scored = [(item, self.calculate_from_item(item, threshold)) for item in items]
        return sorted(scored, key=lambda x: x[1].total, reverse=descending)

    def _get_urgency(self, total: float) -> UrgencyLevel:
        """Determine urgency level from total score."""
        if total >= self.URGENCY_THRESHOLDS[UrgencyLevel.CRITICAL]:
            return UrgencyLevel.CRITICAL
        elif total >= self.URGENCY_THRESHOLDS[UrgencyLevel.HIGH]:
            return UrgencyLevel.HIGH
        elif total >= self.URGENCY_THRESHOLDS[UrgencyLevel.MEDIUM]:
            return UrgencyLevel.MEDIUM
        return UrgencyLevel.LOW

    def _estimate_threshold(self, element_type: str) -> float:
        """Estimate threshold for a type (for priority calculation)."""
        # Type-specific thresholds
        thresholds = {
            "math": 0.95,
            "equation": 0.95,
            "formula": 0.95,
            "text": 0.90,
            "paragraph": 0.90,
            "heading": 0.90,
            "table": 0.88,
            "diagram": 0.85,
            "chart": 0.85,
            "figure": 0.85,
            "image": 0.80,
        }
        normalized = element_type.lower().strip()
        return thresholds.get(normalized, 0.90)

    def get_urgency_distribution(
        self,
        scores: List[PriorityScore],
    ) -> Dict[str, int]:
        """Get distribution of urgency levels."""
        distribution = {level.value: 0 for level in UrgencyLevel}
        for score in scores:
            distribution[score.urgency.value] += 1
        return distribution


# Global scorer instance
_scorer: Optional[PriorityScorer] = None


def get_scorer() -> PriorityScorer:
    """Get global scorer instance."""
    global _scorer
    if _scorer is None:
        _scorer = PriorityScorer()
    return _scorer


def configure_scorer(
    weights: Optional[Dict[str, float]] = None,
    criticality: Optional[Dict[str, float]] = None,
) -> PriorityScorer:
    """Configure global scorer."""
    global _scorer
    _scorer = PriorityScorer(weights=weights, criticality=criticality)
    return _scorer


def calculate_priority(
    confidence: float,
    threshold: float,
    element_type: str,
    is_blocking: bool = False,
    created_at: Optional[datetime] = None,
) -> PriorityScore:
    """Convenience function to calculate priority."""
    return get_scorer().calculate(
        confidence=confidence,
        threshold=threshold,
        element_type=element_type,
        is_blocking=is_blocking,
        created_at=created_at,
    )


__all__ = [
    "UrgencyLevel",
    "PriorityScore",
    "PriorityScorer",
    "get_scorer",
    "configure_scorer",
    "calculate_priority",
]
