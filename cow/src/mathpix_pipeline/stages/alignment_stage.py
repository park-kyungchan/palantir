"""
Stage D: Alignment Stage.

Wraps AlignmentEngine to align TextSpec with VisionSpec, producing AlignmentReport.
Supports dynamic threshold system (v2.0.0).

This is a COMPOSITE INPUT stage - it takes both TextSpec and VisionSpec as input.

Module Version: 1.0.0
"""

from dataclasses import dataclass
from typing import Any, Optional

from ..schemas.common import PipelineStage
from ..schemas.alignment import AlignmentReport
from ..schemas.text_spec import TextSpec
from ..schemas.vision_spec import VisionSpec
from ..schemas.threshold import (
    ThresholdConfig,
    ThresholdContext,
    FeedbackStats,
    compute_effective_threshold,
)
from ..alignment.engine import (
    AlignmentEngine,
    AlignmentEngineConfig,
)
from .base import (
    BaseStage,
    ValidationResult,
    StageMetrics,
    StageExecutionError,
)


# =============================================================================
# Composite Input
# =============================================================================

@dataclass
class AlignmentInput:
    """Composite input for Stage D alignment.

    Stage D is unique in that it requires TWO inputs:
    - text_spec: Output from Stage B (TextSpec)
    - vision_spec: Output from Stage C (VisionSpec)

    Attributes:
        text_spec: TextSpec from Stage B containing text/equation content
        vision_spec: VisionSpec from Stage C containing visual elements
    """
    text_spec: TextSpec
    vision_spec: VisionSpec

    @property
    def image_id(self) -> str:
        """Get image ID from text_spec (primary source)."""
        return self.text_spec.image_id

    def validate_image_ids_match(self) -> bool:
        """Check that both specs refer to the same image."""
        return self.text_spec.image_id == self.vision_spec.image_id


# =============================================================================
# Configuration
# =============================================================================

@dataclass
class AlignmentStageConfig:
    """Configuration for Stage D alignment.

    Attributes:
        base_alignment_threshold: Default alignment threshold (default: 0.60)
        base_inconsistency_threshold: Default inconsistency threshold (default: 0.80)
        enable_threshold_adjustment: Enable dynamic threshold adjustment
        enable_auto_fix_detection: Enable auto-fix suggestions
        threshold_context: Dynamic threshold context (v2.0.0)
        feedback_stats: Feedback loop statistics (v2.0.0)
        threshold_config: Full threshold calibration config (v2.0.0)
        engine_config: Custom AlignmentEngineConfig (optional)
    """
    base_alignment_threshold: float = 0.60
    base_inconsistency_threshold: float = 0.80
    enable_threshold_adjustment: bool = True
    enable_auto_fix_detection: bool = True
    threshold_context: Optional[ThresholdContext] = None
    feedback_stats: Optional[FeedbackStats] = None
    threshold_config: Optional[ThresholdConfig] = None
    engine_config: Optional[AlignmentEngineConfig] = None

    def to_engine_config(self) -> AlignmentEngineConfig:
        """Convert to AlignmentEngineConfig for the underlying engine."""
        if self.engine_config:
            return self.engine_config

        return AlignmentEngineConfig(
            base_alignment_threshold=self.base_alignment_threshold,
            base_inconsistency_threshold=self.base_inconsistency_threshold,
            enable_threshold_adjustment=self.enable_threshold_adjustment,
            enable_auto_fix_detection=self.enable_auto_fix_detection,
        )


# =============================================================================
# Stage Implementation
# =============================================================================

class AlignmentStage(BaseStage[AlignmentInput, AlignmentReport]):
    """Stage D: Text-Vision Alignment with dynamic thresholds.

    Aligns text content (Stage B) with visual elements (Stage C):
    1. Match text labels to diagram elements
    2. Match equations to graph curves
    3. Detect inconsistencies between text and visual
    4. Apply threshold-based review decisions

    Supports v2.0.0 dynamic threshold system:
    - Layer 1: Base thresholds per element type
    - Layer 2: Context modifiers (quality, complexity)
    - Layer 3: Feedback loop adjustments

    Example:
        config = AlignmentStageConfig(
            threshold_context=ThresholdContext(image_quality_score=0.9),
        )
        stage = AlignmentStage(config=config)

        input_data = AlignmentInput(
            text_spec=text_spec,  # from Stage B
            vision_spec=vision_spec,  # from Stage C
        )

        result = await stage.run_async(input_data)
        if result.is_valid:
            alignment_report = result.output
    """

    def __init__(
        self,
        config: Optional[AlignmentStageConfig] = None,
        engine: Optional[AlignmentEngine] = None,
    ):
        """Initialize alignment stage.

        Args:
            config: Stage configuration
            engine: Custom engine (created from config if not provided)
        """
        super().__init__(config or AlignmentStageConfig())

        if engine:
            self._engine = engine
        else:
            self._engine = AlignmentEngine(
                config=self.config.to_engine_config(),
                threshold_config=self.config.threshold_config,
            )

    @property
    def stage_name(self) -> PipelineStage:
        """Return Stage D identifier."""
        return PipelineStage.ALIGNMENT

    @property
    def config(self) -> AlignmentStageConfig:
        """Return typed configuration."""
        return self._config

    @property
    def engine(self) -> AlignmentEngine:
        """Return the underlying alignment engine."""
        return self._engine

    def validate(self, input_data: AlignmentInput) -> ValidationResult:
        """Validate alignment input.

        Validates:
        - Input is not None
        - TextSpec is present and valid
        - VisionSpec is present and valid
        - Image IDs match between specs

        Args:
            input_data: AlignmentInput to validate

        Returns:
            ValidationResult with any issues found
        """
        result = ValidationResult()

        if input_data is None:
            result.add_error("AlignmentInput is required")
            return result

        # Validate TextSpec
        if input_data.text_spec is None:
            result.add_error("TextSpec is required")
        else:
            if not input_data.text_spec.image_id:
                result.add_error("TextSpec.image_id is required")

            # Check for content
            has_content = (
                len(input_data.text_spec.equations) > 0 or
                len(input_data.text_spec.line_segments) > 0
            )
            if not has_content:
                result.add_warning("TextSpec has no equations or line segments")

        # Validate VisionSpec
        if input_data.vision_spec is None:
            result.add_error("VisionSpec is required")
        else:
            if not input_data.vision_spec.image_id:
                result.add_error("VisionSpec.image_id is required")

            # Check for merged elements
            if not input_data.vision_spec.merged_output.elements:
                result.add_warning("VisionSpec has no merged elements")

        # Validate image ID consistency
        if (input_data.text_spec is not None and
            input_data.vision_spec is not None):
            if not input_data.validate_image_ids_match():
                result.add_error(
                    f"Image ID mismatch: TextSpec has '{input_data.text_spec.image_id}', "
                    f"VisionSpec has '{input_data.vision_spec.image_id}'"
                )

        return result

    def _get_effective_threshold(
        self,
        element_type: str,
        context: Optional[ThresholdContext] = None,
        feedback_stats: Optional[FeedbackStats] = None,
    ) -> float:
        """Get effective threshold using dynamic threshold system.

        Args:
            element_type: Type of element (e.g., 'alignment_match')
            context: Optional threshold context
            feedback_stats: Optional feedback statistics

        Returns:
            Effective threshold value
        """
        # Use config values if not provided
        ctx = context or self.config.threshold_context or ThresholdContext()
        stats = feedback_stats or self.config.feedback_stats or FeedbackStats()

        # If no threshold config, use base threshold
        if self.config.threshold_config is None:
            return self.config.base_alignment_threshold

        # Check if element_type exists in config
        if element_type not in self.config.threshold_config.element_thresholds:
            return self.config.base_alignment_threshold

        return compute_effective_threshold(
            element_type=element_type,
            context=ctx,
            feedback_stats=stats,
            config=self.config.threshold_config,
        )

    async def _execute_async(
        self,
        input_data: AlignmentInput,
        **kwargs: Any,
    ) -> AlignmentReport:
        """Execute alignment between text and visual specifications.

        Args:
            input_data: AlignmentInput with text_spec and vision_spec
            **kwargs: Additional parameters (passed to engine)

        Returns:
            AlignmentReport with alignment results

        Raises:
            StageExecutionError: If alignment fails
        """
        try:
            # Get threshold context from kwargs or config
            context = kwargs.pop('threshold_context', None) or self.config.threshold_context
            feedback_stats = kwargs.pop('feedback_stats', None) or self.config.feedback_stats

            # Perform alignment using the engine
            report = self._engine.align(
                text_spec=input_data.text_spec,
                vision_spec=input_data.vision_spec,
                context=context,
                feedback_stats=feedback_stats,
            )

            return report

        except Exception as e:
            raise StageExecutionError(
                message=f"Alignment failed: {e}",
                stage=self.stage_name,
                cause=e,
            )

    def get_metrics(self, output: AlignmentReport) -> StageMetrics:
        """Collect alignment metrics.

        Args:
            output: AlignmentReport from execution

        Returns:
            StageMetrics with alignment statistics
        """
        metrics = StageMetrics(
            stage=self.stage_name,
            success=output is not None,
        )

        if output:
            metrics.elements_processed = output.matched_pairs_count
            metrics.custom_metrics = {
                "matched_pairs": output.matched_pairs_count,
                "inconsistencies": output.inconsistencies_found,
                "unmatched_text": output.unmatched_text_count,
                "unmatched_visual": output.unmatched_visual_count,
                "pairs_above_threshold": output.pairs_above_threshold,
                "pairs_below_threshold": output.pairs_below_threshold,
                "overall_alignment_score": output.overall_alignment_score,
                "overall_confidence": output.overall_confidence,
                "review_required": output.needs_human_review(),
                "has_blockers": output.has_blockers(),
                "image_id": output.image_id,
            }

        return metrics


# =============================================================================
# Convenience Functions
# =============================================================================

def create_alignment_stage(
    config: Optional[AlignmentStageConfig] = None,
    threshold_config: Optional[ThresholdConfig] = None,
) -> AlignmentStage:
    """Factory function to create alignment stage.

    Args:
        config: Optional stage configuration
        threshold_config: Optional threshold configuration

    Returns:
        Configured AlignmentStage instance
    """
    if config is None:
        config = AlignmentStageConfig()

    if threshold_config is not None:
        config.threshold_config = threshold_config

    return AlignmentStage(config=config)


def create_alignment_input(
    text_spec: TextSpec,
    vision_spec: VisionSpec,
) -> AlignmentInput:
    """Factory function to create alignment input.

    Args:
        text_spec: Stage B output
        vision_spec: Stage C output

    Returns:
        AlignmentInput for stage processing
    """
    return AlignmentInput(
        text_spec=text_spec,
        vision_spec=vision_spec,
    )


# =============================================================================
# Export
# =============================================================================

__all__ = [
    # Composite Input
    "AlignmentInput",
    # Configuration
    "AlignmentStageConfig",
    # Stage Implementation
    "AlignmentStage",
    # Convenience Functions
    "create_alignment_stage",
    "create_alignment_input",
]
