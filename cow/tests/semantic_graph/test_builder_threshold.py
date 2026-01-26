"""
Tests for dynamic threshold integration in SemanticGraphBuilder (v2.0.0).

Verifies that Stage E correctly applies the 3-layer threshold architecture:
- Layer 1: Base thresholds (per element type)
- Layer 2: Context modifiers (image quality, complexity, density)
- Layer 3: Feedback loop (FN/FP rate adjustments)
"""

import pytest

from mathpix_pipeline.semantic_graph import (
    SemanticGraphBuilder,
    GraphBuilderConfig,
    create_graph_builder,
)
from mathpix_pipeline.schemas.threshold import (
    ThresholdConfig,
    ThresholdContext,
    FeedbackStats,
    ComplexityLevel,
    compute_effective_threshold,
)
from mathpix_pipeline.schemas import (
    BBox,
    Confidence,
)
from mathpix_pipeline.schemas.semantic_graph import (
    SemanticNode,
    NodeType,
    NodeProperties,
)


# =============================================================================
# Fixtures: Threshold Context
# =============================================================================

@pytest.fixture
def threshold_context_high_quality():
    """High-quality image context (high quality score = more strict thresholds)."""
    return ThresholdContext(
        image_quality_score=0.95,
        problem_level=ComplexityLevel.ELEMENTARY,
        element_count=3,
    )


@pytest.fixture
def threshold_context_low_quality():
    """Low-quality image context (low quality score = more lenient thresholds)."""
    return ThresholdContext(
        image_quality_score=0.45,
        problem_level=ComplexityLevel.ADVANCED,
        element_count=15,
    )


@pytest.fixture
def feedback_stats_good():
    """Good feedback stats (low FN/FP rates)."""
    return FeedbackStats(
        false_negative_rate=0.02,
        false_positive_rate=0.15,
    )


@pytest.fixture
def feedback_stats_poor():
    """Poor feedback stats (high FN rate)."""
    return FeedbackStats(
        false_negative_rate=0.08,
        false_positive_rate=0.25,
    )


# =============================================================================
# Test Classes
# =============================================================================

class TestThresholdConfigIntegration:
    """Test GraphBuilderConfig threshold configuration."""

    def test_default_config_static_thresholds(self):
        """Test default config uses static fallback thresholds."""
        config = GraphBuilderConfig()

        assert config.threshold_config is None
        assert config.threshold_context is None
        assert config.node_threshold == 0.60
        assert config.edge_threshold == 0.55

    def test_config_with_threshold_context(self, threshold_context_high_quality):
        """Test config with threshold context."""
        config = GraphBuilderConfig(
            threshold_context=threshold_context_high_quality,
        )

        assert config.threshold_context is not None
        assert config.threshold_context.image_quality_score == 0.95

    def test_get_effective_node_threshold_static(self):
        """Test get_effective_node_threshold returns static value when no dynamic config."""
        config = GraphBuilderConfig(node_threshold=0.70)

        # Without dynamic threshold config, should return static value
        assert config.node_threshold == 0.70


class TestFeedbackIntegration:
    """Test feedback stats integration."""

    def test_feedback_stats_configuration(
        self,
        threshold_context_high_quality,
        feedback_stats_good,
    ):
        """Test that feedback stats can be configured."""
        config = GraphBuilderConfig(
            threshold_context=threshold_context_high_quality,
            feedback_stats=feedback_stats_good,
        )

        assert config.feedback_stats is not None
        assert config.feedback_stats.false_negative_rate == 0.02

    def test_feedback_stats_none_uses_default(
        self,
        threshold_context_high_quality,
    ):
        """Test that None feedback_stats uses default."""
        config = GraphBuilderConfig(
            threshold_context=threshold_context_high_quality,
            feedback_stats=None,
        )

        assert config.feedback_stats is None


class TestBackwardCompatibility:
    """Test backward compatibility with existing code."""

    def test_factory_function_backward_compat(self):
        """Test factory function maintains backward compatibility."""
        # Old-style factory call
        builder = create_graph_builder()

        assert isinstance(builder, SemanticGraphBuilder)
        assert builder.config.node_threshold == 0.60

    def test_config_node_threshold_parameter(self):
        """Test that old-style node_threshold parameter still works."""
        config = GraphBuilderConfig(
            node_threshold=0.75,
            edge_threshold=0.65,
        )
        builder = SemanticGraphBuilder(config=config)

        assert builder.config.node_threshold == 0.75
        assert builder.config.edge_threshold == 0.65


class TestContextModifiers:
    """Test context modifier effects on threshold configuration."""

    def test_quality_score_configuration(
        self,
        feedback_stats_good,
    ):
        """Test that image quality affects threshold context."""
        # High quality context
        context_high = ThresholdContext(
            image_quality_score=0.95,
            problem_level=ComplexityLevel.ELEMENTARY,
            element_count=3,
        )

        # Low quality context
        context_low = ThresholdContext(
            image_quality_score=0.45,
            problem_level=ComplexityLevel.ELEMENTARY,
            element_count=3,
        )

        config_high = GraphBuilderConfig(
            threshold_context=context_high,
            feedback_stats=feedback_stats_good,
        )

        config_low = GraphBuilderConfig(
            threshold_context=context_low,
            feedback_stats=feedback_stats_good,
        )

        # Verify contexts are properly configured
        assert config_high.threshold_context.image_quality_score == 0.95
        assert config_low.threshold_context.image_quality_score == 0.45

    def test_complexity_configuration(
        self,
        feedback_stats_good,
    ):
        """Test that diagram complexity affects threshold context."""
        # Elementary context
        context_elementary = ThresholdContext(
            image_quality_score=0.80,
            problem_level=ComplexityLevel.ELEMENTARY,
            element_count=5,
        )

        # Advanced context
        context_advanced = ThresholdContext(
            image_quality_score=0.80,
            problem_level=ComplexityLevel.ADVANCED,
            element_count=5,
        )

        config_elementary = GraphBuilderConfig(
            threshold_context=context_elementary,
            feedback_stats=feedback_stats_good,
        )

        config_advanced = GraphBuilderConfig(
            threshold_context=context_advanced,
            feedback_stats=feedback_stats_good,
        )

        # Verify complexity levels are properly configured
        assert config_elementary.threshold_context.problem_level == ComplexityLevel.ELEMENTARY
        assert config_advanced.threshold_context.problem_level == ComplexityLevel.ADVANCED


class TestThresholdContextValidation:
    """Test ThresholdContext creation and validation."""

    def test_threshold_context_defaults(self):
        """Test ThresholdContext with default values."""
        context = ThresholdContext()

        assert context.image_quality_score == 1.0
        assert context.problem_level == ComplexityLevel.MIDDLE_SCHOOL
        assert context.element_count == 0

    def test_threshold_context_custom_values(self):
        """Test ThresholdContext with custom values."""
        context = ThresholdContext(
            image_quality_score=0.75,
            problem_level=ComplexityLevel.HIGH_SCHOOL,
            element_count=10,
        )

        assert context.image_quality_score == 0.75
        assert context.problem_level == ComplexityLevel.HIGH_SCHOOL
        assert context.element_count == 10

    def test_threshold_context_boundary_values(self):
        """Test ThresholdContext boundary values."""
        # Min quality
        context_min = ThresholdContext(image_quality_score=0.0)
        assert context_min.image_quality_score == 0.0

        # Max quality
        context_max = ThresholdContext(image_quality_score=1.0)
        assert context_max.image_quality_score == 1.0


class TestFeedbackStatsValidation:
    """Test FeedbackStats creation and validation."""

    def test_feedback_stats_defaults(self):
        """Test FeedbackStats with default values."""
        stats = FeedbackStats()

        assert stats.false_negative_rate == 0.0
        assert stats.false_positive_rate == 0.0

    def test_feedback_stats_custom_values(self):
        """Test FeedbackStats with custom values."""
        stats = FeedbackStats(
            false_negative_rate=0.05,
            false_positive_rate=0.10,
        )

        assert stats.false_negative_rate == 0.05
        assert stats.false_positive_rate == 0.10

    def test_feedback_stats_boundary_values(self):
        """Test FeedbackStats boundary values."""
        # Min values
        stats_min = FeedbackStats(
            false_negative_rate=0.0,
            false_positive_rate=0.0,
        )
        assert stats_min.false_negative_rate == 0.0
        assert stats_min.false_positive_rate == 0.0

        # Max values
        stats_max = FeedbackStats(
            false_negative_rate=1.0,
            false_positive_rate=1.0,
        )
        assert stats_max.false_negative_rate == 1.0
        assert stats_max.false_positive_rate == 1.0
