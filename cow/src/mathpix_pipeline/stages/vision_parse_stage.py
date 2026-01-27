"""
Stage C: Vision Parse Stage.

Wraps the hybrid YOLO + Claude architecture for visual element detection
and semantic interpretation. Supports 3-tier fallback chain:
1. Primary: YOLO26 + Claude Opus 4.5
2. Fallback 1: Gemini 2.5 zero-shot
3. Fallback 2: Manual annotation required

Module Version: 1.0.0
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional, Union

from ..schemas.common import PipelineStage
from ..schemas.ingestion import IngestionSpec
from ..schemas.vision_spec import VisionSpec
from ..vision import (
    FallbackConfig,
    FallbackExecutor,
    FallbackLevel,
    YOLOConfig,
    InterpretationConfig,
    MergerConfig,
    VisionError,
    create_detector,
    create_interpreter,
)
from .base import (
    BaseStage,
    ValidationResult,
    StageMetrics,
    StageExecutionError,
)


# =============================================================================
# Configuration
# =============================================================================

@dataclass
class VisionParseStageConfig:
    """Configuration for Stage C vision parsing.

    Attributes:
        fallback_config: Fallback strategy configuration
        yolo_config: YOLO detector configuration
        interpretation_config: Claude interpreter configuration
        merger_config: Hybrid merger configuration
        use_mock: Use mock components for testing
        strict_validation: Fail on validation errors
    """
    fallback_config: FallbackConfig = field(default_factory=FallbackConfig)
    yolo_config: Optional[YOLOConfig] = None
    interpretation_config: Optional[InterpretationConfig] = None
    merger_config: Optional[MergerConfig] = None
    use_mock: bool = False
    strict_validation: bool = False


# =============================================================================
# Stage Implementation
# =============================================================================

class VisionParseStage(BaseStage[IngestionSpec, VisionSpec]):
    """Stage C: Vision Parse.

    Processes images through the hybrid detection + interpretation pipeline:
    1. YOLO26 for bounding box detection (precise localization)
    2. Claude Opus 4.5 for semantic interpretation (understanding)
    3. HybridMerger for combining results
    4. Fallback chain for graceful degradation

    The fallback chain ensures processing completes even when primary
    components fail:
    - PRIMARY: YOLO + Claude (optimal quality)
    - GEMINI: Gemini 2.5 zero-shot (degraded but automatic)
    - MANUAL: Manual annotation required (flagged for Stage G)

    Example:
        stage = VisionParseStage(config=VisionParseStageConfig(
            use_mock=True  # For testing without ML dependencies
        ))
        result = await stage.run_async(ingestion_spec)
        if result.is_valid:
            vision_spec = result.output
            print(f"Fallback used: {vision_spec.fallback_used}")
    """

    def __init__(
        self,
        config: Optional[VisionParseStageConfig] = None,
        executor: Optional[FallbackExecutor] = None,
    ):
        """Initialize vision parse stage.

        Args:
            config: Stage configuration
            executor: Custom FallbackExecutor (created from config if not provided)
        """
        super().__init__(config or VisionParseStageConfig())

        if executor:
            self._executor = executor
        else:
            self._executor = FallbackExecutor(
                config=self.config.fallback_config
            )

        # Pre-create detector and interpreter if configs provided
        self._yolo_detector = None
        self._claude_interpreter = None

        if self.config.yolo_config:
            self._yolo_detector = create_detector(
                config=self.config.yolo_config,
                use_mock=self.config.use_mock,
            )

        if self.config.interpretation_config:
            self._claude_interpreter = create_interpreter(
                config=self.config.interpretation_config,
                use_mock=self.config.use_mock,
            )

    @property
    def stage_name(self) -> PipelineStage:
        """Return Stage C identifier."""
        return PipelineStage.VISION_PARSE

    @property
    def config(self) -> VisionParseStageConfig:
        """Return typed configuration."""
        return self._config

    @property
    def executor(self) -> FallbackExecutor:
        """Return the underlying fallback executor."""
        return self._executor

    def validate(self, input_data: IngestionSpec) -> ValidationResult:
        """Validate ingestion spec input.

        Args:
            input_data: IngestionSpec from Stage A

        Returns:
            ValidationResult with any issues found
        """
        result = ValidationResult()

        if input_data is None:
            result.add_error("IngestionSpec is required")
            return result

        # Check image_id
        if not input_data.image_id:
            result.add_error("IngestionSpec must have image_id")

        # Check for image source
        if not input_data.source_path and not input_data.source_url and not input_data.stored_path:
            result.add_error("No image source available (source_path, source_url, or stored_path required)")

        # Check validation status
        if not input_data.validation.is_valid:
            if self.config.strict_validation:
                result.add_error(
                    f"IngestionSpec validation failed: {input_data.validation.error_details}"
                )
            else:
                result.add_warning(
                    f"IngestionSpec has validation issues: {input_data.validation.checks_failed}"
                )

        # Check image metadata
        if input_data.metadata:
            # Warn about small images
            if input_data.metadata.width < 100 or input_data.metadata.height < 100:
                result.add_warning("Image is very small, may affect detection quality")

            # Warn about unsupported formats
            supported_formats = {"png", "jpg", "jpeg", "gif", "webp"}
            if input_data.metadata.format.lower() not in supported_formats:
                result.add_warning(
                    f"Image format '{input_data.metadata.format}' may not be fully supported"
                )

        return result

    def _get_image_source(self, input_data: IngestionSpec) -> Union[str, Path]:
        """Extract image source from IngestionSpec.

        Priority: stored_path > source_path > source_url

        Args:
            input_data: IngestionSpec with image source info

        Returns:
            Image source path or URL
        """
        if input_data.stored_path:
            return input_data.stored_path
        elif input_data.source_path:
            return input_data.source_path
        elif input_data.source_url:
            return input_data.source_url
        else:
            raise StageExecutionError(
                message="No image source available",
                stage=self.stage_name,
            )

    async def _execute_async(
        self,
        input_data: IngestionSpec,
        **kwargs: Any,
    ) -> VisionSpec:
        """Execute vision parsing with fallback chain.

        Args:
            input_data: IngestionSpec from Stage A
            **kwargs: Additional parameters

        Returns:
            VisionSpec with detection + interpretation results

        Raises:
            StageExecutionError: If all fallbacks fail
        """
        try:
            # Get image source
            image_source = self._get_image_source(input_data)
            image_id = input_data.image_id

            # Execute with fallback chain
            vision_spec, fallback_level = await self._executor.execute_with_fallback(
                image=image_source,
                image_id=image_id,
                yolo_detector=self._yolo_detector,
                claude_interpreter=self._claude_interpreter,
            )

            # Log fallback usage
            if fallback_level != FallbackLevel.PRIMARY:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(
                    f"Vision parse used fallback level {fallback_level.value} "
                    f"for image {image_id}"
                )

            return vision_spec

        except VisionError as e:
            raise StageExecutionError(
                message=str(e),
                stage=self.stage_name,
                cause=e,
            )
        except Exception as e:
            raise StageExecutionError(
                message=f"Vision parsing failed: {e}",
                stage=self.stage_name,
                cause=e,
            )

    def get_metrics(self, output: VisionSpec) -> StageMetrics:
        """Collect vision parsing metrics.

        Args:
            output: VisionSpec from execution

        Returns:
            StageMetrics with vision parsing statistics
        """
        metrics = StageMetrics(
            stage=self.stage_name,
            success=output is not None,
        )

        if output:
            # Count elements
            detection_count = 0
            interpretation_count = 0
            merged_count = 0

            if output.detection_layer and output.detection_layer.elements:
                detection_count = len(output.detection_layer.elements)

            if output.interpretation_layer and output.interpretation_layer.elements:
                interpretation_count = len(output.interpretation_layer.elements)

            if output.merged_output and output.merged_output.elements:
                merged_count = len(output.merged_output.elements)

            metrics.elements_processed = merged_count

            metrics.custom_metrics = {
                "image_id": output.image_id,
                "detection_count": detection_count,
                "interpretation_count": interpretation_count,
                "merged_count": merged_count,
                "overall_confidence": output.overall_confidence,
                "fallback_used": output.fallback_used,
                "fallback_model": output.fallback_model,
                "processing_time_ms": output.total_processing_time_ms,
            }

            # Add review metadata if present
            if output.review:
                metrics.custom_metrics["review_required"] = output.review.review_required
                if output.review.review_severity:
                    metrics.custom_metrics["review_severity"] = output.review.review_severity.value

        return metrics
