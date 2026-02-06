"""
Tests for Priority Scorer.
"""
import pytest
from datetime import datetime, timedelta, timezone

from cow_cli.review import (
    UrgencyLevel,
    PriorityScore,
    PriorityScorer,
    get_scorer,
    configure_scorer,
    calculate_priority,
)


class TestUrgencyLevel:
    """Tests for UrgencyLevel enum."""

    def test_urgency_values(self):
        """Test urgency level values."""
        assert UrgencyLevel.CRITICAL.value == "critical"
        assert UrgencyLevel.HIGH.value == "high"
        assert UrgencyLevel.MEDIUM.value == "medium"
        assert UrgencyLevel.LOW.value == "low"


class TestPriorityScore:
    """Tests for PriorityScore dataclass."""

    def test_to_dict(self):
        """Test score serialization."""
        score = PriorityScore(
            total=150.5,
            confidence_gap_score=50.0,
            criticality_score=25.0,
            blocking_score=0.0,
            age_score=75.5,
            urgency=UrgencyLevel.MEDIUM,
            factors={"custom": 10.0},
        )

        d = score.to_dict()

        assert d["total"] == 150.5
        assert d["confidence_gap_score"] == 50.0
        assert d["criticality_score"] == 25.0
        assert d["blocking_score"] == 0.0
        assert d["age_score"] == 75.5
        assert d["urgency"] == "medium"
        assert d["factors"]["custom"] == 10.0


class TestPriorityScorer:
    """Tests for PriorityScorer class."""

    @pytest.fixture
    def scorer(self):
        """Create test scorer."""
        return PriorityScorer()

    def test_default_weights(self, scorer):
        """Test default weight values."""
        assert scorer.weights["confidence_gap"] == 100.0
        assert scorer.weights["criticality"] == 50.0
        assert scorer.weights["blocking"] == 200.0
        assert scorer.weights["age_per_hour"] == 2.0
        assert scorer.weights["age_max"] == 100.0

    def test_custom_weights(self):
        """Test custom weight configuration."""
        scorer = PriorityScorer(weights={"confidence_gap": 200.0})
        assert scorer.weights["confidence_gap"] == 200.0
        assert scorer.weights["criticality"] == 50.0  # unchanged

    def test_get_criticality(self, scorer):
        """Test criticality scores."""
        assert scorer.get_criticality("math") == 1.0
        assert scorer.get_criticality("equation") == 1.0
        assert scorer.get_criticality("text") == 0.7
        assert scorer.get_criticality("table") == 0.9
        assert scorer.get_criticality("diagram") == 0.8
        assert scorer.get_criticality("image") == 0.4
        assert scorer.get_criticality("unknown") == 0.5  # default

    def test_calculate_confidence_gap(self, scorer):
        """Test confidence gap scoring."""
        # No gap (at threshold)
        score = scorer.calculate(
            confidence=0.90,
            threshold=0.90,
            element_type="text",
        )
        assert score.confidence_gap_score == 0.0

        # Above threshold
        score = scorer.calculate(
            confidence=0.95,
            threshold=0.90,
            element_type="text",
        )
        assert score.confidence_gap_score == 0.0

        # Below threshold (gap = 0.10/0.90 = ~11.1%)
        score = scorer.calculate(
            confidence=0.80,
            threshold=0.90,
            element_type="text",
        )
        assert score.confidence_gap_score > 0

    def test_calculate_criticality(self, scorer):
        """Test criticality scoring."""
        # High criticality type (math = 1.0)
        score_math = scorer.calculate(
            confidence=0.85,
            threshold=0.95,
            element_type="math",
        )

        # Low criticality type (image = 0.4)
        score_image = scorer.calculate(
            confidence=0.85,
            threshold=0.95,
            element_type="image",
        )

        assert score_math.criticality_score > score_image.criticality_score
        assert score_math.criticality_score == 50.0  # 1.0 * 50
        assert score_image.criticality_score == 20.0  # 0.4 * 50

    def test_calculate_blocking(self, scorer):
        """Test blocking bonus."""
        score_normal = scorer.calculate(
            confidence=0.85,
            threshold=0.90,
            element_type="text",
            is_blocking=False,
        )

        score_blocking = scorer.calculate(
            confidence=0.85,
            threshold=0.90,
            element_type="text",
            is_blocking=True,
        )

        assert score_normal.blocking_score == 0.0
        assert score_blocking.blocking_score == 200.0

    def test_calculate_age(self, scorer):
        """Test age scoring."""
        now = datetime.now(timezone.utc)

        # New item (0 hours)
        score_new = scorer.calculate(
            confidence=0.85,
            threshold=0.90,
            element_type="text",
            created_at=now,
        )

        # Old item (24 hours)
        old_time = now - timedelta(hours=24)
        score_old = scorer.calculate(
            confidence=0.85,
            threshold=0.90,
            element_type="text",
            created_at=old_time,
        )

        assert score_new.age_score < score_old.age_score
        assert score_old.age_score == pytest.approx(48.0, abs=1.0)  # 24 * 2

    def test_calculate_age_max(self, scorer):
        """Test age score maximum."""
        old_time = datetime.now(timezone.utc) - timedelta(hours=100)
        score = scorer.calculate(
            confidence=0.85,
            threshold=0.90,
            element_type="text",
            created_at=old_time,
        )
        assert score.age_score <= 100.0  # max

    def test_calculate_custom_factors(self, scorer):
        """Test custom factor scoring."""
        score = scorer.calculate(
            confidence=0.85,
            threshold=0.90,
            element_type="text",
            custom_factors={"bonus1": 10.0, "bonus2": 20.0},
        )

        assert "bonus1" in score.factors
        assert "bonus2" in score.factors
        assert score.factors["bonus1"] == 10.0
        assert score.factors["bonus2"] == 20.0

    def test_urgency_levels(self, scorer):
        """Test urgency level assignment."""
        # Low (< 100): High confidence, low criticality
        score_low = scorer.calculate(
            confidence=0.90,
            threshold=0.90,
            element_type="image",  # low criticality = 0.4 * 50 = 20
        )
        assert score_low.total < 100
        assert score_low.urgency == UrgencyLevel.LOW

        # Medium (>= 100): Confidence gap + criticality
        # gap = (0.90 - 0.70) / 0.90 * 100 = 22.2, criticality = 1.0 * 50 = 50
        # Total ~72, need more gap
        score_med = scorer.calculate(
            confidence=0.50,
            threshold=0.90,
            element_type="math",  # gap = 0.44 * 100 = 44.4, crit = 50, total ~94
        )
        # This might still be < 100, let's use an even lower confidence
        score_med = scorer.calculate(
            confidence=0.40,
            threshold=0.90,
            element_type="math",  # gap = 0.55 * 100 = 55.5, crit = 50, total ~105
        )
        assert score_med.total >= 100
        assert score_med.urgency == UrgencyLevel.MEDIUM

        # High (>= 200) - blocking adds 200
        score_high = scorer.calculate(
            confidence=0.85,
            threshold=0.90,
            element_type="math",
            is_blocking=True,
        )
        assert score_high.total >= 200
        assert score_high.urgency == UrgencyLevel.HIGH

        # Critical (>= 300) - blocking + age + gap
        old_time = datetime.now(timezone.utc) - timedelta(hours=50)
        score_crit = scorer.calculate(
            confidence=0.70,
            threshold=0.90,
            element_type="math",
            is_blocking=True,
            created_at=old_time,
        )
        assert score_crit.total >= 300
        assert score_crit.urgency == UrgencyLevel.CRITICAL

    def test_calculate_from_item(self, scorer):
        """Test calculation from item dict."""
        item = {
            "element_type": "equation",
            "confidence": 0.85,
            "is_blocking": False,
        }

        score = scorer.calculate_from_item(item, threshold=0.95)

        assert score.total > 0
        assert score.confidence_gap_score > 0

    def test_calculate_from_item_confidence_rate(self, scorer):
        """Test using confidence_rate key."""
        item = {
            "type": "diagram",
            "confidence_rate": 0.80,
        }

        score = scorer.calculate_from_item(item, threshold=0.85)
        # Should use confidence_rate value
        assert score.confidence_gap_score > 0

    def test_calculate_from_item_datetime_string(self, scorer):
        """Test parsing datetime string."""
        old_time = datetime.now(timezone.utc) - timedelta(hours=10)
        item = {
            "element_type": "text",
            "confidence": 0.85,
            "created_at": old_time.isoformat(),
        }

        score = scorer.calculate_from_item(item, threshold=0.90)
        assert score.age_score > 0

    def test_batch_calculate(self, scorer):
        """Test batch calculation."""
        items = [
            {"element_type": "math", "confidence": 0.90},
            {"element_type": "text", "confidence": 0.80},
            {"element_type": "diagram", "confidence": 0.70},
        ]

        scores = scorer.batch_calculate(items, threshold=0.90)

        assert len(scores) == 3
        # Math at threshold should have lower score
        # Diagram with bigger gap should have higher score
        assert scores[0].confidence_gap_score == 0.0
        assert scores[2].confidence_gap_score > scores[1].confidence_gap_score

    def test_sort_by_priority(self, scorer):
        """Test sorting by priority."""
        items = [
            {"element_type": "text", "confidence": 0.95},  # low priority
            {"element_type": "math", "confidence": 0.70},  # high priority
            {"element_type": "diagram", "confidence": 0.85},  # medium priority
        ]

        sorted_items = scorer.sort_by_priority(items, threshold=0.90)

        # Highest priority first (default descending)
        assert sorted_items[0][0]["element_type"] == "math"
        assert sorted_items[-1][0]["element_type"] == "text"

    def test_sort_by_priority_ascending(self, scorer):
        """Test ascending sort."""
        items = [
            {"element_type": "text", "confidence": 0.95},
            {"element_type": "math", "confidence": 0.70},
        ]

        sorted_items = scorer.sort_by_priority(items, threshold=0.90, descending=False)

        # Lowest priority first
        assert sorted_items[0][0]["element_type"] == "text"

    def test_get_urgency_distribution(self, scorer):
        """Test urgency distribution calculation."""
        scores = [
            PriorityScore(total=50, urgency=UrgencyLevel.LOW),
            PriorityScore(total=150, urgency=UrgencyLevel.MEDIUM),
            PriorityScore(total=250, urgency=UrgencyLevel.HIGH),
            PriorityScore(total=350, urgency=UrgencyLevel.CRITICAL),
            PriorityScore(total=75, urgency=UrgencyLevel.LOW),
        ]

        dist = scorer.get_urgency_distribution(scores)

        assert dist["low"] == 2
        assert dist["medium"] == 1
        assert dist["high"] == 1
        assert dist["critical"] == 1


class TestGlobalScorer:
    """Tests for global scorer functions."""

    def test_get_scorer_singleton(self):
        """Test get_scorer returns singleton."""
        scorer1 = get_scorer()
        scorer2 = get_scorer()
        assert scorer1 is scorer2

    def test_configure_scorer(self):
        """Test configure_scorer creates new instance."""
        scorer = configure_scorer(
            weights={"confidence_gap": 150.0},
            criticality={"custom_type": 0.9},
        )

        assert scorer.weights["confidence_gap"] == 150.0
        assert scorer.get_criticality("custom_type") == 0.9

    def test_calculate_priority_convenience(self):
        """Test calculate_priority convenience function."""
        configure_scorer()  # Reset to defaults

        score = calculate_priority(
            confidence=0.85,
            threshold=0.90,
            element_type="equation",
        )

        assert score.total > 0
        assert score.confidence_gap_score > 0


class TestTimezoneHandling:
    """Tests for timezone handling."""

    @pytest.fixture
    def scorer(self):
        return PriorityScorer()

    def test_naive_datetime_treated_as_utc(self, scorer):
        """Test that naive datetime is treated as UTC."""
        # Create a naive datetime that represents 5 hours ago in UTC
        utc_now = datetime.now(timezone.utc)
        naive_time = utc_now.replace(tzinfo=None) - timedelta(hours=5)

        score = scorer.calculate(
            confidence=0.85,
            threshold=0.90,
            element_type="text",
            created_at=naive_time,
        )

        # Should calculate age as ~5 hours * 2 = 10 points
        assert score.age_score == pytest.approx(10.0, abs=1.0)

    def test_aware_datetime(self, scorer):
        """Test handling of timezone-aware datetime."""
        aware_time = datetime.now(timezone.utc) - timedelta(hours=5)

        score = scorer.calculate(
            confidence=0.85,
            threshold=0.90,
            element_type="text",
            created_at=aware_time,
        )

        assert score.age_score == pytest.approx(10.0, abs=1.0)  # 5 hours * 2
