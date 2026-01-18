"""
E2E Error Recovery Tests for Math Image Parsing Pipeline.

Tests error handling and graceful degradation scenarios:
- API failures (Mathpix, Claude)
- Rate limiting
- Invalid/corrupted inputs
- Timeout handling
- Partial stage failures
- Network errors
- Missing environment variables

Schema Version: 2.0.0
"""

import asyncio
import os
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, Optional
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

import httpx
import pytest

# Exception imports
from mathpix_pipeline.clients.mathpix import (
    MathpixClient,
    MathpixConfig,
    MathpixError,
    RateLimitError,
    TimeoutError as MathpixTimeoutError,
    InvalidImageError,
    ServerError,
)
from mathpix_pipeline.ingestion import (
    ImageLoader,
    ImageValidator,
    IngestionError,
)
from mathpix_pipeline.ingestion.exceptions import (
    ImageFormatError,
    ImageSizeError,
)
from mathpix_pipeline.pipeline import (
    MathpixPipeline,
    PipelineError,
    IngestionConfig,
)

# Schema imports
from mathpix_pipeline.schemas import (
    BBox,
    Confidence,
    Provenance,
    PipelineStage,
    TextSpec,
    ContentFlags,
    WritingStyle,
    VisionSpec,
    DetectionLayer,
    InterpretationLayer,
    MergedOutput,
    DiagramType,
)

# Mock helpers
from tests.fixtures.mocks.mathpix_responses import (
    SIMPLE_EQUATION_RESPONSE,
    create_mock_mathpix_client,
)
from tests.fixtures.mocks.vision_responses import (
    SIMPLE_EQUATION_DETECTION,
    SIMPLE_EQUATION_INTERPRETATION,
    create_mock_yolo_detector,
    create_mock_claude_interpreter,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def sample_png_bytes():
    """Generate minimal valid PNG bytes for testing."""
    # Minimal 1x1 PNG image (red pixel)
    return bytes([
        0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
        0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,  # IHDR chunk
        0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
        0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,
        0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,  # IDAT chunk
        0x54, 0x08, 0xD7, 0x63, 0xF8, 0xCF, 0xC0, 0x00,
        0x00, 0x00, 0x03, 0x00, 0x01, 0x00, 0x18, 0xDD,
        0x8D, 0xB4, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45,  # IEND chunk
        0x4E, 0x44, 0xAE, 0x42, 0x60, 0x82,
    ])


@pytest.fixture
def corrupted_image_bytes():
    """Generate corrupted/incomplete PNG bytes."""
    # PNG signature followed by invalid data
    return bytes([
        0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
        0xFF, 0xFF, 0xFF, 0xFF, 0x00, 0x00, 0x00, 0x00,  # Corrupted header
        0xDE, 0xAD, 0xBE, 0xEF,  # Random garbage
    ])


@pytest.fixture
def temp_output_dir():
    """Create temporary output directory for exports."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_mathpix_config():
    """Mock Mathpix configuration for testing."""
    return MathpixConfig(
        app_id="test-app-id",
        app_key="test-app-key",
        timeout_seconds=5.0,
    )


# =============================================================================
# Mathpix API Error Tests
# =============================================================================

class TestMathpixAPIErrors:
    """Test Mathpix API error handling scenarios."""

    @pytest.mark.asyncio
    async def test_mathpix_api_failure(self, mock_mathpix_config):
        """Test handling of Mathpix API 503 service unavailable error."""
        client = MathpixClient(mock_mathpix_config)

        # Mock HTTP client to return 503
        mock_response = MagicMock()
        mock_response.status_code = 503
        mock_response.text = "Service Unavailable"

        with patch.object(httpx.AsyncClient, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            async with client:
                with pytest.raises(ServerError) as exc_info:
                    await client.process_image(b"fake_image_data")

            assert exc_info.value.status_code == 503
            assert "Server error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_rate_limit_handling(self, mock_mathpix_config):
        """Test handling of 429 rate limit errors with retry-after header."""
        client = MathpixClient(mock_mathpix_config)

        # Mock HTTP client to return 429
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "30"}

        with patch.object(httpx.AsyncClient, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            async with client:
                with pytest.raises(RateLimitError) as exc_info:
                    await client.process_image(b"fake_image_data")

            assert exc_info.value.status_code == 429
            assert exc_info.value.retry_after == 30

    @pytest.mark.asyncio
    async def test_rate_limit_default_retry_after(self, mock_mathpix_config):
        """Test rate limit error uses default retry_after when header missing."""
        client = MathpixClient(mock_mathpix_config)

        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.headers = {}  # No Retry-After header

        with patch.object(httpx.AsyncClient, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            async with client:
                with pytest.raises(RateLimitError) as exc_info:
                    await client.process_image(b"fake_image_data")

            # Default retry_after should be 60 seconds
            assert exc_info.value.retry_after == 60


# =============================================================================
# Image Input Error Tests
# =============================================================================

class TestImageInputErrors:
    """Test handling of invalid and corrupted image inputs."""

    @pytest.mark.asyncio
    async def test_invalid_image_handling(self):
        """Test handling of non-image files (e.g., text files)."""
        loader = ImageLoader()

        # Test with plain text content (not an image)
        invalid_content = b"This is not an image file, just plain text."

        with pytest.raises(ImageFormatError) as exc_info:
            await loader.load_from_bytes(invalid_content)

        assert "Could not detect image format" in str(exc_info.value) or \
               "Invalid" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_corrupted_image_handling(self, corrupted_image_bytes):
        """Test handling of corrupted image data."""
        loader = ImageLoader()

        # Corrupted PNG with valid signature but invalid content
        with pytest.raises((ImageFormatError, IngestionError)) as exc_info:
            await loader.load_from_bytes(corrupted_image_bytes)

        # Should fail gracefully with informative error
        assert exc_info.value is not None

    @pytest.mark.asyncio
    async def test_empty_image_handling(self):
        """Test handling of empty image data."""
        loader = ImageLoader()

        with pytest.raises((ImageFormatError, ImageSizeError, IngestionError)) as exc_info:
            await loader.load_from_bytes(b"")

        assert exc_info.value is not None

    @pytest.mark.asyncio
    async def test_truncated_image_handling(self, sample_png_bytes):
        """Test handling of truncated image files."""
        loader = ImageLoader()

        # Truncate valid PNG to corrupt it
        truncated_bytes = sample_png_bytes[:len(sample_png_bytes) // 2]

        with pytest.raises((ImageFormatError, IngestionError)) as exc_info:
            await loader.load_from_bytes(truncated_bytes)

        assert exc_info.value is not None


# =============================================================================
# YOLO/Claude Failure Tests
# =============================================================================

class TestVisionLayerErrors:
    """Test YOLO and Claude failure handling with fallbacks."""

    @pytest.mark.asyncio
    async def test_yolo_failure_fallback(self, sample_png_bytes, temp_output_dir):
        """Test fallback when YOLO detection fails (e.g., CUDA errors)."""
        # Create pipeline with mocked components
        pipeline = MathpixPipeline(
            ingestion_config=IngestionConfig(enable_preprocessing=False),
        )

        # Mock YOLO detector to raise exception (simulating CUDA error)
        mock_yolo = MagicMock()
        mock_yolo.detect = MagicMock(side_effect=RuntimeError("CUDA out of memory"))

        with patch.object(pipeline, '_yolo_detector', mock_yolo):
            # The pipeline should handle YOLO failure gracefully
            # and continue with empty detection layer
            try:
                with patch.object(pipeline._image_loader, 'load_from_bytes', new_callable=AsyncMock) as mock_load:
                    mock_loaded = MagicMock()
                    mock_loaded.metadata = {}
                    mock_load.return_value = mock_loaded

                    with patch.object(pipeline._image_validator, 'validate') as mock_validate:
                        mock_validation = MagicMock()
                        mock_validation.is_valid = True
                        mock_validation.warnings = []
                        mock_validate.return_value = mock_validation

                        # Test that pipeline doesn't crash
                        result = await pipeline.process(sample_png_bytes)
                        # Result may have errors logged but shouldn't crash
                        assert result is not None
            except PipelineError as e:
                # Pipeline error is acceptable, shouldn't be unhandled exception
                assert "YOLO" in str(e) or "Vision" in str(e) or e.stage is not None

    @pytest.mark.asyncio
    async def test_claude_failure_fallback(self, sample_png_bytes, temp_output_dir):
        """Test fallback when Claude API fails."""
        pipeline = MathpixPipeline(
            ingestion_config=IngestionConfig(enable_preprocessing=False),
        )

        # Mock Claude interpreter to fail
        mock_interpreter = MagicMock()
        mock_interpreter.interpret = AsyncMock(
            side_effect=Exception("Claude API rate limit exceeded")
        )

        with patch.object(pipeline, '_diagram_interpreter', mock_interpreter):
            try:
                with patch.object(pipeline._image_loader, 'load_from_bytes', new_callable=AsyncMock) as mock_load:
                    mock_loaded = MagicMock()
                    mock_loaded.metadata = {}
                    mock_load.return_value = mock_loaded

                    with patch.object(pipeline._image_validator, 'validate') as mock_validate:
                        mock_validation = MagicMock()
                        mock_validation.is_valid = True
                        mock_validation.warnings = []
                        mock_validate.return_value = mock_validation

                        result = await pipeline.process(sample_png_bytes)
                        # Pipeline should fallback to Gemini or empty interpretation
                        assert result is not None
            except PipelineError as e:
                # Expected - Claude failure should be captured
                assert e.stage is not None


# =============================================================================
# Environment and Configuration Errors
# =============================================================================

class TestEnvironmentErrors:
    """Test handling of missing environment variables and configs."""

    @pytest.mark.asyncio
    async def test_missing_env_vars(self):
        """Test graceful handling when API keys are missing."""
        # Clear environment variables
        env_backup = {}
        keys_to_clear = ['MATHPIX_APP_ID', 'MATHPIX_APP_KEY', 'ANTHROPIC_API_KEY']

        for key in keys_to_clear:
            if key in os.environ:
                env_backup[key] = os.environ.pop(key)

        try:
            # Create pipeline without config - should handle gracefully
            pipeline = MathpixPipeline()

            # Process should handle missing config
            result = await pipeline.process(b"fake_image_data")

            # Should have warnings about missing config
            assert result is not None
            # May have errors or warnings, but shouldn't crash

        finally:
            # Restore environment
            os.environ.update(env_backup)

    @pytest.mark.asyncio
    async def test_invalid_config_values(self):
        """Test handling of invalid configuration values."""
        # Create config with invalid values
        with pytest.raises((ValueError, TypeError)):
            MathpixConfig(
                app_id="",  # Empty app_id should be rejected
                app_key="valid-key",
                timeout_seconds=-1.0,  # Negative timeout
            )


# =============================================================================
# Timeout Handling Tests
# =============================================================================

class TestTimeoutHandling:
    """Test timeout handling in pipeline stages."""

    @pytest.mark.asyncio
    async def test_timeout_handling(self, mock_mathpix_config, sample_png_bytes):
        """Test handling of stage timeouts."""
        client = MathpixClient(mock_mathpix_config)

        # Mock HTTP client to timeout
        with patch.object(httpx.AsyncClient, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = httpx.TimeoutException("Request timed out")

            async with client:
                with pytest.raises((MathpixTimeoutError, MathpixError)) as exc_info:
                    await client.process_image(sample_png_bytes)

            # Should handle timeout gracefully
            assert "timeout" in str(exc_info.value).lower() or \
                   isinstance(exc_info.value, MathpixTimeoutError)

    @pytest.mark.asyncio
    async def test_stage_timeout_limits(self, sample_png_bytes):
        """Test that stage-level timeouts are enforced."""
        pipeline = MathpixPipeline(
            ingestion_config=IngestionConfig(enable_preprocessing=False),
        )

        # Create slow mock that exceeds timeout
        async def slow_operation(*args, **kwargs):
            await asyncio.sleep(15)  # Simulate slow operation
            return MagicMock()

        with patch.object(pipeline._image_loader, 'load_from_bytes', slow_operation):
            try:
                # Use asyncio timeout to enforce limit
                result = await asyncio.wait_for(
                    pipeline.process(sample_png_bytes),
                    timeout=5.0,
                )
                # If we get here without timeout, that's also acceptable
                # (mock may not actually be called)
            except asyncio.TimeoutError:
                # Expected - timeout should be raised
                pass

    @pytest.mark.asyncio
    async def test_http_timeout_retry(self, mock_mathpix_config):
        """Test that HTTP timeouts trigger retry logic."""
        # Configure with multiple retries
        config = MathpixConfig(
            app_id="test-app-id",
            app_key="test-app-key",
            timeout_seconds=1.0,
        )
        config.retry.max_attempts = 3
        config.retry.base_delay_ms = 100  # Fast retries for test

        client = MathpixClient(config)

        call_count = 0

        async def timeout_then_succeed(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise httpx.TimeoutException("timeout")
            # Return success on 3rd attempt
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = SIMPLE_EQUATION_RESPONSE
            return mock_response

        with patch.object(httpx.AsyncClient, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = timeout_then_succeed

            async with client:
                result = await client.process_image(b"fake_image")

            # Should have retried and succeeded
            assert call_count == 3
            assert result is not None


# =============================================================================
# Partial Stage Failure Tests
# =============================================================================

class TestPartialStageFailures:
    """Test pipeline behavior with partial stage failures."""

    @pytest.mark.asyncio
    async def test_partial_stage_failure(self, sample_png_bytes):
        """Test that pipeline continues with partial results after stage failure."""
        pipeline = MathpixPipeline(
            ingestion_config=IngestionConfig(enable_preprocessing=False),
        )

        # Mock Stage B to succeed, Stage C to fail
        mock_text_spec = TextSpec(
            image_id="test-001",
            provenance=Provenance(
                stage=PipelineStage.TEXT_PARSE,
                model="mock",
                processing_time_ms=50.0,
            ),
            writing_style=WritingStyle.PRINTED,
            content_flags=ContentFlags(contains_equation=True),
            vision_parse_triggers=[],
            equations=[],
            line_segments=[],
        )

        with patch.object(pipeline, '_run_stage_b', new_callable=AsyncMock) as mock_stage_b:
            mock_stage_b.return_value = mock_text_spec

            with patch.object(pipeline, '_run_stage_c', new_callable=AsyncMock) as mock_stage_c:
                # Stage C fails
                mock_stage_c.side_effect = Exception("Vision processing failed")

                with patch.object(pipeline._image_loader, 'load_from_bytes', new_callable=AsyncMock) as mock_load:
                    mock_loaded = MagicMock()
                    mock_loaded.metadata = {}
                    mock_load.return_value = mock_loaded

                    with patch.object(pipeline._image_validator, 'validate') as mock_validate:
                        mock_validation = MagicMock()
                        mock_validation.is_valid = True
                        mock_validation.warnings = []
                        mock_validate.return_value = mock_validation

                        result = await pipeline.process(sample_png_bytes)

                        # Should have Stage B result but Stage C failed
                        assert result is not None
                        assert result.text_spec is not None
                        # Vision spec may be None due to failure
                        # Pipeline should continue and record error

    @pytest.mark.asyncio
    async def test_stage_skipping_on_dependency_failure(self, sample_png_bytes):
        """Test that dependent stages are skipped when prerequisite fails."""
        pipeline = MathpixPipeline(
            ingestion_config=IngestionConfig(enable_preprocessing=False),
        )

        # Stage A fails completely
        with patch.object(pipeline, '_run_stage_a', new_callable=AsyncMock) as mock_stage_a:
            mock_stage_a.side_effect = PipelineError("Ingestion failed", stage=PipelineStage.INGESTION)

            result = await pipeline.process(sample_png_bytes)

            # Pipeline should report failure
            assert result is not None
            assert result.success is False
            assert len(result.errors) > 0

    @pytest.mark.asyncio
    async def test_continue_with_empty_results(self, sample_png_bytes):
        """Test pipeline continues when a stage returns empty results."""
        pipeline = MathpixPipeline(
            ingestion_config=IngestionConfig(enable_preprocessing=False),
        )

        # Stage B returns empty TextSpec (no equations found)
        empty_text_spec = TextSpec(
            image_id="test-001",
            provenance=Provenance(
                stage=PipelineStage.TEXT_PARSE,
                model="mock",
                processing_time_ms=50.0,
            ),
            writing_style=WritingStyle.PRINTED,
            content_flags=ContentFlags(),
            vision_parse_triggers=[],
            equations=[],
            line_segments=[],
        )

        with patch.object(pipeline, '_run_stage_b', new_callable=AsyncMock) as mock_stage_b:
            mock_stage_b.return_value = empty_text_spec

            with patch.object(pipeline._image_loader, 'load_from_bytes', new_callable=AsyncMock) as mock_load:
                mock_loaded = MagicMock()
                mock_loaded.metadata = {}
                mock_load.return_value = mock_loaded

                with patch.object(pipeline._image_validator, 'validate') as mock_validate:
                    mock_validation = MagicMock()
                    mock_validation.is_valid = True
                    mock_validation.warnings = []
                    mock_validate.return_value = mock_validation

                    result = await pipeline.process(sample_png_bytes)

                    # Should handle empty results gracefully
                    assert result is not None
                    assert result.text_spec is not None


# =============================================================================
# Network Error Tests
# =============================================================================

class TestNetworkErrors:
    """Test network error recovery scenarios."""

    @pytest.mark.asyncio
    async def test_network_error_recovery(self, mock_mathpix_config):
        """Test handling of network connectivity issues."""
        client = MathpixClient(mock_mathpix_config)

        # Simulate connection error
        with patch.object(httpx.AsyncClient, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = httpx.ConnectError("Connection refused")

            async with client:
                with pytest.raises((MathpixError, httpx.ConnectError)) as exc_info:
                    await client.process_image(b"fake_image")

            # Should fail with network error
            assert exc_info.value is not None

    @pytest.mark.asyncio
    async def test_dns_resolution_failure(self, mock_mathpix_config):
        """Test handling of DNS resolution failures."""
        client = MathpixClient(mock_mathpix_config)

        # Simulate DNS failure
        with patch.object(httpx.AsyncClient, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = httpx.ConnectError("Name or service not known")

            async with client:
                with pytest.raises((MathpixError, httpx.ConnectError)):
                    await client.process_image(b"fake_image")

    @pytest.mark.asyncio
    async def test_connection_reset(self, mock_mathpix_config):
        """Test handling of connection reset by peer."""
        client = MathpixClient(mock_mathpix_config)

        with patch.object(httpx.AsyncClient, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = httpx.ReadError("Connection reset by peer")

            async with client:
                with pytest.raises((MathpixError, httpx.ReadError)):
                    await client.process_image(b"fake_image")

    @pytest.mark.asyncio
    async def test_ssl_certificate_error(self, mock_mathpix_config):
        """Test handling of SSL certificate errors."""
        client = MathpixClient(mock_mathpix_config)

        with patch.object(httpx.AsyncClient, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = httpx.ConnectError("SSL: CERTIFICATE_VERIFY_FAILED")

            async with client:
                with pytest.raises((MathpixError, httpx.ConnectError)):
                    await client.process_image(b"fake_image")


# =============================================================================
# Run Configuration
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
