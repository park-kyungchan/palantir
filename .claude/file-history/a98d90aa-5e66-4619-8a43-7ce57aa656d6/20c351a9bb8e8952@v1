# Plan 1: Stage B/C API Integration

> **Version:** 1.0 | **Status:** READY | **Date:** 2026-01-18
> **Auto-Compact Safe:** This file persists across context compaction
> **Execute:** `/execute plan_1_stage_bc_api_integration.md`

---

## Overview

| Item | Value |
|------|-------|
| Complexity | medium |
| Total Tasks | 6 |
| Files Affected | 8 |
| Estimated Time | 2-3 hours |

---

## Current State Analysis

### Stage B (TextParse) - `pipeline.py:485-531`
- **Status:** Placeholder implementation
- **Issue:** Returns empty `TextSpec` instead of calling Mathpix API
- **Required:** Connect to existing `MathpixClient` in `clients/mathpix.py`

### Stage C (VisionParse) - `pipeline.py:533-585`
- **Status:** Placeholder implementation
- **Issue:** Returns empty `VisionSpec` instead of running YOLO + Claude
- **Required:** Connect to existing vision components in `vision/` directory

---

## Tasks

| # | Phase | Task | Status | File |
|---|-------|------|--------|------|
| 1 | Setup | Add MathpixClient import to pipeline.py | pending | `pipeline.py` |
| 2 | Stage B | Implement `_run_stage_b` with MathpixClient | pending | `pipeline.py` |
| 3 | Stage B | Add error handling for API failures | pending | `pipeline.py` |
| 4 | Stage C | Implement `_run_stage_c` with VisionPipeline | pending | `pipeline.py` |
| 5 | Stage C | Add fallback logic for YOLO/Claude failures | pending | `pipeline.py` |
| 6 | Test | Add integration tests for Stage B/C | pending | `tests/integration/` |

---

## Implementation Details

### Task 1: Add MathpixClient Import

```python
# Location: pipeline.py, after line 63

# Stage B: Text Parse (Mathpix)
from .clients.mathpix import MathpixClient, MathpixConfig, MathpixError
```

### Task 2: Implement `_run_stage_b`

**Replace** `_run_stage_b` method in `pipeline.py`:

```python
async def _run_stage_b(
    self,
    ingestion_spec: Optional[IngestionSpec],
    result: PipelineResult,
) -> Optional[TextSpec]:
    """Run Stage B: Text Parse using Mathpix API.

    Calls Mathpix API to extract:
    - LaTeX equations
    - Line segments with positions
    - Content flags (has_diagram, has_graph, etc.)

    Args:
        ingestion_spec: Stage A output with image data
        result: Pipeline result to update

    Returns:
        TextSpec with extracted text elements
    """
    timing = StageTiming(stage=PipelineStage.TEXT_PARSE)
    result.stage_timings.append(timing)

    try:
        if not ingestion_spec:
            result.add_warning(
                "Skipping text parse: no ingestion spec",
                PipelineStage.TEXT_PARSE,
            )
            timing.complete(success=True)
            return None

        # Initialize Mathpix client if not exists
        if not hasattr(self, '_mathpix_client'):
            self._mathpix_client = MathpixClient(
                config=getattr(self, 'mathpix_config', MathpixConfig())
            )

        # Get image bytes from storage
        image_bytes = await self._storage_manager.get_image_bytes(
            ingestion_spec.image_id
        )

        # Call Mathpix API
        text_spec = await self._mathpix_client.process_image(
            image_bytes,
            image_id=ingestion_spec.image_id,
        )

        # Log extraction stats
        logger.info(
            f"Stage B completed: {len(text_spec.equations)} equations, "
            f"{len(text_spec.line_segments)} line segments"
        )

        result.mark_stage_complete(PipelineStage.TEXT_PARSE)
        timing.complete(success=True)

        return text_spec

    except MathpixError as e:
        timing.complete(success=False, error=str(e))
        result.add_error(f"Mathpix API error: {e}", PipelineStage.TEXT_PARSE)
        return None

    except Exception as e:
        timing.complete(success=False, error=str(e))
        result.add_error(f"Text parse failed: {e}", PipelineStage.TEXT_PARSE)
        return None
```

### Task 3: Add Error Handling

Add retry configuration to `__init__`:

```python
def __init__(
    self,
    # ... existing params ...
    mathpix_config: Optional[MathpixConfig] = None,
):
    # ... existing code ...
    self.mathpix_config = mathpix_config or MathpixConfig()
```

### Task 4: Implement `_run_stage_c`

**Replace** `_run_stage_c` method:

```python
async def _run_stage_c(
    self,
    ingestion_spec: Optional[IngestionSpec],
    result: PipelineResult,
) -> Optional[VisionSpec]:
    """Run Stage C: Vision Parse using YOLO + Claude.

    Runs two-layer detection:
    1. YOLO for object detection (fast, local)
    2. Claude for semantic interpretation (accurate, API)
    3. Hybrid merger to combine results

    Args:
        ingestion_spec: Stage A output with image data
        result: Pipeline result to update

    Returns:
        VisionSpec with visual elements and relations
    """
    timing = StageTiming(stage=PipelineStage.VISION_PARSE)
    result.stage_timings.append(timing)

    try:
        if not ingestion_spec:
            result.add_warning(
                "Skipping vision parse: no ingestion spec",
                PipelineStage.VISION_PARSE,
            )
            timing.complete(success=True)
            return None

        # Get image bytes
        image_bytes = await self._storage_manager.get_image_bytes(
            ingestion_spec.image_id
        )

        # Initialize vision components if needed
        if not hasattr(self, '_yolo_detector'):
            from .vision import YOLODetector, GeminiClient, HybridMerger
            self._yolo_detector = YOLODetector()
            self._gemini_client = GeminiClient()
            self._hybrid_merger = HybridMerger()

        # Layer 1: YOLO detection
        detection_layer = await self._yolo_detector.detect(image_bytes)

        # Layer 2: Claude/Gemini interpretation
        interpretation_layer = await self._gemini_client.interpret(
            image_bytes,
            detection_hints=detection_layer.elements,
        )

        # Merge results
        merged_output = self._hybrid_merger.merge(
            detection_layer,
            interpretation_layer,
        )

        # Build VisionSpec
        vision_spec = VisionSpec(
            image_id=ingestion_spec.image_id,
            detection_layer=detection_layer,
            interpretation_layer=interpretation_layer,
            merged_output=merged_output,
        )

        logger.info(
            f"Stage C completed: {len(merged_output.elements)} elements detected"
        )

        result.mark_stage_complete(PipelineStage.VISION_PARSE)
        timing.complete(success=True)

        return vision_spec

    except Exception as e:
        timing.complete(success=False, error=str(e))
        result.add_error(f"Vision parse failed: {e}", PipelineStage.VISION_PARSE)
        return None
```

### Task 5: Add Fallback Logic

```python
# Add fallback in _run_stage_c after YOLO detection

# Layer 1: YOLO detection with fallback
try:
    detection_layer = await self._yolo_detector.detect(image_bytes)
except Exception as yolo_error:
    logger.warning(f"YOLO detection failed, using fallback: {yolo_error}")
    detection_layer = DetectionLayer(elements=[])

# Layer 2: Claude interpretation with fallback
try:
    interpretation_layer = await self._gemini_client.interpret(
        image_bytes,
        detection_hints=detection_layer.elements,
    )
except Exception as claude_error:
    logger.warning(f"Claude interpretation failed, using fallback: {claude_error}")
    from .vision.fallback import create_fallback_interpretation
    interpretation_layer = create_fallback_interpretation(detection_layer)
```

### Task 6: Integration Tests

Create `tests/integration/test_stage_bc_integration.py`:

```python
"""Integration tests for Stage B and C."""

import pytest
from pathlib import Path

from mathpix_pipeline.pipeline import MathpixPipeline, PipelineOptions
from mathpix_pipeline.schemas.common import PipelineStage


class TestStageBIntegration:
    """Integration tests for Stage B (TextParse)."""

    @pytest.mark.asyncio
    async def test_stage_b_with_real_image(self, sample_math_image):
        """Test Stage B with a real math image."""
        pipeline = MathpixPipeline()

        options = PipelineOptions(
            skip_stages=[
                PipelineStage.VISION_PARSE,
                PipelineStage.ALIGNMENT,
                PipelineStage.SEMANTIC_GRAPH,
                PipelineStage.REGENERATION,
                PipelineStage.EXPORT,
            ]
        )

        result = await pipeline.process(sample_math_image, options)

        assert result.text_spec is not None
        assert result.text_spec.image_id is not None


class TestStageCIntegration:
    """Integration tests for Stage C (VisionParse)."""

    @pytest.mark.asyncio
    async def test_stage_c_with_diagram(self, sample_diagram_image):
        """Test Stage C with a diagram image."""
        pipeline = MathpixPipeline()

        options = PipelineOptions(
            skip_stages=[
                PipelineStage.TEXT_PARSE,
                PipelineStage.ALIGNMENT,
                PipelineStage.SEMANTIC_GRAPH,
                PipelineStage.REGENERATION,
                PipelineStage.EXPORT,
            ]
        )

        result = await pipeline.process(sample_diagram_image, options)

        assert result.vision_spec is not None
        assert len(result.vision_spec.merged_output.elements) > 0
```

---

## Verification Checklist

- [ ] MathpixClient properly imported and initialized
- [ ] Stage B calls real Mathpix API
- [ ] Stage C runs YOLO + Claude pipeline
- [ ] Error handling covers all failure modes
- [ ] Fallback logic works when components fail
- [ ] Integration tests pass

---

## Dependencies

| Dependency | Required For | Status |
|------------|--------------|--------|
| `httpx` | MathpixClient | installed |
| `torch` | YOLO detector | verify |
| `anthropic` | Claude API | verify |
| `MATHPIX_APP_ID` | API auth | env var needed |
| `MATHPIX_APP_KEY` | API auth | env var needed |
| `ANTHROPIC_API_KEY` | Claude API | env var needed |

---

## Quick Resume After Auto-Compact

If context is compacted, resume by:

1. Read this file: `.agent/plans/plan_1_stage_bc_api_integration.md`
2. Check TodoWrite for current task status
3. Continue from first PENDING task in sequence

---

## Next Plan

After completing Plan 1, proceed to:
- **Plan 2:** E2E Integration Tests (`plan_2_e2e_integration_tests.md`)
