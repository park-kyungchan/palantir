"""
Tests for Stage H (ExportStage) BaseStage wrapper.

Tests the ExportStage implementation:
- Initialization and configuration
- Input validation
- Execution with mock engine
- Metrics collection
- Error handling
"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from mathpix_pipeline.stages import (
    StageResult,
    StageMetrics,
    ValidationResult,
    StageExecutionError,
)
from mathpix_pipeline.stages.export_stage import (
    ExportStage,
    ExportStageConfig,
    create_export_stage,
)
from mathpix_pipeline.schemas.common import PipelineStage, Provenance, ReviewMetadata
from mathpix_pipeline.schemas.regeneration import (
    OutputFormat,
    RegenerationSpec,
    RegenerationOutput,
)
from mathpix_pipeline.schemas.export import (
    ExportFormat,
    ExportSpec,
    ExportOptions,
    StorageType,
)
from mathpix_pipeline.export.engine import ExportEngine, ExportEngineConfig
from mathpix_pipeline.export.exceptions import ExporterError, ExportPipelineError


# =============================================================================
# Fixtures
# =============================================================================

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
def empty_regeneration_spec():
    """RegenerationSpec with no outputs."""
    return RegenerationSpec(
        image_id="test-empty-001",
        semantic_graph_id="graph-empty",
        outputs=[],
        provenance=Provenance(
            stage=PipelineStage.REGENERATION,
            model="regeneration-engine-v2",
        ),
    )


@pytest.fixture
def low_confidence_regeneration_spec(sample_regeneration_output_latex):
    """RegenerationSpec with low confidence."""
    low_conf_output = RegenerationOutput(
        format=OutputFormat.LATEX,
        content="x",
        confidence=0.25,
        generation_time_ms=10.0,
        element_count=1,
    )
    return RegenerationSpec(
        image_id="test-low-conf-001",
        semantic_graph_id="graph-low-conf",
        outputs=[low_conf_output],
    )


@pytest.fixture
def sample_export_spec_json():
    """Sample JSON ExportSpec."""
    return ExportSpec(
        export_id="export-json-001",
        image_id="test-image-001",
        format=ExportFormat.JSON,
        content_type="application/json",
        file_path="/tmp/exports/test-image-001.json",
        file_size=2048,
        confidence=0.95,
        storage_type=StorageType.LOCAL,
    )


@pytest.fixture
def sample_export_spec_pdf():
    """Sample PDF ExportSpec."""
    return ExportSpec(
        export_id="export-pdf-001",
        image_id="test-image-001",
        format=ExportFormat.PDF,
        content_type="application/pdf",
        file_path="/tmp/exports/test-image-001.pdf",
        file_size=8192,
        confidence=0.90,
        storage_type=StorageType.LOCAL,
    )


@pytest.fixture
def sample_export_specs(sample_export_spec_json, sample_export_spec_pdf):
    """List of sample ExportSpecs."""
    return [sample_export_spec_json, sample_export_spec_pdf]


# =============================================================================
# Initialization Tests
# =============================================================================

class TestExportStageInit:
    """Test ExportStage initialization."""

    def test_default_init(self):
        """Test default initialization."""
        stage = ExportStage()

        assert stage.config is not None
        assert ExportFormat.PDF in stage.config.export_formats
        assert ExportFormat.JSON in stage.config.export_formats
        assert stage.config.parallel_exports is True
        assert stage.engine is not None

    def test_init_with_config(self):
        """Test initialization with custom config."""
        config = ExportStageConfig(
            export_formats=[ExportFormat.LATEX, ExportFormat.SVG],
            parallel_exports=False,
            max_concurrent=2,
            include_metadata=False,
        )
        stage = ExportStage(config=config)

        assert stage.config.export_formats == [ExportFormat.LATEX, ExportFormat.SVG]
        assert stage.config.parallel_exports is False
        assert stage.config.max_concurrent == 2
        assert stage.config.include_metadata is False

    def test_init_with_output_dir(self, tmp_path):
        """Test initialization with custom output directory."""
        config = ExportStageConfig(output_dir=tmp_path)
        stage = ExportStage(config=config)

        assert stage.config.output_dir == tmp_path

    def test_init_with_custom_engine(self):
        """Test initialization with custom engine."""
        mock_engine = MagicMock(spec=ExportEngine)
        mock_engine.get_supported_formats.return_value = [
            ExportFormat.JSON, ExportFormat.PDF
        ]
        stage = ExportStage(engine=mock_engine)

        assert stage.engine is mock_engine

    def test_stage_name(self):
        """Test stage_name property returns EXPORT."""
        stage = ExportStage()

        assert stage.stage_name == PipelineStage.EXPORT

    def test_factory_function_default(self):
        """Test create_export_stage factory with defaults."""
        stage = create_export_stage()

        assert isinstance(stage, ExportStage)
        assert ExportFormat.PDF in stage.config.export_formats

    def test_factory_function_with_kwargs(self):
        """Test create_export_stage with kwargs."""
        stage = create_export_stage(
            export_formats=[ExportFormat.JSON, ExportFormat.LATEX],
            parallel_exports=False,
        )

        assert isinstance(stage, ExportStage)
        assert ExportFormat.JSON in stage.config.export_formats
        assert ExportFormat.LATEX in stage.config.export_formats
        assert stage.config.parallel_exports is False

    def test_factory_function_with_string_formats(self):
        """Test create_export_stage with string format names."""
        stage = create_export_stage(
            export_formats=["json", "pdf"],
        )

        assert isinstance(stage, ExportStage)
        assert ExportFormat.JSON in stage.config.export_formats
        assert ExportFormat.PDF in stage.config.export_formats


# =============================================================================
# Validation Tests
# =============================================================================

class TestExportStageValidation:
    """Test ExportStage input validation."""

    def test_validate_valid_spec(self, sample_regeneration_spec):
        """Test validation passes for valid spec."""
        mock_engine = MagicMock(spec=ExportEngine)
        mock_engine.get_supported_formats.return_value = [
            ExportFormat.JSON, ExportFormat.PDF
        ]
        stage = ExportStage(engine=mock_engine)

        result = stage.validate(sample_regeneration_spec)

        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_validate_none_input(self):
        """Test validation fails for None input."""
        stage = ExportStage()

        result = stage.validate(None)

        assert result.is_valid is False
        assert len(result.errors) == 1
        assert "RegenerationSpec is required" in result.errors[0]

    def test_validate_empty_outputs(self, empty_regeneration_spec):
        """Test validation fails for spec with no outputs."""
        stage = ExportStage()

        result = stage.validate(empty_regeneration_spec)

        assert result.is_valid is False
        assert any("at least one output" in e for e in result.errors)

    def test_validate_low_confidence_warning(self, low_confidence_regeneration_spec):
        """Test validation warns for low confidence spec."""
        mock_engine = MagicMock(spec=ExportEngine)
        mock_engine.get_supported_formats.return_value = [
            ExportFormat.JSON, ExportFormat.PDF
        ]
        stage = ExportStage(engine=mock_engine)

        result = stage.validate(low_confidence_regeneration_spec)

        # Should be valid but with warning
        assert result.is_valid is True
        assert len(result.warnings) > 0
        assert any("Low regeneration confidence" in w for w in result.warnings)

    def test_validate_missing_image_id(self):
        """Test validation fails for missing image_id."""
        spec = RegenerationSpec(
            image_id="",
            semantic_graph_id="graph-001",
            outputs=[
                RegenerationOutput(
                    format=OutputFormat.LATEX,
                    content="x",
                    confidence=0.9,
                    generation_time_ms=10.0,
                )
            ],
        )
        stage = ExportStage()

        result = stage.validate(spec)

        assert result.is_valid is False
        assert any("image_id" in e for e in result.errors)


# =============================================================================
# Execution Tests
# =============================================================================

class TestExportStageExecution:
    """Test ExportStage execution."""

    @pytest.mark.asyncio
    async def test_execute_async_success(self, sample_regeneration_spec, sample_export_specs):
        """Test successful async execution."""
        mock_engine = MagicMock(spec=ExportEngine)
        mock_engine.export_async = AsyncMock(return_value=sample_export_specs)
        mock_engine.get_supported_formats.return_value = [
            ExportFormat.JSON, ExportFormat.PDF
        ]

        stage = ExportStage(engine=mock_engine)
        result = await stage._execute_async(sample_regeneration_spec)

        assert isinstance(result, list)
        assert len(result) == 2
        mock_engine.export_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_async_sequential(self, sample_regeneration_spec, sample_export_specs):
        """Test sequential execution when parallel disabled."""
        mock_engine = MagicMock(spec=ExportEngine)
        mock_engine.export = MagicMock(return_value=sample_export_specs)
        mock_engine.get_supported_formats.return_value = [
            ExportFormat.JSON, ExportFormat.PDF
        ]

        config = ExportStageConfig(parallel_exports=False)
        stage = ExportStage(config=config, engine=mock_engine)
        result = await stage._execute_async(sample_regeneration_spec)

        assert isinstance(result, list)
        assert len(result) == 2
        mock_engine.export.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_async_with_options(self, sample_regeneration_spec, sample_export_specs):
        """Test execution with custom export options."""
        mock_engine = MagicMock(spec=ExportEngine)
        mock_engine.export_async = AsyncMock(return_value=sample_export_specs)
        mock_engine.get_supported_formats.return_value = [
            ExportFormat.JSON, ExportFormat.PDF
        ]

        stage = ExportStage(engine=mock_engine)
        options = ExportOptions(include_metadata=False, compress=True)
        result = await stage._execute_async(
            sample_regeneration_spec,
            export_options=options,
        )

        assert isinstance(result, list)
        # Verify options were passed
        call_kwargs = mock_engine.export_async.call_args.kwargs
        assert call_kwargs.get("options") is options

    @pytest.mark.asyncio
    async def test_execute_async_pipeline_error(self, sample_regeneration_spec):
        """Test execution handles pipeline error."""
        mock_engine = MagicMock(spec=ExportEngine)
        mock_engine.export_async = AsyncMock(
            side_effect=ExportPipelineError(
                "All exports failed",
                stage="export",
            )
        )
        mock_engine.get_supported_formats.return_value = [
            ExportFormat.JSON, ExportFormat.PDF
        ]

        stage = ExportStage(engine=mock_engine)

        with pytest.raises(StageExecutionError) as exc_info:
            await stage._execute_async(sample_regeneration_spec)

        assert "All exports failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_execute_async_exporter_error(self, sample_regeneration_spec):
        """Test execution handles exporter error."""
        mock_engine = MagicMock(spec=ExportEngine)
        mock_engine.export_async = AsyncMock(
            side_effect=ExporterError("PDF export failed", exporter_type="pdf")
        )
        mock_engine.get_supported_formats.return_value = [
            ExportFormat.JSON, ExportFormat.PDF
        ]

        stage = ExportStage(engine=mock_engine)

        with pytest.raises(StageExecutionError) as exc_info:
            await stage._execute_async(sample_regeneration_spec)

        assert "Exporter error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_run_async_full_lifecycle(self, sample_regeneration_spec, sample_export_specs):
        """Test full run_async lifecycle."""
        mock_engine = MagicMock(spec=ExportEngine)
        mock_engine.export_async = AsyncMock(return_value=sample_export_specs)
        mock_engine.get_supported_formats.return_value = [
            ExportFormat.JSON, ExportFormat.PDF
        ]

        stage = ExportStage(engine=mock_engine)
        result = await stage.run_async(sample_regeneration_spec)

        assert isinstance(result, StageResult)
        assert result.is_valid is True
        assert result.output is not None
        assert len(result.output) == 2
        assert result.timing is not None
        assert result.metrics is not None

    @pytest.mark.asyncio
    async def test_run_async_validation_failure(self, empty_regeneration_spec):
        """Test run_async with validation failure."""
        stage = ExportStage()
        result = await stage.run_async(empty_regeneration_spec)

        assert result.is_valid is False
        assert result.output is None
        assert len(result.errors) > 0


# =============================================================================
# Metrics Tests
# =============================================================================

class TestExportStageMetrics:
    """Test ExportStage metrics collection."""

    def test_get_metrics_success(self, sample_export_specs):
        """Test metrics collection for successful export."""
        stage = ExportStage()

        metrics = stage.get_metrics(sample_export_specs)

        assert isinstance(metrics, StageMetrics)
        assert metrics.stage == PipelineStage.EXPORT
        assert metrics.success is True
        assert metrics.elements_processed == 2
        assert "format_count" in metrics.custom_metrics
        assert metrics.custom_metrics["format_count"] == 2
        assert "total_file_size_bytes" in metrics.custom_metrics
        assert metrics.custom_metrics["total_file_size_bytes"] == 10240  # 2048 + 8192

    def test_get_metrics_per_format(self, sample_export_specs):
        """Test metrics include per-format data."""
        stage = ExportStage()

        metrics = stage.get_metrics(sample_export_specs)

        assert "json_size_bytes" in metrics.custom_metrics
        assert "pdf_size_bytes" in metrics.custom_metrics
        assert metrics.custom_metrics["json_size_bytes"] == 2048
        assert metrics.custom_metrics["pdf_size_bytes"] == 8192

    def test_get_metrics_empty_output(self):
        """Test metrics for empty output."""
        stage = ExportStage()

        metrics = stage.get_metrics([])

        assert metrics.success is False
        assert metrics.elements_processed == 0

    def test_get_metrics_none_output(self):
        """Test metrics for None output."""
        stage = ExportStage()

        metrics = stage.get_metrics(None)

        assert metrics.success is False
        assert metrics.elements_processed == 0


# =============================================================================
# Configuration Tests
# =============================================================================

class TestExportStageConfig:
    """Test ExportStageConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = ExportStageConfig()

        assert ExportFormat.PDF in config.export_formats
        assert ExportFormat.JSON in config.export_formats
        assert config.output_dir is None
        assert config.parallel_exports is True
        assert config.max_concurrent == 4
        assert config.include_metadata is True
        assert config.compress is False

    def test_custom_values(self):
        """Test configuration with custom values."""
        config = ExportStageConfig(
            export_formats=[ExportFormat.LATEX, ExportFormat.SVG],
            output_dir=Path("/tmp/exports"),
            parallel_exports=False,
            max_concurrent=2,
        )

        assert config.export_formats == [ExportFormat.LATEX, ExportFormat.SVG]
        assert config.output_dir == Path("/tmp/exports")
        assert config.parallel_exports is False
        assert config.max_concurrent == 2

    def test_to_engine_config(self):
        """Test conversion to engine config."""
        config = ExportStageConfig(
            export_formats=[ExportFormat.JSON, ExportFormat.PDF],
            output_dir=Path("/tmp/exports"),
            parallel_exports=True,
            max_concurrent=8,
        )

        engine_config = config.to_engine_config()

        assert ExportFormat.JSON in engine_config.default_formats
        assert ExportFormat.PDF in engine_config.default_formats
        assert engine_config.output_dir == Path("/tmp/exports")
        assert engine_config.parallel_exports is True
        assert engine_config.max_concurrent == 8

    def test_to_engine_config_default_output_dir(self):
        """Test engine config uses default output dir when not specified."""
        config = ExportStageConfig(output_dir=None)

        engine_config = config.to_engine_config()

        assert engine_config.output_dir == Path("./exports")
