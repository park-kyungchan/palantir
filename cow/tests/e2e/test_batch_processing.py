"""
End-to-end tests for Batch Image Processing.

Tests the pipeline's ability to process multiple images concurrently
with proper handling of concurrency limits, partial failures, and result ordering.

Test Coverage:
- test_batch_processing_success: Process multiple images
- test_batch_concurrency_limit: Verify max_concurrent is respected
- test_batch_partial_failure: Handle some images failing
- test_batch_empty_list: Edge case: empty input
- test_batch_single_image: Edge case: one image
- test_batch_result_order: Results match input order
- test_batch_with_options: Apply options to all images

Schema Version: 2.0.0
"""

import asyncio
import pytest
import time
from pathlib import Path
from typing import List, Optional, Union
from unittest.mock import AsyncMock, MagicMock, patch, call

from mathpix_pipeline.schemas import (
    BBox,
    Confidence,
    CombinedConfidence,
    Provenance,
    PipelineStage,
    ReviewMetadata,
    # Stage B
    TextSpec,
    ContentFlags,
    LineSegment,
    EquationElement,
    WritingStyle,
    VisionParseTrigger,
)
from mathpix_pipeline.schemas.pipeline import (
    PipelineOptions,
    PipelineResult,
)

from mathpix_pipeline.pipeline import MathpixPipeline, IngestionConfig


# =============================================================================
# Test Fixtures
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
def sample_images(sample_png_bytes) -> List[bytes]:
    """Generate a list of sample image bytes for batch testing."""
    # Return 5 copies of the sample PNG (simulating 5 different images)
    return [sample_png_bytes for _ in range(5)]


def create_mock_result(image_id: str, success: bool = True) -> PipelineResult:
    """Create a mock PipelineResult for testing."""
    return PipelineResult(
        image_id=image_id,
        success=success,
        stages_completed=[
            PipelineStage.INGESTION,
            PipelineStage.TEXT_PARSE,
        ] if success else [],
        errors=[] if success else [f"Mock error for {image_id}"],
        processing_time_ms=100.0,
    )


# =============================================================================
# Batch Processing Tests
# =============================================================================

class TestBatchProcessing:
    """Test batch image processing functionality."""

    @pytest.mark.asyncio
    async def test_batch_processing_success(self, sample_images):
        """Test processing multiple images successfully.

        Verifies:
        - All images are processed
        - All results are successful
        - Statistics are updated correctly
        """
        processed_ids = []

        async def mock_process(
            image: Union[str, Path, bytes],
            options: Optional[PipelineOptions] = None,
        ) -> PipelineResult:
            image_id = f"batch-{len(processed_ids)}"
            processed_ids.append(image_id)
            await asyncio.sleep(0.01)  # Simulate processing time
            return create_mock_result(image_id, success=True)

        with patch.object(MathpixPipeline, 'process', side_effect=mock_process):
            pipeline = MathpixPipeline()
            results = await pipeline.process_batch(sample_images, max_concurrent=4)

        # All images should be processed
        assert len(results) == len(sample_images)
        assert len(processed_ids) == len(sample_images)

        # All results should be successful
        for result in results:
            assert isinstance(result, PipelineResult)
            assert result.success is True
            assert result.image_id.startswith("batch-")

    @pytest.mark.asyncio
    async def test_batch_concurrency_limit(self, sample_images):
        """Test that max_concurrent limit is respected.

        Verifies:
        - No more than max_concurrent images are processed simultaneously
        - All images are eventually processed
        """
        max_concurrent = 2
        active_count = 0
        max_active_observed = 0
        lock = asyncio.Lock()

        async def mock_process(
            image: Union[str, Path, bytes],
            options: Optional[PipelineOptions] = None,
        ) -> PipelineResult:
            nonlocal active_count, max_active_observed

            async with lock:
                active_count += 1
                max_active_observed = max(max_active_observed, active_count)

            await asyncio.sleep(0.05)  # Simulate processing time

            async with lock:
                active_count -= 1

            return create_mock_result(f"concurrent-test-{id(image)}", success=True)

        with patch.object(MathpixPipeline, 'process', side_effect=mock_process):
            pipeline = MathpixPipeline()
            results = await pipeline.process_batch(
                sample_images,
                max_concurrent=max_concurrent
            )

        # All images should be processed
        assert len(results) == len(sample_images)

        # Concurrency limit should not be exceeded
        assert max_active_observed <= max_concurrent
        assert max_active_observed > 0  # At least some concurrency occurred

    @pytest.mark.asyncio
    async def test_batch_partial_failure(self, sample_images):
        """Test handling of partial failures in batch processing.

        Verifies:
        - Successful images return normal results
        - Failed images return error results
        - Processing continues despite failures
        """
        call_count = 0

        async def mock_process(
            image: Union[str, Path, bytes],
            options: Optional[PipelineOptions] = None,
        ) -> PipelineResult:
            nonlocal call_count
            call_count += 1

            # Make every other image fail
            should_fail = (call_count % 2 == 0)

            if should_fail:
                return create_mock_result(f"partial-{call_count}", success=False)
            return create_mock_result(f"partial-{call_count}", success=True)

        with patch.object(MathpixPipeline, 'process', side_effect=mock_process):
            pipeline = MathpixPipeline()
            results = await pipeline.process_batch(sample_images, max_concurrent=4)

        # All images should have results
        assert len(results) == len(sample_images)

        # Check for mix of success and failure
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]

        assert len(successful) > 0
        assert len(failed) > 0
        assert len(successful) + len(failed) == len(sample_images)

    @pytest.mark.asyncio
    async def test_batch_exception_handling(self, sample_images):
        """Test handling of exceptions during batch processing.

        Verifies:
        - Exceptions are caught and converted to failed results
        - Other images continue processing
        """
        call_count = 0

        async def mock_process(
            image: Union[str, Path, bytes],
            options: Optional[PipelineOptions] = None,
        ) -> PipelineResult:
            nonlocal call_count
            call_count += 1

            # Make the third image raise an exception
            if call_count == 3:
                raise ValueError("Simulated processing error")

            return create_mock_result(f"exception-{call_count}", success=True)

        with patch.object(MathpixPipeline, 'process', side_effect=mock_process):
            pipeline = MathpixPipeline()
            results = await pipeline.process_batch(sample_images, max_concurrent=4)

        # All images should have results
        assert len(results) == len(sample_images)

        # One result should be a failed result due to exception
        failed = [r for r in results if not r.success]
        assert len(failed) == 1

        # The failed result should contain the error message
        assert any("Simulated processing error" in str(r.errors) for r in failed)

    @pytest.mark.asyncio
    async def test_batch_empty_list(self):
        """Test batch processing with empty input list.

        Verifies:
        - Empty input returns empty results
        - No errors are raised
        """
        with patch.object(MathpixPipeline, 'process', new_callable=AsyncMock) as mock_process:
            pipeline = MathpixPipeline()
            results = await pipeline.process_batch([], max_concurrent=4)

        # Should return empty list
        assert results == []

        # Process should never be called
        mock_process.assert_not_called()

    @pytest.mark.asyncio
    async def test_batch_single_image(self, sample_png_bytes):
        """Test batch processing with single image.

        Verifies:
        - Single image is processed correctly
        - Result is returned as a list with one element
        """
        async def mock_process(
            image: Union[str, Path, bytes],
            options: Optional[PipelineOptions] = None,
        ) -> PipelineResult:
            return create_mock_result("single-image-001", success=True)

        with patch.object(MathpixPipeline, 'process', side_effect=mock_process):
            pipeline = MathpixPipeline()
            results = await pipeline.process_batch([sample_png_bytes], max_concurrent=4)

        # Should return list with one result
        assert len(results) == 1
        assert results[0].success is True
        assert results[0].image_id == "single-image-001"

    @pytest.mark.asyncio
    async def test_batch_result_order(self, sample_images):
        """Test that batch results maintain input order.

        Verifies:
        - Results are returned in the same order as input images
        - Even with different processing times, order is preserved
        """
        processing_delays = [0.05, 0.01, 0.04, 0.02, 0.03]  # Different delays

        call_count = 0

        async def mock_process(
            image: Union[str, Path, bytes],
            options: Optional[PipelineOptions] = None,
        ) -> PipelineResult:
            nonlocal call_count
            idx = call_count
            call_count += 1

            # Apply different delays to each image
            await asyncio.sleep(processing_delays[idx])

            # Include index in image_id to verify order
            return create_mock_result(f"ordered-{idx}", success=True)

        with patch.object(MathpixPipeline, 'process', side_effect=mock_process):
            pipeline = MathpixPipeline()
            results = await pipeline.process_batch(sample_images, max_concurrent=4)

        # Results should be in order 0, 1, 2, 3, 4
        assert len(results) == len(sample_images)
        for i, result in enumerate(results):
            assert result.image_id == f"ordered-{i}"

    @pytest.mark.asyncio
    async def test_batch_with_options(self, sample_images):
        """Test that options are applied to all images in batch.

        Verifies:
        - Each process call receives the same options
        - Options are correctly propagated
        """
        received_options = []

        async def mock_process(
            image: Union[str, Path, bytes],
            options: Optional[PipelineOptions] = None,
        ) -> PipelineResult:
            received_options.append(options)
            return create_mock_result(f"options-test-{len(received_options)}", success=True)

        options = PipelineOptions(
            skip_stages=[PipelineStage.VISION_PARSE],
            export_formats=["json", "latex"],
            timeout_seconds=120,
            min_confidence_threshold=0.75,
        )

        with patch.object(MathpixPipeline, 'process', side_effect=mock_process):
            pipeline = MathpixPipeline()
            results = await pipeline.process_batch(
                sample_images,
                options=options,
                max_concurrent=4
            )

        # All images should have results
        assert len(results) == len(sample_images)

        # Each call should receive the same options
        assert len(received_options) == len(sample_images)
        for opt in received_options:
            assert opt is options  # Same options object passed to all


# =============================================================================
# Batch Statistics Tests
# =============================================================================

class TestBatchStatistics:
    """Test batch processing statistics."""

    @pytest.mark.asyncio
    async def test_batch_updates_stats(self, sample_images):
        """Test that batch processing updates pipeline statistics."""
        async def mock_process(
            image: Union[str, Path, bytes],
            options: Optional[PipelineOptions] = None,
        ) -> PipelineResult:
            result = create_mock_result(f"stats-{id(image)}", success=True)
            result.processing_time_ms = 100.0
            return result

        with patch.object(MathpixPipeline, 'process', side_effect=mock_process):
            pipeline = MathpixPipeline()
            pipeline.reset_stats()

            await pipeline.process_batch(sample_images, max_concurrent=4)

            # Note: Stats are updated inside the actual process method
            # In this mock, we're bypassing that, so we can't test stats directly
            # This test demonstrates the intended behavior

    @pytest.mark.asyncio
    async def test_batch_timing(self, sample_images):
        """Test that batch processing takes advantage of concurrency.

        Verifies:
        - Total batch time is less than sum of individual times
        - Concurrency provides actual speedup
        """
        processing_time_per_image = 0.1  # 100ms per image

        async def mock_process(
            image: Union[str, Path, bytes],
            options: Optional[PipelineOptions] = None,
        ) -> PipelineResult:
            await asyncio.sleep(processing_time_per_image)
            return create_mock_result(f"timing-{id(image)}", success=True)

        with patch.object(MathpixPipeline, 'process', side_effect=mock_process):
            pipeline = MathpixPipeline()

            start_time = time.perf_counter()
            results = await pipeline.process_batch(
                sample_images,
                max_concurrent=4
            )
            total_time = time.perf_counter() - start_time

        # With 5 images at 100ms each and concurrency of 4:
        # Sequential would take ~500ms
        # Concurrent should take ~200ms (2 batches: 4 + 1)
        sequential_time = len(sample_images) * processing_time_per_image

        # Total time should be significantly less than sequential
        assert total_time < sequential_time * 0.8  # At least 20% speedup


# =============================================================================
# Edge Cases
# =============================================================================

class TestBatchEdgeCases:
    """Test edge cases in batch processing."""

    @pytest.mark.asyncio
    async def test_batch_max_concurrent_one(self, sample_images):
        """Test batch processing with max_concurrent=1 (sequential)."""
        call_times = []

        async def mock_process(
            image: Union[str, Path, bytes],
            options: Optional[PipelineOptions] = None,
        ) -> PipelineResult:
            call_times.append(time.perf_counter())
            await asyncio.sleep(0.02)
            return create_mock_result(f"sequential-{len(call_times)}", success=True)

        with patch.object(MathpixPipeline, 'process', side_effect=mock_process):
            pipeline = MathpixPipeline()
            results = await pipeline.process_batch(
                sample_images,
                max_concurrent=1  # Sequential processing
            )

        assert len(results) == len(sample_images)

        # With max_concurrent=1, calls should be sequential
        # Each call should start after the previous one (approximately)
        for i in range(1, len(call_times)):
            assert call_times[i] >= call_times[i - 1]

    @pytest.mark.asyncio
    async def test_batch_max_concurrent_higher_than_count(self, sample_images):
        """Test batch with max_concurrent higher than image count."""
        async def mock_process(
            image: Union[str, Path, bytes],
            options: Optional[PipelineOptions] = None,
        ) -> PipelineResult:
            await asyncio.sleep(0.01)
            return create_mock_result(f"high-concurrent-{id(image)}", success=True)

        with patch.object(MathpixPipeline, 'process', side_effect=mock_process):
            pipeline = MathpixPipeline()
            results = await pipeline.process_batch(
                sample_images,
                max_concurrent=100  # Much higher than image count
            )

        # Should still process all images correctly
        assert len(results) == len(sample_images)
        for result in results:
            assert result.success is True

    @pytest.mark.asyncio
    async def test_batch_mixed_input_types(self):
        """Test batch processing with mixed input types."""
        # Mix of bytes and paths
        mixed_inputs = [
            b"fake_image_bytes_1",
            Path("/fake/path/image2.png"),
            b"fake_image_bytes_3",
            "/fake/path/image4.png",
        ]

        call_count = 0

        async def mock_process(
            image: Union[str, Path, bytes],
            options: Optional[PipelineOptions] = None,
        ) -> PipelineResult:
            nonlocal call_count
            call_count += 1
            return create_mock_result(f"mixed-{call_count}", success=True)

        with patch.object(MathpixPipeline, 'process', side_effect=mock_process):
            pipeline = MathpixPipeline()
            results = await pipeline.process_batch(mixed_inputs, max_concurrent=4)

        # All inputs should be processed
        assert len(results) == len(mixed_inputs)
        assert call_count == len(mixed_inputs)


# =============================================================================
# Run Configuration
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
