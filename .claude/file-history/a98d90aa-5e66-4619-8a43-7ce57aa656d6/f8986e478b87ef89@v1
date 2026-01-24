"""
Alignment Engine for Stage D.

Main orchestrator that combines:
- Text-Visual matching
- Consistency checking
- Inconsistency detection
- Threshold application

Produces AlignmentReport as output.

Schema Version: 2.0.0
Module Version: 1.1.0 - Added structured logging with timing
"""

import logging
import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Dict, Generator, List, Optional, Tuple

try:
    import structlog
    _STRUCTLOG_AVAILABLE = True
except ImportError:
    _STRUCTLOG_AVAILABLE = False
    structlog = None

from ..schemas import (
    AlignmentReport,
    AlignmentStatistics,
    Confidence,
    Inconsistency,
    MatchedPair,
    Provenance,
    PipelineStage,
    ReviewMetadata,
    ReviewSeverity,
    TextElement,
    TextSpec,
    UnmatchedElement,
    VisualElement,
    VisionSpec,
)
from ..schemas.threshold import (
    ThresholdConfig,
    ThresholdContext,
    FeedbackStats,
    compute_effective_threshold,
)
from .matcher import MatcherConfig, TextVisualMatcher
from .consistency import ConsistencyConfig, ConsistencyChecker
from .inconsistency import InconsistencyConfig, InconsistencyDetector


# =============================================================================
# Structured Logging Setup
# =============================================================================

# Standard logger fallback
_std_logger = logging.getLogger(__name__)

# Structured logger (uses structlog if available, falls back to standard)
if _STRUCTLOG_AVAILABLE:
    logger = structlog.get_logger(__name__)
else:
    logger = _std_logger


@contextmanager
def timed_operation(
    operation_name: str,
    **context: Any,
) -> Generator[Dict[str, Any], None, None]:
    """Context manager for timing operations with structured logging.

    Args:
        operation_name: Name of the operation being timed
        **context: Additional context to include in logs

    Yields:
        Dict that can be used to add additional timing data
    """
    timing_data: Dict[str, Any] = {
        "operation": operation_name,
        "start_time": time.perf_counter(),
        **context,
    }

    if _STRUCTLOG_AVAILABLE:
        logger.info(
            f"{operation_name}_started",
            **context,
        )
    else:
        _std_logger.info(f"{operation_name} started: {context}")

    try:
        yield timing_data
    except Exception as e:
        duration_ms = (time.perf_counter() - timing_data["start_time"]) * 1000
        timing_data["duration_ms"] = duration_ms
        timing_data["error"] = str(e)

        if _STRUCTLOG_AVAILABLE:
            logger.error(
                f"{operation_name}_failed",
                duration_ms=duration_ms,
                error=str(e),
                error_type=type(e).__name__,
                **context,
            )
        else:
            _std_logger.error(
                f"{operation_name} failed after {duration_ms:.2f}ms: {e}"
            )
        raise
    else:
        duration_ms = (time.perf_counter() - timing_data["start_time"]) * 1000
        timing_data["duration_ms"] = duration_ms

        if _STRUCTLOG_AVAILABLE:
            logger.info(
                f"{operation_name}_completed",
                duration_ms=duration_ms,
                **context,
            )
        else:
            _std_logger.info(
                f"{operation_name} completed in {duration_ms:.2f}ms"
            )


# =============================================================================
# Configuration
# =============================================================================

@dataclass
class AlignmentEngineConfig:
    """Configuration for alignment engine."""
    # Component configs
    matcher_config: MatcherConfig = None
    consistency_config: ConsistencyConfig = None
    inconsistency_config: InconsistencyConfig = None

    # Threshold settings
    base_alignment_threshold: float = 0.60
    base_inconsistency_threshold: float = 0.80

    # Processing settings
    enable_threshold_adjustment: bool = True
    enable_auto_fix_detection: bool = True

    def __post_init__(self):
        """Initialize default configs if not provided."""
        if self.matcher_config is None:
            self.matcher_config = MatcherConfig()
        if self.consistency_config is None:
            self.consistency_config = ConsistencyConfig()
        if self.inconsistency_config is None:
            self.inconsistency_config = InconsistencyConfig()


# =============================================================================
# Alignment Engine
# =============================================================================

class AlignmentEngine:
    """Main alignment engine for Stage D.

    Orchestrates the alignment process:
    1. Match text elements to visual elements
    2. Check consistency of matched pairs
    3. Detect inconsistencies
    4. Apply thresholds and determine review requirements
    5. Generate AlignmentReport

    Usage:
        config = AlignmentEngineConfig()
        engine = AlignmentEngine(config)

        report = engine.align(text_spec, vision_spec)
    """

    def __init__(
        self,
        config: Optional[AlignmentEngineConfig] = None,
        threshold_config: Optional[ThresholdConfig] = None,
    ):
        """Initialize alignment engine.

        Args:
            config: Engine configuration
            threshold_config: Threshold calibration configuration
        """
        self.config = config or AlignmentEngineConfig()
        self.threshold_config = threshold_config

        # Initialize components
        self.matcher = TextVisualMatcher(self.config.matcher_config)
        self.consistency_checker = ConsistencyChecker(self.config.consistency_config)
        self.inconsistency_detector = InconsistencyDetector(self.config.inconsistency_config)

    def _get_effective_threshold(
        self,
        element_type: str,
        context: Optional[ThresholdContext] = None,
        feedback_stats: Optional[FeedbackStats] = None,
    ) -> float:
        """Get effective threshold for element type.

        Args:
            element_type: Type of element (e.g., 'alignment_match')
            context: Optional threshold context
            feedback_stats: Optional feedback statistics

        Returns:
            Effective threshold value
        """
        if not self.config.enable_threshold_adjustment or not self.threshold_config:
            return self.config.base_alignment_threshold

        if context is None:
            context = ThresholdContext()
        if feedback_stats is None:
            feedback_stats = FeedbackStats()

        return compute_effective_threshold(
            element_type=element_type,
            config=self.threshold_config,
            context=context,
            feedback_stats=feedback_stats,
        )

    def _create_unmatched_elements(
        self,
        unmatched_text: List[TextElement],
        unmatched_visual: List[VisualElement],
        image_id: str,
    ) -> List[UnmatchedElement]:
        """Create UnmatchedElement list from unmatched elements.

        Args:
            unmatched_text: Text elements without match
            unmatched_visual: Visual elements without match
            image_id: Image identifier

        Returns:
            List of UnmatchedElement
        """
        unmatched: List[UnmatchedElement] = []

        for text_elem in unmatched_text:
            unmatched.append(UnmatchedElement(
                id=f"{image_id}-unmatched-text-{text_elem.id}",
                source="text",
                element_id=text_elem.id,
                content=text_elem.content,
                bbox=text_elem.bbox,
                reason="No matching visual element found",
            ))

        for visual_elem in unmatched_visual:
            unmatched.append(UnmatchedElement(
                id=f"{image_id}-unmatched-visual-{visual_elem.id}",
                source="visual",
                element_id=visual_elem.id,
                content=visual_elem.semantic_label,
                bbox=visual_elem.bbox,
                reason="No matching text element found",
            ))

        return unmatched

    def _compute_overall_alignment_score(
        self,
        matched_pairs: List[MatchedPair],
        inconsistencies: List[Inconsistency],
        unmatched_count: int,
        total_elements: int,
    ) -> float:
        """Compute overall alignment score.

        Args:
            matched_pairs: All matched pairs
            inconsistencies: All inconsistencies
            unmatched_count: Number of unmatched elements
            total_elements: Total number of elements

        Returns:
            Overall score (0.0-1.0)
        """
        if total_elements == 0:
            return 0.0

        # Base score from matched pairs
        if matched_pairs:
            avg_consistency = sum(p.consistency_score for p in matched_pairs) / len(matched_pairs)
        else:
            avg_consistency = 0.0

        # Penalty for unmatched elements
        unmatched_penalty = unmatched_count / max(total_elements, 1) * 0.3

        # Penalty for inconsistencies
        blocker_count = sum(1 for i in inconsistencies if i.severity == ReviewSeverity.BLOCKER)
        high_count = sum(1 for i in inconsistencies if i.severity == ReviewSeverity.HIGH)

        inconsistency_penalty = (blocker_count * 0.2) + (high_count * 0.1)

        # Calculate final score
        score = avg_consistency - unmatched_penalty - inconsistency_penalty

        return max(0.0, min(1.0, score))

    def align(
        self,
        text_spec: TextSpec,
        vision_spec: VisionSpec,
        context: Optional[ThresholdContext] = None,
        feedback_stats: Optional[FeedbackStats] = None,
    ) -> AlignmentReport:
        """Perform alignment between text and visual specifications.

        Args:
            text_spec: Stage B output
            vision_spec: Stage C output
            context: Optional threshold context
            feedback_stats: Optional feedback statistics

        Returns:
            AlignmentReport with alignment results
        """
        start_time = time.perf_counter()
        image_id = text_spec.image_id

        # Timing data for each step
        step_timings: Dict[str, float] = {}

        # Log alignment start with structured data
        if _STRUCTLOG_AVAILABLE:
            logger.info(
                "alignment_started",
                image_id=image_id,
                text_elements=len(text_spec.equations) + len(text_spec.line_segments),
                visual_elements=len(vision_spec.merged_output.elements),
            )
        else:
            _std_logger.info(f"Starting alignment for {image_id}")

        try:
            # Get effective thresholds
            with timed_operation("threshold_calculation", image_id=image_id) as timing:
                alignment_threshold = self._get_effective_threshold(
                    "alignment_match", context, feedback_stats
                )
                inconsistency_threshold = self._get_effective_threshold(
                    "inconsistency", context, feedback_stats
                )
            step_timings["threshold_calculation_ms"] = timing.get("duration_ms", 0)

            # Step 1: Match text and visual elements
            with timed_operation("matching", image_id=image_id) as timing:
                matched_pairs = self.matcher.match(
                    text_spec=text_spec,
                    vision_spec=vision_spec,
                    image_id=image_id,
                    base_threshold=alignment_threshold,
                )
            step_timings["matching_ms"] = timing.get("duration_ms", 0)

            if _STRUCTLOG_AVAILABLE:
                logger.debug(
                    "matching_completed",
                    image_id=image_id,
                    matched_pairs=len(matched_pairs),
                    duration_ms=step_timings["matching_ms"],
                )
            else:
                _std_logger.debug(f"Found {len(matched_pairs)} matched pairs")

            # Get unmatched elements
            with timed_operation("unmatched_detection", image_id=image_id) as timing:
                unmatched_text, unmatched_visual = self.matcher.get_unmatched(
                    text_spec, vision_spec, matched_pairs
                )
            step_timings["unmatched_detection_ms"] = timing.get("duration_ms", 0)

            # Step 2: Check consistency
            with timed_operation("consistency_check", image_id=image_id) as timing:
                self.consistency_checker.check_all(matched_pairs)
            step_timings["consistency_check_ms"] = timing.get("duration_ms", 0)

            # Step 3: Detect inconsistencies
            with timed_operation("inconsistency_detection", image_id=image_id) as timing:
                inconsistencies = self.inconsistency_detector.detect_all(
                    matched_pairs=matched_pairs,
                    unmatched_text=unmatched_text,
                    unmatched_visual=unmatched_visual,
                    image_id=image_id,
                )
            step_timings["inconsistency_detection_ms"] = timing.get("duration_ms", 0)

            if _STRUCTLOG_AVAILABLE:
                logger.debug(
                    "inconsistency_detection_completed",
                    image_id=image_id,
                    inconsistencies=len(inconsistencies),
                    duration_ms=step_timings["inconsistency_detection_ms"],
                )
            else:
                _std_logger.debug(f"Detected {len(inconsistencies)} inconsistencies")

            # Step 4: Create unmatched elements list
            unmatched_elements = self._create_unmatched_elements(
                unmatched_text, unmatched_visual, image_id
            )

            # Step 5: Compute overall scores
            total_text = len(text_spec.equations) + len(text_spec.line_segments)
            total_visual = len(vision_spec.merged_output.elements)
            total_elements = total_text + total_visual

            with timed_operation("score_computation", image_id=image_id) as timing:
                overall_alignment_score = self._compute_overall_alignment_score(
                    matched_pairs=matched_pairs,
                    inconsistencies=inconsistencies,
                    unmatched_count=len(unmatched_elements),
                    total_elements=total_elements,
                )
                overall_confidence = self.consistency_checker.compute_overall_score(matched_pairs)
            step_timings["score_computation_ms"] = timing.get("duration_ms", 0)

            # Step 6: Build statistics
            # Note: AlignmentStatistics v2.1.0 only stores input counts.
            # Derived statistics (matched_pairs_count, pairs_above_threshold, etc.)
            # are computed via @computed_field in AlignmentReport.
            statistics = AlignmentStatistics(
                total_text_elements=total_text,
                total_visual_elements=total_visual,
            )

            # Step 7: Create provenance
            processing_time_ms = (time.perf_counter() - start_time) * 1000

            provenance = Provenance(
                stage=PipelineStage.ALIGNMENT,
                model="alignment-engine-v2",
                processing_time_ms=processing_time_ms,
            )

            # Step 8: Build AlignmentReport
            report = AlignmentReport(
                image_id=image_id,
                text_spec_id=text_spec.image_id,
                vision_spec_id=vision_spec.image_id,
                provenance=provenance,
                matched_pairs=matched_pairs,
                inconsistencies=inconsistencies,
                unmatched_elements=unmatched_elements,
                statistics=statistics,
                threshold_config_version="2.0.0",
                base_alignment_threshold=alignment_threshold,
                base_inconsistency_threshold=inconsistency_threshold,
                overall_alignment_score=overall_alignment_score,
                overall_confidence=overall_confidence,
                processing_time_ms=processing_time_ms,
            )

            # Log completion with structured timing data
            if _STRUCTLOG_AVAILABLE:
                logger.info(
                    "alignment_completed",
                    image_id=image_id,
                    duration_ms=processing_time_ms,
                    matched_pairs=len(matched_pairs),
                    inconsistencies=len(inconsistencies),
                    unmatched_elements=len(unmatched_elements),
                    overall_alignment_score=round(overall_alignment_score, 4),
                    overall_confidence=round(overall_confidence, 4),
                    alignment_threshold=alignment_threshold,
                    pairs_above_threshold=statistics.pairs_above_threshold,
                    pairs_below_threshold=statistics.pairs_below_threshold,
                    step_timings=step_timings,
                )
            else:
                _std_logger.info(
                    f"Alignment completed for {image_id}: "
                    f"score={overall_alignment_score:.2f}, "
                    f"pairs={len(matched_pairs)}, "
                    f"inconsistencies={len(inconsistencies)}, "
                    f"duration={processing_time_ms:.2f}ms"
                )

            return report

        except Exception as e:
            processing_time_ms = (time.perf_counter() - start_time) * 1000

            if _STRUCTLOG_AVAILABLE:
                logger.error(
                    "alignment_failed",
                    image_id=image_id,
                    duration_ms=processing_time_ms,
                    error=str(e),
                    error_type=type(e).__name__,
                    step_timings=step_timings,
                )
            else:
                _std_logger.error(
                    f"Alignment failed for {image_id} after {processing_time_ms:.2f}ms: {e}"
                )
            raise


# =============================================================================
# Convenience Functions
# =============================================================================

def create_alignment_engine(
    config: Optional[AlignmentEngineConfig] = None,
    threshold_config: Optional[ThresholdConfig] = None,
) -> AlignmentEngine:
    """Factory function to create alignment engine.

    Args:
        config: Optional engine configuration
        threshold_config: Optional threshold configuration

    Returns:
        Configured AlignmentEngine instance
    """
    return AlignmentEngine(config, threshold_config)


def align_text_and_vision(
    text_spec: TextSpec,
    vision_spec: VisionSpec,
    config: Optional[AlignmentEngineConfig] = None,
) -> AlignmentReport:
    """Convenience function to perform alignment.

    Args:
        text_spec: Stage B output
        vision_spec: Stage C output
        config: Optional engine configuration

    Returns:
        AlignmentReport
    """
    engine = AlignmentEngine(config)
    return engine.align(text_spec, vision_spec)


# =============================================================================
# Export
# =============================================================================

__all__ = [
    "AlignmentEngineConfig",
    "AlignmentEngine",
    "create_alignment_engine",
    "align_text_and_vision",
]
