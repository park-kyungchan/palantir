"""
Tests for Review Router.
"""
import pytest
from datetime import datetime, timedelta, timezone

from cow_cli.review import (
    RoutingDecision,
    RoutingResult,
    ReviewRouter,
    get_router,
    configure_router,
    route,
)


class TestRoutingDecision:
    """Tests for RoutingDecision enum."""

    def test_decision_values(self):
        """Test decision enum values."""
        assert RoutingDecision.AUTO_APPROVE.value == "auto_approve"
        assert RoutingDecision.MANUAL_REVIEW.value == "manual_review"
        assert RoutingDecision.REJECT.value == "reject"


class TestRoutingResult:
    """Tests for RoutingResult dataclass."""

    def test_to_dict(self):
        """Test result serialization."""
        result = RoutingResult(
            decision=RoutingDecision.MANUAL_REVIEW,
            confidence=0.85,
            threshold=0.90,
            element_type="equation",
            priority=75.5,
            reason="Test reason",
        )

        d = result.to_dict()

        assert d["decision"] == "manual_review"
        assert d["confidence"] == 0.85
        assert d["threshold"] == 0.90
        assert d["element_type"] == "equation"
        assert d["priority"] == 75.5
        assert d["reason"] == "Test reason"

    def test_needs_review_true(self):
        """Test needs_review property when manual review needed."""
        result = RoutingResult(
            decision=RoutingDecision.MANUAL_REVIEW,
            confidence=0.85,
            threshold=0.90,
            element_type="text",
            priority=50.0,
            reason="Test",
        )
        assert result.needs_review is True

    def test_needs_review_false(self):
        """Test needs_review property for other decisions."""
        for decision in [RoutingDecision.AUTO_APPROVE, RoutingDecision.REJECT]:
            result = RoutingResult(
                decision=decision,
                confidence=0.85,
                threshold=0.90,
                element_type="text",
                priority=50.0,
                reason="Test",
            )
            assert result.needs_review is False


class TestReviewRouter:
    """Tests for ReviewRouter class."""

    @pytest.fixture
    def router(self):
        """Create test router."""
        return ReviewRouter()

    def test_default_thresholds(self, router):
        """Test default threshold values."""
        assert router.get_threshold("math") == 0.95
        assert router.get_threshold("equation") == 0.95
        assert router.get_threshold("text") == 0.90
        assert router.get_threshold("diagram") == 0.85
        assert router.get_threshold("unknown_type") == 0.90  # default

    def test_custom_thresholds(self):
        """Test custom threshold override."""
        router = ReviewRouter(thresholds={"math": 0.98, "custom": 0.75})

        assert router.get_threshold("math") == 0.98
        assert router.get_threshold("custom") == 0.75
        assert router.get_threshold("text") == 0.90  # unchanged

    def test_custom_review_band(self):
        """Test custom review band."""
        router = ReviewRouter(review_band=0.20)
        assert router.review_band == 0.20

    def test_route_auto_approve(self, router):
        """Test routing to auto approve."""
        # Math at 95% confidence (threshold 95%)
        result = router.route("math", 0.95)
        assert result.decision == RoutingDecision.AUTO_APPROVE

        # Math at 98% confidence
        result = router.route("math", 0.98)
        assert result.decision == RoutingDecision.AUTO_APPROVE

    def test_route_manual_review(self, router):
        """Test routing to manual review."""
        # Math at 85% confidence (threshold 95%, band 15%)
        result = router.route("math", 0.85)
        assert result.decision == RoutingDecision.MANUAL_REVIEW

        # Text at 82% confidence (threshold 90%, band 15%)
        result = router.route("text", 0.82)
        assert result.decision == RoutingDecision.MANUAL_REVIEW

    def test_route_reject(self, router):
        """Test routing to reject."""
        # Math at 70% confidence (below 80% floor)
        result = router.route("math", 0.70)
        assert result.decision == RoutingDecision.REJECT

        # Text at 60% confidence (below 75% floor)
        result = router.route("text", 0.60)
        assert result.decision == RoutingDecision.REJECT

    def test_route_boundary_cases(self, router):
        """Test boundary conditions."""
        # Exactly at threshold
        result = router.route("text", 0.90)
        assert result.decision == RoutingDecision.AUTO_APPROVE

        # Just below threshold
        result = router.route("text", 0.899)
        assert result.decision == RoutingDecision.MANUAL_REVIEW

        # Exactly at review floor
        result = router.route("text", 0.75)
        assert result.decision == RoutingDecision.MANUAL_REVIEW

        # Just below review floor
        result = router.route("text", 0.749)
        assert result.decision == RoutingDecision.REJECT

    def test_route_reason_messages(self, router):
        """Test reason messages are informative."""
        result = router.route("equation", 0.96)
        # Uses format like "95.00%" or "96.00%"
        assert "95" in result.reason
        assert "96" in result.reason

    def test_route_priority_calculation(self, router):
        """Test priority calculation."""
        # Higher confidence gap = higher priority
        result_low = router.route("text", 0.75)
        result_mid = router.route("text", 0.85)

        assert result_low.priority > result_mid.priority

    def test_route_blocking_priority(self, router):
        """Test blocking items get higher priority."""
        result_normal = router.route("text", 0.85, is_blocking=False)
        result_blocking = router.route("text", 0.85, is_blocking=True)

        assert result_blocking.priority > result_normal.priority
        assert result_blocking.priority - result_normal.priority >= 200

    def test_route_age_priority(self, router):
        """Test age increases priority."""
        result_new = router.route("text", 0.85, age_hours=0)
        result_old = router.route("text", 0.85, age_hours=24)

        assert result_old.priority > result_new.priority

    def test_route_element_dict(self, router):
        """Test routing from element dict."""
        element = {
            "type": "equation",
            "confidence": 0.88,
        }

        result = router.route_element(element)

        assert result.element_type == "equation"
        assert result.confidence == 0.88
        assert result.decision == RoutingDecision.MANUAL_REVIEW

    def test_route_element_confidence_rate(self, router):
        """Test using confidence_rate key."""
        element = {
            "type": "diagram",
            "confidence_rate": 0.90,
        }

        result = router.route_element(element)
        assert result.confidence == 0.90

    def test_batch_route(self, router):
        """Test batch routing."""
        elements = [
            {"type": "math", "confidence": 0.98},
            {"type": "text", "confidence": 0.85},
            {"type": "diagram", "confidence": 0.60},  # Below floor (0.85 - 0.15 = 0.70)
        ]

        results = router.batch_route(elements)

        assert len(results) == 3
        assert results[0].decision == RoutingDecision.AUTO_APPROVE
        assert results[1].decision == RoutingDecision.MANUAL_REVIEW
        assert results[2].decision == RoutingDecision.REJECT

    def test_get_stats_empty(self, router):
        """Test stats with no results."""
        stats = router.get_stats([])

        assert stats["total"] == 0
        assert stats["auto_approve_rate"] == 0.0

    def test_get_stats(self, router):
        """Test stats calculation."""
        elements = [
            {"type": "math", "confidence": 0.98},  # approve (>= 0.95)
            {"type": "math", "confidence": 0.95},  # approve (>= 0.95)
            {"type": "text", "confidence": 0.85},  # review (0.75 <= x < 0.90)
            {"type": "diagram", "confidence": 0.60},  # reject (< 0.70)
        ]

        results = router.batch_route(elements)
        stats = router.get_stats(results)

        assert stats["total"] == 4
        assert stats["auto_approve"] == 2
        assert stats["manual_review"] == 1
        assert stats["reject"] == 1
        assert stats["auto_approve_rate"] == 0.5
        assert stats["manual_review_rate"] == 0.25
        assert stats["reject_rate"] == 0.25

    def test_get_criticality(self, router):
        """Test type criticality scores."""
        assert router.get_criticality("math") == 1.0
        assert router.get_criticality("equation") == 1.0
        assert router.get_criticality("text") == 0.7
        assert router.get_criticality("diagram") == 0.8
        assert router.get_criticality("image") == 0.4
        assert router.get_criticality("unknown") == 0.5  # default

    def test_partial_type_matching(self, router):
        """Test partial type name matching."""
        # Should match 'math' for types containing 'math'
        assert router.get_threshold("math_expression") == 0.95
        assert router.get_threshold("inline_math") == 0.95


class TestGlobalRouter:
    """Tests for global router functions."""

    def test_get_router_singleton(self):
        """Test get_router returns singleton."""
        router1 = get_router()
        router2 = get_router()
        assert router1 is router2

    def test_configure_router(self):
        """Test configure_router creates new instance."""
        router = configure_router(
            thresholds={"custom": 0.80},
            review_band=0.20,
        )

        assert router.get_threshold("custom") == 0.80
        assert router.review_band == 0.20

    def test_route_convenience(self):
        """Test route convenience function."""
        configure_router()  # Reset to defaults
        result = route("equation", 0.90)

        assert result.element_type == "equation"
        assert result.decision == RoutingDecision.MANUAL_REVIEW


class TestTypeNormalization:
    """Tests for type name normalization."""

    @pytest.fixture
    def router(self):
        return ReviewRouter()

    def test_lowercase_normalization(self, router):
        """Test that type names are lowercased."""
        assert router.get_threshold("MATH") == router.get_threshold("math")
        assert router.get_threshold("TEXT") == router.get_threshold("text")

    def test_whitespace_normalization(self, router):
        """Test that whitespace is trimmed."""
        assert router.get_threshold("  math  ") == router.get_threshold("math")
        assert router.get_threshold("text\n") == router.get_threshold("text")
