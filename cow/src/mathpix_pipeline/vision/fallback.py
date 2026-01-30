"""
Fallback Strategy for Stage C (Vision Parse) - V2.0.

Implements redesigned fallback chain (Gemini-First Architecture):
1. Primary: Gemini 3 Pro (unified detection + interpretation)
2. Fallback: YOLO26 + Claude Opus 4.5 (legacy pipeline)
3. Manual: Manual annotation (Stage G immediate entry)

Schema Version: 3.0.0
Reference: .agent/prompts/stage-c-redesign-20260130/plan.yaml → task-2.1
"""

import asyncio
import logging
import time
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
from ..schemas.vision_spec import (
    GeminiElement,
    GeminiVisionLayer,
    DiagramAnalysis,
    DiagramType,
    ElementClass,
)
from ..schemas.common import BBox, CombinedConfidence
from .coordinate_converter import convert_box_2d_to_bbox

logger = logging.getLogger(__name__)


# =============================================================================
# Enums (Updated for Gemini-First Architecture)
# =============================================================================

class FallbackLevel(str, Enum):
    """Fallback strategy levels (Gemini-First order)."""
    GEMINI_PRIMARY = "gemini_primary"  # Gemini 3 Pro (unified)
    YOLO_CLAUDE = "yolo_claude"        # Legacy YOLO + Claude fallback
    MANUAL = "manual"                  # Manual annotation required


class FailureReason(str, Enum):
    """Reasons for fallback trigger."""
    # Gemini failures
    GEMINI_NOT_CONFIGURED = "gemini_not_configured"
    GEMINI_API_ERROR = "gemini_api_error"
    GEMINI_TIMEOUT = "gemini_timeout"
    GEMINI_RATE_LIMITED = "gemini_rate_limited"
    GEMINI_PARSE_ERROR = "gemini_parse_error"
    GEMINI_NO_DETECTIONS = "gemini_no_detections"
    GEMINI_LOW_CONFIDENCE = "gemini_low_confidence"

    # YOLO+Claude failures (fallback)
    YOLO_FAILED = "yolo_detection_failed"
    YOLO_NO_DETECTIONS = "yolo_no_detections"
    YOLO_LOW_CONFIDENCE = "yolo_low_confidence"
    CLAUDE_FAILED = "claude_interpretation_failed"
    CLAUDE_LOW_CONFIDENCE = "claude_low_confidence"

    # General
    TIMEOUT = "processing_timeout"
    UNKNOWN = "unknown_error"


# =============================================================================
# Circuit Breaker (for API Stability)
# =============================================================================

class CircuitState(str, Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, skip to fallback
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class CircuitBreaker:
    """
    Circuit breaker for Gemini API calls.

    Prevents cascade failures by short-circuiting to fallback
    when consecutive failures exceed threshold.
    """
    failure_threshold: int = 5       # Failures before opening circuit
    recovery_timeout: float = 60.0   # Seconds before half-open test
    half_open_success_threshold: int = 2  # Successes to close circuit

    _state: CircuitState = field(default=CircuitState.CLOSED, repr=False)
    _failures: int = field(default=0, repr=False)
    _last_failure_time: float = field(default=0.0, repr=False)
    _half_open_successes: int = field(default=0, repr=False)

    @property
    def state(self) -> CircuitState:
        """Get current circuit state with time-based transition."""
        if self._state == CircuitState.OPEN:
            if time.time() - self._last_failure_time > self.recovery_timeout:
                self._state = CircuitState.HALF_OPEN
                self._half_open_successes = 0
                logger.info("Circuit breaker transitioning to HALF_OPEN")
        return self._state

    def record_success(self):
        """Record successful API call."""
        if self._state == CircuitState.HALF_OPEN:
            self._half_open_successes += 1
            if self._half_open_successes >= self.half_open_success_threshold:
                self._state = CircuitState.CLOSED
                self._failures = 0
                logger.info("Circuit breaker CLOSED after recovery")
        elif self._state == CircuitState.CLOSED:
            self._failures = 0

    def record_failure(self):
        """Record failed API call."""
        self._failures += 1
        self._last_failure_time = time.time()

        if self._state == CircuitState.HALF_OPEN:
            self._state = CircuitState.OPEN
            logger.warning("Circuit breaker re-opened after half-open failure")
        elif self._failures >= self.failure_threshold:
            self._state = CircuitState.OPEN
            logger.warning(f"Circuit breaker OPEN after {self._failures} failures")

    def is_available(self) -> bool:
        """Check if circuit allows requests."""
        return self.state in (CircuitState.CLOSED, CircuitState.HALF_OPEN)


# =============================================================================
# Configuration (Updated)
# =============================================================================

@dataclass
class FallbackConfig:
    """Configuration for Gemini-First fallback strategy."""
    # Gemini primary settings
    gemini_model: str = "gemini-2.5-flash"  # Stable model
    gemini_timeout_seconds: float = 60.0
    gemini_min_confidence: float = 0.3
    gemini_min_elements: int = 1

    # Circuit breaker settings
    circuit_failure_threshold: int = 5
    circuit_recovery_timeout: float = 60.0

    # YOLO+Claude fallback settings (legacy)
    yolo_timeout_seconds: float = 30.0
    claude_timeout_seconds: float = 60.0
    min_detection_count: int = 1
    min_detection_confidence: float = 0.3
    min_interpretation_confidence: float = 0.4

    # Manual annotation settings
    priority_boost_on_manual: int = 2  # Boost review priority

    # Enable/disable fallbacks
    enable_yolo_claude_fallback: bool = True
    enable_manual_fallback: bool = True

    # Feature flags
    gemini_enabled: bool = True
    gemini_primary: bool = True  # False = use legacy YOLO+Claude as primary


# =============================================================================
# GeminiVisionLayer → VisionSpec Converter
# =============================================================================

def convert_gemini_to_vision_spec(
    gemini_layer: GeminiVisionLayer,
    image_id: str,
    processing_time_ms: float = 0.0,
) -> VisionSpec:
    """
    Convert GeminiVisionLayer to VisionSpec for Stage D compatibility.

    This ensures the new Gemini output format is compatible with
    the existing pipeline that expects VisionSpec.

    Args:
        gemini_layer: Gemini detection result
        image_id: Image identifier
        processing_time_ms: Total processing time

    Returns:
        VisionSpec compatible with Stage D
    """
    from ..schemas import MergedOutput, MergedElement

    # Convert GeminiElements to MergedElements
    merged_elements = []
    for ge in gemini_layer.elements:
        # Convert box_2d [ymin, xmin, ymax, xmax] 0-1000 to BBox 0-1
        # Use robust convert_box_2d_to_bbox() with edge case handling
        if ge.box_2d and len(ge.box_2d) == 4:
            bbox = convert_box_2d_to_bbox(ge.box_2d, clamp_to_valid=True)
        else:
            # Default bbox for malformed box_2d
            bbox = BBox(x=0.0, y=0.0, width=0.1, height=0.1)
            logger.warning(f"Malformed box_2d for element {ge.id}: {ge.box_2d}")

        # Create CombinedConfidence from Gemini calibrated values
        # For Gemini-only path, detection and interpretation come from same model
        calibrated = ge.calibrated_confidence if ge.calibrated_confidence else ge.confidence
        combined_conf = CombinedConfidence(
            detection_confidence=ge.confidence,
            interpretation_confidence=calibrated,
            combined_value=calibrated,
            bbox_source=gemini_layer.model,
            label_source=gemini_layer.model,
        )

        merged_elements.append(MergedElement(
            id=ge.id,
            bbox=bbox,
            element_class=ge.element_class,
            semantic_label=ge.semantic_label or ge.label or "unknown",
            combined_confidence=combined_conf,
            bbox_source=gemini_layer.model,
            label_source=gemini_layer.model,
        ))

    # Build MergedOutput
    # Extract diagram info from gemini_layer if available
    diagram_type = DiagramType.UNKNOWN
    coordinate_system = None
    if gemini_layer.diagram_analysis:
        # Map string diagram_type to enum if needed
        dt = gemini_layer.diagram_analysis.diagram_type
        if isinstance(dt, str):
            diagram_type = DiagramType(dt) if dt in [e.value for e in DiagramType] else DiagramType.UNKNOWN
        else:
            diagram_type = dt
        coordinate_system = gemini_layer.diagram_analysis.coordinate_system

    merged_output = MergedOutput(
        elements=merged_elements,
        diagram_type=diagram_type,
        coordinate_system=coordinate_system,
        matched_count=len(merged_elements),  # All elements from Gemini
    )

    # Build provenance
    provenance = Provenance(
        stage=PipelineStage.VISION_PARSE,
        model=gemini_layer.model,
        processing_time_ms=processing_time_ms,
    )

    return VisionSpec(
        image_id=image_id,
        provenance=provenance,
        merged_output=merged_output,
        gemini_layer=gemini_layer,  # Preserve original Gemini data
        fallback_used=False,
        fallback_model=None,
        total_processing_time_ms=processing_time_ms,
    )


# =============================================================================
# Fallback Executor (Gemini-First)
# =============================================================================

class FallbackExecutor:
    """
    Executes Gemini-First fallback strategy for Vision Parse.

    Fallback chain: Gemini → YOLO+Claude → Manual

    Usage:
        config = FallbackConfig()
        executor = FallbackExecutor(config)
        result = await executor.execute_with_fallback(image, image_id)
    """

    def __init__(self, config: Optional[FallbackConfig] = None):
        """
        Initialize fallback executor.

        Args:
            config: Fallback configuration
        """
        self.config = config or FallbackConfig()
        self._circuit_breaker = CircuitBreaker(
            failure_threshold=self.config.circuit_failure_threshold,
            recovery_timeout=self.config.circuit_recovery_timeout,
        )
        self._gemini_client = None
        self._yolo_detector = None
        self._claude_interpreter = None

    # =========================================================================
    # Gemini Primary
    # =========================================================================

    async def _try_gemini_primary(
        self,
        image: Union[str, Path, bytes],
        image_id: str,
    ) -> Optional[VisionSpec]:
        """
        Attempt Gemini 3 Pro as primary detector/interpreter.

        Args:
            image: Image to process
            image_id: Image identifier

        Returns:
            VisionSpec if successful, None otherwise
        """
        if not self.config.gemini_enabled or not self.config.gemini_primary:
            return None

        if not self._circuit_breaker.is_available():
            logger.info("Gemini circuit breaker OPEN, skipping to fallback")
            return None

        logger.info(f"Processing {image_id} with Gemini primary")

        try:
            # Import new Gemini client
            from .gemini_vision_client import (
                GeminiVisionClient,
                GeminiClientError,
                GeminiAPIError,
                GeminiParseError,
            )
            from .gemini.config import GeminiConfig, FallbackBehavior

            # Create/reuse client
            if self._gemini_client is None:
                config = GeminiConfig(
                    model=self.config.gemini_model,
                    timeout=self.config.gemini_timeout_seconds,
                    fallback_behavior=FallbackBehavior.NONE,  # We handle fallback
                )
                self._gemini_client = GeminiVisionClient(config)

            # Run detection
            start_time = time.time()
            gemini_layer = self._gemini_client.detect_and_interpret(image)
            processing_time_ms = (time.time() - start_time) * 1000

            # Validate result
            if not gemini_layer.elements:
                logger.warning(f"Gemini returned no elements for {image_id}")
                self._circuit_breaker.record_failure()
                return None

            # Check average confidence
            avg_conf = sum(e.calibrated_confidence for e in gemini_layer.elements) / len(gemini_layer.elements)
            if avg_conf < self.config.gemini_min_confidence:
                logger.warning(
                    f"Gemini confidence too low for {image_id}: {avg_conf:.2f}"
                )
                # Don't count as circuit failure, just low confidence result
                pass

            # Success - record and convert
            self._circuit_breaker.record_success()

            vision_spec = convert_gemini_to_vision_spec(
                gemini_layer, image_id, processing_time_ms
            )

            logger.info(
                f"Gemini primary succeeded for {image_id}: "
                f"{len(gemini_layer.elements)} elements, "
                f"avg_conf={avg_conf:.2f}"
            )

            return vision_spec

        except GeminiClientError as e:
            logger.warning(f"Gemini client error for {image_id}: {e}")
            self._circuit_breaker.record_failure()
            return None
        except ImportError:
            logger.warning("Gemini client not available")
            return None
        except Exception as e:
            logger.exception(f"Unexpected Gemini error for {image_id}: {e}")
            self._circuit_breaker.record_failure()
            return None

    # =========================================================================
    # YOLO + Claude Fallback (Legacy)
    # =========================================================================

    def _check_yolo_success(
        self,
        detection_layer: Optional[DetectionLayer],
    ) -> tuple[bool, Optional[FailureReason]]:
        """Check if YOLO detection was successful."""
        if detection_layer is None:
            return False, FailureReason.YOLO_FAILED

        if len(detection_layer.elements) < self.config.min_detection_count:
            return False, FailureReason.YOLO_NO_DETECTIONS

        if detection_layer.elements:
            avg_conf = sum(
                e.detection_confidence for e in detection_layer.elements
            ) / len(detection_layer.elements)
            if avg_conf < self.config.min_detection_confidence:
                return False, FailureReason.YOLO_LOW_CONFIDENCE

        return True, None

    def _check_interpretation_success(
        self,
        interpretation_layer: Optional[InterpretationLayer],
    ) -> tuple[bool, Optional[FailureReason]]:
        """Check if Claude interpretation was successful."""
        if interpretation_layer is None:
            return False, FailureReason.CLAUDE_FAILED

        if not interpretation_layer.elements:
            return False, FailureReason.CLAUDE_FAILED

        avg_conf = sum(
            e.interpretation_confidence for e in interpretation_layer.elements
        ) / len(interpretation_layer.elements)
        if avg_conf < self.config.min_interpretation_confidence:
            return False, FailureReason.CLAUDE_LOW_CONFIDENCE

        return True, None

    async def _try_yolo_claude_fallback(
        self,
        image: Union[str, Path, bytes],
        image_id: str,
    ) -> Optional[VisionSpec]:
        """
        Attempt YOLO + Claude as fallback.

        Args:
            image: Image to process
            image_id: Image identifier

        Returns:
            VisionSpec if successful, None otherwise
        """
        if not self.config.enable_yolo_claude_fallback:
            return None

        logger.info(f"Attempting YOLO+Claude fallback for {image_id}")

        try:
            from .yolo_detector import create_detector
            from .interpretation_layer import create_interpreter
            from .hybrid_merger import HybridMerger

            yolo = create_detector(use_mock=True)  # Safety default
            interpreter = create_interpreter(use_mock=True)
            merger = HybridMerger()

            # YOLO detection
            detection_layer: Optional[DetectionLayer] = None
            try:
                detection_layer = yolo.detect(image, image_id)
            except Exception as e:
                logger.error(f"YOLO detection failed: {e}")

            yolo_success, yolo_failure = self._check_yolo_success(detection_layer)
            if not yolo_success:
                logger.warning(f"YOLO failed in fallback: {yolo_failure}")
                return None

            # Claude interpretation
            interpretation_layer: Optional[InterpretationLayer] = None
            try:
                interpretation_layer = await interpreter.interpret(
                    image, detection_layer, image_id
                )
            except Exception as e:
                logger.error(f"Claude interpretation failed: {e}")

            interp_success, interp_failure = self._check_interpretation_success(
                interpretation_layer
            )

            # Continue even with interpretation failure (degraded mode)
            if not interp_success:
                logger.warning(f"Claude failed: {interp_failure}, using detection-only")
                interpretation_layer = InterpretationLayer(model="none")

            # Merge results
            merged_output = merger.merge(
                detection_layer or DetectionLayer(),
                interpretation_layer,
                image_id,
            )

            # Calculate timing
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
                interpretation_layer=interpretation_layer,
                merged_output=merged_output,
                fallback_used=True,
                fallback_model="yolo-claude",
                fallback_reason="gemini_primary_failed",
                total_processing_time_ms=total_time,
            )

            logger.info(
                f"YOLO+Claude fallback succeeded for {image_id}: "
                f"{len(merged_output.elements)} elements"
            )

            return vision_spec

        except ImportError as e:
            logger.warning(f"YOLO/Claude modules not available: {e}")
            return None
        except Exception as e:
            logger.exception(f"YOLO+Claude fallback error for {image_id}: {e}")
            return None

    # =========================================================================
    # Manual Fallback
    # =========================================================================

    def _create_manual_fallback_spec(
        self,
        image_id: str,
        failure_reason: FailureReason,
    ) -> VisionSpec:
        """Create VisionSpec marking manual annotation required."""
        from ..schemas import MergedOutput

        review = ReviewMetadata(
            review_required=True,
            review_severity=ReviewSeverity.BLOCKER,
            review_reason=f"Manual annotation required: {failure_reason.value}",
        )

        provenance = Provenance(
            stage=PipelineStage.VISION_PARSE,
            model="manual-required",
        )

        return VisionSpec(
            image_id=image_id,
            provenance=provenance,
            merged_output=MergedOutput(elements=[]),
            fallback_used=True,
            fallback_model="manual",
            fallback_reason=failure_reason.value,
            review=review,
        )

    # =========================================================================
    # Main Execution
    # =========================================================================

    async def execute_with_fallback(
        self,
        image: Union[str, Path, bytes],
        image_id: str,
    ) -> tuple[VisionSpec, FallbackLevel]:
        """
        Execute vision parsing with Gemini-first fallback chain.

        Fallback order:
        1. Gemini 3 Pro (primary)
        2. YOLO + Claude (legacy fallback)
        3. Manual annotation (last resort)

        Args:
            image: Image to process
            image_id: Image identifier

        Returns:
            Tuple of (VisionSpec result, FallbackLevel used)
        """
        # Try Gemini Primary
        result = await self._try_gemini_primary(image, image_id)
        if result:
            return result, FallbackLevel.GEMINI_PRIMARY

        # Try YOLO + Claude Fallback
        result = await self._try_yolo_claude_fallback(image, image_id)
        if result:
            return result, FallbackLevel.YOLO_CLAUDE

        # Manual Fallback (last resort)
        if self.config.enable_manual_fallback:
            logger.warning(f"All automated methods failed for {image_id}, requiring manual")
            return (
                self._create_manual_fallback_spec(image_id, FailureReason.UNKNOWN),
                FallbackLevel.MANUAL,
            )

        # No fallback available - raise error
        raise RuntimeError(
            f"All vision processing methods failed for {image_id} "
            "and manual fallback is disabled"
        )


# =============================================================================
# Convenience Functions
# =============================================================================

async def process_with_fallback(
    image: Union[str, Path, bytes],
    image_id: str,
    config: Optional[FallbackConfig] = None,
) -> VisionSpec:
    """
    Process image with full Gemini-first fallback chain.

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

    logger.info(f"Processed {image_id} with fallback level: {level.value}")

    return vision_spec


def get_circuit_breaker_status() -> Dict[str, Any]:
    """Get current circuit breaker status for monitoring."""
    executor = FallbackExecutor()
    cb = executor._circuit_breaker
    return {
        "state": cb.state.value,
        "failures": cb._failures,
        "is_available": cb.is_available(),
    }


# =============================================================================
# Export
# =============================================================================

__all__ = [
    "FallbackLevel",
    "FailureReason",
    "CircuitState",
    "CircuitBreaker",
    "FallbackConfig",
    "FallbackExecutor",
    "convert_gemini_to_vision_spec",
    "process_with_fallback",
    "get_circuit_breaker_status",
]
