"""
Tests for Pipeline Processor (Stage A → B → C0 integration).
"""
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import tempfile

from cow_cli.pipeline import (
    PipelineProcessor,
    PipelineResult,
    PipelineError,
    process_image,
)
from cow_cli.mathpix.schemas import MathpixResponse
from cow_cli.semantic import ElementType


class TestPipelineProcessor:
    """Tests for PipelineProcessor class."""

    @pytest.fixture
    def mock_mathpix_response(self):
        """Create mock Mathpix API response."""
        return MathpixResponse(
            request_id="test-request-123",
            text="Hello world $x^2$",
            latex_styled="Hello world $x^2$",
            confidence=0.95,
            confidence_rate=0.92,
            image_width=800,
            image_height=600,
            word_data=[
                {
                    "type": "text",
                    "text": "Hello world",
                    "cnt": [[10, 10], [100, 10], [100, 30], [10, 30]],
                    "confidence": 0.95,
                },
                {
                    "type": "math",
                    "text": "$x^2$",
                    "latex": "x^2",
                    "cnt": [[110, 10], [150, 10], [150, 30], [110, 30]],
                    "confidence": 0.88,
                },
            ],
        )

    @pytest.fixture
    def processor(self):
        """Create processor with mocked client."""
        return PipelineProcessor(skip_validation=True)

    @pytest.mark.asyncio
    async def test_process_full_pipeline(self, processor, mock_mathpix_response):
        """Test full pipeline processing."""
        # Mock the mathpix client
        mock_client = AsyncMock()
        mock_client.process_image = AsyncMock(return_value=mock_mathpix_response)
        processor.mathpix_client = mock_client

        with tempfile.NamedTemporaryFile(suffix=".png") as tmp:
            result = await processor.process(tmp.name)

        assert result.success is True
        assert result.document is not None
        assert len(result.document.layout.elements) == 2
        assert len(result.document.content.elements) == 2
        assert result.mathpix_response is not None

    @pytest.mark.asyncio
    async def test_stage_results_recorded(self, processor, mock_mathpix_response):
        """Test that all stage results are recorded."""
        mock_client = AsyncMock()
        mock_client.process_image = AsyncMock(return_value=mock_mathpix_response)
        processor.mathpix_client = mock_client

        with tempfile.NamedTemporaryFile(suffix=".png") as tmp:
            result = await processor.process(tmp.name)

        assert len(result.stages) == 3
        assert result.stage_a_result is not None
        assert result.stage_a_result.stage == "A"
        assert result.stage_b_result is not None
        assert result.stage_b_result.stage == "B"
        assert result.stage_c0_result is not None
        assert result.stage_c0_result.stage == "C0"

    @pytest.mark.asyncio
    async def test_stage_a_validation_failure(self, processor):
        """Test Stage A validation failure handling."""
        processor.skip_validation = False
        # Process non-existent file
        result = await processor.process("/nonexistent/image.png")

        assert result.success is False
        assert "Stage A failed" in result.error

    @pytest.mark.asyncio
    async def test_stage_b_mathpix_failure(self, processor):
        """Test Stage B Mathpix API failure handling."""
        from cow_cli.mathpix.exceptions import MathpixAPIError

        mock_client = AsyncMock()
        mock_client.process_image = AsyncMock(
            side_effect=MathpixAPIError("API error", 500)
        )
        processor.mathpix_client = mock_client

        with tempfile.NamedTemporaryFile(suffix=".png") as tmp:
            result = await processor.process(tmp.name)

        assert result.success is False
        assert "Stage B failed" in result.error

    @pytest.mark.asyncio
    async def test_stage_c0_separation(self, processor, mock_mathpix_response):
        """Test Stage C0 produces correct separation."""
        mock_client = AsyncMock()
        mock_client.process_image = AsyncMock(return_value=mock_mathpix_response)
        processor.mathpix_client = mock_client

        with tempfile.NamedTemporaryFile(suffix=".png") as tmp:
            result = await processor.process(tmp.name)

        doc = result.document

        # Check layout elements
        text_elem = doc.layout.elements[0]
        assert text_elem.type == ElementType.TEXT
        assert text_elem.region is not None

        math_elem = doc.layout.elements[1]
        assert math_elem.type == ElementType.MATH

        # Check content elements
        assert doc.content.elements[0].text == "Hello world"
        assert doc.content.elements[1].latex == "x^2"

    @pytest.mark.asyncio
    async def test_save_outputs(self, processor, mock_mathpix_response):
        """Test output saving."""
        mock_client = AsyncMock()
        mock_client.process_image = AsyncMock(return_value=mock_mathpix_response)
        processor.mathpix_client = mock_client

        with tempfile.TemporaryDirectory() as tmpdir:
            with tempfile.NamedTemporaryFile(suffix=".png") as tmp:
                output_dir = Path(tmpdir) / "output"
                result = await processor.process(tmp.name, output_dir=output_dir)

            assert result.success is True
            assert output_dir.exists()
            assert (output_dir / "layout.json").exists()
            assert (output_dir / "content.json").exists()
            assert (output_dir / "separated.json").exists()

    @pytest.mark.asyncio
    async def test_duration_tracking(self, processor, mock_mathpix_response):
        """Test duration tracking for stages."""
        mock_client = AsyncMock()
        mock_client.process_image = AsyncMock(return_value=mock_mathpix_response)
        processor.mathpix_client = mock_client

        with tempfile.NamedTemporaryFile(suffix=".png") as tmp:
            result = await processor.process(tmp.name)

        assert result.total_duration_ms > 0
        for stage in result.stages:
            assert stage.duration_ms >= 0


class TestPipelineConvenienceFunctions:
    """Tests for convenience functions."""

    @pytest.mark.asyncio
    async def test_process_image_function(self):
        """Test process_image convenience function."""
        mock_response = MathpixResponse(
            request_id="test",
            text="Test",
            image_width=800,
            image_height=600,
            word_data=[{"type": "text", "text": "Test", "cnt": [[0, 0], [100, 50]]}],
        )

        with patch(
            "cow_cli.pipeline.processor.MathpixClient"
        ) as MockClient:
            mock_instance = AsyncMock()
            mock_instance.process_image = AsyncMock(return_value=mock_response)
            MockClient.return_value = mock_instance

            with tempfile.NamedTemporaryFile(suffix=".png") as tmp:
                result = await process_image(tmp.name, skip_validation=True)

            assert result.success is True
            assert result.document is not None


class TestPipelineEdgeCases:
    """Edge case tests for pipeline."""

    @pytest.fixture
    def processor(self):
        return PipelineProcessor(skip_validation=True)

    @pytest.mark.asyncio
    async def test_empty_word_data(self, processor):
        """Test handling of empty word_data."""
        mock_response = MathpixResponse(
            request_id="test",
            text="",
            image_width=800,
            image_height=600,
            word_data=[],
        )

        mock_client = AsyncMock()
        mock_client.process_image = AsyncMock(return_value=mock_response)
        processor.mathpix_client = mock_client

        with tempfile.NamedTemporaryFile(suffix=".png") as tmp:
            result = await processor.process(tmp.name)

        assert result.success is True
        assert len(result.document.layout.elements) == 0
        assert len(result.document.content.elements) == 0

    @pytest.mark.asyncio
    async def test_none_word_data(self, processor):
        """Test handling of None word_data."""
        mock_response = MathpixResponse(
            request_id="test",
            text="Test",
            image_width=800,
            image_height=600,
            word_data=None,
        )

        mock_client = AsyncMock()
        mock_client.process_image = AsyncMock(return_value=mock_response)
        processor.mathpix_client = mock_client

        with tempfile.NamedTemporaryFile(suffix=".png") as tmp:
            result = await processor.process(tmp.name)

        assert result.success is True
        assert len(result.document.layout.elements) == 0

    @pytest.mark.asyncio
    async def test_mathpix_options_passed(self, processor):
        """Test that mathpix options are passed to client."""
        mock_response = MathpixResponse(request_id="test", text="Test")

        mock_client = AsyncMock()
        mock_client.process_image = AsyncMock(return_value=mock_response)
        processor.mathpix_client = mock_client

        custom_options = {"include_line_data": True}

        with tempfile.NamedTemporaryFile(suffix=".png") as tmp:
            await processor.process(tmp.name, mathpix_options=custom_options)

        # Verify options were passed
        call_args = mock_client.process_image.call_args
        assert call_args.kwargs["options"] == custom_options


class TestPipelineResultProperties:
    """Tests for PipelineResult properties."""

    def test_stage_result_accessors(self):
        """Test stage result accessor properties."""
        stages = [
            MagicMock(stage="A", success=True),
            MagicMock(stage="B", success=True),
            MagicMock(stage="C0", success=True),
        ]

        result = PipelineResult(
            image_path="test.png",
            success=True,
            stages=stages,
        )

        assert result.stage_a_result.stage == "A"
        assert result.stage_b_result.stage == "B"
        assert result.stage_c0_result.stage == "C0"

    def test_missing_stage_accessor(self):
        """Test accessor returns None for missing stages."""
        result = PipelineResult(
            image_path="test.png",
            success=False,
            stages=[],
        )

        assert result.stage_a_result is None
        assert result.stage_b_result is None
        assert result.stage_c0_result is None
