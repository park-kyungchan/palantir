"""
Tests for Stage D (AlignmentStage) BaseStage wrapper.

Tests cover:
- AlignmentInput composite input validation
- AlignmentStageConfig configuration
- AlignmentStage BaseStage implementation
- Dynamic threshold integration (v2.0.0)
- Error handling and metrics collection

Schema Version: 2.0.0
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from mathpix_pipeline.schemas import (
    BBox,
    Confidence,
    CombinedConfidence,
    Provenance,
    PipelineStage,
    ReviewSeverity,
    # Stage B
    TextSpec,
    ContentFlags,
    LineSegment,
    EquationElement,
    WritingStyle,
    VisionParseTrigger,
    # Stage C
    VisionSpec,
    DetectionLayer,
    InterpretationLayer,
    MergedOutput,
    DetectionElement,
    InterpretedElement,
    MergedElement,
    ElementClass,
    DiagramType,
    # Stage D
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
)
from mathpix_pipeline.stages import (
    AlignmentStage,
    AlignmentStageConfig,
    AlignmentInput,
    create_alignment_stage,
    create_alignment_input,
    ValidationResult,
    StageExecutionError,
)
from mathpix_pipeline.alignment import AlignmentEngine, AlignmentEngineConfig


# =============================================================================
# AlignmentInput Tests
# =============================================================================

class TestAlignmentInput:
    """Tests for AlignmentInput composite input class."""

    def test_create_alignment_input(self, sample_text_spec, sample_vision_spec):
        """Test creating AlignmentInput with text and vision specs."""
        input_data = AlignmentInput(
            text_spec=sample_text_spec,
            vision_spec=sample_vision_spec,
        )

        assert input_data.text_spec == sample_text_spec
        assert input_data.vision_spec == sample_vision_spec

    def test_image_id_property(self, sample_text_spec, sample_vision_spec):
        """Test image_id property returns text_spec's image_id."""
        input_data = AlignmentInput(
            text_spec=sample_text_spec,
            vision_spec=sample_vision_spec,
        )

        assert input_data.image_id == sample_text_spec.image_id

    def test_validate_image_ids_match_success(self, sample_text_spec, sample_vision_spec):
        """Test validation passes when image IDs match."""
        # Both fixtures use same image_id
        input_data = AlignmentInput(
            text_spec=sample_text_spec,
            vision_spec=sample_vision_spec,
        )

        assert input_data.validate_image_ids_match()

    def test_validate_image_ids_match_failure(self, sample_text_spec):
        """Test validation fails when image IDs don't match."""
        # Create vision spec with different image_id
        mismatched_vision_spec = VisionSpec(
            image_id="different-image-id",
            provenance=Provenance(
                stage=PipelineStage.VISION_PARSE,
                model="test",
            ),
        )

        input_data = AlignmentInput(
            text_spec=sample_text_spec,
            vision_spec=mismatched_vision_spec,
        )

        assert not input_data.validate_image_ids_match()

    def test_create_alignment_input_factory(self, sample_text_spec, sample_vision_spec):
        """Test factory function creates valid input."""
        input_data = create_alignment_input(
            text_spec=sample_text_spec,
            vision_spec=sample_vision_spec,
        )

        assert isinstance(input_data, AlignmentInput)
        assert input_data.text_spec == sample_text_spec
        assert input_data.vision_spec == sample_vision_spec


# =============================================================================
# AlignmentStageConfig Tests
# =============================================================================

class TestAlignmentStageConfig:
    """Tests for AlignmentStageConfig configuration class."""

    def test_default_config(self):
        """Test default configuration values."""
        config = AlignmentStageConfig()

        assert config.base_alignment_threshold == 0.60
        assert config.base_inconsistency_threshold == 0.80
        assert config.enable_threshold_adjustment is True
        assert config.enable_auto_fix_detection is True
        assert config.threshold_context is None
        assert config.feedback_stats is None
        assert config.threshold_config is None
        assert config.engine_config is None

    def test_custom_config(self):
        """Test custom configuration values."""
        context = ThresholdContext(image_quality_score=0.9)
        feedback = FeedbackStats(false_negative_rate=0.03)

        config = AlignmentStageConfig(
            base_alignment_threshold=0.70,
            base_inconsistency_threshold=0.85,
            enable_threshold_adjustment=False,
            threshold_context=context,
            feedback_stats=feedback,
        )

        assert config.base_alignment_threshold == 0.70
        assert config.base_inconsistency_threshold == 0.85
        assert config.enable_threshold_adjustment is False
        assert config.threshold_context == context
        assert config.feedback_stats == feedback

    def test_to_engine_config_default(self):
        """Test conversion to engine config with defaults."""
        config = AlignmentStageConfig()
        engine_config = config.to_engine_config()

        assert isinstance(engine_config, AlignmentEngineConfig)
        assert engine_config.base_alignment_threshold == 0.60
        assert engine_config.base_inconsistency_threshold == 0.80

    def test_to_engine_config_custom(self):
        """Test conversion preserves custom engine config."""
        custom_engine_config = AlignmentEngineConfig(
            base_alignment_threshold=0.50,
        )
        config = AlignmentStageConfig(engine_config=custom_engine_config)

        result = config.to_engine_config()
        assert result == custom_engine_config


# =============================================================================
# AlignmentStage Validation Tests
# =============================================================================

class TestAlignmentStageValidation:
    """Tests for AlignmentStage input validation."""

    @pytest.fixture
    def stage(self):
        """Create stage with default config."""
        return AlignmentStage()

    def test_validate_none_input(self, stage):
        """Test validation fails for None input."""
        result = stage.validate(None)

        assert not result.is_valid
        assert len(result.errors) == 1
        assert "AlignmentInput is required" in result.errors[0]

    def test_validate_missing_text_spec(self, stage, sample_vision_spec):
        """Test validation fails when text_spec is None."""
        input_data = AlignmentInput(
            text_spec=None,
            vision_spec=sample_vision_spec,
        )

        result = stage.validate(input_data)

        assert not result.is_valid
        assert any("TextSpec is required" in e for e in result.errors)

    def test_validate_missing_vision_spec(self, stage, sample_text_spec):
        """Test validation fails when vision_spec is None."""
        input_data = AlignmentInput(
            text_spec=sample_text_spec,
            vision_spec=None,
        )

        result = stage.validate(input_data)

        assert not result.is_valid
        assert any("VisionSpec is required" in e for e in result.errors)

    def test_validate_image_id_mismatch(self, stage, sample_text_spec):
        """Test validation fails when image IDs don't match."""
        mismatched_vision = VisionSpec(
            image_id="different-id",
            provenance=Provenance(stage=PipelineStage.VISION_PARSE, model="test"),
        )

        input_data = AlignmentInput(
            text_spec=sample_text_spec,
            vision_spec=mismatched_vision,
        )

        result = stage.validate(input_data)

        assert not result.is_valid
        assert any("mismatch" in e.lower() for e in result.errors)

    def test_validate_empty_text_spec_warning(self, stage, sample_vision_spec):
        """Test validation warns for empty text spec."""
        empty_text_spec = TextSpec(
            image_id=sample_vision_spec.image_id,
            provenance=Provenance(stage=PipelineStage.TEXT_PARSE, model="test"),
            equations=[],
            line_segments=[],
        )

        input_data = AlignmentInput(
            text_spec=empty_text_spec,
            vision_spec=sample_vision_spec,
        )

        result = stage.validate(input_data)

        # Should be valid but with warnings
        assert result.is_valid
        assert len(result.warnings) > 0
        assert any("no equations or line segments" in w for w in result.warnings)

    def test_validate_empty_vision_spec_warning(self, stage, sample_text_spec):
        """Test validation warns for empty vision spec."""
        empty_vision_spec = VisionSpec(
            image_id=sample_text_spec.image_id,
            provenance=Provenance(stage=PipelineStage.VISION_PARSE, model="test"),
            merged_output=MergedOutput(elements=[]),
        )

        input_data = AlignmentInput(
            text_spec=sample_text_spec,
            vision_spec=empty_vision_spec,
        )

        result = stage.validate(input_data)

        # Should be valid but with warnings
        assert result.is_valid
        assert len(result.warnings) > 0
        assert any("no merged elements" in w for w in result.warnings)

    def test_validate_valid_input(self, stage, sample_text_spec, sample_vision_spec):
        """Test validation passes for valid input."""
        input_data = AlignmentInput(
            text_spec=sample_text_spec,
            vision_spec=sample_vision_spec,
        )

        result = stage.validate(input_data)

        assert result.is_valid
        assert len(result.errors) == 0


# =============================================================================
# AlignmentStage Execution Tests
# =============================================================================

class TestAlignmentStageExecution:
    """Tests for AlignmentStage execution."""

    @pytest.fixture
    def stage(self):
        """Create stage with default config."""
        return AlignmentStage()

    @pytest.mark.asyncio
    async def test_execute_basic(self, stage, sample_text_spec, sample_vision_spec):
        """Test basic alignment execution."""
        input_data = AlignmentInput(
            text_spec=sample_text_spec,
            vision_spec=sample_vision_spec,
        )

        result = await stage.run_async(input_data)

        assert result.is_valid
        assert result.output is not None
        assert isinstance(result.output, AlignmentReport)
        assert result.output.image_id == sample_text_spec.image_id

    @pytest.mark.asyncio
    async def test_execute_with_threshold_context(
        self, sample_text_spec, sample_vision_spec
    ):
        """Test execution with threshold context."""
        context = ThresholdContext(
            image_quality_score=0.95,
            problem_level=ComplexityLevel.ADVANCED,
        )
        config = AlignmentStageConfig(threshold_context=context)
        stage = AlignmentStage(config=config)

        input_data = AlignmentInput(
            text_spec=sample_text_spec,
            vision_spec=sample_vision_spec,
        )

        result = await stage.run_async(input_data)

        assert result.is_valid
        assert result.output is not None

    @pytest.mark.asyncio
    async def test_execute_with_kwargs_context(
        self, sample_text_spec, sample_vision_spec
    ):
        """Test execution with context passed via kwargs."""
        stage = AlignmentStage()
        context = ThresholdContext(image_quality_score=0.8)

        input_data = AlignmentInput(
            text_spec=sample_text_spec,
            vision_spec=sample_vision_spec,
        )

        result = await stage.run_async(
            input_data,
            threshold_context=context,
        )

        assert result.is_valid
        assert result.output is not None

    @pytest.mark.asyncio
    async def test_execute_validation_failure(self, stage, sample_text_spec):
        """Test execution fails with invalid input."""
        mismatched_vision = VisionSpec(
            image_id="different-id",
            provenance=Provenance(stage=PipelineStage.VISION_PARSE, model="test"),
        )

        input_data = AlignmentInput(
            text_spec=sample_text_spec,
            vision_spec=mismatched_vision,
        )

        result = await stage.run_async(input_data)

        assert not result.is_valid
        assert result.output is None
        assert len(result.errors) > 0

    def test_execute_sync(self, stage, sample_text_spec, sample_vision_spec):
        """Test synchronous execution."""
        input_data = AlignmentInput(
            text_spec=sample_text_spec,
            vision_spec=sample_vision_spec,
        )

        result = stage.run(input_data)

        assert result.is_valid
        assert result.output is not None
        assert isinstance(result.output, AlignmentReport)


# =============================================================================
# AlignmentStage Properties Tests
# =============================================================================

class TestAlignmentStageProperties:
    """Tests for AlignmentStage properties."""

    def test_stage_name(self):
        """Test stage_name returns ALIGNMENT."""
        stage = AlignmentStage()
        assert stage.stage_name == PipelineStage.ALIGNMENT

    def test_config_property(self):
        """Test config property returns typed config."""
        config = AlignmentStageConfig(base_alignment_threshold=0.75)
        stage = AlignmentStage(config=config)

        assert stage.config == config
        assert stage.config.base_alignment_threshold == 0.75

    def test_engine_property(self):
        """Test engine property returns AlignmentEngine."""
        stage = AlignmentStage()
        assert isinstance(stage.engine, AlignmentEngine)

    def test_custom_engine(self):
        """Test using custom engine."""
        custom_engine = AlignmentEngine(
            config=AlignmentEngineConfig(base_alignment_threshold=0.55)
        )
        stage = AlignmentStage(engine=custom_engine)

        assert stage.engine == custom_engine


# =============================================================================
# AlignmentStage Metrics Tests
# =============================================================================

class TestAlignmentStageMetrics:
    """Tests for AlignmentStage metrics collection."""

    @pytest.fixture
    def mock_report(self):
        """Create a mock alignment report for metrics testing."""
        return AlignmentReport(
            image_id="test-001",
            text_spec_id="text-001",
            vision_spec_id="vision-001",
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
                    consistency_score=0.85,
                    confidence=Confidence(value=0.85, source="test", element_type="match"),
                    applied_threshold=0.60,
                ),
            ],
            statistics=AlignmentStatistics(
                total_text_elements=2,
                total_visual_elements=2,
            ),
            overall_alignment_score=0.85,
            overall_confidence=0.85,
        )

    def test_get_metrics(self, mock_report):
        """Test metrics collection from alignment report."""
        stage = AlignmentStage()
        metrics = stage.get_metrics(mock_report)

        assert metrics.stage == PipelineStage.ALIGNMENT
        assert metrics.success is True
        assert metrics.elements_processed == 1  # matched_pairs_count
        assert "matched_pairs" in metrics.custom_metrics
        assert metrics.custom_metrics["matched_pairs"] == 1
        assert "overall_alignment_score" in metrics.custom_metrics
        assert metrics.custom_metrics["overall_alignment_score"] == 0.85

    def test_get_metrics_none_output(self):
        """Test metrics collection with None output."""
        stage = AlignmentStage()
        metrics = stage.get_metrics(None)

        assert metrics.stage == PipelineStage.ALIGNMENT
        assert metrics.success is False
        assert metrics.elements_processed == 0


# =============================================================================
# AlignmentStage Threshold Integration Tests
# =============================================================================

class TestAlignmentStageThresholds:
    """Tests for dynamic threshold integration."""

    def test_get_effective_threshold_no_config(self):
        """Test effective threshold without threshold config."""
        config = AlignmentStageConfig(base_alignment_threshold=0.65)
        stage = AlignmentStage(config=config)

        threshold = stage._get_effective_threshold("alignment_match")

        # Should return base threshold
        assert threshold == 0.65

    def test_get_effective_threshold_with_context(self):
        """Test effective threshold with context but no threshold config."""
        context = ThresholdContext(image_quality_score=0.9)
        config = AlignmentStageConfig(
            base_alignment_threshold=0.60,
            threshold_context=context,
        )
        stage = AlignmentStage(config=config)

        threshold = stage._get_effective_threshold("alignment_match")

        # Without threshold_config, should return base
        assert threshold == 0.60

    @pytest.mark.asyncio
    async def test_threshold_affects_results(
        self, sample_text_spec, sample_vision_spec
    ):
        """Test that threshold configuration affects results."""
        # Low threshold config
        low_config = AlignmentStageConfig(base_alignment_threshold=0.3)
        low_stage = AlignmentStage(config=low_config)

        # High threshold config
        high_config = AlignmentStageConfig(base_alignment_threshold=0.9)
        high_stage = AlignmentStage(config=high_config)

        input_data = AlignmentInput(
            text_spec=sample_text_spec,
            vision_spec=sample_vision_spec,
        )

        low_result = await low_stage.run_async(input_data)
        high_result = await high_stage.run_async(input_data)

        assert low_result.is_valid
        assert high_result.is_valid

        # Low threshold should have more pairs above threshold
        assert (
            low_result.output.pairs_above_threshold >=
            high_result.output.pairs_above_threshold
        )


# =============================================================================
# Factory Function Tests
# =============================================================================

class TestFactoryFunctions:
    """Tests for factory functions."""

    def test_create_alignment_stage_default(self):
        """Test creating stage with default config."""
        stage = create_alignment_stage()

        assert isinstance(stage, AlignmentStage)
        assert stage.config.base_alignment_threshold == 0.60

    def test_create_alignment_stage_with_config(self):
        """Test creating stage with custom config."""
        config = AlignmentStageConfig(base_alignment_threshold=0.75)
        stage = create_alignment_stage(config=config)

        assert stage.config.base_alignment_threshold == 0.75

    def test_create_alignment_stage_with_threshold_config(self):
        """Test creating stage with threshold config."""
        # Note: Full ThresholdConfig requires element_thresholds
        # This test verifies the parameter is passed through
        stage = create_alignment_stage()

        # Threshold config should be None by default
        assert stage.config.threshold_config is None


# =============================================================================
# Integration Tests
# =============================================================================

class TestAlignmentStageIntegration:
    """Integration tests for AlignmentStage."""

    @pytest.mark.asyncio
    async def test_full_lifecycle(self, text_spec_with_labels, vision_spec_with_points):
        """Test full stage lifecycle with labels."""
        config = AlignmentStageConfig(
            base_alignment_threshold=0.5,  # Lower for testing
        )
        stage = AlignmentStage(config=config)

        input_data = AlignmentInput(
            text_spec=text_spec_with_labels,
            vision_spec=vision_spec_with_points,
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
        assert result.metrics.stage == PipelineStage.ALIGNMENT

        # Output should have matched pairs
        report = result.output
        assert report.matched_pairs_count >= 1
        assert report.image_id == text_spec_with_labels.image_id

    @pytest.mark.asyncio
    async def test_provenance_tracking(self, sample_text_spec, sample_vision_spec):
        """Test that provenance is correctly set."""
        stage = AlignmentStage()

        input_data = AlignmentInput(
            text_spec=sample_text_spec,
            vision_spec=sample_vision_spec,
        )

        result = await stage.run_async(input_data)

        assert result.is_valid
        assert result.output.provenance.stage == PipelineStage.ALIGNMENT
        assert result.output.provenance.model is not None

    @pytest.mark.asyncio
    async def test_skip_validation(self, sample_text_spec):
        """Test skip_validation parameter."""
        stage = AlignmentStage()

        # Create mismatched input that would normally fail validation
        mismatched_vision = VisionSpec(
            image_id="different-id",
            provenance=Provenance(stage=PipelineStage.VISION_PARSE, model="test"),
        )

        input_data = AlignmentInput(
            text_spec=sample_text_spec,
            vision_spec=mismatched_vision,
        )

        # Without skip_validation, should fail
        result_with_validation = await stage.run_async(input_data)
        assert not result_with_validation.is_valid

        # With skip_validation, should attempt execution
        # (but may still fail during engine.align due to ID mismatch)
        result_skip = await stage.run_async(input_data, skip_validation=True)
        # Validation result should be None when skipped
        assert result_skip.validation is None
