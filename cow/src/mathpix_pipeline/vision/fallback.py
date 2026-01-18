"""
Fallback Strategy for Stage C (Vision Parse).

Implements fallback chain:
1. Primary: YOLO26 + Claude Opus 4.5
2. Fallback 1: Gemini 2.5 (zero-shot)
3. Fallback 2: Manual annotation (Stage G immediate entry)

Schema Version: 2.0.0
"""

import asyncio
import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ..schemas import (
    DetectionLayer,
    InterpretationLayer,
    VisionSpec,
    Provenance,
    PipelineStage,
    ReviewMetadata,
    ReviewSeverity,
)
from .exceptions import (
    GeminiAPIError,
    GeminiNotConfiguredError,
    GeminiRateLimitError,
    GeminiResponseParseError,
    GeminiTimeoutError,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Enums
# =============================================================================

class FallbackLevel(str, Enum):
    """Fallback strategy levels."""
    PRIMARY = "primary"  # YOLO + Claude
    GEMINI = "gemini"  # Gemini zero-shot
    MANUAL = "manual"  # Manual annotation required


class FailureReason(str, Enum):
    """Reasons for fallback trigger."""
    YOLO_FAILED = "yolo_detection_failed"
    YOLO_NO_DETECTIONS = "yolo_no_detections"
    YOLO_LOW_CONFIDENCE = "yolo_low_confidence"
    CLAUDE_FAILED = "claude_interpretation_failed"
    CLAUDE_LOW_CONFIDENCE = "claude_low_confidence"
    GEMINI_FAILED = "gemini_fallback_failed"
    TIMEOUT = "processing_timeout"
    UNKNOWN = "unknown_error"


# =============================================================================
# Configuration
# =============================================================================

@dataclass
class FallbackConfig:
    """Configuration for fallback strategy."""
    # YOLO fallback triggers
    min_detection_count: int = 1
    min_detection_confidence: float = 0.3
    yolo_timeout_seconds: float = 30.0

    # Claude fallback triggers
    min_interpretation_confidence: float = 0.4
    claude_timeout_seconds: float = 60.0

    # Gemini configuration (fallback)
    gemini_model: str = "gemini-2.0-flash"
    gemini_timeout_seconds: float = 45.0

    # Manual annotation settings
    priority_boost_on_manual: int = 2  # Boost review priority

    # Enable/disable fallbacks
    enable_gemini_fallback: bool = True
    enable_manual_fallback: bool = True


# =============================================================================
# Fallback Executor
# =============================================================================

class FallbackExecutor:
    """Executes fallback strategy for Vision Parse.

    Handles failure recovery through the fallback chain:
    YOLO + Claude → Gemini → Manual

    Usage:
        config = FallbackConfig()
        executor = FallbackExecutor(config)

        result = await executor.execute_with_fallback(image, image_id)
    """

    def __init__(self, config: Optional[FallbackConfig] = None):
        """Initialize fallback executor.

        Args:
            config: Fallback configuration
        """
        self.config = config or FallbackConfig()
        self._yolo_detector = None
        self._claude_interpreter = None
        self._gemini_client = None

    def _check_yolo_success(
        self,
        detection_layer: Optional[DetectionLayer],
    ) -> tuple[bool, Optional[FailureReason]]:
        """Check if YOLO detection was successful.

        Args:
            detection_layer: YOLO detection result

        Returns:
            Tuple of (success, failure_reason if failed)
        """
        if detection_layer is None:
            return False, FailureReason.YOLO_FAILED

        if len(detection_layer.elements) < self.config.min_detection_count:
            return False, FailureReason.YOLO_NO_DETECTIONS

        # Check average confidence
        if detection_layer.elements:
            avg_conf = sum(e.detection_confidence for e in detection_layer.elements) / len(detection_layer.elements)
            if avg_conf < self.config.min_detection_confidence:
                return False, FailureReason.YOLO_LOW_CONFIDENCE

        return True, None

    def _check_interpretation_success(
        self,
        interpretation_layer: Optional[InterpretationLayer],
    ) -> tuple[bool, Optional[FailureReason]]:
        """Check if Claude interpretation was successful.

        Args:
            interpretation_layer: Claude interpretation result

        Returns:
            Tuple of (success, failure_reason if failed)
        """
        if interpretation_layer is None:
            return False, FailureReason.CLAUDE_FAILED

        if not interpretation_layer.elements:
            return False, FailureReason.CLAUDE_FAILED

        # Check average confidence
        avg_conf = sum(e.interpretation_confidence for e in interpretation_layer.elements) / len(interpretation_layer.elements)
        if avg_conf < self.config.min_interpretation_confidence:
            return False, FailureReason.CLAUDE_LOW_CONFIDENCE

        return True, None

    async def _try_gemini_fallback(
        self,
        image: Union[str, Path, bytes],
        image_id: str,
    ) -> Optional[VisionSpec]:
        """Attempt Gemini zero-shot fallback.

        Uses GeminiVisionClient for combined bbox detection and
        semantic interpretation when YOLO + Claude fails.

        Args:
            image: Image to process
            image_id: Image identifier

        Returns:
            VisionSpec if successful, None otherwise
        """
        if not self.config.enable_gemini_fallback:
            return None

        logger.info(f"Attempting Gemini fallback for {image_id}")

        try:
            # Import Gemini client
            from .gemini_client import GeminiVisionClient

            # Create client with config
            client = GeminiVisionClient(
                model=self.config.gemini_model,
                timeout_seconds=self.config.gemini_timeout_seconds,
                max_retries=2,
            )

            # Execute fallback detection and interpretation
            result = await client.detect_and_interpret(image, image_id)

            if result:
                logger.info(
                    f"Gemini fallback succeeded for {image_id}: "
                    f"{len(result.merged_output.elements)} elements"
                )
            else:
                logger.warning(f"Gemini fallback returned None for {image_id}")

            return result

        except GeminiNotConfiguredError as e:
            logger.warning(f"Gemini not configured: {e}")
            return None
        except GeminiTimeoutError as e:
            logger.warning(f"Gemini timeout for {image_id}: {e}")
            return None
        except GeminiResponseParseError as e:
            logger.error(f"Gemini parse error for {image_id}: {e}")
            return None
        except GeminiRateLimitError as e:
            logger.warning(f"Gemini rate limited for {image_id}: {e}")
            return None
        except GeminiAPIError as e:
            logger.error(f"Gemini API error for {image_id}: {e}")
            return None
        except ImportError:
            logger.warning("google-generativeai not installed, skipping Gemini fallback")
            return None
        except Exception as e:
            # Catch-all for unexpected errors - log with full traceback
            logger.exception(
                f"Unexpected Gemini fallback error for {image_id}: "
                f"{type(e).__name__}: {e}"
            )
            return None

    def _create_manual_fallback_spec(
        self,
        image_id: str,
        failure_reason: FailureReason,
    ) -> VisionSpec:
        """Create VisionSpec marking manual annotation required.

        Args:
            image_id: Image identifier
            failure_reason: Why fallback was triggered

        Returns:
            VisionSpec with manual review flag
        """
        review = ReviewMetadata(
            review_required=True,
            review_severity=ReviewSeverity.CRITICAL,
            review_reason=f"Manual annotation required: {failure_reason.value}",
        )

        provenance = Provenance(
            stage=PipelineStage.VISION_PARSE,
            model="manual-required",
        )

        return VisionSpec(
            image_id=image_id,
            provenance=provenance,
            fallback_used=True,
            fallback_model="manual",
            fallback_reason=failure_reason.value,
            overall_confidence=0.0,
            review=review,
        )

    async def execute_with_fallback(
        self,
        image: Union[str, Path, bytes],
        image_id: str,
        yolo_detector: Any = None,
        claude_interpreter: Any = None,
    ) -> tuple[VisionSpec, FallbackLevel]:
        """Execute vision parsing with fallback chain.

        Args:
            image: Image to process
            image_id: Image identifier
            yolo_detector: Optional pre-configured YOLO detector
            claude_interpreter: Optional pre-configured Claude interpreter

        Returns:
            Tuple of (VisionSpec result, FallbackLevel used)
        """
        from .yolo_detector import create_detector
        from .interpretation_layer import create_interpreter
        from .hybrid_merger import HybridMerger

        # Use provided instances or create new ones
        yolo = yolo_detector or create_detector(use_mock=True)  # Default to mock for safety
        interpreter = claude_interpreter or create_interpreter(use_mock=True)
        merger = HybridMerger()

        # Phase 1: Try YOLO detection
        detection_layer: Optional[DetectionLayer] = None
        try:
            detection_layer = yolo.detect(image, image_id)
        except Exception as e:
            logger.error(f"YOLO detection failed: {e}")

        yolo_success, yolo_failure = self._check_yolo_success(detection_layer)

        if not yolo_success:
            logger.warning(f"YOLO failed: {yolo_failure}, trying Gemini fallback")

            # Try Gemini fallback
            gemini_result = await self._try_gemini_fallback(image, image_id)
            if gemini_result:
                return gemini_result, FallbackLevel.GEMINI

            # Gemini failed, return manual fallback
            if self.config.enable_manual_fallback:
                return self._create_manual_fallback_spec(
                    image_id,
                    yolo_failure or FailureReason.UNKNOWN,
                ), FallbackLevel.MANUAL

        # Phase 2: Try Claude interpretation
        interpretation_layer: Optional[InterpretationLayer] = None
        try:
            interpretation_layer = await interpreter.interpret(
                image,
                detection_layer,
                image_id,
            )
        except Exception as e:
            logger.error(f"Claude interpretation failed: {e}")

        interp_success, interp_failure = self._check_interpretation_success(interpretation_layer)

        if not interp_success:
            logger.warning(f"Claude failed: {interp_failure}, trying Gemini fallback")

            # Try Gemini fallback
            gemini_result = await self._try_gemini_fallback(image, image_id)
            if gemini_result:
                return gemini_result, FallbackLevel.GEMINI

            # Continue with detection-only (degraded mode)
            if detection_layer and detection_layer.elements:
                logger.info("Continuing with detection-only mode")
                interpretation_layer = InterpretationLayer(model="none")

        # Phase 3: Merge results
        merged_output = merger.merge(
            detection_layer or DetectionLayer(),
            interpretation_layer or InterpretationLayer(model="none"),
            image_id,
        )

        # Build final VisionSpec
        total_time = 0.0
        if detection_layer and detection_layer.inference_time_ms:
            total_time += detection_layer.inference_time_ms
        if interpretation_layer and interpretation_layer.inference_time_ms:
            total_time += interpretation_layer.inference_time_ms

        provenance = Provenance(
            stage=PipelineStage.VISION_PARSE,
            model="hybrid-yolo26-claude",
            processing_time_ms=total_time,
        )

        vision_spec = VisionSpec(
            image_id=image_id,
            provenance=provenance,
            detection_layer=detection_layer or DetectionLayer(),
            interpretation_layer=interpretation_layer or InterpretationLayer(model="none"),
            merged_output=merged_output,
            fallback_used=not (yolo_success and interp_success),
            fallback_model=None if yolo_success and interp_success else "degraded",
            fallback_reason=None if yolo_success and interp_success else str(interp_failure or yolo_failure),
            total_processing_time_ms=total_time,
        )

        return vision_spec, FallbackLevel.PRIMARY


# =============================================================================
# Convenience Functions
# =============================================================================

async def process_with_fallback(
    image: Union[str, Path, bytes],
    image_id: str,
    config: Optional[FallbackConfig] = None,
) -> VisionSpec:
    """Process image with full fallback chain.

    Convenience function for simple usage.

    Args:
        image: Image to process
        image_id: Image identifier
        config: Optional fallback configuration

    Returns:
        VisionSpec result
    """
    executor = FallbackExecutor(config)
    vision_spec, level = await executor.execute_with_fallback(image, image_id)

    if level != FallbackLevel.PRIMARY:
        logger.info(f"Used fallback level: {level.value} for {image_id}")

    return vision_spec


# =============================================================================
# Export
# =============================================================================

__all__ = [
    "FallbackLevel",
    "FailureReason",
    "FallbackConfig",
    "FallbackExecutor",
    "process_with_fallback",
]
