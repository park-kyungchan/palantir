"""
Tests for Stage B (Text Parse) - TextParseStage.

Tests for:
- TextParseStage initialization and configuration
- Input validation logic
- Mathpix API integration (mocked)
- Error handling for various failure scenarios
- Metrics collection

Schema Version: 2.0.0
"""

import asyncio
from pathlib import Path
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mathpix_pipeline.schemas.common import PipelineStage
from mathpix_pipeline.schemas.ingestion import (
    IngestionSpec,
    ImageMetadata,
    ValidationResult as IngestionValidationResult,
    create_ingestion_spec,
)
from mathpix_pipeline.schemas.text_spec import (
    TextSpec,
    ContentFlags,
    VisionParseTrigger,
    WritingStyle,
)
from mathpix_pipeline.clients.mathpix import (
    MathpixClient,
    MathpixConfig,
    MathpixError,
    InvalidImageError,
    RateLimitError,
    TimeoutError as MathpixTimeoutError,
    ServerError,
)
from mathpix_pipeline.stages.text_parse_stage import (
    TextParseStage,
    TextParseStageConfig,
)
from mathpix_pipeline.stages.base import (
    StageExecutionError,
    ValidationResult,
)

from tests.fixtures.mocks.mathpix_responses import (
    SIMPLE_EQUATION_RESPONSE,
    QUADRATIC_GRAPH_RESPONSE,
    GEOMETRY_DIAGRAM_RESPONSE,
    HANDWRITTEN_MATH_RESPONSE,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mathpix_config() -> MathpixConfig:
    """Create test Mathpix configuration."""
    return MathpixConfig(
        app_id="test-app-id",
        app_key="test-app-key",
        base_url="https://api.mathpix.com/v3",
        timeout_seconds=30.0,
    )


@pytest.fixture
def stage_config(mathpix_config: MathpixConfig) -> TextParseStageConfig:
    """Create test stage configuration."""
    return TextParseStageConfig(
        mathpix_config=mathpix_config,
        require_stored_path=False,  # Relaxed for testing
        require_validation_passed=True,
    )


@pytest.fixture
def valid_ingestion_spec(tmp_path: Path) -> IngestionSpec:
    """Create a valid IngestionSpec for testing."""
    # Create a test image file
    image_path = tmp_path / "test_image.png"
    image_path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)

    return create_ingestion_spec(
        image_id="test-image-001",
        format="png",
        width=800,
        height=600,
        file_size_bytes=1024,
        color_mode="RGB",
        source_path=str(image_path),
        stored_path=str(image_path),
        is_valid=True,
        checks_passed=["format_check", "size_check"],
        math_confidence=0.8,
    )


@pytest.fixture
def mock_text_spec() -> TextSpec:
    """Create a mock TextSpec for testing."""
    return TextSpec(
        image_id="test-image-001",
        content_flags=ContentFlags(
            contains_equation=True,
            contains_text=True,
        ),
        text="y = 2x + 3",
        latex="y = 2x + 3",
        confidence=0.95,
        writing_style=WritingStyle.PRINTED,
        processing_time_ms=150.0,
    )


# =============================================================================
# Configuration Tests
# =============================================================================

class TestTextParseStageConfig:
    """Tests for TextParseStageConfig."""

    def test_config_defaults(self):
        """Test default configuration values."""
        config = TextParseStageConfig()

        assert config.mathpix_config is None
        assert config.require_stored_path is True
        assert config.min_image_size == 10
        assert config.max_image_size == 10000
        assert config.require_validation_passed is True

    def test_config_custom_values(self, mathpix_config: MathpixConfig):
        """Test custom configuration values."""
        config = TextParseStageConfig(
            mathpix_config=mathpix_config,
            require_stored_path=False,
            min_image_size=50,
            max_image_size=5000,
            require_validation_passed=False,
        )

        assert config.mathpix_config == mathpix_config
        assert config.require_stored_path is False
        assert config.min_image_size == 50
        assert config.max_image_size == 5000
        assert config.require_validation_passed is False


# =============================================================================
# Stage Initialization Tests
# =============================================================================

class TestTextParseStageInit:
    """Tests for TextParseStage initialization."""

    def test_stage_name(self, stage_config: TextParseStageConfig):
        """Test stage name property."""
        stage = TextParseStage(config=stage_config)
        assert stage.stage_name == PipelineStage.TEXT_PARSE

    def test_config_property(self, stage_config: TextParseStageConfig):
        """Test config property returns typed config."""
        stage = TextParseStage(config=stage_config)
        assert stage.config == stage_config
        assert isinstance(stage.config, TextParseStageConfig)

    def test_init_with_client(
        self,
        stage_config: TextParseStageConfig,
        mathpix_config: MathpixConfig,
    ):
        """Test initialization with custom client."""
        client = MathpixClient(mathpix_config)
        stage = TextParseStage(config=stage_config, client=client)

        assert stage.client == client

    def test_init_without_config(self):
        """Test initialization with default config."""
        stage = TextParseStage()
        assert stage.config is not None
        assert isinstance(stage.config, TextParseStageConfig)


# =============================================================================
# Validation Tests
# =============================================================================

class TestTextParseStageValidation:
    """Tests for TextParseStage input validation."""

    def test_validate_none_input(self, stage_config: TextParseStageConfig):
        """Test validation fails for None input."""
        stage = TextParseStage(config=stage_config)
        result = stage.validate(None)

        assert result.is_valid is False
        assert "required" in result.errors[0].lower()

    def test_validate_missing_metadata(self, stage_config: TextParseStageConfig):
        """Test validation fails for missing metadata."""
        stage = TextParseStage(config=stage_config)

        # Create a spec with None metadata by using object.__setattr__
        # to bypass Pydantic validation for testing purposes
        spec = IngestionSpec(
            image_id="test-id",
            metadata=ImageMetadata(
                format="png",
                width=800,
                height=600,
                color_mode="RGB",
                file_size_bytes=1024,
            ),
            validation=IngestionValidationResult(is_valid=True),
        )
        # Force metadata to None for testing
        object.__setattr__(spec, 'metadata', None)
        result = stage.validate(spec)

        assert result.is_valid is False
        assert "metadata" in result.errors[0].lower()

    def test_validate_image_too_small(self, stage_config: TextParseStageConfig):
        """Test validation fails for images below minimum size."""
        stage = TextParseStage(config=stage_config)

        spec = IngestionSpec(
            image_id="small-image",
            metadata=ImageMetadata(
                format="png",
                width=5,  # Below minimum
                height=600,
                color_mode="RGB",
                file_size_bytes=100,
            ),
            validation=IngestionValidationResult(is_valid=True),
        )
        result = stage.validate(spec)

        assert result.is_valid is False
        assert "width" in result.errors[0].lower()
        assert "below minimum" in result.errors[0].lower()

    def test_validate_image_too_large(self, stage_config: TextParseStageConfig):
        """Test validation fails for images above maximum size."""
        stage = TextParseStage(config=stage_config)

        spec = IngestionSpec(
            image_id="large-image",
            metadata=ImageMetadata(
                format="png",
                width=800,
                height=15000,  # Above maximum
                color_mode="RGB",
                file_size_bytes=100000000,
            ),
            validation=IngestionValidationResult(is_valid=True),
        )
        result = stage.validate(spec)

        assert result.is_valid is False
        assert "height" in result.errors[0].lower()
        assert "exceeds maximum" in result.errors[0].lower()

    def test_validate_failed_ingestion_validation(
        self,
        stage_config: TextParseStageConfig,
    ):
        """Test validation fails when ingestion validation failed."""
        stage = TextParseStage(config=stage_config)

        spec = IngestionSpec(
            image_id="failed-validation",
            metadata=ImageMetadata(
                format="png",
                width=800,
                height=600,
                color_mode="RGB",
                file_size_bytes=1024,
            ),
            validation=IngestionValidationResult(
                is_valid=False,
                checks_failed=["corrupt_file"],
            ),
        )
        result = stage.validate(spec)

        assert result.is_valid is False
        assert "validation failed" in result.errors[0].lower()

    def test_validate_low_math_confidence_warning(
        self,
        stage_config: TextParseStageConfig,
    ):
        """Test validation warns for low math content confidence."""
        stage_config.require_validation_passed = False
        stage = TextParseStage(config=stage_config)

        spec = IngestionSpec(
            image_id="low-confidence",
            metadata=ImageMetadata(
                format="png",
                width=800,
                height=600,
                color_mode="RGB",
                file_size_bytes=1024,
            ),
            validation=IngestionValidationResult(is_valid=True),
            math_content_confidence=0.1,  # Very low
        )
        result = stage.validate(spec)

        assert result.is_valid is True
        assert len(result.warnings) > 0
        assert "low math content confidence" in result.warnings[0].lower()

    def test_validate_success(
        self,
        stage_config: TextParseStageConfig,
        valid_ingestion_spec: IngestionSpec,
    ):
        """Test successful validation."""
        stage = TextParseStage(config=stage_config)
        result = stage.validate(valid_ingestion_spec)

        assert result.is_valid is True
        assert len(result.errors) == 0


# =============================================================================
# Execution Tests (Mocked API)
# =============================================================================

class TestTextParseStageExecution:
    """Tests for TextParseStage execution with mocked Mathpix API."""

    @pytest.mark.asyncio
    async def test_execute_success(
        self,
        stage_config: TextParseStageConfig,
        valid_ingestion_spec: IngestionSpec,
        mock_text_spec: TextSpec,
    ):
        """Test successful text parsing execution."""
        # Create mock client
        mock_client = MagicMock(spec=MathpixClient)
        mock_client.process_image = AsyncMock(return_value=mock_text_spec)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        stage = TextParseStage(config=stage_config, client=mock_client)
        result = await stage.run_async(valid_ingestion_spec)

        assert result.is_valid is True
        assert result.output is not None
        assert result.output.image_id == mock_text_spec.image_id

    @pytest.mark.asyncio
    async def test_execute_with_diagram_triggers(
        self,
        stage_config: TextParseStageConfig,
        valid_ingestion_spec: IngestionSpec,
    ):
        """Test execution with diagram content triggers Stage C."""
        # Create TextSpec with diagram flags
        diagram_text_spec = TextSpec(
            image_id=valid_ingestion_spec.image_id,
            content_flags=ContentFlags(
                contains_equation=True,
                contains_diagram=True,
                contains_graph=True,
            ),
            vision_parse_triggers=[
                VisionParseTrigger.DIAGRAM_EXTRACTION,
                VisionParseTrigger.GRAPH_ANALYSIS,
            ],
            text="y = x^2",
            latex="y = x^2",
            confidence=0.94,
        )

        mock_client = MagicMock(spec=MathpixClient)
        mock_client.process_image = AsyncMock(return_value=diagram_text_spec)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        stage = TextParseStage(config=stage_config, client=mock_client)
        result = await stage.run_async(valid_ingestion_spec)

        assert result.is_valid is True
        assert result.output.content_flags.contains_diagram is True
        assert result.output.should_trigger_vision_parse() is True
        assert VisionParseTrigger.DIAGRAM_EXTRACTION in result.output.vision_parse_triggers

    @pytest.mark.asyncio
    async def test_execute_invalid_image_error(
        self,
        stage_config: TextParseStageConfig,
        valid_ingestion_spec: IngestionSpec,
    ):
        """Test handling of InvalidImageError."""
        mock_client = MagicMock(spec=MathpixClient)
        mock_client.process_image = AsyncMock(
            side_effect=InvalidImageError("Corrupt image data")
        )
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        stage = TextParseStage(config=stage_config, client=mock_client)
        result = await stage.run_async(valid_ingestion_spec)

        assert result.is_valid is False
        assert result.output is None
        assert len(result.errors) > 0
        assert "invalid image" in result.errors[0].lower()

    @pytest.mark.asyncio
    async def test_execute_rate_limit_error(
        self,
        stage_config: TextParseStageConfig,
        valid_ingestion_spec: IngestionSpec,
    ):
        """Test handling of RateLimitError."""
        mock_client = MagicMock(spec=MathpixClient)
        mock_client.process_image = AsyncMock(
            side_effect=RateLimitError(retry_after=60)
        )
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        stage = TextParseStage(config=stage_config, client=mock_client)
        result = await stage.run_async(valid_ingestion_spec)

        assert result.is_valid is False
        assert "rate limit" in result.errors[0].lower()

    @pytest.mark.asyncio
    async def test_execute_timeout_error(
        self,
        stage_config: TextParseStageConfig,
        valid_ingestion_spec: IngestionSpec,
    ):
        """Test handling of TimeoutError."""
        mock_client = MagicMock(spec=MathpixClient)
        mock_client.process_image = AsyncMock(
            side_effect=MathpixTimeoutError("Request timed out", status_code=504)
        )
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        stage = TextParseStage(config=stage_config, client=mock_client)
        result = await stage.run_async(valid_ingestion_spec)

        assert result.is_valid is False
        assert "timeout" in result.errors[0].lower()

    @pytest.mark.asyncio
    async def test_execute_server_error(
        self,
        stage_config: TextParseStageConfig,
        valid_ingestion_spec: IngestionSpec,
    ):
        """Test handling of ServerError."""
        mock_client = MagicMock(spec=MathpixClient)
        mock_client.process_image = AsyncMock(
            side_effect=ServerError("Internal server error", status_code=500)
        )
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        stage = TextParseStage(config=stage_config, client=mock_client)
        result = await stage.run_async(valid_ingestion_spec)

        assert result.is_valid is False
        assert "server error" in result.errors[0].lower()

    @pytest.mark.asyncio
    async def test_execute_no_path_error(
        self,
        stage_config: TextParseStageConfig,
    ):
        """Test error when no image path available."""
        spec = IngestionSpec(
            image_id="no-path",
            metadata=ImageMetadata(
                format="png",
                width=800,
                height=600,
                color_mode="RGB",
                file_size_bytes=1024,
            ),
            validation=IngestionValidationResult(is_valid=True),
            stored_path=None,
            source_path=None,
        )

        mock_client = MagicMock(spec=MathpixClient)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        stage = TextParseStage(config=stage_config, client=mock_client)
        result = await stage.run_async(spec, skip_validation=True)

        assert result.is_valid is False
        assert "no image path" in result.errors[0].lower()


# =============================================================================
# Metrics Tests
# =============================================================================

class TestTextParseStageMetrics:
    """Tests for TextParseStage metrics collection."""

    def test_get_metrics_success(self, stage_config: TextParseStageConfig):
        """Test metrics collection for successful execution."""
        stage = TextParseStage(config=stage_config)

        text_spec = TextSpec(
            image_id="metrics-test",
            content_flags=ContentFlags(
                contains_equation=True,
                contains_diagram=True,
            ),
            vision_parse_triggers=[VisionParseTrigger.DIAGRAM_EXTRACTION],
            text="y = x^2",
            latex="y = x^2",
            confidence=0.95,
            writing_style=WritingStyle.PRINTED,
            processing_time_ms=175.5,
        )

        metrics = stage.get_metrics(text_spec)

        assert metrics.stage == PipelineStage.TEXT_PARSE
        assert metrics.success is True
        assert metrics.custom_metrics["image_id"] == "metrics-test"
        assert metrics.custom_metrics["confidence"] == 0.95
        assert metrics.custom_metrics["contains_diagram"] is True
        assert metrics.custom_metrics["processing_time_ms"] == 175.5
        assert "DIAGRAM_EXTRACTION" in metrics.custom_metrics["vision_parse_triggers"]

    def test_get_metrics_none_output(self, stage_config: TextParseStageConfig):
        """Test metrics collection for None output."""
        stage = TextParseStage(config=stage_config)
        metrics = stage.get_metrics(None)

        assert metrics.stage == PipelineStage.TEXT_PARSE
        assert metrics.success is False
        assert metrics.elements_processed == 0


# =============================================================================
# Integration Tests (Sync Wrapper)
# =============================================================================

class TestTextParseStageSyncExecution:
    """Tests for synchronous execution wrapper."""

    def test_run_sync(
        self,
        stage_config: TextParseStageConfig,
        valid_ingestion_spec: IngestionSpec,
        mock_text_spec: TextSpec,
    ):
        """Test synchronous run method."""
        mock_client = MagicMock(spec=MathpixClient)
        mock_client.process_image = AsyncMock(return_value=mock_text_spec)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        stage = TextParseStage(config=stage_config, client=mock_client)
        result = stage.run(valid_ingestion_spec)

        assert result.is_valid is True
        assert result.output is not None
        assert result.output.image_id == mock_text_spec.image_id


# =============================================================================
# Summary
# =============================================================================

"""
Test Summary:
- Total test functions: 20+
- Coverage areas:
  1. Configuration: defaults, custom values
  2. Initialization: stage_name, config, client
  3. Validation: None input, missing fields, size bounds, validation status
  4. Execution: success, diagram triggers, various error types
  5. Metrics: success case, None output
  6. Sync wrapper: synchronous execution

All tests use mocks for Mathpix API client.
"""
