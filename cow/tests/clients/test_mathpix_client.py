"""
Tests for Stage B (Text Parse) - Mathpix Client.

Tests for:
- MathpixClient API integration
- Response parsing and conversion
- Error handling and retries
- Content flag detection
- Vision parse trigger logic

Schema Version: 2.0.0
"""

import asyncio
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from mathpix_pipeline.clients.mathpix import (
    # Client
    MathpixClient,
    MathpixConfig,
    RetryConfig,
    # Exceptions
    MathpixError,
    RateLimitError,
    TimeoutError,
    InvalidImageError,
    ServerError,
    # Helper functions
    detection_map_to_content_flags,
    should_trigger_vision_parse,
    line_data_to_segments,
    extract_equations,
    parse_detection_regions,
    detect_writing_style,
)
from mathpix_pipeline.schemas import (
    BBox,
    ContentFlags,
    TextSpec,
    VisionParseTrigger,
    WritingStyle,
    PipelineStage,
)

# Import mock responses
from tests.fixtures.mocks.mathpix_responses import (
    SIMPLE_EQUATION_RESPONSE,
    QUADRATIC_GRAPH_RESPONSE,
    GEOMETRY_DIAGRAM_RESPONSE,
    COMPLEX_CALCULUS_RESPONSE,
    HANDWRITTEN_MATH_RESPONSE,
    TRIG_GRAPH_RESPONSE,
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
        retry=RetryConfig(max_attempts=3, base_delay_ms=100),
    )


@pytest.fixture
def sample_image_bytes() -> bytes:
    """Sample image bytes for testing."""
    # Simple PNG header + minimal data
    return b"\x89PNG\r\n\x1a\n" + b"\x00" * 100


# =============================================================================
# Content Flags Conversion Tests
# =============================================================================

class TestContentFlagsConversion:
    """Tests for detection_map to ContentFlags conversion."""

    def test_detection_map_all_true(self):
        """Test conversion with all flags set."""
        detection_map = {
            "contains_math": 1,
            "is_text_only": 0,
            "contains_diagram": 1,
            "contains_graph": 1,
            "contains_geometry": 1,
            "contains_table": 1,
            "is_handwritten": 1,
        }

        flags = detection_map_to_content_flags(detection_map)

        assert flags.contains_equation is True
        assert flags.contains_text is True
        assert flags.contains_diagram is True
        assert flags.contains_graph is True
        assert flags.contains_geometry is True
        assert flags.contains_table is True
        assert flags.contains_handwriting is True

    def test_detection_map_all_false(self):
        """Test conversion with all flags unset."""
        detection_map = {
            "contains_math": 0,
            "is_text_only": 1,
            "contains_diagram": 0,
            "contains_graph": 0,
            "contains_geometry": 0,
            "contains_table": 0,
            "is_handwritten": 0,
        }

        flags = detection_map_to_content_flags(detection_map)

        assert flags.contains_equation is False
        assert flags.contains_text is False
        assert flags.contains_diagram is False
        assert flags.contains_graph is False
        assert flags.contains_geometry is False
        assert flags.contains_table is False
        assert flags.contains_handwriting is False

    def test_detection_map_partial(self):
        """Test conversion with some flags set."""
        detection_map = {
            "contains_math": 1,
            "contains_diagram": 1,
        }

        flags = detection_map_to_content_flags(detection_map)

        assert flags.contains_equation is True
        assert flags.contains_diagram is True
        # Defaults should be False
        assert flags.contains_graph is False


# =============================================================================
# Vision Parse Trigger Tests
# =============================================================================

class TestVisionParseTrigger:
    """Tests for vision parse trigger logic."""

    def test_trigger_on_diagram(self):
        """Test trigger on diagram content."""
        flags = ContentFlags(
            contains_equation=True,
            contains_text=True,
            contains_diagram=True,
        )

        should_trigger, triggers = should_trigger_vision_parse(flags, confidence=0.95)

        assert should_trigger is True
        assert VisionParseTrigger.DIAGRAM_EXTRACTION in triggers

    def test_trigger_on_graph(self):
        """Test trigger on graph content."""
        flags = ContentFlags(
            contains_equation=True,
            contains_graph=True,
        )

        should_trigger, triggers = should_trigger_vision_parse(flags, confidence=0.95)

        assert should_trigger is True
        assert VisionParseTrigger.GRAPH_ANALYSIS in triggers

    def test_trigger_on_geometry(self):
        """Test trigger on geometry content."""
        flags = ContentFlags(
            contains_geometry=True,
        )

        should_trigger, triggers = should_trigger_vision_parse(flags, confidence=0.95)

        assert should_trigger is True
        assert VisionParseTrigger.GEOMETRY_DETECTION in triggers

    def test_trigger_on_low_confidence(self):
        """Test trigger on low confidence."""
        flags = ContentFlags(
            contains_equation=True,
            contains_text=True,
        )

        should_trigger, triggers = should_trigger_vision_parse(
            flags,
            confidence=0.3,
            low_confidence_threshold=0.5,
        )

        assert should_trigger is True
        assert VisionParseTrigger.LOW_CONFIDENCE_REGION in triggers

    def test_no_trigger(self):
        """Test no trigger for simple text."""
        flags = ContentFlags(
            contains_equation=True,
            contains_text=True,
        )

        should_trigger, triggers = should_trigger_vision_parse(flags, confidence=0.95)

        assert should_trigger is False
        assert len(triggers) == 0

    def test_multiple_triggers(self):
        """Test multiple trigger conditions."""
        flags = ContentFlags(
            contains_diagram=True,
            contains_graph=True,
            contains_geometry=True,
        )

        should_trigger, triggers = should_trigger_vision_parse(flags, confidence=0.4)

        assert should_trigger is True
        assert VisionParseTrigger.DIAGRAM_EXTRACTION in triggers
        assert VisionParseTrigger.GRAPH_ANALYSIS in triggers
        assert VisionParseTrigger.GEOMETRY_DETECTION in triggers
        assert VisionParseTrigger.LOW_CONFIDENCE_REGION in triggers


# =============================================================================
# Line Data Conversion Tests
# =============================================================================

class TestLineDataConversion:
    """Tests for line_data to LineSegment conversion."""

    def test_line_data_to_segments(self):
        """Test conversion of line_data to segments."""
        line_data = [
            {
                "type": "text",
                "text": "Sample text",
                "cnt": [[50, 20], [350, 20], [350, 45], [50, 45]],
                "confidence": 0.95,
            },
            {
                "type": "math",
                "text": "y = x^2",
                "latex": "y = x^2",
                "cnt": [[100, 60], [300, 60], [300, 100], [100, 100]],
                "confidence": 0.97,
            },
        ]

        segments = line_data_to_segments(line_data, "test-image-001")

        assert len(segments) == 2

        # Check first segment (text)
        assert segments[0].id == "test-image-001-line-000"
        assert segments[0].text == "Sample text"
        assert segments[0].confidence.value == 0.95
        assert segments[0].line_number == 0

        # Check second segment (math)
        assert segments[1].id == "test-image-001-line-001"
        assert segments[1].text == "y = x^2"
        assert segments[1].latex == "y = x^2"
        assert segments[1].confidence.value == 0.97

    def test_extract_equations(self):
        """Test equation extraction from line_data."""
        line_data = [
            {
                "type": "text",
                "text": "Problem:",
                "cnt": [[50, 20], [150, 20], [150, 45], [50, 45]],
                "confidence": 0.95,
            },
            {
                "type": "math",
                "text": "y = 2x + 3",
                "latex": "y = 2x + 3",
                "cnt": [[100, 60], [300, 60], [300, 100], [100, 100]],
                "confidence": 0.97,
            },
        ]

        equations = extract_equations(line_data, "test-image-002")

        # Should only extract math lines
        assert len(equations) == 1
        assert equations[0].latex == "y = 2x + 3"
        assert equations[0].confidence.value == 0.97

    def test_extract_equations_low_confidence_review(self):
        """Test low confidence equations are flagged for review."""
        line_data = [
            {
                "type": "math",
                "text": "unclear equation",
                "latex": "x = ?",
                "cnt": [[100, 60], [300, 60], [300, 100], [100, 100]],
                "confidence": 0.3,
            },
        ]

        equations = extract_equations(
            line_data,
            "test-image-003",
            low_confidence_threshold=0.5,
        )

        assert len(equations) == 1
        assert equations[0].review.review_required is True
        assert "low confidence" in equations[0].review.review_reason.lower()


# =============================================================================
# Writing Style Detection Tests
# =============================================================================

class TestWritingStyleDetection:
    """Tests for writing style detection."""

    def test_detect_printed(self):
        """Test detection of printed content."""
        response = {
            "detection_map": {
                "is_printed": 1,
                "is_handwritten": 0,
            }
        }
        line_data = []

        style = detect_writing_style(response, line_data)

        assert style == WritingStyle.PRINTED

    def test_detect_handwritten(self):
        """Test detection of handwritten content."""
        response = {
            "detection_map": {
                "is_printed": 0,
                "is_handwritten": 1,
            }
        }
        line_data = []

        style = detect_writing_style(response, line_data)

        assert style == WritingStyle.HANDWRITTEN

    def test_detect_mixed(self):
        """Test detection of mixed content."""
        response = {
            "detection_map": {
                "is_printed": 1,
                "is_handwritten": 1,
            }
        }
        line_data = [
            {"is_handwritten": True},
            {"is_handwritten": False},
        ]

        style = detect_writing_style(response, line_data)

        assert style == WritingStyle.MIXED


# =============================================================================
# MathpixClient Tests
# =============================================================================

class TestMathpixClient:
    """Tests for MathpixClient class."""

    @pytest.mark.asyncio
    async def test_process_image_success(
        self,
        mathpix_config: MathpixConfig,
        sample_image_bytes: bytes,
    ):
        """Test successful image processing."""
        async with MathpixClient(mathpix_config) as client:
            # Mock the HTTP client
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = SIMPLE_EQUATION_RESPONSE

            with patch.object(client._client, "post", new=AsyncMock(return_value=mock_response)):
                text_spec = await client.process_image(sample_image_bytes, image_id="test-001")

        assert isinstance(text_spec, TextSpec)
        assert text_spec.image_id == "test-001"
        assert text_spec.provenance.stage == PipelineStage.TEXT_PARSE
        assert text_spec.latex is not None

    @pytest.mark.asyncio
    async def test_process_image_with_diagram(
        self,
        mathpix_config: MathpixConfig,
        sample_image_bytes: bytes,
    ):
        """Test processing image with diagram triggers."""
        async with MathpixClient(mathpix_config) as client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = QUADRATIC_GRAPH_RESPONSE

            with patch.object(client._client, "post", new=AsyncMock(return_value=mock_response)):
                text_spec = await client.process_image(sample_image_bytes)

        assert text_spec.content_flags.contains_diagram is True
        assert len(text_spec.vision_parse_triggers) > 0
        assert VisionParseTrigger.DIAGRAM_EXTRACTION in text_spec.vision_parse_triggers

    @pytest.mark.asyncio
    async def test_rate_limit_error(
        self,
        mathpix_config: MathpixConfig,
        sample_image_bytes: bytes,
    ):
        """Test rate limit error handling."""
        # Use very low retry attempts for faster test
        mathpix_config.retry.max_attempts = 1

        async with MathpixClient(mathpix_config) as client:
            mock_response = MagicMock()
            mock_response.status_code = 429
            mock_response.headers.get.return_value = "60"

            with patch.object(client._client, "post", new=AsyncMock(return_value=mock_response)):
                with pytest.raises(RateLimitError) as exc_info:
                    await client.process_image(sample_image_bytes)

                assert exc_info.value.status_code == 429

    @pytest.mark.asyncio
    async def test_timeout_error(
        self,
        mathpix_config: MathpixConfig,
        sample_image_bytes: bytes,
    ):
        """Test timeout error handling."""
        mathpix_config.retry.max_attempts = 1

        async with MathpixClient(mathpix_config) as client:
            mock_response = MagicMock()
            mock_response.status_code = 504

            with patch.object(client._client, "post", new=AsyncMock(return_value=mock_response)):
                with pytest.raises(TimeoutError) as exc_info:
                    await client.process_image(sample_image_bytes)

                assert exc_info.value.status_code == 504

    @pytest.mark.asyncio
    async def test_invalid_image_error(
        self,
        mathpix_config: MathpixConfig,
        sample_image_bytes: bytes,
    ):
        """Test invalid image error (no retry)."""
        async with MathpixClient(mathpix_config) as client:
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_response.text = "Invalid image format"
            mock_response.json.return_value = {"error": "Invalid image"}

            with patch.object(client._client, "post", new=AsyncMock(return_value=mock_response)):
                with pytest.raises(InvalidImageError) as exc_info:
                    await client.process_image(sample_image_bytes)

                assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_server_error_with_retry(
        self,
        mathpix_config: MathpixConfig,
        sample_image_bytes: bytes,
    ):
        """Test server error with retry logic."""
        mathpix_config.retry.max_attempts = 2
        mathpix_config.retry.base_delay_ms = 10  # Fast retry for testing

        async with MathpixClient(mathpix_config) as client:
            # First call fails, second succeeds
            mock_error_response = MagicMock()
            mock_error_response.status_code = 500

            mock_success_response = MagicMock()
            mock_success_response.status_code = 200
            mock_success_response.json.return_value = SIMPLE_EQUATION_RESPONSE

            responses = [mock_error_response, mock_success_response]

            with patch.object(client._client, "post", new=AsyncMock(side_effect=responses)):
                text_spec = await client.process_image(sample_image_bytes)

            assert isinstance(text_spec, TextSpec)

    @pytest.mark.asyncio
    async def test_context_manager(self, mathpix_config: MathpixConfig):
        """Test async context manager lifecycle."""
        client = MathpixClient(mathpix_config)

        async with client as c:
            assert c._client is not None

        # After exit, client should be closed
        assert client._client is None

    @pytest.mark.asyncio
    async def test_encode_image_from_path(
        self,
        mathpix_config: MathpixConfig,
        tmp_path,
    ):
        """Test image encoding from file path."""
        # Create test image file
        image_path = tmp_path / "test.png"
        image_path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)

        client = MathpixClient(mathpix_config)
        encoded = client._encode_image(image_path)

        assert encoded.startswith("data:image/png;base64,")

    @pytest.mark.asyncio
    async def test_encode_image_from_bytes(self, mathpix_config: MathpixConfig):
        """Test image encoding from bytes."""
        image_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100

        client = MathpixClient(mathpix_config)
        encoded = client._encode_image(image_bytes)

        assert encoded.startswith("data:image/png;base64,")


# =============================================================================
# Response Parsing Tests
# =============================================================================

class TestResponseParsing:
    """Tests for Mathpix response parsing."""

    @pytest.mark.asyncio
    async def test_parse_simple_equation(self, mathpix_config: MathpixConfig):
        """Test parsing simple equation response."""
        async with MathpixClient(mathpix_config) as client:
            text_spec = client._response_to_text_spec(
                response=SIMPLE_EQUATION_RESPONSE,
                image_id="simple-eq",
                processing_time_ms=150.0,
            )

        assert text_spec.image_id == "simple-eq"
        assert text_spec.latex == "y = 2x + 3"
        assert text_spec.confidence == 0.98
        assert len(text_spec.line_segments) == 2
        assert len(text_spec.equations) == 1

    @pytest.mark.asyncio
    async def test_parse_handwritten_math(self, mathpix_config: MathpixConfig):
        """Test parsing handwritten math response."""
        async with MathpixClient(mathpix_config) as client:
            text_spec = client._response_to_text_spec(
                response=HANDWRITTEN_MATH_RESPONSE,
                image_id="handwritten",
                processing_time_ms=200.0,
            )

        assert text_spec.writing_style == WritingStyle.HANDWRITTEN
        assert text_spec.content_flags.contains_handwriting is True

    @pytest.mark.asyncio
    async def test_parse_geometry_diagram(self, mathpix_config: MathpixConfig):
        """Test parsing geometry diagram response."""
        async with MathpixClient(mathpix_config) as client:
            text_spec = client._response_to_text_spec(
                response=GEOMETRY_DIAGRAM_RESPONSE,
                image_id="geometry",
                processing_time_ms=250.0,
            )

        assert text_spec.content_flags.contains_diagram is True
        assert text_spec.content_flags.contains_geometry is True
        assert VisionParseTrigger.DIAGRAM_EXTRACTION in text_spec.vision_parse_triggers
        assert VisionParseTrigger.GEOMETRY_DETECTION in text_spec.vision_parse_triggers

    @pytest.mark.asyncio
    async def test_parse_complex_calculus(self, mathpix_config: MathpixConfig):
        """Test parsing complex calculus response."""
        async with MathpixClient(mathpix_config) as client:
            text_spec = client._response_to_text_spec(
                response=COMPLEX_CALCULUS_RESPONSE,
                image_id="calculus",
                processing_time_ms=180.0,
            )

        assert "\\int" in text_spec.latex
        assert len(text_spec.equations) >= 2  # Multiple equations in response

    @pytest.mark.asyncio
    async def test_low_confidence_review_flag(self, mathpix_config: MathpixConfig):
        """Test review flag for low confidence results."""
        # Modify config thresholds
        mathpix_config.very_low_confidence_threshold = 0.3
        mathpix_config.low_confidence_threshold = 0.6

        low_conf_response = SIMPLE_EQUATION_RESPONSE.copy()
        low_conf_response["confidence"] = 0.25

        async with MathpixClient(mathpix_config) as client:
            text_spec = client._response_to_text_spec(
                response=low_conf_response,
                image_id="low-conf",
                processing_time_ms=150.0,
            )

        assert text_spec.review.review_required is True
        assert "very low confidence" in text_spec.review.review_reason.lower()


# =============================================================================
# Detection Regions Tests
# =============================================================================

class TestDetectionRegions:
    """Tests for detection region parsing."""

    def test_parse_detection_regions_with_position(self):
        """Test parsing detection regions from position data."""
        response = {
            "position": {
                "top_left_x": 50,
                "top_left_y": 20,
                "width": 300,
                "height": 80,
            },
            "confidence": 0.95,
            "text": "Sample content",
        }

        regions = parse_detection_regions(response, "test-img")

        assert len(regions) >= 1
        assert regions[0].confidence == 0.95

    def test_parse_detection_regions_with_data_array(self):
        """Test parsing multiple detection regions."""
        response = {
            "data": [
                {
                    "type": "equation",
                    "position": {
                        "top_left_x": 100,
                        "top_left_y": 50,
                        "width": 200,
                        "height": 40,
                    },
                    "confidence": 0.96,
                    "text": "y = x^2",
                },
                {
                    "type": "text",
                    "position": {
                        "top_left_x": 100,
                        "top_left_y": 100,
                        "width": 250,
                        "height": 30,
                    },
                    "confidence": 0.93,
                    "text": "Sample text",
                },
            ]
        }

        regions = parse_detection_regions(response, "test-img")

        assert len(regions) >= 2
