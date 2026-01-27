"""
Tests for Stage F (RegenerationStage) BaseStage wrapper.

Tests the RegenerationStage implementation:
- Initialization and configuration
- Input validation
- Execution with mock engine
- Metrics collection
- Error handling
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from mathpix_pipeline.stages import (
    RegenerationStage,
    RegenerationStageConfig,
    StageResult,
    StageMetrics,
    ValidationResult,
    StageExecutionError,
)
from mathpix_pipeline.stages.regeneration_stage import create_regeneration_stage
from mathpix_pipeline.schemas.common import PipelineStage
from mathpix_pipeline.schemas.semantic_graph import (
    SemanticGraph,
    SemanticNode,
    SemanticEdge,
    NodeType,
    EdgeType,
    NodeProperties,
    GraphStatistics,
)
from mathpix_pipeline.schemas.regeneration import (
    OutputFormat,
    RegenerationSpec,
    RegenerationOutput,
    DeltaReport,
)
from mathpix_pipeline.schemas import BBox, Provenance, Confidence
from mathpix_pipeline.regeneration.engine import (
    RegenerationEngine,
    EngineResult,
)
from mathpix_pipeline.regeneration.exceptions import RegenerationError


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def sample_node_equation():
    """Sample equation node for testing."""
    return SemanticNode(
        id="node-eq-001",
        node_type=NodeType.EQUATION,
        label="y = x^2 + 2x + 1",
        properties=NodeProperties(
            latex="y = x^2 + 2x + 1",
            equation="y = x^2 + 2x + 1",
        ),
        bbox=BBox(x=100, y=50, width=200, height=40),
        confidence=Confidence(value=0.92, source="test", element_type="equation"),
    )


@pytest.fixture
def sample_node_point():
    """Sample point node for testing."""
    return SemanticNode(
        id="node-point-001",
        node_type=NodeType.POINT,
        label="A",
        properties=NodeProperties(
            coordinates={"x": 2.0, "y": 3.0},
            point_label="A",
        ),
        bbox=BBox(x=200, y=300, width=20, height=20),
        confidence=Confidence(value=0.88, source="test", element_type="point"),
    )


@pytest.fixture
def sample_node_line():
    """Sample line node for testing."""
    return SemanticNode(
        id="node-line-001",
        node_type=NodeType.LINE,
        label="Line y = 2x + 1",
        properties=NodeProperties(
            slope=2.0,
            y_intercept=1.0,
            equation="y = 2x + 1",
        ),
        bbox=BBox(x=100, y=100, width=300, height=200),
        confidence=Confidence(value=0.85, source="test", element_type="line"),
    )


@pytest.fixture
def sample_semantic_graph(sample_node_equation, sample_node_point, sample_node_line):
    """Sample semantic graph for testing."""
    return SemanticGraph(
        image_id="test-image-001",
        alignment_report_id="alignment-001",
        provenance=Provenance(
            stage=PipelineStage.SEMANTIC_GRAPH,
            model="graph-builder-v2",
            processing_time_ms=150.0,
        ),
        nodes=[sample_node_equation, sample_node_point, sample_node_line],
        edges=[
            SemanticEdge(
                id="edge-001",
                source_id="node-point-001",
                target_id="node-line-001",
                edge_type=EdgeType.LIES_ON,
                confidence=Confidence(value=0.80, source="test", element_type="edge"),
            ),
        ],
    )


@pytest.fixture
def empty_semantic_graph():
    """Semantic graph with no nodes."""
    return SemanticGraph(
        image_id="test-empty-001",
        alignment_report_id="alignment-empty",
        provenance=Provenance(
            stage=PipelineStage.SEMANTIC_GRAPH,
            model="graph-builder-v2",
        ),
        nodes=[],
        edges=[],
    )


@pytest.fixture
def low_confidence_graph():
    """Semantic graph with low overall confidence."""
    low_conf_node = SemanticNode(
        id="node-low-001",
        node_type=NodeType.VARIABLE,
        label="x",
        properties=NodeProperties(latex="x"),
        confidence=Confidence(value=0.25, source="test", element_type="variable"),
    )
    return SemanticGraph(
        image_id="test-low-conf-001",
        alignment_report_id="alignment-low",
        provenance=Provenance(
            stage=PipelineStage.SEMANTIC_GRAPH,
            model="graph-builder-v2",
        ),
        nodes=[low_conf_node],
        edges=[],
    )


@pytest.fixture
def sample_regeneration_output_latex():
    """Sample LaTeX regeneration output."""
    return RegenerationOutput(
        format=OutputFormat.LATEX,
        content="\\[y = x^2 + 2x + 1\\]",
        confidence=0.90,
        generation_time_ms=50.0,
        element_count=3,
        completeness_score=0.95,
    )


@pytest.fixture
def sample_regeneration_output_svg():
    """Sample SVG regeneration output."""
    return RegenerationOutput(
        format=OutputFormat.SVG,
        content='<svg xmlns="http://www.w3.org/2000/svg">...</svg>',
        confidence=0.85,
        generation_time_ms=75.0,
        element_count=3,
        completeness_score=0.90,
    )


@pytest.fixture
def sample_regeneration_spec(sample_regeneration_output_latex, sample_regeneration_output_svg):
    """Sample RegenerationSpec for testing."""
    return RegenerationSpec(
        image_id="test-image-001",
        semantic_graph_id="graph_test-image-001",
        outputs=[sample_regeneration_output_latex, sample_regeneration_output_svg],
        processing_time_ms=125.0,
    )


@pytest.fixture
def mock_engine_result(sample_regeneration_spec):
    """Mock EngineResult for testing."""
    return EngineResult(
        spec=sample_regeneration_spec,
        success=True,
        processing_time_ms=125.0,
        warnings=[],
        errors=[],
    )


# =============================================================================
# Initialization Tests
# =============================================================================

class TestRegenerationStageInit:
    """Test RegenerationStage initialization."""

    def test_default_init(self):
        """Test default initialization."""
        stage = RegenerationStage()

        assert stage.config is not None
        assert stage.config.output_formats == ["latex", "svg"]
        assert stage.config.enable_delta_comparison is True
        assert stage.config.min_confidence_threshold == 0.60
        assert stage.engine is not None

    def test_init_with_config(self):
        """Test initialization with custom config."""
        config = RegenerationStageConfig(
            output_formats=["latex", "tikz"],
            enable_delta_comparison=False,
            min_confidence_threshold=0.75,
            fail_on_low_confidence=True,
        )
        stage = RegenerationStage(config=config)

        assert stage.config.output_formats == ["latex", "tikz"]
        assert stage.config.enable_delta_comparison is False
        assert stage.config.min_confidence_threshold == 0.75
        assert stage.config.fail_on_low_confidence is True

    def test_init_with_custom_engine(self):
        """Test initialization with custom engine."""
        mock_engine = MagicMock(spec=RegenerationEngine)
        stage = RegenerationStage(engine=mock_engine)

        assert stage.engine is mock_engine

    def test_stage_name(self):
        """Test stage_name property returns REGENERATION."""
        stage = RegenerationStage()

        assert stage.stage_name == PipelineStage.REGENERATION

    def test_factory_function_default(self):
        """Test create_regeneration_stage factory with defaults."""
        stage = create_regeneration_stage()

        assert isinstance(stage, RegenerationStage)
        assert stage.config.output_formats == ["latex", "svg"]

    def test_factory_function_with_kwargs(self):
        """Test create_regeneration_stage with kwargs."""
        stage = create_regeneration_stage(
            output_formats=["latex", "svg", "tikz"],
            min_confidence_threshold=0.70,
        )

        assert isinstance(stage, RegenerationStage)
        assert stage.config.output_formats == ["latex", "svg", "tikz"]
        assert stage.config.min_confidence_threshold == 0.70


# =============================================================================
# Validation Tests
# =============================================================================

class TestRegenerationStageValidation:
    """Test RegenerationStage input validation."""

    def test_validate_valid_graph(self, sample_semantic_graph):
        """Test validation passes for valid graph."""
        stage = RegenerationStage()

        result = stage.validate(sample_semantic_graph)

        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_validate_none_input(self):
        """Test validation fails for None input."""
        stage = RegenerationStage()

        result = stage.validate(None)

        assert result.is_valid is False
        assert len(result.errors) == 1
        assert "SemanticGraph is required" in result.errors[0]

    def test_validate_empty_graph(self, empty_semantic_graph):
        """Test validation fails for empty graph."""
        stage = RegenerationStage()

        result = stage.validate(empty_semantic_graph)

        assert result.is_valid is False
        assert any("at least one node" in e for e in result.errors)

    def test_validate_low_confidence_warning(self, low_confidence_graph):
        """Test validation warns for low confidence graph."""
        stage = RegenerationStage()

        result = stage.validate(low_confidence_graph)

        # Should be valid but with warning
        assert result.is_valid is True
        assert len(result.warnings) > 0
        assert any("Low input graph confidence" in w for w in result.warnings)


# =============================================================================
# Execution Tests
# =============================================================================

class TestRegenerationStageExecution:
    """Test RegenerationStage execution."""

    @pytest.mark.asyncio
    async def test_execute_async_success(self, sample_semantic_graph, mock_engine_result):
        """Test successful async execution."""
        mock_engine = MagicMock(spec=RegenerationEngine)
        mock_engine.regenerate = AsyncMock(return_value=mock_engine_result)

        stage = RegenerationStage(engine=mock_engine)
        result = await stage._execute_async(sample_semantic_graph)

        assert isinstance(result, RegenerationSpec)
        assert result.image_id == "test-image-001"
        mock_engine.regenerate.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_async_with_original_content(self, sample_semantic_graph, mock_engine_result):
        """Test execution with original content for delta comparison."""
        mock_engine = MagicMock(spec=RegenerationEngine)
        mock_engine.regenerate = AsyncMock(return_value=mock_engine_result)

        stage = RegenerationStage(engine=mock_engine)
        result = await stage._execute_async(
            sample_semantic_graph,
            original_content="y = x^2",
        )

        assert isinstance(result, RegenerationSpec)
        # Verify original_content was passed
        call_kwargs = mock_engine.regenerate.call_args.kwargs
        assert call_kwargs.get("original_content") == "y = x^2"

    @pytest.mark.asyncio
    async def test_execute_async_engine_failure(self, sample_semantic_graph):
        """Test execution handles engine failure."""
        mock_engine = MagicMock(spec=RegenerationEngine)
        mock_engine.regenerate = AsyncMock(
            side_effect=RegenerationError("Engine failed", details={})
        )

        stage = RegenerationStage(engine=mock_engine)

        with pytest.raises(StageExecutionError) as exc_info:
            await stage._execute_async(sample_semantic_graph)

        assert "Engine failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_run_async_full_lifecycle(self, sample_semantic_graph, mock_engine_result):
        """Test full run_async lifecycle."""
        mock_engine = MagicMock(spec=RegenerationEngine)
        mock_engine.regenerate = AsyncMock(return_value=mock_engine_result)

        stage = RegenerationStage(engine=mock_engine)
        result = await stage.run_async(sample_semantic_graph)

        assert isinstance(result, StageResult)
        assert result.is_valid is True
        assert result.output is not None
        assert result.timing is not None
        assert result.metrics is not None

    @pytest.mark.asyncio
    async def test_run_async_validation_failure(self, empty_semantic_graph):
        """Test run_async with validation failure."""
        stage = RegenerationStage()
        result = await stage.run_async(empty_semantic_graph)

        assert result.is_valid is False
        assert result.output is None
        assert len(result.errors) > 0


# =============================================================================
# Metrics Tests
# =============================================================================

class TestRegenerationStageMetrics:
    """Test RegenerationStage metrics collection."""

    def test_get_metrics_success(self, sample_regeneration_spec):
        """Test metrics collection for successful regeneration."""
        stage = RegenerationStage()

        metrics = stage.get_metrics(sample_regeneration_spec)

        assert isinstance(metrics, StageMetrics)
        assert metrics.stage == PipelineStage.REGENERATION
        assert metrics.success is True
        assert "output_formats" in metrics.custom_metrics
        assert metrics.custom_metrics["output_formats"] == 2
        assert "overall_confidence" in metrics.custom_metrics

    def test_get_metrics_with_delta(self, sample_regeneration_spec):
        """Test metrics include delta report info when present."""
        delta_report = DeltaReport(
            similarity_score=0.85,
            unchanged_count=3,
        )
        sample_regeneration_spec.delta_report = delta_report

        stage = RegenerationStage()
        metrics = stage.get_metrics(sample_regeneration_spec)

        assert metrics.custom_metrics["has_delta_report"] is True
        assert metrics.custom_metrics["delta_similarity"] == 0.85

    def test_get_metrics_none_output(self):
        """Test metrics for None output."""
        stage = RegenerationStage()

        metrics = stage.get_metrics(None)

        assert metrics.success is False
        assert metrics.elements_processed == 0


# =============================================================================
# Configuration Tests
# =============================================================================

class TestRegenerationStageConfig:
    """Test RegenerationStageConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = RegenerationStageConfig()

        assert config.output_formats == ["latex", "svg"]
        assert config.enable_delta_comparison is True
        assert config.min_confidence_threshold == 0.60
        assert config.fail_on_low_confidence is False
        assert config.include_intermediate_results is True

    def test_custom_values(self):
        """Test configuration with custom values."""
        config = RegenerationStageConfig(
            output_formats=["latex", "tikz", "mathml"],
            enable_delta_comparison=False,
            min_confidence_threshold=0.80,
        )

        assert config.output_formats == ["latex", "tikz", "mathml"]
        assert config.enable_delta_comparison is False
        assert config.min_confidence_threshold == 0.80

    def test_to_engine_config(self):
        """Test conversion to engine config."""
        config = RegenerationStageConfig(
            output_formats=["latex", "svg"],
            min_confidence_threshold=0.70,
        )

        engine_config = config.to_engine_config()

        assert OutputFormat.LATEX in engine_config.default_formats
        assert OutputFormat.SVG in engine_config.default_formats
        assert engine_config.min_confidence_threshold == 0.70

    def test_to_engine_config_invalid_format(self):
        """Test conversion handles invalid formats gracefully."""
        config = RegenerationStageConfig(
            output_formats=["latex", "invalid_format", "svg"],
        )

        engine_config = config.to_engine_config()

        # Invalid format should be skipped
        assert len(engine_config.default_formats) == 2
        assert OutputFormat.LATEX in engine_config.default_formats
        assert OutputFormat.SVG in engine_config.default_formats
