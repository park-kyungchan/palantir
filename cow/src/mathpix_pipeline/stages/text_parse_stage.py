"""
Stage B: Text Parse Stage.

Wraps MathpixClient to convert IngestionSpec into TextSpec.
Handles Mathpix API integration with proper error handling.

Module Version: 1.0.0
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional, Union

from ..schemas.common import PipelineStage
from ..schemas.ingestion import IngestionSpec
from ..schemas.text_spec import TextSpec
from ..clients.mathpix import (
    MathpixClient,
    MathpixConfig,
    MathpixError,
    InvalidImageError,
    RateLimitError,
    TimeoutError as MathpixTimeoutError,
    ServerError,
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
class TextParseStageConfig:
    """Configuration for Stage B text parsing.

    Attributes:
        mathpix_config: Configuration for Mathpix API client
        require_stored_path: Whether to require stored_path in input
        min_image_size: Minimum image dimension (width or height)
        max_image_size: Maximum image dimension (width or height)
        require_validation_passed: Whether input must have passed validation
    """
    mathpix_config: Optional[MathpixConfig] = None
    require_stored_path: bool = True
    min_image_size: int = 10
    max_image_size: int = 10000
    require_validation_passed: bool = True


# =============================================================================
# Stage Implementation
# =============================================================================

class TextParseStage(BaseStage[IngestionSpec, TextSpec]):
    """Stage B: Text Parse using Mathpix API.

    Converts IngestionSpec from Stage A into TextSpec through:
    1. Image validation (size, format, path)
    2. Mathpix API call for OCR/text extraction
    3. Response parsing into structured TextSpec
    4. Content flag and trigger determination

    The stage wraps MathpixClient and handles:
    - API errors with proper error categorization
    - Rate limiting with retry logic (handled by client)
    - Invalid image detection
    - Low confidence flagging for review

    Example:
        config = TextParseStageConfig(
            mathpix_config=MathpixConfig(app_id="...", app_key="..."),
        )
        stage = TextParseStage(config=config)
        result = await stage.run_async(ingestion_spec)
        if result.is_valid:
            text_spec = result.output
    """

    def __init__(
        self,
        config: Optional[TextParseStageConfig] = None,
        client: Optional[MathpixClient] = None,
    ):
        """Initialize text parse stage.

        Args:
            config: Stage configuration
            client: Custom MathpixClient (created from config if not provided)
        """
        super().__init__(config or TextParseStageConfig())
        self._client = client
        self._owns_client = client is None

    @property
    def stage_name(self) -> PipelineStage:
        """Return Stage B identifier."""
        return PipelineStage.TEXT_PARSE

    @property
    def config(self) -> TextParseStageConfig:
        """Return typed configuration."""
        return self._config

    @property
    def client(self) -> Optional[MathpixClient]:
        """Return the underlying Mathpix client."""
        return self._client

    def validate(self, input_data: IngestionSpec) -> ValidationResult:
        """Validate ingestion spec input.

        Checks:
        - Input is not None
        - Image metadata is present and valid
        - Image dimensions are within bounds
        - Validation passed (if required)
        - Stored path exists (if required)

        Args:
            input_data: IngestionSpec to validate

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
            return result

        # Check metadata
        if input_data.metadata is None:
            result.add_error("IngestionSpec must have metadata")
            return result

        # Check image dimensions
        width = input_data.metadata.width
        height = input_data.metadata.height

        if width < self.config.min_image_size:
            result.add_error(
                f"Image width {width} is below minimum {self.config.min_image_size}"
            )
        if height < self.config.min_image_size:
            result.add_error(
                f"Image height {height} is below minimum {self.config.min_image_size}"
            )
        if width > self.config.max_image_size:
            result.add_error(
                f"Image width {width} exceeds maximum {self.config.max_image_size}"
            )
        if height > self.config.max_image_size:
            result.add_error(
                f"Image height {height} exceeds maximum {self.config.max_image_size}"
            )

        # Check validation status
        if self.config.require_validation_passed:
            if input_data.validation is None:
                result.add_warning("IngestionSpec has no validation result")
            elif not input_data.validation.is_valid:
                result.add_error("IngestionSpec validation failed")

        # Check stored path
        if self.config.require_stored_path:
            if not input_data.stored_path:
                result.add_error("IngestionSpec must have stored_path")
            elif not Path(input_data.stored_path).exists():
                result.add_error(
                    f"Stored path does not exist: {input_data.stored_path}"
                )

        # Warnings for edge cases
        if input_data.math_content_confidence < 0.3:
            result.add_warning(
                f"Low math content confidence: {input_data.math_content_confidence:.2f}"
            )

        return result

    async def _execute_async(
        self,
        input_data: IngestionSpec,
        **kwargs: Any,
    ) -> TextSpec:
        """Execute text parsing through Mathpix API.

        Args:
            input_data: IngestionSpec from Stage A
            **kwargs: Additional parameters (unused)

        Returns:
            TextSpec with extracted text and equations

        Raises:
            StageExecutionError: If API call or parsing fails
        """
        # Determine image source
        image_source: Union[str, Path]
        if input_data.stored_path:
            image_source = Path(input_data.stored_path)
        elif input_data.source_path:
            image_source = Path(input_data.source_path)
        else:
            raise StageExecutionError(
                message="No image path available in IngestionSpec",
                stage=self.stage_name,
            )

        # Ensure client is available
        if self._client is None:
            if self.config.mathpix_config is None:
                raise StageExecutionError(
                    message="MathpixConfig is required when client is not provided",
                    stage=self.stage_name,
                )
            self._client = MathpixClient(self.config.mathpix_config)

        try:
            # Use context manager if we own the client
            if self._owns_client:
                async with self._client as client:
                    text_spec = await client.process_image(
                        image=image_source,
                        image_id=input_data.image_id,
                    )
            else:
                # Client is externally managed
                text_spec = await self._client.process_image(
                    image=image_source,
                    image_id=input_data.image_id,
                )

            return text_spec

        except InvalidImageError as e:
            raise StageExecutionError(
                message=f"Invalid image format: {e}",
                stage=self.stage_name,
                cause=e,
            )
        except RateLimitError as e:
            raise StageExecutionError(
                message=f"Mathpix API rate limit exceeded (retry after {e.retry_after}s)",
                stage=self.stage_name,
                cause=e,
            )
        except MathpixTimeoutError as e:
            raise StageExecutionError(
                message=f"Mathpix API timeout: {e}",
                stage=self.stage_name,
                cause=e,
            )
        except ServerError as e:
            raise StageExecutionError(
                message=f"Mathpix server error: {e}",
                stage=self.stage_name,
                cause=e,
            )
        except MathpixError as e:
            raise StageExecutionError(
                message=f"Mathpix API error: {e}",
                stage=self.stage_name,
                cause=e,
            )
        except Exception as e:
            raise StageExecutionError(
                message=f"Text parsing failed: {e}",
                stage=self.stage_name,
                cause=e,
            )

    def get_metrics(self, output: TextSpec) -> StageMetrics:
        """Collect text parsing metrics.

        Args:
            output: TextSpec from execution

        Returns:
            StageMetrics with parsing statistics
        """
        metrics = StageMetrics(
            stage=self.stage_name,
            success=output is not None,
        )

        if output:
            metrics.elements_processed = len(output.line_segments)
            metrics.custom_metrics = {
                "image_id": output.image_id,
                "confidence": output.confidence,
                "line_count": len(output.line_segments),
                "equation_count": len(output.equations),
                "vision_parse_triggers": [t.value for t in output.vision_parse_triggers],
                "contains_diagram": output.content_flags.contains_diagram,
                "contains_graph": output.content_flags.contains_graph,
                "contains_geometry": output.content_flags.contains_geometry,
                "writing_style": output.writing_style.value if output.writing_style else None,
                "processing_time_ms": output.processing_time_ms,
                "review_required": output.review.review_required,
            }

        return metrics


# =============================================================================
# Export
# =============================================================================

__all__ = [
    "TextParseStage",
    "TextParseStageConfig",
]
