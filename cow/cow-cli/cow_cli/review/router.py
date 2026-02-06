"""
COW CLI - HITL Review Router

Confidence-based routing logic for automated review decisions.
"""
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger("cow-cli.review.router")


class RoutingDecision(str, Enum):
    """Routing decision types."""
    AUTO_APPROVE = "auto_approve"
    MANUAL_REVIEW = "manual_review"
    REJECT = "reject"


@dataclass
class RoutingResult:
    """Result of a routing decision."""
    decision: RoutingDecision
    confidence: float
    threshold: float
    element_type: str
    priority: float
    reason: str

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "decision": self.decision.value,
            "confidence": self.confidence,
            "threshold": self.threshold,
            "element_type": self.element_type,
            "priority": self.priority,
            "reason": self.reason,
        }

    @property
    def needs_review(self) -> bool:
        """Check if manual review is needed."""
        return self.decision == RoutingDecision.MANUAL_REVIEW


class ReviewRouter:
    """
    Confidence-based routing for review decisions.

    Routes elements to:
    - AUTO_APPROVE: High confidence, no review needed
    - MANUAL_REVIEW: Medium confidence, requires human verification
    - REJECT: Low confidence, needs reprocessing
    """

    # Type-specific confidence thresholds
    DEFAULT_THRESHOLDS: Dict[str, float] = {
        # Math/equation types require high accuracy
        "math": 0.95,
        "equation": 0.95,
        "inline_math": 0.95,
        "display_math": 0.95,
        "formula": 0.95,
        # Text types have medium requirements
        "text": 0.90,
        "paragraph": 0.90,
        "heading": 0.90,
        "caption": 0.88,
        # Visual types have lower requirements
        "diagram": 0.85,
        "chart": 0.85,
        "graph": 0.85,
        "table": 0.88,
        "figure": 0.85,
        "image": 0.80,
        # Default for unknown types
        "default": 0.90,
    }

    # Type criticality scores (for priority calculation)
    TYPE_CRITICALITY: Dict[str, float] = {
        "math": 1.0,
        "equation": 1.0,
        "inline_math": 1.0,
        "display_math": 1.0,
        "formula": 1.0,
        "text": 0.7,
        "paragraph": 0.6,
        "heading": 0.8,
        "caption": 0.5,
        "diagram": 0.8,
        "chart": 0.8,
        "graph": 0.8,
        "table": 0.9,
        "figure": 0.6,
        "image": 0.4,
        "default": 0.5,
    }

    # Review band width (confidence range for manual review)
    REVIEW_BAND = 0.15

    def __init__(
        self,
        thresholds: Optional[Dict[str, float]] = None,
        review_band: float = 0.15,
    ):
        """
        Initialize router.

        Args:
            thresholds: Custom type thresholds (merged with defaults)
            review_band: Width of manual review confidence band
        """
        self.thresholds = {**self.DEFAULT_THRESHOLDS}
        if thresholds:
            self.thresholds.update(thresholds)
        self.review_band = review_band

    def get_threshold(self, element_type: str) -> float:
        """Get confidence threshold for an element type."""
        # Normalize type name
        normalized = element_type.lower().strip()

        # Check for exact match
        if normalized in self.thresholds:
            return self.thresholds[normalized]

        # Check for partial match
        for key, value in self.thresholds.items():
            if key in normalized or normalized in key:
                return value

        return self.thresholds["default"]

    def get_criticality(self, element_type: str) -> float:
        """Get criticality score for an element type."""
        normalized = element_type.lower().strip()
        return self.TYPE_CRITICALITY.get(
            normalized,
            self.TYPE_CRITICALITY["default"]
        )

    def route(
        self,
        element_type: str,
        confidence: float,
        is_blocking: bool = False,
        age_hours: float = 0.0,
    ) -> RoutingResult:
        """
        Route an element based on confidence.

        Args:
            element_type: Type of element (e.g., 'equation', 'diagram')
            confidence: OCR confidence score (0-1)
            is_blocking: Whether this element blocks others
            age_hours: Age in hours (for priority calculation)

        Returns:
            RoutingResult with decision and metadata
        """
        threshold = self.get_threshold(element_type)
        review_floor = threshold - self.review_band

        # Determine decision
        if confidence >= threshold:
            decision = RoutingDecision.AUTO_APPROVE
            reason = f"Confidence {confidence:.2%} >= threshold {threshold:.2%}"
        elif confidence >= review_floor:
            decision = RoutingDecision.MANUAL_REVIEW
            reason = f"Confidence {confidence:.2%} in review band [{review_floor:.2%}, {threshold:.2%})"
        else:
            decision = RoutingDecision.REJECT
            reason = f"Confidence {confidence:.2%} < review floor {review_floor:.2%}"

        # Calculate priority (higher = more urgent)
        priority = self._calculate_priority(
            confidence=confidence,
            threshold=threshold,
            element_type=element_type,
            is_blocking=is_blocking,
            age_hours=age_hours,
        )

        result = RoutingResult(
            decision=decision,
            confidence=confidence,
            threshold=threshold,
            element_type=element_type,
            priority=priority,
            reason=reason,
        )

        logger.debug(f"Routed {element_type}: {decision.value} (priority={priority:.1f})")
        return result

    def route_element(
        self,
        element: Dict[str, Any],
        confidence_key: str = "confidence",
        type_key: str = "type",
    ) -> RoutingResult:
        """
        Route an element dict.

        Args:
            element: Element dictionary
            confidence_key: Key for confidence value
            type_key: Key for element type

        Returns:
            RoutingResult
        """
        element_type = element.get(type_key, "default")
        confidence = element.get(confidence_key, 0.0)

        # Handle confidence_rate as alternate key
        if confidence == 0.0 and "confidence_rate" in element:
            confidence = element["confidence_rate"]

        return self.route(element_type, confidence)

    def _calculate_priority(
        self,
        confidence: float,
        threshold: float,
        element_type: str,
        is_blocking: bool = False,
        age_hours: float = 0.0,
    ) -> float:
        """
        Calculate review priority.

        Priority factors:
        - Confidence gap (how far below threshold)
        - Type criticality (important types = higher priority)
        - Blocking status (blocking elements = higher priority)
        - Age (older items = higher priority)
        """
        # Confidence gap (0-100 points)
        if confidence < threshold:
            confidence_gap = (threshold - confidence) * 100
        else:
            confidence_gap = 0.0

        # Type criticality (0-50 points)
        criticality = self.get_criticality(element_type) * 50

        # Blocking bonus (0 or 200 points)
        blocking_bonus = 200 if is_blocking else 0

        # Age factor (2 points per hour, max 100)
        age_factor = min(age_hours * 2, 100)

        priority = confidence_gap + criticality + blocking_bonus + age_factor

        return round(priority, 2)

    def batch_route(
        self,
        elements: list[Dict[str, Any]],
        confidence_key: str = "confidence",
        type_key: str = "type",
    ) -> list[RoutingResult]:
        """
        Route multiple elements.

        Args:
            elements: List of element dictionaries
            confidence_key: Key for confidence value
            type_key: Key for element type

        Returns:
            List of RoutingResult
        """
        return [
            self.route_element(elem, confidence_key, type_key)
            for elem in elements
        ]

    def get_stats(self, results: list[RoutingResult]) -> dict:
        """
        Get routing statistics.

        Args:
            results: List of routing results

        Returns:
            Statistics dictionary
        """
        total = len(results)
        if total == 0:
            return {
                "total": 0,
                "auto_approve": 0,
                "manual_review": 0,
                "reject": 0,
                "auto_approve_rate": 0.0,
                "manual_review_rate": 0.0,
                "reject_rate": 0.0,
            }

        auto_approve = sum(1 for r in results if r.decision == RoutingDecision.AUTO_APPROVE)
        manual_review = sum(1 for r in results if r.decision == RoutingDecision.MANUAL_REVIEW)
        reject = sum(1 for r in results if r.decision == RoutingDecision.REJECT)

        return {
            "total": total,
            "auto_approve": auto_approve,
            "manual_review": manual_review,
            "reject": reject,
            "auto_approve_rate": auto_approve / total,
            "manual_review_rate": manual_review / total,
            "reject_rate": reject / total,
        }


# Global router instance
_router: Optional[ReviewRouter] = None


def get_router() -> ReviewRouter:
    """Get global router instance."""
    global _router
    if _router is None:
        _router = ReviewRouter()
    return _router


def configure_router(
    thresholds: Optional[Dict[str, float]] = None,
    review_band: float = 0.15,
) -> ReviewRouter:
    """Configure global router."""
    global _router
    _router = ReviewRouter(thresholds=thresholds, review_band=review_band)
    return _router


def route(
    element_type: str,
    confidence: float,
    is_blocking: bool = False,
    age_hours: float = 0.0,
) -> RoutingResult:
    """Convenience function to route using global router."""
    return get_router().route(element_type, confidence, is_blocking, age_hours)


__all__ = [
    "RoutingDecision",
    "RoutingResult",
    "ReviewRouter",
    "get_router",
    "configure_router",
    "route",
]
