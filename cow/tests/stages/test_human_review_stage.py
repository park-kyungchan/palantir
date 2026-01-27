"""
Tests for Stage G (HumanReviewStage) BaseStage wrapper.

Tests cover:
- HumanReviewInput composite input validation
- HumanReviewStageConfig configuration
- HumanReviewStage BaseStage implementation
- Dynamic threshold integration (v2.0.0)
- Priority scoring with thresholds
- Error handling and metrics collection

Schema Version: 2.0.0
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timezone

from mathpix_pipeline.schemas import (
    BBox,
    Confidence,
    CombinedConfidence,
    Provenance,
    PipelineStage,
    ReviewSeverity,
)
from mathpix_pipeline.schemas.pipeline import PipelineResult, PipelineOptions
from mathpix_pipeline.schemas.alignment import (
    AlignmentReport,
    MatchedPair,
    MatchType,
    TextElement,
    VisualElement,
    AlignmentStatistics,
)
from mathpix_pipeline.schemas.threshold import (
    ThresholdConfig,
    ThresholdContext,
    FeedbackStats,
    ComplexityLevel,
    ElementThreshold,
    GlobalSettings,
)
from mathpix_pipeline.schemas.common import RiskLevel
from mathpix_pipeline.stages import (
    HumanReviewStage,
    HumanReviewStageConfig,
    HumanReviewInput,
    ReviewSummary,
    create_human_review_stage,
    create_human_review_input,
    ValidationResult,
    StageExecutionError,
)
from mathpix_pipeline.human_review import (
    PriorityScorer,
    PriorityScorerConfig,
    ReviewQueueManager,
    QueueConfig,
    ReviewPriority,
)


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def sample_pipeline_result():
    """Create a sample PipelineResult for testing."""
    return PipelineResult(
        image_id="test-image-001",
        success=True,
        stages_completed=[
            PipelineStage.INGESTION,
            PipelineStage.TEXT_PARSE,
            PipelineStage.VISION_PARSE,
            PipelineStage.ALIGNMENT,
        ],
        overall_confidence=0.65,
    )


@pytest.fixture
def pipeline_result_with_alignment():
    """Create PipelineResult with alignment report containing low-confidence pairs."""
    alignment_report = AlignmentReport(
        image_id="test-image-002",
        text_spec_id="text-002",
        vision_spec_id="vision-002",
        provenance=Provenance(
            stage=PipelineStage.ALIGNMENT,
            model="alignment-engine-v2",
        ),
        matched_pairs=[
            MatchedPair(
                id="match-001",
                match_type=MatchType.LABEL_TO_POINT,
                text_element=TextElement(
                    id="text-A",
                    content="A",
                    bbox=BBox(x=100, y=100, width=20, height=20),
                ),
                visual_element=VisualElement(
                    id="visual-A",
                    element_class="point",
                    semantic_label="Point A",
                    bbox=BBox(x=100, y=100, width=20, height=20),
                ),
                consistency_score=0.45,
                confidence=Confidence(value=0.45, source="test", element_type="match"),
                applied_threshold=0.60,
            ),
            MatchedPair(
                id="match-002",
                match_type=MatchType.EQUATION_TO_GRAPH,
                text_element=TextElement(
                    id="text-eq",
                    content="y = x^2",
                    bbox=BBox(x=200, y=200, width=100, height=30),
                ),
                visual_element=VisualElement(
                    id="visual-curve",
                    element_class="curve",
                    semantic_label="Parabola",
                    bbox=BBox(x=150, y=150, width=200, height=150),
                ),
                consistency_score=0.85,
                confidence=Confidence(value=0.85, source="test", element_type="match"),
                applied_threshold=0.60,
            ),
        ],
        statistics=AlignmentStatistics(
            total_text_elements=2,
            total_visual_elements=2,
        ),
        overall_alignment_score=0.65,
        overall_confidence=0.65,
    )

    # Create without alignment_report first to avoid recursion in validator
    result = PipelineResult(
        image_id="test-image-002",
        success=True,
        stages_completed=[
            PipelineStage.INGESTION,
            PipelineStage.TEXT_PARSE,
            PipelineStage.VISION_PARSE,
            PipelineStage.ALIGNMENT,
        ],
        overall_confidence=0.65,
    )
    # Set alignment_report using object.__setattr__ to bypass validator
    object.__setattr__(result, "alignment_report", alignment_report)
    return result


@pytest.fixture
def sample_threshold_config():
    """Create a sample ThresholdConfig for testing."""
    return ThresholdConfig(
        global_settings=GlobalSettings(
            min_threshold=0.15,
            max_threshold=0.90,
        ),
        element_thresholds={
            "matched_pair": ElementThreshold(
                base=0.55,
                risk=RiskLevel.MEDIUM,
                default_severity=ReviewSeverity.MEDIUM,
            ),
            "equation": ElementThreshold(
                base=0.50,
                risk=RiskLevel.HIGH,
                default_severity=ReviewSeverity.HIGH,
            ),
            "point": ElementThreshold(
                base=0.45,
                risk=RiskLevel.MEDIUM,
                default_severity=ReviewSeverity.MEDIUM,
            ),
        },
    )


# =============================================================================
# HumanReviewInput Tests
# =============================================================================

class TestHumanReviewInput:
    """Tests for HumanReviewInput composite input class."""

    def test_create_human_review_input(self, sample_pipeline_result):
        """Test creating HumanReviewInput with pipeline result."""
        input_data = HumanReviewInput(
            pipeline_result=sample_pipeline_result,
        )

        assert input_data.pipeline_result == sample_pipeline_result
        assert input_data.threshold_context is None
        assert input_data.feedback_stats is None

    def test_image_id_property(self, sample_pipeline_result):
        """Test image_id property returns pipeline result's image_id."""
        input_data = HumanReviewInput(
            pipeline_result=sample_pipeline_result,
        )

        assert input_data.image_id == "test-image-001"

    def test_needs_review_low_confidence(self, sample_pipeline_result):
        """Test needs_review returns True for low confidence."""
        sample_pipeline_result.overall_confidence = 0.55
        input_data = HumanReviewInput(
            pipeline_result=sample_pipeline_result,
        )

        assert input_data.needs_review() is True

    def test_needs_review_high_confidence(self, sample_pipeline_result):
        """Test needs_review returns False for high confidence."""
        sample_pipeline_result.overall_confidence = 0.85
        sample_pipeline_result.review.review_required = False
        input_data = HumanReviewInput(
            pipeline_result=sample_pipeline_result,
        )

        assert input_data.needs_review() is False

    def test_needs_review_explicit_flag(self, sample_pipeline_result):
        """Test needs_review returns True when review_required is set."""
        sample_pipeline_result.overall_confidence = 0.90
        sample_pipeline_result.review.review_required = True
        input_data = HumanReviewInput(
            pipeline_result=sample_pipeline_result,
        )

        assert input_data.needs_review() is True

    def test_create_with_threshold_context(self, sample_pipeline_result):
        """Test creating input with threshold context."""
        context = ThresholdContext(
            image_quality_score=0.9,
            problem_level=ComplexityLevel.ADVANCED,
        )

        input_data = HumanReviewInput(
            pipeline_result=sample_pipeline_result,
            threshold_context=context,
        )

        assert input_data.threshold_context == context


# =============================================================================
# HumanReviewStageConfig Tests
# =============================================================================

class TestHumanReviewStageConfig:
    """Tests for HumanReviewStageConfig configuration class."""

    def test_default_config(self):
        """Test default configuration values."""
        config = HumanReviewStageConfig()

        assert config.threshold_config is None
        assert config.threshold_context is None
        assert config.feedback_stats is None
        assert config.enable_dynamic_thresholds is True
        assert config.scorer_config is None
        assert config.queue_config is None
        assert config.default_queue_name == "default"
        assert config.min_confidence_for_auto_approve == 0.90
        assert config.max_tasks_per_image == 50

    def test_custom_config(self, sample_threshold_config):
        """Test custom configuration values."""
        context = ThresholdContext(image_quality_score=0.9)
        feedback = FeedbackStats(false_negative_rate=0.03)

        config = HumanReviewStageConfig(
            threshold_config=sample_threshold_config,
            threshold_context=context,
            feedback_stats=feedback,
            enable_dynamic_thresholds=True,
            max_tasks_per_image=100,
        )

        assert config.threshold_config == sample_threshold_config
        assert config.threshold_context == context
        assert config.feedback_stats == feedback
        assert config.max_tasks_per_image == 100

    def test_get_scorer_config_default(self):
        """Test get_scorer_config with defaults."""
        config = HumanReviewStageConfig()
        scorer_config = config.get_scorer_config()

        assert isinstance(scorer_config, PriorityScorerConfig)
        assert scorer_config.threshold_config is None

    def test_get_scorer_config_with_threshold(self, sample_threshold_config):
        """Test get_scorer_config passes threshold config."""
        context = ThresholdContext(image_quality_score=0.85)

        config = HumanReviewStageConfig(
            threshold_config=sample_threshold_config,
            threshold_context=context,
            enable_dynamic_thresholds=True,
        )
        scorer_config = config.get_scorer_config()

        assert scorer_config.threshold_config == sample_threshold_config
        assert scorer_config.threshold_context == context


# =============================================================================
# HumanReviewStage Validation Tests
# =============================================================================

class TestHumanReviewStageValidation:
    """Tests for HumanReviewStage input validation."""

    @pytest.fixture
    def stage(self):
        """Create stage with default config."""
        return HumanReviewStage()

    def test_validate_none_input(self, stage):
        """Test validation fails for None input."""
        result = stage.validate(None)

        assert not result.is_valid
        assert len(result.errors) == 1
        assert "HumanReviewInput is required" in result.errors[0]

    def test_validate_missing_pipeline_result(self, stage):
        """Test validation fails when pipeline_result is None."""
        input_data = HumanReviewInput(
            pipeline_result=None,
        )

        result = stage.validate(input_data)

        assert not result.is_valid
        assert any("PipelineResult is required" in e for e in result.errors)

    def test_validate_missing_image_id(self, stage):
        """Test validation fails when image_id is empty."""
        # Create a valid PipelineResult then set image_id to empty via __setattr__
        pipeline_result = PipelineResult(
            image_id="temp",
            success=True,
        )
        # Bypass pydantic validation to set empty image_id
        object.__setattr__(pipeline_result, "image_id", "")

        input_data = HumanReviewInput(
            pipeline_result=pipeline_result,
        )

        result = stage.validate(input_data)

        assert not result.is_valid
        assert any("image_id is required" in e for e in result.errors)

    def test_validate_high_confidence_warning(self, stage, sample_pipeline_result):
        """Test validation warns for high confidence result."""
        sample_pipeline_result.overall_confidence = 0.95
        sample_pipeline_result.review.review_required = False

        input_data = HumanReviewInput(
            pipeline_result=sample_pipeline_result,
        )

        result = stage.validate(input_data)

        assert result.is_valid
        assert len(result.warnings) > 0
        assert any("may not require human review" in w for w in result.warnings)

    def test_validate_low_quality_warning(self, stage, sample_pipeline_result):
        """Test validation warns for low image quality."""
        context = ThresholdContext(image_quality_score=0.2)

        input_data = HumanReviewInput(
            pipeline_result=sample_pipeline_result,
            threshold_context=context,
        )

        result = stage.validate(input_data)

        assert result.is_valid
        assert any("Low image quality" in w for w in result.warnings)

    def test_validate_valid_input(self, stage, sample_pipeline_result):
        """Test validation passes for valid input."""
        input_data = HumanReviewInput(
            pipeline_result=sample_pipeline_result,
        )

        result = stage.validate(input_data)

        assert result.is_valid
        assert len(result.errors) == 0


# =============================================================================
# HumanReviewStage Execution Tests
# =============================================================================

class TestHumanReviewStageExecution:
    """Tests for HumanReviewStage execution."""

    @pytest.fixture
    def stage(self):
        """Create stage with default config."""
        return HumanReviewStage()

    @pytest.mark.asyncio
    async def test_execute_basic(self, stage, sample_pipeline_result):
        """Test basic execution with pipeline result."""
        input_data = HumanReviewInput(
            pipeline_result=sample_pipeline_result,
        )

        result = await stage.run_async(input_data)

        assert result.is_valid
        assert result.output is not None
        assert isinstance(result.output, ReviewSummary)
        assert result.output.image_id == sample_pipeline_result.image_id

    @pytest.mark.asyncio
    async def test_execute_with_alignment_creates_tasks(
        self, pipeline_result_with_alignment
    ):
        """Test execution creates tasks for low-confidence pairs."""
        stage = HumanReviewStage()

        input_data = HumanReviewInput(
            pipeline_result=pipeline_result_with_alignment,
        )

        result = await stage.run_async(input_data)

        assert result.is_valid
        assert result.output is not None
        # Should have created at least 1 task for the low-confidence pair
        assert result.output.tasks_created >= 1

    @pytest.mark.asyncio
    async def test_execute_with_threshold_context(
        self, pipeline_result_with_alignment
    ):
        """Test execution with threshold context."""
        context = ThresholdContext(
            image_quality_score=0.95,
            problem_level=ComplexityLevel.ADVANCED,
        )
        config = HumanReviewStageConfig(threshold_context=context)
        stage = HumanReviewStage(config=config)

        input_data = HumanReviewInput(
            pipeline_result=pipeline_result_with_alignment,
        )

        result = await stage.run_async(input_data)

        assert result.is_valid
        assert result.output is not None
        assert result.output.threshold_info.get("image_quality_score") == 0.95

    @pytest.mark.asyncio
    async def test_execute_with_kwargs_context(
        self, pipeline_result_with_alignment
    ):
        """Test execution with context passed via kwargs."""
        stage = HumanReviewStage()
        context = ThresholdContext(image_quality_score=0.8)

        input_data = HumanReviewInput(
            pipeline_result=pipeline_result_with_alignment,
        )

        result = await stage.run_async(
            input_data,
            threshold_context=context,
        )

        assert result.is_valid
        assert result.output is not None

    def test_execute_sync(self, stage, sample_pipeline_result):
        """Test synchronous execution."""
        input_data = HumanReviewInput(
            pipeline_result=sample_pipeline_result,
        )

        result = stage.run(input_data)

        assert result.is_valid
        assert result.output is not None
        assert isinstance(result.output, ReviewSummary)


# =============================================================================
# HumanReviewStage Properties Tests
# =============================================================================

class TestHumanReviewStageProperties:
    """Tests for HumanReviewStage properties."""

    def test_stage_name(self):
        """Test stage_name returns HUMAN_REVIEW."""
        stage = HumanReviewStage()
        assert stage.stage_name == PipelineStage.HUMAN_REVIEW

    def test_config_property(self):
        """Test config property returns typed config."""
        config = HumanReviewStageConfig(max_tasks_per_image=25)
        stage = HumanReviewStage(config=config)

        assert stage.config == config
        assert stage.config.max_tasks_per_image == 25

    def test_scorer_property(self):
        """Test scorer property returns PriorityScorer."""
        stage = HumanReviewStage()
        assert isinstance(stage.scorer, PriorityScorer)

    def test_queue_manager_property(self):
        """Test queue_manager property returns ReviewQueueManager."""
        stage = HumanReviewStage()
        assert isinstance(stage.queue_manager, ReviewQueueManager)

    def test_custom_scorer(self):
        """Test using custom scorer."""
        # Weights must sum to 1.0
        custom_scorer = PriorityScorer(
            PriorityScorerConfig(
                confidence_weight=0.50,
                complexity_weight=0.20,
                urgency_weight=0.15,
                business_weight=0.15,
            )
        )
        stage = HumanReviewStage(scorer=custom_scorer)

        assert stage.scorer == custom_scorer


# =============================================================================
# HumanReviewStage Metrics Tests
# =============================================================================

class TestHumanReviewStageMetrics:
    """Tests for HumanReviewStage metrics collection."""

    @pytest.fixture
    def mock_summary(self):
        """Create a mock ReviewSummary for metrics testing."""
        return ReviewSummary(
            image_id="test-001",
            tasks_created=5,
            tasks_by_priority={
                "critical": 1,
                "high": 2,
                "medium": 2,
                "low": 0,
            },
            tasks_by_severity={
                "blocker": 0,
                "high": 1,
                "medium": 4,
                "low": 0,
            },
            task_ids=["task-1", "task-2", "task-3", "task-4", "task-5"],
            processing_time_ms=150.0,
            dynamic_thresholds_enabled=True,
        )

    def test_get_metrics(self, mock_summary):
        """Test metrics collection from ReviewSummary."""
        stage = HumanReviewStage()
        metrics = stage.get_metrics(mock_summary)

        assert metrics.stage == PipelineStage.HUMAN_REVIEW
        assert metrics.success is True
        assert metrics.elements_processed == 5
        assert "tasks_created" in metrics.custom_metrics
        assert metrics.custom_metrics["tasks_created"] == 5
        assert metrics.custom_metrics["critical_count"] == 1
        assert metrics.custom_metrics["high_count"] == 2

    def test_get_metrics_none_output(self):
        """Test metrics collection with None output."""
        stage = HumanReviewStage()
        metrics = stage.get_metrics(None)

        assert metrics.stage == PipelineStage.HUMAN_REVIEW
        assert metrics.success is False
        assert metrics.elements_processed == 0


# =============================================================================
# HumanReviewStage Threshold Integration Tests
# =============================================================================

class TestHumanReviewStageThresholds:
    """Tests for dynamic threshold integration."""

    def test_get_effective_threshold_no_config(self):
        """Test effective threshold without threshold config."""
        config = HumanReviewStageConfig(enable_dynamic_thresholds=False)
        stage = HumanReviewStage(config=config)

        threshold = stage._get_effective_threshold("equation")

        # Should return static default
        assert threshold == 0.55

    def test_get_effective_threshold_static_defaults(self):
        """Test static default thresholds for various element types."""
        config = HumanReviewStageConfig(enable_dynamic_thresholds=False)
        stage = HumanReviewStage(config=config)

        assert stage._get_effective_threshold("equation") == 0.55
        assert stage._get_effective_threshold("point") == 0.50
        assert stage._get_effective_threshold("label") == 0.45
        assert stage._get_effective_threshold("curve") == 0.55

    def test_get_effective_threshold_with_config(self, sample_threshold_config):
        """Test effective threshold with threshold config."""
        context = ThresholdContext(image_quality_score=0.9)
        config = HumanReviewStageConfig(
            threshold_config=sample_threshold_config,
            threshold_context=context,
            enable_dynamic_thresholds=True,
        )
        stage = HumanReviewStage(config=config)

        threshold = stage._get_effective_threshold("matched_pair", context)

        # Should compute dynamic threshold (not just base)
        assert threshold > 0
        assert threshold <= 0.90  # Within global max

    @pytest.mark.asyncio
    async def test_dynamic_thresholds_affect_task_creation(
        self, pipeline_result_with_alignment, sample_threshold_config
    ):
        """Test that dynamic thresholds affect task creation."""
        # Low threshold - should create fewer tasks
        low_context = ThresholdContext(
            image_quality_score=0.95,
            problem_level=ComplexityLevel.ELEMENTARY,
        )
        low_config = HumanReviewStageConfig(
            threshold_config=sample_threshold_config,
            threshold_context=low_context,
            enable_dynamic_thresholds=True,
        )
        low_stage = HumanReviewStage(config=low_config)

        # High threshold config - should create more tasks
        high_context = ThresholdContext(
            image_quality_score=0.5,
            problem_level=ComplexityLevel.ADVANCED,
        )
        high_config = HumanReviewStageConfig(
            threshold_config=sample_threshold_config,
            threshold_context=high_context,
            enable_dynamic_thresholds=True,
        )
        high_stage = HumanReviewStage(config=high_config)

        input_data = HumanReviewInput(
            pipeline_result=pipeline_result_with_alignment,
        )

        low_result = await low_stage.run_async(input_data)
        high_result = await high_stage.run_async(input_data)

        assert low_result.is_valid
        assert high_result.is_valid
        # Both should complete successfully (task counts may vary)


# =============================================================================
# Factory Function Tests
# =============================================================================

class TestFactoryFunctions:
    """Tests for factory functions."""

    def test_create_human_review_stage_default(self):
        """Test creating stage with default config."""
        stage = create_human_review_stage()

        assert isinstance(stage, HumanReviewStage)
        assert stage.config.enable_dynamic_thresholds is True

    def test_create_human_review_stage_with_config(self):
        """Test creating stage with custom config."""
        config = HumanReviewStageConfig(max_tasks_per_image=10)
        stage = create_human_review_stage(config=config)

        assert stage.config.max_tasks_per_image == 10

    def test_create_human_review_stage_with_threshold_config(
        self, sample_threshold_config
    ):
        """Test creating stage with threshold config."""
        stage = create_human_review_stage(
            threshold_config=sample_threshold_config,
            enable_dynamic_thresholds=True,
        )

        assert stage.config.threshold_config == sample_threshold_config
        assert stage.config.enable_dynamic_thresholds is True

    def test_create_human_review_input_factory(self, sample_pipeline_result):
        """Test factory function creates valid input."""
        context = ThresholdContext(image_quality_score=0.8)

        input_data = create_human_review_input(
            pipeline_result=sample_pipeline_result,
            threshold_context=context,
        )

        assert isinstance(input_data, HumanReviewInput)
        assert input_data.pipeline_result == sample_pipeline_result
        assert input_data.threshold_context == context


# =============================================================================
# ReviewSummary Tests
# =============================================================================

class TestReviewSummary:
    """Tests for ReviewSummary output type."""

    def test_has_tasks_true(self):
        """Test has_tasks returns True when tasks exist."""
        summary = ReviewSummary(
            image_id="test-001",
            tasks_created=3,
        )

        assert summary.has_tasks is True

    def test_has_tasks_false(self):
        """Test has_tasks returns False when no tasks."""
        summary = ReviewSummary(
            image_id="test-001",
            tasks_created=0,
        )

        assert summary.has_tasks is False

    def test_critical_count(self):
        """Test critical_count property."""
        summary = ReviewSummary(
            image_id="test-001",
            tasks_created=5,
            tasks_by_priority={
                "critical": 2,
                "high": 2,
                "medium": 1,
            },
        )

        assert summary.critical_count == 2

    def test_high_count(self):
        """Test high_count property."""
        summary = ReviewSummary(
            image_id="test-001",
            tasks_created=5,
            tasks_by_priority={
                "critical": 1,
                "high": 3,
                "medium": 1,
            },
        )

        assert summary.high_count == 3


# =============================================================================
# Integration Tests
# =============================================================================

class TestHumanReviewStageIntegration:
    """Integration tests for HumanReviewStage."""

    @pytest.mark.asyncio
    async def test_full_lifecycle(self, pipeline_result_with_alignment):
        """Test full stage lifecycle."""
        config = HumanReviewStageConfig(
            enable_dynamic_thresholds=False,
        )
        stage = HumanReviewStage(config=config)

        input_data = HumanReviewInput(
            pipeline_result=pipeline_result_with_alignment,
        )

        result = await stage.run_async(input_data)

        # Should succeed
        assert result.is_valid
        assert result.output is not None

        # Should have timing
        assert result.timing is not None
        assert result.timing.success is True

        # Should have metrics
        assert result.metrics is not None
        assert result.metrics.stage == PipelineStage.HUMAN_REVIEW

        # Output should have expected fields
        summary = result.output
        assert summary.image_id == pipeline_result_with_alignment.image_id
        assert isinstance(summary.processing_time_ms, float)

    @pytest.mark.asyncio
    async def test_provenance_tracking(self, sample_pipeline_result):
        """Test that provenance is correctly set."""
        stage = HumanReviewStage()

        input_data = HumanReviewInput(
            pipeline_result=sample_pipeline_result,
        )

        result = await stage.run_async(input_data)

        assert result.is_valid
        assert result.output.provenance.stage == PipelineStage.HUMAN_REVIEW
        assert result.output.provenance.model is not None
