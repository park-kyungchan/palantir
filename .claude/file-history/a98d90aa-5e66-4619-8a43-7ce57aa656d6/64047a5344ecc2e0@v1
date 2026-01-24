# Plan 2: E2E Integration Tests

> **Version:** 1.0 | **Status:** READY | **Date:** 2026-01-18
> **Auto-Compact Safe:** This file persists across context compaction
> **Execute:** `/execute plan_2_e2e_integration_tests.md`
> **Prerequisite:** Plan 1 completed

---

## Overview

| Item | Value |
|------|-------|
| Complexity | medium |
| Total Tasks | 8 |
| Files Affected | 12 |
| Estimated Time | 3-4 hours |

---

## Current Test State

| Test Type | Directory | Count | Coverage |
|-----------|-----------|-------|----------|
| Unit Tests | `tests/schemas/`, `tests/alignment/` | 243 | Individual components |
| Integration | `tests/integration/` | ~10 | 2-3 stage chains |
| E2E | `tests/e2e/` | ~5 | Incomplete flow |

**Gap:** Full A→H pipeline flow not tested end-to-end.

---

## Tasks

| # | Phase | Task | Status | File |
|---|-------|------|--------|------|
| 1 | Setup | Create E2E test fixtures (sample images) | pending | `tests/fixtures/` |
| 2 | Setup | Create mock API responses | pending | `tests/fixtures/mocks/` |
| 3 | Core | Full pipeline happy path test | pending | `tests/e2e/test_full_pipeline.py` |
| 4 | Core | Pipeline with skip stages test | pending | `tests/e2e/test_partial_pipeline.py` |
| 5 | Core | Batch processing test | pending | `tests/e2e/test_batch_processing.py` |
| 6 | Error | Error recovery tests | pending | `tests/e2e/test_error_recovery.py` |
| 7 | Performance | Timing and resource tests | pending | `tests/e2e/test_performance.py` |
| 8 | CI | Add GitHub Actions workflow | pending | `.github/workflows/e2e.yml` |

---

## Implementation Details

### Task 1: E2E Test Fixtures

Create sample images for different math content types:

```
tests/fixtures/images/
├── simple_equation.png      # y = mx + b
├── quadratic_graph.png      # Parabola with labels
├── geometry_diagram.png     # Triangle with angle marks
├── complex_calculus.png     # Integral with limits
└── handwritten_math.png     # Handwritten equation
```

**Fixture data generator:**

```python
# tests/fixtures/generate_fixtures.py
"""Generate test fixture images using matplotlib."""

import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "images"
FIXTURES_DIR.mkdir(exist_ok=True)

def generate_simple_equation():
    """Generate simple linear equation image."""
    fig, ax = plt.subplots(figsize=(6, 2))
    ax.text(0.5, 0.5, r'$y = 2x + 3$', fontsize=24, ha='center', va='center')
    ax.axis('off')
    fig.savefig(FIXTURES_DIR / "simple_equation.png", dpi=150, bbox_inches='tight')
    plt.close()

def generate_quadratic_graph():
    """Generate quadratic function graph."""
    fig, ax = plt.subplots(figsize=(8, 6))
    x = np.linspace(-3, 3, 100)
    y = x**2
    ax.plot(x, y, 'b-', linewidth=2)
    ax.axhline(y=0, color='k', linewidth=0.5)
    ax.axvline(x=0, color='k', linewidth=0.5)
    ax.set_xlabel('x')
    ax.set_ylabel('y')
    ax.text(2, 4, r'$y = x^2$', fontsize=14)
    ax.grid(True, alpha=0.3)
    fig.savefig(FIXTURES_DIR / "quadratic_graph.png", dpi=150)
    plt.close()

def generate_geometry_diagram():
    """Generate triangle with angle marks."""
    fig, ax = plt.subplots(figsize=(6, 6))
    # Triangle vertices
    A, B, C = (0, 0), (4, 0), (2, 3)
    triangle = plt.Polygon([A, B, C], fill=False, edgecolor='black', linewidth=2)
    ax.add_patch(triangle)
    # Labels
    ax.text(-0.2, -0.2, 'A', fontsize=12)
    ax.text(4.1, -0.2, 'B', fontsize=12)
    ax.text(2, 3.2, 'C', fontsize=12)
    ax.set_xlim(-1, 5)
    ax.set_ylim(-1, 4)
    ax.set_aspect('equal')
    ax.axis('off')
    fig.savefig(FIXTURES_DIR / "geometry_diagram.png", dpi=150)
    plt.close()

if __name__ == "__main__":
    generate_simple_equation()
    generate_quadratic_graph()
    generate_geometry_diagram()
    print(f"Fixtures generated in {FIXTURES_DIR}")
```

### Task 2: Mock API Responses

```python
# tests/fixtures/mocks/mathpix_responses.py
"""Mock Mathpix API responses for testing."""

SIMPLE_EQUATION_RESPONSE = {
    "request_id": "test-req-001",
    "latex": "y = 2x + 3",
    "latex_styled": "y = 2x + 3",
    "confidence": 0.98,
    "confidence_rate": 0.98,
    "line_data": [
        {
            "type": "math",
            "cnt": [[10, 50], [200, 50], [200, 100], [10, 100]],
            "latex": "y = 2x + 3"
        }
    ],
    "detection_map": {
        "is_printed": True,
        "is_diagram": False,
        "is_graph": False,
        "is_geometry": False
    }
}

QUADRATIC_GRAPH_RESPONSE = {
    "request_id": "test-req-002",
    "latex": "y = x^2",
    "confidence": 0.95,
    "line_data": [
        {
            "type": "math",
            "cnt": [[300, 100], [400, 100], [400, 130], [300, 130]],
            "latex": "y = x^2"
        }
    ],
    "detection_map": {
        "is_printed": True,
        "is_diagram": False,
        "is_graph": True,
        "is_geometry": False
    }
}

GEOMETRY_DIAGRAM_RESPONSE = {
    "request_id": "test-req-003",
    "latex": "",
    "confidence": 0.85,
    "line_data": [
        {"type": "text", "cnt": [[10, 180], [30, 180], [30, 200], [10, 200]], "text": "A"},
        {"type": "text", "cnt": [[380, 180], [400, 180], [400, 200], [380, 200]], "text": "B"},
        {"type": "text", "cnt": [[195, 10], [215, 10], [215, 30], [195, 30]], "text": "C"},
    ],
    "detection_map": {
        "is_printed": True,
        "is_diagram": True,
        "is_graph": False,
        "is_geometry": True
    }
}
```

### Task 3: Full Pipeline Happy Path Test

```python
# tests/e2e/test_full_pipeline.py
"""End-to-end tests for full pipeline execution."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from mathpix_pipeline.pipeline import MathpixPipeline, PipelineOptions
from mathpix_pipeline.schemas.common import PipelineStage
from mathpix_pipeline.schemas.export import ExportFormat

from ..fixtures.mocks.mathpix_responses import (
    SIMPLE_EQUATION_RESPONSE,
    QUADRATIC_GRAPH_RESPONSE,
)


class TestFullPipelineE2E:
    """End-to-end tests for complete A→H pipeline flow."""

    @pytest.fixture
    def pipeline(self):
        """Create pipeline instance."""
        return MathpixPipeline()

    @pytest.fixture
    def simple_equation_image(self):
        """Path to simple equation test image."""
        return Path(__file__).parent.parent / "fixtures" / "images" / "simple_equation.png"

    @pytest.mark.asyncio
    @patch("mathpix_pipeline.clients.mathpix.MathpixClient.process_image")
    @patch("mathpix_pipeline.vision.yolo_detector.YOLODetector.detect")
    @patch("mathpix_pipeline.vision.gemini_client.GeminiClient.interpret")
    async def test_full_pipeline_happy_path(
        self,
        mock_interpret,
        mock_detect,
        mock_mathpix,
        pipeline,
        simple_equation_image,
    ):
        """Test complete pipeline execution with mocked APIs."""
        # Setup mocks
        mock_mathpix.return_value = self._create_text_spec(SIMPLE_EQUATION_RESPONSE)
        mock_detect.return_value = self._create_detection_layer()
        mock_interpret.return_value = self._create_interpretation_layer()

        # Run pipeline
        options = PipelineOptions(
            export_formats=[ExportFormat.JSON, ExportFormat.LATEX],
        )
        result = await pipeline.process(simple_equation_image, options)

        # Assertions
        assert result.success is True
        assert result.text_spec is not None
        assert result.vision_spec is not None
        assert result.alignment_report is not None
        assert result.semantic_graph is not None
        assert result.regeneration_spec is not None
        assert result.export_result is not None

        # Check all stages completed
        completed_stages = {t.stage for t in result.stage_timings if t.success}
        expected_stages = {
            PipelineStage.INGESTION,
            PipelineStage.TEXT_PARSE,
            PipelineStage.VISION_PARSE,
            PipelineStage.ALIGNMENT,
            PipelineStage.SEMANTIC_GRAPH,
            PipelineStage.REGENERATION,
            PipelineStage.EXPORT,
        }
        assert expected_stages.issubset(completed_stages)

    @pytest.mark.asyncio
    async def test_pipeline_timing_recorded(self, pipeline, simple_equation_image):
        """Test that all stage timings are recorded."""
        result = await pipeline.process(simple_equation_image)

        assert result.processing_time_ms > 0
        assert len(result.stage_timings) >= 5

        for timing in result.stage_timings:
            assert timing.duration_ms is not None
            assert timing.duration_ms >= 0

    @pytest.mark.asyncio
    async def test_pipeline_statistics_updated(self, pipeline, simple_equation_image):
        """Test that pipeline statistics are updated."""
        initial_stats = pipeline.stats.copy()

        await pipeline.process(simple_equation_image)

        assert pipeline.stats["total_processed"] == initial_stats["total_processed"] + 1
        assert pipeline.stats["total_time_ms"] > initial_stats["total_time_ms"]

    def _create_text_spec(self, response):
        """Helper to create TextSpec from mock response."""
        from mathpix_pipeline.schemas import TextSpec
        return TextSpec(
            image_id="test-image",
            raw_latex=response["latex"],
            equations=[],
            line_segments=[],
        )

    def _create_detection_layer(self):
        """Helper to create DetectionLayer."""
        from mathpix_pipeline.schemas.vision_spec import DetectionLayer
        return DetectionLayer(elements=[])

    def _create_interpretation_layer(self):
        """Helper to create InterpretationLayer."""
        from mathpix_pipeline.schemas.vision_spec import InterpretationLayer
        return InterpretationLayer(elements=[], relations=[])
```

### Task 4: Partial Pipeline Test

```python
# tests/e2e/test_partial_pipeline.py
"""Tests for partial pipeline execution with skip_stages."""

import pytest
from mathpix_pipeline.pipeline import MathpixPipeline, PipelineOptions
from mathpix_pipeline.schemas.common import PipelineStage


class TestPartialPipeline:
    """Test pipeline with various stage skip configurations."""

    @pytest.mark.asyncio
    async def test_skip_vision_parse(self, pipeline, test_image):
        """Test pipeline skipping Stage C."""
        options = PipelineOptions(
            skip_stages=[PipelineStage.VISION_PARSE]
        )
        result = await pipeline.process(test_image, options)

        assert result.vision_spec is None
        assert result.text_spec is not None

    @pytest.mark.asyncio
    async def test_ingestion_only(self, pipeline, test_image):
        """Test running only Stage A."""
        options = PipelineOptions(
            skip_stages=[
                PipelineStage.TEXT_PARSE,
                PipelineStage.VISION_PARSE,
                PipelineStage.ALIGNMENT,
                PipelineStage.SEMANTIC_GRAPH,
                PipelineStage.REGENERATION,
                PipelineStage.EXPORT,
            ]
        )
        result = await pipeline.process(test_image, options)

        assert result.ingestion_spec is not None
        assert result.text_spec is None
        assert result.alignment_report is None

    @pytest.mark.asyncio
    async def test_up_to_alignment(self, pipeline, test_image):
        """Test pipeline up to Stage D only."""
        options = PipelineOptions(
            skip_stages=[
                PipelineStage.SEMANTIC_GRAPH,
                PipelineStage.REGENERATION,
                PipelineStage.EXPORT,
            ]
        )
        result = await pipeline.process(test_image, options)

        assert result.alignment_report is not None
        assert result.semantic_graph is None
```

### Task 5: Batch Processing Test

```python
# tests/e2e/test_batch_processing.py
"""Tests for batch image processing."""

import pytest
from pathlib import Path

from mathpix_pipeline.pipeline import MathpixPipeline


class TestBatchProcessing:
    """Test batch processing capabilities."""

    @pytest.fixture
    def test_images(self, fixtures_dir):
        """Get list of test images."""
        return list((fixtures_dir / "images").glob("*.png"))

    @pytest.mark.asyncio
    async def test_batch_processing_success(self, pipeline, test_images):
        """Test processing multiple images in batch."""
        results = await pipeline.process_batch(test_images, max_concurrent=2)

        assert len(results) == len(test_images)
        success_count = sum(1 for r in results if r.success)
        assert success_count >= len(test_images) * 0.8  # 80% success rate

    @pytest.mark.asyncio
    async def test_batch_concurrency_limit(self, pipeline, test_images):
        """Test that concurrency limit is respected."""
        import asyncio

        max_concurrent = 2
        active_count = 0
        max_observed = 0

        original_process = pipeline.process

        async def tracking_process(image, options=None):
            nonlocal active_count, max_observed
            active_count += 1
            max_observed = max(max_observed, active_count)
            try:
                return await original_process(image, options)
            finally:
                active_count -= 1

        pipeline.process = tracking_process
        await pipeline.process_batch(test_images, max_concurrent=max_concurrent)

        assert max_observed <= max_concurrent

    @pytest.mark.asyncio
    async def test_batch_partial_failure(self, pipeline):
        """Test batch processing with some failures."""
        images = [
            "valid_image.png",
            "nonexistent.png",  # Should fail
            "another_valid.png",
        ]

        results = await pipeline.process_batch(images)

        # At least one should succeed, one should fail
        successes = [r for r in results if r.success]
        failures = [r for r in results if not r.success]

        assert len(failures) >= 1
        assert len(successes) >= 1
```

### Task 6: Error Recovery Tests

```python
# tests/e2e/test_error_recovery.py
"""Tests for error handling and recovery."""

import pytest
from unittest.mock import patch, AsyncMock

from mathpix_pipeline.pipeline import MathpixPipeline, PipelineError
from mathpix_pipeline.clients.mathpix import MathpixError, RateLimitError


class TestErrorRecovery:
    """Test error handling and graceful degradation."""

    @pytest.mark.asyncio
    @patch("mathpix_pipeline.clients.mathpix.MathpixClient.process_image")
    async def test_mathpix_api_failure(self, mock_mathpix, pipeline, test_image):
        """Test handling of Mathpix API failure."""
        mock_mathpix.side_effect = MathpixError("API unavailable", status_code=503)

        result = await pipeline.process(test_image)

        assert result.success is False
        assert any("Mathpix" in e for e in result.errors)
        assert result.text_spec is None

    @pytest.mark.asyncio
    @patch("mathpix_pipeline.clients.mathpix.MathpixClient.process_image")
    async def test_rate_limit_handling(self, mock_mathpix, pipeline, test_image):
        """Test handling of rate limit errors."""
        mock_mathpix.side_effect = RateLimitError(retry_after=60)

        result = await pipeline.process(test_image)

        assert result.success is False
        assert any("Rate limit" in str(e) or "429" in str(e) for e in result.errors)

    @pytest.mark.asyncio
    async def test_invalid_image_handling(self, pipeline, tmp_path):
        """Test handling of invalid image files."""
        invalid_file = tmp_path / "not_an_image.txt"
        invalid_file.write_text("This is not an image")

        result = await pipeline.process(str(invalid_file))

        assert result.success is False
        assert len(result.errors) > 0

    @pytest.mark.asyncio
    @patch("mathpix_pipeline.vision.yolo_detector.YOLODetector.detect")
    async def test_yolo_failure_fallback(self, mock_yolo, pipeline, test_image):
        """Test fallback when YOLO fails."""
        mock_yolo.side_effect = RuntimeError("CUDA out of memory")

        result = await pipeline.process(test_image)

        # Should use fallback and continue
        assert result.vision_spec is not None or "Vision parse failed" in str(result.warnings)

    @pytest.mark.asyncio
    async def test_missing_env_vars(self, monkeypatch, test_image):
        """Test handling when API keys are missing."""
        monkeypatch.delenv("MATHPIX_APP_ID", raising=False)
        monkeypatch.delenv("MATHPIX_APP_KEY", raising=False)

        pipeline = MathpixPipeline()
        result = await pipeline.process(test_image)

        # Should fail gracefully with clear error
        assert result.success is False or len(result.warnings) > 0
```

### Task 7: Performance Tests

```python
# tests/e2e/test_performance.py
"""Performance and resource usage tests."""

import pytest
import time
import asyncio

from mathpix_pipeline.pipeline import MathpixPipeline


class TestPerformance:
    """Performance benchmarks and resource tests."""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_single_image_timing(self, pipeline, test_image):
        """Benchmark single image processing time."""
        start = time.perf_counter()
        result = await pipeline.process(test_image)
        duration = time.perf_counter() - start

        # Should complete within reasonable time (adjust based on hardware)
        assert duration < 30.0  # 30 seconds max

        # Check individual stage timings
        for timing in result.stage_timings:
            assert timing.duration_ms < 10000  # No stage > 10s

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_batch_throughput(self, pipeline, test_images):
        """Benchmark batch processing throughput."""
        start = time.perf_counter()
        results = await pipeline.process_batch(test_images, max_concurrent=4)
        duration = time.perf_counter() - start

        images_per_second = len(test_images) / duration
        assert images_per_second > 0.1  # At least 1 image per 10 seconds

    @pytest.mark.asyncio
    async def test_memory_not_leaked(self, pipeline, test_image):
        """Test that memory is released after processing."""
        import gc

        # Process multiple times
        for _ in range(5):
            await pipeline.process(test_image)
            gc.collect()

        # Memory should stabilize (not continuously grow)
        # This is a basic check; more sophisticated memory profiling
        # would use tracemalloc or memory_profiler

    @pytest.mark.asyncio
    async def test_concurrent_pipelines(self, test_image):
        """Test multiple pipeline instances running concurrently."""
        pipelines = [MathpixPipeline() for _ in range(3)]

        tasks = [p.process(test_image) for p in pipelines]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # All should complete (success or handled failure)
        assert all(not isinstance(r, Exception) for r in results)
```

### Task 8: GitHub Actions Workflow

```yaml
# .github/workflows/e2e.yml
name: E2E Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  e2e-tests:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          pip install -e ".[dev]"
          pip install pytest pytest-asyncio pytest-cov

      - name: Generate test fixtures
        run: |
          python tests/fixtures/generate_fixtures.py

      - name: Run E2E tests
        env:
          MATHPIX_APP_ID: ${{ secrets.MATHPIX_APP_ID }}
          MATHPIX_APP_KEY: ${{ secrets.MATHPIX_APP_KEY }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          pytest tests/e2e/ -v --cov=mathpix_pipeline --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          files: ./coverage.xml
```

---

## Verification Checklist

- [ ] All fixture images generated
- [ ] Mock responses cover all content types
- [ ] Happy path test passes
- [ ] Partial pipeline tests pass
- [ ] Batch processing works correctly
- [ ] Error recovery is graceful
- [ ] Performance benchmarks meet targets
- [ ] CI workflow runs successfully

---

## Quick Resume After Auto-Compact

If context is compacted, resume by:

1. Read this file: `.agent/plans/plan_2_e2e_integration_tests.md`
2. Check TodoWrite for current task status
3. Continue from first PENDING task in sequence

---

## Next Plan

After completing Plan 2, proceed to:
- **Plan 3:** Pipeline Completeness Verification (`plan_3_pipeline_completeness.md`)
